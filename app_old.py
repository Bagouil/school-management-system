from flask import Flask, render_template, session, redirect, url_for
from config import Config
from database.db_config import get_db, close_db
from utils.language import Language

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register database close
    app.teardown_appcontext(close_db)
    
    # Initialize language handler
    @app.context_processor
    def inject_language():
        if 'language' not in session:
            session['language'] = Config.DEFAULT_LANGUAGE
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
    
    @app.route('/')
    def index():
        if 'user_id' in session:
            if session['role'] == 'admin':
                return redirect(url_for('dashboard.admin'))
            elif session['role'] == 'teacher':
                return redirect(url_for('dashboard.teacher'))
            elif session['role'] == 'accountant':
                return redirect(url_for('dashboard.accountant'))
        return redirect(url_for('auth.login'))
    
    @app.route('/switch-language/<lang>')
    def switch_language(lang):
        if lang in ['ar', 'en']:
            session['language'] = lang
        return redirect(request.referrer or url_for('index'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)