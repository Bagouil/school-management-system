from database.db_config import get_db
from datetime import datetime

class FeeCategory:
    @staticmethod
    def get_all():
        """Get all fee categories"""
        db = get_db()
        cursor = db.cursor()
        
        query = "SELECT * FROM FeeCategories ORDER BY category_name_ar"
        cursor.execute(query)
        
        columns = [column[0] for column in cursor.description]
        categories = []
        
        for row in cursor.fetchall():
            categories.append(dict(zip(columns, row)))
        
        return categories
    
    @staticmethod
    def get_by_id(category_id):
        """Get fee category by ID"""
        db = get_db()
        cursor = db.cursor()
        
        query = "SELECT * FROM FeeCategories WHERE fee_category_id = ?"
        cursor.execute(query, (category_id,))
        
        row = cursor.fetchone()
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None
    
    @staticmethod
    def create(data):
        """Create new fee category"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        INSERT INTO FeeCategories (category_name_ar, category_name_en, description, amount, is_annual, is_mandatory)
        OUTPUT INSERTED.fee_category_id
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            data['category_name_ar'],
            data['category_name_en'],
            data.get('description', ''),
            data['amount'],
            1 if data.get('is_annual') else 0,
            1 if data.get('is_mandatory', True) else 0
        ))
        
        category_id = cursor.fetchone()[0]
        db.commit()
        return category_id
    
    @staticmethod
    def update(category_id, data):
        """Update fee category"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        UPDATE FeeCategories
        SET category_name_ar = ?, category_name_en = ?, description = ?,
            amount = ?, is_annual = ?, is_mandatory = ?
        WHERE fee_category_id = ?
        """
        
        cursor.execute(query, (
            data['category_name_ar'],
            data['category_name_en'],
            data.get('description', ''),
            data['amount'],
            1 if data.get('is_annual') else 0,
            1 if data.get('is_mandatory', True) else 0,
            category_id
        ))
        
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete(category_id):
        """Delete fee category"""
        db = get_db()
        cursor = db.cursor()
        
        # Check if category is used in student fees
        cursor.execute("SELECT COUNT(*) FROM StudentFees WHERE fee_category_id = ?", (category_id,))
        if cursor.fetchone()[0] > 0:
            return False  # Cannot delete if in use
        
        cursor.execute("DELETE FROM FeeCategories WHERE fee_category_id = ?", (category_id,))
        db.commit()
        return cursor.rowcount > 0


class StudentFee:
    @staticmethod
    def get_all(academic_year_id=None):
        """Get all student fees"""
        db = get_db()
        cursor = db.cursor()
        
        if academic_year_id:
            query = """
            SELECT sf.*, s.first_name_ar, s.last_name_ar, s.student_number,
                   fc.category_name_ar, fc.category_name_en,
                   c.class_name_ar
            FROM StudentFees sf
            JOIN Students s ON sf.student_id = s.student_id
            JOIN FeeCategories fc ON sf.fee_category_id = fc.fee_category_id
            JOIN Classes c ON s.current_class_id = c.class_id
            WHERE sf.academic_year_id = ?
            ORDER BY sf.due_date
            """
            cursor.execute(query, (academic_year_id,))
        else:
            query = """
            SELECT sf.*, s.first_name_ar, s.last_name_ar, s.student_number,
                   fc.category_name_ar, fc.category_name_en,
                   c.class_name_ar
            FROM StudentFees sf
            JOIN Students s ON sf.student_id = s.student_id
            JOIN FeeCategories fc ON sf.fee_category_id = fc.fee_category_id
            JOIN Classes c ON s.current_class_id = c.class_id
            ORDER BY sf.due_date
            """
            cursor.execute(query)
        
        columns = [column[0] for column in cursor.description]
        fees = []
        
        for row in cursor.fetchall():
            fee = dict(zip(columns, row))
            # Get total paid
            cursor.execute("SELECT SUM(amount_paid) FROM FeePayments WHERE student_fee_id = ?", (fee['student_fee_id'],))
            total_paid = cursor.fetchone()[0] or 0
            fee['total_paid'] = total_paid
            fee['balance'] = fee['amount'] - fee['discount_amount'] - total_paid
            fees.append(fee)
        
        return fees
    
    @staticmethod
    def get_student_fees(student_id, academic_year_id=None):
        """Get fees for a specific student"""
        db = get_db()
        cursor = db.cursor()
        
        if academic_year_id:
            query = """
            SELECT sf.*, fc.category_name_ar, fc.category_name_en, fc.amount as original_amount
            FROM StudentFees sf
            JOIN FeeCategories fc ON sf.fee_category_id = fc.fee_category_id
            WHERE sf.student_id = ? AND sf.academic_year_id = ?
            ORDER BY sf.due_date
            """
            cursor.execute(query, (student_id, academic_year_id))
        else:
            query = """
            SELECT sf.*, fc.category_name_ar, fc.category_name_en, fc.amount as original_amount
            FROM StudentFees sf
            JOIN FeeCategories fc ON sf.fee_category_id = fc.fee_category_id
            WHERE sf.student_id = ?
            ORDER BY sf.due_date
            """
            cursor.execute(query, (student_id,))
        
        columns = [column[0] for column in cursor.description]
        fees = []
        
        for row in cursor.fetchall():
            fee = dict(zip(columns, row))
            # Get payments for this fee
            cursor.execute("""
            SELECT * FROM FeePayments 
            WHERE student_fee_id = ? 
            ORDER BY payment_date
            """, (fee['student_fee_id'],))
            
            payment_columns = [column[0] for column in cursor.description]
            payments = []
            for p_row in cursor.fetchall():
                payments.append(dict(zip(payment_columns, p_row)))
            
            fee['payments'] = payments
            fee['total_paid'] = sum(p['amount_paid'] for p in payments)
            fee['balance'] = fee['amount'] - fee['discount_amount'] - fee['total_paid']
            fees.append(fee)
        
        return fees
    
    @staticmethod
    def create(data):
        """Create student fee"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        INSERT INTO StudentFees (student_id, fee_category_id, academic_year_id, 
                                amount, discount_amount, due_date, status, notes)
        OUTPUT INSERTED.student_fee_id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            data['student_id'],
            data['fee_category_id'],
            data['academic_year_id'],
            data['amount'],
            data.get('discount_amount', 0),
            data['due_date'],
            'pending',
            data.get('notes', '')
        ))
        
        fee_id = cursor.fetchone()[0]
        db.commit()
        return fee_id
    
    @staticmethod
    def add_payment(data):
        """Add payment to student fee"""
        db = get_db()
        cursor = db.cursor()
        
        # Generate receipt number
        year = datetime.now().strftime('%Y')
        cursor.execute("""
            SELECT ISNULL(MAX(CAST(RIGHT(receipt_number, 6) AS INT)), 0) + 1 
            FROM FeePayments 
            WHERE receipt_number LIKE ?
        """, (f"RCP-{year}%",))
        
        next_num = cursor.fetchone()[0]
        receipt_number = f"RCP-{year}-{str(next_num).zfill(6)}"
        
        query = """
        INSERT INTO FeePayments (student_fee_id, payment_date, amount_paid, 
                                payment_method, receipt_number, received_by, notes)
        OUTPUT INSERTED.payment_id
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            data['student_fee_id'],
            data['payment_date'],
            data['amount_paid'],
            data['payment_method'],
            receipt_number,
            data['received_by'],
            data.get('notes', '')
        ))
        
        payment_id = cursor.fetchone()[0]
        
        # Update fee status
        cursor.execute("""
            SELECT SUM(amount_paid) as total_paid, amount, discount_amount
            FROM FeePayments fp
            JOIN StudentFees sf ON fp.student_fee_id = sf.student_fee_id
            WHERE fp.student_fee_id = ?
            GROUP BY sf.amount, sf.discount_amount
        """, (data['student_fee_id'],))
        
        result = cursor.fetchone()
        if result:
            total_paid = result[0]
            amount = result[1]
            discount = result[2]
            net_amount = amount - discount
            
            if total_paid >= net_amount:
                status = 'paid'
            elif total_paid > 0:
                status = 'partial'
            else:
                status = 'pending'
            
            cursor.execute("UPDATE StudentFees SET status = ? WHERE student_fee_id = ?", 
                         (status, data['student_fee_id']))
        
        db.commit()
        return payment_id, receipt_number
    
    @staticmethod
    def get_payments(student_fee_id=None):
        """Get payments"""
        db = get_db()
        cursor = db.cursor()
        
        if student_fee_id:
            query = """
            SELECT fp.*, u.username, u.full_name_ar,
                   s.first_name_ar, s.last_name_ar, s.student_number
            FROM FeePayments fp
            JOIN StudentFees sf ON fp.student_fee_id = sf.student_fee_id
            JOIN Students s ON sf.student_id = s.student_id
            JOIN Users u ON fp.received_by = u.user_id
            WHERE fp.student_fee_id = ?
            ORDER BY fp.payment_date DESC
            """
            cursor.execute(query, (student_fee_id,))
        else:
            query = """
            SELECT fp.*, u.username, u.full_name_ar,
                   s.first_name_ar, s.last_name_ar, s.student_number,
                   fc.category_name_ar
            FROM FeePayments fp
            JOIN StudentFees sf ON fp.student_fee_id = sf.student_fee_id
            JOIN Students s ON sf.student_id = s.student_id
            JOIN FeeCategories fc ON sf.fee_category_id = fc.fee_category_id
            JOIN Users u ON fp.received_by = u.user_id
            ORDER BY fp.payment_date DESC
            """
            cursor.execute(query)
        
        columns = [column[0] for column in cursor.description]
        payments = []
        
        for row in cursor.fetchall():
            payments.append(dict(zip(columns, row)))
        
        return payments


class Expense:
    @staticmethod
    def get_all():
        """Get all expenses"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        SELECT e.*, u.username, u.full_name_ar as entered_by_name,
               a.username as approved_by_name
        FROM Expenses e
        LEFT JOIN Users u ON e.entered_by = u.user_id
        LEFT JOIN Users a ON e.approved_by = a.user_id
        ORDER BY e.expense_date DESC
        """
        
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        expenses = []
        
        for row in cursor.fetchall():
            expenses.append(dict(zip(columns, row)))
        
        return expenses
    
    @staticmethod
    def create(data):
        """Create new expense"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        INSERT INTO Expenses (expense_date, expense_category, description, amount,
                            payment_method, reference_number, approved_by, entered_by, notes)
        OUTPUT INSERTED.expense_id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            data['expense_date'],
            data['expense_category'],
            data['description'],
            data['amount'],
            data['payment_method'],
            data.get('reference_number', ''),
            data.get('approved_by'),
            data['entered_by'],
            data.get('notes', '')
        ))
        
        expense_id = cursor.fetchone()[0]
        db.commit()
        return expense_id
    
    @staticmethod
    def get_summary(start_date=None, end_date=None):
        """Get financial summary"""
        db = get_db()
        cursor = db.cursor()
        
        # Total fees collected
        if start_date and end_date:
            cursor.execute("""
            SELECT ISNULL(SUM(amount_paid), 0) as total_collected
            FROM FeePayments
            WHERE payment_date BETWEEN ? AND ?
            """, (start_date, end_date))
        else:
            cursor.execute("SELECT ISNULL(SUM(amount_paid), 0) as total_collected FROM FeePayments")
        
        total_collected = cursor.fetchone()[0]
        
        # Total expenses
        if start_date and end_date:
            cursor.execute("""
            SELECT ISNULL(SUM(amount), 0) as total_expenses
            FROM Expenses
            WHERE expense_date BETWEEN ? AND ?
            """, (start_date, end_date))
        else:
            cursor.execute("SELECT ISNULL(SUM(amount), 0) as total_expenses FROM Expenses")
        
        total_expenses = cursor.fetchone()[0]
        
        # Pending fees
        cursor.execute("""
        SELECT ISNULL(SUM(amount - ISNULL(discount_amount, 0)), 0) as total_pending
        FROM StudentFees
        WHERE status IN ('pending', 'partial')
        """)
        
        total_pending = cursor.fetchone()[0]
        
        # Get payments already made on pending fees
        cursor.execute("""
        SELECT ISNULL(SUM(fp.amount_paid), 0)
        FROM StudentFees sf
        JOIN FeePayments fp ON sf.student_fee_id = fp.student_fee_id
        WHERE sf.status IN ('pending', 'partial')
        """)
        
        paid_on_pending = cursor.fetchone()[0]
        total_pending = total_pending - paid_on_pending
        
        return {
            'total_collected': float(total_collected),
            'total_expenses': float(total_expenses),
            'net_income': float(total_collected - total_expenses),
            'pending_fees': float(total_pending)
        }