from database.db_config import get_db
from datetime import datetime

class ExamType:
    @staticmethod
    def get_all():
        """Get all exam types"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("SELECT * FROM ExamTypes WHERE is_active = 1 ORDER BY sort_order")
            
            if cursor.description is None:
                return []
            
            columns = [column[0] for column in cursor.description]
            exam_types = []
            
            for row in cursor.fetchall():
                exam_types.append(dict(zip(columns, row)))
            
            return exam_types
        except Exception as e:
            print(f"Error in ExamType.get_all: {e}")
            return []
        finally:
            cursor.close()
    
    @staticmethod
    def get_by_id(exam_type_id):
        """Get exam type by ID"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("SELECT * FROM ExamTypes WHERE exam_type_id = ?", (exam_type_id,))
            
            if cursor.description is None:
                return None
            
            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()
            
            if row:
                return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Error in ExamType.get_by_id: {e}")
            return None
        finally:
            cursor.close()


class Exam:
    @staticmethod
    def create(data):
        """Create new exam"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            # Check which columns exist
            cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'Exams'
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            # Build dynamic insert query
            columns = []
            params = []
            
            # Required columns
            base_columns = ['exam_name_ar', 'exam_name_en', 'exam_type_id', 'subject_id', 
                           'class_id', 'academic_year_id', 'exam_date', 'total_marks', 'passing_marks']
            
            for col in base_columns:
                if col in existing_columns:
                    columns.append(col)
                    if col == 'academic_year_id':
                        params.append(data['academic_year_id'])
                    elif col in ['total_marks', 'passing_marks']:
                        params.append(float(data[col]))
                    else:
                        params.append(data.get(col, ''))
            
            # Optional columns
            optional_columns = ['term', 'start_time', 'end_time', 'duration_minutes', 'description', 'created_by']
            for col in optional_columns:
                if col in existing_columns and data.get(col) is not None:
                    columns.append(col)
                    if col == 'created_by':
                        params.append(data['created_by'])
                    elif col == 'term':
                        params.append(int(data.get(col, 1)))
                    elif col in ['start_time', 'end_time']:
                        params.append(data.get(col))
                    elif col == 'duration_minutes':
                        params.append(int(data.get(col, 0)) if data.get(col) else None)
                    else:
                        params.append(data.get(col, ''))
            
            # Build and execute query
            placeholders = ','.join(['?' for _ in columns])
            query = f"INSERT INTO Exams ({','.join(columns)}) OUTPUT INSERTED.exam_id VALUES ({placeholders})"
            
            cursor.execute(query, params)
            exam_id = cursor.fetchone()[0]
            db.commit()
            
            return exam_id
            
        except Exception as e:
            print(f"Error in Exam.create: {e}")
            db.rollback()
            raise e
        finally:
            cursor.close()
    
    @staticmethod
    def get_by_id(exam_id):
        """Get exam by ID"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("""
            SELECT e.*, et.type_name_ar, et.type_name_en, et.weight_percentage,
                   s.subject_name_ar, s.subject_name_en,
                   c.class_name_ar, c.class_name_en
            FROM Exams e
            LEFT JOIN ExamTypes et ON e.exam_type_id = et.exam_type_id
            LEFT JOIN Subjects s ON e.subject_id = s.subject_id
            LEFT JOIN Classes c ON e.class_id = c.class_id
            WHERE e.exam_id = ?
            """, (exam_id,))
            
            if cursor.description is None:
                return None
            
            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()
            
            if row:
                return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Error in Exam.get_by_id: {e}")
            return None
        finally:
            cursor.close()
    
    @staticmethod
    def get_all(filters=None):
        """Get all exams with optional filters"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            query = """
            SELECT e.*, et.type_name_ar, et.type_name_en, et.weight_percentage,
                   s.subject_name_ar, s.subject_name_en,
                   c.class_name_ar, c.class_name_en
            FROM Exams e
            LEFT JOIN ExamTypes et ON e.exam_type_id = et.exam_type_id
            LEFT JOIN Subjects s ON e.subject_id = s.subject_id
            LEFT JOIN Classes c ON e.class_id = c.class_id
            WHERE 1=1
            """
            params = []
            
            if filters:
                if filters.get('class_id'):
                    query += " AND e.class_id = ?"
                    params.append(filters['class_id'])
                if filters.get('subject_id'):
                    query += " AND e.subject_id = ?"
                    params.append(filters['subject_id'])
                if filters.get('term'):
                    query += " AND e.term = ?"
                    params.append(filters['term'])
            
            query += " ORDER BY e.exam_date DESC"
            
            cursor.execute(query, params)
            
            if cursor.description is None:
                return []
            
            columns = [column[0] for column in cursor.description]
            exams = []
            
            for row in cursor.fetchall():
                exams.append(dict(zip(columns, row)))
            
            return exams
            
        except Exception as e:
            print(f"Error in Exam.get_all: {e}")
            return []
        finally:
            cursor.close()
    
    @staticmethod
    def update(exam_id, data):
        """Update exam"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("""
            UPDATE Exams
            SET exam_name_ar = ?, exam_name_en = ?, exam_type_id = ?,
                subject_id = ?, class_id = ?, term = ?, exam_date = ?,
                start_time = ?, end_time = ?, duration_minutes = ?,
                total_marks = ?, passing_marks = ?, description = ?
            WHERE exam_id = ?
            """, (
                data['exam_name_ar'],
                data['exam_name_en'],
                data['exam_type_id'],
                data['subject_id'],
                data['class_id'],
                data.get('term', 1),
                data['exam_date'],
                data.get('start_time'),
                data.get('end_time'),
                data.get('duration_minutes'),
                data['total_marks'],
                data['passing_marks'],
                data.get('description', ''),
                exam_id
            ))
            
            db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error in Exam.update: {e}")
            db.rollback()
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def delete(exam_id):
        """Delete exam"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("DELETE FROM Exams WHERE exam_id = ?", (exam_id,))
            db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error in Exam.delete: {e}")
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def publish(exam_id):
        """Publish exam results"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("UPDATE Exams SET is_published = 1 WHERE exam_id = ?", (exam_id,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error in Exam.publish: {e}")
            return False
        finally:
            cursor.close()


class ExamResults:
    @staticmethod
    def create_or_update(data):
        """Create or update exam result"""
        print("=" * 50)
        print("ExamResults.create_or_update CALLED")
        print(f"Data received: {data}")
        
        db = get_db()
        cursor = db.cursor()
        
        try:
            # DEBUG: Check if the exam exists
            cursor.execute("SELECT exam_id, exam_name_ar FROM Exams WHERE exam_id = ?", (data['exam_id'],))
            exam_check = cursor.fetchone()
            if exam_check:
                print(f"✓ Exam exists: ID={exam_check[0]}, Name={exam_check[1]}")
            else:
                print(f"✗ Exam with ID {data['exam_id']} DOES NOT EXIST!")
                # List available exams
                cursor.execute("SELECT exam_id, exam_name_ar FROM Exams")
                available_exams = cursor.fetchall()
                print("Available exams:")
                for ex in available_exams:
                    print(f"  - ID: {ex[0]}, Name: {ex[1]}")
                return None
            
            # Check if result exists
            cursor.execute("SELECT result_id FROM ExamResults WHERE exam_id = ? AND student_id = ?",
                          (data['exam_id'], data['student_id']))
            existing = cursor.fetchone()
            print(f"Existing result: {existing}")
            
            # Get exam total marks
            cursor.execute("SELECT total_marks FROM Exams WHERE exam_id = ?", (data['exam_id'],))
            exam = cursor.fetchone()
            total_marks = float(exam[0])
            score = float(data['marks_obtained'])
            print(f"Total marks: {total_marks}, Score: {score}")
            
            # Calculate percentage for grade determination
            percentage = (score / total_marks) * 100
            print(f"Percentage: {percentage}")
            
            # Get grade letter based on percentage
            cursor.execute("""
            SELECT TOP 1 grade_letter, grade_points 
            FROM GradeScales 
            WHERE ? BETWEEN min_percentage AND max_percentage
            ORDER BY min_percentage
            """, (percentage,))
            
            grade = cursor.fetchone()
            grade_letter = grade[0] if grade else 'F'
            grade_points = float(grade[1]) if grade else 0.0
            print(f"Grade: {grade_letter}, Points: {grade_points}")
            
            if existing:
                # Update existing
                print("Updating existing record...")
                cursor.execute("""
                UPDATE ExamResults
                SET score = ?, grade_letter = ?, grade_points = ?,
                    remarks = ?, last_updated = GETDATE(), updated_by = ?
                WHERE exam_id = ? AND student_id = ?
                """, (
                    score,
                    grade_letter,
                    grade_points,
                    data.get('remarks', ''),
                    data['entered_by'],
                    data['exam_id'],
                    data['student_id']
                ))
                print(f"Rows affected: {cursor.rowcount}")
                result_id = existing[0]
            else:
                # Insert new
                print("Inserting new record...")
                print(f"Inserting with exam_id: {data['exam_id']}, student_id: {data['student_id']}")
                cursor.execute("""
                INSERT INTO ExamResults (exam_id, student_id, score, grade_letter, grade_points, remarks, entered_by, entered_at)
                OUTPUT INSERTED.result_id
                VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    data['exam_id'],
                    data['student_id'],
                    score,
                    grade_letter,
                    grade_points,
                    data.get('remarks', ''),
                    data['entered_by']
                ))
                result_id = cursor.fetchone()[0]
                print(f"New result_id: {result_id}")
            
            db.commit()
            print("Commit successful")
            return result_id
            
        except Exception as e:
            print(f"ERROR in ExamResults.create_or_update: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return None
        finally:
            cursor.close()
            print("=" * 50)
    
    @staticmethod
    def get_exam_results(exam_id):
        """Get all results for an exam"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("SELECT total_marks FROM Exams WHERE exam_id = ?", (exam_id,))
            exam = cursor.fetchone()
            total_marks = float(exam[0]) if exam else 0
            
            cursor.execute("""
            SELECT er.*, s.first_name_ar, s.last_name_ar, s.student_number
            FROM ExamResults er
            JOIN Students s ON er.student_id = s.student_id
            WHERE er.exam_id = ?
            ORDER BY s.first_name_ar
            """, (exam_id,))
            
            if cursor.description is None:
                return []
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                # Convert Decimal to float
                if 'score' in result:
                    result['marks_obtained'] = float(result['score'])  # Map to expected field name
                if 'grade_points' in result and result['grade_points'] is not None:
                    result['grade_points'] = float(result['grade_points'])
                if total_marks > 0:
                    result['percentage'] = round((float(result['score']) / total_marks) * 100, 2)
                else:
                    result['percentage'] = 0
                results.append(result)
            
            return results
        except Exception as e:
            print(f"Error in ExamResults.get_exam_results: {e}")
            return []
        finally:
            cursor.close()
    
    @staticmethod
    def get_student_results(student_id, academic_year_id=None):
        """Get all results for a student"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            query = """
            SELECT er.*, e.exam_name_ar, e.exam_name_en, e.exam_date, e.total_marks,
                   et.type_name_ar, et.type_name_en,
                   s.subject_name_ar, s.subject_name_en,
                   c.class_name_ar
            FROM ExamResults er
            JOIN Exams e ON er.exam_id = e.exam_id
            JOIN ExamTypes et ON e.exam_type_id = et.exam_type_id
            JOIN Subjects s ON e.subject_id = s.subject_id
            JOIN Classes c ON e.class_id = c.class_id
            WHERE er.student_id = ?
            """
            params = [student_id]
            
            if academic_year_id:
                query += " AND e.academic_year_id = ?"
                params.append(academic_year_id)
            
            query += " ORDER BY e.exam_date DESC"
            
            cursor.execute(query, params)
            
            if cursor.description is None:
                return []
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                # Convert Decimal to float and map fields
                if 'score' in result:
                    result['marks_obtained'] = float(result['score'])
                if 'total_marks' in result:
                    total = float(result['total_marks'])
                    if total > 0:
                        result['percentage'] = round((float(result['score']) / total) * 100, 2)
                    else:
                        result['percentage'] = 0
                results.append(result)
            
            return results
        except Exception as e:
            print(f"Error in ExamResults.get_student_results: {e}")
            return []
        finally:
            cursor.close()


class GradeScale:
    @staticmethod
    def get_all():
        """Get all grade scales"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("SELECT * FROM GradeScales WHERE is_active = 1 ORDER BY min_percentage DESC")
            
            if cursor.description is None:
                return []
            
            columns = [column[0] for column in cursor.description]
            scales = []
            
            for row in cursor.fetchall():
                scales.append(dict(zip(columns, row)))
            
            return scales
        except Exception as e:
            print(f"Error in GradeScale.get_all: {e}")
            return []
        finally:
            cursor.close()