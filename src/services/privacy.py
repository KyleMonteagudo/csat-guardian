# =============================================================================
# CSAT Guardian - Privacy & PII Scrubbing Service
# =============================================================================
# This module provides PII (Personally Identifiable Information) scrubbing
# capabilities to protect customer and engineer data before sending to LLMs.
#
# The privacy service:
# - Removes email addresses
# - Removes phone numbers
# - Removes IP addresses
# - Redacts common PII patterns (SSN, credit cards, etc.)
# - Optionally redacts names using pattern matching
#
# IMPORTANT: This is a best-effort scrubbing layer. It catches common patterns
# but may not catch all PII variations. For maximum security, consider using
# Azure AI Content Safety or a dedicated PII detection service.
# =============================================================================

import re
from typing import Optional
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

# Credit Card Numbers (basic patterns)
CREDIT_CARD_PATTERN = re.compile(
    r'\b(?:\d{4}[-.\s]?){3}\d{4}\b'  # 16 digits with optional separators
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
    
    This service provides a configurable way to remove sensitive information
    from case data, communications, and other text that will be processed
    by Azure OpenAI or other LLM services.
    
    Usage:
        privacy = PrivacyService()
        clean_text = privacy.scrub(case.description)
        
        # Or with specific options:
        privacy = PrivacyService(
            scrub_emails=True,
            scrub_phones=True,
            scrub_urls=False,  # Keep URLs for context
            preserve_domain=True  # Keep email domains: john@contoso.com → [EMAIL]@contoso.com
        )
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
        
        logger.info(
            f"PrivacyService initialized - emails: {scrub_emails}, "
            f"phones: {scrub_phones}, ips: {scrub_ips}"
        )
    
    def scrub(self, text: Optional[str]) -> str:
        """
        Scrub PII from the provided text.
        
        Args:
            text: The text to scrub
            
        Returns:
            str: The text with PII removed
        """
        if not text:
            return ""
        
        scrubbed = text
        redaction_count = 0
        
        # Scrub emails
        if self.scrub_emails:
            if self.preserve_email_domain:
                # Keep domain: john.doe@contoso.com → [EMAIL]@contoso.com
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
        
        if redaction_count > 0:
            logger.debug(f"Scrubbed {redaction_count} PII items from text ({len(text)} chars)")
        
        return scrubbed
    
    def scrub_case_for_llm(
        self,
        title: str,
        description: str,
        timeline_text: Optional[str] = None
    ) -> tuple[str, str, str]:
        """
        Scrub a case's content for LLM processing.
        
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


# =============================================================================
# Module-level singleton for easy access
# =============================================================================

_privacy_service: Optional[PrivacyService] = None


def get_privacy_service() -> PrivacyService:
    """
    Get the privacy service singleton.
    
    Returns:
        PrivacyService: The shared service instance
    """
    global _privacy_service
    
    if _privacy_service is None:
        _privacy_service = PrivacyService()
    
    return _privacy_service


def scrub_pii(text: Optional[str]) -> str:
    """
    Convenience function to scrub PII from text.
    
    Args:
        text: The text to scrub
        
    Returns:
        str: The text with PII removed
    """
    return get_privacy_service().scrub(text)
