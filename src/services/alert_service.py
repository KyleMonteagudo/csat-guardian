# =============================================================================
# CSAT Guardian - Alert Service
# =============================================================================
# This module handles alert generation, deduplication, and delivery.
#
# The alert service:
# - Creates alerts based on case analysis results
# - Prevents duplicate alerts using time-based deduplication
# - Formats alerts for display
# - Delivers alerts via the Teams client (mock or real)
# - Records alert history in the database
# =============================================================================

import uuid
import time
from datetime import datetime
from typing import Optional

from config import AppConfig, get_config
from database import DatabaseManager
from models import (
    Alert, AlertType, AlertUrgency, Case, CaseAnalysis, Engineer
)
from clients.teams_client import TeamsClientBase, get_teams_client
from logger import get_logger, log_notification, log_case_event

# Get logger for this module
logger = get_logger(__name__)


# =============================================================================
# Alert Templates
# =============================================================================

ALERT_TEMPLATES = {
    AlertType.CASE_BRIEFING: {
        "title": "📋 New Case Briefing",
        "urgency": AlertUrgency.LOW,
        "message_template": (
            "A new case has been assigned to you.\n\n"
            "**Summary:** {summary}\n\n"
            "**Initial Sentiment:** {sentiment_label}"
        ),
    },
    AlertType.SENTIMENT_ALERT: {
        "title": "🚨 Negative Sentiment Detected",
        "urgency": AlertUrgency.HIGH,
        "message_template": (
            "Customer appears frustrated or unhappy.\n\n"
            "**Key Signals:**\n{key_phrases}\n\n"
            "**Concerns Identified:**\n{concerns}"
        ),
    },
    AlertType.COMMUNICATION_GAP: {
        "title": "⏰ Communication Gap Alert",
        "urgency": AlertUrgency.MEDIUM,
        "message_template": (
            "This case hasn't had a response in a while.\n\n"
            "**Hours Since Last Response:** {hours_since_response}\n\n"
            "Consider reaching out to the customer with an update."
        ),
    },
    AlertType.SEVEN_DAY_WARNING: {
        "title": "⚠️ 7-Day Update Warning",
        "urgency": AlertUrgency.MEDIUM,
        "message_template": (
            "This case is approaching the 7-day update requirement.\n\n"
            "**Days Since Last Note:** {days_since_note:.1f}\n\n"
            "Please add a case note with a status update."
        ),
    },
    AlertType.SEVEN_DAY_BREACH: {
        "title": "🚨 7-Day Update BREACH",
        "urgency": AlertUrgency.HIGH,
        "message_template": (
            "This case has exceeded the 7-day update requirement!\n\n"
            "**Days Since Last Note:** {days_since_note:.1f}\n\n"
            "Immediate action required - please update the case notes now."
        ),
    },
    AlertType.RECOVERY_SUGGESTION: {
        "title": "💡 Recovery Action Suggested",
        "urgency": AlertUrgency.HIGH,
        "message_template": (
            "Customer sentiment is declining on this case.\n\n"
            "**Trend:** {sentiment_trend}\n\n"
            "Consider taking proactive steps to improve the customer experience."
        ),
    },
}


class AlertService:
    """
    Service for generating and sending alerts to engineers.
    
    This service:
    - Creates alerts based on case analysis
    - Deduplicates alerts to prevent notification fatigue
    - Formats alert content with case-specific details
    - Delivers alerts via Teams (mock or real)
    - Records alert history for auditing
    
    Usage:
        service = AlertService(db, teams_client, config)
        await service.process_analysis(case_analysis)
    """
    
    def __init__(
        self,
        db: DatabaseManager,
        teams_client: Optional[TeamsClientBase] = None,
        config: Optional[AppConfig] = None,
    ):
        """
        Initialize the alert service.
        
        Args:
            db: Database manager for alert history
            teams_client: Teams client for sending notifications
            config: Application configuration
        """
        logger.info("Initializing AlertService")
        
        self.db = db
        self.teams_client = teams_client or get_teams_client()
        self.config = config or get_config()
        
        # Deduplication window (hours) - don't send same alert type twice in this window
        self.dedup_window_hours = 24
        
        logger.debug(f"  → Deduplication window: {self.dedup_window_hours} hours")
    
    async def process_analysis(self, analysis: CaseAnalysis) -> list[Alert]:
        """
        Process a case analysis and send any triggered alerts.
        
        This method:
        1. Checks which alerts were triggered by the analysis
        2. Deduplicates against recently sent alerts
        3. Creates and formats new alerts
        4. Sends alerts via Teams
        5. Records alerts in the database
        
        Args:
            analysis: The case analysis result
            
        Returns:
            list[Alert]: The alerts that were sent
        """
        case = analysis.case
        log_case_event(
            logger, case.id, 
            f"Processing analysis, {len(analysis.alerts_triggered)} alerts triggered"
        )
        
        sent_alerts = []
        
        # Process each triggered alert type
        for alert_type in analysis.alerts_triggered:
            logger.debug(f"[Case {case.id}] Processing alert type: {alert_type.value}")
            
            # Check for recent duplicate
            if await self._is_duplicate(case.id, alert_type):
                logger.info(
                    f"[Case {case.id}] Skipping {alert_type.value} - "
                    f"already sent within {self.dedup_window_hours} hours"
                )
                continue
            
            # Create the alert
            alert = self._create_alert(alert_type, analysis)
            
            # Send the alert
            success = await self._send_alert(alert)
            
            if success:
                # Record in database
                await self._record_alert(alert)
                sent_alerts.append(alert)
                
                log_notification(
                    logger,
                    alert_type.value,
                    case.owner.email,
                    case.id,
                    True,
                )
            else:
                log_notification(
                    logger,
                    alert_type.value,
                    case.owner.email,
                    case.id,
                    False,
                    error="Failed to send",
                )
        
        log_case_event(
            logger, case.id,
            f"Alert processing complete, {len(sent_alerts)} alerts sent"
        )
        
        return sent_alerts
    
    async def _is_duplicate(self, case_id: str, alert_type: AlertType) -> bool:
        """
        Check if this alert type was recently sent for this case.
        
        Args:
            case_id: The case identifier
            alert_type: The type of alert to check
            
        Returns:
            bool: True if a duplicate exists in the dedup window
        """
        recent_alerts = await self.db.get_recent_alerts(
            case_id,
            alert_type.value,
            hours=self.dedup_window_hours,
        )
        
        return len(recent_alerts) > 0
    
    def _create_alert(self, alert_type: AlertType, analysis: CaseAnalysis) -> Alert:
        """
        Create an alert from a template and analysis data.
        
        Args:
            alert_type: The type of alert to create
            analysis: The case analysis with context data
            
        Returns:
            Alert: The formatted alert
        """
        # Get the template
        template = ALERT_TEMPLATES.get(alert_type, {
            "title": f"Alert: {alert_type.value}",
            "urgency": AlertUrgency.MEDIUM,
            "message_template": "Please review this case.",
        })
        
        # Build format data
        format_data = {
            "summary": analysis.summary,
            "sentiment_label": analysis.overall_sentiment.label.value,
            "sentiment_score": f"{analysis.overall_sentiment.score:.2f}",
            "sentiment_trend": analysis.sentiment_trend,
            "days_since_note": analysis.days_since_last_note,
            "hours_since_response": analysis.days_since_last_note * 24,
            "key_phrases": "\n".join(
                f"• \"{phrase}\"" 
                for phrase in analysis.overall_sentiment.key_phrases[:3]
            ) or "• No specific phrases identified",
            "concerns": "\n".join(
                f"• {concern}"
                for concern in analysis.overall_sentiment.concerns[:3]
            ) or "• No specific concerns identified",
        }
        
        # Format the message
        try:
            message = template["message_template"].format(**format_data)
        except KeyError as e:
            logger.warning(f"Missing format key in alert template: {e}")
            message = template["message_template"]
        
        # Create the alert
        alert = Alert(
            id=str(uuid.uuid4()),
            type=alert_type,
            urgency=template["urgency"],
            case_id=analysis.case.id,
            recipient=analysis.case.owner,
            title=template["title"],
            message=message,
            recommendations=analysis.recommendations[:3],  # Top 3 recommendations
        )
        
        logger.debug(f"Created alert: {alert.type.value} for case {alert.case_id}")
        
        return alert
    
    async def _send_alert(self, alert: Alert) -> bool:
        """
        Send an alert via the Teams client.
        
        Args:
            alert: The alert to send
            
        Returns:
            bool: True if the alert was sent successfully
        """
        start_time = time.time()
        
        try:
            logger.info(
                f"Sending {alert.type.value} alert to {alert.recipient.name} "
                f"for case {alert.case_id}"
            )
            
            # Send via Teams client
            success = await self.teams_client.send_alert(alert)
            
            # Update sent timestamp
            if success:
                alert.sent_at = datetime.utcnow()
            
            logger.debug(
                f"Alert send {'succeeded' if success else 'failed'} "
                f"({(time.time() - start_time) * 1000:.1f}ms)"
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}", exc_info=True)
            return False
    
    async def _record_alert(self, alert: Alert) -> None:
        """
        Record an alert in the database for history/auditing.
        
        Args:
            alert: The alert to record
        """
        try:
            await self.db.create_alert(
                alert_id=alert.id,
                alert_type=alert.type.value,
                urgency=alert.urgency.value,
                case_id=alert.case_id,
                recipient_id=alert.recipient.id,
                title=alert.title,
                message=alert.message,
            )
            
            if alert.sent_at:
                await self.db.mark_alert_sent(alert.id)
            
            logger.debug(f"Alert recorded in database: {alert.id}")
            
        except Exception as e:
            logger.error(f"Failed to record alert in database: {e}", exc_info=True)
    
    async def send_case_briefing(
        self,
        case: Case,
        summary: str,
        sentiment_label: str,
    ) -> Optional[Alert]:
        """
        Send a case briefing to an engineer when a case is assigned.
        
        This is a convenience method for sending the initial briefing
        when a new case is assigned or when an engineer requests a summary.
        
        Args:
            case: The case to brief
            summary: AI-generated case summary
            sentiment_label: Initial sentiment assessment
            
        Returns:
            Alert if sent successfully, None otherwise
        """
        # Check for duplicate
        if await self._is_duplicate(case.id, AlertType.CASE_BRIEFING):
            logger.info(f"[Case {case.id}] Case briefing already sent recently")
            return None
        
        # Create a minimal analysis for the alert
        from models import SentimentResult, SentimentLabel
        
        analysis = CaseAnalysis(
            case=case,
            overall_sentiment=SentimentResult.from_score(
                0.5 if sentiment_label == "neutral" else (
                    0.7 if sentiment_label == "positive" else 0.3
                )
            ),
            sentiment_trend="stable",
            compliance_status="compliant",
            days_since_last_note=case.days_since_last_note,
            alerts_triggered=[AlertType.CASE_BRIEFING],
            summary=summary,
            recommendations=["Review the case details", "Reach out to the customer"],
        )
        
        # Create and send the alert
        alert = self._create_alert(AlertType.CASE_BRIEFING, analysis)
        
        if await self._send_alert(alert):
            await self._record_alert(alert)
            return alert
        
        return None


# =============================================================================
# Module-level singleton
# =============================================================================

_alert_service: Optional[AlertService] = None


async def get_alert_service(
    db: Optional[DatabaseManager] = None,
    teams_client: Optional[TeamsClientBase] = None,
    config: Optional[AppConfig] = None,
) -> AlertService:
    """
    Get the alert service singleton.
    
    Args:
        db: Database manager (required on first call)
        teams_client: Teams client (uses default if not provided)
        config: Application configuration (uses default if not provided)
        
    Returns:
        AlertService: The shared service instance
    """
    global _alert_service
    
    if _alert_service is None:
        if db is None:
            raise ValueError("Database manager required on first call to get_alert_service")
        _alert_service = AlertService(db, teams_client, config)
    
    return _alert_service


def reset_alert_service() -> None:
    """Reset the alert service singleton."""
    global _alert_service
    _alert_service = None
    logger.debug("Alert service singleton reset")
