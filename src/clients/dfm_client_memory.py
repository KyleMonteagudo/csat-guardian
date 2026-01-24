# =============================================================================
# CSAT Guardian - In-Memory Mock DfM Client
# =============================================================================
# A simple mock client that uses in-memory data from sample_data_rich.py.
# This is useful for local testing when you don't want to set up SQLite.
#
# Usage in api.py startup:
#     from clients.dfm_client_memory import InMemoryDfMClient
#     app_state.dfm_client = InMemoryDfMClient()
# =============================================================================

from typing import List, Optional

from models import Case, Engineer
from sample_data_rich import (
    get_case_by_id,
    get_cases_by_owner,
    get_engineer_by_id,
    get_all_cases,
    get_sample_engineers,
)
from logger import get_logger

logger = get_logger(__name__)


class InMemoryDfMClient:
    """
    In-memory mock DfM client using sample_data_rich.py.
    
    This client provides case data directly from memory without
    requiring SQLite or any database. Useful for quick local testing.
    """
    
    def __init__(self):
        """Initialize the in-memory client."""
        logger.info("Initializing InMemoryDfMClient")
        logger.info("  → Using rich sample data from sample_data_rich.py")
        logger.info("  → 8 test cases with detailed timelines loaded")
    
    async def get_case(self, case_id: str) -> Optional[Case]:
        """Get a case by ID."""
        logger.debug(f"InMemoryDfMClient.get_case: {case_id}")
        return get_case_by_id(case_id)
    
    async def get_active_cases(self) -> List[Case]:
        """Get all active cases."""
        logger.debug("InMemoryDfMClient.get_active_cases")
        all_cases = get_all_cases()
        # Filter to active cases only
        from models import CaseStatus
        return [c for c in all_cases if c.status == CaseStatus.ACTIVE]
    
    async def get_cases_by_owner(self, owner_id: str) -> List[Case]:
        """Get all cases for an engineer."""
        logger.debug(f"InMemoryDfMClient.get_cases_by_owner: {owner_id}")
        return get_cases_by_owner(owner_id)
    
    async def get_engineer(self, engineer_id: str) -> Optional[Engineer]:
        """Get an engineer by ID."""
        logger.debug(f"InMemoryDfMClient.get_engineer: {engineer_id}")
        return get_engineer_by_id(engineer_id)
    
    async def get_engineers(self) -> List[Engineer]:
        """Get all engineers."""
        logger.debug("InMemoryDfMClient.get_engineers")
        return get_sample_engineers()
    
    async def close(self) -> None:
        """Close connections (no-op for in-memory client)."""
        pass


# =============================================================================
# Factory function
# =============================================================================

_client_instance: Optional[InMemoryDfMClient] = None


def get_in_memory_dfm_client() -> InMemoryDfMClient:
    """Get or create the in-memory DfM client singleton."""
    global _client_instance
    if _client_instance is None:
        _client_instance = InMemoryDfMClient()
    return _client_instance


def reset_in_memory_client() -> None:
    """Reset the client singleton."""
    global _client_instance
    _client_instance = None
