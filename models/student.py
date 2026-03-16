from database.db_config import get_db
from datetime import datetime

class Student:
    @staticmethod
    def create(data):
        """Create new student"""
        db = get_db()
        cursor = db.cursor()
        
        # Generate student number (Year + sequential number)
        year = datetime.now().strftime('%Y')
        cursor.execute("""
            SELECT ISNULL(MAX(CAST(RIGHT(student_number, 4) AS INT)), 0) + 1 
            FROM Students 
            WHERE student_number LIKE ?
        """, (f"{year}%",))
        
        next_num = cursor.fetchone()[0]
        student_number = f"{year}{str(next_num).zfill(4)}"
        
        query = """
        INSERT INTO Students (
            student_number, first_name_ar, last_name_ar, first_name_en, last_name_en,
            birth_date, gender, nationality, address, phone, email,
            enrollment_date, current_class_id, academic_year_id, status
        ) OUTPUT INSERTED.student_id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            student_number,
            data['first_name_ar'],
            data['last_name_ar'],
            data.get('first_name_en', ''),
            data.get('last_name_en', ''),
            data['birth_date'],
            data['gender'],
            data.get('nationality', 'Sudanese'),
            data['address'],
            data['phone'],
            data.get('email', ''),
            data['enrollment_date'],
            data['class_id'],
            data['academic_year_id'],
            'active'
        ))
        
        student_id = cursor.fetchone()[0]
        
        # Add guardian if provided
        if data.get('guardian_name_ar'):
            cursor.execute("""
            INSERT INTO Guardians (
                student_id, relationship_ar, relationship_en, full_name_ar, full_name_en,
                occupation, phone, address, is_primary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student_id,
                data.get('guardian_relation_ar', 'أب'),
                data.get('guardian_relation_en', 'Father'),
                data['guardian_name_ar'],
                data.get('guardian_name_en', ''),
                data.get('guardian_occupation', ''),
                data['guardian_phone'],
                data.get('guardian_address', ''),
                1
            ))
        
        db.commit()
        return student_id
    
    @staticmethod
    def get_all():
        """Get all students"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        SELECT s.*, c.class_name_ar, c.class_name_en, c.class_id
        FROM Students s
        LEFT JOIN Classes c ON s.current_class_id = c.class_id
        WHERE s.status = 'active'
        ORDER BY s.student_id DESC
        """
        
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        students = []
        
        for row in cursor.fetchall():
            students.append(dict(zip(columns, row)))
        
        

        return students
    
    @staticmethod
    def get_by_id(student_id):
        """Get student by ID"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        SELECT s.*, c.class_name_ar, c.class_name_en, c.class_id,
               g.grade_name_ar, g.grade_name_en, g.grade_order
        FROM Students s
        LEFT JOIN Classes c ON s.current_class_id = c.class_id
        LEFT JOIN GradeLevels g ON c.grade_id = g.grade_id
        WHERE s.student_id = ?
        """
        
        cursor.execute(query, (student_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None
    
    @staticmethod
    def update(student_id, data):
        """Update student information"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        UPDATE Students
        SET first_name_ar = ?, last_name_ar = ?, first_name_en = ?, last_name_en = ?,
            birth_date = ?, gender = ?, nationality = ?, address = ?, phone = ?,
            email = ?, current_class_id = ?
        WHERE student_id = ?
        """
        
        cursor.execute(query, (
            data['first_name_ar'],
            data['last_name_ar'],
            data.get('first_name_en', ''),
            data.get('last_name_en', ''),
            data['birth_date'],
            data['gender'],
            data.get('nationality', 'Sudanese'),
            data['address'],
            data['phone'],
            data.get('email', ''),
            data['class_id'],
            student_id
        ))
        
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def get_guardians(student_id):
        """Get guardians for a student"""
        db = get_db()
        cursor = db.cursor()
        
        query = "SELECT * FROM Guardians WHERE student_id = ? ORDER BY is_primary DESC"
        cursor.execute(query, (student_id,))
        
        columns = [column[0] for column in cursor.description]
        guardians = []
        
        for row in cursor.fetchall():
            guardians.append(dict(zip(columns, row)))
        
        return guardians
    
    @staticmethod
    def delete(student_id):
        """Soft delete a student (mark as withdrawn)"""
        db = get_db()
        cursor = db.cursor()
        
        query = "UPDATE Students SET status = 'withdrawn' WHERE student_id = ?"
        cursor.execute(query, (student_id,))
        db.commit()
        
        return cursor.rowcount > 0
    
    @staticmethod
    def update_image(student_id, image_path):
        """Update student profile image"""
        db = get_db()
        cursor = db.cursor()
        
        # Get old image path to delete later
        cursor.execute("SELECT student_image FROM Students WHERE student_id = ?", (student_id,))
        old_image = cursor.fetchone()
        
        cursor.execute("UPDATE Students SET student_image = ? WHERE student_id = ?", 
                      (image_path, student_id))
        db.commit()
        
        return old_image[0] if old_image else None
    
    @staticmethod
    def get_fee_summary(student_id):
        """Get fee summary for a student"""
        db = get_db()
        cursor = db.cursor()
        
        # First, get the total paid per fee using a subquery
        cursor.execute("""
        SELECT 
            COUNT(*) as total_fees,
            ISNULL(SUM(sf.amount), 0) as total_amount,
            ISNULL(SUM(sf.discount_amount), 0) as total_discount,
            ISNULL(SUM(fp.total_paid), 0) as total_paid,
            COUNT(CASE WHEN sf.status = 'paid' THEN 1 END) as paid_count,
            COUNT(CASE WHEN sf.status = 'pending' THEN 1 END) as pending_count,
            COUNT(CASE WHEN sf.status = 'partial' THEN 1 END) as partial_count,
            COUNT(CASE WHEN sf.status = 'overdue' THEN 1 END) as overdue_count
        FROM StudentFees sf
        LEFT JOIN (
            SELECT student_fee_id, SUM(amount_paid) as total_paid
            FROM FeePayments
            GROUP BY student_fee_id
        ) fp ON sf.student_fee_id = fp.student_fee_id
        WHERE sf.student_id = ?
        """, (student_id,))
        
        row = cursor.fetchone()
        if row:
            summary = {
                'total_fees': row[0],
                'total_amount': float(row[1]),
                'total_discount': float(row[2]),
                'total_paid': float(row[3]),
                'balance': float(row[1] - row[2] - row[3]),
                'paid_count': row[4],
                'pending_count': row[5],
                'partial_count': row[6],
                'overdue_count': row[7]
            }
            cursor.close()
            return summary
        
        cursor.close()
        return None
    
    @staticmethod
    def get_attendance_summary(student_id):
        """Get attendance summary for a student"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
        SELECT 
            COUNT(*) as total_days,
            COUNT(CASE WHEN status = 'present' THEN 1 END) as present_days,
            COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_days,
            COUNT(CASE WHEN status = 'late' THEN 1 END) as late_days,
            COUNT(CASE WHEN status = 'excused' THEN 1 END) as excused_days
        FROM StudentAttendance
        WHERE student_id = ?
        """, (student_id,))
        
        row = cursor.fetchone()
        if row:
            summary = {
                'total_days': row[0],
                'present': row[1],
                'absent': row[2],
                'late': row[3],
                'excused': row[4],
                'attendance_percentage': round((row[1] / row[0] * 100), 1) if row[0] > 0 else 0
            }
            cursor.close()
            return summary
        
        cursor.close()
        return None