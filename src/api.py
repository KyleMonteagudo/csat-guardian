# =============================================================================
# CSAT Guardian - FastAPI Backend
# =============================================================================
# Production-ready REST API for CSAT Guardian.
#
# Endpoints:
#   GET  /                    - Health check and API info
#   GET  /api/health          - Detailed health status
#   GET  /api/engineers       - List all engineers
#   GET  /api/cases           - List cases (with optional filters)
#   GET  /api/cases/{id}      - Get case details
#   POST /api/analyze/{id}    - Analyze case sentiment
#   POST /api/chat            - Chat with the agent
#   GET  /api/alerts          - List recent alerts
#
# This API uses the same service layer as the CLI/monitor modes,
# ensuring consistent behavior across all interfaces.
#
# Run locally:
#   uvicorn api:app --host 0.0.0.0 --port 8000 --reload
#
# =============================================================================

import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Local imports
from config import get_config, AppConfig
from models import Case, Engineer, CaseStatus, CaseSeverity, SentimentResult
from logger import get_logger

# Get logger
logger = get_logger(__name__)


# =============================================================================
# Pydantic Models for API
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    timestamp: str
    services: dict


class CaseListResponse(BaseModel):
    """Response for case list endpoint."""
    count: int
    cases: List[dict]


class AnalyzeRequest(BaseModel):
    """Request for case analysis."""
    include_recommendations: bool = True


class AnalyzeResponse(BaseModel):
    """Response for case analysis."""
    case_id: str
    sentiment: dict
    recommendations: List[str]
    analyzed_at: str
    verbose_analysis: Optional[str] = None  # Detailed narrative analysis
    timeline_insights: Optional[List[dict]] = None  # Per-entry insights


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str
    case_id: Optional[str] = None
    engineer_id: Optional[str] = None
    session_id: Optional[str] = None  # For maintaining conversation context


class ChatResponse(BaseModel):
    """Response for chat endpoint."""
    response: str
    case_context: Optional[dict] = None
    suggestions: List[str] = []


class PIITestRequest(BaseModel):
    """Request for PII scrubbing test endpoint."""
    text: str


class PIITestResponse(BaseModel):
    """Response for PII scrubbing test endpoint."""
    original: str
    scrubbed: str
    items_redacted: int
    content_safety_enabled: bool


class FeedbackRequest(BaseModel):
    """Request for submitting user feedback."""
    rating: str = Field(..., description="'positive' or 'negative'")
    comment: Optional[str] = Field(None, description="Optional feedback comment")
    category: str = Field("general", description="Feedback category")
    page: Optional[str] = Field(None, description="Page/view where feedback was submitted")
    engineer_id: Optional[str] = Field(None, description="Current engineer ID if logged in")
    user_agent: Optional[str] = Field(None, description="Browser user agent")


class FeedbackResponse(BaseModel):
    """Response for feedback submission."""
    id: str
    success: bool
    message: str


class FeedbackItem(BaseModel):
    """A single feedback entry."""
    id: str
    rating: str
    comment: Optional[str]
    category: str
    page: Optional[str]
    engineer_id: Optional[str]
    created_at: str
    user_agent: Optional[str]


# =============================================================================
# Application State
# =============================================================================

class AppState:
    """Holds application state and service instances."""
    config: Optional[AppConfig] = None
    dfm_client = None
    sentiment_service = None
    initialized: bool = False


app_state = AppState()


# =============================================================================
# Lifecycle Management
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    Initializes services on startup and cleans up on shutdown.
    """
    logger.info("Starting CSAT Guardian API...")
    
    # Load configuration
    try:
        app_state.config = get_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load full configuration: {e}")
        logger.info("Continuing with default settings for POC")
    
    # Check if we should use in-memory mock data (for demos/hackathon)
    use_mock_data = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
    
    # Initialize DfM client - try Azure SQL adapter first, then in-memory mock
    if not use_mock_data:
        try:
            from clients.azure_sql_adapter import get_azure_sql_adapter
            app_state.dfm_client = await get_azure_sql_adapter()
            logger.info("DfM client initialized (Azure SQL)")
        except Exception as e:
            logger.warning(f"Azure SQL adapter failed: {e}")
            use_mock_data = True  # Fall back to mock
    
    if use_mock_data or app_state.dfm_client is None:
        logger.info("Using in-memory mock client with rich sample data")
        try:
            from clients.dfm_client_memory import get_in_memory_dfm_client
            app_state.dfm_client = get_in_memory_dfm_client()
            logger.info("DfM client initialized (In-Memory Mock - 8 test cases loaded)")
        except Exception as e2:
            logger.warning(f"In-memory mock client also failed: {e2}")
            # Last resort: try the SQLite mock
            try:
                from clients.dfm_client import get_dfm_client
                app_state.dfm_client = await get_dfm_client(app_state.config)
                logger.info("DfM client initialized (SQLite Mock)")
            except Exception as e3:
                logger.error(f"All DfM client options failed: {e3}")
    
    # Initialize sentiment service
    try:
        from services.sentiment_service import SentimentAnalysisService
        app_state.sentiment_service = SentimentAnalysisService(app_state.config)
        logger.info("Sentiment service initialized")
    except Exception as e:
        logger.warning(f"Sentiment service initialization failed: {e}")
    
    app_state.initialized = True
    logger.info("CSAT Guardian API started successfully")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down CSAT Guardian API...")
    if app_state.dfm_client:
        try:
            await app_state.dfm_client.close()
        except Exception:
            pass
    logger.info("CSAT Guardian API shutdown complete")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="CSAT Guardian API",
    description="Proactive CSAT Risk Detection and Intervention",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health & Info Endpoints
# =============================================================================

@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint - basic API info."""
    return {
        "name": "CSAT Guardian API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check endpoint."""
    services = {
        "api": "healthy",
        "config": "healthy" if app_state.config else "unavailable",
        "dfm_client": "healthy" if app_state.dfm_client else "unavailable",
        "sentiment_service": "healthy" if app_state.sentiment_service else "unavailable"
    }
    
    overall_status = "healthy" if all(v == "healthy" for v in services.values()) else "degraded"
    
    # Get environment from env var or default
    environment = os.environ.get("ENVIRONMENT", "dev")
    
    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        environment=environment,
        timestamp=datetime.utcnow().isoformat(),
        services=services
    )


# =============================================================================
# PII Test Endpoint (Development/Verification)
# =============================================================================

@app.post("/api/test-pii", response_model=PIITestResponse)
async def test_pii_scrubbing(request: PIITestRequest):
    """
    Test PII scrubbing functionality.
    
    This endpoint demonstrates the PII scrubbing that happens before
    any text is sent to Azure OpenAI. Use it to verify that sensitive
    information is properly redacted.
    
    **Note**: This is a development/verification endpoint.
    """
    from services.privacy import get_privacy_service
    
    privacy = get_privacy_service()
    
    # Get original length
    original_text = request.text
    original_len = len(original_text)
    
    # Scrub the text
    scrubbed_text = privacy.scrub(original_text)
    scrubbed_len = len(scrubbed_text)
    
    # Count redactions (rough estimate based on redaction tokens found)
    import re
    redaction_pattern = r'\[(EMAIL|PHONE|IP|SSN|CARD|CUSTOMER_ID|ID|URL|KEY)_REDACTED'
    redactions = len(re.findall(redaction_pattern, scrubbed_text))
    
    return PIITestResponse(
        original=original_text,
        scrubbed=scrubbed_text,
        items_redacted=redactions,
        content_safety_enabled=privacy.use_content_safety
    )


# =============================================================================
# Fast Summary Endpoint (Performance Optimized)
# =============================================================================

@app.get("/api/manager/summary")
async def get_manager_summary():
    """
    Fast summary endpoint for manager dashboard.
    Uses SQL aggregation to avoid N+1 queries.
    Returns engineer summaries with case counts and staleness metrics.
    """
    # Try to use direct SQL for performance
    db_manager = None
    try:
        if app_state.dfm_client and hasattr(app_state.dfm_client, '_ensure_db'):
            db_manager = app_state.dfm_client._ensure_db()
        elif app_state.dfm_client and hasattr(app_state.dfm_client, '_db'):
            db_manager = app_state.dfm_client._db
    except:
        pass
    
    if not db_manager:
        # Fallback to slow method if no direct DB access
        logger.warning("Manager summary: No direct DB access, using slow method")
        return await _get_manager_summary_slow()
    
    try:
        conn = db_manager.connect()
        cursor = conn.cursor()
        
        # Single query to get engineer summaries with aggregated metrics
        cursor.execute("""
            SELECT 
                e.id as engineer_id,
                e.name as engineer_name,
                e.email as engineer_email,
                e.team as engineer_team,
                COUNT(CASE WHEN c.status = 'active' THEN 1 END) as active_cases,
                COUNT(CASE WHEN c.status = 'resolved' THEN 1 END) as resolved_cases,
                COUNT(c.id) as total_cases,
                MAX(CASE WHEN c.status = 'active' THEN 
                    DATEDIFF(day, (
                        SELECT MAX(te.created_on) FROM timeline_entries te 
                        WHERE te.case_id = c.id AND te.entry_type IN ('email_sent', 'email_received')
                    ), GETUTCDATE())
                END) as max_days_since_comm,
                AVG(CASE WHEN c.status = 'active' THEN 
                    DATEDIFF(day, (
                        SELECT MAX(te.created_on) FROM timeline_entries te 
                        WHERE te.case_id = c.id AND te.entry_type IN ('email_sent', 'email_received')
                    ), GETUTCDATE())
                END) as avg_days_since_comm
            FROM engineers e
            LEFT JOIN cases c ON c.owner_id = e.id
            WHERE e.id LIKE 'eng-%'
            GROUP BY e.id, e.name, e.email, e.team
            ORDER BY e.name
        """)
        
        engineers = []
        for row in cursor.fetchall():
            # Determine risk level based on staleness
            max_days = row.max_days_since_comm or 0
            avg_days = row.avg_days_since_comm or 0
            
            if max_days >= 7:
                risk_level = "critical"
            elif max_days >= 4 or avg_days >= 3:
                risk_level = "at_risk"
            else:
                risk_level = "healthy"
            
            engineers.append({
                "id": row.engineer_id,
                "name": row.engineer_name,
                "email": row.engineer_email,
                "team": row.engineer_team,
                "active_cases": row.active_cases or 0,
                "resolved_cases": row.resolved_cases or 0,
                "total_cases": row.total_cases or 0,
                "max_days_since_comm": max_days,
                "avg_days_since_comm": round(avg_days, 1) if avg_days else 0,
                "risk_level": risk_level
            })
        
        # Get overall stats
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved,
                COUNT(*) as total
            FROM cases
        """)
        stats_row = cursor.fetchone()
        
        conn.close()
        
        return {
            "engineers": engineers,
            "stats": {
                "total_engineers": len(engineers),
                "total_active_cases": stats_row.active or 0,
                "total_resolved_cases": stats_row.resolved or 0,
                "total_cases": stats_row.total or 0
            }
        }
    except Exception as e:
        logger.error(f"Manager summary SQL failed: {e}")
        return await _get_manager_summary_slow()


async def _get_manager_summary_slow():
    """Fallback slow method for manager summary (loads all cases)."""
    if not app_state.dfm_client:
        raise HTTPException(status_code=503, detail="DfM client not available")
    
    engineers = await app_state.dfm_client.get_engineers()
    return {
        "engineers": [
            {"id": e.id, "name": e.name, "email": e.email, "active_cases": 0, "risk_level": "unknown"}
            for e in engineers if e.id.startswith('eng-')
        ],
        "stats": {"total_engineers": len([e for e in engineers if e.id.startswith('eng-')])}
    }


@app.get("/api/engineer/{engineer_id}/summary")
async def get_engineer_summary(engineer_id: str):
    """
    Fast engineer detail endpoint using SQL aggregation.
    Returns case list with staleness metrics without loading all timeline entries.
    """
    # Try to use direct SQL for performance
    db_manager = None
    try:
        if app_state.dfm_client and hasattr(app_state.dfm_client, '_ensure_db'):
            db_manager = app_state.dfm_client._ensure_db()
        elif app_state.dfm_client and hasattr(app_state.dfm_client, '_db'):
            db_manager = app_state.dfm_client._db
    except:
        pass
    
    if not db_manager:
        raise HTTPException(status_code=503, detail="Direct database access required for performance")
    
    try:
        conn = db_manager.connect()
        cursor = conn.cursor()
        
        # Get engineer info
        cursor.execute("""
            SELECT id, name, email, team FROM engineers WHERE id = ?
        """, (engineer_id,))
        eng_row = cursor.fetchone()
        if not eng_row:
            raise HTTPException(status_code=404, detail="Engineer not found")
        
        # Get cases with computed staleness (single query with subqueries)
        cursor.execute("""
            SELECT 
                c.id,
                c.title,
                c.status,
                c.priority,
                c.created_on,
                cu.company as customer_name,
                cu.tier as customer_tier,
                DATEDIFF(day, (
                    SELECT MAX(te.created_on) FROM timeline_entries te 
                    WHERE te.case_id = c.id AND te.entry_type IN ('email_sent', 'email_received')
                ), GETUTCDATE()) as days_since_comm,
                DATEDIFF(day, (
                    SELECT MAX(te.created_on) FROM timeline_entries te 
                    WHERE te.case_id = c.id AND te.entry_type = 'note'
                ), GETUTCDATE()) as days_since_note,
                (SELECT COUNT(*) FROM timeline_entries te WHERE te.case_id = c.id) as timeline_count
            FROM cases c
            LEFT JOIN customers cu ON cu.id = c.customer_id
            WHERE c.owner_id = ?
            ORDER BY 
                CASE WHEN c.status = 'active' THEN 0 ELSE 1 END,
                c.created_on DESC
        """, (engineer_id,))
        
        cases = []
        active_count = 0
        at_risk_count = 0
        breach_count = 0
        
        for row in cursor.fetchall():
            days_comm = row.days_since_comm if row.days_since_comm is not None else 999
            days_note = row.days_since_note if row.days_since_note is not None else 999
            
            # Determine risk level
            if row.status == 'active':
                active_count += 1
                if days_comm >= 7 or days_note >= 7:
                    risk_level = "breach"
                    breach_count += 1
                elif days_comm >= 4 or days_note >= 4:
                    risk_level = "at_risk"
                    at_risk_count += 1
                else:
                    risk_level = "healthy"
            else:
                risk_level = "resolved"
            
            cases.append({
                "id": row.id,
                "title": row.title,
                "status": row.status,
                "priority": row.priority,
                "created_on": row.created_on.isoformat() if row.created_on else None,
                "customer_name": row.customer_name or "Unknown",
                "customer_tier": row.customer_tier or "Unknown",
                "days_since_comm": days_comm if days_comm < 999 else None,
                "days_since_note": days_note if days_note < 999 else None,
                "timeline_count": row.timeline_count or 0,
                "risk_level": risk_level
            })
        
        conn.close()
        
        return {
            "engineer": {
                "id": eng_row.id,
                "name": eng_row.name,
                "email": eng_row.email,
                "team": eng_row.team
            },
            "summary": {
                "total_cases": len(cases),
                "active_cases": active_count,
                "at_risk_count": at_risk_count,
                "breach_count": breach_count
            },
            "cases": cases
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Engineer summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Engineer Endpoints
# =============================================================================

@app.get("/api/engineers")
async def list_engineers():
    """List all engineers."""
    if not app_state.dfm_client:
        raise HTTPException(status_code=503, detail="DfM client not available")
    
    try:
        engineers = await app_state.dfm_client.get_engineers()
        return {
            "count": len(engineers),
            "engineers": [
                {
                    "id": e.id,
                    "name": e.name,
                    "email": e.email
                }
                for e in engineers
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list engineers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Case Endpoints
# =============================================================================

@app.get("/api/cases")
async def list_cases(
    engineer_id: Optional[str] = Query(None, description="Filter by engineer ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity (sev_a, sev_b, sev_c)")
):
    """
    List cases with optional filters.
    
    - **engineer_id**: Filter cases by assigned engineer
    - **status**: Filter by case status (active, resolved, etc.)
    - **severity**: Filter by severity (sev_a, sev_b, sev_c)
    """
    if not app_state.dfm_client:
        raise HTTPException(status_code=503, detail="DfM client not available")
    
    try:
        if engineer_id:
            cases = await app_state.dfm_client.get_cases_by_owner(engineer_id)
        else:
            cases = await app_state.dfm_client.get_active_cases()
        
        # Apply filters
        if status:
            cases = [c for c in cases if c.status.value == status]
        if severity:
            cases = [c for c in cases if c.severity.value == severity]
        
        # Calculate sentiment/CSAT risk for each case based on timeline content
        case_data = []
        for c in cases:
            # Calculate CSAT risk score based on customer communications
            csat_risk_score = _calculate_csat_risk(c)
            
            case_data.append({
                "id": c.id,
                "title": c.title,
                "status": c.status.value,
                "severity": c.severity.value,
                "customer": {"company": c.customer.company, "tier": c.customer.tier} if c.customer else None,
                "owner": {"id": c.owner.id, "name": c.owner.name} if c.owner else None,
                "created_on": c.created_on.isoformat() if c.created_on else None,
                "days_since_last_note": c.days_since_last_note,
                "days_since_last_outbound": c.days_since_last_outbound,
                "timeline_count": len(c.timeline) if c.timeline else 0,
                "sentiment_score": csat_risk_score,  # CSAT risk (0=high risk, 1=low risk)
                "csat_risk": _get_risk_label(csat_risk_score),
            })
        
        return {
            "count": len(case_data),
            "cases": case_data
        }
    except Exception as e:
        logger.error(f"Failed to list cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _calculate_csat_risk(case) -> float:
    """
    Calculate CSAT risk score for a case based on customer communications.
    
    Returns a score from 0 to 1 where:
    - 0.0-0.3 = High risk (customer frustrated)
    - 0.3-0.6 = Medium risk (some concerns)
    - 0.6-1.0 = Low risk (customer satisfied)
    """
    # Get customer communications
    customer_msgs = [
        e for e in case.timeline 
        if e.is_customer_communication or e.created_by == "Customer"
    ]
    
    if not customer_msgs:
        return 0.6  # Neutral if no customer comms yet
    
    # Analyze sentiment indicators in customer messages
    frustration_indicators = [
        'frustrated', 'disappointed', 'unacceptable', 'urgent', 'escalate',
        'waiting', 'still no', 'again', 'furious', 'angry', 'legal',
        'manager', 'complaint', 'nightmare', 'unacceptable', 'terrible',
        'horrible', 'worst', 'ridiculous', 'outrageous', 'days', 'hours',
        'no response', 'no update', 'ignored'
    ]
    positive_indicators = [
        'thank', 'great', 'appreciate', 'helpful', 'excellent', 'resolved',
        'perfect', 'amazing', 'wonderful', 'fantastic', 'awesome', 'good job',
        'well done', 'impressed', 'saved', 'exactly what', 'works great'
    ]
    
    # Weight more recent messages higher
    total_score = 0.0
    total_weight = 0.0
    
    for i, msg in enumerate(customer_msgs):
        content_lower = msg.content.lower()
        
        # Count indicators
        frustration_count = sum(1 for word in frustration_indicators if word in content_lower)
        positive_count = sum(1 for word in positive_indicators if word in content_lower)
        
        # Calculate message score (0-1)
        if frustration_count > positive_count:
            # More frustration = lower score
            msg_score = max(0.1, 0.5 - (frustration_count * 0.1))
        elif positive_count > 0:
            msg_score = min(0.95, 0.7 + (positive_count * 0.05))
        else:
            msg_score = 0.5  # Neutral
        
        # Weight recent messages more (exponential)
        weight = 1.0 + (i * 0.5)  # Later messages get more weight
        total_score += msg_score * weight
        total_weight += weight
    
    # Calculate weighted average
    avg_score = total_score / total_weight if total_weight > 0 else 0.5
    
    # Factor in communication gaps (2-day rule violation = risk)
    days_since_outbound = case.days_since_last_outbound
    if days_since_outbound > 3:
        avg_score = max(0.1, avg_score - 0.2)  # Penalize for no communication
    elif days_since_outbound > 2:
        avg_score = max(0.2, avg_score - 0.1)
    
    return round(avg_score, 2)


def _get_risk_label(score: float) -> str:
    """Get CSAT risk label from score."""
    if score < 0.35:
        return "critical"
    elif score < 0.55:
        return "at_risk"
    else:
        return "healthy"


@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    """Get detailed case information including timeline."""
    if not app_state.dfm_client:
        raise HTTPException(status_code=503, detail="DfM client not available")
    
    try:
        case = await app_state.dfm_client.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        # Calculate CSAT risk
        csat_risk_score = _calculate_csat_risk(case)
        
        return {
            "id": case.id,
            "title": case.title,
            "description": case.description,
            "status": case.status.value,
            "severity": case.severity.value,
            "customer": {
                "id": case.customer.id,
                "company": case.customer.company,
                "tier": case.customer.tier
            } if case.customer else None,
            "owner": {
                "id": case.owner.id,
                "name": case.owner.name,
                "email": case.owner.email
            } if case.owner else None,
            "created_on": case.created_on.isoformat() if case.created_on else None,
            "modified_on": case.modified_on.isoformat() if case.modified_on else None,
            "days_open": case.days_since_creation,
            "days_since_last_note": case.days_since_last_note,
            "days_since_last_outbound": case.days_since_last_outbound,
            "sentiment_score": csat_risk_score,
            "csat_risk": _get_risk_label(csat_risk_score),
            "timeline": [
                {
                    "id": t.id,
                    "type": t.entry_type.value,
                    "subject": t.subject,
                    "content": t.content,
                    "created_on": t.created_on.isoformat() if t.created_on else None,
                    "created_by": t.created_by,
                    "is_customer": t.is_customer_communication
                }
                for t in (case.timeline or [])
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Analysis Endpoints
# =============================================================================

@app.post("/api/analyze/{case_id}", response_model=AnalyzeResponse)
async def analyze_case(case_id: str, request: AnalyzeRequest = None):
    """
    Analyze case sentiment using Azure OpenAI.
    
    This performs real sentiment analysis on the case content and timeline,
    returning sentiment scores, key phrases, and recommendations.
    """
    if not app_state.dfm_client:
        raise HTTPException(status_code=503, detail="DfM client not available")
    if not app_state.sentiment_service:
        raise HTTPException(status_code=503, detail="Sentiment service not available")
    
    try:
        # Get case
        case = await app_state.dfm_client.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        # Analyze sentiment - returns CaseAnalysis with overall_sentiment
        result = await app_state.sentiment_service.analyze_case(case)
        sentiment = result.overall_sentiment
        
        # Generate verbose narrative analysis
        verbose_analysis = await _generate_verbose_analysis(case, result)
        
        # Generate per-timeline-entry insights
        timeline_insights = _generate_timeline_insights(case, result)
        
        return AnalyzeResponse(
            case_id=case_id,
            sentiment={
                "score": sentiment.score,
                "label": sentiment.label.value,
                "confidence": sentiment.confidence,
                "trend": result.sentiment_trend,
                "key_phrases": sentiment.key_phrases or [],
                "concerns": sentiment.concerns or []
            },
            recommendations=result.recommendations or [],
            analyzed_at=datetime.utcnow().isoformat(),
            verbose_analysis=verbose_analysis,
            timeline_insights=timeline_insights
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_verbose_analysis(case, analysis_result) -> str:
    """Generate a detailed narrative analysis of the case."""
    sentiment = analysis_result.overall_sentiment
    
    # Build narrative based on actual case data
    narrative = f"""## Sentiment Analysis for {case.id}

### Overall Assessment
The customer sentiment is **{sentiment.label.value.upper()}** with a confidence score of {sentiment.confidence:.0%}. 
The sentiment score is {sentiment.score:.2f} on a scale of 0 (very negative) to 1 (very positive).

### Sentiment Trend
{analysis_result.sentiment_trend}

### Key Observations from Communications
"""
    
    # Add key phrases with context
    if sentiment.key_phrases:
        narrative += "\n**Notable phrases from customer communications:**\n"
        for phrase in sentiment.key_phrases[:5]:
            narrative += f'- *"{phrase}"*\n'
    
    # Add concerns
    if sentiment.concerns:
        narrative += "\n**Identified Customer Concerns:**\n"
        for concern in sentiment.concerns[:5]:
            narrative += f"- {concern}\n"
    
    # Add compliance status
    narrative += f"""
### CSAT Rule Compliance
- **7-Day Notes Rule:** {analysis_result.compliance_status.upper()}
- **Days Since Last Note:** {analysis_result.days_since_last_note:.1f} days
"""
    
    # Add specific timeline observations
    if case.timeline:
        narrative += "\n### Communication Timeline Analysis\n"
        
        # Check for communication gaps
        customer_comms = [e for e in case.timeline if e.is_customer_communication]
        engineer_comms = [e for e in case.timeline if not e.is_customer_communication and e.entry_type.value in ['email_sent', 'phone_call']]
        
        if customer_comms:
            last_customer = customer_comms[-1]
            narrative += f"- **Last customer contact:** {last_customer.created_on.strftime('%Y-%m-%d')} - "
            narrative += f'"{last_customer.content[:100]}..."\n'
        
        if engineer_comms:
            last_engineer = engineer_comms[-1]
            narrative += f"- **Last engineer response:** {last_engineer.created_on.strftime('%Y-%m-%d')}\n"
    
    # Add recommendations summary
    if analysis_result.recommendations:
        narrative += "\n### Recommended Actions\n"
        for i, rec in enumerate(analysis_result.recommendations[:5], 1):
            narrative += f"{i}. {rec}\n"
    
    return narrative


def _generate_timeline_insights(case, analysis_result) -> list:
    """Generate per-entry insights for the timeline."""
    insights = []
    
    for entry in case.timeline[-10:]:  # Last 10 entries
        insight = {
            "entry_id": entry.id,
            "date": entry.created_on.isoformat(),
            "type": entry.entry_type.value,
            "author": entry.created_by,
            "is_customer": entry.is_customer_communication,
            "content_preview": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
        }
        
        # Add sentiment indicator based on content analysis
        content_lower = entry.content.lower()
        if entry.is_customer_communication:
            # Check for frustration indicators
            frustration_words = ['frustrated', 'disappointed', 'unacceptable', 'urgent', 'escalate', 'waiting', 'still no', 'again']
            positive_words = ['thank', 'great', 'appreciate', 'helpful', 'excellent', 'resolved']
            
            frustration_count = sum(1 for word in frustration_words if word in content_lower)
            positive_count = sum(1 for word in positive_words if word in content_lower)
            
            if frustration_count > positive_count:
                insight["sentiment_indicator"] = "⚠️ Signs of frustration"
                insight["detected_phrases"] = [w for w in frustration_words if w in content_lower]
            elif positive_count > 0:
                insight["sentiment_indicator"] = "✅ Positive tone"
                insight["detected_phrases"] = [w for w in positive_words if w in content_lower]
            else:
                insight["sentiment_indicator"] = "➡️ Neutral"
                insight["detected_phrases"] = []
        else:
            insight["sentiment_indicator"] = "📝 Engineer activity"
            insight["detected_phrases"] = []
        
        insights.append(insight)
    
    return insights


# =============================================================================
# Chat Endpoint - Powered by Semantic Kernel Agent
# =============================================================================

# Store active agent sessions (in production, use Redis or similar)
_agent_sessions: dict = {}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the CSAT Guardian agent.
    
    The agent uses Semantic Kernel with Azure OpenAI to:
    - Check CSAT rule compliance
    - Analyze case communication timelines
    - Provide specific, actionable coaching
    - Reference actual case events and patterns
    
    Optionally provide case_id for case-specific context.
    """
    try:
        from agent.guardian_agent import CSATGuardianAgent
        
        # Get or create an agent for this session/engineer
        # For POC, use a default engineer - in production, get from auth context
        engineer_id = request.engineer_id or "eng-001"
        
        # Get engineer info
        if app_state.dfm_client:
            engineer = await app_state.dfm_client.get_engineer(engineer_id)
            if not engineer:
                # Create a default engineer for POC
                from models import Engineer
                engineer = Engineer(
                    id=engineer_id,
                    name="POC Engineer",
                    email="engineer@contoso.com",
                    team="CSS Support"
                )
        else:
            from models import Engineer
            engineer = Engineer(
                id=engineer_id,
                name="POC Engineer", 
                email="engineer@contoso.com",
                team="CSS Support"
            )
        
        # Get or create agent session
        session_key = f"{engineer_id}_{request.session_id or 'default'}"
        
        if session_key not in _agent_sessions:
            # Create new agent
            from services.sentiment_service import get_sentiment_service
            
            agent = CSATGuardianAgent(
                engineer=engineer,
                dfm_client=app_state.dfm_client,
                sentiment_service=get_sentiment_service(),
                config=app_state.config,
            )
            _agent_sessions[session_key] = agent
            logger.info(f"Created new agent session: {session_key}")
        else:
            agent = _agent_sessions[session_key]
        
        # Build the message with RICH case context if provided
        message = request.message
        if request.case_id and app_state.dfm_client:
            case = await app_state.dfm_client.get_case(request.case_id)
            if case:
                # Build rich context with full timeline
                timeline_text = ""
                for entry in case.timeline:
                    entry_date = entry.created_on.strftime('%Y-%m-%d %H:%M')
                    timeline_text += f"\n[{entry_date}] {entry.entry_type.value.upper()} by {entry.created_by}:\n"
                    if entry.subject:
                        timeline_text += f"Subject: {entry.subject}\n"
                    timeline_text += f"{entry.content}\n"
                    timeline_text += "-" * 40
                
                context = f"""
=== FULL CASE CONTEXT FOR {case.id} ===

CASE DETAILS:
- Title: {case.title}
- Status: {case.status.value}
- Severity: {case.severity.value}
- Customer: {case.customer.company} ({case.customer.tier} tier)
- Owner: {case.owner.name}
- Created: {case.created_on.strftime('%Y-%m-%d')} ({case.days_since_creation:.0f} days ago)
- Last Updated: {case.modified_on.strftime('%Y-%m-%d')}
- Days Since Last Note: {case.days_since_last_note:.1f}

CASE DESCRIPTION:
{case.description}

FULL COMMUNICATION TIMELINE ({len(case.timeline)} entries):
{timeline_text}

=== END CASE CONTEXT ===

The engineer is asking: {request.message}

Provide a detailed, contextual response that references specific emails, dates, and events from the timeline above. Be specific about what you observe in the actual communications."""
                message = context
        
        # Get response from agent
        response_text = await agent.chat(message)
        
        # Get case context if case_id was provided
        case_context = None
        if request.case_id and app_state.dfm_client:
            case = await app_state.dfm_client.get_case(request.case_id)
            if case:
                case_context = {
                    "id": case.id,
                    "title": case.title,
                    "status": case.status.value,
                    "days_since_last_note": case.days_since_last_note,
                    "days_open": case.days_since_creation
                }
        
        # Generate contextual suggestions based on the conversation
        suggestions = _generate_suggestions(request.message, request.case_id)
        
        return ChatResponse(
            response=response_text,
            case_context=case_context,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        
        # Fallback to simple response if agent fails
        return ChatResponse(
            response=f"I encountered an issue processing your request. Please try again or ask a different question. (Error: {str(e)[:100]})",
            case_context=None,
            suggestions=["Check CSAT rules", "List my cases", "What cases need attention?"]
        )


def _generate_suggestions(message: str, case_id: Optional[str]) -> list:
    """Generate contextual follow-up suggestions."""
    message_lower = message.lower()
    
    if case_id:
        # Case-specific suggestions
        return [
            f"Check CSAT rules for {case_id}",
            f"Analyze timeline for {case_id}",
            f"Get coaching for {case_id}"
        ]
    elif any(word in message_lower for word in ["rule", "compliance", "sla"]):
        return [
            "Explain the 2-day rule",
            "Explain the 7-day rule",
            "Check all my cases for compliance"
        ]
    elif any(word in message_lower for word in ["risk", "concern", "worry"]):
        return [
            "Which cases are high risk?",
            "What are the CSAT risk factors?",
            "How can I reduce CSAT risk?"
        ]
    else:
        return [
            "List my cases",
            "Which cases need attention?",
            "Explain CSAT rules"
        ]


# =============================================================================
# Alerts Endpoint
# =============================================================================

@app.get("/api/alerts")
async def list_alerts(
    limit: int = Query(10, ge=1, le=100, description="Maximum alerts to return"),
    engineer_id: Optional[str] = Query(None, description="Filter by engineer")
):
    """
    List recent alerts.
    
    In production, this pulls from the alerts history table.
    For POC, returns generated alerts based on current case status.
    """
    if not app_state.dfm_client:
        raise HTTPException(status_code=503, detail="DfM client not available")
    
    try:
        # Get cases to generate alerts
        if engineer_id:
            cases = await app_state.dfm_client.get_cases_by_owner(engineer_id)
        else:
            cases = await app_state.dfm_client.get_active_cases()
        
        alerts = []
        for case in cases:
            if case.days_since_last_note >= 7:
                alerts.append({
                    "type": "breach",
                    "severity": "critical",
                    "case_id": case.id,
                    "message": f"Case {case.id} has not been updated in {case.days_since_last_note:.0f} days - SLA BREACH",
                    "created_at": datetime.utcnow().isoformat()
                })
            elif case.days_since_last_note >= 5:
                alerts.append({
                    "type": "warning",
                    "severity": "warning",
                    "case_id": case.id,
                    "message": f"Case {case.id} approaching SLA deadline - {case.days_since_last_note:.1f} days since last update",
                    "created_at": datetime.utcnow().isoformat()
                })
        
        # Sort by severity and limit
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 99))
        
        return {
            "count": len(alerts[:limit]),
            "alerts": alerts[:limit]
        }
    except Exception as e:
        logger.error(f"Failed to list alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Feedback Endpoints
# =============================================================================

# In-memory feedback store (for demo/mock mode)
# In production, this would be stored in Azure SQL
_feedback_store: List[dict] = []

@app.post("/api/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit user feedback (thumbs up/down with optional comment).
    
    Stores feedback in Azure SQL database when available,
    or in-memory for demo/mock mode.
    """
    import uuid
    
    feedback_id = str(uuid.uuid4())[:8]
    feedback_entry = {
        "id": feedback_id,
        "rating": feedback.rating,
        "comment": feedback.comment,
        "category": feedback.category,
        "page": feedback.page,
        "engineer_id": feedback.engineer_id,
        "user_agent": feedback.user_agent,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Try to store in database if available
    if app_state.dfm_client and hasattr(app_state.dfm_client, 'db'):
        try:
            db = app_state.dfm_client.db
            db.execute("""
                INSERT INTO feedback (id, rating, comment, category, page, engineer_id, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback_id,
                feedback.rating,
                feedback.comment,
                feedback.category,
                feedback.page,
                feedback.engineer_id,
                feedback.user_agent,
                datetime.utcnow().isoformat()
            ))
            db.commit()
            logger.info(f"Feedback {feedback_id} stored in database")
        except Exception as e:
            logger.warning(f"Database storage failed, using in-memory: {e}")
            _feedback_store.append(feedback_entry)
    else:
        # Use in-memory store for demo mode
        _feedback_store.append(feedback_entry)
        logger.info(f"Feedback {feedback_id} stored in memory")
    
    return FeedbackResponse(
        id=feedback_id,
        success=True,
        message="Thank you for your feedback!"
    )


@app.get("/api/feedback")
async def list_feedback(
    limit: int = Query(50, ge=1, le=500, description="Maximum feedback entries to return"),
    rating: Optional[str] = Query(None, description="Filter by rating: 'positive' or 'negative'"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    List all submitted feedback.
    
    Returns feedback from database or in-memory store.
    """
    feedback_list = []
    
    # Try to get from database first
    if app_state.dfm_client and hasattr(app_state.dfm_client, 'db'):
        try:
            db = app_state.dfm_client.db
            query = "SELECT * FROM feedback"
            conditions = []
            params = []
            
            if rating:
                conditions.append("rating = ?")
                params.append(rating)
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = db.execute(query, params)
            rows = cursor.fetchall()
            
            for row in rows:
                feedback_list.append({
                    "id": row[0],
                    "rating": row[1],
                    "comment": row[2],
                    "category": row[3],
                    "page": row[4],
                    "engineer_id": row[5],
                    "user_agent": row[6],
                    "created_at": row[7]
                })
        except Exception as e:
            logger.warning(f"Database query failed, using in-memory: {e}")
            feedback_list = _feedback_store.copy()
    else:
        # Use in-memory store
        feedback_list = _feedback_store.copy()
    
    # Apply filters to in-memory data if database failed
    if rating:
        feedback_list = [f for f in feedback_list if f.get("rating") == rating]
    if category:
        feedback_list = [f for f in feedback_list if f.get("category") == category]
    
    # Sort by created_at descending and limit
    feedback_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    feedback_list = feedback_list[:limit]
    
    return {
        "count": len(feedback_list),
        "feedback": feedback_list
    }


@app.get("/feedback", response_class=HTMLResponse)
async def feedback_page():
    """
    Render feedback dashboard page.
    """
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSAT Guardian - Feedback Dashboard</title>
    <link rel="stylesheet" href="/static/css/styles.css">
    <style>
        .feedback-dashboard {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        .feedback-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }
        .feedback-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: var(--background-card);
            padding: 1.5rem;
            border-radius: var(--radius-lg);
            text-align: center;
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent-primary);
        }
        .stat-value.positive { color: var(--accent-success); }
        .stat-value.negative { color: var(--accent-warning); }
        .stat-label {
            color: var(--text-tertiary);
            margin-top: 0.5rem;
        }
        .feedback-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        .feedback-entry {
            background: var(--background-card);
            padding: 1.5rem;
            border-radius: var(--radius-md);
            border-left: 4px solid var(--accent-primary);
        }
        .feedback-entry.positive {
            border-left-color: var(--accent-success);
        }
        .feedback-entry.negative {
            border-left-color: var(--accent-warning);
        }
        .feedback-meta {
            display: flex;
            gap: 1rem;
            font-size: 0.85rem;
            color: var(--text-tertiary);
            margin-top: 0.5rem;
        }
        .feedback-rating {
            font-size: 1.5rem;
        }
        .no-feedback {
            text-align: center;
            padding: 3rem;
            color: var(--text-tertiary);
        }
        .back-link {
            color: var(--text-link);
            text-decoration: none;
        }
        .back-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <nav class="top-nav">
        <div class="nav-brand">
            <span style="font-size: 1.5rem;">🛡️</span>
            <span class="nav-product-name" style="font-weight: 600; font-size: 1.1rem;">CSAT Guardian</span>
        </div>
    </nav>
    
    <div class="feedback-dashboard">
        <div class="feedback-header">
            <div>
                <a href="/ui" class="back-link">← Back to App</a>
                <h1 style="margin-top: 1rem;">📊 Feedback Dashboard</h1>
                <p class="text-muted">User feedback and satisfaction metrics</p>
            </div>
        </div>
        
        <div id="feedback-stats" class="feedback-stats">
            <div class="stat-card">
                <div class="stat-value" id="total-count">-</div>
                <div class="stat-label">Total Feedback</div>
            </div>
            <div class="stat-card">
                <div class="stat-value positive" id="positive-count">-</div>
                <div class="stat-label">👍 Positive</div>
            </div>
            <div class="stat-card">
                <div class="stat-value negative" id="negative-count">-</div>
                <div class="stat-label">👎 Needs Work</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="satisfaction-rate">-</div>
                <div class="stat-label">Satisfaction Rate</div>
            </div>
        </div>
        
        <h2>Recent Feedback</h2>
        <div id="feedback-list" class="feedback-list">
            <div class="no-feedback">Loading feedback...</div>
        </div>
    </div>
    
    <script>
        async function loadFeedback() {
            try {
                const response = await fetch('/api/feedback?limit=100');
                const data = await response.json();
                
                const positive = data.feedback.filter(f => f.rating === 'positive').length;
                const negative = data.feedback.filter(f => f.rating === 'negative').length;
                const total = data.feedback.length;
                const satisfactionRate = total > 0 ? Math.round((positive / total) * 100) : 0;
                
                document.getElementById('total-count').textContent = total;
                document.getElementById('positive-count').textContent = positive;
                document.getElementById('negative-count').textContent = negative;
                document.getElementById('satisfaction-rate').textContent = satisfactionRate + '%';
                
                const listEl = document.getElementById('feedback-list');
                
                if (data.feedback.length === 0) {
                    listEl.innerHTML = '<div class="no-feedback">No feedback submitted yet</div>';
                    return;
                }
                
                listEl.innerHTML = data.feedback.map(f => `
                    <div class="feedback-entry ${f.rating}">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <span class="feedback-rating">${f.rating === 'positive' ? '👍' : '👎'}</span>
                                <strong style="margin-left: 0.5rem;">${f.category || 'General'}</strong>
                            </div>
                            <span class="text-muted text-small">${new Date(f.created_at).toLocaleString()}</span>
                        </div>
                        ${f.comment ? `<p style="margin: 1rem 0 0; color: var(--text-secondary);">${f.comment}</p>` : ''}
                        <div class="feedback-meta">
                            <span>Page: ${f.page || 'Unknown'}</span>
                            ${f.engineer_id ? `<span>Engineer: ${f.engineer_id}</span>` : ''}
                            <span>ID: ${f.id}</span>
                        </div>
                    </div>
                `).join('');
                
            } catch (error) {
                console.error('Error loading feedback:', error);
                document.getElementById('feedback-list').innerHTML = 
                    '<div class="no-feedback">Error loading feedback</div>';
            }
        }
        
        loadFeedback();
        // Refresh every 30 seconds
        setInterval(loadFeedback, 30000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content, status_code=200)


# =============================================================================
# Admin Endpoint - Seed Database (Realistic Quarter Workload)
# =============================================================================

@app.post("/api/admin/seed")
async def seed_database(secret: str = Query(..., description="Admin secret key")):
    """
    Seed the database with realistic quarter workload data.
    
    Simulates:
    - 10 support engineers + 3 managers
    - 20 cases per engineer per month (60 per quarter)
    - 600 total cases spanning 90 days
    - ~10-12 active cases per engineer (current workload)
    - ~48-50 resolved cases per engineer (historical)
    - Varied staleness patterns for compliance tracking
    - 2000+ timeline entries with realistic sentiment patterns
    
    IMPORTANT: Staleness (days_since_last_comm, days_since_last_note) is based on
    fixed dates relative to current time to ensure varied compliance patterns.
    """
    import random
    import uuid
    
    # Simple secret check - in production use proper auth
    expected_secret = os.environ.get("ADMIN_SECRET", "csat-seed-2026")
    if secret != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Get the underlying database manager
    # Try multiple approaches since different client types have different structures
    db_manager = None
    client_type = type(app_state.dfm_client).__name__ if app_state.dfm_client else "None"
    
    try:
        if app_state.dfm_client and hasattr(app_state.dfm_client, '_ensure_db'):
            # Azure SQL adapter - call _ensure_db() to get connection
            db_manager = app_state.dfm_client._ensure_db()
            logger.info(f"Seed: Using Azure SQL adapter's database manager")
        elif app_state.dfm_client and hasattr(app_state.dfm_client, '_db') and app_state.dfm_client._db:
            db_manager = app_state.dfm_client._db
            logger.info(f"Seed: Using _db attribute")
        elif app_state.dfm_client and hasattr(app_state.dfm_client, 'db') and app_state.dfm_client.db:
            db_manager = app_state.dfm_client.db
            logger.info(f"Seed: Using db attribute")
        else:
            # Fallback: try to create a fresh database connection
            logger.warning(f"Seed: Current client ({client_type}) has no db access, attempting direct connection")
            try:
                from db_sync import SyncDatabaseManager
                db_manager = SyncDatabaseManager()
                logger.info("Seed: Created fresh SyncDatabaseManager connection")
            except Exception as db_err:
                raise HTTPException(
                    status_code=503, 
                    detail=f"Database not available. Current client: {client_type}. Direct connection failed: {str(db_err)}"
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")
    
    try:
        conn = db_manager.connect()
        cursor = conn.cursor()
        
        # Set random seed for reproducibility
        random.seed(2026)
        
        # =====================================================================
        # Create feedback table if it doesn't exist
        # =====================================================================
        try:
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'feedback')
                CREATE TABLE feedback (
                    id NVARCHAR(50) PRIMARY KEY,
                    rating NVARCHAR(20) NOT NULL,
                    comment NVARCHAR(MAX),
                    category NVARCHAR(50) DEFAULT 'general',
                    page NVARCHAR(100),
                    engineer_id NVARCHAR(50),
                    user_agent NVARCHAR(500),
                    created_at DATETIME2 DEFAULT GETUTCDATE()
                )
            """)
            conn.commit()
        except Exception as e:
            logger.warning(f"Feedback table creation: {e}")
        
        # =====================================================================
        # Clear existing data (order matters for foreign keys)
        # =====================================================================
        for table in ['case_analyses', 'communication_metrics', 'rule_violations', 
                      'notifications', 'engineer_metrics', 'conversation_messages',
                      'conversations', 'manager_alert_queue', 'timeline_entries', 
                      'cases', 'customers', 'engineers', 'feedback']:
            try:
                cursor.execute(f"DELETE FROM {table}")
            except Exception:
                pass  # Table may not exist
        conn.commit()
        
        # =====================================================================
        # ENGINEERS (10 support + 3 managers)
        # =====================================================================
        engineers = [
            # Azure Platform Team (4 engineers)
            ("eng-001", "Sarah Chen", "sarchen@microsoft.com", "Azure Platform", "mgr-001"),
            ("eng-002", "Marcus Johnson", "marjohn@microsoft.com", "Azure Platform", "mgr-001"),
            ("eng-003", "Emily Rodriguez", "emrod@microsoft.com", "Azure Platform", "mgr-001"),
            ("eng-004", "James Kim", "jamkim@microsoft.com", "Azure Platform", "mgr-001"),
            # Azure Data Team (3 engineers)
            ("eng-005", "Priya Patel", "prpatel@microsoft.com", "Azure Data", "mgr-002"),
            ("eng-006", "David Wang", "dawang@microsoft.com", "Azure Data", "mgr-002"),
            ("eng-007", "Lisa Thompson", "lithomp@microsoft.com", "Azure Data", "mgr-002"),
            # M365 Support Team (3 engineers)
            ("eng-008", "Alex Martinez", "almart@microsoft.com", "M365 Support", "mgr-003"),
            ("eng-009", "Jennifer Lee", "jenlee@microsoft.com", "M365 Support", "mgr-003"),
            ("eng-010", "Robert Brown", "robbro@microsoft.com", "M365 Support", "mgr-003"),
            # Managers (not counted as support engineers)
            ("mgr-001", "Michael Scott", "micscott@microsoft.com", "Management", None),
            ("mgr-002", "Angela Martin", "angmart@microsoft.com", "Management", None),
            ("mgr-003", "Jim Halpert", "jimhal@microsoft.com", "Management", None),
        ]
        for e in engineers:
            cursor.execute("""
                INSERT INTO engineers (id, name, email, team, manager_id) 
                VALUES (?, ?, ?, ?, ?)
            """, e)
        
        support_engineers = [e[0] for e in engineers if e[0].startswith('eng-')]
        
        # =====================================================================
        # CUSTOMERS (40 companies for realistic distribution)
        # =====================================================================
        customers = [
            # Premier Tier (10)
            ("cust-001", "Contoso Financial Services", "Premier"),
            ("cust-002", "Fabrikam Industries", "Premier"),
            ("cust-003", "Northwind Traders", "Premier"),
            ("cust-004", "Adventure Works Cycles", "Premier"),
            ("cust-005", "Wide World Importers", "Premier"),
            ("cust-006", "Trey Research", "Premier"),
            ("cust-007", "The Phone Company", "Premier"),
            ("cust-008", "Coho Vineyard", "Premier"),
            ("cust-009", "Alpine Ski House", "Premier"),
            ("cust-010", "Bellows College", "Premier"),
            # Unified Tier (15)
            ("cust-011", "Tailspin Toys", "Unified"),
            ("cust-012", "Wingtip Toys", "Unified"),
            ("cust-013", "Fourth Coffee", "Unified"),
            ("cust-014", "Graphic Design Institute", "Unified"),
            ("cust-015", "Litware Inc", "Unified"),
            ("cust-016", "Proseware Inc", "Unified"),
            ("cust-017", "Lucerne Publishing", "Unified"),
            ("cust-018", "Margie Travel", "Unified"),
            ("cust-019", "Consolidated Messenger", "Unified"),
            ("cust-020", "Blue Yonder Airlines", "Unified"),
            ("cust-021", "Southridge Video", "Unified"),
            ("cust-022", "School of Fine Art", "Unified"),
            ("cust-023", "Relecloud", "Unified"),
            ("cust-024", "Munson's Pickles", "Unified"),
            ("cust-025", "Lamna Healthcare", "Unified"),
            # Professional Tier (15)
            ("cust-026", "A Datum Corporation", "Professional"),
            ("cust-027", "Best For You Organics", "Professional"),
            ("cust-028", "City Power & Light", "Professional"),
            ("cust-029", "Humongous Insurance", "Professional"),
            ("cust-030", "VanArsdel Ltd", "Professional"),
            ("cust-031", "Woodgrove Bank", "Professional"),
            ("cust-032", "Adatum Corporation", "Professional"),
            ("cust-033", "Nod Publishers", "Professional"),
            ("cust-034", "Parnell Aerospace", "Professional"),
            ("cust-035", "Treyserv Multi-Sport", "Professional"),
            ("cust-036", "Consolidated Shipping", "Professional"),
            ("cust-037", "Liberty Cabs", "Professional"),
            ("cust-038", "Trey Engineering", "Professional"),
            ("cust-039", "Datum Industries", "Professional"),
            ("cust-040", "Pratum Corp", "Professional"),
        ]
        for c in customers:
            cursor.execute("""
                INSERT INTO customers (id, company, tier) 
                VALUES (?, ?, ?)
            """, c)
        
        customer_ids = [c[0] for c in customers]
        
        # =====================================================================
        # Case titles for realistic variety
        # =====================================================================
        azure_titles = [
            "Azure SQL Database connection timeout issues",
            "AKS cluster autoscaling not responding",
            "Azure Front Door routing misconfiguration",
            "API Management gateway timeout",
            "Azure Cache for Redis evictions",
            "Azure Functions cold start latency",
            "VNet peering connectivity issues",
            "Azure Backup restore failure",
            "VM scale set deployment failures",
            "Storage account SAS token errors",
            "Azure AD B2C custom policy error",
            "Virtual WAN hub routing issues",
            "Azure SignalR connection drops",
            "Load Balancer health probe issues",
            "Container Apps scaling failure",
            "Private Endpoint DNS resolution",
            "Azure Arc onboarding failures",
            "Application Insights sampling issues",
            "Service Bus queue deadlettering",
            "Azure Firewall rule processing errors",
            "Sentinel alert rules not matching",
            "Defender for Cloud false positives",
            "Key Vault access policy conflicts",
            "Logic Apps connector auth failures",
            "Cosmos DB high RU consumption",
            "Event Hub throughput exceeded",
            "Azure Monitor alert not firing",
            "Databricks cluster start failures",
            "Power BI refresh gateway timeout",
            "SQL elastic pool DTU exhausted",
            "Stream Analytics job lag",
            "Data Factory pipeline scheduling issues",
            "Synapse Analytics workspace access",
            "Cognitive Services rate limiting",
            "Azure IoT Hub device provisioning",
            "Azure Files SMB latency issues",
            "Azure Bastion connection timeout",
            "Purview data scanning errors",
            "Azure Migrate assessment errors",
            "Azure Spring Apps deployment stuck",
            "Azure Kubernetes ingress 503 errors",
            "Azure DevOps pipeline optimization",
            "Azure AD conditional access blocking",
        ]
        
        m365_titles = [
            "Teams meeting recording unavailable",
            "Dynamics 365 integration broken",
            "Intune device enrollment failures",
            "Defender for Endpoint onboarding",
            "SharePoint site collection recovery",
            "OneDrive sync client conflicts",
            "Power Automate approval workflow",
            "Teams app permission consent",
            "M365 license assignment failures",
            "Graph API permission issues",
            "Exchange Online mail flow delays",
            "Outlook calendar sync issues",
            "Teams voice quality issues",
            "Power Apps connector errors",
            "Planner task sync failures",
            "Yammer group provisioning",
            "Stream video playback issues",
            "Bookings calendar conflicts",
            "Forms response collection errors",
            "Whiteboard sharing failures",
        ]
        
        # =====================================================================
        # GENERATE 600 CASES (60 per engineer)
        # =====================================================================
        cases_created = 0
        timeline_created = 0
        
        # Engineer performance profiles (affects sentiment and staleness patterns)
        engineer_profiles = {
            "eng-001": {"skill": "excellent", "active_cases": 8},   # Top performer
            "eng-002": {"skill": "good", "active_cases": 10},       # Solid
            "eng-003": {"skill": "average", "active_cases": 12},    # Some issues
            "eng-004": {"skill": "excellent", "active_cases": 7},   # Top performer
            "eng-005": {"skill": "struggling", "active_cases": 15}, # Needs coaching
            "eng-006": {"skill": "good", "active_cases": 9},        # Solid
            "eng-007": {"skill": "struggling", "active_cases": 14}, # Needs coaching
            "eng-008": {"skill": "good", "active_cases": 11},       # Solid
            "eng-009": {"skill": "excellent", "active_cases": 6},   # Top performer
            "eng-010": {"skill": "average", "active_cases": 12},    # Some issues
        }
        
        severities = ["sev_a", "sev_b", "sev_c"]
        severity_weights = [0.15, 0.35, 0.50]  # 15% critical, 35% high, 50% medium
        
        for eng_id in support_engineers:
            profile = engineer_profiles[eng_id]
            active_target = profile["active_cases"]
            skill = profile["skill"]
            
            # Use Azure or M365 titles based on team
            if eng_id in ["eng-008", "eng-009", "eng-010"]:
                titles = m365_titles
            else:
                titles = azure_titles
            
            # Generate 60 cases per engineer (20/month for 3 months)
            active_count = 0
            
            for case_num in range(1, 61):
                case_id = f"case-{eng_id[-3:]}-{case_num:03d}"
                
                # Distribute cases across the quarter
                # Month 1: cases 1-20 (60-90 days ago)
                # Month 2: cases 21-40 (30-60 days ago)
                # Month 3: cases 41-60 (0-30 days ago)
                if case_num <= 20:
                    days_created = random.randint(60, 90)
                elif case_num <= 40:
                    days_created = random.randint(30, 59)
                else:
                    days_created = random.randint(0, 29)
                
                # Determine status: active vs resolved
                # More recent cases are more likely to be active
                if active_count < active_target and case_num > 45:
                    status = "active"
                    active_count += 1
                elif active_count < active_target and case_num > 30 and random.random() < 0.3:
                    status = "active"
                    active_count += 1
                else:
                    status = "resolved"
                
                # Select severity (weighted)
                severity = random.choices(severities, weights=severity_weights)[0]
                
                # Select customer and title
                customer_id = random.choice(customer_ids)
                title = random.choice(titles)
                
                # Determine staleness based on skill and status
                if status == "resolved":
                    # Resolved cases: last comm/note at resolution time
                    # Ensure valid range for randint (at least 1)
                    max_offset = max(1, min(10, days_created))
                    days_comm = max(0, days_created - random.randint(1, max_offset))
                    days_note = days_comm
                else:
                    # Active cases: staleness based on engineer skill
                    if skill == "excellent":
                        days_comm = random.choices([0, 1, 2], weights=[0.5, 0.3, 0.2])[0]
                        days_note = random.choices([0, 1, 2, 3], weights=[0.4, 0.3, 0.2, 0.1])[0]
                    elif skill == "good":
                        days_comm = random.choices([0, 1, 2, 3, 4], weights=[0.3, 0.3, 0.2, 0.1, 0.1])[0]
                        days_note = random.choices([0, 1, 2, 3, 4, 5], weights=[0.2, 0.3, 0.2, 0.15, 0.1, 0.05])[0]
                    elif skill == "average":
                        days_comm = random.choices([0, 1, 2, 3, 4, 5, 6, 7], weights=[0.15, 0.2, 0.2, 0.15, 0.1, 0.1, 0.05, 0.05])[0]
                        days_note = random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8], weights=[0.1, 0.15, 0.2, 0.15, 0.15, 0.1, 0.08, 0.05, 0.02])[0]
                    else:  # struggling
                        days_comm = random.choices([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], weights=[0.05, 0.1, 0.1, 0.15, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05])[0]
                        days_note = random.choices([2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14], weights=[0.05, 0.08, 0.1, 0.12, 0.15, 0.12, 0.12, 0.1, 0.08, 0.05, 0.03])[0]
                
                # Insert case
                cursor.execute(f"""
                    INSERT INTO cases (id, title, status, priority, owner_id, customer_id, created_on, modified_on)
                    VALUES (?, ?, ?, ?, ?, ?, 
                            DATEADD(day, -{days_created}, GETUTCDATE()),
                            DATEADD(day, -{min(days_comm, days_note)}, GETUTCDATE()))
                """, (case_id, title, status, severity, eng_id, customer_id))
                cases_created += 1
                
                # =====================================================================
                # TIMELINE ENTRIES for this case
                # =====================================================================
                # Determine sentiment pattern based on skill and randomness
                if skill == "excellent":
                    sentiment_pattern = random.choices(["happy", "neutral", "declining"], weights=[0.6, 0.3, 0.1])[0]
                elif skill == "good":
                    sentiment_pattern = random.choices(["happy", "neutral", "declining", "frustrated"], weights=[0.4, 0.35, 0.15, 0.1])[0]
                elif skill == "average":
                    sentiment_pattern = random.choices(["happy", "neutral", "declining", "frustrated"], weights=[0.25, 0.35, 0.25, 0.15])[0]
                else:  # struggling
                    sentiment_pattern = random.choices(["happy", "neutral", "declining", "frustrated"], weights=[0.15, 0.25, 0.3, 0.3])[0]
                
                # Generate 3-6 timeline entries per case
                num_entries = random.randint(3, 6)
                
                # Sentiment values based on pattern
                if sentiment_pattern == "happy":
                    sentiments = [0.6, 0.7, 0.75, 0.8, 0.85, 0.9]
                elif sentiment_pattern == "frustrated":
                    sentiments = [0.4, 0.3, 0.25, 0.2, 0.15, 0.1]
                elif sentiment_pattern == "declining":
                    sentiments = [0.6, 0.5, 0.4, 0.35, 0.3, 0.25]
                else:  # neutral
                    sentiments = [0.5, 0.55, 0.5, 0.52, 0.48, 0.55]
                
                # Content templates
                happy_contents = [
                    "Thank you for the quick response!",
                    "This solution worked perfectly.",
                    "Great support, really appreciated.",
                    "Exactly what we needed, thanks!",
                    "Excellent documentation provided.",
                ]
                frustrated_contents = [
                    "Still waiting for a response...",
                    "This has been ongoing for too long.",
                    "We need this resolved urgently!",
                    "Escalating to management.",
                    "Unacceptable service level.",
                ]
                neutral_contents = [
                    "Following up on our request.",
                    "Please see attached logs.",
                    "Can you provide an update?",
                    "Acknowledged, will review.",
                    "Working on the analysis.",
                ]
                note_contents = [
                    "Reviewed customer request.",
                    "Sent documentation and guidance.",
                    "Escalated to product team.",
                    "Awaiting customer response.",
                    "Implemented suggested fix.",
                    "Scheduled follow-up call.",
                ]
                
                # Space entries across case lifetime
                entry_days = sorted([random.randint(0, days_created) for _ in range(num_entries)], reverse=True)
                
                # Ensure last comm and last note align with staleness targets
                if status == "active":
                    entry_days[-1] = days_note  # Last entry at note staleness
                    if len(entry_days) > 1:
                        entry_days[-2] = days_comm  # Second to last at comm staleness
                
                for i in range(num_entries):
                    entry_id = f"tl-{case_id[-7:]}-{i+1:02d}"
                    entry_days_ago = entry_days[i]
                    
                    # Alternate between emails and notes
                    if i == num_entries - 1:
                        entry_type = "note"
                        content = random.choice(note_contents)
                        direction = None
                    elif i % 2 == 0:
                        entry_type = "email_received"
                        if sentiment_pattern == "happy":
                            content = random.choice(happy_contents)
                        elif sentiment_pattern == "frustrated":
                            content = random.choice(frustrated_contents)
                        else:
                            content = random.choice(neutral_contents)
                        direction = "inbound"
                    else:
                        entry_type = "email_sent"
                        content = random.choice(note_contents)
                        direction = "outbound"
                    
                    sentiment = sentiments[min(i, len(sentiments)-1)]
                    
                    cursor.execute(f"""
                        INSERT INTO timeline_entries (id, case_id, entry_type, content, created_by, direction, created_on)
                        VALUES (?, ?, ?, ?, 'system', ?, DATEADD(day, -{entry_days_ago}, GETUTCDATE()))
                    """, (entry_id, case_id, entry_type, content, direction))
                    timeline_created += 1
            
            # Commit after each engineer to avoid transaction size issues
            conn.commit()
        
        # =====================================================================
        # SAMPLE FEEDBACK
        # =====================================================================
        feedback_data = [
            ("fb-001", "positive", "The coaching insights are incredibly helpful for my 1:1s!", "coaching", "manager", "mgr-001", 5),
            ("fb-002", "positive", "Love the real-time sentiment analysis. Game changer!", "general", "engineer", "eng-001", 4),
            ("fb-003", "negative", "Trend chart could show more granular data", "ui", "engineer-detail", "mgr-002", 3),
            ("fb-004", "positive", "Finally a tool that helps prevent CSAT issues!", "general", "landing", None, 2),
            ("fb-005", "positive", "Personalized coaching tips are spot-on", "coaching", "engineer-detail", "mgr-001", 1),
            ("fb-006", "positive", "The date range filter is exactly what we needed", "feature", "manager", "mgr-003", 1),
            ("fb-007", "negative", "Would like to see more historical trend data", "feature", "engineer-detail", "mgr-002", 2),
            ("fb-008", "positive", "Great visibility into team performance", "general", "manager", "mgr-001", 0),
        ]
        
        for fb in feedback_data:
            cursor.execute(f"""
                INSERT INTO feedback (id, rating, comment, category, page, engineer_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, DATEADD(day, -{fb[6]}, GETUTCDATE()))
            """, (fb[0], fb[1], fb[2], fb[3], fb[4], fb[5]))
        
        conn.commit()
        
        # =====================================================================
        # Get counts and stats for response
        # =====================================================================
        counts = {}
        for table in ['engineers', 'customers', 'cases', 'timeline_entries', 'feedback']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            except:
                counts[table] = 0
        
        # Get active vs resolved breakdown
        cursor.execute("SELECT status, COUNT(*) FROM cases GROUP BY status")
        status_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get cases per engineer
        cursor.execute("SELECT owner_id, COUNT(*) FROM cases GROUP BY owner_id ORDER BY owner_id")
        cases_per_engineer = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "status": "success",
            "message": "Database seeded with realistic quarter workload",
            "summary": {
                "engineers": 10,
                "cases_per_engineer": 60,
                "total_cases": counts.get('cases', 0),
                "total_timeline_entries": counts.get('timeline_entries', 0),
            },
            "counts": counts,
            "status_breakdown": status_breakdown,
            "cases_per_engineer": cases_per_engineer,
            "engineer_profiles": {
                "excellent": ["eng-001", "eng-004", "eng-009"],
                "good": ["eng-002", "eng-006", "eng-008"],
                "average": ["eng-003", "eng-010"],
                "needs_coaching": ["eng-005", "eng-007"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to seed database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Static Files & UI (if exists)
# =============================================================================

# Serve static files if they exist
static_path = Path(__file__).parent / "static"
if static_path.exists():
    # Serve index.html at /ui (must be before mount to take precedence)
    @app.get("/ui", response_class=HTMLResponse)
    async def serve_ui():
        """Serve the frontend UI."""
        index_file = static_path / "index.html"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read(), status_code=200)
        return HTMLResponse(content="<h1>UI not found</h1>", status_code=404)
    
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# =============================================================================
# Run Application
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
