from flask import Flask, render_template, session, redirect, url_for, request, flash
from database.db_config import get_db, close_db
from utils.language import Language
from models.permission import Permission  # Add this import at the top
import os
from dotenv import load_dotenv
from routes.settings import settings_bp
from routes.themes import themes_bp
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-this')
    # In create_app() function, add:
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
    # Register database close
    app.teardown_appcontext(close_db)
    # In create_app() function, add:
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    # Initialize language handler
    @app.context_processor
    def inject_language():
        if 'language' not in session:
            session['language'] = 'ar'
        return {'lang': Language(session['language'])}
    
    # Add permission checker to template context
    @app.context_processor
    def inject_permissions():
        def has_permission(resource_code, action='access'):
            if 'user_id' not in session:
                return False
            return Permission.check_permission(session['user_id'], resource_code, action)
        return dict(has_permission=has_permission)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.students import students_bp
    from routes.teachers import teachers_bp
    from routes.classes import classes_bp
    from routes.attendance import attendance_bp
    from routes.exams import exams_bp
    from routes.finance import finance_bp
    from routes.reports import reports_bp
    from routes.supervisor import supervisor_bp
    from routes.users import users_bp
    from routes.teacher import teacher_bp
    from routes.audit import audit_bp
    from routes.api import api_bp
    from routes.admin import admin_bp
    
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
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(themes_bp, url_prefix='/themes')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    @app.route('/')
    def index():
        if 'user_id' in session:
            # Load user's theme if not already in session
            if 'theme' not in session:
                try:
                    from models.theme import Theme
                    theme = Theme.get_user_theme(session['user_id'])
                    if theme:
                        session['theme'] = theme
                    else:
                        # Fallback theme
                        session['theme'] = {
                            'primary_color': '#875A7B',
                            'secondary_color': '#6a4b5f',
                            'accent_color': '#FFB347',
                            'success_color': '#28A745',
                            'danger_color': '#DC3545',
                            'warning_color': '#FFC107',
                            'info_color': '#17A2B8',
                            'sidebar_bg': None,
                            'header_bg': None
                        }
                except Exception as e:
                    print(f"Theme error in index: {e}")
                    session['theme'] = {
                        'primary_color': '#875A7B',
                        'secondary_color': '#6a4b5f',
                        'accent_color': '#FFB347',
                        'success_color': '#28A745',
                        'danger_color': '#DC3545',
                        'warning_color': '#FFC107',
                        'info_color': '#17A2B8',
                        'sidebar_bg': None,
                        'header_bg': None
                    }
            
            role = session.get('role')
            
            # Try to redirect based on role, with fallbacks
            try:
                if role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif role == 'supervisor':
                    return redirect(url_for('supervisor.dashboard'))
                elif role == 'teacher':
                    return redirect(url_for('teacher.dashboard'))
                elif role == 'accountant':
                    return redirect(url_for('finance.dashboard'))
                else:
                    # Unknown role, logout
                    session.clear()
                    return redirect(url_for('auth.login'))
            except Exception as e:
                # If any redirect fails, go to a simple dashboard
                print(f"Redirect error: {e}")
                return render_template('simple_dashboard.html', 
                                     role=role,
                                     name=session.get('full_name', 'User'))
        
        return redirect(url_for('auth.login'))
    
    # Admin Dashboard Route
    @app.route('/admin/dashboard')
    def admin_dashboard():
        if 'user_id' not in session or session['role'] != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        from datetime import datetime, timedelta
        
        # Get database connection
        db = get_db()
        cursor = db.cursor()
        
        # ========== STATISTICS CARDS ==========
        # Get total students
        cursor.execute("SELECT COUNT(*) FROM Students WHERE status = 'active'")
        total_students = cursor.fetchone()[0]
        
        # Get total teachers
        cursor.execute("SELECT COUNT(*) FROM Teachers WHERE status = 'active'")
        total_teachers = cursor.fetchone()[0]
        
        # Get total classes
        cursor.execute("SELECT COUNT(*) FROM Classes WHERE academic_year_id = (SELECT year_id FROM AcademicYears WHERE is_current = 1)")
        total_classes = cursor.fetchone()[0]
        
        # Get today's attendance
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
        total_collected = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT ISNULL(SUM(amount), 0) FROM Expenses")
        total_expenses = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT ISNULL(SUM(amount - ISNULL(discount_amount, 0)), 0) FROM StudentFees WHERE status IN ('pending', 'partial')")
        pending_fees = cursor.fetchone()[0] or 0
        
        # Create stats dictionary for the cards
        stats = {
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_classes': total_classes,
            'total_revenue': total_collected,
            'today_attendance': today_attendance,
            'present_today': present_today,
            'absent_today': absent_today,
            'late_today': late_today,
            'total_collected': float(total_collected),
            'total_expenses': float(total_expenses),
            'current_balance': float(total_collected - total_expenses),
            'pending_fees': float(pending_fees)
        }
        
        # ========== RECENT ACTIVITIES ==========
        cursor.execute("""
        SELECT TOP 10
            'fa-user-plus' as icon,
            '#28A745' as color,
            'New Student' as title,
            CONCAT(s.first_name_ar, ' ', s.last_name_ar) as description,
            CONVERT(varchar, s.created_at, 108) as time
        FROM Students s
        WHERE s.created_at >= DATEADD(day, -7, GETDATE())
        UNION ALL
        SELECT TOP 10
            'fa-credit-card' as icon,
            '#FFB347' as color,
            'Payment Received' as title,
            CONCAT(st.first_name_ar, ' ', st.last_name_ar) as description,
            CONVERT(varchar, fp.created_at, 108) as time
        FROM FeePayments fp
        JOIN StudentFees sf ON fp.student_fee_id = sf.student_fee_id
        JOIN Students st ON sf.student_id = st.student_id
        WHERE fp.created_at >= DATEADD(day, -7, GETDATE())
        UNION ALL
        SELECT TOP 10
            'fa-calendar-check' as icon,
            '#17A2B8' as color,
            'Attendance Marked' as title,
            CONCAT(st.first_name_ar, ' ', st.last_name_ar) as description,
            CONVERT(varchar, sa.marked_at, 108) as time
        FROM StudentAttendance sa
        JOIN Students st ON sa.student_id = st.student_id
        WHERE sa.marked_at >= DATEADD(day, -7, GETDATE())
        ORDER BY time DESC
        """)
        
        recent_activities = []
        for row in cursor.fetchall():
            recent_activities.append({
                'icon': row[0],
                'color': row[1],
                'title': row[2],
                'description': row[3],
                'time': row[4]
            })
        
        # ========== ALERTS ==========
        # Get students with low attendance
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute("""
        SELECT TOP 5
            CONCAT(s.first_name_ar, ' ', s.last_name_ar) as student_name,
            COUNT(CASE WHEN sa.status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as attendance_rate
        FROM Students s
        LEFT JOIN StudentAttendance sa ON s.student_id = sa.student_id AND sa.attendance_date >= ?
        WHERE s.status = 'active'
        GROUP BY s.student_id, s.first_name_ar, s.last_name_ar
        HAVING COUNT(CASE WHEN sa.status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) < 75
        ORDER BY attendance_rate
        """, (thirty_days_ago,))
        
        low_attendance_count = cursor.rowcount
        
        # Get overdue fees count
        cursor.execute("""
        SELECT COUNT(DISTINCT student_id)
        FROM StudentFees
        WHERE due_date < GETDATE() AND status IN ('pending', 'partial')
        """)
        overdue_fees_count = cursor.fetchone()[0]
        
        # Get teacher absences today
        cursor.execute("""
        SELECT COUNT(*)
        FROM TeacherAttendance
        WHERE attendance_date = ? AND status = 'absent'
        """, (today,))
        absent_teachers = cursor.fetchone()[0]
        
        alerts = []
        
        if low_attendance_count > 0:
            alerts.append({
                'type': 'warning',
                'icon': 'fa-exclamation-triangle',
                'title': '{% if lang.get_direction() == "rtl" %}تنبيه الحضور{% else %}Attendance Alert{% endif %}',
                'message': f'{low_attendance_count} students have attendance below 75%'
            })
        
        if overdue_fees_count > 0:
            alerts.append({
                'type': 'danger',
                'icon': 'fa-exclamation-circle',
                'title': '{% if lang.get_direction() == "rtl" %}رسوم متأخرة{% else %}Overdue Fees{% endif %}',
                'message': f'{overdue_fees_count} students have overdue fees'
            })
        
        if absent_teachers > 0:
            alerts.append({
                'type': 'info',
                'icon': 'fa-bell',
                'title': '{% if lang.get_direction() == "rtl" %}غياب المعلمين{% else %}Teacher Absences{% endif %}',
                'message': f'{absent_teachers} teachers are absent today'
            })
        
        # ========== CHART DATA ==========
        # Last 7 days for chart
        chart_labels = []
        chart_attendance = []
        chart_fees = []
        
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            chart_labels.append((datetime.now() - timedelta(days=i)).strftime('%a'))
            
            # Get attendance percentage for that day
            cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as percentage
            FROM StudentAttendance
            WHERE attendance_date = ?
            """, (date,))
            result = cursor.fetchone()
            chart_attendance.append(round(float(result[0]) if result[0] else 0, 1))
            
            # Get fees collected that day
            cursor.execute("""
            SELECT ISNULL(SUM(amount_paid), 0)
            FROM FeePayments
            WHERE payment_date = ?
            """, (date,))
            result = cursor.fetchone()
            chart_fees.append(float(result[0]))
        
        cursor.close()
        
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
    # After the language context processor, add this:
    @app.context_processor
    def inject_pending_requests():
        """Inject pending requests count for admin users"""
        if 'user_id' in session and session.get('role') == 'admin':
            try:
                from database.db_config import get_db
                db = get_db()
                cursor = db.cursor()
                cursor.execute("SELECT COUNT(*) FROM AccessRequests WHERE status = 'pending'")
                count = cursor.fetchone()[0]
                cursor.close()
                return {'pending_requests_count': count}
            except:
                return {'pending_requests_count': 0}
        return {'pending_requests_count': 0}

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)