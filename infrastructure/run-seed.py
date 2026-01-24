#!/usr/bin/env python3
"""
Run seed-database.sql against Azure SQL from the dev-box.
This script connects via pyodbc and executes the seed SQL.
"""

import pyodbc
import os

# Connection settings - update password if different
SERVER = "sql-csatguardian-dev.database.windows.net"
DATABASE = "sqldb-csatguardian-dev"
USERNAME = "sqladmin"
PASSWORD = "YourSecureP@ssword123!"

def main():
    # Build connection string
    conn_str = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={SERVER};"
        f"Database={DATABASE};"
        f"Uid={USERNAME};"
        f"Pwd={PASSWORD};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
    )
    
    print(f"Connecting to {SERVER}/{DATABASE}...")
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        print("Connected successfully!")
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    # Read the seed SQL file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    seed_file = os.path.join(script_dir, "seed-database.sql")
    
    print(f"Reading {seed_file}...")
    
    with open(seed_file, 'r') as f:
        sql_content = f.read()
    
    # Split by GO statements and execute each batch
    # Also handle semicolons for individual statements
    batches = sql_content.split('\nGO')
    
    executed = 0
    for batch in batches:
        batch = batch.strip()
        if not batch or batch.startswith('--'):
            continue
            
        # Skip PRINT statements
        if batch.upper().startswith('PRINT'):
            continue
            
        try:
            cursor.execute(batch)
            conn.commit()
            executed += 1
            
            # Check for SELECT results (verification queries)
            if batch.upper().strip().startswith('SELECT'):
                rows = cursor.fetchall()
                for row in rows:
                    print(f"  {row}")
                    
        except Exception as e:
            print(f"Error executing batch: {e}")
            print(f"Batch was: {batch[:100]}...")
    
    print(f"\nExecuted {executed} batches successfully!")
    
    # Verify the data
    print("\nVerifying data...")
    cursor.execute("SELECT COUNT(*) FROM Engineers")
    print(f"  Engineers: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM Customers")
    print(f"  Customers: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM Cases")
    print(f"  Cases: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM TimelineEntries")
    print(f"  TimelineEntries: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT Id, Title, OwnerId FROM Cases ORDER BY Id")
    print("\nCases loaded:")
    for row in cursor.fetchall():
        print(f"  {row.Id}: {row.Title[:40]}... -> {row.OwnerId}")
    
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
