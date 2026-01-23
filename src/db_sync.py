# =============================================================================
# CSAT Guardian - Synchronous Database Module for Streamlit
# =============================================================================
# This module provides synchronous database access using pyodbc.
# Streamlit has issues with async libraries (aioodbc), so we use sync pyodbc.
#
# Usage:
#   from db_sync import SyncDatabaseManager
#   db = SyncDatabaseManager()
#   cases = db.get_cases_for_engineer("ENG001")
# =============================================================================

import os
import pyodbc
from datetime import datetime
from typing import Optional, List
from pathlib import Path

# Try to load environment variables from .env.local (parent directory)
try:
    from dotenv import load_dotenv
    # Look for .env.local in parent directory (csat-guardian folder)
    env_path = Path(__file__).parent.parent / ".env.local"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[OK] Loaded environment from {env_path}")
    else:
        # Try current directory
        load_dotenv(".env.local")
except ImportError:
    pass  # dotenv not installed, rely on environment variables

from models import Case, Engineer, Customer, TimelineEntry, CaseStatus, CasePriority, TimelineEntryType


class SyncDatabaseManager:
    """
    Synchronous database manager for Streamlit compatibility.
    Uses pyodbc instead of aioodbc to avoid event loop conflicts.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            connection_string: Optional ADO.NET style connection string.
                             If not provided, reads from DATABASE_CONNECTION_STRING env var.
        """
        self.connection_string = connection_string or os.getenv("DATABASE_CONNECTION_STRING", "")
        self._connection: Optional[pyodbc.Connection] = None
        
        if not self.connection_string:
            raise ValueError("DATABASE_CONNECTION_STRING environment variable not set")
    
    def _get_odbc_connection_string(self) -> str:
        """Convert ADO.NET connection string to ODBC format."""
        parts = {}
        for part in self.connection_string.split(';'):
            if '=' in part:
                key, value = part.split('=', 1)
                parts[key.strip()] = value.strip()
        
        return (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"Server={parts.get('Server', '')};"
            f"Database={parts.get('Initial Catalog', '')};"
            f"UID={parts.get('User ID', '')};"
            f"PWD={parts.get('Password', '')};"
            "Encrypt=yes;"
            "TrustServerCertificate=no"
        )
    
    def connect(self) -> pyodbc.Connection:
        """Get or create database connection."""
        if self._connection is None:
            odbc_str = self._get_odbc_connection_string()
            self._connection = pyodbc.connect(odbc_str, timeout=30)
        return self._connection
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def get_engineers(self) -> List[Engineer]:
        """Get all engineers from the database."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, Name, Email, TeamsId, CreatedAt, UpdatedAt
            FROM Engineers
        """)
        
        engineers = []
        for row in cursor.fetchall():
            engineers.append(Engineer(
                id=row.Id,
                name=row.Name,
                email=row.Email,
                teams_id=row.TeamsId
            ))
        
        return engineers
    
    def get_engineer(self, engineer_id: str) -> Optional[Engineer]:
        """Get a specific engineer by ID."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, Name, Email, TeamsId
            FROM Engineers
            WHERE Id = ?
        """, (engineer_id,))
        
        row = cursor.fetchone()
        if row:
            return Engineer(
                id=row.Id,
                name=row.Name,
                email=row.Email,
                teams_id=row.TeamsId
            )
        return None
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get a specific customer by ID."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, Company
            FROM Customers
            WHERE Id = ?
        """, (customer_id,))
        
        row = cursor.fetchone()
        if row:
            return Customer(
                id=row.Id,
                company=row.Company
            )
        return None
    
    def get_timeline_entries(self, case_id: str) -> List[TimelineEntry]:
        """Get timeline entries for a case."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, 
                   Direction, IsCustomerCommunication
            FROM TimelineEntries
            WHERE CaseId = ?
            ORDER BY CreatedOn ASC
        """, (case_id,))
        
        entries = []
        for row in cursor.fetchall():
            # Map entry type string to enum
            entry_type = TimelineEntryType.NOTE
            if row.EntryType:
                entry_type_str = row.EntryType.lower()
                if entry_type_str == "email":
                    entry_type = TimelineEntryType.EMAIL
                elif entry_type_str == "phone_call":
                    entry_type = TimelineEntryType.PHONE_CALL
            
            entries.append(TimelineEntry(
                id=row.Id,
                case_id=row.CaseId,
                entry_type=entry_type,
                subject=row.Subject or "",
                content=row.Content or "",
                created_on=row.CreatedOn,
                created_by=row.CreatedBy or "Unknown",
                direction=row.Direction,
                is_customer_communication=bool(row.IsCustomerCommunication)
            ))
        
        return entries
    
    def _map_status(self, status_str: str) -> CaseStatus:
        """Map database status string to CaseStatus enum."""
        if not status_str:
            return CaseStatus.ACTIVE
        status_map = {
            "active": CaseStatus.ACTIVE,
            "in_progress": CaseStatus.IN_PROGRESS,
            "waiting_on_customer": CaseStatus.WAITING_ON_CUSTOMER,
            "waiting_customer": CaseStatus.WAITING_ON_CUSTOMER,  # Alternative spelling
            "waiting_on_vendor": CaseStatus.WAITING_ON_VENDOR,
            "resolved": CaseStatus.RESOLVED,
            "cancelled": CaseStatus.CANCELLED,
            # Map escalated to active since ESCALATED doesn't exist in enum
            "escalated": CaseStatus.ACTIVE,
        }
        return status_map.get(status_str.lower(), CaseStatus.ACTIVE)
    
    def _map_priority(self, priority_str: str) -> CasePriority:
        """Map database priority string to CasePriority enum."""
        priority_map = {
            "low": CasePriority.LOW,
            "medium": CasePriority.MEDIUM,
            "high": CasePriority.HIGH,
        }
        return priority_map.get(priority_str.lower(), CasePriority.MEDIUM)
    
    def get_cases_for_engineer(self, engineer_id: str) -> List[Case]:
        """Get all cases assigned to an engineer."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get the engineer first
        engineer = self.get_engineer(engineer_id)
        if not engineer:
            return []
        
        cursor.execute("""
            SELECT c.Id, c.Title, c.Description, c.Status, c.Priority,
                   c.CreatedOn, c.ModifiedOn, c.OwnerId, c.CustomerId
            FROM Cases c
            WHERE c.OwnerId = ?
            ORDER BY c.CreatedOn DESC
        """, (engineer_id,))
        
        cases = []
        for row in cursor.fetchall():
            # Get customer
            customer = self.get_customer(row.CustomerId)
            if not customer:
                customer = Customer(id=row.CustomerId, company="Unknown")
            
            # Get timeline entries
            timeline = self.get_timeline_entries(row.Id)
            
            cases.append(Case(
                id=row.Id,
                title=row.Title,
                description=row.Description or "",
                status=self._map_status(row.Status),
                priority=self._map_priority(row.Priority),
                created_on=row.CreatedOn,
                modified_on=row.ModifiedOn,
                owner=engineer,
                customer=customer,
                timeline=timeline
            ))
        
        return cases
    
    def get_all_active_cases(self) -> List[Case]:
        """Get all active cases (not resolved/cancelled)."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.Id, c.Title, c.Description, c.Status, c.Priority,
                   c.CreatedOn, c.ModifiedOn, c.OwnerId, c.CustomerId
            FROM Cases c
            WHERE c.Status NOT IN ('resolved', 'cancelled')
            ORDER BY c.CreatedOn DESC
        """)
        
        cases = []
        for row in cursor.fetchall():
            # Get engineer
            engineer = self.get_engineer(row.OwnerId)
            if not engineer:
                engineer = Engineer(id=row.OwnerId, name="Unknown", email="unknown@contoso.com")
            
            # Get customer
            customer = self.get_customer(row.CustomerId)
            if not customer:
                customer = Customer(id=row.CustomerId, company="Unknown")
            
            # Get timeline entries
            timeline = self.get_timeline_entries(row.Id)
            
            cases.append(Case(
                id=row.Id,
                title=row.Title,
                description=row.Description or "",
                status=self._map_status(row.Status),
                priority=self._map_priority(row.Priority),
                created_on=row.CreatedOn,
                modified_on=row.ModifiedOn,
                owner=engineer,
                customer=customer,
                timeline=timeline
            ))
        
        return cases
    
    def test_connection(self) -> bool:
        """Test if database connection works."""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False


# Singleton instance for reuse
_db_instance: Optional[SyncDatabaseManager] = None


def get_database() -> Optional[SyncDatabaseManager]:
    """Get or create the singleton database instance."""
    global _db_instance
    
    if _db_instance is None:
        try:
            _db_instance = SyncDatabaseManager()
            if _db_instance.test_connection():
                print("[OK] Connected to Azure SQL Database")
            else:
                _db_instance = None
        except Exception as e:
            print(f"[FAIL] Failed to connect to database: {e}")
            _db_instance = None
    
    return _db_instance
