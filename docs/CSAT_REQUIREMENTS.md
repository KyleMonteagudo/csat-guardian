# CSAT Guardian - Agent Requirements

> **Document Version**: 1.0  
> **Last Updated**: January 24, 2026  
> **Status**: POC Implementation Guide

## Executive Summary

CSAT Guardian is an AI-powered assistant that helps CSS engineers proactively manage customer satisfaction. The agent provides **case-specific coaching** based on actual case timeline data, not generic advice.

---

## 1. User Interaction Model

### Communication Channels
- **Teams Chat**: Primary interface for engineer interactions
- **Proactive Notifications**: Agent-initiated alerts via Teams

### Interaction Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| **Reactive** | Engineer asks a question | "How can I improve this customer's experience?" |
| **Proactive** | Agent alerts engineer | "Case X hasn't been updated in 6 days" |

### Proactive Alert Triggers
The agent should automatically notify engineers when:

1. **Communication Gap Detected**
   - Case has no customer communication in 2+ days
   - Message: "Hey, case {case_id} hasn't had customer communication in {days} days"

2. **Case Notes Stale**
   - Case notes not updated in 7+ days
   - Message: "Case {case_id} notes are {days} days old - consider adding an update"

3. **CSAT Risk Detected**
   - Timeline shows potential negative sentiment (frustrated email, escalation request, etc.)
   - Message: "Potential CSAT risk detected in case {case_id}: {reason}"

4. **Email Without Follow-up Notes**
   - Engineer sent email to customer but no case notes within 5 hours
   - Message: "You emailed the customer on case {case_id} {hours} hours ago - remember to add case notes"

---

## 2. Data Access & Permissions

### Engineer Access (Default)
- ✅ Own cases only
- ✅ Full case timeline (emails, notes, communications)
- ✅ Customer context (tier, contract, previous CSAT scores)
- ❌ Other engineers' cases
- ❌ Team-wide metrics

### Manager Access (Future - v2)
- ✅ All cases for engineers they manage
- ✅ Team-wide CSAT metrics
- ✅ Comparative analysis across team
- ❌ Cases outside their management scope

---

## 3. CSAT Domain Knowledge

### The Golden Rules

These are the core business rules the agent must know and apply:

```
┌─────────────────────────────────────────────────────────────────────┐
│  RULE 1: 2-Day Communication Rule                                   │
│  ─────────────────────────────────────────────────────────────────  │
│  Customers should NEVER go more than 2 days without hearing from    │
│  their engineer. Even a quick "still investigating" is valuable.    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  RULE 2: 7-Day Notes Rule                                           │
│  ─────────────────────────────────────────────────────────────────  │
│  Case notes should be updated at least every 7 days. This ensures   │
│  anyone picking up the case can understand current status.          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  RULE 3: 5-Hour Email-to-Notes Rule                                 │
│  ─────────────────────────────────────────────────────────────────  │
│  When an engineer emails a customer, case notes should be added     │
│  within 5 hours documenting:                                        │
│    • What was communicated                                          │
│    • Action items                                                   │
│    • Who owns next action (engineer or customer)                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Key CSAT Drivers (Priority Order)

1. **Setting Right Expectations**
   - Be honest about timelines
   - Under-promise, over-deliver
   - If you don't know, say so - then find out

2. **Resolution Time**
   - Track days open vs. similar cases
   - Identify blockers early
   - Escalate when appropriate

3. **Communication Frequency**
   - Regular touchpoints build trust
   - Silence creates anxiety
   - Even "no update" is an update

---

## 4. Guardrails - What the Agent Must NOT Do

### Hard Rules (Never Violate)

| ❌ NEVER | Why |
|----------|-----|
| Promise specific resolution timelines | Creates liability, often wrong |
| Share customer data across engineers | Privacy and compliance |
| Make engineer feel bad about low CSAT | Demotivating, counterproductive |
| Give generic/obvious advice | Engineers already know basics |
| Blame the customer | Not constructive |
| Suggest shortcuts that compromise quality | Short-term thinking |

### Coaching Standards

The agent's coaching MUST be:

```
✅ SPECIFIC to this case
   "In the Jan 15 email, the customer mentioned they have a board meeting Friday.
    Consider prioritizing this case and providing an update by Thursday."

❌ NOT generic
   "You should communicate more frequently with customers."
```

```
✅ ACTIONABLE with context
   "The last 3 emails show increasing frustration. Consider a quick call
    to reset expectations - sometimes voice builds rapport faster than email."

❌ NOT surface-level
   "Customer seems frustrated. Try to be more responsive."
```

```
✅ INSIGHTFUL - sees what engineer might miss
   "This customer has had 2 previous cases with low CSAT, both related to
    communication gaps. They may be especially sensitive to delays."

❌ NOT obvious
   "Customers don't like waiting."
```

---

## 5. Analysis Requirements

### Case Analysis Must Include

When analyzing a case, the agent should examine and report on:

#### Timeline Analysis
- [ ] Days since case opened
- [ ] Days since last customer communication
- [ ] Days since last case notes update
- [ ] Communication frequency pattern
- [ ] Time gaps between interactions

#### Risk Indicators
- [ ] Sentiment trend (improving/declining)
- [ ] Escalation language detected
- [ ] Missed SLA indicators (2-day, 7-day rules)
- [ ] Customer tier vs. response time

#### Contextual Factors
- [ ] Customer's previous CSAT history
- [ ] Complexity indicators
- [ ] Third-party dependencies mentioned
- [ ] Customer expectations stated in timeline

### Response Format

```json
{
  "case_id": "case-001",
  "risk_level": "medium",
  "days_open": 12,
  "communication_analysis": {
    "days_since_customer_contact": 3,
    "rule_violation": "2-day rule exceeded",
    "sentiment_trend": "declining"
  },
  "specific_observations": [
    {
      "date": "2026-01-20",
      "observation": "Customer mentioned deadline of Jan 30",
      "recommendation": "Prioritize - 6 days until customer deadline"
    }
  ],
  "coaching": {
    "immediate_action": "Send update email today acknowledging the Jan 30 deadline",
    "reasoning": "Customer hasn't heard from you in 3 days and has expressed time pressure"
  }
}
```

---

## 6. Success Metrics

### POC Success Criteria

The POC is successful if:

1. **Analysis Depth**
   - Agent provides case-specific insights, not generic advice
   - Recommendations reference actual case timeline events
   - Engineers say "I didn't notice that" at least sometimes

2. **Chat Usefulness**
   - Responses demonstrate understanding of full case context
   - Agent can answer questions about specific interactions
   - Coaching is actionable and specific

3. **Rule Application**
   - Agent correctly identifies 2-day/7-day/5-hour violations
   - Proactive alerts would catch issues before they escalate
   - Risk assessments align with engineer judgment

### Production Success Criteria (Future)

- Measurable improvement in team CSAT scores
- Engineers voluntarily using the tool daily
- Reduction in "surprise" low CSAT surveys
- Manager dashboard provides actionable team insights

---

## 7. Technical Implementation Notes

### Data Model Requirements

To support these requirements, we need:

```
CaseTimeline
├── case_id
├── event_type (email_sent, email_received, note_added, call_logged)
├── event_timestamp
├── event_content (for sentiment analysis)
├── direction (inbound/outbound)
└── actor (engineer/customer/system)

CustomerContext
├── customer_id
├── tier (Premier, Unified, Pro)
├── previous_csat_scores[]
├── contract_details
└── sensitivity_notes
```

### Integration Points

1. **DfM Data Sync** - Pull case timeline data
2. **Teams Bot** - Send proactive notifications
3. **Azure OpenAI** - Analysis and chat
4. **Azure SQL** - Store analysis results, track patterns

---

## Appendix: Example Interactions

### Good Agent Response

**Engineer**: "How can I improve this customer's experience?"

**Agent**: 
> Looking at case CS-2024-4521, I see a few specific opportunities:
>
> 1. **Communication gap**: Your last email was January 21st (3 days ago). The customer's response on Jan 21 mentioned they're "eager to have this resolved before month-end" - that's 7 days away. A quick update today would help.
>
> 2. **Expectation alignment**: In the Jan 18 email, you mentioned "should have an update early next week." It's now Friday - consider either sending that update or explaining the delay.
>
> 3. **Historical context**: This customer gave 3/5 on their previous case last March, with feedback mentioning "slow communication." Being extra responsive here could help rebuild trust.
>
> **Suggested immediate action**: Send a brief status email acknowledging their month-end deadline and providing a realistic timeline for next steps.

### Bad Agent Response (What We Don't Want)

**Engineer**: "How can I improve this customer's experience?"

**Agent**:
> To improve customer experience, consider:
> - Respond promptly to emails
> - Keep case notes updated
> - Set clear expectations
> - Be professional and courteous

*(This is generic advice that any engineer already knows - provides no value)*

---

*Document maintained by CSAT Guardian development team*
