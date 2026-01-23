-- =============================================================================
-- CSAT Guardian - Database Schema and Sample Data
-- =============================================================================
-- Run this script in Azure Portal Query Editor:
-- 1. Go to Azure Portal → SQL databases → sqldb-csatguardian-dev
-- 2. Click "Query editor (preview)" in left menu
-- 3. Login with sqladmin / your password
-- 4. Paste this entire script and click "Run"
-- =============================================================================

-- Create Engineers table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Engineers')
CREATE TABLE Engineers (
    Id NVARCHAR(50) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    Email NVARCHAR(255) NOT NULL,
    TeamsId NVARCHAR(100),
    CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2 DEFAULT GETUTCDATE()
);

-- Create Customers table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Customers')
CREATE TABLE Customers (
    Id NVARCHAR(50) PRIMARY KEY,
    Company NVARCHAR(255) NOT NULL,
    CreatedAt DATETIME2 DEFAULT GETUTCDATE()
);

-- Create Cases table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Cases')
CREATE TABLE Cases (
    Id NVARCHAR(50) PRIMARY KEY,
    Title NVARCHAR(500) NOT NULL,
    Description NVARCHAR(MAX),
    Status NVARCHAR(50) NOT NULL DEFAULT 'active',
    Priority NVARCHAR(50) NOT NULL DEFAULT 'medium',
    OwnerId NVARCHAR(50) NOT NULL,
    CustomerId NVARCHAR(50) NOT NULL,
    CreatedOn DATETIME2 NOT NULL,
    ModifiedOn DATETIME2 NOT NULL,
    FOREIGN KEY (OwnerId) REFERENCES Engineers(Id),
    FOREIGN KEY (CustomerId) REFERENCES Customers(Id)
);

-- Create TimelineEntries table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'TimelineEntries')
CREATE TABLE TimelineEntries (
    Id NVARCHAR(50) PRIMARY KEY,
    CaseId NVARCHAR(50) NOT NULL,
    EntryType NVARCHAR(50) NOT NULL,
    Subject NVARCHAR(500),
    Content NVARCHAR(MAX),
    CreatedOn DATETIME2 NOT NULL,
    CreatedBy NVARCHAR(100),
    IsCustomerCommunication BIT DEFAULT 0,
    FOREIGN KEY (CaseId) REFERENCES Cases(Id)
);

-- Create Alerts table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Alerts')
CREATE TABLE Alerts (
    Id NVARCHAR(50) PRIMARY KEY,
    CaseId NVARCHAR(50) NOT NULL,
    EngineerId NVARCHAR(50) NOT NULL,
    AlertType NVARCHAR(50) NOT NULL,
    Message NVARCHAR(MAX),
    CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
    SentAt DATETIME2,
    FOREIGN KEY (CaseId) REFERENCES Cases(Id),
    FOREIGN KEY (EngineerId) REFERENCES Engineers(Id)
);

-- Clear existing data (for idempotent deployment)
DELETE FROM TimelineEntries;
DELETE FROM Alerts;
DELETE FROM Cases;
DELETE FROM Customers;
DELETE FROM Engineers;

-- Insert Engineers
INSERT INTO Engineers (Id, Name, Email, TeamsId) VALUES
('eng-001', 'John Smith', 'john.smith@microsoft.com', 'john.smith'),
('eng-002', 'Sarah Johnson', 'sarah.johnson@microsoft.com', 'sarah.johnson'),
('eng-003', 'Mike Chen', 'mike.chen@microsoft.com', 'mike.chen');

-- Insert Customers
INSERT INTO Customers (Id, Company) VALUES
('cust-001', 'Contoso Ltd'),
('cust-002', 'Fabrikam Inc'),
('cust-003', 'Northwind Traders'),
('cust-004', 'Adventure Works'),
('cust-005', 'Woodgrove Bank'),
('cust-006', 'Tailspin Toys');

-- Insert Cases (6 scenarios covering different situations)
INSERT INTO Cases (Id, Title, Description, Status, Priority, OwnerId, CustomerId, CreatedOn, ModifiedOn) VALUES
('case-001', 'Azure VM Performance Optimization', 'Customer reports slow VM performance during peak hours. Need help optimizing configuration.', 'active', 'medium', 'eng-001', 'cust-001', DATEADD(day, -10, GETUTCDATE()), DATEADD(day, -3, GETUTCDATE())),
('case-002', 'Storage Account Access Issues', 'Getting 403 errors when accessing blob storage from web app. Urgent production issue.', 'active', 'high', 'eng-001', 'cust-002', DATEADD(day, -5, GETUTCDATE()), DATEADD(day, -1, GETUTCDATE())),
('case-003', 'Azure SQL Query Performance', 'Some queries taking longer than expected. Need query optimization assistance.', 'active', 'medium', 'eng-002', 'cust-003', DATEADD(day, -7, GETUTCDATE()), DATEADD(day, -2, GETUTCDATE())),
('case-004', 'Billing Discrepancy Investigation', 'Customer disputes charges for last month. Claims they were billed for resources not used.', 'active', 'high', 'eng-001', 'cust-004', DATEADD(day, -14, GETUTCDATE()), DATEADD(day, -10, GETUTCDATE())),
('case-005', 'App Service Deployment Failures', 'CI/CD pipeline failing intermittently. Need help debugging deployment issues.', 'active', 'medium', 'eng-002', 'cust-005', DATEADD(day, -8, GETUTCDATE()), DATEADD(day, -6, GETUTCDATE())),
('case-006', 'Network Connectivity Problems', 'VMs in different subnets unable to communicate. NSG rules appear correct.', 'active', 'critical', 'eng-003', 'cust-006', DATEADD(day, -12, GETUTCDATE()), DATEADD(day, -8, GETUTCDATE()));

-- Insert Timeline Entries for Case 1 (Happy path - good sentiment)
INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) VALUES
('tl-001-01', 'case-001', 'email', 'RE: VM Performance', 'Hi, thanks for looking into this. We are seeing slow response times during business hours (9am-5pm EST).', DATEADD(day, -9, GETUTCDATE()), 'Customer', 1),
('tl-001-02', 'case-001', 'note', 'Initial Analysis', 'Reviewed VM metrics. CPU peaks at 95% during reported times. Recommend scaling up or implementing auto-scale.', DATEADD(day, -8, GETUTCDATE()), 'John Smith', 0),
('tl-001-03', 'case-001', 'email', 'RE: VM Performance', 'Thank you so much for the quick response! The recommendations look great. We will implement auto-scaling.', DATEADD(day, -3, GETUTCDATE()), 'Customer', 1);

-- Insert Timeline Entries for Case 2 (Frustrated customer - negative sentiment)
INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) VALUES
('tl-002-01', 'case-002', 'email', 'URGENT: Storage Access', 'This is URGENT! Our production application is DOWN because we cannot access storage. We need this fixed IMMEDIATELY!', DATEADD(day, -4, GETUTCDATE()), 'Customer', 1),
('tl-002-02', 'case-002', 'note', 'Troubleshooting', 'Checking storage account configuration and access policies.', DATEADD(day, -3, GETUTCDATE()), 'John Smith', 0),
('tl-002-03', 'case-002', 'email', 'RE: Storage Access', 'We have been waiting for 2 days now. This is completely unacceptable. We are losing money every hour this is down!', DATEADD(day, -1, GETUTCDATE()), 'Customer', 1);

-- Insert Timeline Entries for Case 3 (Neutral sentiment)
INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) VALUES
('tl-003-01', 'case-003', 'email', 'Query Performance', 'We have some queries that are slower than expected. Can you help us optimize them?', DATEADD(day, -6, GETUTCDATE()), 'Customer', 1),
('tl-003-02', 'case-003', 'note', 'Analysis', 'Requested query execution plans for analysis.', DATEADD(day, -5, GETUTCDATE()), 'Sarah Johnson', 0),
('tl-003-03', 'case-003', 'email', 'RE: Query Performance', 'Here are the execution plans as requested. Let us know what you find.', DATEADD(day, -2, GETUTCDATE()), 'Customer', 1);

-- Insert Timeline Entries for Case 4 (Declining sentiment - 7-day breach)
INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) VALUES
('tl-004-01', 'case-004', 'email', 'Billing Question', 'Hi, we noticed some unexpected charges on our bill. Can you help clarify?', DATEADD(day, -13, GETUTCDATE()), 'Customer', 1),
('tl-004-02', 'case-004', 'note', 'Reviewing charges', 'Looking into billing details for the customer account.', DATEADD(day, -12, GETUTCDATE()), 'John Smith', 0),
('tl-004-03', 'case-004', 'email', 'RE: Billing', 'It has been a week and we still have not heard back. This is getting frustrating. We need answers!', DATEADD(day, -10, GETUTCDATE()), 'Customer', 1);

-- Insert Timeline Entries for Case 5 (7-day warning approaching)
INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) VALUES
('tl-005-01', 'case-005', 'email', 'Deployment Issues', 'Our deployments are failing randomly. Sometimes they work, sometimes they dont.', DATEADD(day, -7, GETUTCDATE()), 'Customer', 1),
('tl-005-02', 'case-005', 'note', 'Initial review', 'Requested deployment logs and pipeline configuration.', DATEADD(day, -6, GETUTCDATE()), 'Sarah Johnson', 0);

-- Insert Timeline Entries for Case 6 (7-day breach with declining sentiment)
INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) VALUES
('tl-006-01', 'case-006', 'email', 'Network Issue', 'VMs cannot communicate across subnets. This is blocking our project timeline.', DATEADD(day, -11, GETUTCDATE()), 'Customer', 1),
('tl-006-02', 'case-006', 'note', 'Checking NSGs', 'Reviewed NSG rules, they appear correct. Need deeper investigation.', DATEADD(day, -10, GETUTCDATE()), 'Mike Chen', 0),
('tl-006-03', 'case-006', 'email', 'RE: Network Issue', 'We have been stuck on this for over a week now. Our deadline is approaching and we are very worried. Please escalate if needed!', DATEADD(day, -8, GETUTCDATE()), 'Customer', 1);

-- Verify data
SELECT 'Engineers' as TableName, COUNT(*) as RowCount FROM Engineers
UNION ALL SELECT 'Customers', COUNT(*) FROM Customers
UNION ALL SELECT 'Cases', COUNT(*) FROM Cases
UNION ALL SELECT 'TimelineEntries', COUNT(*) FROM TimelineEntries
UNION ALL SELECT 'Alerts', COUNT(*) FROM Alerts;

PRINT 'Database schema created and sample data inserted successfully!';
