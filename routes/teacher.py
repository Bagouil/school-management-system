from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.db_config import get_db
from datetime import datetime, date
from models.teacher import Teacher
from models.class_ import Class
from models.attendance import StudentAttendance
from models.exam import Exam

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/dashboard')
def dashboard():
    """Teacher dashboard"""
    if 'user_id' not in session or session['role'] not in ['teacher', 'supervisor']:
        flash('Access denied', 'danger')
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('teacher_id')
    
    # If teacher_id not in session, try to find it
    if not teacher_id:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT teacher_id FROM Teachers WHERE email = ? OR phone = ?", 
                     (session.get('username'), session.get('username')))
        teacher = cursor.fetchone()
        cursor.close()
        
        if teacher:
            teacher_id = teacher[0]
            session['teacher_id'] = teacher_id
        else:
            flash('Teacher profile not linked to this user account', 'danger')
            return redirect(url_for('auth.logout'))
    
    db = get_db()
    cursor = db.cursor()
    
    today = date.today().isoformat()
    teacher_name = session.get('full_name', 'Teacher')
    
    # Get current academic year
    cursor.execute("SELECT year_id FROM AcademicYears WHERE is_current = 1")
    current_year = cursor.fetchone()
    year_id = current_year[0] if current_year else None
    
    # Get teacher's classes with student counts and attendance rates
    # FIXED: Added table aliases to all column references
    cursor.execute("""
    SELECT 
        c.class_id,
        c.class_name_ar,
        c.class_name_en,
        c.capacity,
        g.grade_name_ar,
        tc.is_class_teacher,
        (SELECT COUNT(*) FROM Students s WHERE s.current_class_id = c.class_id AND s.status = 'active') as student_count
    FROM TeacherClasses tc
    JOIN Classes c ON tc.class_id = c.class_id
    JOIN GradeLevels g ON c.grade_id = g.grade_id
    WHERE tc.teacher_id = ? AND tc.academic_year_id = ?
    ORDER BY g.grade_order, c.class_name_ar
    """, (teacher_id, year_id))
    
    columns = [column[0] for column in cursor.description]
    classes = []
    total_students = 0
    
    for row in cursor.fetchall():
        class_dict = dict(zip(columns, row))
        
        # Calculate attendance rate for last 30 days
        from datetime import datetime, timedelta
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # FIXED: Added table aliases to avoid ambiguity
        cursor.execute("""
        SELECT 
            COUNT(CASE WHEN sa.status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as attendance_rate
        FROM StudentAttendance sa
        JOIN Students s ON sa.student_id = s.student_id
        WHERE s.current_class_id = ? AND sa.attendance_date >= ?
        """, (class_dict['class_id'], thirty_days_ago))
        
        rate = cursor.fetchone()[0]
        class_dict['attendance_rate'] = round(float(rate), 1) if rate else 0
        
        classes.append(class_dict)
        total_students += class_dict['student_count']
    
    # Get teacher's subjects
    cursor.execute("""
    SELECT 
        ts.teacher_subject_id,
        ts.subject_id,
        ts.class_id,
        s.subject_name_ar, 
        s.subject_name_en, 
        s.subject_code,
        c.class_name_ar
    FROM TeacherSubjects ts
    JOIN Subjects s ON ts.subject_id = s.subject_id
    JOIN Classes c ON ts.class_id = c.class_id
    WHERE ts.teacher_id = ? AND ts.academic_year_id = ?
    ORDER BY c.class_name_ar, s.subject_name_ar
    """, (teacher_id, year_id))
    
    subject_columns = [column[0] for column in cursor.description]
    subjects = []
    for row in cursor.fetchall():
        subjects.append(dict(zip(subject_columns, row)))
    
    # Get today's attendance percentage
    # FIXED: Added table aliases
    cursor.execute("""
    SELECT 
        COUNT(CASE WHEN sa.status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as today_attendance
    FROM StudentAttendance sa
    JOIN Students s ON sa.student_id = s.student_id
    JOIN TeacherClasses tc ON s.current_class_id = tc.class_id
    WHERE tc.teacher_id = ? AND sa.attendance_date = ?
    """, (teacher_id, today))
    
    today_attendance_row = cursor.fetchone()
    today_attendance = round(float(today_attendance_row[0]), 1) if today_attendance_row and today_attendance_row[0] else 0
    
    # Get today's schedule
    cursor.execute("""
    SELECT 
        tt.timetable_id,
        tt.start_time,
        tt.end_time,
        tt.room,
        s.subject_name_ar,
        c.class_name_ar
    FROM Timetable tt
    JOIN Subjects s ON tt.subject_id = s.subject_id
    JOIN Classes c ON tt.class_id = c.class_id
    WHERE tt.teacher_id = ? AND tt.day_of_week = ?
    ORDER BY tt.start_time
    """, (teacher_id, datetime.now().strftime('%A').lower()))
    
    schedule_columns = [column[0] for column in cursor.description]
    schedule = []
    for row in cursor.fetchall():
        schedule.append(dict(zip(schedule_columns, row)))
    
    # Get upcoming exams for teacher's classes
    cursor.execute("""
    SELECT TOP 5
        e.exam_id,
        e.exam_name_ar,
        e.exam_date,
        e.total_marks,
        s.subject_name_ar,
        c.class_name_ar
    FROM Exams e
    JOIN Subjects s ON e.subject_id = s.subject_id
    JOIN Classes c ON e.class_id = c.class_id
    JOIN TeacherClasses tc ON c.class_id = tc.class_id
    WHERE tc.teacher_id = ? AND e.exam_date >= ?
    ORDER BY e.exam_date
    """, (teacher_id, today))
    
    exam_columns = [column[0] for column in cursor.description]
    upcoming_exams = []
    for row in cursor.fetchall():
        upcoming_exams.append(dict(zip(exam_columns, row)))
    
    # Recent activities
    recent_activities = [
        {
            'icon': 'fa-calendar-check',
            'color': '#28A745',
            'title': 'Attendance Marked' if session.get('language') != 'ar' else 'تسجيل حضور',
            'description': f'You marked attendance for your classes today' if session.get('language') != 'ar' else 'قمت بتسجيل حضور فصولك اليوم',
            'time': 'Today' if session.get('language') != 'ar' else 'اليوم'
        },
        {
            'icon': 'fa-file-alt',
            'color': '#875A7B',
            'title': 'Upcoming Exam' if session.get('language') != 'ar' else 'امتحان قادم',
            'description': f'{upcoming_exams[0].get("exam_name_ar", "Exam")} on {upcoming_exams[0].get("exam_date", "")}' if upcoming_exams else ('No upcoming exams' if session.get('language') != 'ar' else 'لا توجد امتحانات قادمة'),
            'time': 'Soon' if session.get('language') != 'ar' else 'قريباً'
        },
    ]
    
    cursor.close()
    
    return render_template('teacher/dashboard.html',
                         classes=classes,
                         subjects=subjects,
                         total_students=total_students,
                         today_attendance=today_attendance,
                         schedule=schedule,
                         upcoming_exams=upcoming_exams,
                         recent_activities=recent_activities,
                         today=today,
                         teacher_name=teacher_name)

@teacher_bp.route('/my-students')
def my_students():
    """View all students in teacher's classes"""
    if 'user_id' not in session or session['role'] not in ['teacher', 'supervisor']:
        flash('Access denied', 'danger')
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        flash('Teacher profile not found', 'danger')
        return redirect(url_for('auth.logout'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get current academic year
    cursor.execute("SELECT year_id FROM AcademicYears WHERE is_current = 1")
    current_year = cursor.fetchone()
    year_id = current_year[0] if current_year else None
    
    # Get all students in teacher's classes
    cursor.execute("""
    SELECT DISTINCT
        s.student_id,
        s.student_number,
        s.first_name_ar,
        s.last_name_ar,
        s.first_name_en,
        s.last_name_en,
        s.gender,
        s.birth_date,
        c.class_name_ar,
        c.class_id
    FROM Students s
    JOIN Classes c ON s.current_class_id = c.class_id
    JOIN TeacherClasses tc ON c.class_id = tc.class_id
    WHERE tc.teacher_id = ? AND tc.academic_year_id = ? AND s.status = 'active'
    ORDER BY c.class_name_ar, s.first_name_ar
    """, (teacher_id, year_id))
    
    columns = [column[0] for column in cursor.description]
    students = []
    for row in cursor.fetchall():
        students.append(dict(zip(columns, row)))
    
    cursor.close()
    
    return render_template('teacher/my_students.html', students=students)

@teacher_bp.route('/class/<int:class_id>/students')
def class_students(class_id):
    """View students in a specific class"""
    if 'user_id' not in session or session['role'] not in ['teacher', 'supervisor']:
        flash('Access denied', 'danger')
        return redirect(url_for('auth.login'))
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        flash('Class not found', 'danger')
        return redirect(url_for('teacher.dashboard'))
    
    students = Class.get_students(class_id)
    
    return render_template('teacher/class_students.html', 
                         class_obj=class_obj,
                         students=students)

@teacher_bp.route('/class/<int:class_id>')
def class_detail(class_id):
    """View class details"""
    if 'user_id' not in session or session['role'] not in ['teacher', 'supervisor']:
        flash('Access denied', 'danger')
        return redirect(url_for('auth.login'))
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        flash('Class not found', 'danger')
        return redirect(url_for('teacher.dashboard'))
    
    students = Class.get_students(class_id)
    subjects = Class.get_subjects(class_id)
    
    return render_template('teacher/class_detail.html',
                         class_obj=class_obj,
                         students=students,
                         subjects=subjects)

@teacher_bp.route('/class-reports')
def class_reports():
    """View reports for teacher's classes"""
    if 'user_id' not in session or session['role'] not in ['teacher', 'supervisor']:
        flash('Access denied', 'danger')
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        flash('Teacher profile not found', 'danger')
        return redirect(url_for('auth.logout'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get current academic year
    cursor.execute("SELECT year_id FROM AcademicYears WHERE is_current = 1")
    current_year = cursor.fetchone()
    year_id = current_year[0] if current_year else None
    
    # Get teacher's classes with stats
    cursor.execute("""
    SELECT 
        c.class_id,
        c.class_name_ar,
        g.grade_name_ar,
        (SELECT COUNT(*) FROM Students WHERE current_class_id = c.class_id AND status = 'active') as student_count
    FROM TeacherClasses tc
    JOIN Classes c ON tc.class_id = c.class_id
    JOIN GradeLevels g ON c.grade_id = g.grade_id
    WHERE tc.teacher_id = ? AND tc.academic_year_id = ?
    ORDER BY g.grade_order, c.class_name_ar
    """, (teacher_id, year_id))
    
    classes = []
    for row in cursor.fetchall():
        classes.append({
            'class_id': row[0],
            'class_name_ar': row[1],
            'grade_name_ar': row[2],
            'student_count': row[3]
        })
    
    cursor.close()
    
    return render_template('teacher/class_reports.html', classes=classes)