from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.teacher import Teacher
from models.audit import AuditLog
from database.db_config import get_db
import hashlib
from datetime import date
from utils.permission_decorator import role_required

# Use teachers_bp (plural) to match the import in app.py
teachers_bp = Blueprint('teachers', __name__)

@teachers_bp.route('/')
@role_required('admin')
def list_teachers():
    """List all teachers"""

    # Get filter parameter
    status_filter = request.args.get('status', 'active')  # Default to active
    
    db = get_db()
    cursor = db.cursor()
    
    # Get all teachers based on status filter
    if status_filter == 'all':
        cursor.execute("""
        SELECT * FROM Teachers 
        ORDER BY 
            CASE status 
                WHEN 'active' THEN 1 
                WHEN 'inactive' THEN 2 
                ELSE 3 
            END, 
            first_name_ar
        """)
    else:
        cursor.execute("""
        SELECT * FROM Teachers 
        WHERE status = ?
        ORDER BY first_name_ar
        """, (status_filter,))
    
    columns = [column[0] for column in cursor.description]
    teachers = []
    specializations = set()
    
    for row in cursor.fetchall():
        teacher = dict(zip(columns, row))
        teachers.append(teacher)
        if teacher.get('specialization'):
            specializations.add(teacher['specialization'])
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) FROM Teachers WHERE status = 'active'")
    active_teachers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Teachers WHERE status = 'inactive'")
    inactive_teachers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Teachers WHERE status = 'resigned'")
    resigned_teachers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT class_teacher_id) FROM Classes WHERE class_teacher_id IS NOT NULL")
    class_teachers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT subject_id) FROM TeacherSubjects")
    total_subjects = cursor.fetchone()[0]
    
    cursor.close()
    
    total_teachers = active_teachers + inactive_teachers + resigned_teachers
    
    return render_template('teachers/list.html',
                         teachers=teachers,
                         total_teachers=total_teachers,
                         active_teachers=active_teachers,
                         inactive_teachers=inactive_teachers,
                         resigned_teachers=resigned_teachers,
                         class_teachers=class_teachers,
                         total_subjects=total_subjects,
                         specializations=list(specializations),
                         current_status=status_filter)

@teachers_bp.route('/add', methods=['GET', 'POST'])
@role_required('admin')
def add_teacher():
    """Add new teacher"""
    
    today = date.today().isoformat()
    
    if request.method == 'POST':
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Generate teacher number
            cursor.execute("SELECT ISNULL(MAX(CAST(RIGHT(teacher_number, 3) AS INT)), 0) + 1 FROM Teachers")
            next_num = cursor.fetchone()[0]
            teacher_number = f"TCH{str(next_num).zfill(3)}"
            
            # Insert teacher
            cursor.execute("""
            INSERT INTO Teachers (
                teacher_number, first_name_ar, last_name_ar, first_name_en, last_name_en,
                birth_date, gender, qualification, specialization, hire_date,
                phone, email, address, salary, national_id, bank_account, status
            ) OUTPUT INSERTED.teacher_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (
                teacher_number,
                request.form['first_name_ar'],
                request.form['last_name_ar'],
                request.form.get('first_name_en', ''),
                request.form.get('last_name_en', ''),
                request.form['birth_date'],
                request.form['gender'],
                request.form['qualification'],
                request.form['specialization'],
                request.form['hire_date'],
                request.form['phone'],
                request.form['email'],
                request.form.get('address', ''),
                float(request.form['salary']),
                request.form.get('national_id', ''),
                request.form.get('bank_account', '')
            ))
            
            teacher_id = cursor.fetchone()[0]
            
            # Create user account for teacher
            username = request.form['email'].split('@')[0]
            password = 'teacher123'  # Default password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Check if username already exists
            cursor.execute("SELECT user_id FROM Users WHERE username = ?", (username,))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO Users (username, password_hash, email, role, full_name_ar, full_name_en, is_active)
                VALUES (?, ?, ?, 'teacher', ?, ?, 1)
                """, (
                    username,
                    password_hash,
                    request.form['email'],
                    request.form['first_name_ar'] + ' ' + request.form['last_name_ar'],
                    request.form.get('first_name_en', '') + ' ' + request.form.get('last_name_en', '')
                ))
            
            db.commit()
            flash(f'Teacher added successfully! Username: {username}, Password: {password}', 'success')
            return redirect(url_for('teachers.list_teachers'))
            
        except Exception as e:
            flash(f'Error adding teacher: {str(e)}', 'danger')
            db.rollback()
    
    return render_template('teachers/add.html', today=today)
@teachers_bp.route('/<int:teacher_id>/delete', methods=['POST'])
@role_required('admin')
def delete_teacher(teacher_id):
    """Delete teacher"""

    
    teacher = Teacher.get_by_id(teacher_id)
    if not teacher:
        flash('Teacher not found', 'danger')
        return redirect(url_for('teachers.list_teachers'))
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check what status values are allowed
        cursor.execute("""
        SELECT CONSTRAINT_NAME, CHECK_CLAUSE 
        FROM INFORMATION_SCHEMA.CHECK_CONSTRAINTS 
        WHERE CONSTRAINT_NAME LIKE '%status%'
        """)
        constraints = cursor.fetchall()
        print("Status constraints:", constraints)
        
        # Get teacher data for audit log
        teacher_name = f"{teacher['first_name_ar']} {teacher['last_name_ar']}"
        teacher_number = teacher['teacher_number']
        
        # Option 1: Set status to 'inactive' (which should be allowed)
        cursor.execute("UPDATE Teachers SET status = 'inactive' WHERE teacher_id = ?", (teacher_id,))
        
        # Option 2: If you want to permanently delete, you might need to drop the constraint first
        # But let's use 'inactive' for now
        
        db.commit()
        
        # ========== ADD AUDIT LOG HERE ==========
        from models.audit import AuditLog
        AuditLog.log_action(
            action_type='DELETE',
            table_name='Teachers',
            record_id=teacher_id,
            old_data={
                'name': teacher_name,
                'teacher_number': teacher_number,
                'email': teacher.get('email'),
                'specialization': teacher.get('specialization'),
                'status': teacher.get('status')
            },
            new_data={'status': 'inactive'},
            description=f'Teacher deactivated: {teacher_name} ({teacher_number})'
        )
        # ========== END AUDIT LOG ==========
        
        flash('Teacher deactivated successfully', 'success')
        
    except Exception as e:
        print(f"Error deleting teacher: {e}")
        flash(f'Error deactivating teacher: {str(e)}', 'danger')
        db.rollback()
    finally:
        cursor.close()
    
    return redirect(url_for('teachers.list_teachers'))
@teachers_bp.route('/<int:teacher_id>/reactivate', methods=['POST'])
@teachers_bp.route('/<int:teacher_id>/permanent-delete', methods=['POST'])
@role_required('admin')
def permanent_delete_teacher(teacher_id):
    """Permanently delete a teacher (only for inactive teachers)"""

    
    teacher = Teacher.get_by_id(teacher_id)
    if not teacher:
        flash('Teacher not found', 'danger')
        return redirect(url_for('teachers.list_teachers'))
    
    # Only allow permanent deletion of inactive teachers
    if teacher['status'] != 'inactive':
        flash('Only inactive teachers can be permanently deleted', 'danger')
        return redirect(url_for('teachers.list_teachers'))
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        teacher_name = f"{teacher['first_name_ar']} {teacher['last_name_ar']}"
        teacher_number = teacher['teacher_number']
        
        # First, check if teacher is referenced in other tables
        cursor.execute("SELECT COUNT(*) FROM TeacherClasses WHERE teacher_id = ?", (teacher_id,))
        class_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM TeacherSubjects WHERE teacher_id = ?", (teacher_id,))
        subject_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Classes WHERE class_teacher_id = ?", (teacher_id,))
        class_teacher_count = cursor.fetchone()[0]
        
        if class_count > 0 or subject_count > 0 or class_teacher_count > 0:
            # Teacher is still referenced - show error
            error_msg = "Cannot delete teacher because they are still assigned to:"
            if class_count > 0:
                error_msg += f"\n- {class_count} class(es)"
            if subject_count > 0:
                error_msg += f"\n- {subject_count} subject(s)"
            if class_teacher_count > 0:
                error_msg += f"\n- {class_teacher_count} class(es) as class teacher"
            
            flash(error_msg, 'danger')
            return redirect(url_for('teachers.list_teachers', status='inactive'))
        
        # If no references, proceed with deletion
        cursor.execute("DELETE FROM Teachers WHERE teacher_id = ?", (teacher_id,))
        db.commit()
        
        from models.audit import AuditLog
        AuditLog.log_action(
            action_type='DELETE',
            table_name='Teachers',
            record_id=teacher_id,
            old_data={
                'name': teacher_name,
                'teacher_number': teacher_number,
                'email': teacher.get('email')
            },
            description=f'Teacher permanently deleted: {teacher_name} ({teacher_number})'
        )
        
        flash('Teacher permanently deleted successfully', 'success')
        
    except Exception as e:
        print(f"Error deleting teacher: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error deleting teacher: {str(e)}', 'danger')
        db.rollback()
    finally:
        cursor.close()
    
    return redirect(url_for('teachers.list_teachers', status='inactive'))
@teachers_bp.route('/<int:teacher_id>/check-delete')
@role_required('admin')
def check_teacher_delete(teacher_id):
    """Check if teacher can be deleted and show assignments"""

    
    teacher = Teacher.get_by_id(teacher_id)
    if not teacher:
        flash('Teacher not found', 'danger')
        return redirect(url_for('teachers.list_teachers'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get teacher's class assignments
    cursor.execute("""
    SELECT c.class_name_ar, c.class_id, tc.is_class_teacher
    FROM TeacherClasses tc
    JOIN Classes c ON tc.class_id = c.class_id
    WHERE tc.teacher_id = ?
    """, (teacher_id,))
    
    class_assignments = []
    for row in cursor.fetchall():
        class_assignments.append({
            'class_name': row[0],
            'class_id': row[1],
            'is_class_teacher': row[2]
        })
    
    # Get teacher's subject assignments
    cursor.execute("""
    SELECT s.subject_name_ar, c.class_name_ar
    FROM TeacherSubjects ts
    JOIN Subjects s ON ts.subject_id = s.subject_id
    JOIN Classes c ON ts.class_id = c.class_id
    WHERE ts.teacher_id = ?
    """, (teacher_id,))
    
    subject_assignments = []
    for row in cursor.fetchall():
        subject_assignments.append({
            'subject': row[0],
            'class': row[1]
        })
    
    cursor.close()
    
    return render_template('teachers/check_delete.html',
                         teacher=teacher,
                         class_assignments=class_assignments,
                         subject_assignments=subject_assignments)
@role_required('admin')
def reactivate_teacher(teacher_id):
    """Reactivate a deactivated teacher"""

    
    teacher = Teacher.get_by_id(teacher_id)
    if not teacher:
        flash('Teacher not found', 'danger')
        return redirect(url_for('teachers.list_teachers'))
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("UPDATE Teachers SET status = 'active' WHERE teacher_id = ?", (teacher_id,))
        db.commit()
        
        teacher_name = f"{teacher['first_name_ar']} {teacher['last_name_ar']}"
        
        from models.audit import AuditLog
        AuditLog.log_action(
            action_type='UPDATE',
            table_name='Teachers',
            record_id=teacher_id,
            old_data={'status': 'inactive'},
            new_data={'status': 'active'},
            description=f'Teacher reactivated: {teacher_name}'
        )
        
        flash('Teacher reactivated successfully', 'success')
        
    except Exception as e:
        flash(f'Error reactivating teacher: {str(e)}', 'danger')
        db.rollback()
    finally:
        cursor.close()
    
    return redirect(url_for('teachers.list_teachers'))
@teachers_bp.route('/<int:teacher_id>')
def view_teacher(teacher_id):
    """View teacher details"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    teacher = Teacher.get_by_id(teacher_id)
    if not teacher:
        flash('Teacher not found', 'danger')
        return redirect(url_for('teachers.list_teachers'))
    
    # Get current academic year
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT year_id FROM AcademicYears WHERE is_current = 1")
    current_year = cursor.fetchone()
    year_id = current_year[0] if current_year else None
    
    # Get teacher's classes and subjects
    classes = Teacher.get_teacher_classes(teacher_id, year_id)
    subjects = Teacher.get_teacher_subjects(teacher_id, year_id)
    cursor.close()
    
    return render_template('teachers/view.html', teacher=teacher, classes=classes, subjects=subjects)

@teachers_bp.route('/<int:teacher_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit_teacher(teacher_id):
    """Edit teacher information"""

    
    teacher = Teacher.get_by_id(teacher_id)
    if not teacher:
        flash('Teacher not found', 'danger')
        return redirect(url_for('teachers.list_teachers'))
    
    if request.method == 'POST':
        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute("""
            UPDATE Teachers
            SET first_name_ar = ?, last_name_ar = ?, first_name_en = ?, last_name_en = ?,
                birth_date = ?, gender = ?, qualification = ?, specialization = ?,
                phone = ?, email = ?, address = ?, salary = ?
            WHERE teacher_id = ?
            """, (
                request.form['first_name_ar'],
                request.form['last_name_ar'],
                request.form.get('first_name_en', ''),
                request.form.get('last_name_en', ''),
                request.form['birth_date'],
                request.form['gender'],
                request.form['qualification'],
                request.form['specialization'],
                request.form['phone'],
                request.form['email'],
                request.form.get('address', ''),
                float(request.form['salary']),
                teacher_id
            ))
            
            db.commit()
            cursor.close()
            flash('Teacher updated successfully', 'success')
            return redirect(url_for('teachers.view_teacher', teacher_id=teacher_id))
            
        except Exception as e:
            flash(f'Error updating teacher: {str(e)}', 'danger')
            db.rollback()
    
    return render_template('teachers/edit.html', teacher=teacher)

@teachers_bp.route('/<int:teacher_id>/assign-classes', methods=['GET', 'POST'])
@role_required('admin')
def assign_classes(teacher_id):
    """Assign classes to teacher"""

    
    teacher = Teacher.get_by_id(teacher_id)
    if not teacher:
        flash('Teacher not found', 'danger')
        return redirect(url_for('teachers.list_teachers'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get current academic year
    cursor.execute("SELECT year_id FROM AcademicYears WHERE is_current = 1")
    current_year = cursor.fetchone()
    year_id = current_year[0] if current_year else None
    
    if request.method == 'POST':
        class_ids = request.form.getlist('class_ids[]')
        is_class_teacher = request.form.getlist('is_class_teacher[]')
        
        # Remove existing assignments
        cursor.execute("DELETE FROM TeacherClasses WHERE teacher_id = ? AND academic_year_id = ?", 
                      (teacher_id, year_id))
        
        # Add new assignments
        for class_id in class_ids:
            is_ct = '1' if class_id in is_class_teacher else '0'
            cursor.execute("""
            INSERT INTO TeacherClasses (teacher_id, class_id, academic_year_id, is_class_teacher)
            VALUES (?, ?, ?, ?)
            """, (teacher_id, class_id, year_id, is_ct))
            
            # If this is class teacher, update Classes table
            if is_ct == '1':
                cursor.execute("UPDATE Classes SET class_teacher_id = ? WHERE class_id = ?", 
                             (teacher_id, class_id))
        
        db.commit()
        flash('Classes assigned successfully', 'success')
        return redirect(url_for('teachers.view_teacher', teacher_id=teacher_id))
    
    # GET request - show assignment form
    # Get all classes
    cursor.execute("""
    SELECT c.*, g.grade_name_ar, g.grade_name_en
    FROM Classes c
    JOIN GradeLevels g ON c.grade_id = g.grade_id
    WHERE c.academic_year_id = ?
    ORDER BY g.grade_order, c.class_name_ar
    """, (year_id,))
    
    columns = [column[0] for column in cursor.description]
    all_classes = []
    for row in cursor.fetchall():
        all_classes.append(dict(zip(columns, row)))
    
    # Get teacher's current classes
    cursor.execute("""
    SELECT class_id, is_class_teacher 
    FROM TeacherClasses 
    WHERE teacher_id = ? AND academic_year_id = ?
    """, (teacher_id, year_id))
    
    current_class_ids = []
    current_class_teacher_ids = []
    for row in cursor.fetchall():
        current_class_ids.append(row[0])
        if row[1]:  # is_class_teacher
            current_class_teacher_ids.append(row[0])
    
    cursor.close()
    
    return render_template('teachers/assign_classes.html',
                         teacher=teacher,
                         all_classes=all_classes,
                         current_class_ids=current_class_ids,
                         current_class_teacher_ids=current_class_teacher_ids)