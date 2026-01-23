"""
CSAT Guardian - Database Seeding Script
========================================
Creates tables and populates sample data in Azure SQL Database.

Usage:
    python scripts/seed_database.py
"""
import subprocess
import sys
import pyodbc
from datetime import datetime, timedelta
import uuid

def get_password_from_keyvault():
    """Retrieve SQL password from Key Vault."""
    result = subprocess.run(
        'az keyvault secret show --vault-name kv-csatguardian-dev --name SqlServer--AdminPassword --query value -o tsv',
        capture_output=True, text=True, shell=True
    )
    return result.stdout.strip()

def get_connection():
    """Get database connection."""
    password = get_password_from_keyvault()
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=tcp:sql-csatguardian-dev.database.usgovcloudapi.net,1433;"
        "Database=sqldb-csatguardian-dev;"
        "Uid=sqladmin;"
        f"Pwd={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)

def create_tables(cursor):
    """Create all required tables."""
    print("Creating tables...")
    
    # Engineers table
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Engineers' AND xtype='U')
        CREATE TABLE Engineers (
            Id NVARCHAR(50) PRIMARY KEY,
            Name NVARCHAR(200) NOT NULL,
            Email NVARCHAR(200) NOT NULL UNIQUE,
            TeamsId NVARCHAR(100) NULL,
            CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
            UpdatedAt DATETIME2 DEFAULT GETUTCDATE()
        )
    """)
    print("  ✓ Engineers table")
    
    # Customers table
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Customers' AND xtype='U')
        CREATE TABLE Customers (
            Id NVARCHAR(50) PRIMARY KEY,
            Company NVARCHAR(200) NULL,
            CreatedAt DATETIME2 DEFAULT GETUTCDATE()
        )
    """)
    print("  ✓ Customers table")
    
    # Cases table
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Cases' AND xtype='U')
        CREATE TABLE Cases (
            Id NVARCHAR(50) PRIMARY KEY,
            Title NVARCHAR(500) NOT NULL,
            Description NVARCHAR(MAX) NOT NULL,
            Status NVARCHAR(50) NOT NULL DEFAULT 'active',
            Priority NVARCHAR(20) NOT NULL DEFAULT 'medium',
            CreatedOn DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
            ModifiedOn DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
            OwnerId NVARCHAR(50) NOT NULL,
            CustomerId NVARCHAR(50) NOT NULL,
            FOREIGN KEY (OwnerId) REFERENCES Engineers(Id),
            FOREIGN KEY (CustomerId) REFERENCES Customers(Id)
        )
    """)
    print("  ✓ Cases table")
    
    # Timeline Entries table
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TimelineEntries' AND xtype='U')
        CREATE TABLE TimelineEntries (
            Id NVARCHAR(50) PRIMARY KEY,
            CaseId NVARCHAR(50) NOT NULL,
            EntryType NVARCHAR(20) NOT NULL,
            Subject NVARCHAR(500) NULL,
            Content NVARCHAR(MAX) NOT NULL,
            CreatedOn DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
            CreatedBy NVARCHAR(200) NOT NULL,
            Direction NVARCHAR(20) NULL,
            IsCustomerCommunication BIT DEFAULT 0,
            FOREIGN KEY (CaseId) REFERENCES Cases(Id)
        )
    """)
    print("  ✓ TimelineEntries table")
    
    # Alerts table (for tracking sent alerts)
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Alerts' AND xtype='U')
        CREATE TABLE Alerts (
            Id NVARCHAR(50) PRIMARY KEY,
            CaseId NVARCHAR(50) NOT NULL,
            AlertType NVARCHAR(50) NOT NULL,
            Message NVARCHAR(MAX) NOT NULL,
            SentAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
            RecipientId NVARCHAR(50) NOT NULL,
            Acknowledged BIT DEFAULT 0,
            AcknowledgedAt DATETIME2 NULL,
            FOREIGN KEY (CaseId) REFERENCES Cases(Id),
            FOREIGN KEY (RecipientId) REFERENCES Engineers(Id)
        )
    """)
    print("  ✓ Alerts table")
    
    # Sentiment Analysis Results table
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='SentimentResults' AND xtype='U')
        CREATE TABLE SentimentResults (
            Id NVARCHAR(50) PRIMARY KEY,
            CaseId NVARCHAR(50) NOT NULL,
            TimelineEntryId NVARCHAR(50) NULL,
            SentimentLabel NVARCHAR(20) NOT NULL,
            SentimentScore FLOAT NOT NULL,
            AnalyzedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
            ModelVersion NVARCHAR(50) NULL,
            FOREIGN KEY (CaseId) REFERENCES Cases(Id)
        )
    """)
    print("  ✓ SentimentResults table")

def seed_engineers(cursor):
    """Seed engineer data."""
    print("Seeding engineers...")
    
    engineers = [
        ("eng-001", "John Smith", "jsmith@microsoft.com", "teams-001"),
        ("eng-002", "Sarah Johnson", "sjohnson@microsoft.com", "teams-002"),
        ("eng-003", "Mike Chen", "mchen@microsoft.com", "teams-003"),
    ]
    
    for eng in engineers:
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Engineers WHERE Id = ?)
            INSERT INTO Engineers (Id, Name, Email, TeamsId) VALUES (?, ?, ?, ?)
        """, eng[0], eng[0], eng[1], eng[2], eng[3])
        print(f"  ✓ {eng[1]}")

def seed_customers(cursor):
    """Seed customer data."""
    print("Seeding customers...")
    
    customers = [
        ("cust-001", "Contoso Ltd"),
        ("cust-002", "Fabrikam Inc"),
        ("cust-003", "Adventure Works"),
        ("cust-004", "Northwind Traders"),
        ("cust-005", "Tailspin Toys"),
        ("cust-006", "Wide World Importers"),
    ]
    
    for cust in customers:
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Customers WHERE Id = ?)
            INSERT INTO Customers (Id, Company) VALUES (?, ?)
        """, cust[0], cust[0], cust[1])
        print(f"  ✓ {cust[1]}")

def seed_cases(cursor):
    """Seed case data with various scenarios."""
    print("Seeding cases...")
    
    now = datetime.utcnow()
    
    cases = [
        # CASE 1: Happy customer - positive sentiment
        {
            "id": "case-001",
            "title": "Azure VM Performance Optimization",
            "description": "Customer wants help optimizing their Azure VM performance for a web application.",
            "status": "active",
            "priority": "medium",
            "created_on": now - timedelta(days=3),
            "modified_on": now - timedelta(hours=4),
            "owner_id": "eng-001",
            "customer_id": "cust-001",
        },
        # CASE 2: Frustrated customer - negative sentiment, needs intervention
        {
            "id": "case-002",
            "title": "Repeated VM Crashes - URGENT",
            "description": "Production VMs keep crashing. Customer has escalated twice. Very frustrated.",
            "status": "active",
            "priority": "high",
            "created_on": now - timedelta(days=5),
            "modified_on": now - timedelta(hours=2),
            "owner_id": "eng-002",
            "customer_id": "cust-002",
        },
        # CASE 3: Neutral customer - standard case
        {
            "id": "case-003",
            "title": "Storage Account Configuration Question",
            "description": "Customer has questions about configuring geo-redundant storage.",
            "status": "active",
            "priority": "low",
            "created_on": now - timedelta(days=2),
            "modified_on": now - timedelta(hours=8),
            "owner_id": "eng-003",
            "customer_id": "cust-003",
        },
        # CASE 4: At-risk customer - sentiment declining
        {
            "id": "case-004",
            "title": "Billing Discrepancy Investigation",
            "description": "Customer disputing charges for last 3 months. Initially patient, now frustrated.",
            "status": "active",
            "priority": "high",
            "created_on": now - timedelta(days=10),
            "modified_on": now - timedelta(days=1),
            "owner_id": "eng-001",
            "customer_id": "cust-004",
        },
        # CASE 5: 7-day compliance warning - approaching deadline
        {
            "id": "case-005",
            "title": "Network Security Group Setup",
            "description": "Customer needs help setting up NSG rules for their VNet.",
            "status": "active",
            "priority": "medium",
            "created_on": now - timedelta(days=6),
            "modified_on": now - timedelta(days=5, hours=12),
            "owner_id": "eng-002",
            "customer_id": "cust-005",
        },
        # CASE 6: 7-day compliance breach - past deadline
        {
            "id": "case-006",
            "title": "Azure AD Integration Issues",
            "description": "Customer having trouble integrating Azure AD with their on-prem AD.",
            "status": "active",
            "priority": "medium",
            "created_on": now - timedelta(days=14),
            "modified_on": now - timedelta(days=9),
            "owner_id": "eng-003",
            "customer_id": "cust-006",
        },
    ]
    
    for case in cases:
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Cases WHERE Id = ?)
            INSERT INTO Cases (Id, Title, Description, Status, Priority, CreatedOn, ModifiedOn, OwnerId, CustomerId)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, case["id"], case["id"], case["title"], case["description"], case["status"], 
           case["priority"], case["created_on"], case["modified_on"], case["owner_id"], case["customer_id"])
        print(f"  ✓ {case['id']}: {case['title'][:40]}...")

def seed_timeline_entries(cursor):
    """Seed timeline entries for each case."""
    print("Seeding timeline entries...")
    
    now = datetime.utcnow()
    
    entries = [
        # Case 1: Happy customer timeline
        {
            "id": "entry-001-01",
            "case_id": "case-001",
            "entry_type": "email",
            "subject": "Initial Request",
            "content": "Hi, I'd like some help optimizing our VM performance. We're running a web app that's getting slow during peak hours.",
            "created_on": now - timedelta(days=3),
            "created_by": "Customer (Contoso)",
            "direction": "inbound",
            "is_customer": True
        },
        {
            "id": "entry-001-02",
            "case_id": "case-001",
            "entry_type": "note",
            "subject": "Engineer Notes",
            "content": "Reviewed customer's VM configuration. Identified potential improvements in disk I/O and memory allocation.",
            "created_on": now - timedelta(days=2, hours=20),
            "created_by": "John Smith",
            "direction": None,
            "is_customer": False
        },
        {
            "id": "entry-001-03",
            "case_id": "case-001",
            "entry_type": "email",
            "subject": "RE: Initial Request",
            "content": "Thank you so much for the quick response! The recommendations look great. I'll implement them today.",
            "created_on": now - timedelta(days=2, hours=16),
            "created_by": "Customer (Contoso)",
            "direction": "inbound",
            "is_customer": True
        },
        
        # Case 2: Frustrated customer timeline
        {
            "id": "entry-002-01",
            "case_id": "case-002",
            "entry_type": "email",
            "subject": "Production VMs Crashing",
            "content": "Our production VMs have crashed 3 times this week. This is causing significant business impact. We need immediate assistance.",
            "created_on": now - timedelta(days=5),
            "created_by": "Customer (Fabrikam)",
            "direction": "inbound",
            "is_customer": True
        },
        {
            "id": "entry-002-02",
            "case_id": "case-002",
            "entry_type": "phone_call",
            "subject": "Call with customer",
            "content": "Customer extremely frustrated. They've lost revenue due to downtime. Promised to escalate and provide update within 2 hours.",
            "created_on": now - timedelta(days=4, hours=12),
            "created_by": "Sarah Johnson",
            "direction": "outbound",
            "is_customer": False
        },
        {
            "id": "entry-002-03",
            "case_id": "case-002",
            "entry_type": "email",
            "subject": "STILL WAITING FOR RESOLUTION",
            "content": "It's been over 24 hours and we're still having crashes! This is UNACCEPTABLE. I need to speak with a manager immediately. We're considering moving to another cloud provider if this isn't resolved TODAY.",
            "created_on": now - timedelta(days=3, hours=8),
            "created_by": "Customer (Fabrikam)",
            "direction": "inbound",
            "is_customer": True
        },
        {
            "id": "entry-002-04",
            "case_id": "case-002",
            "entry_type": "email",
            "subject": "RE: STILL WAITING FOR RESOLUTION",
            "content": "I demand a call with your manager. This level of service is completely unacceptable for the premium support we're paying for!",
            "created_on": now - timedelta(days=2, hours=4),
            "created_by": "Customer (Fabrikam)",
            "direction": "inbound",
            "is_customer": True
        },
        
        # Case 3: Neutral customer timeline
        {
            "id": "entry-003-01",
            "case_id": "case-003",
            "entry_type": "email",
            "subject": "Storage configuration question",
            "content": "Hello, I have a question about geo-redundant storage. What's the difference between GRS and RA-GRS?",
            "created_on": now - timedelta(days=2),
            "created_by": "Customer (Adventure Works)",
            "direction": "inbound",
            "is_customer": True
        },
        {
            "id": "entry-003-02",
            "case_id": "case-003",
            "entry_type": "email",
            "subject": "RE: Storage configuration question",
            "content": "Thanks for the explanation. One follow-up: how does the failover process work for RA-GRS?",
            "created_on": now - timedelta(days=1, hours=16),
            "created_by": "Customer (Adventure Works)",
            "direction": "inbound",
            "is_customer": True
        },
        
        # Case 4: Declining sentiment timeline
        {
            "id": "entry-004-01",
            "case_id": "case-004",
            "entry_type": "email",
            "subject": "Billing question",
            "content": "Hi, I noticed some charges on our bill that I don't understand. Can you help clarify?",
            "created_on": now - timedelta(days=10),
            "created_by": "Customer (Northwind)",
            "direction": "inbound",
            "is_customer": True
        },
        {
            "id": "entry-004-02",
            "case_id": "case-004",
            "entry_type": "email",
            "subject": "RE: Billing question",
            "content": "Thanks for looking into this. Please let me know what you find.",
            "created_on": now - timedelta(days=8),
            "created_by": "Customer (Northwind)",
            "direction": "inbound",
            "is_customer": True
        },
        {
            "id": "entry-004-03",
            "case_id": "case-004",
            "entry_type": "email",
            "subject": "Following up on billing",
            "content": "It's been several days and I haven't heard back. I'm starting to get concerned about these charges.",
            "created_on": now - timedelta(days=5),
            "created_by": "Customer (Northwind)",
            "direction": "inbound",
            "is_customer": True
        },
        {
            "id": "entry-004-04",
            "case_id": "case-004",
            "entry_type": "email",
            "subject": "RE: Following up on billing",
            "content": "I'm really frustrated now. It's been 10 days and I still don't have answers about why we're being charged $5000 more than expected. This is affecting our budget planning!",
            "created_on": now - timedelta(days=1),
            "created_by": "Customer (Northwind)",
            "direction": "inbound",
            "is_customer": True
        },
        
        # Case 5: Approaching 7-day deadline
        {
            "id": "entry-005-01",
            "case_id": "case-005",
            "entry_type": "email",
            "subject": "NSG Configuration Help",
            "content": "We need help configuring our NSG rules. Can you provide guidance?",
            "created_on": now - timedelta(days=6),
            "created_by": "Customer (Tailspin)",
            "direction": "inbound",
            "is_customer": True
        },
        {
            "id": "entry-005-02",
            "case_id": "case-005",
            "entry_type": "note",
            "subject": "Initial assessment",
            "content": "Reviewed customer's current NSG setup. Will provide recommendations.",
            "created_on": now - timedelta(days=5, hours=12),
            "created_by": "Sarah Johnson",
            "direction": None,
            "is_customer": False
        },
        # Note: No recent updates - approaching 7-day warning
        
        # Case 6: Past 7-day deadline (breach)
        {
            "id": "entry-006-01",
            "case_id": "case-006",
            "entry_type": "email",
            "subject": "Azure AD Integration",
            "content": "We're having issues integrating Azure AD with our on-premises Active Directory.",
            "created_on": now - timedelta(days=14),
            "created_by": "Customer (Wide World)",
            "direction": "inbound",
            "is_customer": True
        },
        {
            "id": "entry-006-02",
            "case_id": "case-006",
            "entry_type": "note",
            "subject": "Research notes",
            "content": "Looking into hybrid AD configuration options for customer.",
            "created_on": now - timedelta(days=9),
            "created_by": "Mike Chen",
            "direction": None,
            "is_customer": False
        },
        # Note: Last update was 9 days ago - past 7-day compliance
    ]
    
    for entry in entries:
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM TimelineEntries WHERE Id = ?)
            INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, Direction, IsCustomerCommunication)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, entry["id"], entry["id"], entry["case_id"], entry["entry_type"], entry["subject"],
           entry["content"], entry["created_on"], entry["created_by"], entry["direction"], entry["is_customer"])
        print(f"  ✓ {entry['id']}: {entry['entry_type']} - {entry['subject'][:30]}...")

def main():
    """Main entry point."""
    print("=" * 60)
    print("CSAT Guardian - Database Seeding")
    print("=" * 60)
    print()
    
    print("Connecting to Azure SQL Database...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("✓ Connected successfully")
        print()
        
        # Create tables
        create_tables(cursor)
        conn.commit()
        print()
        
        # Seed data
        seed_engineers(cursor)
        conn.commit()
        print()
        
        seed_customers(cursor)
        conn.commit()
        print()
        
        seed_cases(cursor)
        conn.commit()
        print()
        
        seed_timeline_entries(cursor)
        conn.commit()
        print()
        
        # Summary
        print("=" * 60)
        print("SEEDING COMPLETE - Summary")
        print("=" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM Engineers")
        print(f"  Engineers: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM Customers")
        print(f"  Customers: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM Cases")
        print(f"  Cases: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM TimelineEntries")
        print(f"  Timeline Entries: {cursor.fetchone()[0]}")
        
        print()
        print("✓ Database seeding completed successfully!")
        
        conn.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
