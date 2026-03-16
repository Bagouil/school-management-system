import hashlib
from db_standalone import get_db_standalone

def create_admin():
    """Create admin user using standalone connection"""
    try:
        # Get database connection
        conn = get_db_standalone()
        cursor = conn.cursor()
        
        # Create admin user
        username = 'admin'
        password = 'admin123'
        # Hash the password using SHA256
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        print(f"Password hash: {password_hash}")  # For debugging
        
        # Delete any existing admin user first (to avoid duplicates)
        cursor.execute("DELETE FROM Users WHERE username = ?", (username,))
        print(f"✓ Removed existing admin user (if any)")
        
        # Insert new admin user
        cursor.execute("""
        INSERT INTO Users (username, password_hash, role, full_name_ar, full_name_en, is_active)
        VALUES (?, ?, 'admin', N'مدير النظام', 'System Admin', 1)
        """, (username, password_hash))
        
        conn.commit()
        print("✓ Admin user inserted successfully")
        
        # Verify the user was created
        cursor.execute("SELECT user_id, username, role FROM Users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user:
            print("\n" + "="*40)
            print("ADMIN USER CREATED SUCCESSFULLY!")
            print("="*40)
            print(f"User ID: {user[0]}")
            print(f"Username: {user[1]}")
            print(f"Role: {user[2]}")
            print(f"Password: {password}")
            print("="*40)
        else:
            print("✗ Failed to verify admin user")
        
        # Show all users in database
        print("\nAll users in database:")
        cursor.execute("SELECT user_id, username, role, full_name_ar FROM Users")
        users = cursor.fetchall()
        for u in users:
            print(f"  - ID: {u[0]}, Username: {u[1]}, Role: {u[2]}, Name: {u[3]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_admin()