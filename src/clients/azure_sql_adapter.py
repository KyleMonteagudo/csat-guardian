# =============================================================================
# CSAT Guardian - Azure SQL DfM Client Adapter
# =============================================================================
# This adapter wraps the synchronous db_sync module to provide an async-compatible
# interface for FastAPI. It uses the SyncDatabaseManager which connects to Azure SQL.
#
# This is a temporary solution for the POC while we wait for real DfM API access.
# Once we have DfM access, this will be replaced with the real API client.
# =============================================================================

import asyncio
from typing import Optional, List
from functools import partial

from models import Case, Engineer
from logger import get_logger

logger = get_logger(__name__)


class AzureSQLDfMAdapter:
    """
    Async adapter for the synchronous Azure SQL database.
    
    Wraps SyncDatabaseManager to provide async methods that FastAPI expects.
    Uses run_in_executor to avoid blocking the event loop.
    """
    
    def __init__(self):
        """Initialize the adapter with Azure SQL connection."""
        logger.info("Initializing AzureSQLDfMAdapter")
        self._db = None
        self._initialized = False
    
    def _ensure_db(self):
        """Lazily initialize database connection."""
        if self._db is None:
            from db_sync import SyncDatabaseManager
            self._db = SyncDatabaseManager()
            logger.info("Connected to Azure SQL Database")
        return self._db
    
    async def _run_sync(self, func, *args):
        """Run a synchronous function in a thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args))
    
    async def get_case(self, case_id: str) -> Optional[Case]:
        """Get a single case by ID."""
        db = self._ensure_db()
        # get_cases_for_engineer returns all cases, we need to filter
        # For now, return None - proper implementation would need a get_case method
        cases = await self._run_sync(db.get_all_active_cases)
        for case in cases:
            if case.id == case_id:
                return case
        return None
    
    async def get_active_cases(self) -> List[Case]:
        """Get all active cases."""
        db = self._ensure_db()
        return await self._run_sync(db.get_all_active_cases)
    
    async def get_cases_by_owner(self, owner_id: str) -> List[Case]:
        """Get cases assigned to an engineer."""
        db = self._ensure_db()
        return await self._run_sync(db.get_cases_for_engineer, owner_id)
    
    async def get_engineer(self, engineer_id: str) -> Optional[Engineer]:
        """Get engineer by ID."""
        db = self._ensure_db()
        return await self._run_sync(db.get_engineer, engineer_id)
    
    async def get_engineers(self) -> List[Engineer]:
        """Get all engineers."""
        db = self._ensure_db()
        return await self._run_sync(db.get_engineers)
    
    async def close(self):
        """Close database connection."""
        if self._db:
            self._db.close()
            self._db = None


async def get_azure_sql_adapter() -> AzureSQLDfMAdapter:
    """Factory function to get the Azure SQL adapter."""
    adapter = AzureSQLDfMAdapter()
    # Test connection
    try:
        adapter._ensure_db()
        return adapter
    except Exception as e:
        logger.error(f"Failed to create Azure SQL adapter: {e}")
        raise
