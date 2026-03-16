from flask import Flask, render_template, session, redirect, url_for, request
from database.db_config import get_db, close_db
from utils.language import Language
import os
from dotenv import load_dotenv
from routes.classes import classes_bp
from routes.supervisor import supervisor_bp
from routes.users import users_bp


load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-this')
    
    # Register database close
    app.teardown_appcontext(close_db)
    
    # Initialize language handler
    @app.context_processor
    def inject_language():
        if 'language' not in session:
            session['language'] = 'ar'
        return {'lang': Language(session['language'])}
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.students import students_bp
    from routes.teachers import teachers_bp
    from routes.classes import classes_bp
    from routes.attendance import attendance_bp
    from routes.exams import exams_bp
    from routes.finance import finance_bp
    from routes.reports import reports_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(teachers_bp, url_prefix='/teachers')
    app.register_blueprint(classes_bp, url_prefix='/classes')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(exams_bp, url_prefix='/exams')
    app.register_blueprint(finance_bp, url_prefix='/finance')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(supervisor_bp, url_prefix='/supervisor') 
    app.register_blueprint(users_bp, url_prefix='/users')

    @app.route('/')
    def index():
        if 'user_id' in session:
            # Redirect to students list for now
            return redirect(url_for('students.list_students'))
        return redirect(url_for('auth.login'))
    @app.route('/admin/dashboard')
    def admin_dashboard():
        if 'user_id' not in session or session['role'] != 'admin':
            flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    from datetime import datetime, timedelta
    from database.db_config import get_db
    
    db = get_db()
    cursor = db.cursor()
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) FROM Students WHERE status = 'active'")
    total_students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Teachers WHERE status = 'active'")
    total_teachers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Classes WHERE academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)")
    total_classes = cursor.fetchone()[0]
    
    # Today's attendance
    today = datetime.now().date().isoformat()
    cursor.execute("""
    SELECT 
        COUNT(CASE WHEN status = 'present' THEN 1 END) as present,
        COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent,
        COUNT(CASE WHEN status = 'late' THEN 1 END) as late
    FROM StudentAttendance 
    WHERE attendance_date = ?
    """, (today,))
    attendance = cursor.fetchone()
    present_today = attendance[0] or 0
    absent_today = attendance[1] or 0
    late_today = attendance[2] or 0
    total_attendance = present_today + absent_today + late_today
    today_attendance = round((present_today / total_attendance * 100) if total_attendance > 0 else 0)
    
    # Financial stats
    cursor.execute("SELECT ISNULL(SUM(amount_paid), 0) FROM FeePayments")
    total_collected = cursor.fetchone()[0]
    
    cursor.execute("SELECT ISNULL(SUM(amount), 0) FROM Expenses")
    total_expenses = cursor.fetchone()[0]
    
    cursor.execute("SELECT ISNULL(SUM(amount - ISNULL(discount_amount, 0)), 0) FROM StudentFees WHERE status IN ('pending', 'partial')")
    pending_fees = cursor.fetchone()[0]
    
    # Recent activities (you can replace these with real data from database)
    recent_activities = [
        {'icon': 'fa-user-plus', 'color': '#28A745', 'title': 'New Student Registered', 'description': 'Student joined Grade 3', 'time': '5 minutes ago'},
        {'icon': 'fa-credit-card', 'color': '#FFB347', 'title': 'Payment Received', 'description': '15,000 SDG collected', 'time': '1 hour ago'},
        {'icon': 'fa-calendar-check', 'color': '#17A2B8', 'title': 'Attendance Marked', 'description': 'Class attendance completed', 'time': '2 hours ago'},
        {'icon': 'fa-user-edit', 'color': '#875A7B', 'title': 'Teacher Assigned', 'description': 'Teacher assigned to class', 'time': '3 hours ago'},
    ]
    
    # Alerts
    alerts = [
        {'type': 'warning', 'icon': 'fa-exclamation-triangle', 'title': 'Low Attendance Alert', 'message': 'Some classes have low attendance'},
        {'type': 'info', 'icon': 'fa-bell', 'title': 'Pending Payments', 'message': 'Students have pending fees'},
        {'type': 'danger', 'icon': 'fa-times-circle', 'title': 'Teacher Absence', 'message': 'Some teachers are absent today'},
    ]
    
    # Chart data (replace with real data)
    chart_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    chart_attendance = [95, 88, 92, 89, 94, 85, 90]
    chart_fees = [15000, 22000, 18000, 25000, 19000, 16000, 21000]
    
    stats = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_revenue': total_collected,
        'today_attendance': today_attendance,
        'present_today': present_today,
        'absent_today': absent_today,
        'late_today': late_today,
        'total_collected': total_collected,
        'total_expenses': total_expenses,
        'current_balance': total_collected - total_expenses,
        'pending_fees': pending_fees
    }
    
    return render_template('dashboard/admin_new.html',
                         stats=stats,
                         recent_activities=recent_activities,
                         alerts=alerts,
                         chart_labels=chart_labels,
                         chart_attendance=chart_attendance,
                         chart_fees=chart_fees,
                         today=today)
    @app.route('/switch-language/<lang>')
    def switch_language(lang):
        if lang in ['ar', 'en']:
            session['language'] = lang
        return redirect(request.referrer or url_for('index'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
    