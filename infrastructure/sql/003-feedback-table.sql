-- =============================================================================
-- CSAT Guardian - Feedback Table
-- =============================================================================
-- Stores user feedback (thumbs up/down with comments)
-- Run this after the main schema is created
-- =============================================================================

-- Drop if exists for clean rebuild
IF OBJECT_ID('feedback', 'U') IS NOT NULL DROP TABLE feedback;
GO

-- Feedback table
CREATE TABLE feedback (
    id NVARCHAR(50) PRIMARY KEY,
    rating NVARCHAR(20) NOT NULL,           -- 'positive' or 'negative'
    comment NVARCHAR(MAX),                  -- Optional user comment
    category NVARCHAR(50) DEFAULT 'general', -- general, ui, coaching, performance, feature, bug
    page NVARCHAR(100),                     -- Page/view where feedback was submitted
    engineer_id NVARCHAR(50),               -- Engineer ID if logged in (optional)
    user_agent NVARCHAR(500),               -- Browser user agent for debugging
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    
    CONSTRAINT chk_feedback_rating CHECK (rating IN ('positive', 'negative'))
);
GO

CREATE INDEX idx_feedback_created ON feedback(created_at DESC);
CREATE INDEX idx_feedback_rating ON feedback(rating);
CREATE INDEX idx_feedback_category ON feedback(category);
GO

PRINT 'Feedback table created successfully!';
GO
