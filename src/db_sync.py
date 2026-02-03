# =============================================================================
# CSAT Guardian - Synchronous Database Module
# =============================================================================
# This module provides synchronous database access using pyodbc.
# Uses per-query connections for thread safety with async FastAPI.
#
# Supports two authentication modes:
# 1. SQL Authentication (username/password) - for local development
# 2. Managed Identity (MSI) - for Azure production (AD-only auth)
#
# Usage:
#   from db_sync import SyncDatabaseManager
#   db = SyncDatabaseManager()
#   cases = db.get_cases_for_engineer("ENG001")
# =============================================================================

import os
import struct
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

from models import Case, Engineer, Customer, TimelineEntry, CaseStatus, CaseSeverity, TimelineEntryType


# Azure SQL resource scope for access token
AZURE_SQL_SCOPE = "https://database.windows.net/.default"


def _get_msi_access_token() -> bytes:
    """
    Get an access token for Azure SQL using Managed Identity.
    
    Returns:
        bytes: The access token encoded for pyodbc SQL_COPT_SS_ACCESS_TOKEN
    """
    from azure.identity import DefaultAzureCredential
    
    credential = DefaultAzureCredential()
    token = credential.get_token(AZURE_SQL_SCOPE)
    
    # Encode token for pyodbc - must be in specific format
    # See: https://docs.microsoft.com/en-us/sql/connect/odbc/using-azure-active-directory
    token_bytes = token.token.encode("utf-16-le")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    return token_struct


class SyncDatabaseManager:
    """
    Synchronous database manager with per-query connections.
    Uses pyodbc with fresh connections per query for thread safety.
    
    Supports two authentication modes controlled by USE_SQL_MANAGED_IDENTITY env var:
    - True (default): Uses Managed Identity for Azure AD authentication
    - False: Uses SQL authentication from connection string (User ID/Password)
    """
    
    def __init__(self, connection_string: Optional[str] = None, use_managed_identity: Optional[bool] = None):
        """
        Initialize database manager.
        
        Args:
            connection_string: Optional ADO.NET style connection string.
                             If not provided, reads from DATABASE_CONNECTION_STRING env var.
            use_managed_identity: Whether to use MSI for authentication.
                                If not provided, reads from USE_SQL_MANAGED_IDENTITY env var (default: True).
        """
        self.connection_string = connection_string or os.getenv("DATABASE_CONNECTION_STRING", "")
        self._connection: Optional[pyodbc.Connection] = None
        
        # Determine authentication mode
        if use_managed_identity is not None:
            self.use_managed_identity = use_managed_identity
        else:
            self.use_managed_identity = os.getenv("USE_SQL_MANAGED_IDENTITY", "true").lower() == "true"
        
        if not self.connection_string:
            raise ValueError("DATABASE_CONNECTION_STRING environment variable not set")
        
        # Parse connection string for server/database info
        self._parse_connection_string()
        
        print(f"[OK] Database manager initialized (MSI auth: {self.use_managed_identity})")
    
    def _parse_connection_string(self):
        """Parse ADO.NET connection string to extract server and database."""
        parts = {}
        for part in self.connection_string.split(';'):
            if '=' in part:
                key, value = part.split('=', 1)
                parts[key.strip()] = value.strip()
        
        self._server = parts.get('Server', '')
        self._database = parts.get('Initial Catalog', '')
        self._user_id = parts.get('User ID', '')
        self._password = parts.get('Password', '')
    
    def _get_odbc_connection_string(self) -> str:
        """Convert ADO.NET connection string to ODBC format (for SQL auth)."""
        return (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"Server={self._server};"
            f"Database={self._database};"
            f"UID={self._user_id};"
            f"PWD={self._password};"
            "Encrypt=yes;"
            "TrustServerCertificate=no"
        )
    
    def _get_odbc_connection_string_msi(self) -> str:
        """Get ODBC connection string for MSI authentication (no credentials)."""
        return (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"Server={self._server};"
            f"Database={self._database};"
            "Encrypt=yes;"
            "TrustServerCertificate=no"
        )
    
    def _get_new_connection(self) -> pyodbc.Connection:
        """Create a new database connection (thread-safe)."""
        if self.use_managed_identity:
            # Use MSI access token
            odbc_str = self._get_odbc_connection_string_msi()
            access_token = _get_msi_access_token()
            # SQL_COPT_SS_ACCESS_TOKEN = 1256
            return pyodbc.connect(odbc_str, attrs_before={1256: access_token}, timeout=30)
        else:
            # Use SQL authentication
            odbc_str = self._get_odbc_connection_string()
            return pyodbc.connect(odbc_str, timeout=30)
    
    def connect(self) -> pyodbc.Connection:
        """Get or create database connection.
        
        Note: For thread-safety with concurrent requests, prefer _get_new_connection().
        This method is kept for backward compatibility but creates a new connection
        each time to avoid 'Connection is busy' errors.
        """
        # Always create a new connection to avoid concurrency issues
        return self._get_new_connection()
    
    def close(self):
        """Close database connection (no-op since we use per-query connections)."""
        # Connections are now closed after each query
        pass
    
    def get_engineers(self) -> List[Engineer]:
        """Get all engineers from the database."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, email, team
                FROM engineers
            """)
            
            engineers = []
            for row in cursor.fetchall():
                engineers.append(Engineer(
                    id=row.id,
                    name=row.name,
                    email=row.email,
                    team=row.team
                ))
            
            return engineers
        finally:
            conn.close()
    
    def get_engineer(self, engineer_id: str) -> Optional[Engineer]:
        """Get a specific engineer by ID."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, email, team
                FROM engineers
                WHERE id = ?
            """, (engineer_id,))
            
            row = cursor.fetchone()
            if row:
                return Engineer(
                    id=row.id,
                    name=row.name,
                    email=row.email,
                    team=row.team
                )
            return None
        finally:
            conn.close()
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get a specific customer by ID."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, company, tier
                FROM customers
                WHERE id = ?
            """, (customer_id,))
            
            row = cursor.fetchone()
            if row:
                return Customer(
                    id=row.id,
                    company=row.company,
                    tier=row.tier
                )
            return None
        finally:
            conn.close()
    
    def get_timeline_entries(self, case_id: str) -> List[TimelineEntry]:
        """Get timeline entries for a case."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, case_id, entry_type, subject, content, created_by, 
                       created_on, direction, is_customer_communication
                FROM timeline_entries
                WHERE case_id = ?
                ORDER BY created_on ASC
            """, (case_id,))
            
            entries = []
            for row in cursor.fetchall():
                # Map entry type string to enum
                entry_type = TimelineEntryType.NOTE
                if row.entry_type:
                    entry_type_str = row.entry_type.lower()
                    if entry_type_str == "email_sent":
                        entry_type = TimelineEntryType.EMAIL_SENT
                    elif entry_type_str == "email_received":
                        entry_type = TimelineEntryType.EMAIL_RECEIVED
                    elif entry_type_str == "phone_call":
                        entry_type = TimelineEntryType.PHONE_CALL
                    elif entry_type_str == "note":
                        entry_type = TimelineEntryType.NOTE
                
                entries.append(TimelineEntry(
                    id=row.id,
                    case_id=row.case_id,
                    entry_type=entry_type,
                    subject=row.subject or "",
                    content=row.content or "",
                    created_on=row.created_on,
                    created_by=row.created_by or "Unknown",
                    direction=row.direction,
                    is_customer_communication=bool(row.is_customer_communication)
                ))
            
            return entries
        finally:
            conn.close()
    
    def _map_status(self, status_val) -> CaseStatus:
        """Map database status to CaseStatus enum."""
        if not status_val:
            return CaseStatus.ACTIVE
        status_str = str(status_val).lower()
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
        return status_map.get(status_str, CaseStatus.ACTIVE)
    
    def _map_severity(self, severity_val) -> CaseSeverity:
        """Map database severity to CaseSeverity enum."""
        if not severity_val:
            return CaseSeverity.SEV_C
        severity_str = str(severity_val).lower()
        severity_map = {
            "sev_a": CaseSeverity.SEV_A,
            "a": CaseSeverity.SEV_A,
            "critical": CaseSeverity.SEV_A,
            "4": CaseSeverity.SEV_A,
            "sev_b": CaseSeverity.SEV_B,
            "b": CaseSeverity.SEV_B,
            "high": CaseSeverity.SEV_B,
            "3": CaseSeverity.SEV_B,
            "sev_c": CaseSeverity.SEV_C,
            "c": CaseSeverity.SEV_C,
            "medium": CaseSeverity.SEV_C,
            "2": CaseSeverity.SEV_C,
            # Note: SEV_D doesn't exist in MS Support - map to SEV_C
            "sev_d": CaseSeverity.SEV_C,
            "d": CaseSeverity.SEV_C,
            "low": CaseSeverity.SEV_C,
            "1": CaseSeverity.SEV_C,
        }
        return severity_map.get(severity_str, CaseSeverity.SEV_C)
    
    def get_cases_for_engineer(self, engineer_id: str) -> List[Case]:
        """Get all cases assigned to an engineer."""
        # Get the engineer first (uses its own connection)
        engineer = self.get_engineer(engineer_id)
        if not engineer:
            return []
        
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.id, c.title, c.description, c.status, c.priority,
                       c.created_on, c.modified_on, c.owner_id, c.customer_id
                FROM cases c
                WHERE c.owner_id = ?
                ORDER BY c.created_on DESC
            """, (engineer_id,))
            
            # Fetch all rows first to avoid connection busy issues
            rows = cursor.fetchall()
        finally:
            conn.close()
        
        cases = []
        for row in rows:
            # Get customer (uses its own connection)
            customer = self.get_customer(row.customer_id)
            if not customer:
                customer = Customer(id=row.customer_id, company="Unknown")
            
            # Get timeline entries (uses its own connection)
            timeline = self.get_timeline_entries(row.id)
            
            cases.append(Case(
                id=row.id,
                title=row.title,
                description=row.description or "",
                status=self._map_status(row.status),
                severity=self._map_severity(row.priority or "medium"),
                created_on=row.created_on,
                modified_on=row.modified_on or row.created_on,
                owner=engineer,
                customer=customer,
                timeline=timeline
            ))
        
        return cases
    
    def get_all_active_cases(self) -> List[Case]:
        """Get all active cases (not resolved/cancelled)."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.id, c.title, c.description, c.status, c.priority,
                       c.created_on, c.modified_on, c.owner_id, c.customer_id
                FROM cases c
                WHERE c.status NOT IN ('resolved', 'cancelled')
                ORDER BY c.created_on DESC
            """)
            
            # Fetch all rows first to avoid connection busy issues
            rows = cursor.fetchall()
        finally:
            conn.close()
        
        cases = []
        for row in rows:
            # Get engineer (uses its own connection)
            engineer = self.get_engineer(row.owner_id)
            if not engineer:
                engineer = Engineer(id=row.owner_id, name="Unknown", email="unknown@contoso.com")
            
            # Get customer (uses its own connection)
            customer = self.get_customer(row.customer_id)
            if not customer:
                customer = Customer(id=row.customer_id, company="Unknown")
            
            # Get timeline entries (uses its own connection)
            timeline = self.get_timeline_entries(row.id)
            
            cases.append(Case(
                id=row.id,
                title=row.title,
                description=row.description or "",
                status=self._map_status(row.status),
                severity=self._map_severity(row.priority or "medium"),
                created_on=row.created_on,
                modified_on=row.modified_on or row.created_on,
                owner=engineer,
                customer=customer,
                timeline=timeline
            ))
        
        return cases
    
    def test_connection(self) -> bool:
        """Test if database connection works."""
        try:
            conn = self.connect()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True
            finally:
                conn.close()
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
