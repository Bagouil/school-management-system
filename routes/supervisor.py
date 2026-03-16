from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.teacher import Teacher
from models.class_ import Class
from models.student import Student
from models.attendance import StudentAttendance
from database.db_config import get_db
from datetime import datetime, date

supervisor_bp = Blueprint('supervisor', __name__)

@supervisor_bp.route('/dashboard')
def dashboard():
    """Supervisor dashboard"""
    if 'user_id' not in session or session['role'] != 'supervisor':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    # Get teacher ID from session
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        # If no teacher_id, try to find it from email
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT teacher_id FROM Teachers WHERE email = ?", (session.get('username'),))
        teacher = cursor.fetchone()
        if teacher:
            session['teacher_id'] = teacher[0]
            teacher_id = teacher[0]
        else:
            flash('Teacher profile not linked to this user account', 'danger')
            return redirect(url_for('auth.logout'))
    
  
@supervisor_bp.route('/class/<int:class_id>')
def view_class(class_id):
    """View class details and students"""
    if 'user_id' not in session or session['role'] != 'supervisor':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        flash('Class not found', 'danger')
        return redirect(url_for('supervisor.dashboard'))
    
    students = Class.get_students(class_id)
    
    return render_template('supervisor/class_view.html',
                         class_obj=class_obj,
                         students=students)

@supervisor_bp.route('/class/<int:class_id>/attendance')
def class_attendance(class_id):
    """View and mark attendance for a class"""
    if 'user_id' not in session or session['role'] != 'supervisor':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        flash('Class not found', 'danger')
        return redirect(url_for('supervisor.dashboard'))
    
    date_param = request.args.get('date', date.today().isoformat())
    attendance = StudentAttendance.get_class_attendance(class_id, date_param)
    
    return render_template('supervisor/class_attendance.html',
                         class_obj=class_obj,
                         attendance=attendance,
                         selected_date=date_param)

@supervisor_bp.route('/class/<int:class_id>/attendance/mark', methods=['POST'])
def mark_attendance(class_id):
    """Mark attendance for a class"""
    if 'user_id' not in session or session['role'] != 'supervisor':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    attendance_date = request.form.get('attendance_date')
    
    students = request.form.getlist('student_ids[]')
    statuses = request.form.getlist('statuses[]')
    remarks = request.form.getlist('remarks[]')
    
    marked_count = 0
    for i, student_id in enumerate(students):
        data = {
            'student_id': student_id,
            'class_id': class_id,
            'attendance_date': attendance_date,
            'status': statuses[i] if i < len(statuses) else 'absent',
            'remarks': remarks[i] if i < len(remarks) else '',
            'marked_by': session['user_id']
        }
        
        if StudentAttendance.mark(data):
            marked_count += 1
    
    flash(f'Attendance marked for {marked_count} students', 'success')
    return redirect(url_for('supervisor.class_attendance', 
                          class_id=class_id, date=attendance_date))

@supervisor_bp.route('/subjects')
def my_subjects():
    """View subjects assigned to teacher"""
    if 'user_id' not in session or session['role'] != 'supervisor':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        flash('Teacher profile not found', 'danger')
        return redirect(url_for('auth.logout'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT year_id FROM AcademicYears WHERE is_current = 1")
    current_year = cursor.fetchone()
    year_id = current_year[0] if current_year else None
    
    subjects = Teacher.get_teacher_subjects(teacher_id, year_id)
    
    return render_template('supervisor/subjects.html', subjects=subjects)