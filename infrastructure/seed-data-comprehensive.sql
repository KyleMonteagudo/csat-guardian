-- =============================================================================
-- CSAT Guardian - Comprehensive Test Data
-- =============================================================================
-- Run this in Azure Cloud Shell using sqlcmd:
--
-- sqlcmd -S sql-csatguardian-dev.database.windows.net -d sqldb-csatguardian-dev -U sqladmin -P 'YourPassword' -i seed-data-comprehensive.sql
--
-- Schema uses LOWERCASE column names (actual Azure SQL schema)
-- =============================================================================

-- Clear existing data (optional - comment out if you want to keep existing)
DELETE FROM timeline_entries;
DELETE FROM cases;
DELETE FROM customers;
DELETE FROM engineers;
GO

-- =============================================================================
-- ENGINEERS
-- =============================================================================
INSERT INTO engineers (id, name, email, team) VALUES
('eng-001', 'Kevin Monteagudo', 'kmonteagudo@microsoft.com', 'CSS Azure Core'),
('eng-002', 'Sarah Chen', 'schen@microsoft.com', 'CSS Azure Core'),
('eng-003', 'Marcus Williams', 'mwilliams@microsoft.com', 'CSS M365');
GO

-- =============================================================================
-- CUSTOMERS
-- =============================================================================
INSERT INTO customers (id, company, tier) VALUES
('cust-001', 'Contoso Healthcare', 'Premier'),
('cust-002', 'Fabrikam Manufacturing', 'Unified'),
('cust-003', 'Adventure Works Retail', 'Premier'),
('cust-004', 'Northwind Financial', 'Premier'),
('cust-005', 'Tailspin Aerospace', 'Unified'),
('cust-006', 'Wide World Importers', 'Pro');
GO

-- =============================================================================
-- CASE 1: HAPPY CUSTOMER - Good communication, positive sentiment
-- Engineer: Kevin | Customer: Contoso Healthcare
-- This case demonstrates IDEAL behavior
-- =============================================================================
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on)
VALUES (
    'case-001',
    'Azure AD B2C configuration for patient portal',
    'We are implementing Azure AD B2C for our new patient portal and need guidance on best practices for healthcare compliance.',
    'active',
    'medium',
    'eng-001',
    'cust-001',
    DATEADD(day, -5, GETUTCDATE()),
    DATEADD(hour, -4, GETUTCDATE())
);

INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, created_on, is_customer_communication) VALUES
('tl-001-01', 'case-001', 'email_received', 'Initial Request', 
'Hi Kevin, we are starting our Azure AD B2C implementation for our patient portal. We need to ensure HIPAA compliance. Can you help us understand the best practices? We have a go-live target of February 15th.',
'Customer', DATEADD(day, -5, GETUTCDATE()), 1),

('tl-001-02', 'case-001', 'email_sent', 'RE: Initial Request',
'Hi! Thank you for reaching out. I would be happy to help with your Azure AD B2C implementation. Given your HIPAA requirements and Feb 15 timeline, I suggest we schedule a call this week to review your architecture. I have availability Thursday at 2pm or Friday at 10am. Which works better?',
'Kevin Monteagudo', DATEADD(day, -5, DATEADD(hour, 2, GETUTCDATE())), 0),

('tl-001-03', 'case-001', 'note', 'Internal Note',
'Customer is implementing B2C for healthcare portal. Key requirements: HIPAA compliance, Feb 15 go-live. Will need to review token lifetimes, MFA policies, and audit logging. Scheduling architecture review call.',
'Kevin Monteagudo', DATEADD(day, -5, DATEADD(hour, 3, GETUTCDATE())), 0),

('tl-001-04', 'case-001', 'email_received', 'RE: Initial Request',
'Thursday at 2pm works great! Looking forward to the call. Should we invite our security team as well?',
'Customer', DATEADD(day, -4, GETUTCDATE()), 1),

('tl-001-05', 'case-001', 'phone_call', 'Architecture Review Call',
'Had 45-min call with customer and their security team. Reviewed B2C architecture. Key decisions: 1) Will use custom policies for HIPAA-compliant flows, 2) Implementing MFA for all users, 3) 1-hour token lifetime. Customer very engaged and appreciative. Next step: I will share documentation on custom policies by Monday.',
'Kevin Monteagudo', DATEADD(day, -2, GETUTCDATE()), 0),

('tl-001-06', 'case-001', 'email_sent', 'Documentation as promised',
'Hi team, as discussed on our call, here is the documentation on B2C custom policies for healthcare scenarios. I have also included a sample policy template you can use as a starting point. Let me know if you have questions!',
'Kevin Monteagudo', DATEADD(day, -1, GETUTCDATE()), 0),

('tl-001-07', 'case-001', 'note', 'Follow-up Note',
'Sent custom policy documentation. Customer has everything needed to proceed. Will check in Friday to see if they have questions. On track for Feb 15 go-live.',
'Kevin Monteagudo', DATEADD(day, -1, DATEADD(hour, 1, GETUTCDATE())), 0),

('tl-001-08', 'case-001', 'email_received', 'RE: Documentation',
'Kevin, this is exactly what we needed! The sample template saved us hours of work. We have started implementing and everything is going smoothly. Thank you for the excellent support!',
'Customer', DATEADD(hour, -4, GETUTCDATE()), 1);
GO

-- =============================================================================
-- CASE 2: FRUSTRATED CUSTOMER - Communication gaps, escalation language
-- Engineer: Kevin | Customer: Fabrikam Manufacturing  
-- This case has CSAT RISK - 2-day rule violated, declining sentiment
-- =============================================================================
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on)
VALUES (
    'case-002',
    'Production SQL Server down after patching - CRITICAL',
    'Our production SQL Server went down after applying the monthly patches. We cannot process orders. This is a SEV1 situation affecting $50K/hour in revenue.',
    'active',
    'critical',
    'eng-001',
    'cust-002',
    DATEADD(day, -4, GETUTCDATE()),
    DATEADD(day, -2, GETUTCDATE())
);

INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, created_on, is_customer_communication) VALUES
('tl-002-01', 'case-002', 'email_received', 'URGENT: Production Down',
'Our production SQL Server crashed after patching last night. We CANNOT process any customer orders. This is costing us approximately $50,000 per hour in lost revenue. We need immediate assistance!',
'Customer', DATEADD(day, -4, GETUTCDATE()), 1),

('tl-002-02', 'case-002', 'email_sent', 'RE: URGENT: Production Down',
'I understand the severity and I am treating this as top priority. Can you please share the SQL error logs from the Event Viewer? Also, which specific patches were applied? I will start investigating immediately.',
'Kevin Monteagudo', DATEADD(day, -4, DATEADD(hour, 1, GETUTCDATE())), 0),

('tl-002-03', 'case-002', 'note', 'Initial Investigation',
'SEV1 - Production SQL down after patching. Customer losing $50K/hr. Requested error logs. Need to identify which patch caused the issue.',
'Kevin Monteagudo', DATEADD(day, -4, DATEADD(hour, 1, GETUTCDATE())), 0),

('tl-002-04', 'case-002', 'email_received', 'Logs Attached',
'Here are the error logs. The crash happens on startup. Our DBA tried rolling back the patches but the server still wont start. PLEASE HURRY.',
'Customer', DATEADD(day, -4, DATEADD(hour, 2, GETUTCDATE())), 1),

('tl-002-05', 'case-002', 'note', 'Log Analysis',
'Reviewed logs - seeing corruption in master database after patch rollback attempt. This is complex. Escalating to SQL PG for guidance. Will update customer.',
'Kevin Monteagudo', DATEADD(day, -4, DATEADD(hour, 4, GETUTCDATE())), 0),

('tl-002-06', 'case-002', 'email_received', 'Still Waiting',
'It has been 6 hours since my last email. What is the status? Our CEO is asking for answers. We have had to tell customers we cannot fulfill their orders. This is becoming a nightmare.',
'Customer', DATEADD(day, -4, DATEADD(hour, 8, GETUTCDATE())), 1),

('tl-002-07', 'case-002', 'email_received', 'Day 2 - No Resolution',
'This is now DAY 2 and we still do not have our production system back. I have escalated internally to our VP who is now involved. We need to understand what is being done and when this will be resolved. The lack of communication is unacceptable.',
'Customer', DATEADD(day, -3, GETUTCDATE()), 1),

('tl-002-08', 'case-002', 'note', 'Escalation Note',
'Customer escalated to their VP. Still waiting on SQL PG response. Need to provide update to customer today.',
'Kevin Monteagudo', DATEADD(day, -3, DATEADD(hour, 2, GETUTCDATE())), 0),

('tl-002-09', 'case-002', 'email_received', 'Considering Legal Action',
'I am absolutely furious. THREE DAYS of downtime, over $3.6 MILLION in lost revenue, and I have received ONE email from Microsoft. I am escalating this to our legal team and will be filing a formal complaint. I want to speak with your manager IMMEDIATELY. This level of support is completely unacceptable for a Premier customer.',
'Customer', DATEADD(day, -2, GETUTCDATE()), 1);
GO

-- =============================================================================
-- CASE 3: 7-DAY RULE BREACH - No notes in 8 days
-- Engineer: Kevin | Customer: Adventure Works
-- This case violates the 7-day notes rule
-- =============================================================================
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on)
VALUES (
    'case-003',
    'Azure DevOps pipeline optimization inquiry',
    'We would like guidance on optimizing our Azure DevOps pipelines for faster build times.',
    'active',
    'low',
    'eng-001',
    'cust-003',
    DATEADD(day, -12, GETUTCDATE()),
    DATEADD(day, -8, GETUTCDATE())
);

INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, created_on, is_customer_communication) VALUES
('tl-003-01', 'case-003', 'email_received', 'Pipeline Optimization',
'Hi, our Azure DevOps pipelines are taking 45 minutes to complete. We would like to get them under 15 minutes. Can you help us identify optimization opportunities?',
'Customer', DATEADD(day, -12, GETUTCDATE()), 1),

('tl-003-02', 'case-003', 'email_sent', 'RE: Pipeline Optimization',
'Happy to help! To provide targeted recommendations, could you share your pipeline YAML file and let me know what types of builds you are running (Docker, .NET, Node.js, etc.)?',
'Kevin Monteagudo', DATEADD(day, -11, GETUTCDATE()), 0),

('tl-003-03', 'case-003', 'note', 'Initial Note',
'Customer wants to optimize DevOps pipelines from 45min to 15min. Requested pipeline YAML and build type info. Will analyze and provide recommendations once received.',
'Kevin Monteagudo', DATEADD(day, -11, GETUTCDATE()), 0),

('tl-003-04', 'case-003', 'email_received', 'Pipeline Files',
'Here is our main pipeline YAML. We are building a .NET 6 application with Docker containers. The YAML is attached.',
'Customer', DATEADD(day, -10, GETUTCDATE()), 1),

('tl-003-05', 'case-003', 'note', 'Analysis Note',
'Received pipeline YAML. Initial review shows several optimization opportunities: parallel jobs, caching, and agent pool changes. Will document recommendations.',
'Kevin Monteagudo', DATEADD(day, -8, GETUTCDATE()), 0);

-- NOTE: No activity for 8 days after this - 7-day rule BREACH
GO

-- =============================================================================
-- CASE 4: DECLINING SENTIMENT - Started positive, trending negative
-- Engineer: Sarah | Customer: Northwind Financial
-- Shows sentiment deterioration over time
-- =============================================================================
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on)
VALUES (
    'case-004',
    'Azure Kubernetes Service intermittent pod failures',
    'We are experiencing random pod restarts in our AKS cluster. Happening 2-3 times per day affecting our trading platform.',
    'active',
    'high',
    'eng-002',
    'cust-004',
    DATEADD(day, -7, GETUTCDATE()),
    DATEADD(hour, -12, GETUTCDATE())
);

INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, created_on, is_customer_communication) VALUES
('tl-004-01', 'case-004', 'email_received', 'AKS Pod Issues',
'Hi Sarah, we have been seeing intermittent pod restarts in our production AKS cluster. It is happening 2-3 times daily and affecting our trading platform. We would appreciate your help investigating.',
'Customer', DATEADD(day, -7, GETUTCDATE()), 1),

('tl-004-02', 'case-004', 'email_sent', 'RE: AKS Pod Issues',
'Thank you for reporting this. Pod restarts can have several causes. To help diagnose, could you run kubectl describe pod on one of the affected pods and share the output? Also, please share any relevant logs from kubectl logs.',
'Sarah Chen', DATEADD(day, -7, DATEADD(hour, 3, GETUTCDATE())), 0),

('tl-004-03', 'case-004', 'note', 'Initial Assessment',
'Northwind Financial - AKS pod restart issue affecting trading platform. High priority due to financial impact. Requested pod descriptions and logs.',
'Sarah Chen', DATEADD(day, -7, DATEADD(hour, 3, GETUTCDATE())), 0),

('tl-004-04', 'case-004', 'email_received', 'Logs Provided',
'Here are the pod descriptions and logs as requested. We really hope you can help us figure this out quickly.',
'Customer', DATEADD(day, -6, GETUTCDATE()), 1),

('tl-004-05', 'case-004', 'email_sent', 'Initial Findings',
'Looking at the logs, I see OOMKilled events which indicates your pods are running out of memory. I recommend increasing the memory limits in your deployment. I will send specific recommendations shortly.',
'Sarah Chen', DATEADD(day, -5, GETUTCDATE()), 0),

('tl-004-06', 'case-004', 'email_received', 'Tried Your Suggestion',
'We increased memory limits as you suggested but the restarts are still happening. In fact, they seem to be happening more frequently now. Any other ideas?',
'Customer', DATEADD(day, -4, GETUTCDATE()), 1),

('tl-004-07', 'case-004', 'email_sent', 'Additional Analysis',
'I apologize that the initial fix did not work. Let me dig deeper. Can you enable diagnostic logs and share the AKS cluster diagnostics?',
'Sarah Chen', DATEADD(day, -4, DATEADD(hour, 6, GETUTCDATE())), 0),

('tl-004-08', 'case-004', 'email_received', 'Getting Concerned',
'Sarah, we enabled diagnostics 2 days ago and shared the data. We have not heard back. The restarts are now happening 5-6 times per day and our traders are losing confidence in the platform. We really need this resolved.',
'Customer', DATEADD(day, -2, GETUTCDATE()), 1),

('tl-004-09', 'case-004', 'note', 'Diagnostic Review',
'Reviewed diagnostics. Seeing node pressure issues, not just pod memory. May need to scale the node pool. Need to test this theory.',
'Sarah Chen', DATEADD(day, -1, GETUTCDATE()), 0),

('tl-004-10', 'case-004', 'email_received', 'Losing Patience',
'It has been a WEEK and we are no closer to a solution. We have tried everything you suggested and nothing works. Our head of trading is now asking why we chose Azure. I need a concrete resolution plan TODAY or I will need to escalate this.',
'Customer', DATEADD(hour, -12, GETUTCDATE()), 1);
GO

-- =============================================================================
-- CASE 5: 2-DAY RULE WARNING - Last outbound 3 days ago
-- Engineer: Kevin | Customer: Tailspin Aerospace
-- Communication gap - customer waiting
-- =============================================================================
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on)
VALUES (
    'case-005',
    'Azure Synapse Analytics cost optimization',
    'Looking for ways to reduce our Azure Synapse costs which have been higher than expected.',
    'active',
    'medium',
    'eng-001',
    'cust-005',
    DATEADD(day, -6, GETUTCDATE()),
    DATEADD(day, -3, GETUTCDATE())
);

INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, created_on, is_customer_communication) VALUES
('tl-005-01', 'case-005', 'email_received', 'Synapse Costs',
'Hi, our Azure Synapse costs have been running about 40% higher than we budgeted. We would like help understanding where the costs are coming from and how to optimize.',
'Customer', DATEADD(day, -6, GETUTCDATE()), 1),

('tl-005-02', 'case-005', 'email_sent', 'RE: Synapse Costs',
'I can definitely help with cost optimization. Could you share access to your Synapse workspace so I can review the workload patterns and identify optimization opportunities?',
'Kevin Monteagudo', DATEADD(day, -5, GETUTCDATE()), 0),

('tl-005-03', 'case-005', 'note', 'Initial Note',
'Tailspin - Synapse cost optimization. Costs 40% over budget. Requested workspace access to analyze workloads.',
'Kevin Monteagudo', DATEADD(day, -5, GETUTCDATE()), 0),

('tl-005-04', 'case-005', 'email_received', 'Access Granted',
'I have granted you Reader access to our Synapse workspace. Please let me know what you find. Our CFO is asking about this.',
'Customer', DATEADD(day, -4, GETUTCDATE()), 1),

('tl-005-05', 'case-005', 'note', 'Analysis Started',
'Customer granted workspace access. Starting cost analysis. Will review DWU usage, paused schedules, and query patterns.',
'Kevin Monteagudo', DATEADD(day, -3, GETUTCDATE()), 0);

-- NOTE: No customer communication for 3 days - 2-day rule violation
GO

-- =============================================================================
-- CASE 6: RESOLVED HAPPY - Good outcome, customer satisfied
-- Engineer: Marcus | Customer: Wide World Importers
-- Example of a well-handled case
-- =============================================================================
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on)
VALUES (
    'case-006',
    'Power BI embedded licensing questions',
    'Need clarification on Power BI Embedded licensing for our customer-facing analytics portal.',
    'resolved',
    'medium',
    'eng-003',
    'cust-006',
    DATEADD(day, -8, GETUTCDATE()),
    DATEADD(day, -1, GETUTCDATE())
);

INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, created_on, is_customer_communication) VALUES
('tl-006-01', 'case-006', 'email_received', 'Licensing Question',
'Hi, we are building a customer-facing analytics portal using Power BI Embedded. We are confused about the licensing model. Can you help clarify whether we need per-user licenses or capacity-based licensing?',
'Customer', DATEADD(day, -8, GETUTCDATE()), 1),

('tl-006-02', 'case-006', 'email_sent', 'RE: Licensing Question',
'Great question! For customer-facing scenarios, you typically want Power BI Embedded with capacity-based licensing. This allows unlimited external users without per-user licenses. Let me explain the options and help you estimate costs.',
'Marcus Williams', DATEADD(day, -7, GETUTCDATE()), 0),

('tl-006-03', 'case-006', 'phone_call', 'Licensing Deep Dive Call',
'45-minute call with customer to review licensing options. Walked through A SKUs vs EM SKUs, explained cost model. Customer will use A2 SKU for their expected workload. They appreciated the clear explanation.',
'Marcus Williams', DATEADD(day, -5, GETUTCDATE()), 0),

('tl-006-04', 'case-006', 'email_sent', 'Summary and Resources',
'Thanks for the great call today! As discussed, here is the summary: 1) Use A2 SKU for capacity, 2) Embed tokens for external users, 3) Auto-pause for cost savings. I attached the documentation we reviewed.',
'Marcus Williams', DATEADD(day, -5, DATEADD(hour, 2, GETUTCDATE())), 0),

('tl-006-05', 'case-006', 'note', 'Resolution Note',
'Customer understands licensing model. Will proceed with A2 SKU. Provided documentation and cost calculator. Case should be ready to close.',
'Marcus Williams', DATEADD(day, -5, DATEADD(hour, 2, GETUTCDATE())), 0),

('tl-006-06', 'case-006', 'email_received', 'Thank You!',
'Marcus, thank you so much for your help! The call was incredibly helpful and the documentation you provided answered all our remaining questions. We are moving forward with the A2 SKU as you recommended. This has been an excellent support experience - please close the case.',
'Customer', DATEADD(day, -2, GETUTCDATE()), 1),

('tl-006-07', 'case-006', 'note', 'Case Closed',
'Customer confirmed satisfaction. Closing case. Excellent outcome.',
'Marcus Williams', DATEADD(day, -1, GETUTCDATE()), 0);
GO

-- =============================================================================
-- CASE 7: 5-HOUR RULE VIOLATION - Email sent, no notes added
-- Engineer: Kevin | Customer: Contoso Healthcare  
-- Email sent 8 hours ago with no follow-up notes
-- =============================================================================
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on)
VALUES (
    'case-007',
    'Azure Front Door WAF rule configuration',
    'Need help configuring WAF rules for our healthcare API endpoints.',
    'active',
    'high',
    'eng-001',
    'cust-001',
    DATEADD(day, -2, GETUTCDATE()),
    DATEADD(hour, -8, GETUTCDATE())
);

INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, created_on, is_customer_communication) VALUES
('tl-007-01', 'case-007', 'email_received', 'WAF Configuration Help',
'We need to configure WAF rules on Azure Front Door for our healthcare APIs. We want to protect against OWASP top 10 but are seeing false positives blocking legitimate traffic. Can you help?',
'Customer', DATEADD(day, -2, GETUTCDATE()), 1),

('tl-007-02', 'case-007', 'email_sent', 'RE: WAF Configuration',
'I can help with WAF tuning. False positives are common with default rule sets. Can you share which specific rules are triggering? You can find this in the WAF logs under FrontDoorWebApplicationFirewallLog.',
'Kevin Monteagudo', DATEADD(day, -2, DATEADD(hour, 4, GETUTCDATE())), 0),

('tl-007-03', 'case-007', 'note', 'Initial Triage',
'Customer experiencing WAF false positives on healthcare APIs. Requested specific rule IDs from logs.',
'Kevin Monteagudo', DATEADD(day, -2, DATEADD(hour, 5, GETUTCDATE())), 0),

('tl-007-04', 'case-007', 'email_received', 'Rule IDs',
'Here are the rule IDs we are seeing: 942430, 942431, and 949110. These are blocking our JSON payloads that contain patient data.',
'Customer', DATEADD(day, -1, GETUTCDATE()), 1),

('tl-007-05', 'case-007', 'email_sent', 'Exclusion Recommendations',
'Based on those rule IDs, I recommend creating exclusions for your specific API paths. I have created a detailed guide with the exact exclusion syntax you need. Here are the steps...',
'Kevin Monteagudo', DATEADD(hour, -8, GETUTCDATE()), 0);

-- NOTE: Email sent 8 hours ago but NO NOTES added - 5-hour rule violation
GO

-- =============================================================================
-- CASE 8: COMPLEX MULTI-PARTY - Third party dependency causing delays
-- Engineer: Sarah | Customer: Fabrikam Manufacturing
-- Shows complexity with external dependencies
-- =============================================================================
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on)
VALUES (
    'case-008',
    'SAP integration with Azure Data Factory failing',
    'Our ADF pipeline that connects to SAP has been failing since the SAP upgrade last week. Need help troubleshooting.',
    'active',
    'high',
    'eng-002',
    'cust-002',
    DATEADD(day, -5, GETUTCDATE()),
    DATEADD(hour, -6, GETUTCDATE())
);

INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, created_on, is_customer_communication) VALUES
('tl-008-01', 'case-008', 'email_received', 'ADF-SAP Integration Broken',
'Sarah, after our SAP upgrade last week, all our ADF pipelines that pull data from SAP are failing. We get a generic connection error. This is blocking our nightly data warehouse refresh.',
'Customer', DATEADD(day, -5, GETUTCDATE()), 1),

('tl-008-02', 'case-008', 'email_sent', 'RE: ADF-SAP Integration',
'Sorry to hear about the integration issues. SAP connector issues after upgrades are often related to RFC function changes. Can you share the exact error message and confirm which SAP connector version you are using in your self-hosted IR?',
'Sarah Chen', DATEADD(day, -5, DATEADD(hour, 3, GETUTCDATE())), 0),

('tl-008-03', 'case-008', 'note', 'Investigation Start',
'Fabrikam - ADF to SAP integration broken after SAP upgrade. Likely RFC or connector compatibility issue. Requested error details and connector version.',
'Sarah Chen', DATEADD(day, -5, DATEADD(hour, 4, GETUTCDATE())), 0),

('tl-008-04', 'case-008', 'email_received', 'Error Details',
'Error: "RFC_ERROR_SYSTEM_FAILURE - Connection to SAP system failed". We are using SAP connector version 4.1. The self-hosted IR is version 5.28.',
'Customer', DATEADD(day, -4, GETUTCDATE()), 1),

('tl-008-05', 'case-008', 'email_sent', 'Connector Update Needed',
'The error and your versions suggest you need to update the SAP .NET Connector to version 3.1. The version you have (4.1) may not be compatible with your upgraded SAP system. Here are the steps to update...',
'Sarah Chen', DATEADD(day, -4, DATEADD(hour, 5, GETUTCDATE())), 0),

('tl-008-06', 'case-008', 'note', 'Root Cause Identified',
'Root cause: SAP .NET Connector version mismatch after SAP upgrade. Customer needs NCo 3.1. Sent update instructions.',
'Sarah Chen', DATEADD(day, -4, DATEADD(hour, 6, GETUTCDATE())), 0),

('tl-008-07', 'case-008', 'email_received', 'SAP Team Blocking',
'Sarah, we tried to update the connector but our SAP team says they cannot approve any changes without a full security review. That will take 2 weeks. Is there any workaround? Our data warehouse is now 4 days stale.',
'Customer', DATEADD(day, -3, GETUTCDATE()), 1),

('tl-008-08', 'case-008', 'email_sent', 'Workaround Options',
'I understand the SAP team constraints. Here are two potential workarounds while you wait for approval: 1) Use the OData connector if SAP exposes OData services, 2) Export to flat files and use blob storage as intermediate step. Both avoid the RFC dependency.',
'Sarah Chen', DATEADD(day, -2, GETUTCDATE()), 0),

('tl-008-09', 'case-008', 'email_received', 'Workarounds Not Viable',
'Unfortunately, neither workaround works for us. SAP OData is not enabled and flat files would require significant pipeline rewrites. We are stuck waiting for SAP team. Can Microsoft help expedite the security review somehow?',
'Customer', DATEADD(day, -1, GETUTCDATE()), 1),

('tl-008-10', 'case-008', 'note', 'Blocked on Third Party',
'Customer blocked by internal SAP team security review (2 week timeline). Workarounds not viable. Need to help customer communicate urgency to their SAP team or find another option.',
'Sarah Chen', DATEADD(hour, -6, GETUTCDATE()), 0);
GO

PRINT 'Seed data loaded successfully!';
PRINT 'Cases created: 8';
PRINT 'Engineers created: 3';
PRINT 'Customers created: 6';
GO
