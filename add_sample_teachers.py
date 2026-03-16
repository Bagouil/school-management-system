from db_standalone import get_db_standalone
import hashlib
import random

def add_sample_teachers():
    """Add sample teachers and assign them to subjects and classes"""
    conn = get_db_standalone()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("ADDING SAMPLE TEACHERS AND SUBJECTS")
    print("=" * 60)
    
    # First, check if we have subjects
    cursor.execute("SELECT COUNT(*) FROM Subjects")
    subject_count = cursor.fetchone()[0]
    
    if subject_count == 0:
        print("No subjects found. Adding default subjects...")
        # Insert default subjects
        subjects = [
            ('اللغة العربية', 'Arabic Language', 'ARB', 1, 1),
            ('اللغة الإنجليزية', 'English Language', 'ENG', 1, 1),
            ('الرياضيات', 'Mathematics', 'MATH', 1, 1),
            ('العلوم', 'Science', 'SCI', 1, 1),
            ('الدراسات الإسلامية', 'Islamic Studies', 'ISL', 1, 1),
            ('الدراسات الاجتماعية', 'Social Studies', 'SOC', 1, 1),
            ('التربية البدنية', 'Physical Education', 'PE', 1, 1),
            ('الحاسوب', 'Computer', 'COM', 1, 1),
            ('التربية الفنية', 'Art Education', 'ART', 1, 1),
            
            # Secondary level subjects
            ('الفيزياء', 'Physics', 'PHY', 9, 1),
            ('الكيمياء', 'Chemistry', 'CHEM', 9, 1),
            ('الأحياء', 'Biology', 'BIO', 9, 1),
            ('الجيولوجيا', 'Geology', 'GEO', 9, 1),
            ('التاريخ', 'History', 'HIST', 9, 1),
            ('الجغرافيا', 'Geography', 'GEOG', 9, 1),
            ('الفلسفة', 'Philosophy', 'PHIL', 9, 1),
            ('علم النفس', 'Psychology', 'PSY', 9, 1),
        ]
        
        for subject in subjects:
            cursor.execute("""
            INSERT INTO Subjects (subject_name_ar, subject_name_en, subject_code, grade_level_id, is_active)
            VALUES (?, ?, ?, ?, ?)
            """, subject)
        
        print(f"✓ Added {len(subjects)} subjects")
    
    # Get current academic year
    cursor.execute("SELECT year_id FROM AcademicYears WHERE is_current = 1")
    year_result = cursor.fetchone()
    if not year_result:
        # Create current academic year if not exists
        cursor.execute("""
        INSERT INTO AcademicYears (year_name_ar, year_name_en, start_date, end_date, is_current)
        VALUES (?, ?, ?, ?, ?)
        """, ('٢٠٢٤-٢٠٢٥', '2024-2025', '2024-09-01', '2025-06-30', 1))
        year_id = 1
        print("✓ Created academic year 2024-2025")
    else:
        year_id = year_result[0]
    
    # Sample teachers data
    sample_teachers = [
        {
            'first_name_ar': 'أحمد',
            'last_name_ar': 'محمد',
            'first_name_en': 'Ahmed',
            'last_name_en': 'Mohamed',
            'email': 'ahmed.teacher@school.edu',
            'phone': '0912345671',
            'qualification': 'بكالوريوس رياضيات',
            'specialization': 'رياضيات',
            'salary': 7500.00,
            'subjects': ['الرياضيات', 'الفيزياء']
        },
        {
            'first_name_ar': 'فاطمة',
            'last_name_ar': 'عمر',
            'first_name_en': 'Fatima',
            'last_name_en': 'Omar',
            'email': 'fatima.teacher@school.edu',
            'phone': '0912345672',
            'qualification': 'بكالوريوس لغة عربية',
            'specialization': 'لغة عربية',
            'salary': 7200.00,
            'subjects': ['اللغة العربية', 'الدراسات الإسلامية']
        },
        {
            'first_name_ar': 'خالد',
            'last_name_ar': 'علي',
            'first_name_en': 'Khaled',
            'last_name_en': 'Ali',
            'email': 'khaled.teacher@school.edu',
            'phone': '0912345673',
            'qualification': 'بكالوريوس لغة إنجليزية',
            'specialization': 'لغة إنجليزية',
            'salary': 7800.00,
            'subjects': ['اللغة الإنجليزية']
        },
        {
            'first_name_ar': 'نورة',
            'last_name_ar': 'عبدالله',
            'first_name_en': 'Noura',
            'last_name_en': 'Abdullah',
            'email': 'noura.teacher@school.edu',
            'phone': '0912345674',
            'qualification': 'بكالوريوس علوم',
            'specialization': 'علوم',
            'salary': 7100.00,
            'subjects': ['العلوم', 'الأحياء', 'الكيمياء']
        },
        {
            'first_name_ar': 'محمد',
            'last_name_ar': 'إبراهيم',
            'first_name_en': 'Mohamed',
            'last_name_en': 'Ibrahim',
            'email': 'mohamed.teacher@school.edu',
            'phone': '0912345675',
            'qualification': 'بكالوريوس دراسات إسلامية',
            'specialization': 'دراسات إسلامية',
            'salary': 6900.00,
            'subjects': ['الدراسات الإسلامية', 'الفلسفة']
        },
        {
            'first_name_ar': 'سارة',
            'last_name_ar': 'خالد',
            'first_name_en': 'Sara',
            'last_name_en': 'Khaled',
            'email': 'sara.teacher@school.edu',
            'phone': '0912345676',
            'qualification': 'بكالوريوس حاسوب',
            'specialization': 'حاسوب',
            'salary': 8200.00,
            'subjects': ['الحاسوب', 'الرياضيات']
        },
        {
            'first_name_ar': 'عمر',
            'last_name_ar': 'حسن',
            'first_name_en': 'Omar',
            'last_name_en': 'Hassan',
            'email': 'omar.teacher@school.edu',
            'phone': '0912345677',
            'qualification': 'بكالوريوس تربية بدنية',
            'specialization': 'تربية بدنية',
            'salary': 6500.00,
            'subjects': ['التربية البدنية']
        },
        {
            'first_name_ar': 'ليلى',
            'last_name_ar': 'أحمد',
            'first_name_en': 'Layla',
            'last_name_en': 'Ahmed',
            'email': 'layla.teacher@school.edu',
            'phone': '0912345678',
            'qualification': 'بكالوريوس تربية فنية',
            'specialization': 'تربية فنية',
            'salary': 6800.00,
            'subjects': ['التربية الفنية']
        },
        {
            'first_name_ar': 'يوسف',
            'last_name_ar': 'محمود',
            'first_name_en': 'Yousef',
            'last_name_en': 'Mahmoud',
            'email': 'yousef.teacher@school.edu',
            'phone': '0912345679',
            'qualification': 'بكالوريوس تاريخ',
            'specialization': 'تاريخ',
            'salary': 7000.00,
            'subjects': ['التاريخ', 'الجغرافيا']
        },
        {
            'first_name_ar': 'هدى',
            'last_name_ar': 'صالح',
            'first_name_en': 'Huda',
            'last_name_en': 'Saleh',
            'email': 'huda.teacher@school.edu',
            'phone': '0912345680',
            'qualification': 'بكالوريوس كيمياء',
            'specialization': 'كيمياء',
            'salary': 7500.00,
            'subjects': ['الكيمياء', 'العلوم']
        }
    ]
    
    print("\n" + "=" * 60)
    print("ADDING TEACHERS")
    print("=" * 60)
    
    teacher_ids = []
    for teacher in sample_teachers:
        # Check if teacher already exists
        cursor.execute("SELECT teacher_id FROM Teachers WHERE email = ?", (teacher['email'],))
        existing = cursor.fetchone()
        
        if existing:
            teacher_id = existing[0]
            print(f"• Teacher {teacher['first_name_ar']} {teacher['last_name_ar']} already exists (ID: {teacher_id})")
        else:
            # Generate teacher number
            cursor.execute("SELECT ISNULL(MAX(CAST(RIGHT(teacher_number, 3) AS INT)), 0) + 1 FROM Teachers")
            next_num = cursor.fetchone()[0]
            teacher_number = f"TCH{str(next_num).zfill(3)}"
            
            # Insert teacher
            cursor.execute("""
            INSERT INTO Teachers (
                teacher_number, first_name_ar, last_name_ar, first_name_en, last_name_en,
                birth_date, gender, qualification, specialization, hire_date,
                phone, email, salary, status
            ) OUTPUT INSERTED.teacher_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (
                teacher_number,
                teacher['first_name_ar'],
                teacher['last_name_ar'],
                teacher['first_name_en'],
                teacher['last_name_en'],
                '1985-01-01',
                'male' if teacher['first_name_ar'] in ['أحمد', 'خالد', 'محمد', 'عمر', 'يوسف'] else 'female',
                teacher['qualification'],
                teacher['specialization'],
                '2020-09-01',
                teacher['phone'],
                teacher['email'],
                teacher['salary']
            ))
            
            teacher_id = cursor.fetchone()[0]
            
            # Create user account for teacher
            username = teacher['email'].split('@')[0]
            password = 'teacher123'
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Check if username exists
            cursor.execute("SELECT user_id FROM Users WHERE username = ?", (username,))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO Users (username, password_hash, email, role, full_name_ar, full_name_en, is_active)
                VALUES (?, ?, ?, 'teacher', ?, ?, 1)
                """, (
                    username,
                    password_hash,
                    teacher['email'],
                    teacher['first_name_ar'] + ' ' + teacher['last_name_ar'],
                    teacher['first_name_en'] + ' ' + teacher['last_name_en']
                ))
                print(f"✓ Created user: {username} / {password}")
            
            print(f"✓ Added teacher: {teacher['first_name_ar']} {teacher['last_name_ar']} (ID: {teacher_id})")
            teacher_ids.append((teacher_id, teacher))
    
    print("\n" + "=" * 60)
    print("ASSIGNING TEACHERS TO CLASSES AND SUBJECTS")
    print("=" * 60)
    
    # Get all classes
    cursor.execute("""
    SELECT c.class_id, c.class_name_ar, g.grade_id 
    FROM Classes c
    JOIN GradeLevels g ON c.grade_id = g.grade_id
    WHERE c.academic_year_id = ?
    """, (year_id,))
    
    classes = cursor.fetchall()
    
    if not classes:
        print("No classes found. Please add classes first.")
    else:
        # Assign teachers to classes and subjects
        for teacher_id, teacher in teacher_ids:
            # Randomly assign to 2-4 classes
            num_classes = random.randint(2, 4)
            assigned_classes = random.sample(classes, min(num_classes, len(classes)))
            
            for class_id, class_name, grade_id in assigned_classes:
                # Assign to class
                cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM TeacherClasses WHERE teacher_id = ? AND class_id = ? AND academic_year_id = ?)
                BEGIN
                    INSERT INTO TeacherClasses (teacher_id, class_id, academic_year_id, is_class_teacher)
                    VALUES (?, ?, ?, 0)
                END
                """, (teacher_id, class_id, year_id, teacher_id, class_id, year_id))
                
                # Find subjects this teacher can teach
                for subject_name in teacher['subjects']:
                    cursor.execute("""
                    SELECT subject_id FROM Subjects 
                    WHERE subject_name_ar LIKE ? OR subject_name_en LIKE ?
                    """, (f'%{subject_name}%', f'%{subject_name}%'))
                    
                    subject_result = cursor.fetchone()
                    if subject_result:
                        subject_id = subject_result[0]
                        
                        # Assign subject to teacher for this class
                        cursor.execute("""
                        IF NOT EXISTS (SELECT 1 FROM TeacherSubjects WHERE teacher_id = ? AND subject_id = ? AND class_id = ? AND academic_year_id = ?)
                        BEGIN
                            INSERT INTO TeacherSubjects (teacher_id, subject_id, class_id, academic_year_id)
                            VALUES (?, ?, ?, ?)
                        END
                        """, (teacher_id, subject_id, class_id, year_id, teacher_id, subject_id, class_id, year_id))
                        
                        # Add to ClassSubjects
                        cursor.execute("""
                        IF NOT EXISTS (SELECT 1 FROM ClassSubjects WHERE class_id = ? AND subject_id = ? AND academic_year_id = ?)
                        BEGIN
                            INSERT INTO ClassSubjects (class_id, subject_id, academic_year_id, teacher_id, hours_per_week)
                            VALUES (?, ?, ?, ?, ?)
                        END
                        ELSE
                        BEGIN
                            UPDATE ClassSubjects SET teacher_id = ? WHERE class_id = ? AND subject_id = ? AND academic_year_id = ?
                        END
                        """, (class_id, subject_id, year_id, class_id, subject_id, year_id, teacher_id, 4, 
                              teacher_id, class_id, subject_id, year_id))
            
            print(f"✓ Assigned {teacher['first_name_ar']} {teacher['last_name_ar']} to {len(assigned_classes)} classes")
    
    # Assign class teachers
    print("\n" + "=" * 60)
    print("ASSIGNING CLASS TEACHERS")
    print("=" * 60)
    
    cursor.execute("SELECT teacher_id, first_name_ar, last_name_ar FROM Teachers WHERE status = 'active'")
    all_teachers = cursor.fetchall()
    
    for class_id, class_name, grade_id in classes:
        if all_teachers:
            teacher_id, first_name, last_name = random.choice(all_teachers)
            
            cursor.execute("UPDATE Classes SET class_teacher_id = ? WHERE class_id = ?", (teacher_id, class_id))
            
            cursor.execute("""
            UPDATE TeacherClasses 
            SET is_class_teacher = 1 
            WHERE teacher_id = ? AND class_id = ? AND academic_year_id = ?
            """, (teacher_id, class_id, year_id))
            
            print(f"✓ Assigned {first_name} {last_name} as class teacher for {class_name}")
    
    conn.commit()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    cursor.execute("SELECT COUNT(*) FROM Teachers WHERE status = 'active'")
    teacher_count = cursor.fetchone()[0]
    print(f"Total active teachers: {teacher_count}")
    
    cursor.execute("SELECT COUNT(*) FROM TeacherClasses")
    tc_count = cursor.fetchone()[0]
    print(f"Total teacher-class assignments: {tc_count}")
    
    cursor.execute("SELECT COUNT(*) FROM TeacherSubjects")
    ts_count = cursor.fetchone()[0]
    print(f"Total teacher-subject assignments: {ts_count}")
    
    cursor.execute("SELECT COUNT(*) FROM ClassSubjects")
    cs_count = cursor.fetchone()[0]
    print(f"Total class-subject assignments: {cs_count}")
    
    cursor.execute("SELECT COUNT(*) FROM Classes WHERE class_teacher_id IS NOT NULL")
    ct_count = cursor.fetchone()[0]
    print(f"Classes with class teacher: {ct_count}")
    
    print("\n" + "=" * 60)
    print("TEACHER LOGIN CREDENTIALS")
    print("=" * 60)
    for teacher in sample_teachers:
        username = teacher['email'].split('@')[0]
        print(f"{teacher['first_name_ar']} {teacher['last_name_ar']}: {username} / teacher123")
    print("=" * 60)
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    add_sample_teachers()