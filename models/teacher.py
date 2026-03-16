from database.db_config import get_db

class Teacher:
    @staticmethod
    def get_all():
        """Get all active teachers"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        SELECT * FROM Teachers 
        WHERE status = 'active'
        ORDER BY first_name_ar
        """
        
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        teachers = []
        
        for row in cursor.fetchall():
            teachers.append(dict(zip(columns, row)))
        
        return teachers
    
    @staticmethod
    def get_by_id(teacher_id):
        """Get teacher by ID"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("""
            SELECT teacher_id, teacher_number, first_name_ar, last_name_ar, 
                   first_name_en, last_name_en, birth_date, gender, 
                   qualification, specialization, hire_date, phone, email, 
                   address, salary, national_id, bank_account, status,
                   teacher_image
            FROM Teachers 
            WHERE teacher_id = ?
            """, (teacher_id,))
            
            if cursor.description is None:
                return None
            
            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()
            
            if row:
                teacher = {}
                for i, col in enumerate(columns):
                    teacher[col] = row[i]
                return teacher
            return None
        except Exception as e:
            print(f"Error in get_by_id: {e}")
            return None
        finally:
            cursor.close()
    
    @staticmethod
    def get_teacher_classes(teacher_id, academic_year_id=None):
        """Get classes assigned to a teacher"""
        db = get_db()
        cursor = db.cursor()
        
        if academic_year_id:
            query = """
            SELECT c.*, g.grade_name_ar, g.grade_name_en,
                   tc.is_class_teacher
            FROM TeacherClasses tc
            JOIN Classes c ON tc.class_id = c.class_id
            JOIN GradeLevels g ON c.grade_id = g.grade_id
            WHERE tc.teacher_id = ? AND tc.academic_year_id = ?
            ORDER BY g.grade_order, c.class_name_ar
            """
            cursor.execute(query, (teacher_id, academic_year_id))
        else:
            query = """
            SELECT c.*, g.grade_name_ar, g.grade_name_en,
                   tc.is_class_teacher,
                   ay.year_name_ar, ay.year_name_en
            FROM TeacherClasses tc
            JOIN Classes c ON tc.class_id = c.class_id
            JOIN GradeLevels g ON c.grade_id = g.grade_id
            JOIN AcademicYears ay ON tc.academic_year_id = ay.year_id
            WHERE tc.teacher_id = ?
            ORDER BY ay.year_id DESC, g.grade_order, c.class_name_ar
            """
            cursor.execute(query, (teacher_id,))
        
        columns = [column[0] for column in cursor.description]
        classes = []
        
        for row in cursor.fetchall():
            classes.append(dict(zip(columns, row)))
        
        return classes
    
    @staticmethod
    def get_teacher_subjects(teacher_id, academic_year_id=None):
        """Get subjects assigned to a teacher for specific classes"""
        db = get_db()
        cursor = db.cursor()
        
        if academic_year_id:
            query = """
            SELECT ts.*, s.subject_name_ar, s.subject_name_en, s.subject_code,
                   c.class_name_ar, c.class_name_en, g.grade_name_ar
            FROM TeacherSubjects ts
            JOIN Subjects s ON ts.subject_id = s.subject_id
            JOIN Classes c ON ts.class_id = c.class_id
            JOIN GradeLevels g ON c.grade_id = g.grade_id
            WHERE ts.teacher_id = ? AND ts.academic_year_id = ?
            ORDER BY g.grade_order, c.class_name_ar, s.subject_name_ar
            """
            cursor.execute(query, (teacher_id, academic_year_id))
        else:
            query = """
            SELECT ts.*, s.subject_name_ar, s.subject_name_en, s.subject_code,
                   c.class_name_ar, c.class_name_en, g.grade_name_ar,
                   ay.year_name_ar, ay.year_name_en
            FROM TeacherSubjects ts
            JOIN Subjects s ON ts.subject_id = s.subject_id
            JOIN Classes c ON ts.class_id = c.class_id
            JOIN GradeLevels g ON c.grade_id = g.grade_id
            JOIN AcademicYears ay ON ts.academic_year_id = ay.year_id
            WHERE ts.teacher_id = ?
            ORDER BY ay.year_id DESC, g.grade_order, c.class_name_ar, s.subject_name_ar
            """
            cursor.execute(query, (teacher_id,))
        
        columns = [column[0] for column in cursor.description]
        subjects = []
        
        for row in cursor.fetchall():
            subjects.append(dict(zip(columns, row)))
        
        return subjects
    
    @staticmethod
    def assign_to_class(teacher_id, class_id, academic_year_id, is_class_teacher=False):
        """Assign teacher to a class"""
        db = get_db()
        cursor = db.cursor()
        
        # Check if already assigned
        cursor.execute("""
        SELECT teacher_class_id FROM TeacherClasses 
        WHERE teacher_id = ? AND class_id = ? AND academic_year_id = ?
        """, (teacher_id, class_id, academic_year_id))
        
        if cursor.fetchone():
            # Update existing
            cursor.execute("""
            UPDATE TeacherClasses 
            SET is_class_teacher = ?, assigned_date = GETDATE()
            WHERE teacher_id = ? AND class_id = ? AND academic_year_id = ?
            """, (1 if is_class_teacher else 0, teacher_id, class_id, academic_year_id))
        else:
            # Insert new
            cursor.execute("""
            INSERT INTO TeacherClasses (teacher_id, class_id, academic_year_id, is_class_teacher)
            VALUES (?, ?, ?, ?)
            """, (teacher_id, class_id, academic_year_id, 1 if is_class_teacher else 0))
        
        db.commit()
        return True
    
    @staticmethod
    def assign_subject(teacher_id, subject_id, class_id, academic_year_id):
        """Assign subject to teacher for a specific class"""
        db = get_db()
        cursor = db.cursor()
        
        # Check if already assigned
        cursor.execute("""
        SELECT teacher_subject_id FROM TeacherSubjects 
        WHERE teacher_id = ? AND subject_id = ? AND class_id = ? AND academic_year_id = ?
        """, (teacher_id, subject_id, class_id, academic_year_id))
        
        if cursor.fetchone():
            return False  # Already assigned
        
        cursor.execute("""
        INSERT INTO TeacherSubjects (teacher_id, subject_id, class_id, academic_year_id)
        VALUES (?, ?, ?, ?)
        """, (teacher_id, subject_id, class_id, academic_year_id))
        
        db.commit()
        return True
    
    @staticmethod
    def remove_from_class(teacher_id, class_id, academic_year_id):
        """Remove teacher from class"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
        DELETE FROM TeacherClasses 
        WHERE teacher_id = ? AND class_id = ? AND academic_year_id = ?
        """, (teacher_id, class_id, academic_year_id))
        
        # Also remove subject assignments for this class
        cursor.execute("""
        DELETE FROM TeacherSubjects 
        WHERE teacher_id = ? AND class_id = ? AND academic_year_id = ?
        """, (teacher_id, class_id, academic_year_id))
        
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def get_class_teachers(class_id, academic_year_id):
        """Get teachers assigned to a class"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        SELECT t.*, tc.is_class_teacher,
               STRING_AGG(s.subject_name_ar, ', ') as subjects_ar,
               STRING_AGG(s.subject_name_en, ', ') as subjects_en
        FROM TeacherClasses tc
        JOIN Teachers t ON tc.teacher_id = t.teacher_id
        LEFT JOIN TeacherSubjects ts ON t.teacher_id = ts.teacher_id 
            AND ts.class_id = tc.class_id AND ts.academic_year_id = tc.academic_year_id
        LEFT JOIN Subjects s ON ts.subject_id = s.subject_id
        WHERE tc.class_id = ? AND tc.academic_year_id = ?
        GROUP BY t.teacher_id, t.first_name_ar, t.last_name_ar, t.first_name_en, 
                 t.last_name_en, t.teacher_number, t.phone, t.email, t.qualification,
                 t.specialization, tc.is_class_teacher
        """
        
        cursor.execute(query, (class_id, academic_year_id))
        columns = [column[0] for column in cursor.description]
        teachers = []
        
        for row in cursor.fetchall():
            teachers.append(dict(zip(columns, row)))
        
        return teachers