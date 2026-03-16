import pyodbc
from flask import g
import os
from dotenv import load_dotenv

load_dotenv()

def get_db():
    """Get database connection using Windows Authentication"""
    if 'db' not in g:
        server = os.getenv('SQL_SERVER', 'localhost')
        database = os.getenv('SQL_DATABASE', 'SchoolManagementSystem')
        
        # Use Windows Authentication (Trusted_Connection)
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
        )
        
        try:
            g.db = pyodbc.connect(conn_str, timeout=30)
            print("Successfully connected to SQL Server using Windows Authentication")
        except Exception as e:
            print(f"Connection error: {e}")
            # Try alternative server names if localhost fails
            alternatives = ['(local)', '.', '127.0.0.1']
            for alt_server in alternatives:
                try:
                    alt_conn_str = (
                        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                        f"SERVER={alt_server};"
                        f"DATABASE={database};"
                        f"Trusted_Connection=yes;"
                    )
                    g.db = pyodbc.connect(alt_conn_str, timeout=30)
                    print(f"Successfully connected using {alt_server}")
                    break
                except:
                    continue
            else:
                raise Exception("Could not connect to SQL Server with any method")
    
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()