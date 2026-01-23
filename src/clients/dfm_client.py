# =============================================================================
# CSAT Guardian - DfM Client Interface
# =============================================================================
# This module defines the interface for DfM (Dynamics for Microsoft) data access.
#
# The design uses dependency injection to allow swapping between:
# - MockDfMClient: Uses local SQLite database with sample data (POC)
# - RealDfMClient: Calls the actual Dynamics 365 API (Production)
#
# Both implementations conform to the same interface (DfMClientBase),
# making it easy to switch between them based on configuration.
#
# Usage:
#     from clients.dfm_client import get_dfm_client
#     
#     client = get_dfm_client(config)
#     cases = await client.get_active_cases()
# =============================================================================

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from config import AppConfig, get_config
from database import DatabaseManager
from models import (
    Case, Engineer, Customer, TimelineEntry, 
    CaseStatus, CasePriority, TimelineEntryType
)
from logger import get_logger, log_api_call

# Get logger for this module
logger = get_logger(__name__)


class DfMClientBase(ABC):
    """
    Abstract base class for DfM client implementations.
    
    This defines the interface that both Mock and Real implementations
    must follow. By programming against this interface, we can easily
    swap between implementations based on configuration.
    
    Methods:
        get_case: Get a single case by ID
        get_active_cases: Get all active cases
        get_cases_by_owner: Get cases assigned to a specific engineer
        get_engineer: Get engineer details by ID
    """
    
    @abstractmethod
    async def get_case(self, case_id: str) -> Optional[Case]:
        """
        Get a single case by ID.
        
        Args:
            case_id: The unique case identifier
            
        Returns:
            Case if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_active_cases(self) -> list[Case]:
        """
        Get all active cases.
        
        Returns:
            list[Case]: All cases with active status
        """
        pass
    
    @abstractmethod
    async def get_cases_by_owner(self, owner_id: str) -> list[Case]:
        """
        Get all cases assigned to a specific engineer.
        
        Args:
            owner_id: The engineer's unique identifier
            
        Returns:
            list[Case]: Cases assigned to the engineer
        """
        pass
    
    @abstractmethod
    async def get_engineer(self, engineer_id: str) -> Optional[Engineer]:
        """
        Get engineer details by ID.
        
        Args:
            engineer_id: The engineer's unique identifier
            
        Returns:
            Engineer if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_engineers(self) -> list[Engineer]:
        """
        Get all engineers.
        
        Returns:
            list[Engineer]: All available engineers
        """
        pass
    
    async def close(self) -> None:
        """Close any open connections. Override if needed."""
        pass

class MockDfMClient(DfMClientBase):
    """
    Mock DfM client that reads from local SQLite database.
    
    This implementation is used during POC development when we don't
    have access to the real DfM APIs. It provides the same interface
    as the real client, allowing the rest of the application to work
    without modification.
    
    The mock data is populated by running the sample_data.py script.
    
    Attributes:
        db: The database manager instance
    """
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize the mock DfM client.
        
        Args:
            db: The database manager for accessing sample data
        """
        logger.info("Initializing MockDfMClient (POC mode)")
        logger.info("  → Using local SQLite database for case data")
        logger.info("  → Real DfM API calls will be added when access is approved")
        self.db = db
    
    def _convert_db_case_to_model(self, db_case) -> Case:
        """
        Convert a database case object to a Pydantic model.
        
        This helper method transforms the SQLAlchemy ORM object
        into the Pydantic model used by the rest of the application.
        
        Args:
            db_case: The database case object
            
        Returns:
            Case: The Pydantic case model
        """
        # Convert engineer
        engineer = Engineer(
            id=db_case.owner.id,
            name=db_case.owner.name,
            email=db_case.owner.email,
            teams_id=db_case.owner.teams_id,
        )
        
        # Convert customer
        customer = Customer(
            id=db_case.customer.id,
            company=db_case.customer.company,
        )
        
        # Convert timeline entries
        timeline = []
        for entry in db_case.timeline_entries:
            timeline.append(TimelineEntry(
                id=entry.id,
                case_id=entry.case_id,
                entry_type=TimelineEntryType(entry.entry_type),
                subject=entry.subject,
                content=entry.content,
                created_on=entry.created_on,
                created_by=entry.created_by,
                direction=entry.direction,
                is_customer_communication=entry.is_customer_communication,
            ))
        
        # Sort timeline by date
        timeline.sort(key=lambda x: x.created_on)
        
        # Convert status and priority to enums
        status_map = {
            "active": CaseStatus.ACTIVE,
            "resolved": CaseStatus.RESOLVED,
            "cancelled": CaseStatus.CANCELLED,
            "in_progress": CaseStatus.IN_PROGRESS,
            "waiting_on_customer": CaseStatus.WAITING_ON_CUSTOMER,
            "waiting_on_vendor": CaseStatus.WAITING_ON_VENDOR,
        }
        priority_map = {
            "high": CasePriority.HIGH,
            "medium": CasePriority.MEDIUM,
            "low": CasePriority.LOW,
        }
        
        # Create and return the Case model
        return Case(
            id=db_case.id,
            title=db_case.title,
            description=db_case.description,
            status=status_map.get(db_case.status, CaseStatus.ACTIVE),
            priority=priority_map.get(db_case.priority, CasePriority.MEDIUM),
            created_on=db_case.created_on,
            modified_on=db_case.modified_on,
            owner=engineer,
            customer=customer,
            timeline=timeline,
        )
    
    async def get_case(self, case_id: str) -> Optional[Case]:
        """
        Get a single case by ID from the local database.
        
        Args:
            case_id: The unique case identifier
            
        Returns:
            Case if found, None otherwise
        """
        start_time = time.time()
        logger.debug(f"MockDfMClient.get_case: Fetching case {case_id}")
        
        try:
            # Query the database
            db_case = await self.db.get_case(case_id)
            
            if db_case is None:
                # Log the API call (simulated)
                log_api_call(
                    logger, "dfm_mock", "get_case", True,
                    duration_ms=(time.time() - start_time) * 1000,
                    case_id=case_id,
                    result="not_found"
                )
                return None
            
            # Convert to Pydantic model
            case = self._convert_db_case_to_model(db_case)
            
            # Log the successful retrieval
            log_api_call(
                logger, "dfm_mock", "get_case", True,
                duration_ms=(time.time() - start_time) * 1000,
                case_id=case_id,
                result="found"
            )
            
            return case
            
        except Exception as e:
            # Log the error
            log_api_call(
                logger, "dfm_mock", "get_case", False,
                duration_ms=(time.time() - start_time) * 1000,
                case_id=case_id,
                error=str(e)
            )
            logger.error(f"Error fetching case {case_id}: {e}", exc_info=True)
            raise
    
    async def get_active_cases(self) -> list[Case]:
        """
        Get all active cases from the local database.
        
        Returns:
            list[Case]: All cases with active or in_progress status
        """
        start_time = time.time()
        logger.info("MockDfMClient.get_active_cases: Fetching all active cases")
        
        try:
            # Query the database
            db_cases = await self.db.get_active_cases()
            
            # Convert to Pydantic models
            cases = [self._convert_db_case_to_model(c) for c in db_cases]
            
            # Log the successful retrieval
            log_api_call(
                logger, "dfm_mock", "get_active_cases", True,
                duration_ms=(time.time() - start_time) * 1000,
                count=len(cases)
            )
            
            logger.info(f"  → Found {len(cases)} active cases")
            return cases
            
        except Exception as e:
            # Log the error
            log_api_call(
                logger, "dfm_mock", "get_active_cases", False,
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
            logger.error(f"Error fetching active cases: {e}", exc_info=True)
            raise
    
    async def get_cases_by_owner(self, owner_id: str) -> list[Case]:
        """
        Get all cases assigned to a specific engineer.
        
        Args:
            owner_id: The engineer's unique identifier
            
        Returns:
            list[Case]: Cases assigned to the engineer
        """
        start_time = time.time()
        logger.debug(f"MockDfMClient.get_cases_by_owner: Fetching cases for {owner_id}")
        
        try:
            # Query the database
            db_cases = await self.db.get_cases_by_owner(owner_id)
            
            # Convert to Pydantic models
            cases = [self._convert_db_case_to_model(c) for c in db_cases]
            
            # Log the successful retrieval
            log_api_call(
                logger, "dfm_mock", "get_cases_by_owner", True,
                duration_ms=(time.time() - start_time) * 1000,
                owner_id=owner_id,
                count=len(cases)
            )
            
            return cases
            
        except Exception as e:
            # Log the error
            log_api_call(
                logger, "dfm_mock", "get_cases_by_owner", False,
                duration_ms=(time.time() - start_time) * 1000,
                owner_id=owner_id,
                error=str(e)
            )
            logger.error(f"Error fetching cases for owner {owner_id}: {e}", exc_info=True)
            raise
    
    async def get_engineer(self, engineer_id: str) -> Optional[Engineer]:
        """
        Get engineer details by ID.
        
        Args:
            engineer_id: The engineer's unique identifier
            
        Returns:
            Engineer if found, None otherwise
        """
        start_time = time.time()
        logger.debug(f"MockDfMClient.get_engineer: Fetching engineer {engineer_id}")
        
        try:
            # Query the database
            db_engineer = await self.db.get_engineer(engineer_id)
            
            if db_engineer is None:
                log_api_call(
                    logger, "dfm_mock", "get_engineer", True,
                    duration_ms=(time.time() - start_time) * 1000,
                    engineer_id=engineer_id,
                    result="not_found"
                )
                return None
            
            # Convert to Pydantic model
            engineer = Engineer(
                id=db_engineer.id,
                name=db_engineer.name,
                email=db_engineer.email,
                teams_id=db_engineer.teams_id,
            )
            
            log_api_call(
                logger, "dfm_mock", "get_engineer", True,
                duration_ms=(time.time() - start_time) * 1000,
                engineer_id=engineer_id,
                result="found"
            )
            
            return engineer
            
        except Exception as e:
            log_api_call(
                logger, "dfm_mock", "get_engineer", False,
                duration_ms=(time.time() - start_time) * 1000,
                engineer_id=engineer_id,
                error=str(e)
            )
            logger.error(f"Error fetching engineer {engineer_id}: {e}", exc_info=True)
            raise
    
    async def get_engineers(self) -> list[Engineer]:
        """
        Get all engineers.
        
        Returns:
            list[Engineer]: All available engineers
        """
        start_time = time.time()
        logger.debug("MockDfMClient.get_engineers: Fetching all engineers")
        
        try:
            # Query the database
            db_engineers = await self.db.get_all_engineers()
            
            # Convert to Pydantic models
            engineers = [
                Engineer(
                    id=e.id,
                    name=e.name,
                    email=e.email,
                    teams_id=e.teams_id,
                )
                for e in db_engineers
            ]
            
            log_api_call(
                logger, "dfm_mock", "get_engineers", True,
                duration_ms=(time.time() - start_time) * 1000,
                count=len(engineers)
            )
            
            return engineers
            
        except Exception as e:
            log_api_call(
                logger, "dfm_mock", "get_engineers", False,
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
            logger.error(f"Error fetching engineers: {e}", exc_info=True)
            raise
    
    async def close(self) -> None:
        """Close database connection."""
        if self.db:
            await self.db.close()


class RealDfMClient(DfMClientBase):
    """
    Real DfM client that calls the Dynamics 365 API.
    
    TODO: Implement when API access is approved.
    
    This class will:
    - Authenticate using OAuth 2.0 / service principal
    - Call the Dynamics 365 Web API endpoints
    - Transform API responses to Pydantic models
    
    Endpoints required:
    - GET /api/data/v9.2/incidents
    - GET /api/data/v9.2/incidents({id})
    - GET /api/data/v9.2/annotations
    - GET /api/data/v9.2/emails
    - GET /api/data/v9.2/phonecalls
    - GET /api/data/v9.2/activitypointers
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the real DfM client.
        
        Args:
            config: Application configuration with DfM credentials
        """
        logger.info("Initializing RealDfMClient")
        logger.warning("  → Real DfM API access is not yet implemented")
        logger.warning("  → Waiting for API access approval")
        self.config = config
        
        # TODO: Initialize OAuth client for authentication
        # TODO: Initialize HTTP client for API calls
    
    async def get_case(self, case_id: str) -> Optional[Case]:
        """
        Get a single case by ID from the real DfM API.
        
        TODO: Implement when API access is approved.
        """
        raise NotImplementedError(
            "Real DfM API access is not yet implemented. "
            "Set USE_MOCK_DFM=true to use mock data."
        )
    
    async def get_active_cases(self) -> list[Case]:
        """
        Get all active cases from the real DfM API.
        
        TODO: Implement when API access is approved.
        """
        raise NotImplementedError(
            "Real DfM API access is not yet implemented. "
            "Set USE_MOCK_DFM=true to use mock data."
        )
    
    async def get_cases_by_owner(self, owner_id: str) -> list[Case]:
        """
        Get all cases assigned to a specific engineer from the real DfM API.
        
        TODO: Implement when API access is approved.
        """
        raise NotImplementedError(
            "Real DfM API access is not yet implemented. "
            "Set USE_MOCK_DFM=true to use mock data."
        )
    
    async def get_engineer(self, engineer_id: str) -> Optional[Engineer]:
        """
        Get engineer details by ID from the real DfM API.
        
        TODO: Implement when API access is approved.
        """
        raise NotImplementedError(
            "Real DfM API access is not yet implemented. "
            "Set USE_MOCK_DFM=true to use mock data."
        )
    
    async def get_engineers(self) -> list[Engineer]:
        """
        Get all engineers from the real DfM API.
        
        TODO: Implement when API access is approved.
        """
        raise NotImplementedError(
            "Real DfM API access is not yet implemented. "
            "Set USE_MOCK_DFM=true to use mock data."
        )


# =============================================================================
# Factory Function
# =============================================================================

_dfm_client: Optional[DfMClientBase] = None


async def get_dfm_client(
    config: Optional[AppConfig] = None,
    db: Optional[DatabaseManager] = None,
) -> DfMClientBase:
    """
    Get the appropriate DfM client based on configuration.
    
    This factory function returns either the Mock or Real client
    depending on the USE_MOCK_DFM configuration flag.
    
    Args:
        config: Application configuration (uses global config if not provided)
        db: Database manager for mock client (created if not provided)
        
    Returns:
        DfMClientBase: The configured DfM client
        
    Example:
        client = await get_dfm_client()
        cases = await client.get_active_cases()
    """
    global _dfm_client
    
    # Use cached client if available
    if _dfm_client is not None:
        return _dfm_client
    
    # Get configuration
    if config is None:
        config = get_config()
    
    # Choose client based on configuration
    if config.features.use_mock_dfm:
        logger.info("Creating MockDfMClient (USE_MOCK_DFM=true)")
        
        # Initialize database if not provided
        if db is None:
            db = DatabaseManager(config.database.path)
            await db.initialize()
        
        _dfm_client = MockDfMClient(db)
    else:
        logger.info("Creating RealDfMClient (USE_MOCK_DFM=false)")
        _dfm_client = RealDfMClient(config)
    
    return _dfm_client


def reset_dfm_client() -> None:
    """
    Reset the DfM client singleton.
    
    This is useful for testing or when configuration changes.
    """
    global _dfm_client
    _dfm_client = None
    logger.debug("DfM client singleton reset")
