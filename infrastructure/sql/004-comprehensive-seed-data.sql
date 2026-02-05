-- =============================================================================
-- CSAT Guardian - Comprehensive Seed Data (Full Quarter)
-- =============================================================================
-- This script creates realistic test data spanning a full quarter (90 days)
-- with 50+ cases across multiple engineers showing various sentiment patterns
-- =============================================================================

-- Clear existing data in reverse dependency order
DELETE FROM conversation_messages;
DELETE FROM conversations;
DELETE FROM case_analyses;
DELETE FROM communication_metrics;
DELETE FROM rule_violations;
DELETE FROM notifications;
DELETE FROM engineer_metrics;
DELETE FROM manager_alert_queue;
DELETE FROM timeline_entries;
DELETE FROM cases;
DELETE FROM customers;
DELETE FROM engineers;
DELETE FROM feedback;
GO

-- =============================================================================
-- ENGINEERS (CSS Support Team)
-- =============================================================================
INSERT INTO engineers (id, name, email, team, manager_id) VALUES
-- Team 1 - Azure Platform Support
('eng-001', 'Sarah Chen', 'sarchen@microsoft.com', 'Azure Platform', 'mgr-001'),
('eng-002', 'Marcus Johnson', 'marjohn@microsoft.com', 'Azure Platform', 'mgr-001'),
('eng-003', 'Emily Rodriguez', 'emrod@microsoft.com', 'Azure Platform', 'mgr-001'),
('eng-004', 'James Kim', 'jamkim@microsoft.com', 'Azure Platform', 'mgr-001'),

-- Team 2 - Azure Data Services
('eng-005', 'Priya Patel', 'prpatel@microsoft.com', 'Azure Data', 'mgr-002'),
('eng-006', 'David Wang', 'dawang@microsoft.com', 'Azure Data', 'mgr-002'),
('eng-007', 'Lisa Thompson', 'lithomp@microsoft.com', 'Azure Data', 'mgr-002'),

-- Team 3 - M365 Support
('eng-008', 'Alex Martinez', 'almart@microsoft.com', 'M365 Support', 'mgr-003'),
('eng-009', 'Jennifer Lee', 'jenlee@microsoft.com', 'M365 Support', 'mgr-003'),
('eng-010', 'Robert Brown', 'robbro@microsoft.com', 'M365 Support', 'mgr-003'),

-- Managers
('mgr-001', 'Michael Scott', 'micscott@microsoft.com', 'Management', NULL),
('mgr-002', 'Angela Martin', 'angmart@microsoft.com', 'Management', NULL),
('mgr-003', 'Jim Halpert', 'jimhal@microsoft.com', 'Management', NULL);
GO

-- =============================================================================
-- CUSTOMERS (50+ Companies)
-- =============================================================================
INSERT INTO customers (id, company, tier) VALUES
-- Premier Tier
('cust-001', 'Contoso Financial Services', 'Premier'),
('cust-002', 'Fabrikam Industries', 'Premier'),
('cust-003', 'Northwind Traders', 'Premier'),
('cust-004', 'Adventure Works Cycles', 'Premier'),
('cust-005', 'Wide World Importers', 'Premier'),
('cust-006', 'Trey Research', 'Premier'),
('cust-007', 'The Phone Company', 'Premier'),
('cust-008', 'Coho Vineyard', 'Premier'),

-- Unified Tier
('cust-009', 'Tailspin Toys', 'Unified'),
('cust-010', 'Wingtip Toys', 'Unified'),
('cust-011', 'Fourth Coffee', 'Unified'),
('cust-012', 'Graphic Design Institute', 'Unified'),
('cust-013', 'Litware Inc', 'Unified'),
('cust-014', 'Proseware Inc', 'Unified'),
('cust-015', 'Lucerne Publishing', 'Unified'),
('cust-016', 'Margie Travel', 'Unified'),
('cust-017', 'Consolidated Messenger', 'Unified'),
('cust-018', 'Blue Yonder Airlines', 'Unified'),

-- Professional Tier
('cust-019', 'A Datum Corporation', 'Professional'),
('cust-020', 'Bellows College', 'Professional'),
('cust-021', 'Best For You Organics', 'Professional'),
('cust-022', 'City Power & Light', 'Professional'),
('cust-023', 'Humongous Insurance', 'Professional'),
('cust-024', 'VanArsdel Ltd', 'Professional'),
('cust-025', 'Woodgrove Bank', 'Professional');
GO

-- =============================================================================
-- CASES - Full Quarter (90 days of data, 60 cases)
-- =============================================================================
-- Mix of severities, statuses, and sentiment patterns

-- Week 1-2: Cases from 80-90 days ago (resolved)
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on) VALUES
('case-001', 'Azure SQL Database connection timeout issues', 'Customer experiencing intermittent connection failures to Azure SQL', 'resolved', 'sev_b', 'eng-001', 'cust-001', DATEADD(day, -88, GETUTCDATE()), DATEADD(day, -80, GETUTCDATE())),
('case-002', 'VM scale set deployment failures', 'VMSS deployments failing with quota exceeded errors', 'resolved', 'sev_b', 'eng-002', 'cust-002', DATEADD(day, -87, GETUTCDATE()), DATEADD(day, -82, GETUTCDATE())),
('case-003', 'Storage account access denied errors', 'Blob storage returning 403 errors despite valid SAS tokens', 'resolved', 'sev_c', 'eng-003', 'cust-003', DATEADD(day, -86, GETUTCDATE()), DATEADD(day, -81, GETUTCDATE())),
('case-004', 'Teams meeting recording unavailable', 'Meeting recordings not appearing in OneDrive', 'resolved', 'sev_c', 'eng-008', 'cust-004', DATEADD(day, -85, GETUTCDATE()), DATEADD(day, -79, GETUTCDATE())),
('case-005', 'Power BI refresh failures', 'Scheduled refresh failing with gateway timeout', 'resolved', 'sev_b', 'eng-005', 'cust-005', DATEADD(day, -84, GETUTCDATE()), DATEADD(day, -78, GETUTCDATE()));

-- Week 3-4: Cases from 60-80 days ago
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on) VALUES
('case-006', 'AKS cluster node pool scaling issues', 'Autoscaler not responding to CPU thresholds', 'resolved', 'sev_a', 'eng-001', 'cust-001', DATEADD(day, -75, GETUTCDATE()), DATEADD(day, -70, GETUTCDATE())),
('case-007', 'Azure AD conditional access blocking users', 'Legitimate users blocked by CA policies', 'resolved', 'sev_a', 'eng-004', 'cust-006', DATEADD(day, -73, GETUTCDATE()), DATEADD(day, -68, GETUTCDATE())),
('case-008', 'Cosmos DB high RU consumption', 'Unexpected RU usage causing throttling', 'resolved', 'sev_b', 'eng-006', 'cust-007', DATEADD(day, -72, GETUTCDATE()), DATEADD(day, -65, GETUTCDATE())),
('case-009', 'SharePoint site collection deletion request', 'Need to recover accidentally deleted site', 'resolved', 'sev_c', 'eng-009', 'cust-008', DATEADD(day, -71, GETUTCDATE()), DATEADD(day, -66, GETUTCDATE())),
('case-010', 'Exchange Online mail flow delays', 'Emails delayed by 4+ hours intermittently', 'resolved', 'sev_b', 'eng-010', 'cust-009', DATEADD(day, -70, GETUTCDATE()), DATEADD(day, -63, GETUTCDATE())),
('case-011', 'Azure Functions cold start latency', 'Functions taking 10+ seconds to start', 'resolved', 'sev_c', 'eng-002', 'cust-010', DATEADD(day, -68, GETUTCDATE()), DATEADD(day, -60, GETUTCDATE())),
('case-012', 'Logic Apps connector authentication failures', 'OAuth refresh failing for Salesforce connector', 'resolved', 'sev_b', 'eng-003', 'cust-011', DATEADD(day, -66, GETUTCDATE()), DATEADD(day, -58, GETUTCDATE())),
('case-013', 'Synapse Analytics workspace access issues', 'Users cannot access Synapse studio', 'resolved', 'sev_b', 'eng-007', 'cust-012', DATEADD(day, -64, GETUTCDATE()), DATEADD(day, -55, GETUTCDATE())),
('case-014', 'Intune device enrollment failures', 'Windows autopilot enrollment stuck at 50%', 'resolved', 'sev_b', 'eng-008', 'cust-013', DATEADD(day, -62, GETUTCDATE()), DATEADD(day, -54, GETUTCDATE()));

-- Week 5-6: Cases from 40-60 days ago
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on) VALUES
('case-015', 'Azure DevOps pipeline agent issues', 'Self-hosted agents going offline randomly', 'resolved', 'sev_b', 'eng-001', 'cust-014', DATEADD(day, -55, GETUTCDATE()), DATEADD(day, -48, GETUTCDATE())),
('case-016', 'Application Gateway 502 errors', 'Backend health probe failing intermittently', 'resolved', 'sev_a', 'eng-004', 'cust-015', DATEADD(day, -53, GETUTCDATE()), DATEADD(day, -45, GETUTCDATE())),
('case-017', 'Data Factory pipeline scheduling issues', 'Pipelines not triggering at scheduled times', 'resolved', 'sev_c', 'eng-005', 'cust-016', DATEADD(day, -52, GETUTCDATE()), DATEADD(day, -44, GETUTCDATE())),
('case-018', 'Event Hub throughput exceeded', 'Messages being throttled during peak hours', 'resolved', 'sev_b', 'eng-006', 'cust-017', DATEADD(day, -50, GETUTCDATE()), DATEADD(day, -42, GETUTCDATE())),
('case-019', 'OneDrive sync client conflicts', 'Multiple users experiencing sync conflicts', 'resolved', 'sev_c', 'eng-009', 'cust-018', DATEADD(day, -48, GETUTCDATE()), DATEADD(day, -40, GETUTCDATE())),
('case-020', 'Service Bus queue deadlettering', 'Messages unexpectedly going to deadletter queue', 'resolved', 'sev_b', 'eng-002', 'cust-019', DATEADD(day, -46, GETUTCDATE()), DATEADD(day, -38, GETUTCDATE())),
('case-021', 'Key Vault access policy conflicts', 'RBAC and access policies conflicting', 'resolved', 'sev_c', 'eng-003', 'cust-020', DATEADD(day, -44, GETUTCDATE()), DATEADD(day, -36, GETUTCDATE())),
('case-022', 'Azure Monitor alert not firing', 'Critical CPU alert not triggering notifications', 'resolved', 'sev_a', 'eng-007', 'cust-021', DATEADD(day, -42, GETUTCDATE()), DATEADD(day, -35, GETUTCDATE()));

-- Week 7-8: Cases from 20-40 days ago (mix of resolved and active)
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on) VALUES
('case-023', 'VNet peering connectivity issues', 'Traffic not flowing between peered VNets', 'resolved', 'sev_b', 'eng-001', 'cust-022', DATEADD(day, -35, GETUTCDATE()), DATEADD(day, -28, GETUTCDATE())),
('case-024', 'Azure Backup restore failure', 'VM restore failing with cryptic error', 'resolved', 'sev_a', 'eng-004', 'cust-023', DATEADD(day, -33, GETUTCDATE()), DATEADD(day, -25, GETUTCDATE())),
('case-025', 'Stream Analytics job lag', 'Output delay exceeding 5 minutes', 'active', 'sev_b', 'eng-005', 'cust-024', DATEADD(day, -32, GETUTCDATE()), DATEADD(day, -5, GETUTCDATE())),
('case-026', 'Teams voice quality issues', 'Echo and latency on PSTN calls', 'resolved', 'sev_b', 'eng-008', 'cust-025', DATEADD(day, -30, GETUTCDATE()), DATEADD(day, -22, GETUTCDATE())),
('case-027', 'Cognitive Services rate limiting', 'OpenAI calls being throttled despite quota', 'active', 'sev_b', 'eng-006', 'cust-001', DATEADD(day, -28, GETUTCDATE()), DATEADD(day, -3, GETUTCDATE())),
('case-028', 'Azure Arc onboarding failures', 'On-prem servers not connecting to Arc', 'active', 'sev_c', 'eng-002', 'cust-002', DATEADD(day, -26, GETUTCDATE()), DATEADD(day, -4, GETUTCDATE())),
('case-029', 'Power Automate approval workflow broken', 'Approval emails not being sent', 'resolved', 'sev_c', 'eng-009', 'cust-003', DATEADD(day, -25, GETUTCDATE()), DATEADD(day, -18, GETUTCDATE())),
('case-030', 'SQL Managed Instance performance', 'Query performance degraded after migration', 'active', 'sev_b', 'eng-007', 'cust-004', DATEADD(day, -24, GETUTCDATE()), DATEADD(day, -2, GETUTCDATE())),
('case-031', 'Defender for Cloud false positives', 'Security alerts for legitimate traffic', 'resolved', 'sev_c', 'eng-003', 'cust-005', DATEADD(day, -23, GETUTCDATE()), DATEADD(day, -15, GETUTCDATE())),
('case-032', 'Azure Front Door routing issues', 'Origin selection not following rules', 'active', 'sev_b', 'eng-001', 'cust-006', DATEADD(day, -22, GETUTCDATE()), DATEADD(day, -1, GETUTCDATE()));

-- Week 9-10: Cases from 7-20 days ago (mostly active)
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on) VALUES
('case-033', 'Azure Container Apps scaling failure', 'Revision not scaling beyond 2 replicas', 'active', 'sev_b', 'eng-004', 'cust-007', DATEADD(day, -18, GETUTCDATE()), DATEADD(day, -2, GETUTCDATE())),
('case-034', 'Purview data scanning errors', 'Scans failing on blob storage account', 'active', 'sev_c', 'eng-005', 'cust-008', DATEADD(day, -17, GETUTCDATE()), DATEADD(day, -3, GETUTCDATE())),
('case-035', 'Graph API permission issues', 'App registration cannot access user data', 'active', 'sev_b', 'eng-010', 'cust-009', DATEADD(day, -16, GETUTCDATE()), DATEADD(day, -1, GETUTCDATE())),
('case-036', 'Azure IoT Hub device provisioning', 'DPS not enrolling devices correctly', 'active', 'sev_c', 'eng-006', 'cust-010', DATEADD(day, -15, GETUTCDATE()), DATEADD(day, -4, GETUTCDATE())),
('case-037', 'Static Web Apps deployment failures', 'GitHub Actions workflow failing', 'resolved', 'sev_c', 'eng-002', 'cust-011', DATEADD(day, -14, GETUTCDATE()), DATEADD(day, -10, GETUTCDATE())),
('case-038', 'Azure API Management latency', 'API responses taking 5+ seconds', 'active', 'sev_a', 'eng-001', 'cust-012', DATEADD(day, -13, GETUTCDATE()), DATEADD(day, -1, GETUTCDATE())),
('case-039', 'Sentinel alert rules not matching', 'KQL queries returning no results', 'active', 'sev_b', 'eng-003', 'cust-013', DATEADD(day, -12, GETUTCDATE()), DATEADD(day, -2, GETUTCDATE())),
('case-040', 'Dynamics 365 integration broken', 'Power Platform connector failing', 'active', 'sev_b', 'eng-008', 'cust-014', DATEADD(day, -11, GETUTCDATE()), DATEADD(day, -3, GETUTCDATE())),
('case-041', 'Azure AD B2C custom policy error', 'User journey failing at MFA step', 'active', 'sev_b', 'eng-004', 'cust-015', DATEADD(day, -10, GETUTCDATE()), DATEADD(day, -1, GETUTCDATE())),
('case-042', 'Load Balancer health probe issues', 'Backend instances showing unhealthy', 'active', 'sev_a', 'eng-007', 'cust-016', DATEADD(day, -9, GETUTCDATE()), DATEADD(day, -1, GETUTCDATE())),
('case-043', 'Teams app permission consent', 'Admin consent not propagating', 'active', 'sev_c', 'eng-009', 'cust-017', DATEADD(day, -8, GETUTCDATE()), DATEADD(day, -2, GETUTCDATE()));

-- Week 11-12: Recent cases (last 7 days)
INSERT INTO cases (id, title, description, status, priority, owner_id, customer_id, created_on, modified_on) VALUES
('case-044', 'Azure Kubernetes ingress 503 errors', 'Nginx ingress returning 503 for all routes', 'active', 'sev_a', 'eng-001', 'cust-018', DATEADD(day, -6, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-045', 'Databricks cluster start failures', 'Cluster cannot acquire nodes from pool', 'active', 'sev_b', 'eng-005', 'cust-019', DATEADD(day, -5, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-046', 'Azure Files performance degradation', 'SMB latency exceeding 100ms', 'active', 'sev_b', 'eng-006', 'cust-020', DATEADD(day, -5, GETUTCDATE()), DATEADD(day, -1, GETUTCDATE())),
('case-047', 'Private Endpoint DNS resolution', 'On-prem cannot resolve private endpoint', 'active', 'sev_b', 'eng-002', 'cust-021', DATEADD(day, -4, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-048', 'Azure Firewall rule processing', 'Network rules not being evaluated', 'active', 'sev_a', 'eng-003', 'cust-022', DATEADD(day, -4, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-049', 'Outlook calendar sync issues', 'Calendar not syncing to mobile devices', 'active', 'sev_c', 'eng-010', 'cust-023', DATEADD(day, -3, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-050', 'Azure SignalR connection drops', 'Clients disconnecting every 5 minutes', 'active', 'sev_b', 'eng-004', 'cust-024', DATEADD(day, -3, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-051', 'Power BI embedded capacity issues', 'Capacity showing 100% but no queries', 'active', 'sev_b', 'eng-007', 'cust-025', DATEADD(day, -2, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-052', 'Azure Cache for Redis evictions', 'Keys being evicted despite available memory', 'active', 'sev_b', 'eng-001', 'cust-001', DATEADD(day, -2, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-053', 'Virtual WAN hub routing', 'Branch traffic not reaching spoke VNets', 'active', 'sev_a', 'eng-004', 'cust-002', DATEADD(day, -1, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-054', 'Azure Migrate assessment errors', 'Discovery agent not reporting data', 'active', 'sev_c', 'eng-008', 'cust-003', DATEADD(day, -1, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-055', 'M365 license assignment failures', 'Group-based licensing not working', 'active', 'sev_c', 'eng-009', 'cust-004', DATEADD(day, -1, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-056', 'Azure SQL elastic pool DTU exhausted', 'All databases in pool experiencing timeouts', 'active', 'sev_a', 'eng-005', 'cust-005', DATEADD(day, 0, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-057', 'Application Insights sampling issues', 'Missing telemetry for specific requests', 'active', 'sev_c', 'eng-002', 'cust-006', DATEADD(day, 0, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-058', 'Azure Spring Apps deployment stuck', 'Deployment showing in progress for 2 hours', 'active', 'sev_b', 'eng-003', 'cust-007', DATEADD(day, 0, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-059', 'Defender for Endpoint onboarding', 'Machines showing unhealthy status', 'active', 'sev_b', 'eng-010', 'cust-008', DATEADD(day, 0, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE())),
('case-060', 'Azure Bastion connection timeout', 'RDP via Bastion disconnecting after 10 min', 'active', 'sev_c', 'eng-006', 'cust-009', DATEADD(day, 0, GETUTCDATE()), DATEADD(day, 0, GETUTCDATE()));
GO

-- =============================================================================
-- TIMELINE ENTRIES (Communications for sentiment analysis)
-- =============================================================================
-- Creating varied communication patterns for each case

-- Case 044 - Frustrated customer, slow response (Low sentiment)
INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, direction, created_on) VALUES
('tl-044-01', 'case-044', 'email_received', 'URGENT: Production down', 'Our entire production environment is inaccessible. This is costing us thousands per hour. We need immediate assistance!', 'cust-018', 'inbound', DATEADD(day, -6, GETUTCDATE())),
('tl-044-02', 'case-044', 'email_sent', 'RE: URGENT: Production down', 'Thank you for contacting Microsoft Support. We have received your case and will begin investigation shortly.', 'eng-001', 'outbound', DATEADD(day, -5, GETUTCDATE())),
('tl-044-03', 'case-044', 'email_received', 'RE: URGENT: Production down', 'Its been 24 hours and we still dont have our systems back. This is completely unacceptable. I need to speak with a manager immediately.', 'cust-018', 'inbound', DATEADD(day, -4, GETUTCDATE())),
('tl-044-04', 'case-044', 'note', 'Internal note', 'Escalated to engineering. AKS team investigating ingress controller issue.', 'eng-001', NULL, DATEADD(day, -4, GETUTCDATE())),
('tl-044-05', 'case-044', 'email_sent', 'RE: URGENT: Production down', 'We have identified the issue with the ingress controller and are working on a fix. ETA 2-4 hours.', 'eng-001', 'outbound', DATEADD(day, -3, GETUTCDATE())),
('tl-044-06', 'case-044', 'email_received', 'RE: URGENT: Production down', 'This has been an absolute disaster. We are reconsidering our entire Azure strategy because of this incident.', 'cust-018', 'inbound', DATEADD(day, -2, GETUTCDATE()));

-- Case 045 - Moderately frustrated (Medium sentiment)
INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, direction, created_on) VALUES
('tl-045-01', 'case-045', 'email_received', 'Databricks cluster issues', 'Our data engineering team cannot start any clusters. Jobs are failing and reports are not being generated.', 'cust-019', 'inbound', DATEADD(day, -5, GETUTCDATE())),
('tl-045-02', 'case-045', 'email_sent', 'RE: Databricks cluster issues', 'Thank you for reporting this. I am reviewing your workspace configuration. Can you share the cluster logs?', 'eng-005', 'outbound', DATEADD(day, -5, GETUTCDATE())),
('tl-045-03', 'case-045', 'email_received', 'RE: Databricks cluster issues', 'Logs attached. This is impacting our daily reporting.', 'cust-019', 'inbound', DATEADD(day, -4, GETUTCDATE())),
('tl-045-04', 'case-045', 'note', 'Analysis complete', 'Issue is related to node pool capacity in the region. Working with capacity team.', 'eng-005', NULL, DATEADD(day, -3, GETUTCDATE())),
('tl-045-05', 'case-045', 'email_sent', 'RE: Databricks cluster issues', 'The issue is related to capacity constraints. We are working on increasing allocation. Workaround: try smaller cluster size.', 'eng-005', 'outbound', DATEADD(day, -2, GETUTCDATE()));

-- Case 052 - Good communication, positive experience (High sentiment)
INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, direction, created_on) VALUES
('tl-052-01', 'case-052', 'email_received', 'Redis eviction question', 'Hi, we are seeing unexpected key evictions in our Redis cache. Memory shows 80% usage but keys are being removed.', 'cust-001', 'inbound', DATEADD(day, -2, GETUTCDATE())),
('tl-052-02', 'case-052', 'email_sent', 'RE: Redis eviction question', 'Thank you for the detailed description. This is likely related to memory fragmentation. Let me investigate your metrics.', 'eng-001', 'outbound', DATEADD(day, -2, GETUTCDATE())),
('tl-052-03', 'case-052', 'phone_call', 'Troubleshooting call', 'Discussed memory policies and fragmentation ratio. Customer understood the issue and appreciated the quick response.', 'eng-001', NULL, DATEADD(day, -1, GETUTCDATE())),
('tl-052-04', 'case-052', 'email_sent', 'RE: Redis eviction question', 'As discussed, I recommend switching to Premium tier with clustering. I have included a migration guide.', 'eng-001', 'outbound', DATEADD(day, -1, GETUTCDATE())),
('tl-052-05', 'case-052', 'email_received', 'RE: Redis eviction question', 'This is excellent support! The explanation was very clear and the guide is super helpful. Thank you Sarah!', 'cust-001', 'inbound', DATEADD(day, 0, GETUTCDATE()));

-- Case 038 - Escalated, frustrated (Low sentiment)
INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, direction, created_on) VALUES
('tl-038-01', 'case-038', 'email_received', 'Critical: API latency', 'Our APIs are taking 5+ seconds to respond. This is causing customer-facing issues and we are losing business.', 'cust-012', 'inbound', DATEADD(day, -13, GETUTCDATE())),
('tl-038-02', 'case-038', 'email_sent', 'RE: Critical: API latency', 'I understand the urgency. Let me review your APIM configuration and backend health.', 'eng-001', 'outbound', DATEADD(day, -12, GETUTCDATE())),
('tl-038-03', 'case-038', 'email_received', 'RE: Critical: API latency', 'Still waiting for update. This has been going on for days now.', 'cust-012', 'inbound', DATEADD(day, -10, GETUTCDATE())),
('tl-038-04', 'case-038', 'email_received', 'RE: Critical: API latency', 'I need to escalate this to your management. The lack of progress is unacceptable for a Sev A case.', 'cust-012', 'inbound', DATEADD(day, -8, GETUTCDATE())),
('tl-038-05', 'case-038', 'note', 'Manager escalation', 'Customer escalated to management. Working with APIM product team urgently.', 'eng-001', NULL, DATEADD(day, -7, GETUTCDATE())),
('tl-038-06', 'case-038', 'email_sent', 'RE: Critical: API latency', 'I sincerely apologize for the delay. We have identified a configuration issue and are implementing a fix.', 'eng-001', 'outbound', DATEADD(day, -5, GETUTCDATE()));

-- Case 032 - Good resolution (High sentiment)
INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, direction, created_on) VALUES
('tl-032-01', 'case-032', 'email_received', 'Front Door routing question', 'Traffic is not being routed according to our rules. Can you help investigate?', 'cust-006', 'inbound', DATEADD(day, -22, GETUTCDATE())),
('tl-032-02', 'case-032', 'email_sent', 'RE: Front Door routing question', 'Happy to help! Can you share your routing rule configuration?', 'eng-001', 'outbound', DATEADD(day, -22, GETUTCDATE())),
('tl-032-03', 'case-032', 'email_received', 'RE: Front Door routing question', 'Config attached. Thanks for the quick response!', 'cust-006', 'inbound', DATEADD(day, -21, GETUTCDATE())),
('tl-032-04', 'case-032', 'phone_call', 'Configuration review', 'Walked through routing rules with customer. Found wildcard pattern issue.', 'eng-001', NULL, DATEADD(day, -20, GETUTCDATE())),
('tl-032-05', 'case-032', 'email_sent', 'RE: Front Door routing question', 'Great news! I found the issue - the wildcard pattern needs to be updated. See attached fix.', 'eng-001', 'outbound', DATEADD(day, -19, GETUTCDATE())),
('tl-032-06', 'case-032', 'email_received', 'RE: Front Door routing question', 'That fixed it! You are amazing Sarah. Will definitely give positive feedback on this case.', 'cust-006', 'inbound', DATEADD(day, -18, GETUTCDATE()));

-- Add timeline entries for more cases to create diverse sentiment patterns

-- Case 056 - New critical, responsive (Medium sentiment starting)
INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, direction, created_on) VALUES
('tl-056-01', 'case-056', 'email_received', 'CRITICAL: All databases down', 'Entire elastic pool is experiencing connection timeouts. This is a P1 incident for our company.', 'cust-005', 'inbound', DATEADD(hour, -4, GETUTCDATE())),
('tl-056-02', 'case-056', 'email_sent', 'RE: CRITICAL: All databases down', 'Received - treating as highest priority. Checking pool metrics now.', 'eng-005', 'outbound', DATEADD(hour, -3, GETUTCDATE())),
('tl-056-03', 'case-056', 'note', 'Initial analysis', 'DTU exhausted - one database running expensive queries. Identifying culprit.', 'eng-005', NULL, DATEADD(hour, -2, GETUTCDATE()));

-- Case 030 - Long running, getting frustrated (Declining sentiment)
INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, direction, created_on) VALUES
('tl-030-01', 'case-030', 'email_received', 'SQL MI performance', 'After migrating to Managed Instance, query performance has degraded significantly.', 'cust-004', 'inbound', DATEADD(day, -24, GETUTCDATE())),
('tl-030-02', 'case-030', 'email_sent', 'RE: SQL MI performance', 'Can you share the query execution plans from before and after migration?', 'eng-007', 'outbound', DATEADD(day, -23, GETUTCDATE())),
('tl-030-03', 'case-030', 'email_received', 'RE: SQL MI performance', 'Plans attached. Still waiting for analysis.', 'cust-004', 'inbound', DATEADD(day, -20, GETUTCDATE())),
('tl-030-04', 'case-030', 'note', 'Analysis in progress', 'Comparing execution plans. Some index recommendations identified.', 'eng-007', NULL, DATEADD(day, -15, GETUTCDATE())),
('tl-030-05', 'case-030', 'email_received', 'RE: SQL MI performance', 'It has been over 2 weeks. Our users are complaining daily about slow reports. When will this be resolved?', 'cust-004', 'inbound', DATEADD(day, -10, GETUTCDATE())),
('tl-030-06', 'case-030', 'email_sent', 'RE: SQL MI performance', 'Apologies for the delay. I have identified some missing indexes. Please try adding these.', 'eng-007', 'outbound', DATEADD(day, -8, GETUTCDATE())),
('tl-030-07', 'case-030', 'email_received', 'RE: SQL MI performance', 'Tried the indexes but still slow. I am losing faith in this migration. We may need to go back to on-prem.', 'cust-004', 'inbound', DATEADD(day, -5, GETUTCDATE()));

-- Case 041 - Technical challenge, good engagement (Medium-High sentiment)
INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, direction, created_on) VALUES
('tl-041-01', 'case-041', 'email_received', 'B2C custom policy MFA issue', 'Our custom policy fails at the MFA step. Error code attached.', 'cust-015', 'inbound', DATEADD(day, -10, GETUTCDATE())),
('tl-041-02', 'case-041', 'email_sent', 'RE: B2C custom policy MFA issue', 'Thank you for the detailed error info. Let me review the policy XML.', 'eng-004', 'outbound', DATEADD(day, -10, GETUTCDATE())),
('tl-041-03', 'case-041', 'phone_call', 'Technical deep dive', 'Walked through policy XML. Found misconfigured technical profile.', 'eng-004', NULL, DATEADD(day, -8, GETUTCDATE())),
('tl-041-04', 'case-041', 'email_sent', 'RE: B2C custom policy MFA issue', 'As discussed, the TechnicalProfile for MFA needs the correct OutputClaims. Updated XML attached.', 'eng-004', 'outbound', DATEADD(day, -7, GETUTCDATE())),
('tl-041-05', 'case-041', 'email_received', 'RE: B2C custom policy MFA issue', 'Much better! MFA working now but users see a brief error flash. Any ideas?', 'cust-015', 'inbound', DATEADD(day, -5, GETUTCDATE())),
('tl-041-06', 'case-041', 'email_sent', 'RE: B2C custom policy MFA issue', 'That flash is due to JavaScript loading timing. Add a loading spinner to smooth the UX.', 'eng-004', 'outbound', DATEADD(day, -3, GETUTCDATE()));

-- Case 027 - Rate limiting frustration (Low-Medium sentiment)  
INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, direction, created_on) VALUES
('tl-027-01', 'case-027', 'email_received', 'OpenAI rate limiting', 'We are getting 429 errors constantly even though we have PTU capacity.', 'cust-001', 'inbound', DATEADD(day, -28, GETUTCDATE())),
('tl-027-02', 'case-027', 'email_sent', 'RE: OpenAI rate limiting', 'Let me check your quota allocation and usage patterns.', 'eng-006', 'outbound', DATEADD(day, -27, GETUTCDATE())),
('tl-027-03', 'case-027', 'email_received', 'RE: OpenAI rate limiting', 'Any update? We are losing customers because of slow AI responses.', 'cust-001', 'inbound', DATEADD(day, -20, GETUTCDATE())),
('tl-027-04', 'case-027', 'note', 'Quota investigation', 'Customer hitting regional limits. Need capacity team input.', 'eng-006', NULL, DATEADD(day, -18, GETUTCDATE())),
('tl-027-05', 'case-027', 'email_sent', 'RE: OpenAI rate limiting', 'You are hitting regional capacity limits. Workaround: distribute across multiple regions.', 'eng-006', 'outbound', DATEADD(day, -15, GETUTCDATE())),
('tl-027-06', 'case-027', 'email_received', 'RE: OpenAI rate limiting', 'That is not really a solution - it adds complexity and latency. Can you increase our regional quota?', 'cust-001', 'inbound', DATEADD(day, -10, GETUTCDATE())),
('tl-027-07', 'case-027', 'email_sent', 'RE: OpenAI rate limiting', 'Quota increases require business justification. I have started the process - ETA 2 weeks.', 'eng-006', 'outbound', DATEADD(day, -5, GETUTCDATE()));

-- More timeline entries for additional cases...
INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, direction, created_on) VALUES
('tl-047-01', 'case-047', 'email_received', 'Private endpoint DNS', 'On-prem servers cannot resolve private endpoint FQDNs.', 'cust-021', 'inbound', DATEADD(day, -4, GETUTCDATE())),
('tl-047-02', 'case-047', 'email_sent', 'RE: Private endpoint DNS', 'This is a common scenario. Let me document the DNS forwarding setup you need.', 'eng-002', 'outbound', DATEADD(day, -4, GETUTCDATE())),
('tl-047-03', 'case-047', 'phone_call', 'DNS configuration call', 'Walked through conditional forwarder setup for privatelink zones.', 'eng-002', NULL, DATEADD(day, -3, GETUTCDATE())),
('tl-047-04', 'case-047', 'email_sent', 'RE: Private endpoint DNS', 'Detailed architecture diagram and step-by-step guide attached.', 'eng-002', 'outbound', DATEADD(day, -2, GETUTCDATE())),
('tl-047-05', 'case-047', 'email_received', 'RE: Private endpoint DNS', 'This is exactly what we needed! Clear and comprehensive. Thank you Marcus!', 'cust-021', 'inbound', DATEADD(day, -1, GETUTCDATE()));

INSERT INTO timeline_entries (id, case_id, entry_type, subject, content, created_by, direction, created_on) VALUES
('tl-048-01', 'case-048', 'email_received', 'Firewall blocking legitimate traffic', 'Azure Firewall is dropping packets that should be allowed by our rules.', 'cust-022', 'inbound', DATEADD(day, -4, GETUTCDATE())),
('tl-048-02', 'case-048', 'email_sent', 'RE: Firewall blocking legitimate traffic', 'Can you share the diagnostic logs and rule collection configuration?', 'eng-003', 'outbound', DATEADD(day, -4, GETUTCDATE())),
('tl-048-03', 'case-048', 'email_received', 'RE: Firewall blocking legitimate traffic', 'Logs attached. This is impacting our production services significantly.', 'cust-022', 'inbound', DATEADD(day, -3, GETUTCDATE())),
('tl-048-04', 'case-048', 'note', 'Rule analysis', 'Found rule priority conflict - deny rule evaluated before allow rule.', 'eng-003', NULL, DATEADD(day, -2, GETUTCDATE())),
('tl-048-05', 'case-048', 'email_sent', 'RE: Firewall blocking legitimate traffic', 'I found the issue - rule priority needs adjustment. See recommended changes.', 'eng-003', 'outbound', DATEADD(day, -1, GETUTCDATE()));
GO

-- =============================================================================
-- CASE ANALYSES (Pre-computed sentiment scores)
-- =============================================================================
INSERT INTO case_analyses (id, case_id, sentiment_score, sentiment_label, confidence, risk_level, key_indicators, recommendations, analyzed_at) VALUES
('ana-044', 'case-044', 0.25, 'negative', 0.92, 'critical', '["production outage","cost per hour","unacceptable","reconsidering Azure"]', '["Immediate escalation recommended","Schedule recovery call","Provide compensation consideration"]', DATEADD(hour, -1, GETUTCDATE())),
('ana-045', 'case-045', 0.48, 'neutral', 0.78, 'at_risk', '["impacting reporting","daily impact"]', '["Continue regular updates","Provide workaround timeline"]', DATEADD(hour, -1, GETUTCDATE())),
('ana-052', 'case-052', 0.88, 'positive', 0.95, 'healthy', '["excellent support","very clear","super helpful"]', '["Share best practices","Request testimonial"]', DATEADD(hour, -1, GETUTCDATE())),
('ana-038', 'case-038', 0.32, 'negative', 0.89, 'critical', '["losing business","unacceptable","lack of progress","escalate to management"]', '["Manager involvement required","Daily status updates","Root cause documentation"]', DATEADD(hour, -1, GETUTCDATE())),
('ana-032', 'case-032', 0.85, 'positive', 0.91, 'healthy', '["quick response","amazing","positive feedback"]', '["Recognition for engineer","Document solution for KB"]', DATEADD(hour, -1, GETUTCDATE())),
('ana-056', 'case-056', 0.52, 'neutral', 0.75, 'at_risk', '["P1 incident","critical"]', '["Maintain rapid response","Provide regular updates"]', DATEADD(hour, -1, GETUTCDATE())),
('ana-030', 'case-030', 0.35, 'negative', 0.87, 'critical', '["losing faith","may go back to on-prem","complaining daily"]', '["Escalate to specialist","Provide migration rollback plan","Executive engagement"]', DATEADD(hour, -1, GETUTCDATE())),
('ana-041', 'case-041', 0.72, 'positive', 0.82, 'healthy', '["much better","working now"]', '["Continue technical guidance","Document solution"]', DATEADD(hour, -1, GETUTCDATE())),
('ana-027', 'case-027', 0.42, 'neutral', 0.80, 'at_risk', '["losing customers","not really a solution","adds complexity"]', '["Expedite quota request","Provide interim solution"]', DATEADD(hour, -1, GETUTCDATE())),
('ana-047', 'case-047', 0.90, 'positive', 0.93, 'healthy', '["exactly what we needed","clear and comprehensive"]', '["Great documentation example","Share with team"]', DATEADD(hour, -1, GETUTCDATE())),
('ana-048', 'case-048', 0.55, 'neutral', 0.79, 'at_risk', '["impacting production"]', '["Implement fix quickly","Verify no recurrence"]', DATEADD(hour, -1, GETUTCDATE()));
GO

-- =============================================================================
-- SAMPLE FEEDBACK DATA
-- =============================================================================
INSERT INTO feedback (id, rating, comment, category, page, engineer_id, user_agent, created_at) VALUES
('fb-001', 'positive', 'The coaching insights are incredibly helpful for my 1:1s with my team.', 'coaching', 'manager', 'mgr-001', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', DATEADD(day, -5, GETUTCDATE())),
('fb-002', 'positive', 'Love the real-time sentiment analysis. Helps me prioritize cases.', 'general', 'engineer', 'eng-001', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', DATEADD(day, -4, GETUTCDATE())),
('fb-003', 'negative', 'The trend chart could show more detail - maybe daily instead of weekly.', 'ui', 'engineer-detail', 'mgr-002', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', DATEADD(day, -3, GETUTCDATE())),
('fb-004', 'positive', 'Finally a tool that helps prevent CSAT issues before they happen!', 'general', 'landing', NULL, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', DATEADD(day, -2, GETUTCDATE())),
('fb-005', 'positive', 'The personalized coaching tips are spot-on. Very actionable.', 'coaching', 'engineer-detail', 'mgr-001', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', DATEADD(day, -1, GETUTCDATE()));
GO

PRINT '';
PRINT '=========================================';
PRINT 'Comprehensive seed data created!';
PRINT '=========================================';
PRINT 'Engineers: 13 (10 support + 3 managers)';
PRINT 'Customers: 25';
PRINT 'Cases: 60 (spanning 90 days)';
PRINT 'Timeline entries: 50+';
PRINT 'Case analyses: 11';
PRINT 'Sample feedback: 5';
PRINT '=========================================';
GO
