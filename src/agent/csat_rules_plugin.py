# =============================================================================
# CSAT Guardian - CSAT Rules Plugin
# =============================================================================
# This plugin encodes CSAT business rules and provides timeline analysis
# capabilities for the conversational agent.
#
# Rules encoded:
# - 2-Day Communication Rule: Customers shouldn't go 2+ days without contact
# - 7-Day Notes Rule: Case notes must be updated at least every 7 days  
# - 5-Hour Email-to-Notes Rule: Notes should follow emails within 5 hours
#
# The plugin provides functions that:
# - Check rule compliance for a case
# - Analyze communication patterns
# - Identify CSAT risk factors
# - Provide specific, actionable coaching
# =============================================================================

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from semantic_kernel.functions import kernel_function

from models import Case, TimelineEntry, TimelineEntryType
from logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# CSAT Rules Constants
# =============================================================================

class CSATRuleViolation(Enum):
    """Types of CSAT rule violations."""
    TWO_DAY_COMMUNICATION = "2-day communication rule"
    SEVEN_DAY_NOTES = "7-day notes rule"
    FIVE_HOUR_EMAIL_NOTES = "5-hour email-to-notes rule"


@dataclass
class RuleViolation:
    """A detected rule violation with context."""
    rule: CSATRuleViolation
    severity: str  # "warning" or "breach"
    days_exceeded: float
    last_event_date: Optional[datetime]
    recommendation: str


@dataclass
class CommunicationGap:
    """A detected gap in customer communication."""
    start_date: datetime
    end_date: datetime
    gap_days: float
    customer_messages_during_gap: int


@dataclass
class TimelineAnalysis:
    """Complete timeline analysis results."""
    case_id: str
    days_open: float
    total_communications: int
    customer_communications: int
    engineer_communications: int
    avg_response_time_hours: Optional[float]
    longest_gap_days: float
    rule_violations: List[RuleViolation]
    communication_pattern: str  # "responsive", "sporadic", "delayed"
    risk_level: str  # "low", "medium", "high"
    risk_factors: List[str]


# =============================================================================
# CSAT Rules Plugin
# =============================================================================

class CSATRulesPlugin:
    """
    Semantic Kernel plugin that provides CSAT rule checking and timeline analysis.
    
    This plugin encodes the CSS CSAT business rules:
    - 2-day rule: Customer should hear from engineer at least every 2 days
    - 7-day rule: Case notes must be updated at least every 7 days
    - 5-hour rule: After emailing customer, add notes within 5 hours
    
    The agent can call these functions to:
    - Check compliance for a specific case
    - Get detailed timeline analysis
    - Understand CSAT risk factors
    - Get specific coaching recommendations
    """
    
    def __init__(self, dfm_client, current_engineer_id: str):
        """
        Initialize the CSAT rules plugin.
        
        Args:
            dfm_client: Client for accessing case data
            current_engineer_id: The ID of the current engineer
        """
        self.dfm_client = dfm_client
        self.current_engineer_id = current_engineer_id
        logger.debug(f"CSATRulesPlugin initialized for engineer: {current_engineer_id}")
    
    @kernel_function(
        name="check_csat_rules",
        description="Check a case against all CSAT rules (2-day communication, 7-day notes, 5-hour email-to-notes) and identify any violations"
    )
    async def check_csat_rules(self, case_id: str) -> str:
        """
        Check a case against all CSAT rules.
        
        Args:
            case_id: The case identifier
            
        Returns:
            str: A detailed rule compliance report
        """
        logger.info(f"CSATRulesPlugin.check_csat_rules called for case: {case_id}")
        
        try:
            case = await self.dfm_client.get_case(case_id)
            
            if case is None:
                return f"Case {case_id} not found."
            
            # Security check
            if case.owner.id != self.current_engineer_id:
                return f"You don't have access to case {case_id}."
            
            violations = self._check_all_rules(case)
            
            if not violations:
                return f"""✅ **CSAT Rule Compliance: Case {case_id}**

All CSAT rules are being followed! Keep up the good work.

**Status:**
• 2-Day Communication Rule: ✅ Compliant
• 7-Day Notes Rule: ✅ Compliant
• 5-Hour Email-to-Notes Rule: ✅ Compliant
"""
            
            result = f"""⚠️ **CSAT Rule Violations: Case {case_id}**

The following rules need attention:

"""
            for v in violations:
                emoji = "🚨" if v.severity == "breach" else "⚠️"
                result += f"""{emoji} **{v.rule.value.upper()}**
   Exceeded by: {v.days_exceeded:.1f} days
   Last relevant activity: {v.last_event_date.strftime('%Y-%m-%d %H:%M') if v.last_event_date else 'Never'}
   **Recommendation:** {v.recommendation}

"""
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking CSAT rules: {e}", exc_info=True)
            return f"Error checking rules for case {case_id}: {str(e)}"
    
    @kernel_function(
        name="analyze_communication_timeline",
        description="Analyze the communication pattern on a case - response times, gaps, frequency - to identify CSAT risks"
    )
    async def analyze_communication_timeline(self, case_id: str) -> str:
        """
        Analyze the communication timeline of a case.
        
        Args:
            case_id: The case identifier
            
        Returns:
            str: Detailed timeline analysis
        """
        logger.info(f"CSATRulesPlugin.analyze_communication_timeline called for case: {case_id}")
        
        try:
            case = await self.dfm_client.get_case(case_id)
            
            if case is None:
                return f"Case {case_id} not found."
            
            if case.owner.id != self.current_engineer_id:
                return f"You don't have access to case {case_id}."
            
            analysis = self._analyze_timeline(case)
            
            result = f"""📊 **Communication Timeline Analysis: Case {case_id}**

**Overview:**
• Case open for: {analysis.days_open:.0f} days
• Total timeline entries: {analysis.total_communications}
• Customer messages: {analysis.customer_communications}
• Engineer messages: {analysis.engineer_communications}

**Communication Pattern:** {analysis.communication_pattern.upper()}
"""
            
            if analysis.avg_response_time_hours:
                result += f"• Average response time: {analysis.avg_response_time_hours:.1f} hours\n"
            
            result += f"• Longest communication gap: {analysis.longest_gap_days:.1f} days\n"
            
            # Risk assessment
            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}
            result += f"""
**CSAT Risk Level:** {risk_emoji.get(analysis.risk_level, '⚪')} {analysis.risk_level.upper()}

"""
            
            if analysis.risk_factors:
                result += "**Risk Factors:**\n"
                for factor in analysis.risk_factors:
                    result += f"• {factor}\n"
            
            if analysis.rule_violations:
                result += "\n**Rule Violations:**\n"
                for v in analysis.rule_violations:
                    result += f"• {v.rule.value}: exceeded by {v.days_exceeded:.1f} days\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing timeline: {e}", exc_info=True)
            return f"Error analyzing case {case_id}: {str(e)}"
    
    @kernel_function(
        name="get_csat_coaching",
        description="Get specific, actionable coaching recommendations for a case based on its timeline and CSAT risk factors"
    )
    async def get_csat_coaching(self, case_id: str) -> str:
        """
        Get specific CSAT coaching for a case.
        
        Args:
            case_id: The case identifier
            
        Returns:
            str: Specific coaching recommendations
        """
        logger.info(f"CSATRulesPlugin.get_csat_coaching called for case: {case_id}")
        
        try:
            case = await self.dfm_client.get_case(case_id)
            
            if case is None:
                return f"Case {case_id} not found."
            
            if case.owner.id != self.current_engineer_id:
                return f"You don't have access to case {case_id}."
            
            analysis = self._analyze_timeline(case)
            coaching = self._generate_coaching(case, analysis)
            
            result = f"""🎯 **CSAT Coaching: Case {case_id}**

"""
            
            if not coaching:
                result += """Great job! This case is being handled well from a CSAT perspective.

**Continue doing:**
• Regular customer communication
• Timely case note updates
• Setting clear expectations
"""
            else:
                result += "**Specific Recommendations:**\n\n"
                for i, (observation, why, action) in enumerate(coaching, 1):
                    result += f"""**{i}. {observation}**
   *Why it matters:* {why}
   *Action:* {action}

"""
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating coaching: {e}", exc_info=True)
            return f"Error generating coaching for case {case_id}: {str(e)}"
    
    @kernel_function(
        name="get_csat_rules_reference",
        description="Get a reference of all CSAT rules and best practices. Use this when the engineer asks about CSAT rules or wants to understand best practices."
    )
    def get_csat_rules_reference(self) -> str:
        """
        Get a reference of all CSAT rules.
        
        Returns:
            str: CSAT rules reference
        """
        return """📘 **CSAT Rules Reference**

**THE GOLDEN RULES:**

**1. 2-Day Communication Rule** ⏰
   Customers should NEVER go more than 2 days without hearing from their engineer.
   • Even a brief "still investigating" counts
   • Silence creates customer anxiety
   • This is the #1 driver of low CSAT

**2. 7-Day Notes Rule** 📝
   Case notes must be updated at least every 7 days.
   • Anyone picking up the case should understand status
   • Document: current status, blockers, next steps, action owner
   • Notes are your safety net for handoffs

**3. 5-Hour Email-to-Notes Rule** ✉️
   After emailing a customer, add case notes within 5 hours.
   • Document what was communicated
   • List action items and owners
   • Capture who has the next action

**KEY CSAT DRIVERS (Priority Order):**
1. **Setting Right Expectations** - Be honest, under-promise/over-deliver
2. **Resolution Time** - Track days open, identify blockers early
3. **Communication Frequency** - Regular touchpoints build trust

**COACHING STANDARDS:**
✅ Specific to THIS case (reference actual timeline events)
✅ Actionable with clear next steps
✅ Insightful - catch what might be missed
✅ Supportive - never blame, always coach

**NEVER DO:**
❌ Promise specific resolution timelines
❌ Give generic advice without case context
❌ Make the engineer feel bad about past performance
"""
    
    # =========================================================================
    # Internal Analysis Methods
    # =========================================================================
    
    def _check_all_rules(self, case: Case) -> List[RuleViolation]:
        """Check all CSAT rules and return violations."""
        violations = []
        now = datetime.now()
        
        # Rule 1: 2-Day Communication Rule
        last_customer_comm = self._get_last_customer_communication(case)
        if last_customer_comm:
            days_since_comm = (now - last_customer_comm.created_on).total_seconds() / 86400
            if days_since_comm > 2:
                violations.append(RuleViolation(
                    rule=CSATRuleViolation.TWO_DAY_COMMUNICATION,
                    severity="breach" if days_since_comm > 3 else "warning",
                    days_exceeded=days_since_comm - 2,
                    last_event_date=last_customer_comm.created_on,
                    recommendation=f"Send a status update to the customer today. They haven't heard from you in {days_since_comm:.0f} days."
                ))
        elif case.days_since_creation > 2:
            violations.append(RuleViolation(
                rule=CSATRuleViolation.TWO_DAY_COMMUNICATION,
                severity="breach",
                days_exceeded=case.days_since_creation - 2,
                last_event_date=case.created_on,
                recommendation="No customer communication found. Reach out to the customer immediately."
            ))
        
        # Rule 2: 7-Day Notes Rule
        days_since_note = case.days_since_last_note
        if days_since_note > 7:
            last_note = self._get_last_note(case)
            violations.append(RuleViolation(
                rule=CSATRuleViolation.SEVEN_DAY_NOTES,
                severity="breach",
                days_exceeded=days_since_note - 7,
                last_event_date=last_note.created_on if last_note else case.created_on,
                recommendation=f"Add case notes immediately. Notes are {days_since_note:.0f} days old."
            ))
        elif days_since_note > 5:
            last_note = self._get_last_note(case)
            violations.append(RuleViolation(
                rule=CSATRuleViolation.SEVEN_DAY_NOTES,
                severity="warning",
                days_exceeded=days_since_note - 5,
                last_event_date=last_note.created_on if last_note else case.created_on,
                recommendation=f"Case notes are {days_since_note:.0f} days old. Plan to update them soon."
            ))
        
        # Rule 3: 5-Hour Email-to-Notes Rule
        email_without_notes = self._check_email_notes_rule(case)
        if email_without_notes:
            email_date, hours_elapsed = email_without_notes
            if hours_elapsed > 5:
                violations.append(RuleViolation(
                    rule=CSATRuleViolation.FIVE_HOUR_EMAIL_NOTES,
                    severity="warning" if hours_elapsed < 24 else "breach",
                    days_exceeded=(hours_elapsed - 5) / 24,
                    last_event_date=email_date,
                    recommendation=f"You sent an email {hours_elapsed:.0f} hours ago without adding case notes. Add notes documenting what was discussed."
                ))
        
        return violations
    
    def _analyze_timeline(self, case: Case) -> TimelineAnalysis:
        """Perform comprehensive timeline analysis."""
        now = datetime.now()
        
        # Count communications
        customer_comms = [e for e in case.timeline if e.is_customer_communication]
        engineer_comms = [e for e in case.timeline 
                         if e.entry_type in [TimelineEntryType.EMAIL_SENT, TimelineEntryType.PHONE_CALL]
                         and not e.is_customer_communication]
        
        # Calculate gaps
        gaps = self._calculate_communication_gaps(case)
        longest_gap = max([g.gap_days for g in gaps], default=0)
        
        # Calculate average response time
        avg_response = self._calculate_avg_response_time(case)
        
        # Determine communication pattern
        if avg_response and avg_response < 24:
            pattern = "responsive"
        elif longest_gap > 3:
            pattern = "delayed"
        else:
            pattern = "sporadic"
        
        # Check rule violations
        violations = self._check_all_rules(case)
        
        # Calculate risk factors
        risk_factors = []
        if longest_gap > 2:
            risk_factors.append(f"Communication gap of {longest_gap:.0f} days detected")
        if case.days_since_last_note > 5:
            risk_factors.append(f"Case notes {case.days_since_last_note:.0f} days old")
        if len(customer_comms) > len(engineer_comms) * 2:
            risk_factors.append("Customer is reaching out more than you're responding")
        
        # Determine risk level
        if len(violations) > 1 or any(v.severity == "breach" for v in violations):
            risk_level = "high"
        elif violations or risk_factors:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return TimelineAnalysis(
            case_id=case.id,
            days_open=case.days_since_creation,
            total_communications=len(case.timeline),
            customer_communications=len(customer_comms),
            engineer_communications=len(engineer_comms),
            avg_response_time_hours=avg_response,
            longest_gap_days=longest_gap,
            rule_violations=violations,
            communication_pattern=pattern,
            risk_level=risk_level,
            risk_factors=risk_factors,
        )
    
    def _generate_coaching(self, case: Case, analysis: TimelineAnalysis) -> List[tuple]:
        """Generate specific coaching recommendations."""
        coaching = []
        
        # Coaching based on violations
        for v in analysis.rule_violations:
            if v.rule == CSATRuleViolation.TWO_DAY_COMMUNICATION:
                coaching.append((
                    f"No customer communication in {v.days_exceeded + 2:.0f} days",
                    "Silence is the #1 driver of low CSAT. Customers worry when they don't hear from you.",
                    "Send a status update today, even if it's just 'still investigating, will have more by [date]'."
                ))
            elif v.rule == CSATRuleViolation.SEVEN_DAY_NOTES:
                coaching.append((
                    f"Case notes are {v.days_exceeded + 7:.0f} days old",
                    "Outdated notes make handoffs risky and show lack of case momentum.",
                    "Add notes today documenting: current status, blockers, next steps, who owns next action."
                ))
        
        # Coaching based on timeline patterns
        if analysis.communication_pattern == "delayed":
            recent_entries = case.timeline[-5:] if case.timeline else []
            customer_waiting = [e for e in recent_entries if e.is_customer_communication]
            if customer_waiting:
                last_customer = customer_waiting[-1]
                coaching.append((
                    f"Customer reached out on {last_customer.created_on.strftime('%Y-%m-%d')}",
                    "Delayed responses signal to customers that their issue isn't a priority.",
                    "Respond within 24 hours, even if just to acknowledge and set expectations."
                ))
        
        # Look for specific timeline events that need attention
        for entry in case.timeline[-10:]:
            content_lower = entry.content.lower()
            
            # Detect urgency signals
            if any(word in content_lower for word in ['urgent', 'asap', 'critical', 'deadline', 'board meeting', 'go-live']):
                if entry.is_customer_communication:
                    coaching.append((
                        f"Customer mentioned urgency on {entry.created_on.strftime('%Y-%m-%d')}: found keywords suggesting deadline pressure",
                        "Unacknowledged urgency leads to missed expectations and low CSAT.",
                        "Acknowledge the timeline constraint and provide a realistic update on what you can deliver by when."
                    ))
            
            # Detect frustration signals
            if any(word in content_lower for word in ['frustrated', 'disappointed', 'unacceptable', 'escalate', 'manager']):
                if entry.is_customer_communication:
                    coaching.append((
                        f"Customer expressed frustration on {entry.created_on.strftime('%Y-%m-%d')}",
                        "Frustration that isn't addressed quickly often results in escalations and low CSAT.",
                        "Consider a phone call to reset expectations. Voice communication builds rapport faster than email."
                    ))
        
        return coaching[:5]  # Limit to 5 recommendations
    
    def _get_last_customer_communication(self, case: Case) -> Optional[TimelineEntry]:
        """Get the most recent outbound communication to customer."""
        outbound = [e for e in case.timeline 
                    if e.entry_type in [TimelineEntryType.EMAIL_SENT, TimelineEntryType.PHONE_CALL]
                    and not e.is_customer_communication]
        return max(outbound, key=lambda e: e.created_on) if outbound else None
    
    def _get_last_note(self, case: Case) -> Optional[TimelineEntry]:
        """Get the most recent case note."""
        notes = [e for e in case.timeline if e.entry_type == TimelineEntryType.NOTE]
        return max(notes, key=lambda e: e.created_on) if notes else None
    
    def _check_email_notes_rule(self, case: Case) -> Optional[tuple]:
        """Check if recent emails have corresponding notes within 5 hours."""
        now = datetime.now()
        
        # Get emails sent in the last 48 hours
        recent_emails = [
            e for e in case.timeline
            if e.entry_type == TimelineEntryType.EMAIL_SENT
            and not e.is_customer_communication
            and (now - e.created_on).total_seconds() < 48 * 3600
        ]
        
        for email in recent_emails:
            # Check if there's a note within 5 hours after this email
            email_time = email.created_on
            five_hours_later = email_time + timedelta(hours=5)
            
            notes_after = [
                e for e in case.timeline
                if e.entry_type == TimelineEntryType.NOTE
                and email_time < e.created_on <= five_hours_later
            ]
            
            if not notes_after:
                hours_elapsed = (now - email_time).total_seconds() / 3600
                if hours_elapsed > 5:
                    return (email_time, hours_elapsed)
        
        return None
    
    def _calculate_communication_gaps(self, case: Case) -> List[CommunicationGap]:
        """Calculate gaps in customer communication."""
        gaps = []
        
        outbound_comms = sorted([
            e for e in case.timeline
            if e.entry_type in [TimelineEntryType.EMAIL_SENT, TimelineEntryType.PHONE_CALL]
            and not e.is_customer_communication
        ], key=lambda e: e.created_on)
        
        # Calculate gaps between outbound communications
        for i in range(1, len(outbound_comms)):
            prev = outbound_comms[i - 1]
            curr = outbound_comms[i]
            gap_days = (curr.created_on - prev.created_on).total_seconds() / 86400
            
            if gap_days > 1:  # Only track gaps > 1 day
                # Count customer messages during this gap
                customer_msgs = len([
                    e for e in case.timeline
                    if e.is_customer_communication
                    and prev.created_on < e.created_on < curr.created_on
                ])
                
                gaps.append(CommunicationGap(
                    start_date=prev.created_on,
                    end_date=curr.created_on,
                    gap_days=gap_days,
                    customer_messages_during_gap=customer_msgs,
                ))
        
        return gaps
    
    def _calculate_avg_response_time(self, case: Case) -> Optional[float]:
        """Calculate average response time to customer messages."""
        sorted_timeline = sorted(case.timeline, key=lambda e: e.created_on)
        response_times = []
        
        for i, entry in enumerate(sorted_timeline):
            if entry.is_customer_communication:
                # Find next engineer response
                for j in range(i + 1, len(sorted_timeline)):
                    next_entry = sorted_timeline[j]
                    if next_entry.entry_type in [TimelineEntryType.EMAIL_SENT, TimelineEntryType.PHONE_CALL]:
                        if not next_entry.is_customer_communication:
                            hours = (next_entry.created_on - entry.created_on).total_seconds() / 3600
                            response_times.append(hours)
                            break
        
        return sum(response_times) / len(response_times) if response_times else None
