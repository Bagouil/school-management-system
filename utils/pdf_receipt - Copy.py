from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import io
import os
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display

# Get the absolute path to the fonts directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, 'static', 'fonts', 'Amiri-Regular.ttf')

# Register Arabic font
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont('Arabic', FONT_PATH))
        ARABIC_FONT = 'Arabic'
    else:
        ARABIC_FONT = 'Helvetica'
except:
    ARABIC_FONT = 'Helvetica'

def reshape_arabic_text(text):
    """Reshape Arabic text for proper display"""
    if not text:
        return ''
    try:
        text = str(text)
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    except:
        return text
def rtl_row(label, value, label_style, value_style):
    """Return a row for Arabic tables (value first then label)"""
    return [
        Paragraph(value, value_style),
        Paragraph(reshape_arabic_text(label), label_style)
    ]

def ltr_row(label, value, label_style, value_style):
    """Return a row for English tables"""
    return [
        Paragraph(label, label_style),
        Paragraph(value, value_style)
    ]
class PDFReceiptGenerator:
    @staticmethod
    def generate_payment_receipt(payment, student, fee_category, school_settings, user, language='ar'):
        """Generate an Odoo-style professional receipt with proper RTL layout"""
        
        is_arabic = language == 'ar'
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        story = []
        
        # Odoo-style color scheme
        primary_color = colors.HexColor('#875A7B')
        light_grey = colors.HexColor('#F5F5F5')
        medium_grey = colors.HexColor('#E0E0E0')
        dark_grey = colors.HexColor('#666666')
        
        # Create styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName=ARABIC_FONT if is_arabic else 'Helvetica-Bold',
            fontSize=22,
            textColor=primary_color,
            alignment=TA_CENTER,
            spaceAfter=15,
            encoding='utf-8'
        )
        
        company_style = ParagraphStyle(
            'CompanyStyle',
            parent=styles['Heading2'],
            fontName=ARABIC_FONT if is_arabic else 'Helvetica-Bold',
            fontSize=16,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=5,
            encoding='utf-8'
        )
        
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Heading3'],
            fontName=ARABIC_FONT if is_arabic else 'Helvetica-Bold',
            fontSize=12,
            textColor=dark_grey,
            alignment=TA_CENTER,
            spaceAfter=10,
            encoding='utf-8'
        )
        
        # Label style - Right aligned for Arabic, Left aligned for English
        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontName=ARABIC_FONT if is_arabic else 'Helvetica',
            fontSize=9,
            textColor=dark_grey,
            alignment=TA_RIGHT if is_arabic else TA_LEFT,
            encoding='utf-8'
        )
        
        # Value style - Left aligned for both languages
        value_style = ParagraphStyle(
            'ValueStyle',
            parent=styles['Normal'],
            fontName=ARABIC_FONT if is_arabic else 'Helvetica',
            fontSize=10,
            textColor=colors.black,
            alignment=TA_RIGHT if is_arabic else TA_LEFT,
            encoding='utf-8'
        )
        
        # Bold label style
        bold_label_style = ParagraphStyle(
            'BoldLabelStyle',
            parent=styles['Normal'],
            fontName=ARABIC_FONT if is_arabic else 'Helvetica-Bold',
            fontSize=9,
            textColor=colors.black,
            alignment=TA_RIGHT if is_arabic else TA_LEFT,
            encoding='utf-8'
        )
        
        center_style = ParagraphStyle(
            'CenterStyle',
            parent=styles['Normal'],
            fontName=ARABIC_FONT if is_arabic else 'Helvetica',
            fontSize=8,
            textColor=dark_grey,
            alignment=TA_CENTER,
            encoding='utf-8'
        )
        
        # Get school info
        school_name_ar = school_settings.get('school_name_ar', 'المدرسة')
        school_name_en = school_settings.get('school_name_en', 'School')
        school_address = school_settings.get('school_address', '')
        school_phone = school_settings.get('school_phone', '')
        school_email = school_settings.get('school_email', '')
        
        # Company Header with Logo
        logo_path = os.path.join(BASE_DIR, 'static', 'images', 'school_logo.png')
        
        # Create header table (Odoo style)
        if os.path.exists(logo_path):
            try:
                im = Image(logo_path, width=1*inch, height=1*inch)
                im.hAlign = 'CENTER'
                
                # Header with logo and company name
                header_data = [
                    [im, 
                     Paragraph(reshape_arabic_text(school_name_ar) if is_arabic else school_name_en, company_style),
                     im],  # Duplicate for balance
                ]
                
                header_table = Table(header_data, colWidths=[2*inch, 4*inch, 2*inch])
                header_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                    ('ALIGN', (2, 0), (2, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                story.append(header_table)
            except:
                story.append(Paragraph(reshape_arabic_text(school_name_ar) if is_arabic else school_name_en, company_style))
        else:
            story.append(Paragraph(reshape_arabic_text(school_name_ar) if is_arabic else school_name_en, company_style))
        
        # Address line
        if school_address:
            story.append(Paragraph(reshape_arabic_text(school_address) if is_arabic else school_address, center_style))
        
        # Contact line
        contact_parts = []
        if school_phone:
            contact_parts.append(f"{reshape_arabic_text('هاتف:') if is_arabic else 'Tel:'} {school_phone}")
        if school_email:
            contact_parts.append(f"{reshape_arabic_text('بريد:') if is_arabic else 'Email:'} {school_email}")
        if contact_parts:
            story.append(Paragraph(" | ".join(contact_parts), center_style))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Receipt Title
        story.append(Paragraph(reshape_arabic_text("إيصال استلام رسوم") if is_arabic else "PAYMENT RECEIPT", title_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Receipt Number and Date - FIXED RTL ORDER
        if is_arabic:
            receipt_info_data = [
                [
                    Paragraph(payment['receipt_number'], value_style),
                    Paragraph(reshape_arabic_text("رقم الإيصال:"), label_style),
                    Paragraph(payment['payment_date'], value_style),
                    Paragraph(reshape_arabic_text("التاريخ:"), label_style)
                ]
            ]
        else:
            receipt_info_data = [
                [
                    Paragraph("Receipt No.:", label_style),
                    Paragraph(payment['receipt_number'], value_style),
                    Paragraph("Date:", label_style),
                    Paragraph(payment['payment_date'], value_style)
                ]
            ]
        
        receipt_table = Table(receipt_info_data, colWidths=[2.3*inch, 1.2*inch, 2.3*inch, 1.2*inch])
        receipt_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_grey),
            ('BOX', (0, 0), (-1, -1), 0.5, medium_grey),
            ('ALIGN', (0, 0), (0, 0), 'RIGHT' if is_arabic else 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT' if is_arabic else 'LEFT'),
            ('ALIGN', (3, 0), (3, 0), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT if is_arabic else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(receipt_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Student Information Section
        story.append(Paragraph(reshape_arabic_text("معلومات الطالب") if is_arabic else "STUDENT INFORMATION", header_style))
        story.append(Spacer(1, 0.1*inch))
        
        student_name = f"{student['first_name_ar']} {student['last_name_ar']}"
        
        if is_arabic:
            # Arabic: Label on right, value on left
            customer_data = [
                [
                    Paragraph(reshape_arabic_text(student_name), value_style),
                    Paragraph(reshape_arabic_text("الاسم:"), label_style),
                    Paragraph(student['student_number'], value_style),
                    Paragraph(reshape_arabic_text("الرقم الدراسي:"), label_style)
                ],
                [
                    Paragraph(reshape_arabic_text(student['class_name_ar']), value_style),
                    Paragraph(reshape_arabic_text("الصف:"), label_style),
                    Paragraph(school_settings.get('academic_year', '2024-2025'), value_style),
                    Paragraph(reshape_arabic_text("العام الدراسي:"), label_style)
                ],
            ]
        else:
            # English: Label on left, value on right
            customer_data = [
                [Paragraph("Name:", label_style),
                 Paragraph(student_name, value_style),
                 Paragraph("Student ID:", label_style),
                 Paragraph(student['student_number'], value_style)],
                [Paragraph("Class:", label_style),
                 Paragraph(student['class_name_en'], value_style),
                 Paragraph("Academic Year:", label_style),
                 Paragraph(school_settings.get('academic_year', '2024-2025'), value_style)],
            ]
        
        customer_table = Table(customer_data, colWidths=[2.3*inch, 1.2*inch, 2.3*inch, 1.2*inch] if is_arabic else [1.2*inch, 2.3*inch, 1.2*inch, 2.3*inch])
        customer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_grey),
            ('BOX', (0, 0), (-1, -1), 0.5, medium_grey),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT' if is_arabic else 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT' if is_arabic else 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT if is_arabic else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(customer_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Payment Details Table
        story.append(Paragraph(reshape_arabic_text("تفاصيل الدفع") if is_arabic else "PAYMENT DETAILS", header_style))
        story.append(Spacer(1, 0.1*inch))
        
        fee_name = fee_category['category_name_ar'] if is_arabic else fee_category['category_name_en']
        amount = f"{float(payment['amount_paid']):,.2f}"
        
        if is_arabic:
            payment_data = [
                [Paragraph(reshape_arabic_text("البيان"), bold_label_style),
                 Paragraph(reshape_arabic_text("المبلغ"), bold_label_style)],
                [Paragraph(reshape_arabic_text(fee_name), label_style),
                 Paragraph(f"{amount} SDG", value_style)],
            ]
        else:
            payment_data = [
                [Paragraph("Description", bold_label_style),
                 Paragraph("Amount", bold_label_style)],
                [Paragraph(fee_name, label_style),
                 Paragraph(f"{amount} SDG", value_style)],
            ]
        
        # Add total row
        if is_arabic:
            payment_data.append(
                [Paragraph(reshape_arabic_text("الإجمالي"), bold_label_style),
                 Paragraph(f"{amount} SDG", bold_label_style)]
            )
        else:
            payment_data.append(
                [Paragraph("TOTAL", bold_label_style),
                 Paragraph(f"{amount} SDG", bold_label_style)]
            )
        
        payment_table = Table(payment_data, colWidths=[4.5*inch, 1.5*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, 1), light_grey),
            ('BACKGROUND', (0, -1), (-1, -1), light_grey),
            ('BOX', (0, 0), (-1, -1), 1, medium_grey),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT' if is_arabic else 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT if is_arabic else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(payment_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Payment Method
        if payment['payment_method'] == 'cash':
            method = reshape_arabic_text('نقداً') if is_arabic else 'Cash'
        elif payment['payment_method'] == 'bank_transfer':
            method = reshape_arabic_text('تحويل بنكي') if is_arabic else 'Bank Transfer'
        else:
            method = reshape_arabic_text('شيك') if is_arabic else 'Check'
        
        if is_arabic:
            method_data = [[
                Paragraph(method, value_style),
                Paragraph(reshape_arabic_text("طريقة الدفع:"), bold_label_style)
            ]]
        else:
            method_data = [[
                Paragraph("Payment Method:", bold_label_style),
                Paragraph(method, value_style)
            ]]
        
        method_table = Table(method_data, colWidths=[1.5*inch, 4.5*inch])
        method_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_grey),
            ('BOX', (0, 0), (-1, -1), 0.5, medium_grey),
            ('ALIGN', (0, 0), (0, 0), 'RIGHT' if is_arabic else 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(method_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Signatures
        if is_arabic:
            signature_data = [
                [Paragraph(reshape_arabic_text("المحاسب"), bold_label_style),
                 Paragraph(reshape_arabic_text("المستلم"), bold_label_style),
                 Paragraph(reshape_arabic_text("ختم المدرسة"), bold_label_style)],
                [Paragraph("__________________", label_style),
                 Paragraph("__________________", label_style),
                 Paragraph("__________________", label_style)],
                [Paragraph(reshape_arabic_text(user['full_name_ar']), label_style),
                 Paragraph("", label_style),
                 Paragraph("", label_style)],
            ]
        else:
            signature_data = [
                [Paragraph("Accountant", bold_label_style),
                 Paragraph("Received by", bold_label_style),
                 Paragraph("School Stamp", bold_label_style)],
                [Paragraph("__________________", label_style),
                 Paragraph("__________________", label_style),
                 Paragraph("__________________", label_style)],
                [Paragraph(user['full_name_ar'], label_style),
                 Paragraph("", label_style),
                 Paragraph("", label_style)],
            ]
        
        signature_table = Table(signature_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), ARABIC_FONT if is_arabic else 'Helvetica'),
        ]))
        story.append(signature_table)
        
        # Footer
        story.append(Spacer(1, 0.2*inch))
        thank_you = reshape_arabic_text("شكراً لثقتكم") if is_arabic else "Thank you for your business"
        story.append(Paragraph(thank_you, center_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer