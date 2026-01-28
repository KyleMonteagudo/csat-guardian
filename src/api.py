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
    
    # Initialize DfM client - try Azure SQL adapter first, then in-memory mock
    try:
        from clients.azure_sql_adapter import get_azure_sql_adapter
        app_state.dfm_client = await get_azure_sql_adapter()
        logger.info("DfM client initialized (Azure SQL)")
    except Exception as e:
        logger.warning(f"Azure SQL adapter failed: {e}")
        logger.info("Falling back to in-memory mock client with rich sample data")
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
    severity: Optional[str] = Query(None, description="Filter by severity (sev_a, sev_b, sev_c, sev_d)")
):
    """
    List cases with optional filters.
    
    - **engineer_id**: Filter cases by assigned engineer
    - **status**: Filter by case status (active, resolved, etc.)
    - **severity**: Filter by severity (sev_a, sev_b, sev_c, sev_d)
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
        
        return {
            "count": len(cases),
            "cases": [
                {
                    "id": c.id,
                    "title": c.title,
                    "status": c.status.value,
                    "severity": c.severity.value,
                    "customer_company": c.customer.company if c.customer else None,
                    "owner_name": c.owner.name if c.owner else None,
                    "created_on": c.created_on.isoformat() if c.created_on else None,
                    "days_since_last_note": c.days_since_last_note,
                    "timeline_count": len(c.timeline) if c.timeline else 0
                }
                for c in cases
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    """Get detailed case information including timeline."""
    if not app_state.dfm_client:
        raise HTTPException(status_code=503, detail="DfM client not available")
    
    try:
        case = await app_state.dfm_client.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
        return {
            "id": case.id,
            "title": case.title,
            "description": case.description,
            "status": case.status.value,
            "severity": case.severity.value,
            "customer": {
                "id": case.customer.id,
                "company": case.customer.company
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
        
        return AnalyzeResponse(
            case_id=case_id,
            sentiment={
                "score": sentiment.score,
                "label": sentiment.label.value,
                "confidence": sentiment.confidence,
                "trend": result.sentiment_trend,
                "key_phrases": sentiment.key_phrases or []
            },
            recommendations=result.recommendations or [],
            analyzed_at=datetime.utcnow().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        
        # Build the message with case context if provided
        message = request.message
        if request.case_id:
            message = f"[Context: Discussing case {request.case_id}] {message}"
        
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
# Admin Endpoint - Seed Database
# =============================================================================

@app.post("/api/admin/seed")
async def seed_database(secret: str = Query(..., description="Admin secret key")):
    """
    Seed the database with test data.
    Requires secret key for basic protection.
    Uses actual database schema (lowercase columns).
    """
    # Simple secret check - in production use proper auth
    expected_secret = os.environ.get("ADMIN_SECRET", "csat-seed-2026")
    if secret != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    if not app_state.dfm_client or not hasattr(app_state.dfm_client, 'db'):
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        conn = app_state.dfm_client.db.connect()
        cursor = conn.cursor()
        
        # Clear existing data (order matters for foreign keys)
        cursor.execute("DELETE FROM TimelineEntries")
        cursor.execute("DELETE FROM Cases")
        cursor.execute("DELETE FROM Customers")
        cursor.execute("DELETE FROM Engineers")
        conn.commit()
        
        # Insert Engineers (actual schema: id, name, email, team)
        engineers = [
            ("eng-001", "John Smith", "john.smith@microsoft.com", "Support"),
            ("eng-002", "Sarah Johnson", "sarah.johnson@microsoft.com", "Support"),
            ("eng-003", "Mike Chen", "mike.chen@microsoft.com", "Support"),
        ]
        for e in engineers:
            cursor.execute("INSERT INTO Engineers (id, name, email, team) VALUES (?, ?, ?, ?)", e)
        
        # Insert Customers (actual schema: id, name, company, tier)
        customers = [
            ("cust-001", "Contoso Contact", "Contoso Ltd", "enterprise"),
            ("cust-002", "Fabrikam Contact", "Fabrikam Inc", "enterprise"),
            ("cust-003", "Northwind Contact", "Northwind Traders", "standard"),
            ("cust-004", "Adventure Contact", "Adventure Works", "premium"),
            ("cust-005", "Woodgrove Contact", "Woodgrove Bank", "enterprise"),
            ("cust-006", "Tailspin Contact", "Tailspin Toys", "standard"),
        ]
        for c in customers:
            cursor.execute("INSERT INTO Customers (id, name, company, tier) VALUES (?, ?, ?, ?)", c)
        
        # Insert Cases (actual schema: id, title, customer_id, engineer_id, status, severity, created_at)
        # Using severity as int: 1=low, 2=medium, 3=high, 4=critical
        cases = [
            ("case-001", "Azure VM Performance Optimization", "cust-001", "eng-001", 1, 2, -10),
            ("case-002", "Storage Account Access Issues", "cust-002", "eng-001", 1, 3, -5),
            ("case-003", "Azure SQL Query Performance", "cust-003", "eng-002", 1, 2, -7),
            ("case-004", "Billing Discrepancy Investigation", "cust-004", "eng-001", 1, 3, -14),
            ("case-005", "App Service Deployment Failures", "cust-005", "eng-002", 1, 2, -8),
            ("case-006", "Network Connectivity Problems", "cust-006", "eng-003", 1, 4, -12),
        ]
        for c in cases:
            cursor.execute(f"""
                INSERT INTO Cases (id, title, customer_id, engineer_id, status, severity, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, DATEADD(day, {c[6]}, GETUTCDATE()))
            """, (c[0], c[1], c[2], c[3], c[4], c[5]))
        
        # Insert Timeline Entries (actual schema: id, case_id, entry_type, content, sentiment_score, created_at)
        timeline = [
            ("tl-001-01", "case-001", "email", "Thanks for looking into this. We are seeing slow response times.", 0.6, -9),
            ("tl-001-02", "case-001", "note", "Reviewed VM metrics. CPU peaks at 95%. Recommend scaling.", 0.5, -8),
            ("tl-001-03", "case-001", "email", "Thank you so much for the quick response! Very helpful.", 0.9, -3),
            ("tl-002-01", "case-002", "email", "This is URGENT! Our production application is DOWN!", -0.8, -4),
            ("tl-002-02", "case-002", "note", "Checking storage account configuration and access policies.", 0.5, -3),
            ("tl-002-03", "case-002", "email", "We have been waiting 2 days. This is completely unacceptable!", -0.9, -1),
            ("tl-003-01", "case-003", "email", "Some queries are slower than expected. Can you help?", 0.3, -6),
            ("tl-003-02", "case-003", "note", "Requested query execution plans for analysis.", 0.5, -5),
            ("tl-003-03", "case-003", "email", "Here are the execution plans as requested.", 0.4, -2),
            ("tl-004-01", "case-004", "email", "We noticed some unexpected charges. Can you clarify?", 0.2, -13),
            ("tl-004-02", "case-004", "note", "Looking into billing details for the customer account.", 0.5, -12),
            ("tl-004-03", "case-004", "email", "It has been a week! This is getting very frustrating!", -0.7, -10),
            ("tl-005-01", "case-005", "email", "Deployments are failing randomly. Sometimes work, sometimes dont.", 0.1, -7),
            ("tl-005-02", "case-005", "note", "Requested deployment logs and pipeline configuration.", 0.5, -6),
            ("tl-006-01", "case-006", "email", "VMs cannot communicate across subnets. Blocking our project!", -0.3, -11),
            ("tl-006-02", "case-006", "note", "NSG rules appear correct. Need deeper investigation.", 0.4, -10),
            ("tl-006-03", "case-006", "email", "Stuck for over a week now. Very worried. Please escalate!", -0.6, -8),
        ]
        for t in timeline:
            cursor.execute(f"""
                INSERT INTO TimelineEntries (id, case_id, entry_type, content, sentiment_score, created_at) 
                VALUES (?, ?, ?, ?, ?, DATEADD(day, {t[5]}, GETUTCDATE()))
            """, (t[0], t[1], t[2], t[3], t[4]))
        
        conn.commit()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM Engineers")
        eng_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM Customers")
        cust_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM Cases")
        case_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM TimelineEntries")
        timeline_count = cursor.fetchone()[0]
        
        return {
            "status": "success",
            "message": "Database seeded successfully",
            "counts": {
                "engineers": eng_count,
                "customers": cust_count,
                "cases": case_count,
                "timeline_entries": timeline_count
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
