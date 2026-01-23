# =============================================================================
# CSAT Guardian - Clients Module
# =============================================================================
# This package contains client implementations for external services.
#
# Available clients:
# - dfm_client: Interface to DfM (Dynamics for Microsoft) - mock or real
# - teams_client: Interface to Microsoft Teams - mock or real
#
# The clients use a dependency injection pattern:
# - Mock implementations for POC development
# - Real implementations for production (when API access is approved)
# - Configuration flags control which implementation is used
# =============================================================================

from clients.dfm_client import (
    DfMClientBase,
    MockDfMClient,
    RealDfMClient,
    get_dfm_client,
    reset_dfm_client,
)

from clients.teams_client import (
    TeamsClientBase,
    MockTeamsClient,
    RealTeamsClient,
    get_teams_client,
    reset_teams_client,
)

__all__ = [
    # DfM Client
    "DfMClientBase",
    "MockDfMClient",
    "RealDfMClient",
    "get_dfm_client",
    "reset_dfm_client",
    # Teams Client
    "TeamsClientBase",
    "MockTeamsClient",
    "RealTeamsClient",
    "get_teams_client",
    "reset_teams_client",
]
