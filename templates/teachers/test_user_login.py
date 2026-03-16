from database.db_config import get_db
import hashlib

def test_user_login(username, password):
    """Test user login directly"""
    db = get_db()
    cursor = db.cursor()
    
    # Hash the password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Try to find the user
    cursor.execute("""
    SELECT user_id, username, role, full_name_ar, full_name_en, is_active
    FROM Users 
    WHERE username = ? AND password_hash = ?
    """, (username, password_hash))
    
    user = cursor.fetchone()
    
    if user:
        print(f"✓ Login successful!")
        print(f"  User ID: {user[0]}")
        print(f"  Username: {user[1]}")
        print(f"  Role: {user[2]}")
        print(f"  Name: {user[3] or user[4]}")
        print(f"  Active: {user[5]}")
        return True
    else:
        print(f"✗ Login failed - Invalid username or password")
        
        # Check if user exists at all
        cursor.execute("SELECT username, password_hash, is_active FROM Users WHERE username = ?", (username,))
        existing = cursor.fetchone()
        if existing:
            print(f"  Username exists: {existing[0]}")
            print(f"  Stored hash: {existing[1]}")
            print(f"  Provided hash: {password_hash}")
            print(f"  Active: {existing[2]}")
            print(f"  Hashes match: {existing[1] == password_hash}")
        else:
            print(f"  Username '{username}' does not exist")
    
    cursor.close()
    return False

def list_all_users():
    """List all users in the database"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
    SELECT user_id, username, role, email, is_active, 
           CONVERT(varchar, created_at, 120) as created
    FROM Users
    ORDER BY user_id
    """)
    
    print("\n" + "="*60)
    print("ALL USERS IN DATABASE")
    print("="*60)
    
    users = cursor.fetchall()
    if not users:
        print("No users found")
    else:
        for user in users:
            print(f"ID: {user[0]}, Username: {user[1]}, Role: {user[2]}, Email: {user[3]}, Active: {user[4]}, Created: {user[5]}")
    
    cursor.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 2:
        username = sys.argv[1]
        password = sys.argv[2]
        test_user_login(username, password)
    else:
        # Test with the user you just created
        username = input("Enter username to test: ")
        password = input("Enter password: ")
        test_user_login(username, password)
    
    list_all_users()