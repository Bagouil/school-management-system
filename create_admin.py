# create_admin.py
from database.db_config import get_db
import hashlib

def create_admin():
    """Create admin user"""
    try:
        db = get_db()
        cursor = db.cursor()

        # Create admin user
        username = 'admin'
        password = 'admin123'
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Check if admin already exists
        cursor.execute("SELECT COUNT(*) FROM Users WHERE username = ?", (username,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO Users (username, password_hash, role, full_name_ar, full_name_en, is_active)
            VALUES (?, ?, 'admin', N'مدير النظام', 'System Admin', 1)
            """, (username, password_hash))
            db.commit()
            print("✓ Admin user created successfully!")
            print("  Username: admin")
            print("  Password: admin123")
        else:
            print("✓ Admin user already exists")
            
    except Exception as e:
        print(f"Error creating admin user: {e}")

if __name__ == "__main__":
    create_admin()