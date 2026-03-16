import csv
import io
from flask import send_file
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.audit import AuditLog
from database.db_config import get_db
from datetime import datetime
from utils.permission_decorator import role_required
audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/')
@role_required('admin')
def audit_logs():
    """View audit logs"""

    
    # Get filter parameters
    page = request.args.get('page', 1, type=int)
    per_page = 50
    user_id = request.args.get('user_id', type=int)
    action_type = request.args.get('action_type')
    table_name = request.args.get('table_name')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    search = request.args.get('search')
    
    filters = {}
    if user_id:
        filters['user_id'] = user_id
    if action_type:
        filters['action_type'] = action_type
    if table_name:
        filters['table_name'] = table_name
    if from_date:
        filters['from_date'] = from_date
    if to_date:
        filters['to_date'] = to_date + ' 23:59:59'
    if search:
        filters['search'] = search
    
    # Get logs
    offset = (page - 1) * per_page
    logs = AuditLog.get_logs(filters, per_page, offset)
    total = AuditLog.get_logs_count(filters)
    
    # Get filter options
    action_types = AuditLog.get_action_types()
    tables = AuditLog.get_tables()
    
    # Get users for filter
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT user_id, username FROM Users ORDER BY username")
        users = []
        if cursor.description:
            for row in cursor.fetchall():
                users.append({'user_id': row[0], 'username': row[1]})
    except Exception as e:
        print(f"Error fetching users: {e}")
        users = []
    finally:
        cursor.close()
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }
    
    return render_template('audit/logs.html',
                         logs=logs,
                         pagination=pagination,
                         users=users,
                         action_types=action_types,
                         tables=tables,
                         selected_user=user_id,
                         selected_action=action_type,
                         selected_table=table_name,
                         from_date=from_date,
                         to_date=to_date,
                         search=search)

@audit_bp.route('/log/<int:log_id>')
@role_required('admin')
def view_log(log_id):
    """View single log entry with full details"""

    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # First check if the log exists
        cursor.execute("SELECT COUNT(*) FROM AuditLogs WHERE log_id = ?", (log_id,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            return jsonify({'error': 'Log not found'}), 404
        
        # Get the log details
        cursor.execute("""
        SELECT 
            log_id, 
            user_id, 
            username, 
            user_role, 
            action_type, 
            table_name,
            record_id, 
            old_data, 
            new_data, 
            ip_address, 
            user_agent, 
            CONVERT(varchar, created_at, 20) as created_at,
            description
        FROM AuditLogs
        WHERE log_id = ?
        """, (log_id,))
        
        # Check if we have a valid result
        if cursor.description is None:
            return jsonify({'error': 'No data returned'}), 404
        
        # Get column names
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Log not found'}), 404
        
        # Build dictionary
        log = {}
        for i, col in enumerate(columns):
            log[col] = row[i]
        
        # Parse JSON data
        import json
        if log.get('old_data'):
            try:
                log['old_data_parsed'] = json.loads(log['old_data'])
            except:
                log['old_data_parsed'] = log['old_data']
        else:
            log['old_data_parsed'] = None
            
        if log.get('new_data'):
            try:
                log['new_data_parsed'] = json.loads(log['new_data'])
            except:
                log['new_data_parsed'] = log['new_data']
        else:
            log['new_data_parsed'] = None
        
        return jsonify(log)
        
    except Exception as e:
        print(f"Error in view_log: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
@staticmethod
def get_logs(filters=None, limit=100, offset=0):
    """Get audit logs with optional filters"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        query = """
        SELECT 
            log_id, user_id, username, user_role, action_type, table_name,
            record_id, old_data, new_data, ip_address, user_agent, 
            CONVERT(varchar, created_at, 20) as created_at,
            description
        FROM AuditLogs
        WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('user_id'):
                query += " AND user_id = ?"
                params.append(filters['user_id'])
            if filters.get('action_type'):
                query += " AND action_type = ?"
                params.append(filters['action_type'])
            if filters.get('table_name'):
                query += " AND table_name = ?"
                params.append(filters['table_name'])
            if filters.get('from_date'):
                query += " AND created_at >= ?"
                params.append(filters['from_date'])
            if filters.get('to_date'):
                query += " AND created_at <= ?"
                params.append(filters['to_date'])
            if filters.get('search'):
                query += " AND (username LIKE ? OR description LIKE ?)"
                search_param = f"%{filters['search']}%"
                params.extend([search_param, search_param])
        
        query += " ORDER BY created_at DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
        
        cursor.execute(query, params)
        
        # Check if we have a valid result
        if cursor.description is None:
            return []
        
        columns = [column[0] for column in cursor.description]
        logs = []
        for row in cursor.fetchall():
            log = {}
            for i, col in enumerate(columns):
                log[col] = row[i]
            logs.append(log)
        
        return logs
        
    except Exception as e:
        print(f"Error in get_logs: {e}")
        return []
    finally:
        cursor.close()
@staticmethod
def get_logs_count(filters=None):
    """Get total count of logs matching filters"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        query = "SELECT COUNT(*) FROM AuditLogs WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('user_id'):
                query += " AND user_id = ?"
                params.append(filters['user_id'])
            if filters.get('action_type'):
                query += " AND action_type = ?"
                params.append(filters['action_type'])
            if filters.get('table_name'):
                query += " AND table_name = ?"
                params.append(filters['table_name'])
            if filters.get('from_date'):
                query += " AND created_at >= ?"
                params.append(filters['from_date'])
            if filters.get('to_date'):
                query += " AND created_at <= ?"
                params.append(filters['to_date'])
            if filters.get('search'):
                query += " AND (username LIKE ? OR description LIKE ?)"
                search_param = f"%{filters['search']}%"
                params.extend([search_param, search_param])
        
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        return count
        
    except Exception as e:
        print(f"Error in get_logs_count: {e}")
        return 0
    finally:
        cursor.close()
@audit_bp.route('/export')
@role_required('admin')
def export_logs():
    """Export audit logs to CSV"""

    
    # Get filter parameters (same as in the main view)
    user_id = request.args.get('user_id', type=int)
    action_type = request.args.get('action_type')
    table_name = request.args.get('table_name')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    search = request.args.get('search')
    
    filters = {}
    if user_id:
        filters['user_id'] = user_id
    if action_type:
        filters['action_type'] = action_type
    if table_name:
        filters['table_name'] = table_name
    if from_date:
        filters['from_date'] = from_date
    if to_date:
        filters['to_date'] = to_date + ' 23:59:59'
    if search:
        filters['search'] = search
    
    # Get all logs (no pagination)
    db = get_db()
    cursor = db.cursor()
    
    try:
        query = """
        SELECT 
            log_id,
            CONVERT(varchar, created_at, 20) as created_at,
            username,
            user_role,
            action_type,
            table_name,
            record_id,
            ip_address,
            description
        FROM AuditLogs
        WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('user_id'):
                query += " AND user_id = ?"
                params.append(filters['user_id'])
            if filters.get('action_type'):
                query += " AND action_type = ?"
                params.append(filters['action_type'])
            if filters.get('table_name'):
                query += " AND table_name = ?"
                params.append(filters['table_name'])
            if filters.get('from_date'):
                query += " AND created_at >= ?"
                params.append(filters['from_date'])
            if filters.get('to_date'):
                query += " AND created_at <= ?"
                params.append(filters['to_date'])
            if filters.get('search'):
                query += " AND (username LIKE ? OR description LIKE ?)"
                search_param = f"%{filters['search']}%"
                params.extend([search_param, search_param])
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers (bilingual)
        if session.get('language') == 'ar':
            headers = [
                'المعرف', 'التاريخ', 'اسم المستخدم', 'الدور', 
                'الإجراء', 'الجدول', 'معرف السجل', 'عنوان IP', 'الوصف'
            ]
        else:
            headers = [
                'ID', 'Date/Time', 'Username', 'Role', 
                'Action', 'Table', 'Record ID', 'IP Address', 'Description'
            ]
        writer.writerow(headers)
        
        # Write data
        if cursor.description:
            for row in cursor.fetchall():
                writer.writerow(row)
        
        output.seek(0)
        
        # Generate filename with date
        filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error exporting logs: {e}")
        flash('Error exporting logs', 'danger')
        return redirect(url_for('audit.audit_logs'))
    finally:
        cursor.close()
@staticmethod
def get_action_types():
    """Get distinct action types for filter dropdown"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("SELECT DISTINCT action_type FROM AuditLogs ORDER BY action_type")
        
        if cursor.description is None:
            return []
        
        actions = [row[0] for row in cursor.fetchall()]
        return actions
    except Exception as e:
        print(f"Error in get_action_types: {e}")
        return []
    finally:
        cursor.close()

@staticmethod
def get_tables():
    """Get distinct table names for filter dropdown"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("SELECT DISTINCT table_name FROM AuditLogs ORDER BY table_name")
        
        if cursor.description is None:
            return []
        
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    except Exception as e:
        print(f"Error in get_tables: {e}")
        return []
    finally:
        cursor.close()