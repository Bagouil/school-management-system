from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.theme import Theme
from database.db_config import get_db
import json

themes_bp = Blueprint('themes', __name__)

@themes_bp.route('/')
def list_themes():
    """List all available themes"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        themes = Theme.get_all()
        current_theme = Theme.get_user_theme(session['user_id'])
    except Exception as e:
        print(f"Error loading themes: {e}")
        themes = []
        current_theme = {
            'primary_color': '#875A7B',
            'secondary_color': '#6a4b5f',
            'accent_color': '#FFB347',
            'success_color': '#28A745',
            'danger_color': '#DC3545',
            'warning_color': '#FFC107',
            'info_color': '#17A2B8'
        }
    
    return render_template('themes/list.html', themes=themes, current_theme=current_theme)

@themes_bp.route('/apply/<int:theme_id>', methods=['POST'])
def apply_theme(theme_id):
    """Apply theme to current user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        theme = Theme.get_by_id(theme_id)
        if not theme:
            return jsonify({'error': 'Theme not found'}), 404
        
        success = Theme.set_user_theme(session['user_id'], theme_id)
        if success:
            session['theme'] = theme  # Store in session for immediate use
            return jsonify({'success': True, 'theme': theme})
        else:
            return jsonify({'error': 'Failed to save theme'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@themes_bp.route('/preview/<int:theme_id>')
def preview_theme(theme_id):
    """Preview theme without applying"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        theme = Theme.get_by_id(theme_id)
        if not theme:
            flash('Theme not found', 'danger')
            return redirect(url_for('themes.list_themes'))
        
        return render_template('themes/preview.html', theme=theme)
    except Exception as e:
        flash(f'Error loading theme: {str(e)}', 'danger')
        return redirect(url_for('themes.list_themes'))

@themes_bp.route('/customize')
def customize():
    """Custom theme creation page"""
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    return render_template('themes/customize.html')

@themes_bp.route('/save-custom', methods=['POST'])
def save_custom_theme():
    """Save custom theme"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    db = None
    cursor = None
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
        INSERT INTO Themes (theme_name_ar, theme_name_en, primary_color, secondary_color, 
                           accent_color, success_color, danger_color, warning_color, info_color,
                           sidebar_bg, header_bg, is_default, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1)
        """, (
            request.form['theme_name_ar'],
            request.form['theme_name_en'],
            request.form['primary_color'],
            request.form['secondary_color'],
            request.form['accent_color'],
            request.form.get('success_color', '#28A745'),
            request.form.get('danger_color', '#DC3545'),
            request.form.get('warning_color', '#FFC107'),
            request.form.get('info_color', '#17A2B8'),
            request.form.get('sidebar_bg', request.form['primary_color']),
            request.form.get('header_bg', request.form['primary_color'])
        ))
        
        db.commit()
        
        # Get the last inserted ID
        cursor.execute("SELECT SCOPE_IDENTITY()")
        theme_id = cursor.fetchone()[0]
        
        return jsonify({'success': True, 'theme_id': theme_id})
        
    except Exception as e:
        if db:
            db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        if cursor:
            cursor.close()