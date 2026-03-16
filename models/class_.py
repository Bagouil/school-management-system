from database.db_config import get_db

class Class:
    @staticmethod
    def get_all_active():
        """Get all active classes for the current academic year"""
        db = get_db()
        cursor = db.cursor()
        
        # FIXED - Get grade_order from GradeLevels without GROUP BY issues
        query = """
        SELECT c.*, g.grade_name_ar, g.grade_name_en, g.grade_id, g.grade_order,
               t.teacher_id as class_teacher_id,
               CONCAT(t.first_name_ar, ' ', t.last_name_ar) as class_teacher_name,
               (SELECT COUNT(*) FROM Students WHERE current_class_id = c.class_id AND status = 'active') as student_count
        FROM Classes c
        JOIN GradeLevels g ON c.grade_id = g.grade_id
        LEFT JOIN Teachers t ON c.class_teacher_id = t.teacher_id
        WHERE c.academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)
        ORDER BY g.grade_order, c.class_name_ar
        """
        
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        classes = []
        
        for row in cursor.fetchall():
            classes.append(dict(zip(columns, row)))
        
        return classes
    
    @staticmethod
    def get_by_id(class_id):
        """Get class by ID"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        SELECT c.*, g.grade_name_ar, g.grade_name_en, g.grade_id,
               t.teacher_id as class_teacher_id,
               CONCAT(t.first_name_ar, ' ', t.last_name_ar) as class_teacher_name
        FROM Classes c
        JOIN GradeLevels g ON c.grade_id = g.grade_id
        LEFT JOIN Teachers t ON c.class_teacher_id = t.teacher_id
        WHERE c.class_id = ?
        """
        
        cursor.execute(query, (class_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None
    
    @staticmethod
    def create(data):
        """Create a new class"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        INSERT INTO Classes (grade_id, class_name_ar, class_name_en, academic_year_id, capacity, class_teacher_id)
        OUTPUT INSERTED.class_id
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            data['grade_id'],
            data['class_name_ar'],
            data['class_name_en'],
            data['academic_year_id'],
            data.get('capacity', 30),
            data.get('class_teacher_id')
        ))
        
        class_id = cursor.fetchone()[0]
        db.commit()
        return class_id
    
    @staticmethod
    def update(class_id, data):
        """Update class information"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        UPDATE Classes
        SET grade_id = ?, class_name_ar = ?, class_name_en = ?, 
            capacity = ?, class_teacher_id = ?
        WHERE class_id = ?
        """
        
        cursor.execute(query, (
            data['grade_id'],
            data['class_name_ar'],
            data['class_name_en'],
            data.get('capacity', 30),
            data.get('class_teacher_id'),
            class_id
        ))
        
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def get_students(class_id):
        """Get all students in a class"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        SELECT student_id, first_name_ar, last_name_ar, first_name_en, last_name_en, 
               student_number, gender, birth_date
        FROM Students
        WHERE current_class_id = ? AND status = 'active'
        ORDER BY first_name_ar
        """
        
        cursor.execute(query, (class_id,))
        columns = [column[0] for column in cursor.description]
        students = []
        
        for row in cursor.fetchall():
            students.append(dict(zip(columns, row)))
        
        return students
    
    @staticmethod
    def get_subjects(class_id):
        """Get subjects for a class with assigned teachers"""
        db = get_db()
        cursor = db.cursor()
        
        query = """
        SELECT cs.*, s.subject_name_ar, s.subject_name_en, s.subject_code,
               t.teacher_id, CONCAT(t.first_name_ar, ' ', t.last_name_ar) as teacher_name
        FROM ClassSubjects cs
        JOIN Subjects s ON cs.subject_id = s.subject_id
        LEFT JOIN Teachers t ON cs.teacher_id = t.teacher_id
        WHERE cs.class_id = ? AND cs.academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)
        ORDER BY s.subject_name_ar
        """
        
        cursor.execute(query, (class_id,))
        columns = [column[0] for column in cursor.description]
        subjects = []
        
        for row in cursor.fetchall():
            subjects.append(dict(zip(columns, row)))
        
        return subjects
    
    @staticmethod
    def add_subject(class_id, subject_id, teacher_id=None, hours_per_week=0):
        """Add a subject to a class"""
        db = get_db()
        cursor = db.cursor()
        
        # Get current academic year
        cursor.execute("SELECT year_id FROM AcademicYears WHERE is_current = 1")
        year_id = cursor.fetchone()[0]
        
        # Check if subject already exists for this class
        cursor.execute("""
        SELECT class_subject_id FROM ClassSubjects 
        WHERE class_id = ? AND subject_id = ? AND academic_year_id = ?
        """, (class_id, subject_id, year_id))
        
        if cursor.fetchone():
            return False  # Already exists
        
        cursor.execute("""
        INSERT INTO ClassSubjects (class_id, subject_id, academic_year_id, teacher_id, hours_per_week)
        VALUES (?, ?, ?, ?, ?)
        """, (class_id, subject_id, year_id, teacher_id, hours_per_week))
        
        db.commit()
        return True
    
    @staticmethod
    def update_subject(class_subject_id, teacher_id=None, hours_per_week=None):
        """Update subject assignment"""
        db = get_db()
        cursor = db.cursor()
        
        query = "UPDATE ClassSubjects SET "
        params = []
        
        if teacher_id is not None:
            query += "teacher_id = ?, "
            params.append(teacher_id)
        
        if hours_per_week is not None:
            query += "hours_per_week = ?, "
            params.append(hours_per_week)
        
        query = query.rstrip(', ') + " WHERE class_subject_id = ?"
        params.append(class_subject_id)
        
        cursor.execute(query, params)
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def remove_subject(class_subject_id):
        """Remove subject from class"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM ClassSubjects WHERE class_subject_id = ?", (class_subject_id,))
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def get_available_teachers(class_id, subject_id=None):
        """Get teachers available to assign to this class"""
        db = get_db()
        cursor = db.cursor()
        
        if subject_id:
            # Teachers who can teach this subject
            query = """
            SELECT DISTINCT t.teacher_id, t.first_name_ar, t.last_name_ar, t.teacher_number,
                   CASE WHEN ts.teacher_id IS NOT NULL THEN 1 ELSE 0 END as qualified
            FROM Teachers t
            LEFT JOIN TeacherSubjects ts ON t.teacher_id = ts.teacher_id AND ts.subject_id = ?
            WHERE t.status = 'active'
            ORDER BY qualified DESC, t.first_name_ar
            """
            cursor.execute(query, (subject_id,))
        else:
            # All active teachers
            query = """
            SELECT teacher_id, first_name_ar, last_name_ar, teacher_number, 1 as qualified
            FROM Teachers
            WHERE status = 'active'
            ORDER BY first_name_ar
            """
            cursor.execute(query)
        
        columns = [column[0] for column in cursor.description]
        teachers = []
        
        for row in cursor.fetchall():
            teachers.append(dict(zip(columns, row)))
        
        return teachers