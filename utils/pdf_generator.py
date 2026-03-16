from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import io
from datetime import datetime

class PDFGenerator:
    @staticmethod
    def generate_student_id_card(student, lang):
        """Generate student ID card PDF"""
        buffer = io.BytesIO()
        
        # Create canvas
        c = canvas.Canvas(buffer, pagesize=(2.5*inch, 3.5*inch))
        
        # Set RTL if Arabic
        if lang.get_direction() == 'rtl':
            # Draw border
            c.setStrokeColor(colors.black)
            c.setLineWidth(2)
            c.rect(5, 5, 2.5*inch-10, 3.5*inch-10)
            
            # School name
            c.setFont("Helvetica-Bold", 10)
            c.drawRightString(2.3*inch, 3.3*inch, "المدرسة الخاصة")
            
            # Student photo placeholder
            c.rect(1.8*inch, 2.5*inch, 0.6*inch, 0.7*inch)
            c.setFont("Helvetica", 6)
            c.drawRightString(2.3*inch, 2.8*inch, "صورة")
            
            # Student info
            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(2.3*inch, 2.3*inch, f"الاسم: {student['first_name_ar']} {student['last_name_ar']}")
            c.drawRightString(2.3*inch, 2.1*inch, f"الصف: {student['class_name_ar']}")
            c.drawRightString(2.3*inch, 1.9*inch, f"الرقم: {student['student_number']}")
            
            # Issue date
            c.setFont("Helvetica", 6)
            c.drawRightString(2.3*inch, 1.5*inch, f"تاريخ الإصدار: {datetime.now().strftime('%Y-%m-%d')}")
            
            # Valid stamp
            c.setFont("Helvetica-Bold", 7)
            c.drawRightString(2.3*inch, 1.2*inch, "صالح للعام 2024-2025")
        else:
            # English version
            c.setStrokeColor(colors.black)
            c.setLineWidth(2)
            c.rect(5, 5, 2.5*inch-10, 3.5*inch-10)
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(0.3*inch, 3.3*inch, "Private School")
            
            c.rect(0.3*inch, 2.5*inch, 0.6*inch, 0.7*inch)
            c.setFont("Helvetica", 6)
            c.drawString(0.5*inch, 2.8*inch, "Photo")
            
            c.setFont("Helvetica-Bold", 8)
            c.drawString(0.3*inch, 2.3*inch, f"Name: {student['first_name_en']} {student['last_name_en']}")
            c.drawString(0.3*inch, 2.1*inch, f"Class: {student['class_name_en']}")
            c.drawString(0.3*inch, 1.9*inch, f"ID: {student['student_number']}")
            
            c.setFont("Helvetica", 6)
            c.drawString(0.3*inch, 1.5*inch, f"Issue Date: {datetime.now().strftime('%Y-%m-%d')}")
            
            c.setFont("Helvetica-Bold", 7)
            c.drawString(0.3*inch, 1.2*inch, "Valid for 2024-2025")
        
        c.save()
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_report_card(student, subjects, results, lang):
        """Generate report card PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # School header
        if lang.get_direction() == 'rtl':
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                fontSize=18
            )
            story.append(Paragraph("المدرسة الخاصة", title_style))
            
            # Student info
            info_style = ParagraphStyle(
                'InfoStyle',
                parent=styles['Normal'],
                alignment=TA_RIGHT,
                fontSize=12,
                rightIndent=20
            )
            story.append(Paragraph(f"اسم الطالب: {student['first_name_ar']} {student['last_name_ar']}", info_style))
            story.append(Paragraph(f"الصف: {student['class_name_ar']}", info_style))
        else:
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                alignment=TA_CENTER,
                fontSize=18
            )
            story.append(Paragraph("Private School", title_style))
            
            info_style = ParagraphStyle(
                'InfoStyle',
                parent=styles['Normal'],
                alignment=TA_LEFT,
                fontSize=12,
                leftIndent=20
            )
            story.append(Paragraph(f"Student Name: {student['first_name_en']} {student['last_name_en']}", info_style))
            story.append(Paragraph(f"Class: {student['class_name_en']}", info_style))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Results table
        if lang.get_direction() == 'rtl':
            data = [['المادة', 'الدرجة', 'التقدير']]
            for subject, result in zip(subjects, results):
                data.append([subject['subject_name_ar'], str(result['score']), result['grade_letter']])
            
            # Add total
            total_score = sum(r['score'] for r in results)
            data.append(['المجموع', str(total_score), ''])
            
            # Calculate percentage
            max_total = len(results) * 100
            percentage = (total_score / max_total) * 100
            data.append(['النسبة المئوية', f"{percentage:.1f}%", ''])
        else:
            data = [['Subject', 'Score', 'Grade']]
            for subject, result in zip(subjects, results):
                data.append([subject['subject_name_en'], str(result['score']), result['grade_letter']])
            
            total_score = sum(r['score'] for r in results)
            data.append(['Total', str(total_score), ''])
            
            max_total = len(results) * 100
            percentage = (total_score / max_total) * 100
            data.append(['Percentage', f"{percentage:.1f}%", ''])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer