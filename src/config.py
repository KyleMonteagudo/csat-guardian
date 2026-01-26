# =============================================================================
# CSAT Guardian - Configuration Module
# =============================================================================
# This module handles all application configuration, loading settings from
# environment variables, Azure Key Vault, and providing typed access.
#
# Key Features:
# - Type-safe configuration with Pydantic validation
# - Environment variable loading with python-dotenv
# - Azure Key Vault integration for secrets (production)
# - Default values for development/POC mode
# - Feature flags for gradual rollout
#
# Secret Loading Priority:
# 1. Environment variables (for local dev with .env.local)
# 2. Azure Key Vault (for production, using Managed Identity)
# =============================================================================

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathlib import Path

# -----------------------------------------------------------------------------
# Load environment variables from .env file
# -----------------------------------------------------------------------------
# This must happen before we read any os.environ values
# Try .env.local first (gitignored), then .env
# Use absolute path to handle running from different directories
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env.local")
load_dotenv(_project_root / ".env")


# -----------------------------------------------------------------------------
# Azure Commercial Cloud Configuration
# -----------------------------------------------------------------------------

AZURE_AUTHORITY = "https://login.microsoftonline.com"
AZURE_KEYVAULT_SUFFIX = "vault.azure.net"
AZURE_SQL_SUFFIX = "database.windows.net"
AZURE_OPENAI_SUFFIX = "openai.azure.com"
AZURE_GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
AZURE_CONTAINER_REGISTRY_SUFFIX = "azurecr.io"
AZURE_WEBAPP_SUFFIX = "azurewebsites.net"


# -----------------------------------------------------------------------------
# Azure Key Vault Helper
# -----------------------------------------------------------------------------

def get_secret_from_keyvault(secret_name: str, default: str = "") -> str:
    """
    Retrieve a secret from Azure Key Vault.
    
    This function uses DefaultAzureCredential which supports:
    - Managed Identity (in Azure)
    - Azure CLI credentials (local dev)
    - Environment credentials (CI/CD)
    
    Automatically detects Azure Government vs Commercial cloud based on
    the AZURE_CLOUD environment variable.
    
    Args:
        secret_name: Name of the secret in Key Vault (e.g., "AzureOpenAI--ApiKey")
        default: Default value if secret not found or Key Vault not configured
        
    Returns:
        str: The secret value, or default if not found
    """
    # Check if Key Vault URL is configured
    vault_url = os.getenv("AZURE_KEY_VAULT_URL")
    
    if not vault_url:
        # Key Vault not configured, return default
        return default
    
    try:
        # Import Azure SDK (only when needed)
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
        
        # Get the authority host (auto-detect from AZURE_CLOUD or use override)
        authority_host = os.getenv("AZURE_AUTHORITY_HOST", AZURE_AUTHORITY)
        
        # Create credential with appropriate authority
        credential = DefaultAzureCredential(
            authority=authority_host
        )
        client = SecretClient(vault_url=vault_url, credential=credential)
        
        # Retrieve the secret
        secret = client.get_secret(secret_name)
        return secret.value or default
        
    except ImportError:
        # Azure SDK not installed (e.g., in minimal test environment)
        print(f"Warning: azure-identity not installed, cannot access Key Vault")
        return default
    except Exception as e:
        # Log error but don't crash - fall back to default
        print(f"Warning: Could not retrieve secret '{secret_name}' from Key Vault: {e}")
        return default


def get_config_value(
    env_var_name: str,
    keyvault_secret_name: Optional[str] = None,
    default: str = ""
) -> str:
    """
    Get a configuration value with fallback chain.
    
    Priority:
    1. Environment variable (for local dev)
    2. Azure Key Vault (for production secrets)
    3. Default value
    
    Args:
        env_var_name: Name of the environment variable
        keyvault_secret_name: Name of the secret in Key Vault (optional)
        default: Default value if neither source has the value
        
    Returns:
        str: The configuration value
    """
    # First, check environment variable
    value = os.getenv(env_var_name)
    
    if value:
        return value
    
    # If no env var and Key Vault secret name provided, try Key Vault
    if keyvault_secret_name:
        value = get_secret_from_keyvault(keyvault_secret_name, "")
        if value:
            return value
    
    # Fall back to default
    return default


class AzureOpenAIConfig(BaseModel):
    """
    Configuration settings for Azure OpenAI service.
    
    These settings control how we connect to Azure OpenAI for:
    - Sentiment analysis of case content
    - Generating troubleshooting recommendations
    - Summarizing case details for engineer briefings
    
    Attributes:
        endpoint: The Azure OpenAI resource endpoint URL
        api_key: The API key for authentication (only used if use_managed_identity=False)
        deployment: The model deployment name (e.g., 'gpt-4o')
        api_version: The Azure OpenAI API version to use
        use_managed_identity: Use Managed Identity (MSI) for authentication instead of API key
    """
    endpoint: str = Field(
        default="",
        description="Azure OpenAI endpoint URL"
    )
    api_key: str = Field(
        default="",
        description="Azure OpenAI API key (only used if use_managed_identity=False)"
    )
    deployment: str = Field(
        default="gpt-4o",
        description="Model deployment name"
    )
    api_version: str = Field(
        default="2024-02-15-preview",
        description="Azure OpenAI API version"
    )
    use_managed_identity: bool = Field(
        default=True,
        description="Use Managed Identity for Azure OpenAI authentication (recommended for production)"
    )


class DatabaseConfig(BaseModel):
    """
    Configuration settings for database connectivity.
    
    Supports two modes:
    1. SQLite (local/POC): Uses path to local .db file
    2. Azure SQL (production): Uses connection_string from Key Vault
    
    The connection_string takes precedence over path if provided.
    
    Attributes:
        path: Path to SQLite database file (for local dev)
        connection_string: Full SQL connection string (for Azure SQL)
        echo: Whether to log all SQL statements (for debugging)
    """
    path: str = Field(
        default="data/csat_guardian.db",
        description="Path to SQLite database file (local mode)"
    )
    connection_string: Optional[str] = Field(
        default=None,
        description="SQL connection string (Azure SQL mode)"
    )
    echo: bool = Field(
        default=False,
        description="Log all SQL statements"
    )
    
    @property
    def effective_connection_string(self) -> str:
        """
        Get the effective database connection string.
        
        Returns Azure SQL connection string if provided,
        otherwise returns SQLite connection string.
        """
        if self.connection_string:
            return self.connection_string
        return f"sqlite+aiosqlite:///{self.path}"


class DfMConfig(BaseModel):
    """
    Configuration settings for DfM (Dynamics for Microsoft) integration.
    
    NOTE: These settings are placeholders for the POC.
    When we receive API access approval, we'll populate these values
    and switch USE_MOCK_DFM to false.
    
    Attributes:
        base_url: The Dynamics 365 instance URL
        tenant_id: Azure AD tenant ID for authentication
        client_id: Registered application client ID
        client_secret: Application secret (use Key Vault in production)
    """
    base_url: Optional[str] = Field(
        default=None,
        description="DfM/Dynamics 365 instance URL"
    )
    tenant_id: Optional[str] = Field(
        default=None,
        description="Azure AD tenant ID"
    )
    client_id: Optional[str] = Field(
        default=None,
        description="Application client ID"
    )
    client_secret: Optional[str] = Field(
        default=None,
        description="Application client secret"
    )


class TeamsConfig(BaseModel):
    """
    Configuration settings for Microsoft Teams integration.
    
    NOTE: These settings are placeholders for the POC.
    When we receive Teams bot approval, we'll populate these values
    and switch USE_MOCK_TEAMS to false.
    
    Attributes:
        graph_base_url: Microsoft Graph API base URL
        bot_app_id: Bot Framework application ID
        bot_app_password: Bot Framework application password
    """
    graph_base_url: str = Field(
        default="https://graph.microsoft.com/v1.0",
        description="Microsoft Graph API base URL"
    )
    bot_app_id: Optional[str] = Field(
        default=None,
        description="Teams Bot application ID"
    )
    bot_app_password: Optional[str] = Field(
        default=None,
        description="Teams Bot application password"
    )


class AlertThresholds(BaseModel):
    """
    Configuration for alert triggering thresholds.
    
    These values control when CSAT Guardian generates alerts:
    - Sentiment scores below threshold trigger negative sentiment alerts
    - Cases without updates trigger communication gap alerts
    - Cases approaching/exceeding 7 days trigger compliance alerts
    
    Attributes:
        negative_sentiment_threshold: Score below which sentiment is "negative" (0.0-1.0)
        no_response_alert_hours: Hours without engineer response before alert
        case_update_warning_days: Days without notes before warning (compliance)
        case_update_breach_days: Days without notes before breach alert
        scan_interval_minutes: How often to scan for updates
    """
    negative_sentiment_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Sentiment score threshold for negative alerts"
    )
    no_response_alert_hours: int = Field(
        default=24,
        ge=1,
        description="Hours without response before alert"
    )
    case_update_warning_days: int = Field(
        default=5,
        ge=1,
        description="Days without update before warning"
    )
    case_update_breach_days: int = Field(
        default=7,
        ge=1,
        description="Days without update before breach alert"
    )
    scan_interval_minutes: int = Field(
        default=15,
        ge=1,
        description="Minutes between case scans"
    )


class FeatureFlags(BaseModel):
    """
    Feature flags for controlling application behavior.
    
    These flags allow us to:
    - Use mock services during POC development
    - Gradually enable features as they're approved
    - Toggle features for testing and debugging
    
    Attributes:
        use_mock_dfm: Use mock DfM data instead of real API
        use_mock_teams: Use mock Teams notifications (console output)
        verbose_logging: Enable detailed debug logging
        enable_sentiment_analysis: Enable AI sentiment analysis
        enable_compliance_tracking: Enable 7-day compliance tracking
        use_sql_managed_identity: Use Managed Identity for Azure SQL authentication
    """
    use_mock_dfm: bool = Field(
        default=True,
        description="Use mock DfM data (POC mode)"
    )
    use_mock_teams: bool = Field(
        default=True,
        description="Use mock Teams notifications (POC mode)"
    )
    verbose_logging: bool = Field(
        default=True,
        description="Enable verbose debug logging"
    )
    enable_sentiment_analysis: bool = Field(
        default=True,
        description="Enable sentiment analysis feature"
    )
    enable_compliance_tracking: bool = Field(
        default=True,
        description="Enable 7-day compliance tracking"
    )
    use_sql_managed_identity: bool = Field(
        default=True,
        description="Use Managed Identity for Azure SQL authentication (recommended for production)"
    )


class AppConfig(BaseModel):
    """
    Main application configuration container.
    
    This class aggregates all configuration sections and provides
    a single point of access for all application settings.
    
    Usage:
        config = AppConfig.from_environment()
        print(config.azure_openai.endpoint)
        print(config.thresholds.negative_sentiment_threshold)
    
    Attributes:
        azure_openai: Azure OpenAI service configuration
        database: Database connection configuration
        dfm: DfM/Dynamics 365 configuration (placeholder for POC)
        teams: Microsoft Teams configuration (placeholder for POC)
        thresholds: Alert triggering thresholds
        features: Feature flags for toggling functionality
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    azure_openai: AzureOpenAIConfig = Field(
        default_factory=AzureOpenAIConfig
    )
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig
    )
    dfm: DfMConfig = Field(
        default_factory=DfMConfig
    )
    teams: TeamsConfig = Field(
        default_factory=TeamsConfig
    )
    thresholds: AlertThresholds = Field(
        default_factory=AlertThresholds
    )
    features: FeatureFlags = Field(
        default_factory=FeatureFlags
    )
    log_level: str = Field(
        default="DEBUG",
        description="Logging level"
    )
    
    @classmethod
    def from_environment(cls) -> "AppConfig":
        """
        Create an AppConfig instance from environment variables and Key Vault.
        
        This method reads configuration from:
        1. Environment variables (local development)
        2. Azure Key Vault (production secrets)
        
        Secrets (API keys, connection strings) are loaded from Key Vault
        in production, with environment variables as fallback for local dev.
        
        Returns:
            AppConfig: Fully populated configuration object
            
        Example:
            # In your main.py or startup code:
            config = AppConfig.from_environment()
            
            # Access configuration values:
            if config.features.use_mock_dfm:
                print("Running in POC mode with mock data")
        """
        return cls(
            # -------------------------
            # Azure OpenAI Configuration
            # Secrets loaded from Key Vault in production
            # -------------------------
            azure_openai=AzureOpenAIConfig(
                endpoint=get_config_value(
                    "AZURE_OPENAI_ENDPOINT",
                    "AzureOpenAI--Endpoint",
                    ""
                ),
                api_key=get_config_value(
                    "AZURE_OPENAI_API_KEY",
                    "AzureOpenAI--ApiKey",
                    ""
                ),
                deployment=get_config_value(
                    "AZURE_OPENAI_DEPLOYMENT",
                    None,
                    "gpt-4o"
                ),
                api_version=get_config_value(
                    "AZURE_OPENAI_API_VERSION",
                    None,
                    "2024-02-15-preview"
                ),
                use_managed_identity=os.getenv(
                    "USE_OPENAI_MANAGED_IDENTITY", "true"
                ).lower() == "true",
            ),
            # -------------------------
            # Database Configuration
            # Connection string from Key Vault in production
            # -------------------------
            database=DatabaseConfig(
                path=os.getenv("DATABASE_PATH", "data/csat_guardian.db"),
                connection_string=get_config_value(
                    "DATABASE_CONNECTION_STRING",
                    "SqlServer--ConnectionString",
                    None
                ),
                echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            ),
            # -------------------------
            # DfM Configuration (Placeholder for POC)
            # Will use Key Vault for secrets when real API is available
            # -------------------------
            dfm=DfMConfig(
                base_url=os.getenv("DFM_BASE_URL"),
                tenant_id=os.getenv("DFM_TENANT_ID"),
                client_id=os.getenv("DFM_CLIENT_ID"),
                client_secret=os.getenv("DFM_CLIENT_SECRET"),
            ),
            # -------------------------
            # Teams Configuration (Placeholder for POC)
            # -------------------------
            teams=TeamsConfig(
                graph_base_url=os.getenv("GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0"),
                bot_app_id=os.getenv("TEAMS_BOT_APP_ID"),
                bot_app_password=os.getenv("TEAMS_BOT_APP_PASSWORD"),
            ),
            # -------------------------
            # Alert Thresholds
            # -------------------------
            thresholds=AlertThresholds(
                negative_sentiment_threshold=float(
                    os.getenv("NEGATIVE_SENTIMENT_THRESHOLD", "0.3")
                ),
                no_response_alert_hours=int(
                    os.getenv("NO_RESPONSE_ALERT_HOURS", "24")
                ),
                case_update_warning_days=int(
                    os.getenv("CASE_UPDATE_WARNING_DAYS", "5")
                ),
                case_update_breach_days=int(
                    os.getenv("CASE_UPDATE_BREACH_DAYS", "7")
                ),
                scan_interval_minutes=int(
                    os.getenv("SCAN_INTERVAL_MINUTES", "15")
                ),
            ),
            # -------------------------
            # Feature Flags
            # -------------------------
            features=FeatureFlags(
                use_mock_dfm=os.getenv("USE_MOCK_DFM", "true").lower() == "true",
                use_mock_teams=os.getenv("USE_MOCK_TEAMS", "true").lower() == "true",
                verbose_logging=os.getenv("VERBOSE_LOGGING", "true").lower() == "true",
                enable_sentiment_analysis=os.getenv(
                    "ENABLE_SENTIMENT_ANALYSIS", "true"
                ).lower() == "true",
                enable_compliance_tracking=os.getenv(
                    "ENABLE_COMPLIANCE_TRACKING", "true"
                ).lower() == "true",
                use_sql_managed_identity=os.getenv(
                    "USE_SQL_MANAGED_IDENTITY", "true"
                ).lower() == "true",
            ),
            # -------------------------
            # Logging
            # -------------------------
            log_level=os.getenv("LOG_LEVEL", "DEBUG"),
        )
    
    def validate_for_production(self) -> list[str]:
        """
        Validate that all required production settings are configured.
        
        This method checks that essential configuration values are set
        and returns a list of any missing or invalid settings. Use this
        before deploying to production to ensure all integrations will work.
        
        Returns:
            list[str]: List of validation errors (empty if all valid)
            
        Example:
            config = AppConfig.from_environment()
            errors = config.validate_for_production()
            if errors:
                for error in errors:
                    print(f"Configuration error: {error}")
                sys.exit(1)
        """
        errors = []
        
        # Check Azure OpenAI (required for sentiment analysis)
        if self.features.enable_sentiment_analysis:
            if not self.azure_openai.endpoint:
                errors.append("AZURE_OPENAI_ENDPOINT is required for sentiment analysis")
            # API key only required if not using Managed Identity
            if not self.azure_openai.use_managed_identity and not self.azure_openai.api_key:
                errors.append("AZURE_OPENAI_API_KEY is required when not using Managed Identity")
        
        # Check DfM (required if not using mock)
        if not self.features.use_mock_dfm:
            if not self.dfm.base_url:
                errors.append("DFM_BASE_URL is required when USE_MOCK_DFM is false")
            if not self.dfm.tenant_id:
                errors.append("DFM_TENANT_ID is required when USE_MOCK_DFM is false")
            if not self.dfm.client_id:
                errors.append("DFM_CLIENT_ID is required when USE_MOCK_DFM is false")
        
        # Check Teams (required if not using mock)
        if not self.features.use_mock_teams:
            if not self.teams.bot_app_id:
                errors.append("TEAMS_BOT_APP_ID is required when USE_MOCK_TEAMS is false")
            if not self.teams.bot_app_password:
                errors.append("TEAMS_BOT_APP_PASSWORD is required when USE_MOCK_TEAMS is false")
        
        return errors


# -----------------------------------------------------------------------------
# Module-level singleton for easy access
# -----------------------------------------------------------------------------
# This allows other modules to import the configuration directly:
# from config import config
# print(config.azure_openai.endpoint)

_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get the application configuration singleton.
    
    This function provides a single, shared configuration instance
    across the entire application. The configuration is loaded once
    on first access and cached for subsequent calls.
    
    Returns:
        AppConfig: The shared configuration instance
        
    Example:
        from config import get_config
        
        config = get_config()
        if config.features.verbose_logging:
            print("Verbose logging is enabled")
    """
    global _config
    if _config is None:
        _config = AppConfig.from_environment()
    return _config


def reload_config() -> AppConfig:
    """
    Reload the configuration from environment variables.
    
    This function forces a reload of all configuration values,
    useful for testing or when environment variables have changed.
    
    Returns:
        AppConfig: The newly loaded configuration instance
        
    Example:
        # After changing environment variables:
        from config import reload_config
        
        config = reload_config()
        print(f"New log level: {config.log_level}")
    """
    global _config
    _config = AppConfig.from_environment()
    return _config
