# =============================================================================
# CSAT Guardian - Rich Sample Data for Local Testing
# =============================================================================
# This module provides comprehensive mock data for testing the agent locally.
# 
# Cases included:
# - case-001: Happy customer (ideal behavior)
# - case-002: Frustrated customer (CSAT risk - escalation language)
# - case-003: 7-day rule breach (no notes in 8 days)
# - case-004: Declining sentiment (started good, getting worse)
# - case-005: 2-day rule violation (no comms in 3 days)
# - case-006: Resolved happy (well-handled)
# - case-007: 5-hour rule violation (email sent, no notes)
# - case-008: Complex third-party dependency
# =============================================================================

from datetime import datetime, timedelta
from typing import List, Optional

from models import (
    Engineer, Customer, Case, TimelineEntry,
    CaseStatus, CaseSeverity, TimelineEntryType
)


def get_sample_engineers() -> List[Engineer]:
    """Get list of sample engineers."""
    return [
        Engineer(
            id="eng-001",
            name="Kevin Monteagudo",
            email="kmonteagudo@microsoft.com",
            team="CSS Azure Core"
        ),
        Engineer(
            id="eng-002",
            name="Sarah Chen",
            email="schen@microsoft.com",
            team="CSS Azure Core"
        ),
        Engineer(
            id="eng-003",
            name="Marcus Williams",
            email="mwilliams@microsoft.com",
            team="CSS M365"
        ),
    ]


def get_sample_customers() -> List[Customer]:
    """Get list of sample customers."""
    return [
        Customer(id="cust-001", company="Contoso Healthcare", tier="Premier"),
        Customer(id="cust-002", company="Fabrikam Manufacturing", tier="Unified"),
        Customer(id="cust-003", company="Adventure Works Retail", tier="Premier"),
        Customer(id="cust-004", company="Northwind Financial", tier="Premier"),
        Customer(id="cust-005", company="Tailspin Aerospace", tier="Unified"),
        Customer(id="cust-006", company="Wide World Importers", tier="Pro"),
    ]


def get_sample_cases() -> List[Case]:
    """
    Get comprehensive sample cases for testing.
    
    Each case is designed to test specific CSAT rules and scenarios.
    """
    now = datetime.now()
    engineers = {e.id: e for e in get_sample_engineers()}
    customers = {c.id: c for c in get_sample_customers()}
    
    cases = []
    
    # =========================================================================
    # CASE 1: HAPPY CUSTOMER - Good communication, positive sentiment
    # Tests: Ideal behavior, no violations
    # =========================================================================
    case1 = Case(
        id="2501140050001234",
        title="Azure AD B2C configuration for patient portal",
        description="We are implementing Azure AD B2C for our new patient portal and need guidance on best practices for healthcare compliance.",
        status=CaseStatus.ACTIVE,
        severity=CaseSeverity.SEV_C,
        owner=engineers["eng-001"],
        customer=customers["cust-001"],
        created_on=now - timedelta(days=5),
        modified_on=now - timedelta(hours=4),
        timeline=[
            TimelineEntry(
                id="tl-001-01",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Initial Request",
                content="Hi Kevin, we are starting our Azure AD B2C implementation for our patient portal. We need to ensure HIPAA compliance. Can you help us understand the best practices? We have a go-live target of February 15th.",
                created_by="Customer",
                created_on=now - timedelta(days=5),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-001-02",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="RE: Initial Request",
                content="Hi! Thank you for reaching out. I would be happy to help with your Azure AD B2C implementation. Given your HIPAA requirements and Feb 15 timeline, I suggest we schedule a call this week to review your architecture. I have availability Thursday at 2pm or Friday at 10am. Which works better?",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=5, hours=-2),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-001-03",
                entry_type=TimelineEntryType.NOTE,
                subject="Internal Note",
                content="Customer is implementing B2C for healthcare portal. Key requirements: HIPAA compliance, Feb 15 go-live. Will need to review token lifetimes, MFA policies, and audit logging. Scheduling architecture review call.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=5, hours=-3),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-001-04",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="RE: Initial Request",
                content="Thursday at 2pm works great! Looking forward to the call. Should we invite our security team as well?",
                created_by="Customer",
                created_on=now - timedelta(days=4),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-001-05",
                entry_type=TimelineEntryType.PHONE_CALL,
                subject="Architecture Review Call",
                content="Had 45-min call with customer and their security team. Reviewed B2C architecture. Key decisions: 1) Will use custom policies for HIPAA-compliant flows, 2) Implementing MFA for all users, 3) 1-hour token lifetime. Customer very engaged and appreciative. Next step: I will share documentation on custom policies by Monday.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=2),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-001-06",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="Documentation as promised",
                content="Hi team, as discussed on our call, here is the documentation on B2C custom policies for healthcare scenarios. I have also included a sample policy template you can use as a starting point. Let me know if you have questions!",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=1),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-001-07",
                entry_type=TimelineEntryType.NOTE,
                subject="Follow-up Note",
                content="Sent custom policy documentation. Customer has everything needed to proceed. Will check in Friday to see if they have questions. On track for Feb 15 go-live.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=1, hours=-1),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-001-08",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="RE: Documentation",
                content="Kevin, this is exactly what we needed! The sample template saved us hours of work. We have started implementing and everything is going smoothly. Thank you for the excellent support!",
                created_by="Customer",
                created_on=now - timedelta(hours=4),
                is_customer_communication=True
            ),
        ]
    )
    cases.append(case1)
    
    # =========================================================================
    # CASE 2: FRUSTRATED CUSTOMER - Communication gaps, escalation language
    # Tests: 2-day rule violation, declining sentiment, CSAT risk
    # =========================================================================
    case2 = Case(
        id="2501130050005678",
        title="Production SQL Server down after patching - CRITICAL",
        description="Our production SQL Server went down after applying the monthly patches. We cannot process orders. This is a SEV1 situation affecting $50K/hour in revenue.",
        status=CaseStatus.ACTIVE,
        severity=CaseSeverity.SEV_A,
        owner=engineers["eng-001"],
        customer=customers["cust-002"],
        created_on=now - timedelta(days=4),
        modified_on=now - timedelta(days=2),
        timeline=[
            TimelineEntry(
                id="tl-002-01",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="URGENT: Production Down",
                content="Our production SQL Server crashed after patching last night. We CANNOT process any customer orders. This is costing us approximately $50,000 per hour in lost revenue. We need immediate assistance!",
                created_by="Customer",
                created_on=now - timedelta(days=4),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-002-02",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="RE: URGENT: Production Down",
                content="I understand the severity and I am treating this as top priority. Can you please share the SQL error logs from the Event Viewer? Also, which specific patches were applied? I will start investigating immediately.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=4, hours=-1),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-002-03",
                entry_type=TimelineEntryType.NOTE,
                subject="Initial Investigation",
                content="SEV1 - Production SQL down after patching. Customer losing $50K/hr. Requested error logs. Need to identify which patch caused the issue.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=4, hours=-1),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-002-04",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Logs Attached",
                content="Here are the error logs. The crash happens on startup. Our DBA tried rolling back the patches but the server still wont start. PLEASE HURRY.",
                created_by="Customer",
                created_on=now - timedelta(days=4, hours=-2),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-002-05",
                entry_type=TimelineEntryType.NOTE,
                subject="Log Analysis",
                content="Reviewed logs - seeing corruption in master database after patch rollback attempt. This is complex. Escalating to SQL PG for guidance. Will update customer.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=4, hours=-4),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-002-06",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Still Waiting",
                content="It has been 6 hours since my last email. What is the status? Our CEO is asking for answers. We have had to tell customers we cannot fulfill their orders. This is becoming a nightmare.",
                created_by="Customer",
                created_on=now - timedelta(days=4, hours=-8),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-002-07",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Day 2 - No Resolution",
                content="This is now DAY 2 and we still do not have our production system back. I have escalated internally to our VP who is now involved. We need to understand what is being done and when this will be resolved. The lack of communication is unacceptable.",
                created_by="Customer",
                created_on=now - timedelta(days=3),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-002-08",
                entry_type=TimelineEntryType.NOTE,
                subject="Escalation Note",
                content="Customer escalated to their VP. Still waiting on SQL PG response. Need to provide update to customer today.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=3, hours=-2),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-002-09",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Considering Legal Action",
                content="I am absolutely furious. THREE DAYS of downtime, over $3.6 MILLION in lost revenue, and I have received ONE email from Microsoft. I am escalating this to our legal team and will be filing a formal complaint. I want to speak with your manager IMMEDIATELY. This level of support is completely unacceptable for a Premier customer.",
                created_by="Customer",
                created_on=now - timedelta(days=2),
                is_customer_communication=True
            ),
        ]
    )
    cases.append(case2)
    
    # =========================================================================
    # CASE 3: 7-DAY RULE BREACH - No notes in 8 days
    # Tests: 7-day notes rule violation
    # =========================================================================
    case3 = Case(
        id="2501100050009012",
        title="Azure DevOps pipeline optimization inquiry",
        description="We would like guidance on optimizing our Azure DevOps pipelines for faster build times.",
        status=CaseStatus.ACTIVE,
        severity=CaseSeverity.SEV_C,
        owner=engineers["eng-001"],
        customer=customers["cust-003"],
        created_on=now - timedelta(days=12),
        modified_on=now - timedelta(days=8),
        timeline=[
            TimelineEntry(
                id="tl-003-01",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Pipeline Optimization",
                content="Hi, our Azure DevOps pipelines are taking 45 minutes to complete. We would like to get them under 15 minutes. Can you help us identify optimization opportunities?",
                created_by="Customer",
                created_on=now - timedelta(days=12),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-003-02",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="RE: Pipeline Optimization",
                content="Happy to help! To provide targeted recommendations, could you share your pipeline YAML file and let me know what types of builds you are running (Docker, .NET, Node.js, etc.)?",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=11),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-003-03",
                entry_type=TimelineEntryType.NOTE,
                subject="Initial Note",
                content="Customer wants to optimize DevOps pipelines from 45min to 15min. Requested pipeline YAML and build type info. Will analyze and provide recommendations once received.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=11),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-003-04",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Pipeline Files",
                content="Here is our main pipeline YAML. We are building a .NET 6 application with Docker containers. The YAML is attached.",
                created_by="Customer",
                created_on=now - timedelta(days=10),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-003-05",
                entry_type=TimelineEntryType.NOTE,
                subject="Analysis Note",
                content="Received pipeline YAML. Initial review shows several optimization opportunities: parallel jobs, caching, and agent pool changes. Will document recommendations.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=8),
                is_customer_communication=False
            ),
            # NOTE: No activity for 8 days after this - 7-day rule BREACH
        ]
    )
    cases.append(case3)
    
    # =========================================================================
    # CASE 4: DECLINING SENTIMENT - Started positive, trending negative
    # Tests: Sentiment trend analysis
    # =========================================================================
    case4 = Case(
        id="2501080050003456",
        title="Azure Kubernetes Service intermittent pod failures",
        description="We are experiencing random pod restarts in our AKS cluster. Happening 2-3 times per day affecting our trading platform.",
        status=CaseStatus.ACTIVE,
        severity=CaseSeverity.SEV_B,
        owner=engineers["eng-002"],
        customer=customers["cust-004"],
        created_on=now - timedelta(days=7),
        modified_on=now - timedelta(hours=12),
        timeline=[
            TimelineEntry(
                id="tl-004-01",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="AKS Pod Issues",
                content="Hi Sarah, we have been seeing intermittent pod restarts in our production AKS cluster. It is happening 2-3 times daily and affecting our trading platform. We would appreciate your help investigating.",
                created_by="Customer",
                created_on=now - timedelta(days=7),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-004-02",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="RE: AKS Pod Issues",
                content="Thank you for reporting this. Pod restarts can have several causes. To help diagnose, could you run kubectl describe pod on one of the affected pods and share the output? Also, please share any relevant logs from kubectl logs.",
                created_by="Sarah Chen",
                created_on=now - timedelta(days=7, hours=-3),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-004-03",
                entry_type=TimelineEntryType.NOTE,
                subject="Initial Assessment",
                content="Northwind Financial - AKS pod restart issue affecting trading platform. High priority due to financial impact. Requested pod descriptions and logs.",
                created_by="Sarah Chen",
                created_on=now - timedelta(days=7, hours=-3),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-004-04",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Logs Provided",
                content="Here are the pod descriptions and logs as requested. We really hope you can help us figure this out quickly.",
                created_by="Customer",
                created_on=now - timedelta(days=6),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-004-05",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="Initial Findings",
                content="Looking at the logs, I see OOMKilled events which indicates your pods are running out of memory. I recommend increasing the memory limits in your deployment. I will send specific recommendations shortly.",
                created_by="Sarah Chen",
                created_on=now - timedelta(days=5),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-004-06",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Tried Your Suggestion",
                content="We increased memory limits as you suggested but the restarts are still happening. In fact, they seem to be happening more frequently now. Any other ideas?",
                created_by="Customer",
                created_on=now - timedelta(days=4),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-004-07",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="Additional Analysis",
                content="I apologize that the initial fix did not work. Let me dig deeper. Can you enable diagnostic logs and share the AKS cluster diagnostics?",
                created_by="Sarah Chen",
                created_on=now - timedelta(days=4, hours=-6),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-004-08",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Getting Concerned",
                content="Sarah, we enabled diagnostics 2 days ago and shared the data. We have not heard back. The restarts are now happening 5-6 times per day and our traders are losing confidence in the platform. We really need this resolved.",
                created_by="Customer",
                created_on=now - timedelta(days=2),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-004-09",
                entry_type=TimelineEntryType.NOTE,
                subject="Diagnostic Review",
                content="Reviewed diagnostics. Seeing node pressure issues, not just pod memory. May need to scale the node pool. Need to test this theory.",
                created_by="Sarah Chen",
                created_on=now - timedelta(days=1),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-004-10",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Losing Patience",
                content="It has been a WEEK and we are no closer to a solution. We have tried everything you suggested and nothing works. Our head of trading is now asking why we chose Azure. I need a concrete resolution plan TODAY or I will need to escalate this.",
                created_by="Customer",
                created_on=now - timedelta(hours=12),
                is_customer_communication=True
            ),
        ]
    )
    cases.append(case4)
    
    # =========================================================================
    # CASE 5: 2-DAY RULE WARNING - Last outbound 3 days ago
    # Tests: 2-day communication rule violation
    # =========================================================================
    case5 = Case(
        id="2501090050007890",
        title="Azure Synapse Analytics cost optimization",
        description="Looking for ways to reduce our Azure Synapse costs which have been higher than expected.",
        status=CaseStatus.ACTIVE,
        severity=CaseSeverity.SEV_C,
        owner=engineers["eng-001"],
        customer=customers["cust-005"],
        created_on=now - timedelta(days=6),
        modified_on=now - timedelta(days=3),
        timeline=[
            TimelineEntry(
                id="tl-005-01",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Synapse Costs",
                content="Hi, our Azure Synapse costs have been running about 40% higher than we budgeted. We would like help understanding where the costs are coming from and how to optimize.",
                created_by="Customer",
                created_on=now - timedelta(days=6),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-005-02",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="RE: Synapse Costs",
                content="I can definitely help with cost optimization. Could you share access to your Synapse workspace so I can review the workload patterns and identify optimization opportunities?",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=5),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-005-03",
                entry_type=TimelineEntryType.NOTE,
                subject="Initial Note",
                content="Tailspin - Synapse cost optimization. Costs 40% over budget. Requested workspace access to analyze workloads.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=5),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-005-04",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Access Granted",
                content="I have granted you Reader access to our Synapse workspace. Please let me know what you find. Our CFO is asking about this.",
                created_by="Customer",
                created_on=now - timedelta(days=4),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-005-05",
                entry_type=TimelineEntryType.NOTE,
                subject="Analysis Started",
                content="Customer granted workspace access. Starting cost analysis. Will review DWU usage, paused schedules, and query patterns.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=3),
                is_customer_communication=False
            ),
            # NOTE: No customer communication for 3 days - 2-day rule violation
        ]
    )
    cases.append(case5)
    
    # =========================================================================
    # CASE 6: RESOLVED HAPPY - Good outcome, customer satisfied
    # Tests: Example of well-handled case
    # =========================================================================
    case6 = Case(
        id="2501050050002345",
        title="Power BI embedded licensing questions",
        description="Need clarification on Power BI Embedded licensing for our customer-facing analytics portal.",
        status=CaseStatus.RESOLVED,
        severity=CaseSeverity.SEV_C,
        owner=engineers["eng-003"],
        customer=customers["cust-006"],
        created_on=now - timedelta(days=8),
        modified_on=now - timedelta(days=1),
        timeline=[
            TimelineEntry(
                id="tl-006-01",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Licensing Question",
                content="Hi, we are building a customer-facing analytics portal using Power BI Embedded. We are confused about the licensing model. Can you help clarify whether we need per-user licenses or capacity-based licensing?",
                created_by="Customer",
                created_on=now - timedelta(days=8),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-006-02",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="RE: Licensing Question",
                content="Great question! For customer-facing scenarios, you typically want Power BI Embedded with capacity-based licensing. This allows unlimited external users without per-user licenses. Let me explain the options and help you estimate costs.",
                created_by="Marcus Williams",
                created_on=now - timedelta(days=7),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-006-03",
                entry_type=TimelineEntryType.PHONE_CALL,
                subject="Licensing Deep Dive Call",
                content="45-minute call with customer to review licensing options. Walked through A SKUs vs EM SKUs, explained cost model. Customer will use A2 SKU for their expected workload. They appreciated the clear explanation.",
                created_by="Marcus Williams",
                created_on=now - timedelta(days=5),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-006-04",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="Summary and Resources",
                content="Thanks for the great call today! As discussed, here is the summary: 1) Use A2 SKU for capacity, 2) Embed tokens for external users, 3) Auto-pause for cost savings. I attached the documentation we reviewed.",
                created_by="Marcus Williams",
                created_on=now - timedelta(days=5, hours=-2),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-006-05",
                entry_type=TimelineEntryType.NOTE,
                subject="Resolution Note",
                content="Customer understands licensing model. Will proceed with A2 SKU. Provided documentation and cost calculator. Case should be ready to close.",
                created_by="Marcus Williams",
                created_on=now - timedelta(days=5, hours=-2),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-006-06",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Thank You!",
                content="Marcus, thank you so much for your help! The call was incredibly helpful and the documentation you provided answered all our remaining questions. We are moving forward with the A2 SKU as you recommended. This has been an excellent support experience - please close the case.",
                created_by="Customer",
                created_on=now - timedelta(days=2),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-006-07",
                entry_type=TimelineEntryType.NOTE,
                subject="Case Closed",
                content="Customer confirmed satisfaction. Closing case. Excellent outcome.",
                created_by="Marcus Williams",
                created_on=now - timedelta(days=1),
                is_customer_communication=False
            ),
        ]
    )
    cases.append(case6)
    
    # =========================================================================
    # CASE 7: 5-HOUR RULE VIOLATION - Email sent, no notes added
    # Tests: 5-hour email-to-notes rule
    # =========================================================================
    case7 = Case(
        id="2501120050006789",
        title="Azure Front Door WAF rule configuration",
        description="Need help configuring WAF rules for our healthcare API endpoints.",
        status=CaseStatus.ACTIVE,
        severity=CaseSeverity.SEV_B,
        owner=engineers["eng-001"],
        customer=customers["cust-001"],
        created_on=now - timedelta(days=2),
        modified_on=now - timedelta(hours=8),
        timeline=[
            TimelineEntry(
                id="tl-007-01",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="WAF Configuration Help",
                content="We need to configure WAF rules on Azure Front Door for our healthcare APIs. We want to protect against OWASP top 10 but are seeing false positives blocking legitimate traffic. Can you help?",
                created_by="Customer",
                created_on=now - timedelta(days=2),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-007-02",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="RE: WAF Configuration",
                content="I can help with WAF tuning. False positives are common with default rule sets. Can you share which specific rules are triggering? You can find this in the WAF logs under FrontDoorWebApplicationFirewallLog.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=2, hours=-4),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-007-03",
                entry_type=TimelineEntryType.NOTE,
                subject="Initial Triage",
                content="Customer experiencing WAF false positives on healthcare APIs. Requested specific rule IDs from logs.",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(days=2, hours=-5),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-007-04",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Rule IDs",
                content="Here are the rule IDs we are seeing: 942430, 942431, and 949110. These are blocking our JSON payloads that contain patient data.",
                created_by="Customer",
                created_on=now - timedelta(days=1),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-007-05",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="Exclusion Recommendations",
                content="Based on those rule IDs, I recommend creating exclusions for your specific API paths. I have created a detailed guide with the exact exclusion syntax you need. Here are the steps...",
                created_by="Kevin Monteagudo",
                created_on=now - timedelta(hours=8),
                is_customer_communication=False
            ),
            # NOTE: Email sent 8 hours ago but NO NOTES added - 5-hour rule violation
        ]
    )
    cases.append(case7)
    
    # =========================================================================
    # CASE 8: COMPLEX MULTI-PARTY - Third party dependency causing delays
    # Tests: Handling blocked scenarios
    # =========================================================================
    case8 = Case(
        id="2501100050004567",
        title="SAP integration with Azure Data Factory failing",
        description="Our ADF pipeline that connects to SAP has been failing since the SAP upgrade last week. Need help troubleshooting.",
        status=CaseStatus.ACTIVE,
        severity=CaseSeverity.SEV_B,
        owner=engineers["eng-002"],
        customer=customers["cust-002"],
        created_on=now - timedelta(days=5),
        modified_on=now - timedelta(hours=6),
        timeline=[
            TimelineEntry(
                id="tl-008-01",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="ADF-SAP Integration Broken",
                content="Sarah, after our SAP upgrade last week, all our ADF pipelines that pull data from SAP are failing. We get a generic connection error. This is blocking our nightly data warehouse refresh.",
                created_by="Customer",
                created_on=now - timedelta(days=5),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-008-02",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="RE: ADF-SAP Integration",
                content="Sorry to hear about the integration issues. SAP connector issues after upgrades are often related to RFC function changes. Can you share the exact error message and confirm which SAP connector version you are using in your self-hosted IR?",
                created_by="Sarah Chen",
                created_on=now - timedelta(days=5, hours=-3),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-008-03",
                entry_type=TimelineEntryType.NOTE,
                subject="Investigation Start",
                content="Fabrikam - ADF to SAP integration broken after SAP upgrade. Likely RFC or connector compatibility issue. Requested error details and connector version.",
                created_by="Sarah Chen",
                created_on=now - timedelta(days=5, hours=-4),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-008-04",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Error Details",
                content='Error: "RFC_ERROR_SYSTEM_FAILURE - Connection to SAP system failed". We are using SAP connector version 4.1. The self-hosted IR is version 5.28.',
                created_by="Customer",
                created_on=now - timedelta(days=4),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-008-05",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="Connector Update Needed",
                content="The error and your versions suggest you need to update the SAP .NET Connector to version 3.1. The version you have (4.1) may not be compatible with your upgraded SAP system. Here are the steps to update...",
                created_by="Sarah Chen",
                created_on=now - timedelta(days=4, hours=-5),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-008-06",
                entry_type=TimelineEntryType.NOTE,
                subject="Root Cause Identified",
                content="Root cause: SAP .NET Connector version mismatch after SAP upgrade. Customer needs NCo 3.1. Sent update instructions.",
                created_by="Sarah Chen",
                created_on=now - timedelta(days=4, hours=-6),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-008-07",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="SAP Team Blocking",
                content="Sarah, we tried to update the connector but our SAP team says they cannot approve any changes without a full security review. That will take 2 weeks. Is there any workaround? Our data warehouse is now 4 days stale.",
                created_by="Customer",
                created_on=now - timedelta(days=3),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-008-08",
                entry_type=TimelineEntryType.EMAIL_SENT,
                subject="Workaround Options",
                content="I understand the SAP team constraints. Here are two potential workarounds while you wait for approval: 1) Use the OData connector if SAP exposes OData services, 2) Export to flat files and use blob storage as intermediate step. Both avoid the RFC dependency.",
                created_by="Sarah Chen",
                created_on=now - timedelta(days=2),
                is_customer_communication=False
            ),
            TimelineEntry(
                id="tl-008-09",
                entry_type=TimelineEntryType.EMAIL_RECEIVED,
                subject="Workarounds Not Viable",
                content="Unfortunately, neither workaround works for us. SAP OData is not enabled and flat files would require significant pipeline rewrites. We are stuck waiting for SAP team. Can Microsoft help expedite the security review somehow?",
                created_by="Customer",
                created_on=now - timedelta(days=1),
                is_customer_communication=True
            ),
            TimelineEntry(
                id="tl-008-10",
                entry_type=TimelineEntryType.NOTE,
                subject="Blocked on Third Party",
                content="Customer blocked by internal SAP team security review (2 week timeline). Workarounds not viable. Need to help customer communicate urgency to their SAP team or find another option.",
                created_by="Sarah Chen",
                created_on=now - timedelta(hours=6),
                is_customer_communication=False
            ),
        ]
    )
    cases.append(case8)
    
    return cases


# =============================================================================
# Helper functions for the mock DfM client
# =============================================================================

_cached_data = None

def get_mock_data():
    """Get or create cached mock data."""
    global _cached_data
    if _cached_data is None:
        _cached_data = {
            "engineers": {e.id: e for e in get_sample_engineers()},
            "customers": {c.id: c for c in get_sample_customers()},
            "cases": {c.id: c for c in get_sample_cases()},
        }
    return _cached_data


def get_case_by_id(case_id: str) -> Optional[Case]:
    """Get a case by ID."""
    return get_mock_data()["cases"].get(case_id)


def get_cases_by_owner(owner_id: str) -> List[Case]:
    """Get all cases for an engineer."""
    return [c for c in get_mock_data()["cases"].values() if c.owner.id == owner_id]


def get_engineer_by_id(engineer_id: str) -> Optional[Engineer]:
    """Get an engineer by ID."""
    return get_mock_data()["engineers"].get(engineer_id)


def get_all_cases() -> List[Case]:
    """Get all cases."""
    return list(get_mock_data()["cases"].values())
