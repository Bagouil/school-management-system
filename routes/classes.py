from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.class_ import Class
from models.teacher import Teacher
from models.student import Student
from database.db_config import get_db
from datetime import datetime

classes_bp = Blueprint('classes', __name__)

@classes_bp.route('/')
def list_classes():
    """List all classes"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    classes = Class.get_all_active()
    
    # Get statistics
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM Classes WHERE academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)")
    total_classes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Classes WHERE class_teacher_id IS NOT NULL")
    classes_with_teacher = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Subjects WHERE is_active = 1")
    total_subjects = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Students WHERE status = 'active'")
    total_students = cursor.fetchone()[0]
    
    # Get grade levels for add form
    cursor.execute("SELECT * FROM GradeLevels ORDER BY grade_order")
    grade_columns = [column[0] for column in cursor.description]
    grade_levels = []
    for row in cursor.fetchall():
        grade_levels.append(dict(zip(grade_columns, row)))
    
    # Get academic years
    cursor.execute("SELECT * FROM AcademicYears ORDER BY start_date DESC")
    year_columns = [column[0] for column in cursor.description]
    academic_years = []
    for row in cursor.fetchall():
        academic_years.append(dict(zip(year_columns, row)))
    
    # Get teachers for assignment
    cursor.execute("SELECT teacher_id, first_name_ar, last_name_ar, specialization, teacher_image FROM Teachers WHERE status = 'active'")
    teachers = []
    for row in cursor.fetchall():
        teachers.append({
            'teacher_id': row[0],
            'first_name_ar': row[1],
            'last_name_ar': row[2],
            'specialization': row[3],
            'teacher_image': row[4]
        })
    
    cursor.close()
    
    return render_template('classes/list.html',
                         classes=classes,
                         total_classes=total_classes,
                         classes_with_teacher=classes_with_teacher,
                         total_subjects=total_subjects,
                         total_students=total_students,
                         grade_levels=grade_levels,
                         academic_years=academic_years,
                         teachers=teachers)

@classes_bp.route('/add', methods=['POST'])
def add_class():
    """Add new class"""
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('classes.list_classes'))
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get current academic year
        cursor.execute("SELECT year_id FROM AcademicYears WHERE is_current = 1")
        year_id = cursor.fetchone()[0]
        
        data = {
            'grade_id': request.form['grade_id'],
            'class_name_ar': request.form['class_name_ar'],
            'class_name_en': request.form.get('class_name_en', ''),
            'academic_year_id': year_id,
            'capacity': int(request.form.get('capacity', 30)),
            'class_teacher_id': request.form.get('class_teacher_id') or None
        }
        
        class_id = Class.create(data)
        flash('Class added successfully', 'success')
        
    except Exception as e:
        flash(f'Error adding class: {str(e)}', 'danger')
    
    return redirect(url_for('classes.list_classes'))
@classes_bp.route('/<int:class_id>/edit', methods=['GET', 'POST'])
def edit_class(class_id):
    """Edit class information"""
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        flash('Class not found', 'danger')
        return redirect(url_for('classes.list_classes'))
    
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        try:
            data = {
                'grade_id': request.form['grade_id'],
                'class_name_ar': request.form['class_name_ar'],
                'class_name_en': request.form.get('class_name_en', ''),
                'capacity': int(request.form.get('capacity', 30)),
                'class_teacher_id': request.form.get('class_teacher_id') or None
            }
            
            if Class.update(class_id, data):
                flash('Class updated successfully', 'success')
                return redirect(url_for('classes.view_class', class_id=class_id))
            else:
                flash('No changes were made', 'info')
                
        except Exception as e:
            flash(f'Error updating class: {str(e)}', 'danger')
            db.rollback()
    
    # Get grade levels for dropdown
    cursor.execute("SELECT * FROM GradeLevels ORDER BY grade_order")
    grade_columns = [column[0] for column in cursor.description]
    grade_levels = []
    for row in cursor.fetchall():
        grade_levels.append(dict(zip(grade_columns, row)))
    
    # Get teachers for dropdown
    cursor.execute("SELECT teacher_id, first_name_ar, last_name_ar FROM Teachers WHERE status = 'active'")
    teachers = []
    for row in cursor.fetchall():
        teachers.append({
            'teacher_id': row[0],
            'first_name_ar': row[1],
            'last_name_ar': row[2]
        })
    
    cursor.close()
    
    return render_template('classes/edit_class.html',
                         class_obj=class_obj,
                         grade_levels=grade_levels,
                         teachers=teachers)
@classes_bp.route('/<int:class_id>')
def view_class(class_id):
    """View class details"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        flash('Class not found', 'danger')
        return redirect(url_for('classes.list_classes'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get students in this class - FIXED: qualified column names
    cursor.execute("""
    SELECT 
        s.student_id, 
        s.first_name_ar, 
        s.last_name_ar, 
        s.student_number, 
        s.gender, 
        s.birth_date
    FROM Students s
    WHERE s.current_class_id = ? AND s.status = 'active'
    ORDER BY s.first_name_ar
    """, (class_id,))
    
    columns = [column[0] for column in cursor.description]
    students = []
    for row in cursor.fetchall():
        students.append(dict(zip(columns, row)))
    
    # Get subjects with teachers - FIXED: qualified column names
    cursor.execute("""
    SELECT 
        cs.class_subject_id,
        cs.subject_id,
        cs.teacher_id,
        cs.hours_per_week,
        s.subject_name_ar, 
        s.subject_name_en, 
        s.subject_code,
        t.teacher_id as teacher_id,
        CONCAT(t.first_name_ar, ' ', t.last_name_ar) as teacher_name
    FROM ClassSubjects cs
    JOIN Subjects s ON cs.subject_id = s.subject_id
    LEFT JOIN Teachers t ON cs.teacher_id = t.teacher_id
    WHERE cs.class_id = ? AND cs.academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)
    ORDER BY s.subject_name_ar
    """, (class_id,))
    
    subjects = []
    total_hours = 0
    subject_columns = [column[0] for column in cursor.description]
    for row in cursor.fetchall():
        subject = dict(zip(subject_columns, row))
        subjects.append(subject)
        total_hours += subject.get('hours_per_week', 0)
    
    # Get teachers with their subjects - FIXED: qualified column names
    cursor.execute("""
    SELECT DISTINCT 
        t.teacher_id, 
        t.first_name_ar, 
        t.last_name_ar, 
        t.specialization, 
        t.teacher_image,
        tc.is_class_teacher
    FROM TeacherClasses tc
    JOIN Teachers t ON tc.teacher_id = t.teacher_id
    WHERE tc.class_id = ? AND tc.academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)
    """, (class_id,))
    
    teachers = []
    for teacher_row in cursor.fetchall():
        teacher = {
            'teacher_id': teacher_row[0],
            'first_name_ar': teacher_row[1],
            'last_name_ar': teacher_row[2],
            'specialization': teacher_row[3],
            'teacher_image': teacher_row[4],
            'is_class_teacher': teacher_row[5],
            'subjects': []
        }
        
        # Get subjects for this teacher in this class
        cursor.execute("""
        SELECT s.subject_name_ar
        FROM TeacherSubjects ts
        JOIN Subjects s ON ts.subject_id = s.subject_id
        WHERE ts.teacher_id = ? AND ts.class_id = ? 
          AND ts.academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)
        """, (teacher['teacher_id'], class_id))
        
        for subj_row in cursor.fetchall():
            teacher['subjects'].append({'subject_name_ar': subj_row[0]})
        
        teachers.append(teacher)
    
    # Get current academic year
    cursor.execute("SELECT year_name_ar FROM AcademicYears WHERE is_current = 1")
    academic_year_row = cursor.fetchone()
    academic_year = {'year_name_ar': academic_year_row[0] if academic_year_row else ''}
    
    # Calculate attendance rate for last 30 days - FIXED: qualified column names
    from datetime import datetime, timedelta
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    cursor.execute("""
    SELECT 
        COUNT(CASE WHEN sa.status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as attendance_rate
    FROM StudentAttendance sa
    JOIN Students s ON sa.student_id = s.student_id
    WHERE s.current_class_id = ? AND sa.attendance_date >= ?
    """, (class_id, thirty_days_ago))
    
    attendance_rate_row = cursor.fetchone()
    attendance_rate = attendance_rate_row[0] if attendance_rate_row and attendance_rate_row[0] else 0
    attendance_rate = round(float(attendance_rate), 1)
    
    # Recent activities - you can customize these based on actual data
    recent_activities = [
        {
            'icon': 'fa-user-plus',
            'color': '#28A745',
            'title': 'New Student Added' if session.get('language') != 'ar' else 'إضافة طالب جديد',
            'description': 'Student joined the class' if session.get('language') != 'ar' else 'طالب انضم للصف',
            'time': '2 hours ago' if session.get('language') != 'ar' else 'قبل ساعتين'
        },
        {
            'icon': 'fa-chalkboard-teacher',
            'color': '#875A7B',
            'title': 'Teacher Assigned' if session.get('language') != 'ar' else 'تعيين معلم',
            'description': 'Teacher assigned to subject' if session.get('language') != 'ar' else 'تم تعيين معلم لمادة',
            'time': '1 day ago' if session.get('language') != 'ar' else 'قبل يوم'
        },
        {
            'icon': 'fa-calendar-check',
            'color': '#17A2B8',
            'title': 'Attendance Marked' if session.get('language') != 'ar' else 'تسجيل حضور',
            'description': f'Attendance recorded for {len(students)} students' if session.get('language') != 'ar' else f'تم تسجيل حضور {len(students)} طالب',
            'time': '1 day ago' if session.get('language') != 'ar' else 'قبل يوم'
        },
    ]
    
    cursor.close()
    
    return render_template('classes/class_detail.html',
                         class_obj=class_obj,
                         students=students,
                         subjects=subjects,
                         teachers=teachers,
                         academic_year=academic_year,
                         total_hours=total_hours,
                         attendance_rate=attendance_rate,
                         recent_activities=recent_activities)

@classes_bp.route('/<int:class_id>/subjects')
def manage_subjects(class_id):
    """Manage class subjects"""
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('classes.list_classes'))
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        flash('Class not found', 'danger')
        return redirect(url_for('classes.list_classes'))
    
    subjects = Class.get_subjects(class_id)
    student_count = len(Class.get_students(class_id))
    
    # Get available subjects
    db = get_db()
    cursor = db.cursor()
    
    # Get all subjects
    cursor.execute("SELECT * FROM Subjects WHERE is_active = 1 ORDER BY subject_name_ar")
    columns = [column[0] for column in cursor.description]
    all_subjects = []
    for row in cursor.fetchall():
        all_subjects.append(dict(zip(columns, row)))
    
    # Filter out already added subjects
    added_subject_ids = [s['subject_id'] for s in subjects]
    available_subjects = [s for s in all_subjects if s['subject_id'] not in added_subject_ids]
    
    # Get teachers
    cursor.execute("""
    SELECT teacher_id, first_name_ar, last_name_ar 
    FROM Teachers WHERE status = 'active'
    ORDER BY first_name_ar
    """)
    teachers = []
    for row in cursor.fetchall():
        teachers.append({
            'teacher_id': row[0],
            'first_name_ar': row[1],
            'last_name_ar': row[2]
        })
    
    cursor.close()
    
    return render_template('classes/subjects.html',
                         class_obj=class_obj,
                         subjects=subjects,
                         available_subjects=available_subjects,
                         teachers=teachers,
                         student_count=student_count)

@classes_bp.route('/<int:class_id>/subjects/add', methods=['POST'])
def add_subject(class_id):
    """Add subject to class"""
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('classes.list_classes'))
    
    try:
        subject_id = request.form['subject_id']
        teacher_id = request.form.get('teacher_id') or None
        hours_per_week = int(request.form.get('hours_per_week', 4))
        
        Class.add_subject(class_id, subject_id, teacher_id, hours_per_week)
        flash('Subject added to class successfully', 'success')
        
    except Exception as e:
        flash(f'Error adding subject: {str(e)}', 'danger')
    
    return redirect(url_for('classes.manage_subjects', class_id=class_id))

@classes_bp.route('/subject/assign-teacher', methods=['POST'])
def assign_teacher_to_subject():
    """Assign teacher to class subject"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        class_subject_id = data['class_subject_id']
        teacher_id = data.get('teacher_id')
        hours_per_week = data.get('hours_per_week', 4)
        
        Class.update_subject(class_subject_id, teacher_id, hours_per_week)
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@classes_bp.route('/subject/remove', methods=['POST'])
def remove_subject():
    """Remove subject from class"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        class_subject_id = data['class_subject_id']
        
        Class.remove_subject(class_subject_id)
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@classes_bp.route('/<int:class_id>/assign-teacher')
def assign_teacher(class_id):
    """Page to assign class teacher"""
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('classes.list_classes'))
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        flash('Class not found', 'danger')
        return redirect(url_for('classes.list_classes'))
    
    # Get student count
    students = Class.get_students(class_id)
    student_count = len(students)
    
    # Get available teachers
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
    SELECT teacher_id, first_name_ar, last_name_ar, teacher_number 
    FROM Teachers WHERE status = 'active'
    ORDER BY first_name_ar
    """)
    teachers = []
    for row in cursor.fetchall():
        teachers.append({
            'teacher_id': row[0],
            'first_name_ar': row[1],
            'last_name_ar': row[2],
            'teacher_number': row[3]
        })
    cursor.close()
    
    return render_template('classes/assign_teacher.html',
                         class_obj=class_obj,
                         teachers=teachers,
                         student_count=student_count)

@classes_bp.route('/<int:class_id>/assign-teacher', methods=['POST'])
def save_class_teacher(class_id):
    """Save class teacher assignment"""
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('classes.list_classes'))
    
    try:
        teacher_id = request.form.get('teacher_id') or None
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE Classes SET class_teacher_id = ? WHERE class_id = ?", (teacher_id, class_id))
        db.commit()
        cursor.close()
        
        flash('Class teacher assigned successfully', 'success')
        
    except Exception as e:
        flash(f'Error assigning teacher: {str(e)}', 'danger')
    
    return redirect(url_for('classes.view_class', class_id=class_id))