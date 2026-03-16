# init_database.py
import pyodbc

def create_database():
    """Create database and tables using Windows Authentication"""
    try:
        # Connect to master database
        conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=master;Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str, timeout=30)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'SchoolManagementSystem')
        BEGIN
            CREATE DATABASE SchoolManagementSystem
        END
        """)
        
        print("✓ Database checked/created successfully")
        conn.close()
        
        # Now connect to our database and create tables
        conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=SchoolManagementSystem;Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str, timeout=30)
        cursor = conn.cursor()
        
        # Create Users table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Users')
        BEGIN
            CREATE TABLE Users (
                user_id INT IDENTITY(1,1) PRIMARY KEY,
                username NVARCHAR(50) UNIQUE NOT NULL,
                password_hash NVARCHAR(255) NOT NULL,
                email NVARCHAR(100),
                role NVARCHAR(20) CHECK (role IN ('admin', 'teacher', 'accountant')) NOT NULL,
                full_name_ar NVARCHAR(100),
                full_name_en NVARCHAR(100),
                is_active BIT DEFAULT 1,
                last_login DATETIME,
                created_at DATETIME DEFAULT GETDATE()
            )
            PRINT 'Users table created'
        END
        ELSE
            PRINT 'Users table already exists'
        """)
        
        # Create GradeLevels table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'GradeLevels')
        BEGIN
            CREATE TABLE GradeLevels (
                grade_id INT IDENTITY(1,1) PRIMARY KEY,
                grade_name_ar NVARCHAR(50),
                grade_name_en NVARCHAR(50),
                level_type NVARCHAR(20) CHECK (level_type IN ('basic', 'secondary')) NOT NULL,
                grade_order INT,
                academic_stage NVARCHAR(50)
            )
            PRINT 'GradeLevels table created'
        END
        """)
        
        # Insert grade levels if table is empty
        cursor.execute("SELECT COUNT(*) FROM GradeLevels")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO GradeLevels (grade_name_ar, grade_name_en, level_type, grade_order, academic_stage) VALUES
            (N'الأساس 1', 'Basic 1', 'basic', 1, 'Basic Education'),
            (N'الأساس 2', 'Basic 2', 'basic', 2, 'Basic Education'),
            (N'الأساس 3', 'Basic 3', 'basic', 3, 'Basic Education'),
            (N'الأساس 4', 'Basic 4', 'basic', 4, 'Basic Education'),
            (N'الأساس 5', 'Basic 5', 'basic', 5, 'Basic Education'),
            (N'الأساس 6', 'Basic 6', 'basic', 6, 'Basic Education'),
            (N'الأساس 7', 'Basic 7', 'basic', 7, 'Basic Education'),
            (N'الأساس 8', 'Basic 8', 'basic', 8, 'Basic Education'),
            (N'الثانوي 1', 'Secondary 1', 'secondary', 9, 'Secondary Education'),
            (N'الثانوي 2', 'Secondary 2', 'secondary', 10, 'Secondary Education'),
            (N'الثانوي 3', 'Secondary 3', 'secondary', 11, 'Secondary Education')
            """)
            print("✓ Grade levels inserted")
        
        # Create AcademicYears table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AcademicYears')
        BEGIN
            CREATE TABLE AcademicYears (
                year_id INT IDENTITY(1,1) PRIMARY KEY,
                year_name_ar NVARCHAR(50),
                year_name_en NVARCHAR(50),
                start_date DATE,
                end_date DATE,
                is_current BIT DEFAULT 0
            )
            PRINT 'AcademicYears table created'
        END
        """)
        
        # Insert current academic year if table is empty
        cursor.execute("SELECT COUNT(*) FROM AcademicYears")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO AcademicYears (year_name_ar, year_name_en, start_date, end_date, is_current) VALUES
            (N'2024-2025', '2024-2025', '2024-09-01', '2025-06-30', 1)
            """)
            print("✓ Academic year inserted")
        
        # Create Classes table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Classes')
        BEGIN
            CREATE TABLE Classes (
                class_id INT IDENTITY(1,1) PRIMARY KEY,
                grade_id INT,
                class_name_ar NVARCHAR(50),
                class_name_en NVARCHAR(50),
                academic_year_id INT,
                capacity INT DEFAULT 30,
                FOREIGN KEY (grade_id) REFERENCES GradeLevels(grade_id),
                FOREIGN KEY (academic_year_id) REFERENCES AcademicYears(year_id)
            )
            PRINT 'Classes table created'
        END
        """)
        
        # Insert sample classes
        cursor.execute("SELECT COUNT(*) FROM Classes")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO Classes (grade_id, class_name_ar, class_name_en, academic_year_id, capacity) VALUES
            (1, N'الأساس 1 - أ', 'Basic 1 - A', 1, 30),
            (1, N'الأساس 1 - ب', 'Basic 1 - B', 1, 30),
            (2, N'الأساس 2 - أ', 'Basic 2 - A', 1, 30),
            (3, N'الأساس 3 - أ', 'Basic 3 - A', 1, 30)
            """)
            print("✓ Sample classes inserted")
        
        # Create Students table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Students')
        BEGIN
            CREATE TABLE Students (
                student_id INT IDENTITY(1,1) PRIMARY KEY,
                student_number NVARCHAR(20) UNIQUE NOT NULL,
                first_name_ar NVARCHAR(50),
                last_name_ar NVARCHAR(50),
                first_name_en NVARCHAR(50),
                last_name_en NVARCHAR(50),
                birth_date DATE,
                gender NVARCHAR(10) CHECK (gender IN ('male', 'female')),
                nationality NVARCHAR(50) DEFAULT 'Sudanese',
                religion NVARCHAR(50),
                address NVARCHAR(MAX),
                phone NVARCHAR(20),
                email NVARCHAR(100),
                enrollment_date DATE,
                current_class_id INT,
                academic_year_id INT,
                status NVARCHAR(20) CHECK (status IN ('active', 'transferred', 'graduated', 'withdrawn')) DEFAULT 'active',
                previous_school NVARCHAR(MAX),
                student_image NVARCHAR(255),
                created_at DATETIME DEFAULT GETDATE(),
                FOREIGN KEY (current_class_id) REFERENCES Classes(class_id),
                FOREIGN KEY (academic_year_id) REFERENCES AcademicYears(year_id)
            )
            PRINT 'Students table created'
        END
        """)
        
        conn.commit()
        print("\n✓ All tables created/verified successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_database()