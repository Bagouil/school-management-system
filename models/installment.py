from database.db_config import get_db
from datetime import datetime, timedelta

class InstallmentPlan:
    @staticmethod
    def get_all():
        """Get all installment plans"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("SELECT * FROM InstallmentPlans WHERE is_active = 1 ORDER BY number_of_installments")
        columns = [column[0] for column in cursor.description]
        plans = []
        
        for row in cursor.fetchall():
            plans.append(dict(zip(columns, row)))
        
        cursor.close()
        return plans
    
    @staticmethod
    def get_by_id(plan_id):
        """Get installment plan by ID"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("SELECT * FROM InstallmentPlans WHERE plan_id = ?", (plan_id,))
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None


class StudentInstallment:
    @staticmethod
    def create_installments(student_fee_id, plan_id, total_amount, start_date):
        """Create installments for a student fee"""
        db = get_db()
        cursor = db.cursor()
        
        # Get plan details
        cursor.execute("SELECT number_of_installments FROM InstallmentPlans WHERE plan_id = ?", (plan_id,))
        plan = cursor.fetchone()
        if not plan:
            return False
        
        num_installments = plan[0]
        installment_amount = total_amount / num_installments
        
        # Create installments
        for i in range(1, num_installments + 1):
            due_date = datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=30 * i)
            cursor.execute("""
            INSERT INTO StudentInstallments (student_fee_id, installment_number, amount, due_date, status)
            VALUES (?, ?, ?, ?, 'pending')
            """, (student_fee_id, i, installment_amount, due_date.strftime('%Y-%m-%d')))
        
        # Update student fee
        cursor.execute("""
        UPDATE StudentFees 
        SET installment_plan_id = ?, allow_partial_payment = 1 
        WHERE student_fee_id = ?
        """, (plan_id, student_fee_id))
        
        db.commit()
        cursor.close()
        return True
    
    @staticmethod
    def get_student_installments(student_fee_id):
        """Get all installments for a student fee"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
        SELECT * FROM StudentInstallments 
        WHERE student_fee_id = ? 
        ORDER BY installment_number
        """, (student_fee_id,))
        
        columns = [column[0] for column in cursor.description]
        installments = []
        
        for row in cursor.fetchall():
            inst = dict(zip(columns, row))
            inst['remaining'] = inst['amount'] - inst['paid_amount']
            inst['is_overdue'] = inst['due_date'] < datetime.now().date() and inst['status'] != 'paid'
            installments.append(inst)
        
        cursor.close()
        return installments
    
    @staticmethod
    def make_installment_payment(installment_id, amount_paid, payment_date, payment_method, received_by, notes=''):
        """Make a payment towards an installment"""
        db = get_db()
        cursor = db.cursor()
        
        # Get installment details
        cursor.execute("""
        SELECT si.*, sf.student_fee_id 
        FROM StudentInstallments si
        JOIN StudentFees sf ON si.student_fee_id = sf.student_fee_id
        WHERE si.installment_id = ?
        """, (installment_id,))
        
        installment = cursor.fetchone()
        if not installment:
            return None
        
        new_paid = installment[4] + amount_paid
        status = 'paid' if new_paid >= installment[3] else 'partial'
        
        # Update installment
        cursor.execute("""
        UPDATE StudentInstallments 
        SET paid_amount = ?, status = ?, payment_date = ?
        WHERE installment_id = ?
        """, (new_paid, status, payment_date, installment_id))
        
        # Generate receipt number
        year = datetime.now().strftime('%Y')
        cursor.execute("""
            SELECT ISNULL(MAX(CAST(RIGHT(receipt_number, 6) AS INT)), 0) + 1 
            FROM FeePayments 
            WHERE receipt_number LIKE ?
        """, (f"RCP-{year}%",))
        
        next_num = cursor.fetchone()[0]
        receipt_number = f"RCP-{year}-{str(next_num).zfill(6)}"
        
        # Record payment in FeePayments
        cursor.execute("""
        INSERT INTO FeePayments (student_fee_id, payment_date, amount_paid, 
                                payment_method, receipt_number, received_by, notes)
        OUTPUT INSERTED.payment_id
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            installment[6],  # student_fee_id
            payment_date,
            amount_paid,
            payment_method,
            receipt_number,
            received_by,
            f"Installment {installment[2]} payment: {notes}"
        ))
        
        payment_id = cursor.fetchone()[0]
        
        # Check if all installments are paid
        cursor.execute("""
        SELECT COUNT(*) FROM StudentInstallments 
        WHERE student_fee_id = ? AND status != 'paid'
        """, (installment[6],))
        
        pending_count = cursor.fetchone()[0]
        
        if pending_count == 0:
            cursor.execute("UPDATE StudentFees SET status = 'paid' WHERE student_fee_id = ?", (installment[6],))
        
        db.commit()
        cursor.close()
        
        return {'payment_id': payment_id, 'receipt_number': receipt_number}
    
    @staticmethod
    def get_installment_summary(student_fee_id):
        """Get summary of installments for a fee"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
        SELECT 
            COUNT(*) as total_installments,
            SUM(amount) as total_amount,
            SUM(paid_amount) as total_paid,
            COUNT(CASE WHEN status = 'paid' THEN 1 END) as paid_installments,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_installments,
            COUNT(CASE WHEN due_date < GETDATE() AND status != 'paid' THEN 1 END) as overdue_installments
        FROM StudentInstallments
        WHERE student_fee_id = ?
        """, (student_fee_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return {
                'total_installments': row[0],
                'total_amount': float(row[1]),
                'total_paid': float(row[2]),
                'paid_installments': row[3],
                'pending_installments': row[4],
                'overdue_installments': row[5],
                'balance': float(row[1] - row[2])
            }
        return None