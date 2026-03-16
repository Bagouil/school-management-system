from database.db_config import get_db

def add_sample_classes():
    """Add sample classes if none exist"""
    db = get_db()
    cursor = db.cursor()
    
    # Check if classes exist
    cursor.execute("SELECT COUNT(*) FROM Classes")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("No classes found. Adding sample classes...")
        
        # Get academic year
        cursor.execute("SELECT year_id FROM AcademicYears WHERE is_current = 1")
        year_result = cursor.fetchone()
        
        if not year_result:
            print("No academic year found. Creating academic year...")
            # Create academic year if none exists
            cursor.execute("""
            INSERT INTO AcademicYears (year_name_ar, year_name_en, start_date, end_date, is_current)
            OUTPUT INSERTED.year_id
            VALUES (N'2024-2025', '2024-2025', '2024-09-01', '2025-06-30', 1)
            """)
            year_id = cursor.fetchone()[0]
        else:
            year_id = year_result[0]
        
        # Add sample classes (without N prefix - that's for SQL only)
        classes = [
            (1, 'الأساس 1 - أ', 'Basic 1 - A', year_id, 30),
            (1, 'الأساس 1 - ب', 'Basic 1 - B', year_id, 30),
            (2, 'الأساس 2 - أ', 'Basic 2 - A', year_id, 30),
            (2, 'الأساس 2 - ب', 'Basic 2 - B', year_id, 30),
            (3, 'الأساس 3 - أ', 'Basic 3 - A', year_id, 30),
            (3, 'الأساس 3 - ب', 'Basic 3 - B', year_id, 30),
            (4, 'الأساس 4 - أ', 'Basic 4 - A', year_id, 30),
            (4, 'الأساس 4 - ب', 'Basic 4 - B', year_id, 30),
            (5, 'الأساس 5 - أ', 'Basic 5 - A', year_id, 30),
            (5, 'الأساس 5 - ب', 'Basic 5 - B', year_id, 30),
            (6, 'الأساس 6 - أ', 'Basic 6 - A', year_id, 30),
            (6, 'الأساس 6 - ب', 'Basic 6 - B', year_id, 30),
            (7, 'الأساس 7 - أ', 'Basic 7 - A', year_id, 30),
            (7, 'الأساس 7 - ب', 'Basic 7 - B', year_id, 30),
            (8, 'الأساس 8 - أ', 'Basic 8 - A', year_id, 30),
            (8, 'الأساس 8 - ب', 'Basic 8 - B', year_id, 30),
            (9, 'الثانوي 1 - أ', 'Secondary 1 - A', year_id, 30),
            (9, 'الثانوي 1 - ب', 'Secondary 1 - B', year_id, 30),
            (10, 'الثانوي 2 - أ', 'Secondary 2 - A', year_id, 30),
            (10, 'الثانوي 2 - ب', 'Secondary 2 - B', year_id, 30),
            (11, 'الثانوي 3 - أ', 'Secondary 3 - A', year_id, 30),
            (11, 'الثانوي 3 - ب', 'Secondary 3 - B', year_id, 30),
        ]
        
        for class_data in classes:
            cursor.execute("""
            INSERT INTO Classes (grade_id, class_name_ar, class_name_en, academic_year_id, capacity)
            VALUES (?, ?, ?, ?, ?)
            """, class_data)
        
        db.commit()
        print(f"✓ Added {len(classes)} sample classes")
        
        # Verify classes were added
        cursor.execute("SELECT COUNT(*) FROM Classes")
        new_count = cursor.fetchone()[0]
        print(f"✓ Total classes now: {new_count}")
        
    else:
        print(f"✓ Found {count} existing classes")
        
        # Show the classes
        cursor.execute("""
        SELECT c.class_id, c.class_name_ar, c.class_name_en, g.grade_name_ar
        FROM Classes c
        JOIN GradeLevels g ON c.grade_id = g.grade_id
        ORDER BY g.grade_order, c.class_name_ar
        """)
        
        classes = cursor.fetchall()
        print("\nExisting classes:")
        for c in classes:
            print(f"  - {c[1]} ({c[2]})")

if __name__ == "__main__":
    add_sample_classes()