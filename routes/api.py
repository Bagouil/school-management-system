from flask import Blueprint, jsonify, session,request
from database.db_config import get_db

api_bp = Blueprint('api', __name__)

@api_bp.route('/teachers/<int:teacher_id>/classes')
def get_teacher_classes(teacher_id):
    """Get classes assigned to a teacher"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
    SELECT 
        c.class_id,
        c.class_name_ar,
        c.class_name_en,
        tc.is_class_teacher
    FROM TeacherClasses tc
    JOIN Classes c ON tc.class_id = c.class_id
    WHERE tc.teacher_id = ? AND tc.academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)
    """, (teacher_id,))
    
    classes = []
    for row in cursor.fetchall():
        classes.append({
            'class_id': row[0],
            'class_name_ar': row[1],
            'class_name_en': row[2],
            'is_class_teacher': bool(row[3])
        })
    
    cursor.close()
    return jsonify(classes)

@api_bp.route('/teachers/<int:teacher_id>/subjects')
def get_teacher_subjects(teacher_id):
    """Get subjects assigned to a teacher"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
    SELECT 
        ts.class_id,
        ts.subject_id,
        s.subject_name_ar,
        s.subject_name_en
    FROM TeacherSubjects ts
    JOIN Subjects s ON ts.subject_id = s.subject_id
    WHERE ts.teacher_id = ? AND ts.academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)
    """, (teacher_id,))
    
    subjects = []
    for row in cursor.fetchall():
        subjects.append({
            'class_id': row[0],
            'subject_id': row[1],
            'subject_name_ar': row[2],
            'subject_name_en': row[3]
        })
    
    cursor.close()
    return jsonify(subjects)

@api_bp.route('/classes/available')
def get_available_classes():
    """Get all classes for the current academic year"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
    SELECT class_id, class_name_ar, class_name_en
    FROM Classes
    WHERE academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)
    ORDER BY class_name_ar
    """)
    
    classes = []
    for row in cursor.fetchall():
        classes.append({
            'class_id': row[0],
            'class_name_ar': row[1],
            'class_name_en': row[2]
        })
    
    cursor.close()
    return jsonify(classes)

@api_bp.route('/subjects/by-class/<int:class_id>')
def get_subjects_by_class(class_id):
    """Get all subjects available for a class"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
    SELECT s.subject_id, s.subject_name_ar, s.subject_name_en
    FROM Subjects s
    WHERE s.is_active = 1
    ORDER BY s.subject_name_ar
    """)
    
    subjects = []
    for row in cursor.fetchall():
        subjects.append({
            'subject_id': row[0],
            'subject_name_ar': row[1],
            'subject_name_en': row[2]
        })
    
    cursor.close()
    return jsonify(subjects)
@api_bp.route('/access-request', methods=['POST'])
def access_request():
    
    """Handle access permission requests from users"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.get_json()
    message = data.get('message', '')
    current_role = data.get('current_role', '')
    requested_page = data.get('requested_page', '')
    
    # Store the request in database
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
    INSERT INTO AccessRequests (user_id, username, current_role, requested_page, message, status)
    VALUES (?, ?, ?, ?, ?, 'pending')
    """, (
        session['user_id'],
        session.get('username', 'unknown'),
        current_role,
        requested_page,
        message
    ))
    
    db.commit()
    cursor.close()
    
    # You could also send an email notification to admins here
    
    return jsonify({'success': True, 'message': 'Request sent successfully'})
@api_bp.route('/analytics/chart-data/<period>')
def chart_data(period):
    """Get real chart data for analytics"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    from datetime import datetime, timedelta
    
    db = get_db()
    cursor = db.cursor()
    
    today = datetime.now()
    labels = []
    attendance_data = []
    fees_data = []
    
    if period == 'week':
        # Last 7 days
        for i in range(6, -1, -1):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            labels.append((today - timedelta(days=i)).strftime('%a'))
            
            # Get attendance percentage for that day
            cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as percentage
            FROM StudentAttendance
            WHERE attendance_date = ?
            """, (date,))
            result = cursor.fetchone()
            attendance_data.append(round(float(result[0]) if result[0] else 0, 1))
            
            # Get fees collected that day
            cursor.execute("""
            SELECT ISNULL(SUM(amount_paid), 0)
            FROM FeePayments
            WHERE payment_date = ?
            """, (date,))
            result = cursor.fetchone()
            fees_data.append(float(result[0]))
            
    elif period == 'month':
        # Last 30 days grouped by week
        for i in range(4, -1, -1):
            week_start = today - timedelta(days=(i+1)*7)
            week_end = today - timedelta(days=i*7)
            labels.append(f"W{4-i}")
            
            # Average attendance for the week
            cursor.execute("""
            SELECT AVG(daily_percentage) as avg_attendance
            FROM (
                SELECT 
                    attendance_date,
                    COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as daily_percentage
                FROM StudentAttendance
                WHERE attendance_date BETWEEN ? AND ?
                GROUP BY attendance_date
            ) as daily
            """, (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
            result = cursor.fetchone()
            attendance_data.append(round(float(result[0]) if result[0] else 0, 1))
            
            # Total fees for the week
            cursor.execute("""
            SELECT ISNULL(SUM(amount_paid), 0)
            FROM FeePayments
            WHERE payment_date BETWEEN ? AND ?
            """, (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
            result = cursor.fetchone()
            fees_data.append(float(result[0]))
            
    else:  # year
        # Last 12 months
        for i in range(11, -1, -1):
            month_date = today - timedelta(days=30*i)
            labels.append(month_date.strftime('%b'))
            
            month_start = (today.replace(day=1) - timedelta(days=30*i)).strftime('%Y-%m-01')
            if i == 0:
                month_end = today.strftime('%Y-%m-%d')
            else:
                next_month = (today.replace(day=1) - timedelta(days=30*(i-1))).strftime('%Y-%m-01')
                month_end = (datetime.strptime(next_month, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Average attendance for the month
            cursor.execute("""
            SELECT AVG(daily_percentage) as avg_attendance
            FROM (
                SELECT 
                    attendance_date,
                    COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as daily_percentage
                FROM StudentAttendance
                WHERE attendance_date BETWEEN ? AND ?
                GROUP BY attendance_date
            ) as daily
            """, (month_start, month_end))
            result = cursor.fetchone()
            attendance_data.append(round(float(result[0]) if result[0] else 0, 1))
            
            # Total fees for the month
            cursor.execute("""
            SELECT ISNULL(SUM(amount_paid), 0)
            FROM FeePayments
            WHERE payment_date BETWEEN ? AND ?
            """, (month_start, month_end))
            result = cursor.fetchone()
            fees_data.append(float(result[0]))
    
    cursor.close()
    
    return jsonify({
        'labels': labels,
        'attendance': attendance_data,
        'fees': fees_data
    })