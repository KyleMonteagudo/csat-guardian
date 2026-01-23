# =============================================================================
# CSAT Guardian - Services Module
# =============================================================================
# This package contains the core business logic services.
#
# Available services:
# - sentiment_service: Analyzes customer sentiment using Azure OpenAI
# - alert_service: Generates and sends alerts to engineers
#
# These services are the heart of CSAT Guardian's functionality.
# =============================================================================

from services.sentiment_service import (
    SentimentAnalysisService,
    get_sentiment_service,
    reset_sentiment_service,
)

from services.alert_service import (
    AlertService,
    get_alert_service,
    reset_alert_service,
)

__all__ = [
    # Sentiment Service
    "SentimentAnalysisService",
    "get_sentiment_service",
    "reset_sentiment_service",
    # Alert Service
    "AlertService",
    "get_alert_service",
    "reset_alert_service",
]
