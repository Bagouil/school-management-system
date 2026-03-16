from database.db_config import get_db
import hashlib

def add_sample_teachers():
    """Add sample teachers and create user accounts"""
    db = get_db()
    cursor = db.cursor()
    
    # Sample teachers
    teachers = [
        {
            'teacher_number': 'TCH001',
            'first_name_ar': 'أحمد',
            'last_name_ar': 'محمد',
            'first_name_en': 'Ahmed',
            'last_name_en': 'Mohamed',
            'email': 'ahmed@school.edu',
            'phone': '0912345671',
            'qualification': 'بكالوريوس رياضيات',
            'specialization': 'رياضيات',
            'salary': 5000.00
        },
        {
            'teacher_number': 'TCH002',
            'first_name_ar': 'فاطمة',
            'last_name_ar': 'عمر',
            'first_name_en': 'Fatima',
            'last_name_en': 'Omar',
            'email': 'fatima@school.edu',
            'phone': '0912345672',
            'qualification': 'بكالوريوس لغة عربية',
            'specialization': 'لغة عربية',
            'salary': 5200.00
        }
    ]
    
    for teacher in teachers:
        # Check if teacher already exists
        cursor.execute("SELECT teacher_id FROM Teachers WHERE teacher_number = ?", 
                      (teacher['teacher_number'],))
        if not cursor.fetchone():
            # Insert teacher
            cursor.execute("""
            INSERT INTO Teachers (teacher_number, first_name_ar, last_name_ar, 
                                 first_name_en, last_name_en, email, phone,
                                 qualification, specialization, salary, status)
            OUTPUT INSERTED.teacher_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (teacher['teacher_number'], teacher['first_name_ar'], teacher['last_name_ar'],
                  teacher['first_name_en'], teacher['last_name_en'], teacher['email'],
                  teacher['phone'], teacher['qualification'], teacher['specialization'],
                  teacher['salary']))
            
            teacher_id = cursor.fetchone()[0]
            
            # Create user account for teacher
            username = teacher['email'].split('@')[0]
            password = 'teacher123'
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute("""
            INSERT INTO Users (username, password_hash, email, role, 
                             full_name_ar, full_name_en, is_active)
            VALUES (?, ?, ?, 'teacher', ?, ?, 1)
            """, (username, password_hash, teacher['email'],
                  teacher['first_name_ar'] + ' ' + teacher['last_name_ar'],
                  teacher['first_name_en'] + ' ' + teacher['last_name_en']))
            
            print(f"Created teacher: {teacher['first_name_ar']} - Username: {username}, Password: teacher123")
    
    db.commit()
    print("Sample teachers added successfully!")

if __name__ == "__main__":
    add_sample_teachers()