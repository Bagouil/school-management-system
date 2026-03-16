from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database.db_config import get_db
from datetime import datetime
from utils.permission_decorator import role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/access-requests')
@role_required('admin')
def access_requests():
    """View all access requests"""
    db = get_db()
    cursor = db.cursor()
    
    # Get all requests
    cursor.execute("""
    SELECT 
        request_id, user_id, username, current_role, 
        requested_page, message, status, 
        CONVERT(varchar, created_at, 20) as created_at
    FROM AccessRequests
    ORDER BY 
        CASE status 
            WHEN 'pending' THEN 1 
            WHEN 'approved' THEN 2 
            ELSE 3 
        END,
        created_at DESC
    """)
    
    columns = [column[0] for column in cursor.description]
    requests = []
    pending_count = 0
    approved_count = 0
    rejected_count = 0
    
    for row in cursor.fetchall():
        req = dict(zip(columns, row))
        requests.append(req)
        
        if req['status'] == 'pending':
            pending_count += 1
        elif req['status'] == 'approved':
            approved_count += 1
        elif req['status'] == 'rejected':
            rejected_count += 1
    
    cursor.close()
    
    return render_template('admin/access_requests.html',
                         requests=requests,
                         pending_count=pending_count,
                         approved_count=approved_count,
                         rejected_count=rejected_count)

@admin_bp.route('/access-requests/<int:request_id>/approve', methods=['POST'])
@role_required('admin')
def approve_request(request_id):
    """Approve an access request"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
        UPDATE AccessRequests
        SET status = 'approved', reviewed_by = ?, reviewed_at = GETDATE()
        WHERE request_id = ?
        """, (session['user_id'], request_id))
        
        db.commit()
        
        # Get the request details to know which user to notify
        cursor.execute("SELECT user_id, username FROM AccessRequests WHERE request_id = ?", (request_id,))
        request_data = cursor.fetchone()
        
        # You could add a notification system here
        
        cursor.close()
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/access-requests/<int:request_id>/reject', methods=['POST'])
@role_required('admin')
def reject_request(request_id):
    """Reject an access request"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
        UPDATE AccessRequests
        SET status = 'rejected', reviewed_by = ?, reviewed_at = GETDATE()
        WHERE request_id = ?
        """, (session['user_id'], request_id))
        
        db.commit()
        cursor.close()
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/access-requests/<int:request_id>/message')
@role_required('admin')
def get_request_message(request_id):
    
    
    """Get full message for a request"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
    SELECT username, current_role, message, CONVERT(varchar, created_at, 20) as created_at
    FROM AccessRequests
    WHERE request_id = ?
    """, (request_id,))
    
    row = cursor.fetchone()
    cursor.close()
    
    if row:
        return jsonify({
            'username': row[0],
            'current_role': row[1],
            'message': row[2] or '',
            'created_at': row[3]
        })
    
    return jsonify({'error': 'Request not found'}), 404
@admin_bp.context_processor
def inject_pending_count():
    """Inject pending requests count for all templates"""
    if 'user_id' in session and session['role'] == 'admin':
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM AccessRequests WHERE status = 'pending'")
        count = cursor.fetchone()[0]
        cursor.close()
        return {'pending_requests_count': count}
    return {'pending_requests_count': 0}