from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.theme import Theme
from models.audit import AuditLog
from database.db_config import get_db
import hashlib

# Create the blueprint first
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        print(f"\n=== LOGIN ATTEMPT ===")
        print(f"Username: {username}")
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        db = get_db()
        cursor = db.cursor()
        
        # Try to login
        cursor.execute("""
            SELECT user_id, username, role, full_name_ar, full_name_en, is_active
            FROM Users 
            WHERE username = ? AND password_hash = ?
        """, (username, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            print(f"✓ Login successful for user {user[1]}")
            
            if not user[5]:
                flash('Account is disabled', 'danger')
                cursor.close()
                return render_template('login.html')
            
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[2]
            session['full_name'] = user[3] or user[4] or user[1]
            # ========== ADD AUDIT LOG HERE ==========
            from models.audit import AuditLog
            AuditLog.log_action(
                action_type='LOGIN',
                table_name='Users',
                record_id=user[0],
                description=f'User logged in: {username}'
            )
            # ========== END AUDIT LOG ==========
            # Load user's theme
            try:
                from models.theme import Theme
                theme = Theme.get_user_theme(user[0])
                if theme:
                    session['theme'] = theme
                else:
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
                print(f"Theme error: {e}")
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
            
            # If user is a teacher/supervisor, get their teacher_id
            if user[2] in ['teacher', 'supervisor']:
                # Try to find teacher by email first, then by username
                cursor2 = db.cursor()
                
                # Method 1: Try by email (if user email matches teacher email)
                cursor2.execute("""
                    SELECT teacher_id, first_name_ar, last_name_ar 
                    FROM Teachers 
                    WHERE email = ?
                """, (user[1],))  # Try username as email
                
                teacher = cursor2.fetchone()
                
                # Method 2: If not found, try by phone
                if not teacher:
                    cursor2.execute("""
                        SELECT teacher_id, first_name_ar, last_name_ar 
                        FROM Teachers 
                        WHERE phone = ?
                    """, (user[1],))  # Try username as phone
                    teacher = cursor2.fetchone()
                
                # Method 3: Try by email from users table
                if not teacher:
                    cursor2.execute("""
                        SELECT t.teacher_id, t.first_name_ar, t.last_name_ar 
                        FROM Teachers t
                        JOIN Users u ON t.email = u.email
                        WHERE u.user_id = ?
                    """, (user[0],))
                    teacher = cursor2.fetchone()
                
                cursor2.close()
                
                if teacher:
                    session['teacher_id'] = teacher[0]
                    print(f"✓ Teacher linked: {teacher[1]} {teacher[2]} (ID: {teacher[0]})")
                else:
                    print(f"⚠ No teacher record found for user {user[1]}")
                    # You might want to create a teacher record here or show a warning
            
            cursor.close()
            flash(f'Welcome {session["full_name"]}!', 'success')
            
            # Redirect based on role
            try:
                if user[2] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user[2] == 'supervisor':
                    return redirect(url_for('supervisor.dashboard'))
                elif user[2] == 'teacher':
                    return redirect(url_for('teacher.dashboard'))
                elif user[2] == 'accountant':
                    return redirect(url_for('finance.dashboard'))
                else:
                    return redirect(url_for('index'))
            except Exception as e:
                print(f"Redirect error: {e}")
                return redirect(url_for('index'))
        else:
            print(f"✗ Invalid login for {username}")
            cursor.close()
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')
@auth_bp.route('/logout')
def logout():
    # ========== ADD AUDIT LOG HERE ==========
    if 'user_id' in session:
        from models.audit import AuditLog
        AuditLog.log_action(
            action_type='LOGOUT',
            table_name='Users',
            record_id=session['user_id'],
            description=f'User logged out: {session.get("username")}'
        )
    # ========== END AUDIT LOG ==========
    
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))
@auth_bp.route('/profile')
def profile():
    """User profile page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    cursor = db.cursor()
    
    # First, check which columns exist
    cursor.execute("""
    SELECT COLUMN_NAME 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Users'
    """)
    
    existing_columns = [row[0] for row in cursor.fetchall()]
    
    # Build dynamic query based on existing columns
    select_columns = ['user_id', 'username', 'email', 'role', 'full_name_ar', 'full_name_en']
    
    if 'profile_image' in existing_columns:
        select_columns.append('profile_image')
    if 'created_at' in existing_columns:
        select_columns.append('created_at')
    if 'last_login' in existing_columns:
        select_columns.append('last_login')
    
    query = f"SELECT {', '.join(select_columns)} FROM Users WHERE user_id = ?"
    
    cursor.execute(query, (session['user_id'],))
    
    columns = [column[0] for column in cursor.description]
    user = dict(zip(columns, cursor.fetchone()))
    
    # Add default values for missing columns
    if 'profile_image' not in user:
        user['profile_image'] = None
    if 'created_at' not in user:
        user['created_at'] = None
    if 'last_login' not in user:
        user['last_login'] = None
    
    # Get recent activities (simplified)
    recent_activities = [
        {
            'icon': 'fa-sign-in-alt',
            'color': '#28A745',
            'title': 'Login' if session.get('language') != 'ar' else 'تسجيل دخول',
            'description': 'You logged into the system' if session.get('language') != 'ar' else 'قمت بتسجيل الدخول إلى النظام',
            'time': 'Just now' if session.get('language') != 'ar' else 'الآن'
        },
        {
            'icon': 'fa-user-edit',
            'color': '#875A7B',
            'title': 'Profile Update' if session.get('language') != 'ar' else 'تحديث الملف',
            'description': 'You viewed your profile' if session.get('language') != 'ar' else 'قمت بعرض ملفك الشخصي',
            'time': 'Just now' if session.get('language') != 'ar' else 'الآن'
        }
    ]
    
    cursor.close()
    
    return render_template('auth/profile.html', 
                         user=user, 
                         recent_activities=recent_activities)
@auth_bp.route('/profile/update', methods=['POST'])
def update_profile():
    """Update user profile"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
        UPDATE Users 
        SET full_name_ar = ?, full_name_en = ?, email = ?
        WHERE user_id = ?
        """, (
            request.form.get('full_name_ar', ''),
            request.form.get('full_name_en', ''),
            request.form['email'],
            session['user_id']
        ))
        
        db.commit()
        flash('Profile updated successfully', 'success')
        
    except Exception as e:
        flash(f'Error updating profile: {str(e)}', 'danger')
        db.rollback()
    
    cursor.close()
    return redirect(url_for('auth.profile'))

@auth_bp.route('/profile/upload-photo', methods=['POST'])
def upload_profile_photo():
    """Upload profile photo"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    from utils.file_upload import save_uploaded_file, delete_file
    
    file_path = save_uploaded_file(file, 'profiles')
    if not file_path:
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if profile_image column exists
    cursor.execute("""
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Users' AND COLUMN_NAME = 'profile_image'
    """)
    has_profile_image = cursor.fetchone()[0] > 0
    
    if has_profile_image:
        # Get old photo to delete
        cursor.execute("SELECT profile_image FROM Users WHERE user_id = ?", (session['user_id'],))
        old_photo = cursor.fetchone()
        
        cursor.execute("UPDATE Users SET profile_image = ? WHERE user_id = ?", 
                      (file_path, session['user_id']))
        db.commit()
        
        # Delete old photo if exists
        if old_photo and old_photo[0]:
            delete_file(old_photo[0])
    else:
        # Column doesn't exist yet
        cursor.close()
        return jsonify({'success': False, 'error': 'Profile image column not available in database'}), 400
    
    cursor.close()
    
    return jsonify({'success': True, 'path': file_path})


@auth_bp.route('/profile/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('auth.profile'))
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters', 'danger')
        return redirect(url_for('auth.profile'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Verify current password
    current_hash = hashlib.sha256(current_password.encode()).hexdigest()
    cursor.execute("SELECT user_id FROM Users WHERE user_id = ? AND password_hash = ?", 
                  (session['user_id'], current_hash))
    
    if not cursor.fetchone():
        flash('Current password is incorrect', 'danger')
        cursor.close()
        return redirect(url_for('auth.profile'))
    
    # Update password
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    cursor.execute("UPDATE Users SET password_hash = ? WHERE user_id = ?", 
                  (new_hash, session['user_id']))
    db.commit()
    cursor.close()
    
    flash('Password changed successfully', 'success')
    return redirect(url_for('auth.profile'))


@auth_bp.route('/profile/toggle-twofactor', methods=['POST'])
def toggle_twofactor():
    """Toggle two-factor authentication"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.get_json()
    enabled = data.get('enabled', False)
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if two_factor_enabled column exists
    cursor.execute("""
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Users' AND COLUMN_NAME = 'two_factor_enabled'
    """)
    has_twofactor = cursor.fetchone()[0] > 0
    
    if has_twofactor:
        cursor.execute("UPDATE Users SET two_factor_enabled = ? WHERE user_id = ?", 
                      (1 if enabled else 0, session['user_id']))
        db.commit()
    else:
        cursor.close()
        return jsonify({'success': False, 'error': 'Two-factor authentication not available'}), 400
    
    cursor.close()
    
    return jsonify({'success': True})
@auth_bp.route('/ping', methods=['POST'])
def ping():
    """Keep session alive"""
    if 'user_id' in session:
        # Refresh session by modifying it
        session['last_activity'] = datetime.now().isoformat()
        session.modified = True
        return jsonify({'status': 'ok', 'message': 'Session extended'})
    return jsonify({'status': 'error', 'message': 'Not logged in'}), 401