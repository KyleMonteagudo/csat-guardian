# CSAT Guardian Design Session - Chat History
**Date:** January 22, 2026  
**Participants:** Kyle Monteagudo, GitHub Copilot (Claude Opus 4.5)  
**Purpose:** Design and document CSAT Guardian application for security review approval

---

## Session Summary

This chat session focused on designing CSAT Guardian, an AI-powered proactive customer support optimization tool. The goal was to create comprehensive security review documentation to obtain API access to DfM (Dynamics for Microsoft).

---

## Conversation Timeline

### 1. Initial Concept Discussion

**User Request:** Build "CSAT Guardian" - a proactive support experience optimization tool

**Key Requirements Identified:**
- Monitor DfM cases for negative customer sentiment
- Provide engineers with case briefings and troubleshooting suggestions
- Alert engineers when customers appear unhappy
- Shift from reactive (post-survey) to proactive (real-time) CSAT management

**Technology Stack Discussed:**
- Azure OpenAI (GPT-4o) for sentiment analysis
- DfM (Dynamics for Microsoft) for case data
- Microsoft Teams for engineer notifications
- Azure Functions / Container Apps for hosting
- Managed Identity for authentication

---

### 2. Security Review Documentation Created

**Deliverable:** `APPLICATION_SECURITY_REVIEW.md`

**Document Structure:**
1. Executive Summary
2. Application Overview & Business Justification
3. Architecture (with ASCII diagrams)
4. Data Access Requirements
5. Identity & Authentication
6. Data Storage & Retention
7. Security Controls
8. Notification System Requirements
9. Operational Requirements
10. Risk Assessment
11. Implementation Phases
12. Appendices (API endpoints, sample config, glossary)

---

### 3. User Clarification: Phone Call Data

**User Input:** "We don't get voice data from the calls - the engineer types notes into DfM after/during the call"

**Changes Made:**
- Updated Phone Call Notes description to clarify: "engineer notes about customer calls (note: no voice/audio data - just written notes about the call)"
- Updated API endpoint comments
- Ensured document clearly states READ-ONLY text data only

---

### 4. User Clarification: 7-Day Compliance Tracking

**User Input:** Need to track cases that haven't been updated in 7 days (warning at day 5-6, alert at day 7+)

**Changes Made:**
- Added capability #6: "Enforces 7-day case note update compliance with proactive warnings"
- Added "7-Day Warning" notification type (Medium urgency, day 5-6)
- Added "7-Day Breach" notification type (High urgency, day 7+)
- Added `complianceAlerts` configuration section:
  ```json
  "complianceAlerts": {
    "caseUpdateRequiredDays": 7,
    "warningThresholdDays": 5,
    "breachAlertEnabled": true,
    "warningAlertEnabled": true
  }
  ```

---

### 5. User Clarification: Conversational Interaction

**User Input:** "The engineer should be able to interact with the agent in Teams, and have conversations if they need to, in order to get the best assistance from the agent."

**Changes Made:**
- Added capability #7: "Converses with engineers in Teams for interactive guidance and follow-up questions"
- Added new section 3.4: Teams Bot Framework Access
- Added `Chat.ReadWrite` permission for reading engineer replies
- Added new section 7.2: Conversational Interaction with example dialogues
- Updated user access from "Recipient Only" to "Conversational"
- Added Azure Bot Service to API endpoints
- Updated implementation phases to include bot setup

**Example Interactions Documented:**
```
👤 Engineer: "Tell me more about why this customer seems frustrated"
🤖 Guardian: "Based on the case timeline, the customer has expressed frustration..."

👤 Engineer: "Can you summarize case 12345678?"
🤖 Guardian: "📋 Case #12345678 Summary: ..."
```

**Conversation Boundaries Defined:**
- Agent only discusses cases assigned to the engineer
- Cannot modify case data or contact customers
- Provides suggestions - engineer makes all decisions
- Session-based history (not permanently stored)

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| READ-ONLY access to DfM | Minimize risk; agent advises, doesn't act |
| No PII storage | Data minimization; sentiment analysis doesn't need identity |
| Managed Identity | No credentials in code; enterprise security pattern |
| Teams Bot (not just webhooks) | Enable conversational interaction with engineers |
| 7-day compliance tracking | Business requirement for case update cadence |
| Configurable thresholds | Different teams may have different needs |

---

## Files Created This Session

| File | Purpose |
|------|---------|
| `csat-guardian/docs/APPLICATION_SECURITY_REVIEW.md` | Comprehensive security review documentation (~575 lines) |
| `csat-guardian/docs/chat-history/2026-01-22_csat-guardian-design-session.md` | This conversation log |

---

## Next Steps (Discussed)

1. **Submit security review** - Document is ready for approval process
2. **Presentation deck** - Offered to create stakeholder presentation (not yet requested)
3. **Project scaffolding** - Can begin code structure once API access approved

---

## Technical Notes

### Architecture Summary
```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│     DfM      │────▶│  CSAT Guardian  │────▶│    Teams     │
│  (Dynamics)  │     │    Service      │◀───▶│  (Bot Chat)  │
└──────────────┘     └────────┬────────┘     └──────────────┘
   READ-ONLY                  │
                     ┌────────▼────────┐
                     │   Azure OpenAI  │
                     │  (Sentiment AI) │
                     └─────────────────┘
```

### Key Permissions Required
- **DfM:** Read incidents, annotations, emails, phonecalls, activities
- **Graph:** Chat.Create, Chat.ReadWrite, User.Read.All, ChannelMessage.Send
- **Bot:** Azure Bot Service registration, Teams App Manifest

### Data Flow
1. Case created/updated in DfM
2. CSAT Guardian reads case data (webhook or polling)
3. Azure OpenAI analyzes sentiment
4. If alert threshold met → Teams notification to engineer
5. Engineer can converse with bot for guidance
6. Aggregate metrics logged (no PII)

---

## Session End Notes

This session successfully produced a comprehensive security review document that addresses:
- Business justification
- Technical architecture
- Data access requirements (READ-ONLY)
- Security controls
- Privacy considerations (no PII storage)
- Conversational interaction capabilities
- 7-day compliance tracking
- Implementation roadmap

The document is ready for security team review to obtain DfM API access.

---

*Chat history saved: January 22, 2026*
