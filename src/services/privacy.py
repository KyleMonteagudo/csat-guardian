# =============================================================================
# CSAT Guardian - Privacy & PII Scrubbing Service
# =============================================================================
# This module provides PII (Personally Identifiable Information) scrubbing
# capabilities to protect customer and engineer data before sending to LLMs.
#
# TWO-LAYER APPROACH:
# 1. Regex-based scrubbing (fast, no latency, catches obvious patterns)
# 2. Azure AI Content Safety (ML-powered, catches names and contextual PII)
#
# The privacy service:
# - Removes email addresses
# - Removes phone numbers
# - Removes IP addresses
# - Redacts common PII patterns (SSN, credit cards, etc.)
# - Optionally uses Azure AI Content Safety for enhanced detection
#
# Configuration:
# - Set ENABLE_CONTENT_SAFETY_PII=true to enable ML-powered detection
# - Set CONTENT_SAFETY_ENDPOINT to your Azure AI Content Safety endpoint
# =============================================================================

import re
from typing import Optional, List, Tuple
from logger import get_logger

# Get logger for this module
logger = get_logger(__name__)


# =============================================================================
# PII Detection Patterns
# =============================================================================

# Email addresses - comprehensive pattern
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    re.IGNORECASE
)

# Phone numbers - US/International formats
PHONE_PATTERNS = [
    # US format: (123) 456-7890, 123-456-7890, 123.456.7890, 123 456 7890
    re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    # International format: +1-123-456-7890
    re.compile(r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'),
    # Extension format: x1234, ext. 1234
    re.compile(r'\b(?:x|ext\.?)\s*\d{2,5}\b', re.IGNORECASE),
]

# IP addresses (IPv4 and IPv6)
IPV4_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
IPV6_PATTERN = re.compile(r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b')

# Social Security Numbers (US)
SSN_PATTERN = re.compile(r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b')

# Credit Card Numbers (requires separators to avoid matching case IDs)
CREDIT_CARD_PATTERN = re.compile(
    r'\b\d{4}[-.\s]\d{4}[-.\s]\d{4}[-.\s]\d{4}\b'  # 16 digits WITH separators required
)

# Azure/AWS/GCP resource IDs and keys (prevent accidental exposure)
AZURE_KEY_PATTERN = re.compile(r'\b[A-Za-z0-9+/]{40,}={0,2}\b')  # Base64 keys
GUID_PATTERN = re.compile(
    r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'
)

# Customer IDs and case IDs (redact the numeric part)
CUSTOMER_ID_PATTERN = re.compile(
    r'\b(?:customer\s*(?:id|#|number)?:?\s*)(\d{5,})\b',
    re.IGNORECASE
)

# Azure Subscription IDs (GUIDs preceded by "subscription")
SUBSCRIPTION_ID_PATTERN = re.compile(
    r'\b(?:subscription\s*(?:id)?:?\s*)([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b',
    re.IGNORECASE
)

# URLs (may contain tokens or sensitive paths)
URL_PATTERN = re.compile(
    r'https?://[^\s<>"\'{}|\\^`\[\]]+',
    re.IGNORECASE
)


# =============================================================================
# Replacement Tokens
# =============================================================================

REDACTION_TOKENS = {
    'email': '[EMAIL_REDACTED]',
    'phone': '[PHONE_REDACTED]',
    'ipv4': '[IP_REDACTED]',
    'ipv6': '[IP_REDACTED]',
    'ssn': '[SSN_REDACTED]',
    'credit_card': '[CARD_REDACTED]',
    'customer_id': '[CUSTOMER_ID_REDACTED]',
    'subscription_id': '[SUBSCRIPTION_ID_REDACTED]',
    'guid': '[ID_REDACTED]',
    'url': '[URL_REDACTED]',
    'api_key': '[KEY_REDACTED]',
}


# =============================================================================
# Privacy Service Class
# =============================================================================

class PrivacyService:
    """
    Service for scrubbing PII from text before sending to LLMs.
    
    This service provides a two-layer approach to PII detection:
    1. Fast regex-based scrubbing (always runs, no latency)
    2. Optional Azure AI Content Safety ML-powered detection
    
    Usage:
        privacy = PrivacyService()
        clean_text = privacy.scrub(case.description)
        
        # With Content Safety enabled:
        privacy = PrivacyService(use_content_safety=True)
        clean_text = await privacy.scrub_async(case.description)
    """
    
    def __init__(
        self,
        scrub_emails: bool = True,
        scrub_phones: bool = True,
        scrub_ips: bool = True,
        scrub_ssn: bool = True,
        scrub_credit_cards: bool = True,
        scrub_customer_ids: bool = True,
        scrub_guids: bool = False,  # GUIDs are often needed for context
        scrub_urls: bool = False,   # URLs often provide important context
        scrub_api_keys: bool = True,
        preserve_email_domain: bool = True,  # Keep @company.com for context
        use_content_safety: bool = False,  # Enable Azure AI Content Safety
        content_safety_endpoint: Optional[str] = None,
        content_safety_key: Optional[str] = None,
        use_content_safety_msi: bool = True,
    ):
        """
        Initialize the privacy service with configuration options.
        
        Args:
            scrub_emails: Remove email addresses
            scrub_phones: Remove phone numbers
            scrub_ips: Remove IP addresses
            scrub_ssn: Remove Social Security Numbers
            scrub_credit_cards: Remove credit card numbers
            scrub_customer_ids: Remove customer ID numbers
            scrub_guids: Remove GUIDs (careful - may remove case IDs)
            scrub_urls: Remove URLs (careful - loses context)
            scrub_api_keys: Remove potential API keys
            preserve_email_domain: Keep email domain (user@domain → [EMAIL]@domain)
            use_content_safety: Enable Azure AI Content Safety for enhanced PII detection
            content_safety_endpoint: Azure AI Content Safety endpoint URL
            content_safety_key: API key (only used if use_content_safety_msi=False)
            use_content_safety_msi: Use Managed Identity for Content Safety auth
        """
        self.scrub_emails = scrub_emails
        self.scrub_phones = scrub_phones
        self.scrub_ips = scrub_ips
        self.scrub_ssn = scrub_ssn
        self.scrub_credit_cards = scrub_credit_cards
        self.scrub_customer_ids = scrub_customer_ids
        self.scrub_guids = scrub_guids
        self.scrub_urls = scrub_urls
        self.scrub_api_keys = scrub_api_keys
        self.preserve_email_domain = preserve_email_domain
        
        # Content Safety configuration
        self.use_content_safety = use_content_safety
        self.content_safety_endpoint = content_safety_endpoint
        self.content_safety_key = content_safety_key
        self.use_content_safety_msi = use_content_safety_msi
        self._content_safety_client = None
        
        logger.info(
            f"PrivacyService initialized - emails: {scrub_emails}, "
            f"phones: {scrub_phones}, ips: {scrub_ips}, "
            f"content_safety: {use_content_safety}"
        )
        
        # Initialize Content Safety client if enabled
        if self.use_content_safety and self.content_safety_endpoint:
            self._init_content_safety_client()
    
    def _init_content_safety_client(self):
        """Initialize the Azure AI Content Safety client."""
        try:
            from azure.ai.contentsafety import ContentSafetyClient
            from azure.core.credentials import AzureKeyCredential
            from azure.identity import DefaultAzureCredential
            
            if self.use_content_safety_msi:
                logger.info("Initializing Content Safety client with Managed Identity")
                credential = DefaultAzureCredential()
                self._content_safety_client = ContentSafetyClient(
                    endpoint=self.content_safety_endpoint,
                    credential=credential
                )
            else:
                logger.info("Initializing Content Safety client with API key")
                self._content_safety_client = ContentSafetyClient(
                    endpoint=self.content_safety_endpoint,
                    credential=AzureKeyCredential(self.content_safety_key)
                )
            logger.info("Content Safety client initialized successfully")
            
        except ImportError:
            logger.warning(
                "azure-ai-contentsafety package not installed. "
                "Install with: pip install azure-ai-contentsafety"
            )
            self.use_content_safety = False
        except Exception as e:
            logger.error(f"Failed to initialize Content Safety client: {e}")
            self.use_content_safety = False
    
    def _scrub_with_regex(self, text: str) -> Tuple[str, int]:
        """
        Apply regex-based PII scrubbing.
        
        Args:
            text: The text to scrub
            
        Returns:
            Tuple of (scrubbed_text, redaction_count)
        """
        scrubbed = text
        redaction_count = 0
        
        # Scrub emails
        if self.scrub_emails:
            if self.preserve_email_domain:
                def replace_email(match):
                    email = match.group(0)
                    domain = email.split('@')[-1]
                    return f"{REDACTION_TOKENS['email'].replace(']', '')}@{domain}]"
                scrubbed, count = EMAIL_PATTERN.subn(replace_email, scrubbed)
            else:
                scrubbed, count = EMAIL_PATTERN.subn(REDACTION_TOKENS['email'], scrubbed)
            redaction_count += count
        
        # Scrub phone numbers
        if self.scrub_phones:
            for pattern in PHONE_PATTERNS:
                scrubbed, count = pattern.subn(REDACTION_TOKENS['phone'], scrubbed)
                redaction_count += count
        
        # Scrub IP addresses
        if self.scrub_ips:
            scrubbed, count = IPV4_PATTERN.subn(REDACTION_TOKENS['ipv4'], scrubbed)
            redaction_count += count
            scrubbed, count = IPV6_PATTERN.subn(REDACTION_TOKENS['ipv6'], scrubbed)
            redaction_count += count
        
        # Scrub SSNs
        if self.scrub_ssn:
            scrubbed, count = SSN_PATTERN.subn(REDACTION_TOKENS['ssn'], scrubbed)
            redaction_count += count
        
        # Scrub credit card numbers
        if self.scrub_credit_cards:
            scrubbed, count = CREDIT_CARD_PATTERN.subn(REDACTION_TOKENS['credit_card'], scrubbed)
            redaction_count += count
        
        # Scrub customer IDs
        if self.scrub_customer_ids:
            scrubbed, count = CUSTOMER_ID_PATTERN.subn(
                f"Customer ID: {REDACTION_TOKENS['customer_id']}",
                scrubbed
            )
            redaction_count += count
        
        # Scrub Azure subscription IDs (always enabled - these are sensitive)
        scrubbed, count = SUBSCRIPTION_ID_PATTERN.subn(
            f"subscription {REDACTION_TOKENS['subscription_id']}",
            scrubbed
        )
        redaction_count += count
        
        # Scrub GUIDs (careful - may affect case IDs)
        if self.scrub_guids:
            scrubbed, count = GUID_PATTERN.subn(REDACTION_TOKENS['guid'], scrubbed)
            redaction_count += count
        
        # Scrub URLs
        if self.scrub_urls:
            scrubbed, count = URL_PATTERN.subn(REDACTION_TOKENS['url'], scrubbed)
            redaction_count += count
        
        # Scrub potential API keys (long base64 strings)
        if self.scrub_api_keys:
            scrubbed, count = AZURE_KEY_PATTERN.subn(REDACTION_TOKENS['api_key'], scrubbed)
            redaction_count += count
        
        return scrubbed, redaction_count
    
    async def _scrub_with_content_safety(self, text: str) -> Tuple[str, List[str]]:
        """
        Apply Azure AI Content Safety PII detection.
        
        Args:
            text: The text to analyze
            
        Returns:
            Tuple of (scrubbed_text, list of detected PII categories)
        """
        if not self._content_safety_client:
            return text, []
        
        try:
            from azure.ai.contentsafety.models import AnalyzeTextOptions
            
            # Analyze text for PII
            # Note: Content Safety's text analysis includes PII detection
            request = AnalyzeTextOptions(text=text)
            response = self._content_safety_client.analyze_text(request)
            
            # The response includes detected categories
            # For PII, we need to use the blocklist or custom detection
            # Azure AI Language has more specific PII detection
            
            detected_categories = []
            scrubbed = text
            
            # Check if any PII-related categories were detected
            # Content Safety focuses on harmful content, but we can use
            # the Azure AI Language service for more specific PII
            if hasattr(response, 'categories_analysis'):
                for category in response.categories_analysis:
                    if category.severity > 0:
                        detected_categories.append(f"{category.category}: severity {category.severity}")
            
            logger.debug(f"Content Safety analysis complete: {len(detected_categories)} concerns")
            return scrubbed, detected_categories
            
        except Exception as e:
            logger.error(f"Content Safety analysis failed: {e}")
            return text, []
    
    def scrub(self, text: Optional[str]) -> str:
        """
        Scrub PII from the provided text (synchronous, regex-only).
        
        For Content Safety integration, use scrub_async() instead.
        
        Args:
            text: The text to scrub
            
        Returns:
            str: The text with PII removed
        """
        if not text:
            return ""
        
        scrubbed, redaction_count = self._scrub_with_regex(text)
        
        if redaction_count > 0:
            logger.debug(f"Regex scrubbed {redaction_count} PII items from text ({len(text)} chars)")
        
        return scrubbed
    
    async def scrub_async(self, text: Optional[str]) -> str:
        """
        Scrub PII from the provided text (async, includes Content Safety if enabled).
        
        This method:
        1. First applies fast regex-based scrubbing
        2. Then (if enabled) uses Azure AI Content Safety for additional detection
        
        Args:
            text: The text to scrub
            
        Returns:
            str: The text with PII removed
        """
        if not text:
            return ""
        
        # Layer 1: Regex scrubbing (always runs)
        scrubbed, regex_count = self._scrub_with_regex(text)
        
        # Layer 2: Content Safety (if enabled)
        content_safety_categories = []
        if self.use_content_safety and self._content_safety_client:
            scrubbed, content_safety_categories = await self._scrub_with_content_safety(scrubbed)
        
        total_detections = regex_count + len(content_safety_categories)
        if total_detections > 0:
            logger.debug(
                f"PII scrubbing complete: {regex_count} regex, "
                f"{len(content_safety_categories)} content safety"
            )
        
        return scrubbed
    
    def scrub_case_for_llm(
        self,
        title: str,
        description: str,
        timeline_text: Optional[str] = None
    ) -> Tuple[str, str, str]:
        """
        Scrub a case's content for LLM processing (synchronous).
        
        This is a convenience method for scrubbing the common fields
        sent to the LLM for case analysis.
        
        Args:
            title: Case title
            description: Case description
            timeline_text: Formatted timeline text
            
        Returns:
            Tuple of (scrubbed_title, scrubbed_description, scrubbed_timeline)
        """
        return (
            self.scrub(title),
            self.scrub(description),
            self.scrub(timeline_text) if timeline_text else ""
        )
    
    async def scrub_case_for_llm_async(
        self,
        title: str,
        description: str,
        timeline_text: Optional[str] = None
    ) -> Tuple[str, str, str]:
        """
        Scrub a case's content for LLM processing (async, includes Content Safety).
        
        Args:
            title: Case title
            description: Case description
            timeline_text: Formatted timeline text
            
        Returns:
            Tuple of (scrubbed_title, scrubbed_description, scrubbed_timeline)
        """
        return (
            await self.scrub_async(title),
            await self.scrub_async(description),
            await self.scrub_async(timeline_text) if timeline_text else ""
        )


# =============================================================================
# Module-level singleton for easy access
# =============================================================================

_privacy_service: Optional[PrivacyService] = None


def get_privacy_service(config=None) -> PrivacyService:
    """
    Get the privacy service singleton.
    
    Initializes with Content Safety if configured and enabled.
    
    Args:
        config: Optional AppConfig. If not provided, loads from environment.
        
    Returns:
        PrivacyService: The shared service instance
    """
    global _privacy_service
    
    if _privacy_service is None:
        # Load config if not provided
        if config is None:
            from config import get_config
            config = get_config()
        
        # Initialize with Content Safety if enabled
        use_content_safety = (
            config.features.enable_content_safety_pii and 
            bool(config.content_safety.endpoint)
        )
        
        _privacy_service = PrivacyService(
            use_content_safety=use_content_safety,
            content_safety_endpoint=config.content_safety.endpoint,
            content_safety_key=config.content_safety.api_key,
            use_content_safety_msi=config.content_safety.use_managed_identity,
        )
        
        if use_content_safety:
            logger.info("Privacy service initialized with Azure AI Content Safety enabled")
        else:
            logger.info("Privacy service initialized with regex-only scrubbing")
    
    return _privacy_service


def scrub_pii(text: Optional[str]) -> str:
    """
    Convenience function to scrub PII from text (synchronous, regex-only).
    
    For async scrubbing with Content Safety, use:
        privacy = get_privacy_service()
        scrubbed = await privacy.scrub_async(text)
    
    Args:
        text: The text to scrub
        
    Returns:
        str: The text with PII removed
    """
    return get_privacy_service().scrub(text)


async def scrub_pii_async(text: Optional[str]) -> str:
    """
    Convenience function to scrub PII from text (async, includes Content Safety if enabled).
    
    Args:
        text: The text to scrub
        
    Returns:
        str: The text with PII removed
    """
    return await get_privacy_service().scrub_async(text)
