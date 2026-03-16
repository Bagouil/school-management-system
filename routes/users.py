from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.audit import AuditLog
from database.db_config import get_db
from models.permission import ResourceCategory, Permission
import hashlib
import random
import string
from utils.permission_decorator import role_required

users_bp = Blueprint('users', __name__)

def generate_password(length=8):
    """Generate random password"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

@users_bp.route('/')
@role_required('admin')
def list_users():
    """List all users"""

    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
    SELECT u.*, 
           CASE 
               WHEN u.role = 'admin' THEN 'مدير'
               WHEN u.role = 'teacher' THEN 'معلم'
               WHEN u.role = 'supervisor' THEN 'مشرف'
               WHEN u.role = 'accountant' THEN 'محاسب'
           END as role_ar,
           t.teacher_id,
           CONCAT(t.first_name_ar, ' ', t.last_name_ar) as teacher_name
    FROM Users u
    LEFT JOIN Teachers t ON u.email = t.email
    ORDER BY u.user_id DESC
    """)
    
    columns = [column[0] for column in cursor.description]
    users = []
    for row in cursor.fetchall():
        users.append(dict(zip(columns, row)))
    
    return render_template('users/list.html', users=users)

@users_bp.route('/add', methods=['GET', 'POST'])
@role_required('admin')
def add_user():
    """Add new user"""
    
    if request.method == 'POST':
        try:
            db = get_db()
            cursor = db.cursor()
            
            username = request.form['username']
            password = request.form.get('password', generate_password())
            # IMPORTANT: Hash the password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            role = request.form['role']
            email = request.form['email']
            full_name_ar = request.form['full_name_ar']
            full_name_en = request.form.get('full_name_en', '')
            
            # Check if username exists
            cursor.execute("SELECT user_id FROM Users WHERE username = ?", (username,))
            if cursor.fetchone():
                flash('Username already exists', 'danger')
                return redirect(url_for('users.add_user'))
            
            # Check if email exists
            cursor.execute("SELECT user_id FROM Users WHERE email = ?", (email,))
            if cursor.fetchone():
                flash('Email already exists', 'danger')
                return redirect(url_for('users.add_user'))
            
            cursor.execute("""
            INSERT INTO Users (username, password_hash, email, role, full_name_ar, full_name_en, is_active)
            OUTPUT INSERTED.user_id
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (username, password_hash, email, role, full_name_ar, full_name_en))
            
            user_id = cursor.fetchone()[0]
            db.commit()
            # ========== ADD AUDIT LOG HERE ==========
            from models.audit import AuditLog
            AuditLog.log_action(
                action_type='CREATE',
                table_name='Users',
                record_id=user_id,
                new_data={
                    'username': username,
                    'email': email,
                    'role': role,
                    'full_name_ar': full_name_ar,
                    'full_name_en': full_name_en
                },
                description=f'New user created: {username} ({role})'
            )
            # ========== END AUDIT LOG ==========
            flash(f'User added successfully! Username: {username}, Password: {password}', 'success')
            return redirect(url_for('users.list_users'))
            
        except Exception as e:
            flash(f'Error adding user: {str(e)}', 'danger')
            db.rollback()
    
    return render_template('users/add.html')

@users_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_user(user_id):
    """Edit user"""

    
    db = get_db()
    cursor = db.cursor()
    # Get old data before update for audit log
    cursor.execute("SELECT username, email, role, full_name_ar, full_name_en, is_active FROM Users WHERE user_id = ?", (user_id,))
    old_data_row = cursor.fetchone()
    old_data = {
        'username': old_data_row[0],
        'email': old_data_row[1],
        'role': old_data_row[2],
        'full_name_ar': old_data_row[3],
        'full_name_en': old_data_row[4],
        'is_active': old_data_row[5]
    }
    if request.method == 'POST':
        try:
            role = request.form['role']
            email = request.form['email']
            full_name_ar = request.form['full_name_ar']
            full_name_en = request.form.get('full_name_en', '')
            is_active = 1 if request.form.get('is_active') else 0
            
            cursor.execute("""
            UPDATE Users 
            SET role = ?, email = ?, full_name_ar = ?, full_name_en = ?, is_active = ?
            WHERE user_id = ?
            """, (role, email, full_name_ar, full_name_en, is_active, user_id))
            
            # If password reset requested
            if request.form.get('reset_password'):
                new_password = generate_password()
                password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                cursor.execute("UPDATE Users SET password_hash = ? WHERE user_id = ?", 
                             (password_hash, user_id))
                flash(f'Password reset successful! New password: {new_password}', 'warning')
            
            db.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('users.list_users'))
            
        except Exception as e:
            flash(f'Error updating user: {str(e)}', 'danger')
    
    cursor.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,))
    columns = [column[0] for column in cursor.description]
    user = dict(zip(columns, cursor.fetchone()))
    
    return render_template('users/edit.html', user=user)

@users_bp.route('/delete/<int:user_id>', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    """Delete user"""

    
    if user_id == session['user_id']:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('users.list_users'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get user data before deleting for audit log
    cursor.execute("SELECT username, email, role FROM Users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    username = user_data[0] if user_data else 'Unknown'
    email = user_data[1] if user_data else 'Unknown'
    role = user_data[2] if user_data else 'Unknown'
    
    cursor.execute("DELETE FROM Users WHERE user_id = ?", (user_id,))
    db.commit()
    
    # ========== ADD AUDIT LOG HERE ==========
    from models.audit import AuditLog
    AuditLog.log_action(
        action_type='DELETE',
        table_name='Users',
        record_id=user_id,
        old_data={
            'username': username,
            'email': email,
            'role': role
        },
        description=f'User deleted: {username} ({role})'
    )
    # ========== END AUDIT LOG ==========
    flash('User deleted successfully', 'success')
    return redirect(url_for('users.list_users'))

@users_bp.route('/roles')
@role_required('admin')
def manage_roles():
    """Manage user roles and permissions"""

    
    roles = [
        {'id': 'admin', 'name_ar': 'مدير', 'name_en': 'Admin', 'description_ar': 'صلاحية كاملة للنظام', 'description_en': 'Full system access'},
        {'id': 'supervisor', 'name_ar': 'مشرف تربوي', 'name_en': 'Supervisor', 'description_ar': 'إدارة الفصول والطلاب', 'description_en': 'Manage classes and students'},
        {'id': 'teacher', 'name_ar': 'معلم', 'name_en': 'Teacher', 'description_ar': 'تسجيل الحضور والدرجات', 'description_en': 'Mark attendance and grades'},
        {'id': 'accountant', 'name_ar': 'محاسب', 'name_en': 'Accountant', 'description_ar': 'إدارة الرسوم والمصروفات', 'description_en': 'Manage fees and expenses'}
    ]
    
    return render_template('users/roles.html', roles=roles)


@users_bp.route('/<int:user_id>/permissions')
@role_required('admin')
def manage_permissions(user_id):
    """Manage user permissions"""

    
    db = get_db()
    cursor = db.cursor()
    
    # Get user info
    cursor.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,))
    columns = [column[0] for column in cursor.description]
    user = dict(zip(columns, cursor.fetchone()))
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('users.list_users'))
    
    # Get all resource categories with their resources
    categories = ResourceCategory.get_with_resources()
    
    # Get user's current permissions
    user_perms = Permission.get_user_permissions(user_id)
    
    cursor.close()
    
    return render_template('users/permissions.html',
                         user=user,
                         categories=categories,
                         user_perms=user_perms)

@users_bp.route('/<int:user_id>/permissions/save', methods=['POST'])
@role_required('admin')
def save_permissions(user_id):
    """Save user permissions"""
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get all resources
        cursor.execute("SELECT resource_id, resource_code FROM Resources")
        resources = cursor.fetchall()
        
        expiry_date = request.form.get('expiry_date') or None
        
        # Process each resource
        for resource_id, resource_code in resources:
            can_access = 1 if request.form.get(f'access_{resource_id}') else 0
            can_create = 1 if request.form.get(f'create_{resource_id}') else 0
            can_edit = 1 if request.form.get(f'edit_{resource_id}') else 0
            can_delete = 1 if request.form.get(f'delete_{resource_id}') else 0
            
            # Check if this matches the role defaults
            cursor.execute("""
            SELECT can_access, can_create, can_edit, can_delete 
            FROM Permissions p
            JOIN Users u ON p.role = u.role
            WHERE u.user_id = ? AND p.resource_id = ?
            """, (user_id, resource_id))
            
            role_perms = cursor.fetchone()
            
            if role_perms:
                # If all permissions match role defaults, remove user-specific override
                if (can_access == role_perms[0] and can_create == role_perms[1] and 
                    can_edit == role_perms[2] and can_delete == role_perms[3]):
                    Permission.remove_user_permission(user_id, resource_id)
                else:
                    # Save user-specific override
                    Permission.update_user_permission(
                        user_id, resource_id, can_access, can_create, 
                        can_edit, can_delete, session['user_id'], expiry_date
                    )
        
        flash('Permissions updated successfully', 'success')
        
    except Exception as e:
        flash(f'Error updating permissions: {str(e)}', 'danger')
        db.rollback()
    
    return redirect(url_for('users.list_users'))