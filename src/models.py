# =============================================================================
# CSAT Guardian - Data Models
# =============================================================================
# This module defines the data models used throughout the application.
# These models represent:
# - Cases from DfM (or mock data)
# - Timeline entries (notes, emails, calls)
# - Sentiment analysis results
# - Alerts and notifications
#
# All models use Pydantic for:
# - Type validation
# - Serialization/deserialization
# - Documentation via docstrings
# =============================================================================

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# Enums for Type Safety
# =============================================================================

class CaseStatus(str, Enum):
    """
    Enumeration of possible case statuses in DfM.
    
    These map to the statecode field in Dynamics 365 Incident entity.
    """
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"
    WAITING_ON_CUSTOMER = "waiting_on_customer"
    WAITING_ON_VENDOR = "waiting_on_vendor"


class CaseSeverity(str, Enum):
    """
    Enumeration of case severity levels.
    
    These map to the severitycode field in Dynamics 365 Incident entity.
    """
    SEV_A = "sev_a"      # Critical - Production down
    SEV_B = "sev_b"      # High - Major impact
    SEV_C = "sev_c"      # Medium - Moderate impact
    SEV_D = "sev_d"      # Low - Minimal impact


class SentimentLabel(str, Enum):
    """
    Enumeration of sentiment analysis results.
    
    These labels are assigned based on the sentiment score:
    - POSITIVE: Score > 0.6
    - NEUTRAL: Score 0.4 - 0.6
    - NEGATIVE: Score < 0.4
    """
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class TimelineEntryType(str, Enum):
    """
    Enumeration of timeline entry types.
    
    These represent the different types of activities that can
    appear in a case timeline.
    """
    NOTE = "note"
    EMAIL = "email"
    EMAIL_SENT = "email_sent"
    EMAIL_RECEIVED = "email_received"
    PHONE_CALL = "phone_call"
    TASK = "task"
    APPOINTMENT = "appointment"


class AlertType(str, Enum):
    """
    Enumeration of alert types that CSAT Guardian can generate.
    
    Each alert type has different urgency and content.
    """
    CASE_BRIEFING = "case_briefing"
    SENTIMENT_ALERT = "sentiment_alert"
    COMMUNICATION_GAP = "communication_gap"
    SEVEN_DAY_WARNING = "7day_warning"
    SEVEN_DAY_BREACH = "7day_breach"
    RECOVERY_SUGGESTION = "recovery_suggestion"


class AlertUrgency(str, Enum):
    """
    Enumeration of alert urgency levels.
    
    Urgency affects how the notification is displayed to the engineer.
    """
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# Data Models
# =============================================================================

class Engineer(BaseModel):
    """
    Model representing a support engineer.
    
    This contains the information needed to route notifications
    and personalize agent interactions.
    
    Attributes:
        id: Unique identifier (from DfM/Azure AD)
        name: Full display name
        email: Email address (for Teams routing and backup notifications)
        teams_id: Microsoft Teams user ID (for direct messages)
    """
    id: str = Field(
        description="Unique engineer identifier"
    )
    name: str = Field(
        description="Engineer's full name"
    )
    email: str = Field(
        description="Engineer's email address"
    )
    teams_id: Optional[str] = Field(
        default=None,
        description="Microsoft Teams user ID"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "eng-001",
                "name": "John Smith",
                "email": "jsmith@microsoft.com",
                "teams_id": "12345-abcde-67890"
            }
        }


class Customer(BaseModel):
    """
    Model representing a customer.
    
    NOTE: We intentionally store minimal customer information.
    We do NOT store PII like names, addresses, or phone numbers.
    This model exists only for case association, not identification.
    
    Attributes:
        id: Unique customer identifier (anonymized reference)
        company: Company name (if applicable)
        tier: Support tier (Premier, Unified, Pro, etc.)
    """
    id: str = Field(
        description="Anonymized customer identifier"
    )
    company: Optional[str] = Field(
        default=None,
        description="Customer's company name"
    )
    tier: Optional[str] = Field(
        default="Standard",
        description="Customer support tier (Premier, Unified, Pro, Standard)"
    )


class TimelineEntry(BaseModel):
    """
    Model representing a single entry in the case timeline.
    
    Timeline entries include notes, emails, phone call notes, etc.
    These are analyzed for sentiment and communication patterns.
    
    Attributes:
        id: Unique activity identifier from DfM
        case_id: The parent case ID
        entry_type: The type of activity (note, email, phone_call, etc.)
        subject: Subject line or title
        content: The text content to analyze
        created_on: When this entry was created
        created_by: Who created this entry (engineer or customer)
        direction: For emails - inbound (from customer) or outbound (to customer)
        is_customer_communication: True if this is from/to the customer
    """
    id: str = Field(
        description="Unique activity identifier"
    )
    case_id: Optional[str] = Field(
        default=None,
        description="Parent case identifier"
    )
    entry_type: TimelineEntryType = Field(
        description="Type of timeline entry"
    )
    subject: Optional[str] = Field(
        default=None,
        description="Subject line or title"
    )
    content: str = Field(
        description="Text content of the entry"
    )
    created_on: datetime = Field(
        description="When this entry was created"
    )
    created_by: str = Field(
        description="Creator's name or identifier"
    )
    direction: Optional[str] = Field(
        default=None,
        description="For emails: 'inbound' or 'outbound'"
    )
    is_customer_communication: bool = Field(
        default=False,
        description="True if this involves customer interaction"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "note-001",
                "case_id": "case-12345678",
                "entry_type": "email",
                "subject": "RE: Issue with shared mailbox",
                "content": "I've been waiting for 3 days with no update. This is unacceptable.",
                "created_on": "2026-01-20T14:30:00Z",
                "created_by": "customer",
                "direction": "inbound",
                "is_customer_communication": True
            }
        }


class Case(BaseModel):
    """
    Model representing a support case from DfM.
    
    This is the primary data structure that CSAT Guardian monitors.
    Cases contain basic metadata and a timeline of activities.
    
    Attributes:
        id: Unique case identifier (incident ID in DfM)
        title: Case title/subject
        description: Initial case description
        status: Current case status
        severity: Case severity level (Sev A/B/C/D)
        created_on: When the case was created
        modified_on: When the case was last modified
        owner: The engineer assigned to this case
        customer: The customer who opened the case
        timeline: List of timeline entries (notes, emails, etc.)
    """
    id: str = Field(
        description="Unique case identifier"
    )
    title: str = Field(
        description="Case title/subject"
    )
    description: str = Field(
        description="Initial case description"
    )
    status: CaseStatus = Field(
        description="Current case status"
    )
    severity: CaseSeverity = Field(
        description="Case severity level (Sev A/B/C/D)"
    )
    created_on: datetime = Field(
        description="Case creation timestamp"
    )
    modified_on: datetime = Field(
        description="Last modification timestamp"
    )
    owner: Engineer = Field(
        description="Assigned engineer"
    )
    customer: Customer = Field(
        description="Customer information"
    )
    timeline: list[TimelineEntry] = Field(
        default_factory=list,
        description="Case timeline entries"
    )
    
    @property
    def days_since_creation(self) -> float:
        """
        Calculate the number of days since case creation.
        
        Returns:
            float: Days elapsed since case was created
        """
        delta = datetime.utcnow() - self.created_on
        return delta.total_seconds() / (24 * 3600)
    
    @property
    def days_since_last_update(self) -> float:
        """
        Calculate the number of days since last case update.
        
        This is used for 7-day compliance tracking.
        
        Returns:
            float: Days elapsed since last update
        """
        delta = datetime.utcnow() - self.modified_on
        return delta.total_seconds() / (24 * 3600)
    
    @property
    def days_since_last_note(self) -> float:
        """
        Calculate days since the last case note was added.
        
        This specifically looks at NOTE type entries for compliance.
        
        Returns:
            float: Days elapsed since last note (or since creation if no notes)
        """
        # Filter to just notes
        notes = [
            e for e in self.timeline 
            if e.entry_type == TimelineEntryType.NOTE
        ]
        
        if not notes:
            # No notes, use case creation date
            return self.days_since_creation
        
        # Find the most recent note
        latest_note = max(notes, key=lambda x: x.created_on)
        delta = datetime.utcnow() - latest_note.created_on
        return delta.total_seconds() / (24 * 3600)
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "case-12345678",
                "title": "Unable to access shared mailbox after migration",
                "description": "After the recent mailbox migration, I can no longer access the shared mailbox 'sales@contoso.com'.",
                "status": "active",
                "severity": "sev_c",
                "created_on": "2026-01-15T09:00:00Z",
                "modified_on": "2026-01-20T14:30:00Z",
                "owner": {
                    "id": "eng-001",
                    "name": "John Smith",
                    "email": "jsmith@microsoft.com"
                },
                "customer": {
                    "id": "cust-001",
                    "company": "Contoso Ltd"
                },
                "timeline": []
            }
        }


class SentimentResult(BaseModel):
    """
    Model representing the result of sentiment analysis.
    
    This is returned by the sentiment analysis service after
    analyzing case content or timeline entries.
    
    Attributes:
        score: Sentiment score from 0.0 (very negative) to 1.0 (very positive)
        label: Categorical label (positive, neutral, negative)
        confidence: Confidence in the analysis (0.0 to 1.0)
        key_phrases: Phrases that indicate the sentiment
        concerns: Specific customer concerns identified
        recommendations: Suggested actions based on sentiment
    """
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Sentiment score (0=negative, 1=positive)"
    )
    label: SentimentLabel = Field(
        description="Categorical sentiment label"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Analysis confidence score"
    )
    key_phrases: list[str] = Field(
        default_factory=list,
        description="Key phrases indicating sentiment"
    )
    concerns: list[str] = Field(
        default_factory=list,
        description="Specific customer concerns identified"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Suggested actions for the engineer"
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the analysis was performed"
    )
    
    @classmethod
    def from_score(cls, score: float, **kwargs) -> "SentimentResult":
        """
        Create a SentimentResult from just a score.
        
        This automatically assigns the label based on the score:
        - score < 0.4: NEGATIVE
        - score 0.4-0.6: NEUTRAL
        - score > 0.6: POSITIVE
        
        Args:
            score: The sentiment score (0.0 to 1.0)
            **kwargs: Additional fields to set
            
        Returns:
            SentimentResult: A fully populated result
        """
        if score < 0.4:
            label = SentimentLabel.NEGATIVE
        elif score > 0.6:
            label = SentimentLabel.POSITIVE
        else:
            label = SentimentLabel.NEUTRAL
        
        return cls(
            score=score,
            label=label,
            confidence=kwargs.get("confidence", 0.8),
            key_phrases=kwargs.get("key_phrases", []),
            concerns=kwargs.get("concerns", []),
            recommendations=kwargs.get("recommendations", []),
        )


class CaseAnalysis(BaseModel):
    """
    Model representing a complete analysis of a case.
    
    This combines case data with sentiment analysis and
    compliance tracking results.
    
    Attributes:
        case: The case being analyzed
        overall_sentiment: Aggregate sentiment across all timeline entries
        sentiment_trend: How sentiment has changed over time ("improving", "declining", "stable")
        compliance_status: Whether the case meets update requirements
        days_since_last_note: Days since last case note
        alerts_triggered: List of alert types that should be sent
        summary: AI-generated case summary
        recommendations: Suggested next actions
    """
    case: Case = Field(
        description="The analyzed case"
    )
    overall_sentiment: SentimentResult = Field(
        description="Aggregate sentiment analysis"
    )
    sentiment_trend: str = Field(
        default="stable",
        description="Sentiment trend: 'improving', 'declining', or 'stable'"
    )
    compliance_status: str = Field(
        default="compliant",
        description="Compliance status: 'compliant', 'warning', or 'breach'"
    )
    days_since_last_note: float = Field(
        description="Days since last case note"
    )
    alerts_triggered: list[AlertType] = Field(
        default_factory=list,
        description="Alerts that should be sent"
    )
    summary: str = Field(
        default="",
        description="AI-generated case summary"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Suggested next actions"
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this analysis was performed"
    )


class Alert(BaseModel):
    """
    Model representing an alert to be sent to an engineer.
    
    Alerts are generated based on case analysis results and
    sent via Teams (or console in POC mode).
    
    Attributes:
        id: Unique alert identifier
        type: The type of alert
        urgency: How urgent this alert is
        case_id: The related case ID
        recipient: The engineer to notify
        title: Alert title/headline
        message: Full alert message
        recommendations: Suggested actions
        created_at: When the alert was created
        sent_at: When the alert was actually sent (None if not yet sent)
        acknowledged: Whether the engineer has seen/acknowledged the alert
    """
    id: str = Field(
        description="Unique alert identifier"
    )
    type: AlertType = Field(
        description="Type of alert"
    )
    urgency: AlertUrgency = Field(
        description="Alert urgency level"
    )
    case_id: str = Field(
        description="Related case ID"
    )
    recipient: Engineer = Field(
        description="Engineer to notify"
    )
    title: str = Field(
        description="Alert title"
    )
    message: str = Field(
        description="Full alert message"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Suggested actions"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When alert was created"
    )
    sent_at: Optional[datetime] = Field(
        default=None,
        description="When alert was sent"
    )
    acknowledged: bool = Field(
        default=False,
        description="Whether engineer acknowledged"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "alert-001",
                "type": "sentiment_alert",
                "urgency": "high",
                "case_id": "case-12345678",
                "recipient": {
                    "id": "eng-001",
                    "name": "John Smith",
                    "email": "jsmith@microsoft.com"
                },
                "title": "🚨 Negative Sentiment Detected",
                "message": "Customer appears frustrated with response timeline.",
                "recommendations": [
                    "Acknowledge the delay and apologize",
                    "Provide a concrete update on progress"
                ],
                "created_at": "2026-01-22T10:00:00Z"
            }
        }


class ConversationMessage(BaseModel):
    """
    Model representing a message in a conversation with the agent.
    
    This tracks the conversation between an engineer and CSAT Guardian
    in Teams (or console in POC mode).
    
    Attributes:
        id: Unique message identifier
        role: Who sent this message ("engineer" or "agent")
        content: The message text
        case_id: The case being discussed (if any)
        timestamp: When the message was sent
    """
    id: str = Field(
        description="Unique message identifier"
    )
    role: str = Field(
        description="Message sender: 'engineer' or 'agent'"
    )
    content: str = Field(
        description="Message content"
    )
    case_id: Optional[str] = Field(
        default=None,
        description="Related case ID if discussing a specific case"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When message was sent"
    )


class ConversationSession(BaseModel):
    """
    Model representing a conversation session with an engineer.
    
    Sessions are temporary and not persisted long-term. They maintain
    context for an ongoing conversation with the agent.
    
    Attributes:
        id: Unique session identifier
        engineer: The engineer in this conversation
        messages: List of messages in the conversation
        active_case_id: The case currently being discussed
        started_at: When the session started
        last_activity: When the last message was sent
    """
    id: str = Field(
        description="Unique session identifier"
    )
    engineer: Engineer = Field(
        description="The engineer in this conversation"
    )
    messages: list[ConversationMessage] = Field(
        default_factory=list,
        description="Conversation messages"
    )
    active_case_id: Optional[str] = Field(
        default=None,
        description="Currently discussed case"
    )
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session start time"
    )
    last_activity: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity time"
    )
    
    def add_message(self, role: str, content: str, case_id: Optional[str] = None) -> ConversationMessage:
        """
        Add a message to the conversation.
        
        Args:
            role: Who is sending ("engineer" or "agent")
            content: The message text
            case_id: Optional case ID being discussed
            
        Returns:
            ConversationMessage: The newly added message
        """
        import uuid
        
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            case_id=case_id or self.active_case_id,
            timestamp=datetime.utcnow()
        )
        
        self.messages.append(message)
        self.last_activity = message.timestamp
        
        # Update active case if mentioned
        if case_id:
            self.active_case_id = case_id
        
        return message
