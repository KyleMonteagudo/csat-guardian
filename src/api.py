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
# Admin Endpoint - Seed Database (Comprehensive Quarter Data)
# =============================================================================

@app.post("/api/admin/seed")
async def seed_database(secret: str = Query(..., description="Admin secret key")):
    """
    Seed the database with comprehensive test data for a full quarter.
    
    Creates:
    - 13 engineers (10 support + 3 managers)
    - 25 customers across tiers
    - 60 cases spanning 90 days with varied staleness patterns
    - 100+ timeline entries with realistic sentiment patterns
    - Feedback table and sample feedback
    
    IMPORTANT: Staleness (days_since_last_comm, days_since_last_note) is based on
    fixed dates relative to current time to ensure varied compliance patterns.
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
        # ENGINEERS (13 total: 10 support + 3 managers)
        # =====================================================================
        engineers = [
            # Azure Platform Team
            ("eng-001", "Sarah Chen", "sarchen@microsoft.com", "Azure Platform", "mgr-001"),
            ("eng-002", "Marcus Johnson", "marjohn@microsoft.com", "Azure Platform", "mgr-001"),
            ("eng-003", "Emily Rodriguez", "emrod@microsoft.com", "Azure Platform", "mgr-001"),
            ("eng-004", "James Kim", "jamkim@microsoft.com", "Azure Platform", "mgr-001"),
            # Azure Data Team
            ("eng-005", "Priya Patel", "prpatel@microsoft.com", "Azure Data", "mgr-002"),
            ("eng-006", "David Wang", "dawang@microsoft.com", "Azure Data", "mgr-002"),
            ("eng-007", "Lisa Thompson", "lithomp@microsoft.com", "Azure Data", "mgr-002"),
            # M365 Support Team
            ("eng-008", "Alex Martinez", "almart@microsoft.com", "M365 Support", "mgr-003"),
            ("eng-009", "Jennifer Lee", "jenlee@microsoft.com", "M365 Support", "mgr-003"),
            ("eng-010", "Robert Brown", "robbro@microsoft.com", "M365 Support", "mgr-003"),
            # Managers
            ("mgr-001", "Michael Scott", "micscott@microsoft.com", "Management", None),
            ("mgr-002", "Angela Martin", "angmart@microsoft.com", "Management", None),
            ("mgr-003", "Jim Halpert", "jimhal@microsoft.com", "Management", None),
        ]
        for e in engineers:
            cursor.execute("""
                INSERT INTO engineers (id, name, email, team, manager_id) 
                VALUES (?, ?, ?, ?, ?)
            """, e)
        
        # =====================================================================
        # CUSTOMERS (25 companies across tiers)
        # =====================================================================
        customers = [
            # Premier Tier
            ("cust-001", "Contoso Financial Services", "Premier"),
            ("cust-002", "Fabrikam Industries", "Premier"),
            ("cust-003", "Northwind Traders", "Premier"),
            ("cust-004", "Adventure Works Cycles", "Premier"),
            ("cust-005", "Wide World Importers", "Premier"),
            ("cust-006", "Trey Research", "Premier"),
            ("cust-007", "The Phone Company", "Premier"),
            ("cust-008", "Coho Vineyard", "Premier"),
            # Unified Tier
            ("cust-009", "Tailspin Toys", "Unified"),
            ("cust-010", "Wingtip Toys", "Unified"),
            ("cust-011", "Fourth Coffee", "Unified"),
            ("cust-012", "Graphic Design Institute", "Unified"),
            ("cust-013", "Litware Inc", "Unified"),
            ("cust-014", "Proseware Inc", "Unified"),
            ("cust-015", "Lucerne Publishing", "Unified"),
            ("cust-016", "Margie Travel", "Unified"),
            ("cust-017", "Consolidated Messenger", "Unified"),
            ("cust-018", "Blue Yonder Airlines", "Unified"),
            # Professional Tier
            ("cust-019", "A Datum Corporation", "Professional"),
            ("cust-020", "Bellows College", "Professional"),
            ("cust-021", "Best For You Organics", "Professional"),
            ("cust-022", "City Power & Light", "Professional"),
            ("cust-023", "Humongous Insurance", "Professional"),
            ("cust-024", "VanArsdel Ltd", "Professional"),
            ("cust-025", "Woodgrove Bank", "Professional"),
        ]
        for c in customers:
            cursor.execute("""
                INSERT INTO customers (id, company, tier) 
                VALUES (?, ?, ?)
            """, c)
        
        # =====================================================================
        # CASES (60 cases with varied staleness patterns)
        # Format: (id, title, status, priority, owner_id, customer_id, 
        #          days_since_created, days_since_last_comm, days_since_last_note)
        # 
        # STALENESS PATTERNS:
        # - Fresh (0-1 days): Good communication
        # - Approaching (3-5 days): Needs attention soon
        # - Breach (7+ days): SLA violation
        # =====================================================================
        cases_data = [
            # ==== Sarah Chen (eng-001) - Mix of patterns ====
            # Fresh cases
            ("case-001", "Azure SQL Database connection timeout issues", "active", "sev_b", "eng-001", "cust-001", 15, 0, 0),
            ("case-002", "AKS cluster autoscaling not responding", "active", "sev_a", "eng-001", "cust-006", 8, 1, 0),
            ("case-003", "Azure Front Door routing misconfiguration", "active", "sev_b", "eng-001", "cust-012", 22, 0, 1),
            # Approaching SLA
            ("case-004", "API Management gateway timeout - CRITICAL", "active", "sev_a", "eng-001", "cust-018", 13, 4, 3),
            ("case-005", "Azure Cache for Redis evictions", "active", "sev_b", "eng-001", "cust-001", 5, 3, 4),
            # In breach - stale notes
            ("case-006", "Azure DevOps pipeline optimization inquiry", "active", "sev_c", "eng-001", "cust-003", 45, 2, 12),
            ("case-007", "Azure Functions cold start latency", "active", "sev_c", "eng-001", "cust-019", 30, 1, 8),
            
            # ==== Marcus Johnson (eng-002) - Generally good ====
            ("case-008", "Private Endpoint DNS resolution issues", "active", "sev_b", "eng-002", "cust-021", 6, 0, 0),
            ("case-009", "Azure Arc onboarding failures", "active", "sev_c", "eng-002", "cust-002", 12, 1, 1),
            ("case-010", "Application Insights sampling issues", "active", "sev_c", "eng-002", "cust-006", 4, 0, 2),
            ("case-011", "Static Web Apps deployment failures", "resolved", "sev_c", "eng-002", "cust-011", 20, 5, 5),
            # One breach case
            ("case-012", "Service Bus queue deadlettering", "active", "sev_b", "eng-002", "cust-019", 35, 8, 9),
            
            # ==== Emily Rodriguez (eng-003) - Some issues ====
            ("case-013", "Azure Firewall rule processing errors", "active", "sev_a", "eng-003", "cust-022", 4, 0, 0),
            ("case-014", "Sentinel alert rules not matching", "active", "sev_b", "eng-003", "cust-013", 14, 2, 2),
            # Stale communications
            ("case-015", "Defender for Cloud false positives", "active", "sev_c", "eng-003", "cust-005", 28, 6, 4),
            ("case-016", "Key Vault access policy conflicts", "active", "sev_c", "eng-003", "cust-020", 40, 5, 7),
            # Major breach
            ("case-017", "Logic Apps connector auth failures", "active", "sev_b", "eng-003", "cust-011", 55, 10, 14),
            
            # ==== James Kim (eng-004) - Top performer ====
            ("case-018", "Azure AD B2C custom policy error", "active", "sev_b", "eng-004", "cust-015", 12, 0, 0),
            ("case-019", "Virtual WAN hub routing issues", "active", "sev_a", "eng-004", "cust-002", 3, 0, 0),
            ("case-020", "Azure SignalR connection drops", "active", "sev_b", "eng-004", "cust-024", 7, 1, 1),
            ("case-021", "Load Balancer health probe issues", "active", "sev_a", "eng-004", "cust-016", 9, 0, 1),
            ("case-022", "Azure AD conditional access blocking", "resolved", "sev_a", "eng-004", "cust-006", 25, 2, 2),
            ("case-023", "Container Apps scaling failure", "active", "sev_b", "eng-004", "cust-007", 18, 1, 0),
            
            # ==== Priya Patel (eng-005) - Needs coaching ====
            ("case-024", "Databricks cluster start failures", "active", "sev_b", "eng-005", "cust-019", 8, 3, 5),
            ("case-025", "Power BI refresh gateway timeout", "active", "sev_b", "eng-005", "cust-005", 15, 4, 6),
            ("case-026", "Azure SQL elastic pool DTU exhausted", "active", "sev_a", "eng-005", "cust-005", 2, 0, 3),
            ("case-027", "Stream Analytics job lag exceeding 5min", "active", "sev_b", "eng-005", "cust-024", 32, 6, 8),
            # Breach cases
            ("case-028", "Data Factory pipeline scheduling issues", "active", "sev_c", "eng-005", "cust-016", 50, 9, 11),
            ("case-029", "Synapse Analytics workspace access", "active", "sev_b", "eng-005", "cust-012", 38, 7, 10),
            
            # ==== David Wang (eng-006) - Average ====
            ("case-030", "Cognitive Services rate limiting", "active", "sev_b", "eng-006", "cust-001", 28, 3, 3),
            ("case-031", "Azure IoT Hub device provisioning", "active", "sev_c", "eng-006", "cust-010", 15, 4, 4),
            ("case-032", "Azure Files SMB latency exceeding 100ms", "active", "sev_b", "eng-006", "cust-020", 7, 1, 2),
            ("case-033", "Azure Bastion connection timeout", "active", "sev_c", "eng-006", "cust-009", 5, 0, 0),
            ("case-034", "Event Hub throughput exceeded", "resolved", "sev_b", "eng-006", "cust-017", 45, 2, 2),
            ("case-035", "Cosmos DB high RU consumption", "active", "sev_b", "eng-006", "cust-007", 20, 5, 6),
            
            # ==== Lisa Thompson (eng-007) - Struggling ====
            ("case-036", "SQL Managed Instance performance degraded", "active", "sev_b", "eng-007", "cust-004", 24, 5, 8),
            ("case-037", "Power BI embedded capacity issues", "active", "sev_b", "eng-007", "cust-025", 10, 4, 5),
            ("case-038", "Azure Monitor alert not firing", "active", "sev_a", "eng-007", "cust-021", 18, 6, 9),
            # Major breaches
            ("case-039", "Purview data scanning errors", "active", "sev_c", "eng-007", "cust-008", 35, 11, 15),
            ("case-040", "Azure Migrate assessment errors", "active", "sev_c", "eng-007", "cust-003", 42, 8, 12),
            
            # ==== Alex Martinez (eng-008) - M365 team ====
            ("case-041", "Teams meeting recording unavailable", "active", "sev_c", "eng-008", "cust-004", 10, 1, 1),
            ("case-042", "Dynamics 365 integration broken", "active", "sev_b", "eng-008", "cust-014", 14, 3, 4),
            ("case-043", "Intune device enrollment failures", "active", "sev_b", "eng-008", "cust-013", 20, 2, 3),
            ("case-044", "Defender for Endpoint onboarding", "active", "sev_b", "eng-008", "cust-008", 6, 0, 0),
            ("case-045", "Azure Migrate assessment stuck", "active", "sev_c", "eng-008", "cust-003", 30, 6, 8),
            
            # ==== Jennifer Lee (eng-009) - Excellent ====
            ("case-046", "SharePoint site collection recovery", "resolved", "sev_c", "eng-009", "cust-008", 18, 1, 1),
            ("case-047", "OneDrive sync client conflicts", "active", "sev_c", "eng-009", "cust-018", 12, 0, 0),
            ("case-048", "Power Automate approval workflow", "active", "sev_c", "eng-009", "cust-003", 8, 1, 2),
            ("case-049", "Teams app permission consent", "active", "sev_c", "eng-009", "cust-017", 6, 0, 0),
            ("case-050", "M365 license assignment failures", "active", "sev_c", "eng-009", "cust-004", 4, 0, 1),
            
            # ==== Robert Brown (eng-010) - Mixed ====
            ("case-051", "Graph API permission issues", "active", "sev_b", "eng-010", "cust-009", 16, 1, 2),
            ("case-052", "Exchange Online mail flow delays", "active", "sev_b", "eng-010", "cust-009", 22, 4, 5),
            ("case-053", "Outlook calendar sync to mobile", "active", "sev_c", "eng-010", "cust-023", 5, 0, 0),
            # Breach
            ("case-054", "Teams voice quality issues", "active", "sev_b", "eng-010", "cust-025", 30, 7, 9),
            
            # ==== Additional cases for variety ====
            ("case-055", "Azure Spring Apps deployment stuck", "active", "sev_b", "eng-003", "cust-007", 3, 0, 0),
            ("case-056", "Azure Kubernetes ingress 503 errors", "active", "sev_a", "eng-001", "cust-018", 6, 2, 1),
            ("case-057", "VNet peering connectivity issues", "resolved", "sev_b", "eng-002", "cust-022", 35, 3, 3),
            ("case-058", "Azure Backup restore failure", "active", "sev_a", "eng-004", "cust-023", 8, 0, 0),
            ("case-059", "VM scale set deployment failures", "active", "sev_b", "eng-001", "cust-002", 12, 2, 3),
            ("case-060", "Storage account SAS token errors", "active", "sev_c", "eng-002", "cust-003", 25, 1, 2),
        ]
        
        for case in cases_data:
            case_id, title, status, priority, owner_id, customer_id, days_created, days_comm, days_note = case
            cursor.execute(f"""
                INSERT INTO cases (id, title, status, priority, owner_id, customer_id, created_on, modified_on)
                VALUES (?, ?, ?, ?, ?, ?, 
                        DATEADD(day, -{days_created}, GETUTCDATE()),
                        DATEADD(day, -{min(days_comm, days_note)}, GETUTCDATE()))
            """, (case_id, title, status, priority, owner_id, customer_id))
        
        conn.commit()
        
        # =====================================================================
        # TIMELINE ENTRIES with fixed staleness
        # The last entry for each case determines "days since last" metrics
        # We create entries going back in time, with the LAST one at the 
        # specified staleness level
        # =====================================================================
        
        def add_timeline(case_id, days_comm, days_note, sentiment_pattern, customer_id):
            """Add timeline entries for a case with specified staleness."""
            entries = []
            entry_num = 1
            
            # Determine sentiment based on pattern
            if sentiment_pattern == "happy":
                sentiments = [0.7, 0.75, 0.8, 0.85]
                contents = [
                    ("email_received", "Hi, we have a question about our Azure configuration.", 0.6),
                    ("email_sent", "Thank you for reaching out! I'd be happy to help.", 0.7),
                    ("email_received", "That solution worked perfectly! Thank you so much!", 0.9),
                    ("note", "Customer confirmed resolution. Great feedback received.", 0.8),
                ]
            elif sentiment_pattern == "frustrated":
                sentiments = [0.5, 0.3, 0.2, 0.1]
                contents = [
                    ("email_received", "We're experiencing critical issues with our production environment.", 0.4),
                    ("email_sent", "I understand the urgency. Let me investigate immediately.", 0.6),
                    ("email_received", "It's been days with no resolution! This is unacceptable.", 0.2),
                    ("note", "Customer escalated. Need to prioritize this case.", 0.4),
                ]
            elif sentiment_pattern == "declining":
                sentiments = [0.6, 0.5, 0.35, 0.25]
                contents = [
                    ("email_received", "We need help troubleshooting intermittent issues.", 0.5),
                    ("email_sent", "I'll look into this. Can you provide more details?", 0.6),
                    ("email_received", "Still waiting for a proper solution. Getting frustrated.", 0.3),
                    ("note", "Customer sentiment declining. Need faster resolution.", 0.4),
                ]
            else:  # neutral
                sentiments = [0.5, 0.55, 0.5, 0.55]
                contents = [
                    ("email_received", "We have a question about best practices.", 0.5),
                    ("email_sent", "Here's some documentation that should help.", 0.6),
                    ("email_received", "Thanks, we'll review and get back to you.", 0.5),
                    ("note", "Sent documentation. Awaiting customer feedback.", 0.5),
                ]
            
            # Add entries working backwards from staleness dates
            base_days = max(days_comm, days_note) + 5  # Start earlier than staleness
            
            for i, (entry_type, content, sentiment) in enumerate(contents):
                entry_id = f"tl-{case_id[-3:]}-{entry_num:02d}"
                
                # Calculate days ago for this entry
                if entry_type in ["email_sent", "email_received"]:
                    if i == len(contents) - 2:  # Second to last is last comm
                        days_ago = days_comm
                    else:
                        days_ago = base_days - i
                else:  # note
                    if i == len(contents) - 1:  # Last is the most recent note
                        days_ago = days_note
                    else:
                        days_ago = base_days - i
                
                direction = "inbound" if entry_type == "email_received" else ("outbound" if entry_type == "email_sent" else None)
                
                entries.append((entry_id, case_id, entry_type, content, sentiment, days_ago, direction))
                entry_num += 1
            
            return entries
        
        # Generate timeline for each case based on their staleness pattern
        all_timeline = []
        
        # Assign sentiment patterns based on case characteristics
        case_patterns = {
            # Happy customers (fresh cases, resolved, good sentiment)
            "case-001": "happy", "case-003": "happy", "case-008": "happy", 
            "case-018": "happy", "case-019": "happy", "case-020": "happy",
            "case-021": "happy", "case-046": "happy", "case-047": "happy",
            "case-048": "happy", "case-049": "happy", "case-050": "happy",
            "case-053": "happy", "case-058": "happy",
            
            # Frustrated customers (long cases, breaches, critical)
            "case-004": "frustrated", "case-012": "frustrated", "case-017": "frustrated",
            "case-028": "frustrated", "case-029": "frustrated", "case-038": "frustrated",
            "case-039": "frustrated", "case-040": "frustrated", "case-054": "frustrated",
            "case-056": "frustrated",
            
            # Declining sentiment
            "case-005": "declining", "case-006": "declining", "case-015": "declining",
            "case-024": "declining", "case-025": "declining", "case-027": "declining",
            "case-036": "declining", "case-037": "declining", "case-052": "declining",
        }
        
        for case in cases_data:
            case_id = case[0]
            customer_id = case[5]
            days_comm = case[7]
            days_note = case[8]
            pattern = case_patterns.get(case_id, "neutral")
            
            entries = add_timeline(case_id, days_comm, days_note, pattern, customer_id)
            all_timeline.extend(entries)
        
        # Insert all timeline entries
        for entry in all_timeline:
            entry_id, case_id, entry_type, content, sentiment, days_ago, direction = entry
            cursor.execute(f"""
                INSERT INTO timeline_entries (id, case_id, entry_type, content, created_by, direction, created_on)
                VALUES (?, ?, ?, ?, 'system', ?, DATEADD(day, -{days_ago}, GETUTCDATE()))
            """, (entry_id, case_id, entry_type, content, direction))
        
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
        ]
        
        for fb in feedback_data:
            cursor.execute(f"""
                INSERT INTO feedback (id, rating, comment, category, page, engineer_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, DATEADD(day, -{fb[6]}, GETUTCDATE()))
            """, (fb[0], fb[1], fb[2], fb[3], fb[4], fb[5]))
        
        conn.commit()
        
        # =====================================================================
        # Get counts for response
        # =====================================================================
        counts = {}
        for table in ['engineers', 'customers', 'cases', 'timeline_entries', 'feedback']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            except:
                counts[table] = 0
        
        return {
            "status": "success",
            "message": "Database seeded with comprehensive quarter data",
            "counts": counts,
            "staleness_patterns": {
                "fresh_cases": "0-2 days since last comm/note",
                "approaching_sla": "3-5 days since last comm/note", 
                "in_breach": "7+ days since last comm/note",
                "engineers_with_breaches": ["eng-003", "eng-005", "eng-007", "eng-010"]
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
