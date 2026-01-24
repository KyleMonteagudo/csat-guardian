-- =============================================================================
-- CSAT Guardian - Complete Database Schema
-- =============================================================================
-- Run in Azure Cloud Shell:
--   sqlcmd -S sql-csatguardian-dev.database.windows.net -d sqldb-csatguardian-dev -U sqladmin -P 'YourPassword' -i schema-complete.sql
--
-- This schema supports:
-- - DfM data sync (cases, timeline)
-- - CSAT analysis results
-- - Communication metrics for manager insights
-- - Rule violation tracking
-- - Notifications (for Teams integration later)
-- - Conversation sessions
-- - Aggregated engineer metrics
-- =============================================================================

-- =============================================================================
-- DROP EXISTING TABLES (for clean rebuild)
-- =============================================================================
-- Drop all foreign key constraints first
DECLARE @sql NVARCHAR(MAX) = N'';
SELECT @sql += N'ALTER TABLE ' + QUOTENAME(OBJECT_SCHEMA_NAME(parent_object_id)) 
    + '.' + QUOTENAME(OBJECT_NAME(parent_object_id)) 
    + ' DROP CONSTRAINT ' + QUOTENAME(name) + ';'
FROM sys.foreign_keys;
EXEC sp_executesql @sql;
GO

-- Now drop tables in reverse dependency order
IF OBJECT_ID('manager_alert_queue', 'U') IS NOT NULL DROP TABLE manager_alert_queue;
IF OBJECT_ID('conversation_messages', 'U') IS NOT NULL DROP TABLE conversation_messages;
IF OBJECT_ID('conversations', 'U') IS NOT NULL DROP TABLE conversations;
IF OBJECT_ID('engineer_metrics', 'U') IS NOT NULL DROP TABLE engineer_metrics;
IF OBJECT_ID('notifications', 'U') IS NOT NULL DROP TABLE notifications;
IF OBJECT_ID('rule_violations', 'U') IS NOT NULL DROP TABLE rule_violations;
IF OBJECT_ID('communication_metrics', 'U') IS NOT NULL DROP TABLE communication_metrics;
IF OBJECT_ID('case_analyses', 'U') IS NOT NULL DROP TABLE case_analyses;
IF OBJECT_ID('timeline_entries', 'U') IS NOT NULL DROP TABLE timeline_entries;
IF OBJECT_ID('cases', 'U') IS NOT NULL DROP TABLE cases;
IF OBJECT_ID('customers', 'U') IS NOT NULL DROP TABLE customers;
IF OBJECT_ID('engineers', 'U') IS NOT NULL DROP TABLE engineers;
IF OBJECT_ID('vw_data_retention', 'V') IS NOT NULL DROP VIEW vw_data_retention;
GO

-- =============================================================================
-- CORE TABLES (DfM Sync)
-- =============================================================================

-- Engineers (internal MS employees - not PII)
CREATE TABLE engineers (
    id NVARCHAR(50) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(100),
    team NVARCHAR(100),
    manager_id NVARCHAR(50),              -- For manager mode (references engineers.id)
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

-- Customers (company only - no individual PII)
CREATE TABLE customers (
    id NVARCHAR(50) PRIMARY KEY,
    company NVARCHAR(200) NOT NULL,
    tier NVARCHAR(50),                    -- Premier, Unified, Pro
    created_at DATETIME2 DEFAULT GETUTCDATE()
);
GO

-- Cases (synced from DfM)
CREATE TABLE cases (
    id NVARCHAR(50) PRIMARY KEY,
    title NVARCHAR(500) NOT NULL,
    description NVARCHAR(MAX),
    status NVARCHAR(50) NOT NULL,         -- active, resolved, cancelled, etc.
    priority NVARCHAR(50),                -- critical, high, medium, low
    owner_id NVARCHAR(50) NOT NULL,
    customer_id NVARCHAR(50) NOT NULL,
    created_on DATETIME2 NOT NULL,
    modified_on DATETIME2,
    synced_at DATETIME2 DEFAULT GETUTCDATE(),
    
    CONSTRAINT fk_cases_owner FOREIGN KEY (owner_id) REFERENCES engineers(id),
    CONSTRAINT fk_cases_customer FOREIGN KEY (customer_id) REFERENCES customers(id)
);
GO

CREATE INDEX idx_cases_owner ON cases(owner_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_created ON cases(created_on);
GO

-- Timeline Entries (synced from DfM)
CREATE TABLE timeline_entries (
    id NVARCHAR(50) PRIMARY KEY,
    case_id NVARCHAR(50) NOT NULL,
    entry_type NVARCHAR(50) NOT NULL,     -- email_sent, email_received, note, phone_call
    subject NVARCHAR(500),
    content NVARCHAR(MAX),
    created_by NVARCHAR(100),
    created_on DATETIME2 NOT NULL,
    direction NVARCHAR(20),               -- inbound, outbound
    is_customer_communication BIT DEFAULT 0,
    synced_at DATETIME2 DEFAULT GETUTCDATE(),
    
    CONSTRAINT fk_timeline_case FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);
GO

CREATE INDEX idx_timeline_case ON timeline_entries(case_id);
CREATE INDEX idx_timeline_created ON timeline_entries(created_on);
CREATE INDEX idx_timeline_type ON timeline_entries(entry_type);
GO

-- =============================================================================
-- ANALYTICS TABLES (Our Generated Data)
-- =============================================================================

-- Case-level analysis results
CREATE TABLE case_analyses (
    id INT IDENTITY(1,1) PRIMARY KEY,
    case_id NVARCHAR(50) NOT NULL,
    analyzed_at DATETIME2 DEFAULT GETUTCDATE(),
    
    -- Sentiment
    overall_sentiment_score DECIMAL(3,2),  -- 0.00 to 1.00
    sentiment_label NVARCHAR(20),          -- positive, neutral, negative
    sentiment_trend NVARCHAR(20),          -- improving, stable, declining
    confidence DECIMAL(3,2),
    key_phrases NVARCHAR(MAX),             -- JSON array
    concerns NVARCHAR(MAX),                -- JSON array
    
    -- Compliance
    compliance_status NVARCHAR(20),        -- compliant, warning, breach
    days_since_last_note DECIMAL(5,1),
    days_since_customer_contact DECIMAL(5,1),
    
    -- Risk
    risk_level NVARCHAR(20),               -- low, medium, high
    risk_factors NVARCHAR(MAX),            -- JSON array
    
    -- AI-generated
    summary NVARCHAR(MAX),
    recommendations NVARCHAR(MAX),         -- JSON array
    
    CONSTRAINT fk_analysis_case FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);
GO

CREATE INDEX idx_analyses_case ON case_analyses(case_id);
CREATE INDEX idx_analyses_date ON case_analyses(analyzed_at);
CREATE INDEX idx_analyses_risk ON case_analyses(risk_level);
GO

-- Individual communication event metrics (for detailed analysis)
CREATE TABLE communication_metrics (
    id INT IDENTITY(1,1) PRIMARY KEY,
    case_id NVARCHAR(50) NOT NULL,
    timeline_entry_id NVARCHAR(50) NOT NULL,
    engineer_id NVARCHAR(50) NOT NULL,
    
    -- Timing
    event_timestamp DATETIME2 NOT NULL,
    response_time_hours DECIMAL(10,2),     -- Time since last customer msg (NULL if not applicable)
    
    -- Sentiment of this specific message
    sentiment_score DECIMAL(3,2),
    
    -- Tone analysis (from AI)
    tone_professional BIT,
    tone_empathetic BIT,
    tone_proactive BIT,
    tone_defensive BIT,
    
    -- Expectation setting
    sets_timeline_expectation BIT,
    sets_next_steps BIT,
    acknowledges_customer_concern BIT,
    
    analyzed_at DATETIME2 DEFAULT GETUTCDATE(),
    
    CONSTRAINT fk_metrics_case FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
    CONSTRAINT fk_metrics_timeline FOREIGN KEY (timeline_entry_id) REFERENCES timeline_entries(id),
    CONSTRAINT fk_metrics_engineer FOREIGN KEY (engineer_id) REFERENCES engineers(id)
);
GO

CREATE INDEX idx_comm_metrics_case ON communication_metrics(case_id);
CREATE INDEX idx_comm_metrics_engineer ON communication_metrics(engineer_id);
CREATE INDEX idx_comm_metrics_date ON communication_metrics(event_timestamp);
GO

-- Rule violations history
CREATE TABLE rule_violations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    case_id NVARCHAR(50) NOT NULL,
    engineer_id NVARCHAR(50) NOT NULL,
    
    rule_type NVARCHAR(50) NOT NULL,       -- 2_day_communication, 7_day_notes, 5_hour_email_notes
    severity NVARCHAR(20) NOT NULL,        -- warning, breach
    detected_at DATETIME2 DEFAULT GETUTCDATE(),
    days_exceeded DECIMAL(5,2),
    
    resolved_at DATETIME2,                 -- NULL if still open
    resolution_note NVARCHAR(500),
    
    CONSTRAINT fk_violations_case FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
    CONSTRAINT fk_violations_engineer FOREIGN KEY (engineer_id) REFERENCES engineers(id)
);
GO

CREATE INDEX idx_violations_engineer ON rule_violations(engineer_id);
CREATE INDEX idx_violations_case ON rule_violations(case_id);
CREATE INDEX idx_violations_open ON rule_violations(resolved_at) WHERE resolved_at IS NULL;
GO

-- =============================================================================
-- NOTIFICATIONS (For Teams Integration)
-- =============================================================================

CREATE TABLE notifications (
    id INT IDENTITY(1,1) PRIMARY KEY,
    engineer_id NVARCHAR(50) NOT NULL,
    case_id NVARCHAR(50),                  -- NULL for general notifications
    
    notification_type NVARCHAR(50) NOT NULL,  -- csat_risk, rule_violation, sentiment_alert, daily_summary
    title NVARCHAR(200) NOT NULL,
    message NVARCHAR(MAX) NOT NULL,
    priority NVARCHAR(20) NOT NULL,        -- low, medium, high, critical
    
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    sent_at DATETIME2,                     -- When sent to Teams (NULL if pending)
    read_at DATETIME2,                     -- When engineer acknowledged
    dismissed_at DATETIME2,                -- If engineer dismissed without action
    
    CONSTRAINT fk_notif_engineer FOREIGN KEY (engineer_id) REFERENCES engineers(id),
    CONSTRAINT fk_notif_case FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE SET NULL
);
GO

CREATE INDEX idx_notifications_engineer ON notifications(engineer_id);
CREATE INDEX idx_notifications_pending ON notifications(sent_at) WHERE sent_at IS NULL;
CREATE INDEX idx_notifications_created ON notifications(created_at);
GO

-- =============================================================================
-- CONVERSATIONS (Session-based, not long-term retention)
-- =============================================================================

CREATE TABLE conversations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    session_id NVARCHAR(100) NOT NULL UNIQUE,  -- UUID for the session
    engineer_id NVARCHAR(50) NOT NULL,
    case_id NVARCHAR(50),                      -- Optional - if discussing specific case
    
    channel NVARCHAR(50) NOT NULL,             -- teams, api, web
    started_at DATETIME2 DEFAULT GETUTCDATE(),
    last_activity_at DATETIME2 DEFAULT GETUTCDATE(),
    ended_at DATETIME2,                        -- When session ended
    
    CONSTRAINT fk_conv_engineer FOREIGN KEY (engineer_id) REFERENCES engineers(id)
);
GO

CREATE INDEX idx_conversations_engineer ON conversations(engineer_id);
CREATE INDEX idx_conversations_session ON conversations(session_id);
GO

-- Individual messages in conversations (session-based retention)
CREATE TABLE conversation_messages (
    id INT IDENTITY(1,1) PRIMARY KEY,
    conversation_id INT NOT NULL,
    
    role NVARCHAR(20) NOT NULL,            -- user, assistant, system
    content NVARCHAR(MAX) NOT NULL,
    timestamp DATETIME2 DEFAULT GETUTCDATE(),
    
    -- For assistant messages
    tokens_used INT,
    model_used NVARCHAR(50),
    
    CONSTRAINT fk_messages_conv FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);
GO

CREATE INDEX idx_messages_conversation ON conversation_messages(conversation_id);
GO

-- =============================================================================
-- AGGREGATED METRICS (For Manager Dashboard)
-- =============================================================================

CREATE TABLE engineer_metrics (
    id INT IDENTITY(1,1) PRIMARY KEY,
    engineer_id NVARCHAR(50) NOT NULL,
    
    period_type NVARCHAR(20) NOT NULL,     -- daily, weekly, monthly
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Volume
    cases_active INT DEFAULT 0,
    cases_resolved INT DEFAULT 0,
    cases_created INT DEFAULT 0,
    
    -- Response metrics
    avg_response_time_hours DECIMAL(10,2),
    max_response_time_hours DECIMAL(10,2),
    min_response_time_hours DECIMAL(10,2),
    
    -- Communication quality
    avg_sentiment_score DECIMAL(3,2),
    communications_sent INT DEFAULT 0,
    communications_per_case DECIMAL(5,2),
    
    -- Proactivity
    proactive_updates_count INT DEFAULT 0,    -- Updates without customer prompting
    reactive_updates_count INT DEFAULT 0,     -- Updates after customer reached out
    proactive_ratio DECIMAL(3,2),             -- proactive / total
    
    -- Compliance
    rule_violations_count INT DEFAULT 0,
    two_day_violations INT DEFAULT 0,
    seven_day_violations INT DEFAULT 0,
    five_hour_violations INT DEFAULT 0,
    
    -- Tone/Quality (from AI analysis)
    tone_professional_pct DECIMAL(5,2),
    tone_empathetic_pct DECIMAL(5,2),
    expectation_setting_pct DECIMAL(5,2),     -- % of comms that set expectations
    
    calculated_at DATETIME2 DEFAULT GETUTCDATE(),
    
    CONSTRAINT fk_engmetrics_engineer FOREIGN KEY (engineer_id) REFERENCES engineers(id),
    CONSTRAINT uq_engineer_period UNIQUE (engineer_id, period_type, period_start)
);
GO

CREATE INDEX idx_engmetrics_engineer ON engineer_metrics(engineer_id);
CREATE INDEX idx_engmetrics_period ON engineer_metrics(period_start);
GO

-- =============================================================================
-- MANAGER ALERT QUEUE (For nightly email job)
-- =============================================================================

CREATE TABLE manager_alert_queue (
    id INT IDENTITY(1,1) PRIMARY KEY,
    manager_id NVARCHAR(50) NOT NULL,
    engineer_id NVARCHAR(50) NOT NULL,
    case_id NVARCHAR(50) NOT NULL,
    
    alert_type NVARCHAR(50) NOT NULL,      -- high_risk_case, rule_breach, sentiment_decline
    alert_priority NVARCHAR(20) NOT NULL,  -- high, critical
    summary NVARCHAR(MAX) NOT NULL,
    
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    included_in_email_at DATETIME2,        -- When included in manager email
    email_batch_id NVARCHAR(50),           -- Groups alerts sent in same email
    
    CONSTRAINT fk_alert_manager FOREIGN KEY (manager_id) REFERENCES engineers(id),
    CONSTRAINT fk_alert_engineer FOREIGN KEY (engineer_id) REFERENCES engineers(id),
    CONSTRAINT fk_alert_case FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);
GO

CREATE INDEX idx_alerts_manager ON manager_alert_queue(manager_id);
CREATE INDEX idx_alerts_pending ON manager_alert_queue(included_in_email_at) WHERE included_in_email_at IS NULL;
GO

-- =============================================================================
-- DATA RETENTION POLICY HELPER
-- =============================================================================

-- View for identifying data to clean up (90 day retention for metrics)
CREATE VIEW vw_data_retention AS
SELECT 
    'case_analyses' as table_name,
    COUNT(*) as records_to_delete,
    MIN(analyzed_at) as oldest_record
FROM case_analyses 
WHERE analyzed_at < DATEADD(day, -90, GETUTCDATE())

UNION ALL

SELECT 
    'communication_metrics',
    COUNT(*),
    MIN(analyzed_at)
FROM communication_metrics 
WHERE analyzed_at < DATEADD(day, -90, GETUTCDATE())

UNION ALL

SELECT 
    'rule_violations',
    COUNT(*),
    MIN(detected_at)
FROM rule_violations 
WHERE detected_at < DATEADD(day, -90, GETUTCDATE())
  AND resolved_at IS NOT NULL  -- Keep open violations

UNION ALL

SELECT 
    'engineer_metrics',
    COUNT(*),
    MIN(period_start)
FROM engineer_metrics 
WHERE period_start < DATEADD(day, -90, GETUTCDATE())

UNION ALL

SELECT 
    'conversations',
    COUNT(*),
    MIN(started_at)
FROM conversations 
WHERE ended_at IS NOT NULL 
  AND ended_at < DATEADD(day, -7, GETUTCDATE());  -- 7 day retention for ended sessions
GO

PRINT 'Schema created successfully!';
PRINT '';
PRINT 'Tables created:';
PRINT '  - engineers';
PRINT '  - customers';
PRINT '  - cases';
PRINT '  - timeline_entries';
PRINT '  - case_analyses';
PRINT '  - communication_metrics';
PRINT '  - rule_violations';
PRINT '  - notifications';
PRINT '  - conversations';
PRINT '  - conversation_messages';
PRINT '  - engineer_metrics';
PRINT '  - manager_alert_queue';
PRINT '';
PRINT 'Views created:';
PRINT '  - vw_data_retention';
GO
