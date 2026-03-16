import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_standalone():
    """Get database connection for standalone scripts (no Flask context)"""
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
        conn = pyodbc.connect(conn_str, timeout=30)
        print("✓ Connected to SQL Server successfully")
        return conn
    except Exception as e:
        print(f"✗ Connection error: {e}")
        # Try alternative server names
        alternatives = ['(local)', '.', '127.0.0.1']
        for alt_server in alternatives:
            try:
                alt_conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={alt_server};"
                    f"DATABASE={database};"
                    f"Trusted_Connection=yes;"
                )
                conn = pyodbc.connect(alt_conn_str, timeout=30)
                print(f"✓ Connected using {alt_server}")
                return conn
            except:
                continue
        raise Exception("Could not connect to SQL Server with any method")