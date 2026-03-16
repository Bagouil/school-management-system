from functools import wraps
from flask import session, flash, redirect, url_for
from models.permission import Permission

def requires_permission(resource_code, action='access'):
    """Decorator to check if user has permission for a resource"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login first', 'danger')
                return redirect(url_for('auth.login'))
            
            user_id = session['user_id']
            
            if not Permission.check_permission(user_id, resource_code, action):
                flash('You do not have permission to access this resource', 'danger')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def has_permission(resource_code, action='access'):
    """Helper function to check permission in templates"""
    if 'user_id' not in session:
        return False
    return Permission.check_permission(session['user_id'], resource_code, action)
from flask import render_template, session
from functools import wraps

def permission_required(required_roles=None, required_permission=None):
    """Decorator to check permissions with friendly access denied page"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login first', 'warning')
                return redirect(url_for('auth.login'))
            
            # Check role-based access
            if required_roles and session['role'] not in required_roles:
                return render_template('errors/access_denied.html', 
                                     required_roles=required_roles,
                                     current_role=session['role'])
            
            # Check specific permissions
            if required_permission:
                from models.permission import Permission
                if not Permission.check_permission(session['user_id'], required_permission):
                    return render_template('errors/access_denied.html',
                                         required_permission=required_permission,
                                         current_role=session['role'])
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_required(*roles):
    """Simplified decorator for role-based access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login first', 'warning')
                return redirect(url_for('auth.login'))
            
            if session['role'] not in roles:
                return render_template('errors/access_denied.html',
                                     required_roles=list(roles),
                                     current_role=session['role'])
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator