"""
Test SQL Server connectivity for CSAT Guardian.
This script fetches the password from Key Vault and tests the connection.

Usage:
    # Using environment variables:
    export SQL_SERVER=sql-csatguardian.database.windows.net
    export SQL_DATABASE=sqldb-csatguardian
    export KEY_VAULT_NAME=kv-csatguardian
    python scripts/test_db_connection.py
"""
import os
import sys
import subprocess

# Configuration - Override via environment variables
SQL_SERVER = os.environ.get('SQL_SERVER', 'sql-csatguardian.database.windows.net')
SQL_DATABASE = os.environ.get('SQL_DATABASE', 'sqldb-csatguardian')
KEY_VAULT_NAME = os.environ.get('KEY_VAULT_NAME', 'kv-csatguardian')
SQL_USERNAME = os.environ.get('SQL_USERNAME', 'sqladmin')
RESOURCE_GROUP = os.environ.get('RESOURCE_GROUP', 'KMonteagudo_CSAT_Guardian')

# First, get password from Key Vault via Azure CLI
result = subprocess.run(
    f'az keyvault secret show --vault-name {KEY_VAULT_NAME} --name SqlServer--AdminPassword --query value -o tsv',
    capture_output=True, text=True, shell=True
)
password = result.stdout.strip()

if not password:
    print("ERROR: Could not retrieve password from Key Vault")
    print(result.stderr)
    sys.exit(1)

print(f"✓ Retrieved password from Key Vault ({KEY_VAULT_NAME})")

# Now test the connection
try:
    import pyodbc
    
    conn_str = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server=tcp:{SQL_SERVER},1433;"
        f"Database={SQL_DATABASE};"
        f"Uid={SQL_USERNAME};"
        f"Pwd={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    print(f"Connecting to {SQL_SERVER}...")
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
            # Extract server name without domain
            server_name = SQL_SERVER.split('.')[0]
            print(f"\n  Your IP appears to be: {ip_match.group(1)}")
            print(f"  Run this to add firewall rule:")
            print(f"  az sql server firewall-rule create --resource-group {RESOURCE_GROUP} --server {server_name} --name AllowMyIP --start-ip-address {ip_match.group(1)} --end-ip-address {ip_match.group(1)}")
    sys.exit(1)
