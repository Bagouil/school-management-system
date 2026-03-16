import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, session,send_file
from models.attendance import StudentAttendance, TeacherAttendance
from models.class_ import Class
from database.db_config import get_db
from datetime import datetime, timedelta, date

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/')
def index():
    """Attendance dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    cursor = db.cursor()
    
    today = date.today()
    today_str = today.isoformat()
    
    # Get total students count
    cursor.execute("SELECT COUNT(*) FROM Students WHERE status = 'active'")
    total_students = cursor.fetchone()[0] or 0
    
    # Get today's attendance stats
    cursor.execute("""
    SELECT 
        COUNT(CASE WHEN status = 'present' THEN 1 END) as present,
        COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent,
        COUNT(CASE WHEN status = 'late' THEN 1 END) as late,
        COUNT(CASE WHEN status = 'excused' THEN 1 END) as excused
    FROM StudentAttendance 
    WHERE attendance_date = ?
    """, (today_str,))
    
    row = cursor.fetchone()
    present_today = row[0] or 0
    absent_today = row[1] or 0
    late_today = row[2] or 0
    excused_today = row[3] or 0
    
    # Calculate percentages
    total_marked = present_today + absent_today + late_today + excused_today
    attendance_percentage = round((present_today / total_marked * 100), 1) if total_marked > 0 else 0
    absence_percentage = round((absent_today / total_marked * 100), 1) if total_marked > 0 else 0
    
    # Get average attendance for the last 30 days
    cursor.execute("""
    SELECT AVG(daily_present * 100.0 / NULLIF(daily_total, 0)) as avg_attendance
    FROM (
        SELECT 
            attendance_date,
            SUM(CASE WHEN status = 'present' THEN 1 END) as daily_present,
            COUNT(*) as daily_total
        FROM StudentAttendance
        WHERE attendance_date >= DATEADD(day, -30, ?)
        GROUP BY attendance_date
    ) as daily_stats
    """, (today_str,))
    
    avg_attendance = cursor.fetchone()[0] or 0
    average_attendance = round(avg_attendance, 1)
    
    # Get today's classes attendance
    cursor.execute("""
    SELECT 
        c.class_id,
        c.class_name_ar,
        c.class_name_en,
        CONCAT(t.first_name_ar, ' ', t.last_name_ar) as teacher_name,
        COUNT(s.student_id) as total_students,
        SUM(CASE WHEN sa.status = 'present' THEN 1 ELSE 0 END) as present,
        SUM(CASE WHEN sa.status = 'absent' THEN 1 ELSE 0 END) as absent,
        SUM(CASE WHEN sa.status = 'late' THEN 1 ELSE 0 END) as late,
        SUM(CASE WHEN sa.status = 'excused' THEN 1 ELSE 0 END) as excused
    FROM Classes c
    JOIN Students s ON c.class_id = s.current_class_id AND s.status = 'active'
    LEFT JOIN Teachers t ON c.class_teacher_id = t.teacher_id
    LEFT JOIN StudentAttendance sa ON s.student_id = sa.student_id 
        AND sa.attendance_date = ?
    WHERE c.academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)
    GROUP BY c.class_id, c.class_name_ar, c.class_name_en, t.first_name_ar, t.last_name_ar
    ORDER BY c.class_name_ar
    """, (today_str,))
    
    classes_attendance = []
    classes_count = 0
    completed_classes = 0
    
    for row in cursor.fetchall():
        total = row[4] or 0
        present = row[5] or 0
        absent = row[6] or 0
        late = row[7] or 0
        excused = row[8] or 0
        
        # Calculate percentages
        present_percentage = round((present / total * 100), 1) if total > 0 else 0
        absent_percentage = round((absent / total * 100), 1) if total > 0 else 0
        late_percentage = round((late / total * 100), 1) if total > 0 else 0
        
        classes_attendance.append({
            'id': row[0],
            'name_ar': row[1],
            'name_en': row[2],
            'teacher_name': row[3] or 'غير معين',
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'excused': excused,
            'present_percentage': present_percentage,
            'absent_percentage': absent_percentage,
            'late_percentage': late_percentage,
            'marked': present + absent + late + excused
        })
        
        if (present + absent + late + excused) == total:
            completed_classes += 1
    
    classes_count = len(classes_attendance)
    
    # Get recent attendance records
    cursor.execute("""
    SELECT TOP 10
        sa.status,
        s.first_name_ar,
        s.last_name_ar,
        c.class_name_ar,
        sa.attendance_date,
        CONVERT(varchar, sa.marked_at, 108) as marked_time
    FROM StudentAttendance sa
    JOIN Students s ON sa.student_id = s.student_id
    JOIN Classes c ON s.current_class_id = c.class_id
    ORDER BY sa.marked_at DESC
    """)
    
    recent_records = []
    status_map = {
        'present': {'icon': 'fa-user-check', 'color': 'success', 'label': 'حاضر'},
        'absent': {'icon': 'fa-user-times', 'color': 'danger', 'label': 'غائب'},
        'late': {'icon': 'fa-clock', 'color': 'warning', 'label': 'متأخر'},
        'excused': {'icon': 'fa-check-circle', 'color': 'info', 'label': 'معذور'}
    }
    
    for row in cursor.fetchall():
        status = row[0]
        status_info = status_map.get(status, {'icon': 'fa-question', 'color': 'secondary', 'label': status})
        
        # Calculate time ago
        time_ago = row[5] if row[5] else 'قبل قليل'
        
        recent_records.append({
            'type': status,
            'icon': status_info['icon'],
            'student_name': f"{row[1]} {row[2]}",
            'class_name': row[3],
            'status': status_info['label'],
            'status_color': status_info['color'],
            'time': time_ago
        })
    
    # Get weekly attendance data for chart
    week_days = []
    week_attendance = []
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime('%Y-%m-%d')
        day_name = day.strftime('%A')
        
        # Arabic day names
        day_names_ar = {
            'Monday': 'الإثنين',
            'Tuesday': 'الثلاثاء',
            'Wednesday': 'الأربعاء',
            'Thursday': 'الخميس',
            'Friday': 'الجمعة',
            'Saturday': 'السبت',
            'Sunday': 'الأحد'
        }
        week_days.append(day_names_ar.get(day_name, day_name))
        
        # Get attendance percentage for this day
        cursor.execute("""
        SELECT 
            COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as percentage
        FROM StudentAttendance
        WHERE attendance_date = ?
        """, (day_str,))
        
        percentage = cursor.fetchone()[0] or 0
        week_attendance.append(round(percentage, 1))
    
    cursor.close()
    
    return render_template('attendance/dashboard.html',
                         today=today_str,
                         present_today=present_today,
                         absent_today=absent_today,
                         late_today=late_today,
                         excused_today=excused_today,
                         total_students=total_students,
                         attendance_percentage=attendance_percentage,
                         absence_percentage=absence_percentage,
                         average_attendance=average_attendance,
                         classes_attendance=classes_attendance,
                         classes_count=classes_count,
                         completed_classes=completed_classes,
                         recent_records=recent_records,
                         week_days=week_days,
                         week_attendance=week_attendance)

@attendance_bp.route('/student')
@attendance_bp.route('/student')
def student_attendance():
    """Student attendance page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    from datetime import date
    today = date.today().isoformat()
    
    # Check if form was submitted
    class_id = request.args.get('class_id')
    selected_date = request.args.get('date', today)
    
    if class_id:
        # Redirect to the class attendance view
        return redirect(url_for('attendance.view_class_attendance', 
                                class_id=class_id, 
                                date=selected_date))
    
    db = get_db()
    cursor = db.cursor()
    
    # FIXED QUERY - Use a subquery to count students instead of LEFT JOIN
    cursor.execute("""
    SELECT 
        c.class_id,
        c.class_name_ar,
        c.class_name_en,
        g.grade_name_ar,
        g.grade_name_en,
        g.grade_order,
        (SELECT COUNT(*) FROM Students WHERE current_class_id = c.class_id AND status = 'active') as student_count
    FROM Classes c
    JOIN GradeLevels g ON c.grade_id = g.grade_id
    WHERE c.academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)
    ORDER BY g.grade_order, c.class_name_ar
    """)
    
    columns = [column[0] for column in cursor.description]
    classes = []
    seen_class_ids = set()  # Track seen class IDs to prevent duplicates
    
    for row in cursor.fetchall():
        class_dict = dict(zip(columns, row))
        # Only add if we haven't seen this class ID before
        if class_dict['class_id'] not in seen_class_ids:
            seen_class_ids.add(class_dict['class_id'])
            classes.append(class_dict)
    
    cursor.close()
    
    return render_template('attendance/student.html',
                         classes=classes,
                         today=today)

@attendance_bp.route('/student/mark', methods=['POST'])
def mark_student_attendance():
    """Mark student attendance"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    class_id = request.form.get('class_id')
    attendance_date = request.form.get('attendance_date')
    
    if not class_id or not attendance_date:
        flash('Class and date are required', 'danger')
        return redirect(url_for('attendance.student_attendance'))
    
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
    return redirect(url_for('attendance.view_class_attendance', 
                          class_id=class_id, date=attendance_date))

@attendance_bp.route('/student/class/<int:class_id>')
def view_class_attendance(class_id):
    """View attendance for a class on a specific date"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    date_param = request.args.get('date', date.today().isoformat())
    
    class_obj = Class.get_by_id(class_id)
    if not class_obj:
        flash('Class not found', 'danger')
        return redirect(url_for('attendance.student_attendance'))
    
    attendance = StudentAttendance.get_class_attendance(class_id, date_param)
    
    # Check if specific student is highlighted
    student_id = request.args.get('student_id')
    
    return render_template('attendance/class_view.html',
                         class_obj=class_obj,
                         attendance=attendance,
                         selected_date=date_param,
                         highlighted_student=student_id)

@attendance_bp.route('/student/report')
def student_report():
    """Student attendance report"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    class_id = request.args.get('class_id')
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    sort_by = request.args.get('sort_by', 'name')
    
    db = get_db()
    cursor = db.cursor()
    
    # Get all classes for filter
    cursor.execute("""
    SELECT c.class_id, c.class_name_ar, g.grade_name_ar
    FROM Classes c
    JOIN GradeLevels g ON c.grade_id = g.grade_id
    WHERE c.academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)
    ORDER BY g.grade_order, c.class_name_ar
    """)
    
    columns = [column[0] for column in cursor.description]
    all_classes = []
    for row in cursor.fetchall():
        all_classes.append(dict(zip(columns, row)))
    
    class_obj = None
    report = []
    
    if class_id:
        # Get class info
        cursor.execute("""
        SELECT c.*, g.grade_name_ar, g.grade_name_en
        FROM Classes c
        JOIN GradeLevels g ON c.grade_id = g.grade_id
        WHERE c.class_id = ?
        """, (class_id,))
        
        row = cursor.fetchone()
        if row:
            columns = [column[0] for column in cursor.description]
            class_obj = dict(zip(columns, row))
        
        # Get monthly report
        report = StudentAttendance.get_monthly_report(class_id, year, month)
        
        # Sort report based on user selection
        if sort_by == 'attendance':
            report.sort(key=lambda x: x['attendance_percentage'], reverse=True)
        elif sort_by == 'absent':
            report.sort(key=lambda x: x['absent'], reverse=True)
        else:  # sort by name
            report.sort(key=lambda x: x['name_ar'])
    
    cursor.close()
    
    months = [
        {'value': 1, 'name_ar': 'يناير', 'name_en': 'January'},
        {'value': 2, 'name_ar': 'فبراير', 'name_en': 'February'},
        {'value': 3, 'name_ar': 'مارس', 'name_en': 'March'},
        {'value': 4, 'name_ar': 'أبريل', 'name_en': 'April'},
        {'value': 5, 'name_ar': 'مايو', 'name_en': 'May'},
        {'value': 6, 'name_ar': 'يونيو', 'name_en': 'June'},
        {'value': 7, 'name_ar': 'يوليو', 'name_en': 'July'},
        {'value': 8, 'name_ar': 'أغسطس', 'name_en': 'August'},
        {'value': 9, 'name_ar': 'سبتمبر', 'name_en': 'September'},
        {'value': 10, 'name_ar': 'أكتوبر', 'name_en': 'October'},
        {'value': 11, 'name_ar': 'نوفمبر', 'name_en': 'November'},
        {'value': 12, 'name_ar': 'ديسمبر', 'name_en': 'December'}
    ]
    
    return render_template('attendance/student_report.html',
                         classes=all_classes,
                         class_obj=class_obj,
                         report=report,
                         month=month,
                         year=year,
                         months=months)

@attendance_bp.route('/teacher')
def teacher_attendance():
    """Teacher attendance page"""
    if 'user_id' not in session or session['role'] not in ['admin']:
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    from datetime import date
    today = date.today().isoformat()
    
    db = get_db()
    cursor = db.cursor()
    
    # Get all active teachers
    cursor.execute("""
    SELECT teacher_id, first_name_ar, last_name_ar, teacher_number
    FROM Teachers
    WHERE status = 'active'
    ORDER BY first_name_ar
    """)
    
    columns = [column[0] for column in cursor.description]
    teachers = []
    for row in cursor.fetchall():
        teachers.append(dict(zip(columns, row)))
    
    cursor.close()
    
    return render_template('attendance/teacher.html',
                         teachers=teachers,
                         today=today)

@attendance_bp.route('/teacher/mark', methods=['POST'])
def mark_teacher_attendance():
    """Mark teacher attendance"""
    if 'user_id' not in session or session['role'] not in ['admin']:
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    attendance_date = request.form.get('attendance_date')
    
    if not attendance_date:
        flash('Date is required', 'danger')
        return redirect(url_for('attendance.teacher_attendance'))
    
    teacher_ids = request.form.getlist('teacher_ids[]')
    statuses = request.form.getlist('statuses[]')
    remarks = request.form.getlist('remarks[]')
    
    marked_count = 0
    for i, teacher_id in enumerate(teacher_ids):
        data = {
            'teacher_id': teacher_id,
            'attendance_date': attendance_date,
            'status': statuses[i] if i < len(statuses) else 'absent',
            'remarks': remarks[i] if i < len(remarks) else '',
            'marked_by': session['user_id']
        }
        
        if TeacherAttendance.mark(data):
            marked_count += 1
    
    flash(f'Attendance marked for {marked_count} teachers', 'success')
    return redirect(url_for('attendance.view_teacher_attendance', date=attendance_date))

@attendance_bp.route('/teacher/view')
def view_teacher_attendance():
    """View teacher attendance for a specific date"""
    if 'user_id' not in session or session['role'] not in ['admin']:
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    date_param = request.args.get('date', date.today().isoformat())
    
    attendance = TeacherAttendance.get_daily_attendance(date_param)
    
    return render_template('attendance/teacher_view.html',
                         attendance=attendance,
                         selected_date=date_param)
                         
@attendance_bp.route('/print-report')
def print_report():
    """Generate print-friendly attendance report"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    from datetime import datetime
    
    # Get parameters
    class_id = request.args.get('class_id')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    report_type = request.args.get('type', 'class')  # class, student, monthly
    
    db = get_db()
    cursor = db.cursor()
    
    # Get school settings
    cursor.execute("SELECT setting_key, setting_value FROM SystemSettings")
    school_settings = {row[0]: row[1] for row in cursor.fetchall()}
    school_name = school_settings.get('school_name_ar', 'المدرسة')
    
    attendance_data = []
    class_name = None
    total_students = 0
    present_count = 0
    absent_count = 0
    late_count = 0
    excused_count = 0
    
    if report_type == 'class' and class_id:
        # Get class name
        cursor.execute("SELECT class_name_ar FROM Classes WHERE class_id = ?", (class_id,))
        class_row = cursor.fetchone()
        class_name = class_row[0] if class_row else None
        
        # Get attendance for this class on this date
        cursor.execute("""
        SELECT 
            s.student_id,
            s.student_number,
            CONCAT(s.first_name_ar, ' ', s.last_name_ar) as student_name,
            sa.status,
            sa.remarks
        FROM Students s
        LEFT JOIN StudentAttendance sa ON s.student_id = sa.student_id 
            AND sa.attendance_date = ?
        WHERE s.current_class_id = ? AND s.status = 'active'
        ORDER BY s.first_name_ar
        """, (date, class_id))
        
        for row in cursor.fetchall():
            record = {
                'student_id': row[0],
                'student_number': row[1],
                'student_name': row[2],
                'status': row[3] or 'absent',
                'remarks': row[4] or ''
            }
            attendance_data.append(record)
            total_students += 1
            
            if record['status'] == 'present':
                present_count += 1
            elif record['status'] == 'absent':
                absent_count += 1
            elif record['status'] == 'late':
                late_count += 1
            elif record['status'] == 'excused':
                excused_count += 1
    
    cursor.close()
    
    attendance_percentage = round((present_count / total_students * 100) if total_students > 0 else 0, 1)
    
    report_title = f"تقرير حضور الصف {class_name} - {date}" if class_name else "تقرير الحضور"
    
    return render_template('attendance/print_report.html',
                         school_name=school_name,
                         report_title=report_title,
                         report_date=datetime.now().strftime('%Y-%m-%d'),
                         period=date,
                         class_name=class_name,
                         total_students=total_students,
                         present_count=present_count,
                         absent_count=absent_count,
                         late_count=late_count,
                         excused_count=excused_count,
                         attendance_percentage=attendance_percentage,
                         attendance_data=attendance_data,
                         generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                         
@attendance_bp.route('/export-report/<string:format>')
def export_attendance_report(format):
    """Export attendance report to CSV/Excel"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Get parameters
    class_id = request.args.get('class_id')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    if not class_id:
        flash('Class ID is required', 'danger')
        return redirect(url_for('attendance.index'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get class name
    cursor.execute("SELECT class_name_ar FROM Classes WHERE class_id = ?", (class_id,))
    class_row = cursor.fetchone()
    class_name = class_row[0] if class_row else 'Unknown'
    
    # Get attendance data
    cursor.execute("""
    SELECT 
        s.student_number,
        s.first_name_ar,
        s.last_name_ar,
        CASE 
            WHEN sa.status = 'present' THEN 'حاضر'
            WHEN sa.status = 'absent' THEN 'غائب'
            WHEN sa.status = 'late' THEN 'متأخر'
            WHEN sa.status = 'excused' THEN 'معذور'
            ELSE 'غير مسجل'
        END as status,
        ISNULL(sa.remarks, '') as remarks
    FROM Students s
    LEFT JOIN StudentAttendance sa ON s.student_id = sa.student_id 
        AND sa.attendance_date = ?
    WHERE s.current_class_id = ? AND s.status = 'active'
    ORDER BY s.first_name_ar
    """, (date, class_id))
    
    attendance_data = cursor.fetchall()
    cursor.close()
    
    # Generate filename
    filename = f"attendance_{class_name}_{date}".replace(' ', '_')
    
    if format == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['الرقم الدراسي', 'الاسم الأول', 'الاسم الأخير', 'الحالة', 'ملاحظات'])
        
        # Write data
        for row in attendance_data:
            writer.writerow(row)
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{filename}.csv"
        )
    
    elif format == 'excel':
        try:
            import pandas as pd
            import io
            
            # Prepare data for DataFrame
            data = []
            for row in attendance_data:
                data.append({
                    'الرقم الدراسي': row[0],
                    'الاسم الأول': row[1],
                    'الاسم الأخير': row[2],
                    'الحالة': row[3],
                    'ملاحظات': row[4]
                })
            
            df = pd.DataFrame(data)
            
            # Create Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Attendance', index=False)
                
                # Format the Excel file
                workbook = writer.book
                worksheet = writer.sheets['Attendance']
                
                # Adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            output.seek(0)
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f"{filename}.xlsx"
            )
            
        except ImportError:
            flash('Please install pandas and openpyxl: pip install pandas openpyxl', 'danger')
            return redirect(url_for('attendance.view_class_attendance', class_id=class_id, date=date))
    
    else:
        flash('Invalid export format', 'danger')
        return redirect(url_for('attendance.view_class_attendance', class_id=class_id, date=date))