import xlsxwriter
import io
from datetime import datetime

class ExcelReportGenerator:
    @staticmethod
    def generate_student_report(students, title="تقرير الطلاب"):
        """Generate Excel report for students"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Students')
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#875A7B',
            'color': 'white',
            'align': 'center',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'align': 'center',
            'border': 1
        })
        
        date_format = workbook.add_format({
            'align': 'center',
            'border': 1,
            'num_format': 'yyyy-mm-dd'
        })
        
        # Headers
        headers = ['#', 'الرقم الدراسي', 'الاسم', 'الصف', 'الجنس', 'تاريخ الميلاد', 'الهاتف', 'البريد', 'تاريخ التسجيل']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Data
        for row, student in enumerate(students, start=1):
            worksheet.write(row, 0, row, cell_format)
            worksheet.write(row, 1, student['student_number'], cell_format)
            worksheet.write(row, 2, f"{student['first_name_ar']} {student['last_name_ar']}", cell_format)
            worksheet.write(row, 3, student.get('class_name_ar', ''), cell_format)
            worksheet.write(row, 4, 'ذكر' if student['gender'] == 'male' else 'أنثى', cell_format)
            worksheet.write(row, 5, student['birth_date'], date_format)
            worksheet.write(row, 6, student['phone'], cell_format)
            worksheet.write(row, 7, student.get('email', ''), cell_format)
            worksheet.write(row, 8, student['enrollment_date'], date_format)
        
        # Adjust column widths
        worksheet.set_column(0, 0, 5)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 2, 25)
        worksheet.set_column(3, 3, 15)
        worksheet.set_column(4, 4, 8)
        worksheet.set_column(5, 5, 12)
        worksheet.set_column(6, 6, 15)
        worksheet.set_column(7, 7, 25)
        worksheet.set_column(8, 8, 12)
        
        workbook.close()
        output.seek(0)
        return output
    
    @staticmethod
    def generate_fees_report(fees, title="تقرير الرسوم"):
        """Generate Excel report for fees"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Fees')
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#28A745',
            'color': 'white',
            'align': 'center',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'align': 'center',
            'border': 1
        })
        
        currency_format = workbook.add_format({
            'align': 'center',
            'border': 1,
            'num_format': '#,##0.00 SDG'
        })
        
        # Headers
        headers = ['#', 'الرقم الدراسي', 'اسم الطالب', 'الصف', 'نوع الرسوم', 
                   'المبلغ', 'المدفوع', 'المتبقي', 'تاريخ الاستحقاق', 'الحالة']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Data
        total_amount = 0
        total_paid = 0
        total_balance = 0
        
        for row, fee in enumerate(fees, start=1):
            worksheet.write(row, 0, row, cell_format)
            worksheet.write(row, 1, fee['student_number'], cell_format)
            worksheet.write(row, 2, fee['student_name'], cell_format)
            worksheet.write(row, 3, fee['class_name'], cell_format)
            worksheet.write(row, 4, fee['fee_type'], cell_format)
            worksheet.write(row, 5, fee['amount'], currency_format)
            worksheet.write(row, 6, fee['paid'], currency_format)
            worksheet.write(row, 7, fee['balance'], currency_format)
            worksheet.write(row, 8, fee['due_date'], cell_format)
            worksheet.write(row, 9, fee['status'], cell_format)
            
            total_amount += fee['amount']
            total_paid += fee['paid']
            total_balance += fee['balance']
        
        # Totals row
        last_row = len(fees) + 1
        worksheet.write(last_row, 4, 'الإجمالي:', header_format)
        worksheet.write(last_row, 5, total_amount, currency_format)
        worksheet.write(last_row, 6, total_paid, currency_format)
        worksheet.write(last_row, 7, total_balance, currency_format)
        
        # Adjust column widths
        worksheet.set_column(0, 0, 5)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 2, 25)
        worksheet.set_column(3, 3, 15)
        worksheet.set_column(4, 4, 20)
        worksheet.set_column(5, 8, 15)
        worksheet.set_column(9, 9, 12)
        
        workbook.close()
        output.seek(0)
        return output
    
    @staticmethod
    def generate_attendance_report(attendance_data, title="تقرير الحضور"):
        """Generate Excel report for attendance"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Attendance')
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#17A2B8',
            'color': 'white',
            'align': 'center',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'align': 'center',
            'border': 1
        })
        
        # Headers
        headers = ['#', 'الرقم الدراسي', 'اسم الطالب', 'الصف', 'عدد أيام الحضور', 
                   'عدد أيام الغياب', 'نسبة الحضور']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Data
        for row, record in enumerate(attendance_data, start=1):
            worksheet.write(row, 0, row, cell_format)
            worksheet.write(row, 1, record['student_number'], cell_format)
            worksheet.write(row, 2, record['student_name'], cell_format)
            worksheet.write(row, 3, record['class_name'], cell_format)
            worksheet.write(row, 4, record['present'], cell_format)
            worksheet.write(row, 5, record['absent'], cell_format)
            worksheet.write(row, 6, f"{record['percentage']}%", cell_format)
        
        workbook.close()
        output.seek(0)
        return output
    
    @staticmethod
    def generate_expenses_report(expenses, title="تقرير المصروفات"):
        """Generate Excel report for expenses"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Expenses')
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#DC3545',
            'color': 'white',
            'align': 'center',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'align': 'center',
            'border': 1
        })
        
        currency_format = workbook.add_format({
            'align': 'center',
            'border': 1,
            'num_format': '#,##0.00 SDG'
        })
        
        # Headers
        headers = ['#', 'التاريخ', 'الفئة', 'الوصف', 'المبلغ', 'طريقة الدفع', 'رقم المرجع']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Data
        total_amount = 0
        
        for row, expense in enumerate(expenses, start=1):
            worksheet.write(row, 0, row, cell_format)
            worksheet.write(row, 1, expense['expense_date'], cell_format)
            worksheet.write(row, 2, expense['expense_category'], cell_format)
            worksheet.write(row, 3, expense['description'], cell_format)
            worksheet.write(row, 4, expense['amount'], currency_format)
            worksheet.write(row, 5, expense['payment_method'], cell_format)
            worksheet.write(row, 6, expense.get('reference_number', ''), cell_format)
            
            total_amount += expense['amount']
        
        # Totals row
        last_row = len(expenses) + 1
        worksheet.write(last_row, 3, 'الإجمالي:', header_format)
        worksheet.write(last_row, 4, total_amount, currency_format)
        
        workbook.close()
        output.seek(0)
        return output