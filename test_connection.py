import pyodbc

print("Testing SQL Server Connections...")
print("-" * 50)

# Method 1: Try Windows Authentication first (if you're on Windows)
try:
    conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=master;Trusted_Connection=yes;'
    conn = pyodbc.connect(conn_str)
    print("✓ Windows Authentication: SUCCESS")
    conn.close()
except Exception as e:
    print(f"✗ Windows Authentication: FAILED - {str(e)}")

# Method 2: Try with (local) instead of localhost
try:
    conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=(local);DATABASE=master;Trusted_Connection=yes;'
    conn = pyodbc.connect(conn_str)
    print("✓ (local) Windows Auth: SUCCESS")
    conn.close()
except Exception as e:
    print(f"✗ (local) Windows Auth: FAILED - {str(e)}")

# Method 3: Try with .\SQLEXPRESS (default instance name)
try:
    conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\SQLEXPRESS;DATABASE=master;Trusted_Connection=yes;'
    conn = pyodbc.connect(conn_str)
    print("✓ .\\SQLEXPRESS Windows Auth: SUCCESS")
    conn.close()
except Exception as e:
    print(f"✗ .\\SQLEXPRESS Windows Auth: FAILED - {str(e)}")

# Method 4: Try SQL Auth with sa (replace password with your actual sa password)
try:
    conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=master;UID=sa;PWD=your_password_here;'
    conn = pyodbc.connect(conn_str)
    print("✓ SQL Auth (sa): SUCCESS")
    conn.close()
except Exception as e:
    print(f"✗ SQL Auth (sa): FAILED - {str(e)}")

print("\n" + "="*50)
print("If all connections failed, check:")
print("1. Is SQL Server running? (Check Services)")
print("2. Is TCP/IP protocol enabled? (SQL Server Configuration Manager)")
print("3. Is SQL Server Browser service running?")
print("4. Is firewall blocking port 1433?")