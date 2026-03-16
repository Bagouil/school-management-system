from functools import wraps
from flask import session, request
from models.audit import AuditLog
import json

def audit_log(action_type, table_name):
    """Decorator to automatically log actions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Store request data before the function executes
            request_data = request.get_json() if request.is_json else request.form.to_dict()
            
            # Execute the function
            result = f(*args, **kwargs)
            
            # Log after successful execution
            if result and hasattr(result, 'status_code') and result.status_code < 400:
                # Try to get record ID from response or kwargs
                record_id = kwargs.get('record_id') or kwargs.get('id') or kwargs.get('student_id') or kwargs.get('teacher_id')
                
                description = f"{action_type} on {table_name}"
                if record_id:
                    description += f" (ID: {record_id})"
                
                AuditLog.log_action(
                    action_type=action_type,
                    table_name=table_name,
                    record_id=record_id,
                    new_data=request_data,
                    description=description
                )
            
            return result
        return decorated_function
    return decorator