from database.db_config import get_db

class Subject:
    @staticmethod
    def get_all():
        """Get all active subjects"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
        SELECT s.*, g.grade_name_ar, g.grade_name_en
        FROM Subjects s
        LEFT JOIN GradeLevels g ON s.grade_level_id = g.grade_id
        WHERE s.is_active = 1
        ORDER BY g.grade_order, s.subject_name_ar
        """)
        
        columns = [column[0] for column in cursor.description]
        subjects = []
        
        for row in cursor.fetchall():
            subjects.append(dict(zip(columns, row)))
        
        cursor.close()
        return subjects
    
    @staticmethod
    def get_by_id(subject_id):
        """Get subject by ID"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
        SELECT s.*, g.grade_name_ar, g.grade_name_en
        FROM Subjects s
        LEFT JOIN GradeLevels g ON s.grade_level_id = g.grade_id
        WHERE s.subject_id = ?
        """, (subject_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None
    
    @staticmethod
    def get_by_grade(grade_level_id):
        """Get subjects for a specific grade level"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
        SELECT * FROM Subjects
        WHERE grade_level_id = ? AND is_active = 1
        ORDER BY subject_name_ar
        """, (grade_level_id,))
        
        columns = [column[0] for column in cursor.description]
        subjects = []
        
        for row in cursor.fetchall():
            subjects.append(dict(zip(columns, row)))
        
        cursor.close()
        return subjects
    
    @staticmethod
    def create(data):
        """Create a new subject"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
        INSERT INTO Subjects (subject_name_ar, subject_name_en, subject_code, grade_level_id, is_active)
        OUTPUT INSERTED.subject_id
        VALUES (?, ?, ?, ?, ?)
        """, (
            data['subject_name_ar'],
            data['subject_name_en'],
            data.get('subject_code', ''),
            data['grade_level_id'],
            1
        ))
        
        subject_id = cursor.fetchone()[0]
        db.commit()
        cursor.close()
        return subject_id
    
    @staticmethod
    def update(subject_id, data):
        """Update subject"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
        UPDATE Subjects
        SET subject_name_ar = ?, subject_name_en = ?, subject_code = ?,
            grade_level_id = ?, is_active = ?
        WHERE subject_id = ?
        """, (
            data['subject_name_ar'],
            data['subject_name_en'],
            data.get('subject_code', ''),
            data['grade_level_id'],
            data.get('is_active', 1),
            subject_id
        ))
        
        db.commit()
        rows_affected = cursor.rowcount
        cursor.close()
        return rows_affected > 0
    
    @staticmethod
    def delete(subject_id):
        """Soft delete subject (mark as inactive)"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("UPDATE Subjects SET is_active = 0 WHERE subject_id = ?", (subject_id,))
        db.commit()
        rows_affected = cursor.rowcount
        cursor.close()
        return rows_affected > 0