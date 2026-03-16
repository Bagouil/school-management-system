from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.graphics.barcode import code128

import io
import os
import arabic_reshaper
from bidi.algorithm import get_display

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, 'static', 'fonts', 'Amiri-Regular.ttf')

# Register Arabic font
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont('Arabic', FONT_PATH))
    ARABIC_FONT = "Arabic"
else:
    ARABIC_FONT = "Helvetica"


def reshape_ar(text):
    """Reshape Arabic text for proper RTL display"""
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)


class PDFReceiptGenerator:

    @staticmethod
    def generate_payment_receipt(payment, student, fee_category, school_settings, user, language="ar"):
        """Generate a professional school payment receipt PDF with two copies and barcode"""
        is_ar = language == "ar"
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )

        story = []
        styles = getSampleStyleSheet()

        primary = colors.HexColor("#875A7B")
        grey = colors.HexColor("#F5F5F5")
        border = colors.HexColor("#DDDDDD")

        # Paragraph styles
        title_style = ParagraphStyle(
            "title", parent=styles["Heading1"], fontName=ARABIC_FONT,
            fontSize=22, alignment=TA_CENTER, textColor=primary
        )
        label_style = ParagraphStyle(
            "label", parent=styles["Normal"], fontName=ARABIC_FONT,
            alignment=TA_RIGHT if is_ar else TA_LEFT
        )
        value_style = ParagraphStyle(
            "value", parent=styles["Normal"], fontName=ARABIC_FONT,
            alignment=TA_RIGHT if is_ar else TA_LEFT
        )
        center_style = ParagraphStyle(
            "center", parent=styles["Normal"], fontName=ARABIC_FONT,
            alignment=TA_CENTER
        )

        # School info
        school_name = school_settings.get(
            "school_name_ar", "المدرسة") if is_ar else school_settings.get("school_name_en", "School")
        logo_path = os.path.join(BASE_DIR, "static", "images", "school_logo.png")

        def add_header():
            if os.path.exists(logo_path):
                img = Image(logo_path, 1 * inch, 1 * inch)
                header = Table(
                    [[img, Paragraph(reshape_ar(school_name), center_style), img]],
                    colWidths=[1.5 * inch, 4 * inch, 1.5 * inch]
                )
                header.setStyle(TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER")
                ]))
                story.append(header)
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                reshape_ar("إيصال استلام رسوم") if is_ar else "PAYMENT RECEIPT",
                title_style
            ))
            story.append(Spacer(1, 20))

        def add_receipt_info():
            table = Table([
                [
                    Paragraph(payment["receipt_number"], value_style),
                    Paragraph(reshape_ar("رقم الإيصال") if is_ar else "Receipt No.", label_style),
                    Paragraph(payment["payment_date"], value_style),
                    Paragraph(reshape_ar("التاريخ") if is_ar else "Date", label_style)
                ]
            ], colWidths=[2 * inch, 1.5 * inch, 2 * inch, 1.5 * inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), grey),
                ("BOX", (0, 0), (-1, -1), 0.5, border)
            ]))
            story.append(table)
            story.append(Spacer(1, 20))

        def add_student_info():
            student_name = f"{student['first_name_ar']} {student['last_name_ar']}" if is_ar else f"{student['first_name_en']} {student['last_name_en']}"
            table = Table([
                [
                    Paragraph(reshape_ar(student_name), value_style),
                    Paragraph(reshape_ar("الاسم") if is_ar else "Name", label_style),
                    Paragraph(student["student_number"], value_style),
                    Paragraph(reshape_ar("الرقم الدراسي") if is_ar else "Student ID", label_style)
                ],
                [
                    Paragraph(reshape_ar(student["class_name_ar"]) if is_ar else student["class_name_en"], value_style),
                    Paragraph(reshape_ar("الصف") if is_ar else "Class", label_style),
                    Paragraph(school_settings.get("academic_year", ""), value_style),
                    Paragraph(reshape_ar("العام الدراسي") if is_ar else "Academic Year", label_style)
                ]
            ], colWidths=[2 * inch, 1.5 * inch, 2 * inch, 1.5 * inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), grey),
                ("BOX", (0, 0), (-1, -1), 0.5, border)
            ]))
            story.append(table)
            story.append(Spacer(1, 20))

        def add_payment_info():
            fee_name = fee_category["category_name_ar"] if is_ar else fee_category["category_name_en"]
            amount = f"{float(payment['amount_paid']):,.2f} SDG"
            table = Table([
                [Paragraph(reshape_ar("البيان") if is_ar else "Description", center_style),
                 Paragraph(reshape_ar("المبلغ") if is_ar else "Amount", center_style)],
                [Paragraph(reshape_ar(fee_name), value_style), Paragraph(amount, value_style)],
                [Paragraph(reshape_ar("الإجمالي") if is_ar else "TOTAL", center_style), Paragraph(amount, center_style)]
            ], colWidths=[4.5 * inch, 2 * inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), primary),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 1, border),
                ("BACKGROUND", (0, -1), (-1, -1), grey),
                ("ALIGN", (1, 1), (1, -1), "RIGHT")
            ]))
            story.append(table)
            story.append(Spacer(1, 40))

        def add_barcode():
            barcode = code128.Code128(
                payment["receipt_number"],
                barHeight=40,
                barWidth=1.2
            )
            barcode_table = Table([[barcode]], colWidths=[7 * inch])
            barcode_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 20)
            ]))
            story.append(barcode_table)

        def add_signatures():
            table = Table([
                [
                    Paragraph(reshape_ar("المحاسب") if is_ar else "Accountant", center_style),
                    Paragraph(reshape_ar("المستلم") if is_ar else "Received by", center_style),
                    Paragraph(reshape_ar("ختم المدرسة") if is_ar else "School Stamp", center_style)
                ],
                ["________________", "________________", "________________"]
            ], colWidths=[2.5 * inch, 2.5 * inch, 2.5 * inch])
            table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER")
            ]))
            story.append(table)
            story.append(Spacer(1, 20))

        def add_watermark(canvas, doc):
            if os.path.exists(logo_path):
                canvas.saveState()
                canvas.setFillAlpha(0.06)
                canvas.drawImage(
                    logo_path, 150, 250, width=300, height=300, mask="auto"
                )
                canvas.restoreState()

        # Build two copies per page
        for _ in range(2):  # Student copy + Accounting copy
            add_header()
            add_receipt_info()
            add_student_info()
            add_payment_info()
            add_signatures()
            add_barcode()
            if _ == 0:
                story.append(PageBreak())  # Second copy on new page

        doc.build(story, onFirstPage=add_watermark, onLaterPages=add_watermark)
        buffer.seek(0)
        return buffer