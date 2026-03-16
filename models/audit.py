from database.db_config import get_db
from flask import request, session
import json
from datetime import datetime

class AuditLog:
    @staticmethod
    def log_action(action_type, table_name, record_id=None, old_data=None, new_data=None, description=None):
        """Log an action to the audit log"""
        if 'user_id' not in session:
            return
        
        db = get_db()
        cursor = db.cursor()
        
        # Convert data to JSON if provided
        old_data_json = json.dumps(old_data, ensure_ascii=False) if old_data else None
        new_data_json = json.dumps(new_data, ensure_ascii=False) if new_data else None
        
        # Get IP address and user agent
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', None)
        
        cursor.execute("""
        INSERT INTO AuditLogs (
            user_id, username, user_role, action_type, table_name, 
            record_id, old_data, new_data, ip_address, user_agent, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session['user_id'],
            session.get('username', 'unknown'),
            session.get('role', 'unknown'),
            action_type,
            table_name,
            record_id,
            old_data_json,
            new_data_json,
            ip_address,
            user_agent,
            description
        ))
        
        db.commit()
        cursor.close()
    
    @staticmethod
    def get_logs(filters=None, limit=100, offset=0):
        """Get audit logs with optional filters"""
        db = get_db()
        cursor = db.cursor()
        
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
        
        columns = [column[0] for column in cursor.description]
        logs = []
        for row in cursor.fetchall():
            log = dict(zip(columns, row))
            logs.append(log)
        
        cursor.close()
        return logs
    
    @staticmethod
    def get_logs_count(filters=None):
        """Get total count of logs matching filters"""
        db = get_db()
        cursor = db.cursor()
        
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
        cursor.close()
        return count
    
    @staticmethod
    def get_action_types():
        """Get distinct action types for filter dropdown"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("SELECT DISTINCT action_type FROM AuditLogs ORDER BY action_type")
        actions = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return actions
    
    @staticmethod
    def get_tables():
        """Get distinct table names for filter dropdown"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("SELECT DISTINCT table_name FROM AuditLogs ORDER BY table_name")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables