from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from database.db_config import get_db
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.permission_decorator import role_required

settings_bp = Blueprint('settings', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@settings_bp.route('/')
@role_required('admin')
def index():
    """Settings index"""

    
    return render_template('settings/index.html')

# ==================== SCHOOL LOGO ====================
@settings_bp.route('/logo')
@role_required('admin')
def logo():
    """Logo management page"""

    
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'school_logo.png')
    logo_exists = os.path.exists(logo_path)
    
    # Add cache buster to force browser to reload new logo
    cache_buster = datetime.now().timestamp() if logo_exists else 0
    
    return render_template('settings/logo.html', 
                         logo_exists=logo_exists,
                         cache_buster=cache_buster)

@settings_bp.route('/logo/upload', methods=['POST'])
@role_required('admin')
def upload_logo():
    """Upload school logo"""

    
    if 'logo' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('settings.logo'))
    
    file = request.files['logo']
    
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('settings.logo'))
    
    # Check file extension
    if not allowed_file(file.filename):
        flash('File type not allowed. Please upload PNG, JPG, JPEG, or GIF', 'danger')
        return redirect(url_for('settings.logo'))
    
    # Check file size (limit to 2MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 2 * 1024 * 1024:  # 2MB
        flash('File too large. Maximum size is 2MB', 'danger')
        return redirect(url_for('settings.logo'))
    
    try:
        # Create upload folder if it doesn't exist
        upload_folder = os.path.join(current_app.root_path, 'static', 'images')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save as PNG regardless of input format
        from PIL import Image
        import io
        
        # Open the image with PIL
        img = Image.open(file)
        
        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            else:
                background.paste(img)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if too large (max 300x300)
        max_size = (300, 300)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save as PNG
        file_path = os.path.join(upload_folder, 'school_logo.png')
        
        # Delete old logo if exists
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Save new logo
        img.save(file_path, 'PNG', quality=95, optimize=True)
        
        flash('Logo uploaded successfully!', 'success')
        
    except Exception as e:
        flash(f'Error uploading logo: {str(e)}', 'danger')
    
    return redirect(url_for('settings.logo'))
@settings_bp.route('/logo/delete', methods=['POST'])
@role_required('admin')
def delete_logo():
    """Delete school logo"""

    
    try:
        logo_path = os.path.join(current_app.root_path, 'static', 'images', 'school_logo.png')
        
        if os.path.exists(logo_path):
            os.remove(logo_path)
            flash('Logo deleted successfully', 'success')
        else:
            flash('No logo found', 'info')
            
    except Exception as e:
        flash(f'Error deleting logo: {str(e)}', 'danger')
    
    return redirect(url_for('settings.logo'))
@settings_bp.route('/logo/settings')
@role_required('admin')
def logo_settings():
    """Logo settings page"""

    
    db = get_db()
    cursor = db.cursor()
    
    # Get logo settings from database
    cursor.execute("SELECT setting_value FROM SystemSettings WHERE setting_key = 'logo_config'")
    result = cursor.fetchone()
    
    default_config = {
        'width': 1.2 * 72,  # Convert to points (1.2 inches * 72)
        'height': 1.2 * 72,
        'alignment': 'center',
        'border': False,
        'border_color': '#cccccc'
    }
    
    if result and result[0]:
        try:
            saved_config = json.loads(result[0])
            # Convert saved values
            logo_config = {
                'width': float(saved_config.get('width', default_config['width'])),
                'height': float(saved_config.get('height', default_config['height'])),
                'alignment': saved_config.get('alignment', default_config['alignment']),
                'border': saved_config.get('border', default_config['border']),
                'border_color': saved_config.get('border_color', default_config['border_color'])
            }
        except:
            logo_config = default_config
    else:
        logo_config = default_config
    
    cursor.close()
    
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'school_logo.png')
    logo_exists = os.path.exists(logo_path)
    cache_buster = datetime.now().timestamp() if logo_exists else 0
    
    return render_template('settings/logo_settings.html',
                         logo_config=logo_config,
                         logo_exists=logo_exists,
                         cache_buster=cache_buster)

@settings_bp.route('/logo/settings/save', methods=['POST'])
@role_required('admin')
def save_logo_settings():
    """Save logo settings"""

    
    try:
        # Get form values
        width_inches = float(request.form.get('logo_width', 1.2))
        height_inches = float(request.form.get('logo_height', 1.2))
        alignment = request.form.get('logo_alignment', 'center')
        border = request.form.get('logo_border') == 'on'
        
        # Convert inches to points (1 inch = 72 points)
        logo_config = {
            'width': width_inches * 72,
            'height': height_inches * 72,
            'alignment': alignment,
            'border': border,
            'border_color': '#cccccc'
        }
        
        # Save to database
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            IF EXISTS (SELECT 1 FROM SystemSettings WHERE setting_key = 'logo_config')
                UPDATE SystemSettings SET setting_value = ? WHERE setting_key = 'logo_config'
            ELSE
                INSERT INTO SystemSettings (setting_key, setting_value) VALUES ('logo_config', ?)
        """, (json.dumps(logo_config), json.dumps(logo_config)))
        
        db.commit()
        cursor.close()
        
        flash('Logo settings saved successfully!', 'success')
        
    except Exception as e:
        flash(f'Error saving logo settings: {str(e)}', 'danger')
    
    return redirect(url_for('settings.logo_settings'))
# ==================== SCHOOL INFORMATION ====================
@settings_bp.route('/school-info')
@role_required('admin')
def school_info():
    """School information settings"""

    
    db = get_db()
    cursor = db.cursor()
    
    # Get current settings
    cursor.execute("SELECT setting_key, setting_value FROM SystemSettings")
    settings = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    
    # Set defaults if not exists
    defaults = {
        'school_name_ar': 'المدرسة',
        'school_name_en': 'School',
        'school_address': '',
        'school_phone': '',
        'school_email': '',
        'school_website': ''
    }
    
    for key, value in defaults.items():
        if key not in settings:
            settings[key] = value
    
    return render_template('settings/school_info.html', settings=settings)

@settings_bp.route('/school-info/save', methods=['POST'])
@role_required('admin')
def save_school_info():
    """Save school information"""

    
    db = get_db()
    cursor = db.cursor()
    
    fields = [
        'school_name_ar', 'school_name_en', 'school_address',
        'school_phone', 'school_email', 'school_website'
    ]
    
    try:
        for field in fields:
            value = request.form.get(field, '')
            cursor.execute("""
                IF EXISTS (SELECT 1 FROM SystemSettings WHERE setting_key = ?)
                    UPDATE SystemSettings SET setting_value = ? WHERE setting_key = ?
                ELSE
                    INSERT INTO SystemSettings (setting_key, setting_value) VALUES (?, ?)
            """, (field, value, field, field, value))
        
        db.commit()
        cursor.close()
        flash('School information updated successfully', 'success')
        
    except Exception as e:
        flash(f'Error saving information: {str(e)}', 'danger')
    
    return redirect(url_for('settings.school_info'))

# ==================== ACADEMIC YEAR ====================
@settings_bp.route('/academic-year')
@role_required('admin')
def academic_year():
    """Academic year settings"""

    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM AcademicYears ORDER BY start_date DESC")
    columns = [column[0] for column in cursor.description]
    academic_years = []
    
    for row in cursor.fetchall():
        academic_years.append(dict(zip(columns, row)))
    
    cursor.close()
    
    return render_template('settings/academic_year.html', academic_years=academic_years)

@settings_bp.route('/academic-year/add', methods=['POST'])
@role_required('admin')
def add_academic_year():
    """Add new academic year"""

    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO AcademicYears (year_name_ar, year_name_en, start_date, end_date, is_current)
        VALUES (?, ?, ?, ?, 0)
        """, (
            request.form['year_name_ar'],
            request.form['year_name_en'],
            request.form['start_date'],
            request.form['end_date']
        ))
        
        db.commit()
        flash('Academic year added successfully', 'success')
        
    except Exception as e:
        flash(f'Error adding academic year: {str(e)}', 'danger')
    
    cursor.close()
    return redirect(url_for('settings.academic_year'))

@settings_bp.route('/academic-year/set-current/<int:year_id>', methods=['POST'])
@role_required('admin')
def set_current_year(year_id):
    """Set current academic year"""

    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Reset all years to not current
        cursor.execute("UPDATE AcademicYears SET is_current = 0")
        
        # Set selected year as current
        cursor.execute("UPDATE AcademicYears SET is_current = 1 WHERE year_id = ?", (year_id,))
        
        db.commit()
        flash('Current academic year updated successfully', 'success')
        
    except Exception as e:
        flash(f'Error updating academic year: {str(e)}', 'danger')
    
    cursor.close()
    return redirect(url_for('settings.academic_year'))