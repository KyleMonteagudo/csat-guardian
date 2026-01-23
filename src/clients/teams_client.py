# =============================================================================
# CSAT Guardian - Teams Notification Client
# =============================================================================
# This module defines the interface for Microsoft Teams notifications.
#
# The design uses dependency injection to allow swapping between:
# - MockTeamsClient: Outputs notifications to console/logs (POC)
# - RealTeamsClient: Sends actual Teams messages via Graph API (Production)
#
# Both implementations conform to the same interface (TeamsClientBase),
# making it easy to switch between them based on configuration.
#
# Usage:
#     from clients.teams_client import get_teams_client
#     
#     client = get_teams_client(config)
#     await client.send_alert(alert)
# =============================================================================

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from config import AppConfig, get_config
from models import Alert, Engineer, AlertUrgency, ConversationMessage
from logger import get_logger, log_notification

# Get logger for this module
logger = get_logger(__name__)


class TeamsClientBase(ABC):
    """
    Abstract base class for Teams client implementations.
    
    This defines the interface that both Mock and Real implementations
    must follow. By programming against this interface, we can easily
    swap between implementations based on configuration.
    
    Methods:
        send_alert: Send an alert notification to an engineer
        send_message: Send a conversational message to an engineer
        format_alert_card: Format an alert as an Adaptive Card
    """
    
    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send an alert notification to an engineer.
        
        Args:
            alert: The alert to send
            
        Returns:
            bool: True if the alert was sent successfully
        """
        pass
    
    @abstractmethod
    async def send_message(
        self,
        recipient: Engineer,
        message: str,
        case_id: Optional[str] = None,
    ) -> bool:
        """
        Send a conversational message to an engineer.
        
        Args:
            recipient: The engineer to message
            message: The message text
            case_id: Optional related case ID
            
        Returns:
            bool: True if the message was sent successfully
        """
        pass
    
    def format_alert_card(self, alert: Alert) -> dict:
        """
        Format an alert as a Microsoft Adaptive Card.
        
        Adaptive Cards are a platform-agnostic way to render
        rich content in Teams messages.
        
        Args:
            alert: The alert to format
            
        Returns:
            dict: The Adaptive Card JSON structure
        """
        # Choose emoji based on urgency
        urgency_emoji = {
            AlertUrgency.HIGH: "🚨",
            AlertUrgency.MEDIUM: "⚠️",
            AlertUrgency.LOW: "ℹ️",
        }
        emoji = urgency_emoji.get(alert.urgency, "📢")
        
        # Build the Adaptive Card
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"{emoji} {alert.title}",
                    "weight": "Bolder",
                    "size": "Large",
                    "wrap": True,
                },
                {
                    "type": "TextBlock",
                    "text": f"Case: {alert.case_id}",
                    "isSubtle": True,
                    "spacing": "None",
                },
                {
                    "type": "TextBlock",
                    "text": alert.message,
                    "wrap": True,
                    "spacing": "Medium",
                },
            ],
            "actions": [],
        }
        
        # Add recommendations if present
        if alert.recommendations:
            recommendations_text = "\n".join(
                f"• {rec}" for rec in alert.recommendations
            )
            card["body"].append({
                "type": "TextBlock",
                "text": "💡 **Suggested Actions:**",
                "weight": "Bolder",
                "spacing": "Medium",
            })
            card["body"].append({
                "type": "TextBlock",
                "text": recommendations_text,
                "wrap": True,
                "spacing": "Small",
            })
        
        # Add action button to view case (placeholder URL)
        card["actions"].append({
            "type": "Action.OpenUrl",
            "title": "View Case in DfM",
            "url": f"https://dynamics.microsoft.com/case/{alert.case_id}",
        })
        
        # Add reply action for conversational interaction
        card["actions"].append({
            "type": "Action.Submit",
            "title": "Ask CSAT Guardian",
            "data": {
                "action": "start_conversation",
                "case_id": alert.case_id,
            },
        })
        
        return card


class MockTeamsClient(TeamsClientBase):
    """
    Mock Teams client that outputs to console/logs.
    
    This implementation is used during POC development when we don't
    have access to the real Teams Bot API. It provides the same interface
    as the real client, allowing the rest of the application to work
    without modification.
    
    Notifications are printed to the console and logged for review.
    """
    
    def __init__(self):
        """Initialize the mock Teams client."""
        logger.info("Initializing MockTeamsClient (POC mode)")
        logger.info("  → Notifications will be output to console")
        logger.info("  → Real Teams integration will be added when access is approved")
    
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send an alert notification (outputs to console).
        
        Args:
            alert: The alert to send
            
        Returns:
            bool: Always returns True in mock mode
        """
        start_time = time.time()
        
        # Log that we're sending an alert
        logger.info(f"MockTeamsClient.send_alert: Sending alert to {alert.recipient.name}")
        
        # Print a formatted alert to console
        print("\n" + "=" * 70)
        print("📬 MOCK TEAMS NOTIFICATION")
        print("=" * 70)
        print(f"To: {alert.recipient.name} ({alert.recipient.email})")
        print(f"Type: {alert.type.value}")
        print(f"Urgency: {alert.urgency.value.upper()}")
        print(f"Case: {alert.case_id}")
        print("-" * 70)
        print(f"📌 {alert.title}")
        print("-" * 70)
        print(alert.message)
        
        if alert.recommendations:
            print("\n💡 Suggested Actions:")
            for i, rec in enumerate(alert.recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("=" * 70)
        print(f"[Sent at {datetime.utcnow().isoformat()}Z]")
        print("=" * 70 + "\n")
        
        # Log the notification
        log_notification(
            logger,
            alert.type.value,
            alert.recipient.email,
            alert.case_id,
            True,
            channel="mock_console",
            duration_ms=(time.time() - start_time) * 1000,
        )
        
        return True
    
    async def send_message(
        self,
        recipient: Engineer,
        message: str,
        case_id: Optional[str] = None,
    ) -> bool:
        """
        Send a conversational message (outputs to console).
        
        Args:
            recipient: The engineer to message
            message: The message text
            case_id: Optional related case ID
            
        Returns:
            bool: Always returns True in mock mode
        """
        start_time = time.time()
        
        logger.info(f"MockTeamsClient.send_message: Sending message to {recipient.name}")
        
        # Print a formatted message to console
        print("\n" + "-" * 70)
        print("💬 MOCK TEAMS MESSAGE")
        print("-" * 70)
        print(f"To: {recipient.name}")
        if case_id:
            print(f"Case: {case_id}")
        print("-" * 70)
        print(f"🤖 CSAT Guardian: {message}")
        print("-" * 70 + "\n")
        
        logger.debug(
            f"Message sent to {recipient.email}",
            extra={
                "recipient": recipient.email,
                "case_id": case_id,
                "duration_ms": (time.time() - start_time) * 1000,
            }
        )
        
        return True


class RealTeamsClient(TeamsClientBase):
    """
    Real Teams client that sends messages via Microsoft Graph API.
    
    TODO: Implement when Teams Bot access is approved.
    
    This class will:
    - Authenticate using Bot Framework credentials
    - Create 1:1 chats with engineers
    - Send Adaptive Cards as messages
    - Receive and process engineer replies
    
    Graph API endpoints required:
    - POST /v1.0/chats (create chat)
    - POST /v1.0/chats/{id}/messages (send message)
    - GET /v1.0/chats/{id}/messages (read replies)
    - GET /v1.0/users/{id} (resolve user details)
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the real Teams client.
        
        Args:
            config: Application configuration with Teams credentials
        """
        logger.info("Initializing RealTeamsClient")
        logger.warning("  → Real Teams API access is not yet implemented")
        logger.warning("  → Waiting for Bot registration approval")
        self.config = config
        
        # TODO: Initialize Bot Framework client
        # TODO: Initialize Microsoft Graph client
    
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send an alert notification via Teams.
        
        TODO: Implement when Teams Bot access is approved.
        """
        raise NotImplementedError(
            "Real Teams API access is not yet implemented. "
            "Set USE_MOCK_TEAMS=true to use mock notifications."
        )
    
    async def send_message(
        self,
        recipient: Engineer,
        message: str,
        case_id: Optional[str] = None,
    ) -> bool:
        """
        Send a conversational message via Teams.
        
        TODO: Implement when Teams Bot access is approved.
        """
        raise NotImplementedError(
            "Real Teams API access is not yet implemented. "
            "Set USE_MOCK_TEAMS=true to use mock notifications."
        )


# =============================================================================
# Factory Function
# =============================================================================

_teams_client: Optional[TeamsClientBase] = None


def get_teams_client(config: Optional[AppConfig] = None) -> TeamsClientBase:
    """
    Get the appropriate Teams client based on configuration.
    
    This factory function returns either the Mock or Real client
    depending on the USE_MOCK_TEAMS configuration flag.
    
    Args:
        config: Application configuration (uses global config if not provided)
        
    Returns:
        TeamsClientBase: The configured Teams client
        
    Example:
        client = get_teams_client()
        await client.send_alert(alert)
    """
    global _teams_client
    
    # Use cached client if available
    if _teams_client is not None:
        return _teams_client
    
    # Get configuration
    if config is None:
        config = get_config()
    
    # Choose client based on configuration
    if config.features.use_mock_teams:
        logger.info("Creating MockTeamsClient (USE_MOCK_TEAMS=true)")
        _teams_client = MockTeamsClient()
    else:
        logger.info("Creating RealTeamsClient (USE_MOCK_TEAMS=false)")
        _teams_client = RealTeamsClient(config)
    
    return _teams_client


def reset_teams_client() -> None:
    """
    Reset the Teams client singleton.
    
    This is useful for testing or when configuration changes.
    """
    global _teams_client
    _teams_client = None
    logger.debug("Teams client singleton reset")
