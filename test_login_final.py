import hashlib
from db_standalone import get_db_standalone

def test_login(username, password):
    """Test login using standalone connection"""
    try:
        # Get database connection
        conn = get_db_standalone()
        cursor = conn.cursor()
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        print(f"Testing login for: {username}")
        print(f"Password hash: {password_hash}")
        
        # Try to find the user
        cursor.execute("""
        SELECT user_id, username, role, full_name_ar, full_name_en, password_hash
        FROM Users 
        WHERE username = ?
        """, (username,))
        
        user = cursor.fetchone()
        
        if user:
            print(f"\n✓ User found in database:")
            print(f"  User ID: {user[0]}")
            print(f"  Username: {user[1]}")
            print(f"  Role: {user[2]}")
            print(f"  Stored password hash: {user[5]}")
            print(f"  Provided password hash: {password_hash}")
            
            if user[5] == password_hash:
                print("\n✓ PASSWORDS MATCH! Login would be successful.")
            else:
                print("\n✗ PASSWORDS DO NOT MATCH! Login would fail.")
        else:
            print(f"\n✗ User '{username}' not found in database")
            
            # Show available users
            cursor.execute("SELECT username FROM Users")
            users = cursor.fetchall()
            if users:
                print("Available users:")
                for u in users:
                    print(f"  - {u[0]}")
            else:
                print("No users in database")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with admin credentials
    test_login('admin', 'admin123')