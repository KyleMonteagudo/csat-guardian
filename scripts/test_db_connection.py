"""
Test SQL Server connectivity for CSAT Guardian.
This script fetches the password from Key Vault and tests the connection.
"""
import os
import sys
import subprocess

# First, get password from Key Vault via Azure CLI
result = subprocess.run(
    ['cmd', '/c', 'az', 'keyvault', 'secret', 'show', 
     '--vault-name', 'kv-csatguardian-dev', 
     '--name', 'SqlServer--AdminPassword', 
     '--query', 'value', '-o', 'tsv'],
    capture_output=True, text=True, shell=True
)
password = result.stdout.strip()

if not password:
    print("ERROR: Could not retrieve password from Key Vault")
    print(result.stderr)
    sys.exit(1)

print(f"✓ Retrieved password from Key Vault")

# Now test the connection
try:
    import pyodbc
    
    server = "sql-csatguardian-dev.database.usgovcloudapi.net"
    database = "sqldb-csatguardian-dev"
    username = "sqladmin"
    
    conn_str = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server=tcp:{server},1433;"
        f"Database={database};"
        f"Uid={username};"
        f"Pwd={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    print(f"Connecting to {server}...")
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Test query
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()[0]
    print(f"✓ SUCCESS! Connected to SQL Server")
    print(f"  Version: {version[:60]}...")
    
    # Check what tables exist
    cursor.execute("""
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
    """)
    tables = cursor.fetchall()
    print(f"  Tables: {[t[0] for t in tables] if tables else '(none - database is empty)'}")
    
    conn.close()
    print("✓ Connection closed successfully")
    
except pyodbc.Error as e:
    print(f"✗ Connection FAILED: {e}")
    # Extract the IP from error message if present
    error_str = str(e)
    if "IP address" in error_str:
        import re
        ip_match = re.search(r"IP address '([\d.]+)'", error_str)
        if ip_match:
            print(f"\n  Your IP appears to be: {ip_match.group(1)}")
            print(f"  Run this to add firewall rule:")
            print(f"  az sql server firewall-rule create --resource-group rg-csatguardian-dev --server sql-csatguardian-dev --name AllowMyIP --start-ip-address {ip_match.group(1)} --end-ip-address {ip_match.group(1)}")
    sys.exit(1)
