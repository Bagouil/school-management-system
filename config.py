import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # SQL Server Connection
    SQL_SERVER = os.environ.get('SQL_SERVER') or 'localhost'
    SQL_DATABASE = os.environ.get('SQL_DATABASE') or 'SchoolManagementSystem'
    SQL_USERNAME = os.environ.get('SQL_USERNAME') or 'sa'
    SQL_PASSWORD = os.environ.get('SQL_PASSWORD') or 'your_password'
    
    # Connection string for pyodbc
    SQL_CONNECTION_STRING = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USERNAME};PWD={SQL_PASSWORD}'
    
    # Upload folders
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Language settings
    LANGUAGES = {
        'ar': 'Arabic',
        'en': 'English'
    }
    DEFAULT_LANGUAGE = 'ar'