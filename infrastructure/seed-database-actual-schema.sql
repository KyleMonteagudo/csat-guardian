-- =============================================================================
-- CSAT Guardian - Sample Data for ACTUAL Azure SQL Schema
-- =============================================================================
-- This script works with the ACTUAL deployed schema which uses:
-- - Lowercase column names (id, name, email, team, etc.)
-- - Different column names than originally planned
--
-- Run this from the dev-box or via the /api/admin/seed endpoint
-- =============================================================================

-- Clear existing data (order matters for foreign keys)
DELETE FROM TimelineEntries;
DELETE FROM Cases;
DELETE FROM Customers;
DELETE FROM Engineers;

-- Insert Engineers (actual schema: id, name, email, team)
INSERT INTO Engineers (id, name, email, team) VALUES
('eng-001', 'John Smith', 'john.smith@microsoft.com', 'Support'),
('eng-002', 'Sarah Johnson', 'sarah.johnson@microsoft.com', 'Support'),
('eng-003', 'Mike Chen', 'mike.chen@microsoft.com', 'Support');

-- Insert Customers (actual schema: id, name, company, tier)
INSERT INTO Customers (id, name, company, tier) VALUES
('cust-001', 'Contoso Contact', 'Contoso Ltd', 'enterprise'),
('cust-002', 'Fabrikam Contact', 'Fabrikam Inc', 'enterprise'),
('cust-003', 'Northwind Contact', 'Northwind Traders', 'standard'),
('cust-004', 'Adventure Contact', 'Adventure Works', 'premium'),
('cust-005', 'Woodgrove Contact', 'Woodgrove Bank', 'enterprise'),
('cust-006', 'Tailspin Contact', 'Tailspin Toys', 'standard');

-- Insert Cases (actual schema: id, title, customer_id, engineer_id, status, severity, created_at)
-- status: integer (1=active, 2=pending, 3=resolved)
-- severity: integer (1=low, 2=medium, 3=high, 4=critical)
INSERT INTO Cases (id, title, customer_id, engineer_id, status, severity, created_at) VALUES
('case-001', 'Azure VM Performance Optimization', 'cust-001', 'eng-001', 1, 2, DATEADD(day, -10, GETUTCDATE())),
('case-002', 'Storage Account Access Issues', 'cust-002', 'eng-001', 1, 3, DATEADD(day, -5, GETUTCDATE())),
('case-003', 'Azure SQL Query Performance', 'cust-003', 'eng-002', 1, 2, DATEADD(day, -7, GETUTCDATE())),
('case-004', 'Billing Discrepancy Investigation', 'cust-004', 'eng-001', 1, 3, DATEADD(day, -14, GETUTCDATE())),
('case-005', 'App Service Deployment Failures', 'cust-005', 'eng-002', 1, 2, DATEADD(day, -8, GETUTCDATE())),
('case-006', 'Network Connectivity Problems', 'cust-006', 'eng-003', 1, 4, DATEADD(day, -12, GETUTCDATE()));

-- Insert Timeline Entries (actual schema: id, case_id, entry_type, content, sentiment_score, created_at)
-- Case 1: Happy customer (positive sentiment)
INSERT INTO TimelineEntries (id, case_id, entry_type, content, sentiment_score, created_at) VALUES
('tl-001-01', 'case-001', 'email', 'Hi, thanks for looking into this. We are seeing slow response times during business hours.', 0.6, DATEADD(day, -9, GETUTCDATE())),
('tl-001-02', 'case-001', 'note', 'Reviewed VM metrics. CPU peaks at 95%. Recommend scaling up or implementing auto-scale.', 0.5, DATEADD(day, -8, GETUTCDATE())),
('tl-001-03', 'case-001', 'email', 'Thank you so much for the quick response! The recommendations look great.', 0.9, DATEADD(day, -3, GETUTCDATE()));

-- Case 2: Frustrated customer (negative sentiment, urgent)
INSERT INTO TimelineEntries (id, case_id, entry_type, content, sentiment_score, created_at) VALUES
('tl-002-01', 'case-002', 'email', 'This is URGENT! Our production application is DOWN because we cannot access storage!', -0.8, DATEADD(day, -4, GETUTCDATE())),
('tl-002-02', 'case-002', 'note', 'Checking storage account configuration and access policies.', 0.5, DATEADD(day, -3, GETUTCDATE())),
('tl-002-03', 'case-002', 'email', 'We have been waiting for 2 days now. This is completely unacceptable!', -0.9, DATEADD(day, -1, GETUTCDATE()));

-- Case 3: Neutral customer
INSERT INTO TimelineEntries (id, case_id, entry_type, content, sentiment_score, created_at) VALUES
('tl-003-01', 'case-003', 'email', 'We have some queries that are slower than expected. Can you help us optimize them?', 0.3, DATEADD(day, -6, GETUTCDATE())),
('tl-003-02', 'case-003', 'note', 'Requested query execution plans for analysis.', 0.5, DATEADD(day, -5, GETUTCDATE())),
('tl-003-03', 'case-003', 'email', 'Here are the execution plans as requested. Let us know what you find.', 0.4, DATEADD(day, -2, GETUTCDATE()));

-- Case 4: Declining sentiment - 10+ days without note update (CRITICAL ALERT expected)
INSERT INTO TimelineEntries (id, case_id, entry_type, content, sentiment_score, created_at) VALUES
('tl-004-01', 'case-004', 'email', 'Hi, we noticed some unexpected charges on our bill. Can you help clarify?', 0.2, DATEADD(day, -13, GETUTCDATE())),
('tl-004-02', 'case-004', 'note', 'Looking into billing details for the customer account.', 0.5, DATEADD(day, -12, GETUTCDATE())),
('tl-004-03', 'case-004', 'email', 'It has been a week! This is getting very frustrating. We need answers!', -0.7, DATEADD(day, -10, GETUTCDATE()));

-- Case 5: 6 days since last note (WARNING ALERT expected)
INSERT INTO TimelineEntries (id, case_id, entry_type, content, sentiment_score, created_at) VALUES
('tl-005-01', 'case-005', 'email', 'Our deployments are failing randomly. Sometimes they work, sometimes they dont.', 0.1, DATEADD(day, -7, GETUTCDATE())),
('tl-005-02', 'case-005', 'note', 'Requested deployment logs and pipeline configuration.', 0.5, DATEADD(day, -6, GETUTCDATE()));

-- Case 6: 8+ days without update, declining sentiment (CRITICAL ALERT expected)
INSERT INTO TimelineEntries (id, case_id, entry_type, content, sentiment_score, created_at) VALUES
('tl-006-01', 'case-006', 'email', 'VMs cannot communicate across subnets. This is blocking our project timeline.', -0.3, DATEADD(day, -11, GETUTCDATE())),
('tl-006-02', 'case-006', 'note', 'Reviewed NSG rules, they appear correct. Need deeper investigation.', 0.4, DATEADD(day, -10, GETUTCDATE())),
('tl-006-03', 'case-006', 'email', 'Stuck for over a week now. Very worried about our deadline. Please escalate!', -0.6, DATEADD(day, -8, GETUTCDATE()));

-- Verify data
SELECT 'Engineers' as TableName, COUNT(*) as RowCount FROM Engineers
UNION ALL SELECT 'Customers', COUNT(*) FROM Customers
UNION ALL SELECT 'Cases', COUNT(*) FROM Cases
UNION ALL SELECT 'TimelineEntries', COUNT(*) FROM TimelineEntries;

-- Expected alerts after seeding:
-- eng-001: case-004 (CRITICAL - 10+ days since note)
-- eng-002: case-005 (WARNING - 6 days since note)
-- eng-003: case-006 (CRITICAL - 8+ days since note)
