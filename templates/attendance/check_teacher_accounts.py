from db_standalone import get_db_standalone
import hashlib

def check_teacher_accounts():
    """Check what teacher accounts exist in the database"""
    conn = get_db_standalone()
    cursor = conn.cursor()
    
    print("\n=== CHECKING TEACHER ACCOUNTS ===\n")
    
    # Check Teachers table
    cursor.execute("""
    SELECT teacher_id, first_name_ar, last_name_ar, email, phone 
    FROM Teachers 
    WHERE status = 'active'
    """)
    
    teachers = cursor.fetchall()
    print(f"Found {len(teachers)} active teachers:")
    for t in teachers:
        print(f"  - {t[1]} {t[2]} (ID: {t[0]}, Email: {t[3]}, Phone: {t[4]})")
    
    print("\n" + "="*50)
    
    # Check Users table for teacher accounts
    cursor.execute("""
    SELECT user_id, username, email, role, full_name_ar 
    FROM Users 
    WHERE role = 'teacher'
    """)
    
    users = cursor.fetchall()
    print(f"\nFound {len(users)} teacher user accounts:")
    for u in users:
        print(f"  - {u[4]} (Username: {u[1]}, Email: {u[2]})")
    
    print("\n" + "="*50)
    
    # Check if any teachers are linked to user accounts
    cursor.execute("""
    SELECT t.teacher_id, t.first_name_ar, t.last_name_ar, u.user_id, u.username
    FROM Teachers t
    LEFT JOIN Users u ON t.email = u.email OR t.phone = u.username
    WHERE t.status = 'active'
    """)
    
    linked = cursor.fetchall()
    print("\nTeacher-User linking:")
    for l in linked:
        if l[3]:
            print(f"  ✓ {l[1]} {l[2]} is linked to user '{l[4]}'")
        else:
            print(f"  ✗ {l[1]} {l[2]} has NO linked user account")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_teacher_accounts()