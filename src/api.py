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
from models import Case, Engineer, CaseStatus, CasePriority, SentimentResult
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


class ChatResponse(BaseModel):
    """Response for chat endpoint."""
    response: str
    case_context: Optional[dict] = None
    suggestions: List[str] = []


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
    
    # Initialize DfM client - try Azure SQL adapter first, then mock
    try:
        from clients.azure_sql_adapter import get_azure_sql_adapter
        app_state.dfm_client = await get_azure_sql_adapter()
        logger.info("DfM client initialized (Azure SQL)")
    except Exception as e:
        logger.warning(f"Azure SQL adapter failed: {e}")
        logger.info("Falling back to mock DfM client")
        try:
            from clients.dfm_client import get_dfm_client
            app_state.dfm_client = await get_dfm_client(app_state.config)
            logger.info("DfM client initialized (Mock)")
        except Exception as e2:
            logger.warning(f"Mock DfM client also failed: {e2}")
    
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
    priority: Optional[str] = Query(None, description="Filter by priority")
):
    """
    List cases with optional filters.
    
    - **engineer_id**: Filter cases by assigned engineer
    - **status**: Filter by case status (active, resolved, etc.)
    - **priority**: Filter by priority (high, medium, low)
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
        if priority:
            cases = [c for c in cases if c.priority.value == priority]
        
        return {
            "count": len(cases),
            "cases": [
                {
                    "id": c.id,
                    "title": c.title,
                    "status": c.status.value,
                    "priority": c.priority.value,
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
            "priority": case.priority.value,
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
# Chat Endpoint
# =============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the CSAT Guardian agent.
    
    The agent can:
    - Answer questions about cases
    - Provide recommendations for improving CSAT
    - Offer coaching based on case analysis
    
    Optionally provide case_id for case-specific context.
    """
    try:
        # For POC, implement simple response logic
        # In production, this would use Semantic Kernel with Azure OpenAI
        
        message = request.message.lower()
        case_context = None
        
        # If case_id provided, get case context
        if request.case_id and app_state.dfm_client:
            case = await app_state.dfm_client.get_case(request.case_id)
            if case:
                case_context = {
                    "id": case.id,
                    "title": case.title,
                    "status": case.status.value,
                    "days_since_last_note": case.days_since_last_note
                }
        
        # Simple keyword-based responses for POC
        # Will be replaced with Semantic Kernel agent
        if any(word in message for word in ["risk", "csat", "concern", "worry"]):
            response = "Based on the case analysis, I recommend checking cases that haven't been updated in over 5 days, as they have higher CSAT risk."
            suggestions = ["View at-risk cases", "Run sentiment analysis", "Set up alerts"]
        elif any(word in message for word in ["recommend", "suggest", "advice", "help"]):
            response = "I suggest proactive communication with the customer, providing regular updates even when there's no new information to share."
            suggestions = ["Send status update", "Schedule call", "Review similar cases"]
        elif any(word in message for word in ["coach", "improve", "better", "feedback"]):
            response = "Key areas for improvement: ensure timely responses within SLA, document all customer interactions, and set clear expectations."
            suggestions = ["Review response times", "Update case notes", "Check SLA compliance"]
        else:
            response = "I'm here to help you manage CSAT risk. Ask me about case risks, recommendations, or coaching tips."
            suggestions = ["What cases are at risk?", "How can I improve CSAT?", "Analyze my cases"]
        
        return ChatResponse(
            response=response,
            case_context=case_context,
            suggestions=suggestions
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        
        # Clear existing data
        cursor.execute("DELETE FROM TimelineEntries")
        cursor.execute("DELETE FROM Alerts")
        cursor.execute("DELETE FROM Cases")
        cursor.execute("DELETE FROM Customers")
        cursor.execute("DELETE FROM Engineers")
        conn.commit()
        
        # Insert Engineers
        engineers = [
            ("eng-001", "John Smith", "john.smith@microsoft.com", "john.smith"),
            ("eng-002", "Sarah Johnson", "sarah.johnson@microsoft.com", "sarah.johnson"),
            ("eng-003", "Mike Chen", "mike.chen@microsoft.com", "mike.chen"),
        ]
        for e in engineers:
            cursor.execute("INSERT INTO Engineers (Id, Name, Email, TeamsId) VALUES (?, ?, ?, ?)", e)
        
        # Insert Customers
        customers = [
            ("cust-001", "Contoso Ltd"),
            ("cust-002", "Fabrikam Inc"),
            ("cust-003", "Northwind Traders"),
            ("cust-004", "Adventure Works"),
            ("cust-005", "Woodgrove Bank"),
            ("cust-006", "Tailspin Toys"),
        ]
        for c in customers:
            cursor.execute("INSERT INTO Customers (Id, Company) VALUES (?, ?)", c)
        
        # Insert Cases with historical dates
        cursor.execute("""
            INSERT INTO Cases (Id, Title, Description, Status, Priority, OwnerId, CustomerId, CreatedOn, ModifiedOn) VALUES
            ('case-001', 'Azure VM Performance Optimization', 'Customer reports slow VM performance', 'active', 'medium', 'eng-001', 'cust-001', DATEADD(day, -10, GETUTCDATE()), DATEADD(day, -3, GETUTCDATE()))
        """)
        cursor.execute("""
            INSERT INTO Cases (Id, Title, Description, Status, Priority, OwnerId, CustomerId, CreatedOn, ModifiedOn) VALUES
            ('case-002', 'Storage Account Access Issues', 'Getting 403 errors', 'active', 'high', 'eng-001', 'cust-002', DATEADD(day, -5, GETUTCDATE()), DATEADD(day, -1, GETUTCDATE()))
        """)
        cursor.execute("""
            INSERT INTO Cases (Id, Title, Description, Status, Priority, OwnerId, CustomerId, CreatedOn, ModifiedOn) VALUES
            ('case-003', 'Azure SQL Query Performance', 'Queries taking longer', 'active', 'medium', 'eng-002', 'cust-003', DATEADD(day, -7, GETUTCDATE()), DATEADD(day, -2, GETUTCDATE()))
        """)
        cursor.execute("""
            INSERT INTO Cases (Id, Title, Description, Status, Priority, OwnerId, CustomerId, CreatedOn, ModifiedOn) VALUES
            ('case-004', 'Billing Discrepancy Investigation', 'Customer disputes charges', 'active', 'high', 'eng-001', 'cust-004', DATEADD(day, -14, GETUTCDATE()), DATEADD(day, -10, GETUTCDATE()))
        """)
        cursor.execute("""
            INSERT INTO Cases (Id, Title, Description, Status, Priority, OwnerId, CustomerId, CreatedOn, ModifiedOn) VALUES
            ('case-005', 'App Service Deployment Failures', 'CI/CD pipeline failing', 'active', 'medium', 'eng-002', 'cust-005', DATEADD(day, -8, GETUTCDATE()), DATEADD(day, -6, GETUTCDATE()))
        """)
        cursor.execute("""
            INSERT INTO Cases (Id, Title, Description, Status, Priority, OwnerId, CustomerId, CreatedOn, ModifiedOn) VALUES
            ('case-006', 'Network Connectivity Problems', 'VMs cannot communicate', 'active', 'critical', 'eng-003', 'cust-006', DATEADD(day, -12, GETUTCDATE()), DATEADD(day, -8, GETUTCDATE()))
        """)
        
        # Insert Timeline Entries with historical dates
        timeline = [
            ("tl-001-01", "case-001", "email", "RE: VM Performance", "Thanks for looking into this.", -9, "Customer", 1),
            ("tl-001-02", "case-001", "note", "Initial Analysis", "Reviewed VM metrics. CPU peaks at 95%.", -8, "John Smith", 0),
            ("tl-001-03", "case-001", "email", "RE: VM Performance", "Thank you so much for the quick response!", -3, "Customer", 1),
            ("tl-002-01", "case-002", "email", "URGENT: Storage Access", "This is URGENT! Our production application is DOWN!", -4, "Customer", 1),
            ("tl-002-02", "case-002", "note", "Troubleshooting", "Checking storage account configuration.", -3, "John Smith", 0),
            ("tl-002-03", "case-002", "email", "RE: Storage Access", "We have been waiting 2 days. This is unacceptable!", -1, "Customer", 1),
            ("tl-003-01", "case-003", "email", "Query Performance", "Some queries slower than expected.", -6, "Customer", 1),
            ("tl-003-02", "case-003", "note", "Analysis", "Requested query execution plans.", -5, "Sarah Johnson", 0),
            ("tl-003-03", "case-003", "email", "RE: Query Performance", "Here are the execution plans.", -2, "Customer", 1),
            ("tl-004-01", "case-004", "email", "Billing Question", "We noticed unexpected charges.", -13, "Customer", 1),
            ("tl-004-02", "case-004", "note", "Reviewing charges", "Looking into billing details.", -12, "John Smith", 0),
            ("tl-004-03", "case-004", "email", "RE: Billing", "It has been a week! This is frustrating!", -10, "Customer", 1),
            ("tl-005-01", "case-005", "email", "Deployment Issues", "Deployments failing randomly.", -7, "Customer", 1),
            ("tl-005-02", "case-005", "note", "Initial review", "Requested deployment logs.", -6, "Sarah Johnson", 0),
            ("tl-006-01", "case-006", "email", "Network Issue", "VMs cannot communicate across subnets.", -11, "Customer", 1),
            ("tl-006-02", "case-006", "note", "Checking NSGs", "NSG rules appear correct.", -10, "Mike Chen", 0),
            ("tl-006-03", "case-006", "email", "RE: Network Issue", "Stuck for over a week. Please escalate!", -8, "Customer", 1),
        ]
        for t in timeline:
            cursor.execute(f"""
                INSERT INTO TimelineEntries (Id, CaseId, EntryType, Subject, Content, CreatedOn, CreatedBy, IsCustomerCommunication) 
                VALUES (?, ?, ?, ?, ?, DATEADD(day, {t[5]}, GETUTCDATE()), ?, ?)
            """, (t[0], t[1], t[2], t[3], t[4], t[6], t[7]))
        
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
