from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from database.db_config import get_db
from datetime import datetime, timedelta
import io
import csv

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
def index():
    """Reports dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    return render_template('reports/index.html')

@reports_bp.route('/students')
def student_reports():
    """Student reports page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get filter parameters
    class_id = request.args.get('class_id')
    status = request.args.get('status', 'active')
    
    # Build query
    query = """
    SELECT 
        s.student_id,
        s.student_number,
        s.first_name_ar,
        s.last_name_ar,
        s.first_name_en,
        s.last_name_en,
        s.gender,
        s.birth_date,
        s.enrollment_date,
        s.status,
        c.class_name_ar,
        c.class_id
    FROM Students s
    LEFT JOIN Classes c ON s.current_class_id = c.class_id
    WHERE 1=1
    """
    params = []
    
    if class_id:
        query += " AND s.current_class_id = ?"
        params.append(class_id)
    if status:
        query += " AND s.status = ?"
        params.append(status)
    
    query += " ORDER BY s.enrollment_date DESC"
    
    cursor.execute(query, params)
    columns = [column[0] for column in cursor.description]
    students = []
    for row in cursor.fetchall():
        students.append(dict(zip(columns, row)))
    
    # Get classes for filter
    cursor.execute("SELECT class_id, class_name_ar FROM Classes ORDER BY class_name_ar")
    classes = [{'class_id': row[0], 'class_name_ar': row[1]} for row in cursor.fetchall()]
    
    cursor.close()
    
    return render_template('reports/students.html', 
                         students=students, 
                         classes=classes,
                         selected_class=class_id,
                         selected_status=status)

@reports_bp.route('/attendance')
def attendance_reports():
    """Attendance reports page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get filter parameters
    class_id = request.args.get('class_id')
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Get classes for filter
    cursor.execute("SELECT class_id, class_name_ar FROM Classes ORDER BY class_name_ar")
    classes = [{'class_id': row[0], 'class_name_ar': row[1]} for row in cursor.fetchall()]
    
    # Get attendance summary
    attendance_data = []
    if class_id:
        cursor.execute("""
        SELECT 
            s.student_id,
            s.student_number,
            CONCAT(s.first_name_ar, ' ', s.last_name_ar) as student_name,
            COUNT(sa.attendance_id) as total_days,
            SUM(CASE WHEN sa.status = 'present' THEN 1 ELSE 0 END) as present_days,
            SUM(CASE WHEN sa.status = 'absent' THEN 1 ELSE 0 END) as absent_days,
            SUM(CASE WHEN sa.status = 'late' THEN 1 ELSE 0 END) as late_days,
            SUM(CASE WHEN sa.status = 'excused' THEN 1 ELSE 0 END) as excused_days
        FROM Students s
        LEFT JOIN StudentAttendance sa ON s.student_id = sa.student_id 
            AND sa.attendance_date BETWEEN ? AND ?
        WHERE s.current_class_id = ? AND s.status = 'active'
        GROUP BY s.student_id, s.student_number, s.first_name_ar, s.last_name_ar
        ORDER BY s.first_name_ar
        """, (start_date, end_date, class_id))
        
        columns = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            record['attendance_percentage'] = round((record['present_days'] / record['total_days'] * 100) if record['total_days'] > 0 else 0, 1)
            attendance_data.append(record)
    
    cursor.close()
    
    return render_template('reports/attendance.html',
                         classes=classes,
                         attendance_data=attendance_data,
                         selected_class=class_id,
                         start_date=start_date,
                         end_date=end_date)

@reports_bp.route('/class/<int:class_id>')
def class_report(class_id):
    """Generate class report"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    from models.class_ import Class
    from models.attendance import StudentAttendance
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        flash('Class not found', 'danger')
        return redirect(url_for('classes.list_classes'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get class students
    students = Class.get_students(class_id)
    
    # Get attendance statistics for the last 30 days
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    cursor.execute("""
    SELECT 
        s.student_id,
        s.first_name_ar,
        s.last_name_ar,
        s.student_number,
        COUNT(sa.attendance_id) as total_days,
        SUM(CASE WHEN sa.status = 'present' THEN 1 ELSE 0 END) as present_days,
        SUM(CASE WHEN sa.status = 'absent' THEN 1 ELSE 0 END) as absent_days,
        SUM(CASE WHEN sa.status = 'late' THEN 1 ELSE 0 END) as late_days,
        SUM(CASE WHEN sa.status = 'excused' THEN 1 ELSE 0 END) as excused_days
    FROM Students s
    LEFT JOIN StudentAttendance sa ON s.student_id = sa.student_id 
        AND sa.attendance_date >= ?
    WHERE s.current_class_id = ? AND s.status = 'active'
    GROUP BY s.student_id, s.first_name_ar, s.last_name_ar, s.student_number
    ORDER BY s.first_name_ar
    """, (thirty_days_ago, class_id))
    
    columns = [column[0] for column in cursor.description]
    attendance_stats = []
    for row in cursor.fetchall():
        stats = dict(zip(columns, row))
        stats['attendance_percentage'] = round((stats['present_days'] / stats['total_days'] * 100), 1) if stats['total_days'] > 0 else 0
        attendance_stats.append(stats)
    
    # Get subject information
    cursor.execute("""
    SELECT 
        s.subject_name_ar,
        s.subject_name_en,
        s.subject_code,
        cs.hours_per_week,
        CONCAT(t.first_name_ar, ' ', t.last_name_ar) as teacher_name
    FROM ClassSubjects cs
    JOIN Subjects s ON cs.subject_id = s.subject_id
    LEFT JOIN Teachers t ON cs.teacher_id = t.teacher_id
    WHERE cs.class_id = ? AND cs.academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)
    ORDER BY s.subject_name_ar
    """, (class_id,))
    
    subject_columns = [column[0] for column in cursor.description]
    subjects = []
    for row in cursor.fetchall():
        subjects.append(dict(zip(subject_columns, row)))
    
    cursor.close()
    
    return render_template('reports/class_report.html',
                         class_obj=class_obj,
                         students=students,
                         attendance_stats=attendance_stats,
                         subjects=subjects,
                         report_date=datetime.now().strftime('%Y-%m-%d'))

@reports_bp.route('/export/<string:report_type>/<string:format>')
def export_report(report_type, format):
    """Export reports in various formats"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    cursor = db.cursor()
    
    filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}"
    
    if report_type == 'students':
        # Get student data
        cursor.execute("""
        SELECT 
            s.student_number,
            s.first_name_ar,
            s.last_name_ar,
            s.first_name_en,
            s.last_name_en,
            s.gender,
            s.birth_date,
            s.phone,
            s.email,
            c.class_name_ar,
            s.enrollment_date,
            s.status
        FROM Students s
        LEFT JOIN Classes c ON s.current_class_id = c.class_id
        WHERE s.status = 'active'
        ORDER BY s.student_id
        """)
        
        data = cursor.fetchall()
        
        if format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['الرقم الدراسي', 'الاسم الأول', 'الاسم الأخير', 'الاسم بالإنجليزية', 'اللقب بالإنجليزية', 'الجنس', 'تاريخ الميلاد', 'الهاتف', 'البريد', 'الصف', 'تاريخ التسجيل', 'الحالة'])
            writer.writerows(data)
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8-sig')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f"{filename}.csv"
            )
    
    flash('Export feature coming soon', 'info')
    return redirect(url_for('reports.index'))