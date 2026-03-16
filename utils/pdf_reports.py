from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import os
from datetime import datetime

class PDFReportGenerator:
    @staticmethod
    def generate_student_report(students, title="تقرير الطلاب"):
        """Generate PDF report for students"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#875A7B'),
            alignment=1,
            spaceAfter=20
        )
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Table data
        data = [['#', 'الرقم الدراسي', 'الاسم', 'الصف', 'الجنس', 'الهاتف']]
        for i, student in enumerate(students, 1):
            data.append([
                str(i),
                student['student_number'],
                f"{student['first_name_ar']} {student['last_name_ar']}",
                student.get('class_name_ar', ''),
                'ذكر' if student['gender'] == 'male' else 'أنثى',
                student['phone']
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#875A7B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_fees_report(fees, title="تقرير الرسوم"):
        """Generate PDF report for fees"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#28A745'),
            alignment=1,
            spaceAfter=20
        )
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Table data
        data = [['#', 'الرقم الدراسي', 'اسم الطالب', 'الصف', 'نوع الرسوم', 
                 'المبلغ', 'المدفوع', 'المتبقي', 'الحالة']]
        
        total_amount = 0
        total_paid = 0
        total_balance = 0
        
        for i, fee in enumerate(fees, 1):
            data.append([
                str(i),
                fee['student_number'],
                fee['student_name'],
                fee['class_name'],
                fee['fee_type'],
                f"{fee['amount']:,.0f}",
                f"{fee['paid']:,.0f}",
                f"{fee['balance']:,.0f}",
                fee['status']
            ])
            total_amount += fee['amount']
            total_paid += fee['paid']
            total_balance += fee['balance']
        
        # Add totals row
        data.append(['', '', '', '', 'الإجمالي:', 
                    f"{total_amount:,.0f}", f"{total_paid:,.0f}", f"{total_balance:,.0f}", ''])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28A745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        doc.build(story)
        buffer.seek(0)
        return buffer