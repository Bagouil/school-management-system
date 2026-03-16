import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, subfolder='uploads'):
    """Save uploaded file and return the path"""
    if file and allowed_file(file.filename):
        # Create secure filename and add unique identifier
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        new_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Create upload folder if it doesn't exist
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'uploads', subfolder)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_folder, new_filename)
        file.save(file_path)
        
        # Return relative path for database
        return f"uploads/{subfolder}/{new_filename}"
    
    return None

def delete_file(file_path):
    """Delete a file from the filesystem"""
    if file_path:
        full_path = os.path.join(current_app.root_path, 'static', file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    return False