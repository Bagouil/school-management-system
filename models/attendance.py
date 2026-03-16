from database.db_config import get_db
from datetime import datetime, date

class StudentAttendance:
    @staticmethod
    def mark(data):
        """Mark student attendance"""
        db = get_db()
        cursor = db.cursor()
        
        # Check if attendance already marked for this student on this date
        cursor.execute("""
        SELECT attendance_id FROM StudentAttendance 
        WHERE student_id = ? AND attendance_date = ?
        """, (data['student_id'], data['attendance_date']))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing attendance
            query = """
            UPDATE StudentAttendance
            SET status = ?, remarks = ?, marked_by = ?, marked_at = GETDATE()
            WHERE attendance_id = ?
            """
            cursor.execute(query, (
                data['status'],
                data.get('remarks', ''),
                data['marked_by'],
                existing[0]
            ))
        else:
            # Insert new attendance
            query = """
            INSERT INTO StudentAttendance (student_id, class_id, attendance_date, status, remarks, marked_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                data['student_id'],
                data['class_id'],
                data['attendance_date'],
                data['status'],
                data.get('remarks', ''),
                data['marked_by']
            ))
        
        db.commit()
        return True
    
    @staticmethod
    def get_class_attendance(class_id, attendance_date):
        """Get attendance for a class on a specific date"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        SELECT s.student_id, s.first_name_ar, s.last_name_ar, s.student_number,
               sa.status, sa.remarks, sa.attendance_id
        FROM Students s
        LEFT JOIN StudentAttendance sa ON s.student_id = sa.student_id 
            AND sa.attendance_date = ? AND sa.class_id = ?
        WHERE s.current_class_id = ? AND s.status = 'active'
        ORDER BY s.first_name_ar
        """
        
        cursor.execute(query, (attendance_date, class_id, class_id))
        columns = [column[0] for column in cursor.description]
        attendance = []
        
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            record['status'] = record['status'] or 'absent'  # Default to absent if not marked
            attendance.append(record)
        
        return attendance
    
    @staticmethod
    def get_student_attendance(student_id, start_date=None, end_date=None):
        """Get attendance for a student over a period"""
        db = get_db()
        cursor = db.cursor()
        
        if start_date and end_date:
            query = """
            SELECT * FROM StudentAttendance
            WHERE student_id = ? AND attendance_date BETWEEN ? AND ?
            ORDER BY attendance_date DESC
            """
            cursor.execute(query, (student_id, start_date, end_date))
        else:
            query = """
            SELECT * FROM StudentAttendance
            WHERE student_id = ?
            ORDER BY attendance_date DESC
            """
            cursor.execute(query, (student_id,))
        
        columns = [column[0] for column in cursor.description]
        attendance = []
        
        for row in cursor.fetchall():
            attendance.append(dict(zip(columns, row)))
        
        return attendance
    
    @staticmethod
    def get_monthly_report(class_id, year, month):
        """Get monthly attendance report for a class"""
        db = get_db()
        cursor = db.cursor()
        
        # Get all students in class
        cursor.execute("""
        SELECT student_id, first_name_ar, last_name_ar, student_number
        FROM Students
        WHERE current_class_id = ? AND status = 'active'
        ORDER BY first_name_ar
        """, (class_id,))
        
        students = cursor.fetchall()
        
        # Get all attendance for the month
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        report = []
        for student in students:
            cursor.execute("""
            SELECT attendance_date, status
            FROM StudentAttendance
            WHERE student_id = ? AND attendance_date >= ? AND attendance_date < ?
            ORDER BY attendance_date
            """, (student[0], start_date, end_date))
            
            attendance_records = cursor.fetchall()
            
            # Calculate statistics
            total_days = len(attendance_records)
            present = sum(1 for r in attendance_records if r[1] == 'present')
            absent = sum(1 for r in attendance_records if r[1] == 'absent')
            late = sum(1 for r in attendance_records if r[1] == 'late')
            excused = sum(1 for r in attendance_records if r[1] == 'excused')
            
            attendance_percentage = (present / total_days * 100) if total_days > 0 else 0
            
            report.append({
                'student_id': student[0],
                'name_ar': f"{student[1]} {student[2]}",
                'student_number': student[3],
                'total_days': total_days,
                'present': present,
                'absent': absent,
                'late': late,
                'excused': excused,
                'attendance_percentage': round(attendance_percentage, 1),
                'records': attendance_records
            })
        
        return report


class TeacherAttendance:
    @staticmethod
    def mark(data):
        """Mark teacher attendance"""
        db = get_db()
        cursor = db.cursor()
        
        # Check if attendance already marked
        cursor.execute("""
        SELECT attendance_id FROM TeacherAttendance 
        WHERE teacher_id = ? AND attendance_date = ?
        """, (data['teacher_id'], data['attendance_date']))
        
        existing = cursor.fetchone()
        
        if existing:
            query = """
            UPDATE TeacherAttendance
            SET status = ?, remarks = ?, marked_by = ?, marked_at = GETDATE()
            WHERE attendance_id = ?
            """
            cursor.execute(query, (
                data['status'],
                data.get('remarks', ''),
                data['marked_by'],
                existing[0]
            ))
        else:
            query = """
            INSERT INTO TeacherAttendance (teacher_id, attendance_date, status, remarks, marked_by)
            VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                data['teacher_id'],
                data['attendance_date'],
                data['status'],
                data.get('remarks', ''),
                data['marked_by']
            ))
        
        db.commit()
        return True
    
    @staticmethod
    def get_daily_attendance(attendance_date):
        """Get attendance for all teachers on a specific date"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        SELECT t.teacher_id, t.first_name_ar, t.last_name_ar, t.teacher_number,
               ta.status, ta.remarks, ta.attendance_id
        FROM Teachers t
        LEFT JOIN TeacherAttendance ta ON t.teacher_id = ta.teacher_id 
            AND ta.attendance_date = ?
        WHERE t.status = 'active'
        ORDER BY t.first_name_ar
        """
        
        cursor.execute(query, (attendance_date,))
        columns = [column[0] for column in cursor.description]
        attendance = []
        
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            record['status'] = record['status'] or 'absent'
            attendance.append(record)
        
        return attendance
    
    @staticmethod
    def get_teacher_attendance(teacher_id, start_date=None, end_date=None):
        """Get attendance for a specific teacher"""
        db = get_db()
        cursor = db.cursor()
        
        if start_date and end_date:
            query = """
            SELECT * FROM TeacherAttendance
            WHERE teacher_id = ? AND attendance_date BETWEEN ? AND ?
            ORDER BY attendance_date DESC
            """
            cursor.execute(query, (teacher_id, start_date, end_date))
        else:
            query = """
            SELECT * FROM TeacherAttendance
            WHERE teacher_id = ?
            ORDER BY attendance_date DESC
            """
            cursor.execute(query, (teacher_id,))
        
        columns = [column[0] for column in cursor.description]
        attendance = []
        
        for row in cursor.fetchall():
            attendance.append(dict(zip(columns, row)))
        
        return attendance