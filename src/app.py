# =============================================================================
# CSAT Guardian - Streamlit POC Dashboard
# =============================================================================
# A modern web interface for CSAT Guardian demonstrating:
# - Case overview and status dashboard
# - Real-time sentiment analysis
# - Conversational AI chat interface
# - Alert visualization
#
# Usage:
#   streamlit run app.py
#   streamlit run app.py --server.port 8501
#
# =============================================================================

import asyncio
import streamlit as st
from datetime import datetime
from typing import Optional, List

# Local imports
from config import get_config
from database import DatabaseManager
from clients.dfm_client import get_dfm_client
from services.sentiment_service import get_sentiment_service
from models import Case, Engineer, CaseStatus, CasePriority


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="CSAT Guardian",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-top: 0;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    
    /* Status badges */
    .status-active { color: #28a745; font-weight: bold; }
    .status-warning { color: #ffc107; font-weight: bold; }
    .status-danger { color: #dc3545; font-weight: bold; }
    
    /* Chat messages */
    .chat-user {
        background-color: #e3f2fd;
        padding: 10px 15px;
        border-radius: 15px 15px 5px 15px;
        margin: 5px 0;
    }
    .chat-assistant {
        background-color: #f5f5f5;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 5px;
        margin: 5px 0;
    }
    
    /* Case cards */
    .case-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        transition: box-shadow 0.3s;
    }
    .case-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Session State Management
# =============================================================================

def init_session_state():
    """Initialize session state variables."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
        st.session_state.config = None
        st.session_state.database = None
        st.session_state.dfm_client = None
        st.session_state.sentiment_service = None
        st.session_state.current_engineer = None
        st.session_state.cases = []
        st.session_state.selected_case = None
        st.session_state.chat_history = []
        st.session_state.analysis_cache = {}


async def initialize_services():
    """Initialize all Azure services."""
    if st.session_state.initialized:
        return True
    
    try:
        # Load config
        st.session_state.config = get_config()
        
        # Connect to Azure SQL (use effective_connection_string for fallback handling)
        conn_string = st.session_state.config.database.effective_connection_string
        st.session_state.database = DatabaseManager(conn_string)
        await st.session_state.database.initialize()
        
        # Initialize DfM client
        st.session_state.dfm_client = await get_dfm_client(
            st.session_state.config,
            st.session_state.database
        )
        
        # Initialize sentiment service
        st.session_state.sentiment_service = get_sentiment_service(
            st.session_state.config
        )
        
        st.session_state.initialized = True
        return True
        
    except Exception as e:
        import traceback
        st.error(f"Failed to initialize services: {e}")
        st.code(traceback.format_exc(), language="python")
        return False


async def load_engineer(engineer_id: str) -> Optional[Engineer]:
    """Load engineer from database."""
    if not st.session_state.database:
        return None
    
    engineer_db = await st.session_state.database.get_engineer(engineer_id)
    if engineer_db:
        return Engineer(
            id=engineer_db.id,
            name=engineer_db.name,
            email=engineer_db.email,
        )
    return None


async def load_cases(engineer_id: str) -> List[Case]:
    """Load cases for an engineer."""
    if not st.session_state.dfm_client:
        return []
    
    return await st.session_state.dfm_client.get_cases_by_owner(engineer_id)


async def analyze_sentiment(case: Case) -> dict:
    """Analyze sentiment for a case."""
    cache_key = f"{case.id}_{len(case.timeline)}"
    
    if cache_key in st.session_state.analysis_cache:
        return st.session_state.analysis_cache[cache_key]
    
    if not st.session_state.sentiment_service:
        return None
    
    result = await st.session_state.sentiment_service.analyze_case_sentiment(case)
    st.session_state.analysis_cache[cache_key] = result
    return result


# =============================================================================
# UI Components
# =============================================================================

def render_header():
    """Render the main header."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<p class="main-header">🛡️ CSAT Guardian</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Proactive Customer Satisfaction Monitoring</p>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: right; padding-top: 10px;">
            <span style="color: #28a745;">●</span> Connected to Azure Gov<br/>
            <small style="color: #666;">{datetime.now().strftime('%Y-%m-%d %H:%M')}</small>
        </div>
        """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with engineer selection and filters."""
    with st.sidebar:
        st.markdown("### 👤 Engineer Profile")
        
        engineer_options = {
            "eng-001": "John Smith",
            "eng-002": "Mike Chen", 
            "eng-003": "Sarah Johnson"
        }
        
        selected_id = st.selectbox(
            "Select Engineer",
            options=list(engineer_options.keys()),
            format_func=lambda x: f"{engineer_options[x]} ({x})",
            key="engineer_select"
        )
        
        st.markdown("---")
        st.markdown("### 🔍 Filters")
        
        status_filter = st.multiselect(
            "Case Status",
            options=[s.value for s in CaseStatus],
            default=["active", "in_progress"],
            key="status_filter"
        )
        
        priority_filter = st.multiselect(
            "Priority",
            options=[p.value for p in CasePriority],
            default=["high", "medium", "low"],
            key="priority_filter"
        )
        
        st.markdown("---")
        st.markdown("### ⚙️ Settings")
        
        show_compliance = st.checkbox("Show Compliance Status", value=True)
        show_sentiment = st.checkbox("Show Sentiment Indicators", value=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #888; font-size: 0.8rem;">
            <p>CSAT Guardian v0.1.0</p>
            <p>Azure Government</p>
        </div>
        """, unsafe_allow_html=True)
        
        return selected_id, status_filter, priority_filter, show_compliance, show_sentiment


def render_metrics(cases: List[Case]):
    """Render the metrics dashboard."""
    total = len(cases)
    active = sum(1 for c in cases if c.status == CaseStatus.ACTIVE)
    high_priority = sum(1 for c in cases if c.priority == CasePriority.HIGH)
    overdue = sum(1 for c in cases if c.days_since_last_note >= 7)
    warning = sum(1 for c in cases if 5 <= c.days_since_last_note < 7)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Cases", total)
    with col2:
        st.metric("Active", active)
    with col3:
        st.metric("High Priority", high_priority, delta=None)
    with col4:
        st.metric("⚠️ Warning", warning, delta=None)
    with col5:
        st.metric("🚨 Overdue", overdue, delta=None if overdue == 0 else f"+{overdue}")


def get_status_icon(case: Case) -> str:
    """Get status icon based on compliance."""
    if case.days_since_last_note >= 7:
        return "🚨"
    elif case.days_since_last_note >= 5:
        return "⚠️"
    else:
        return "✅"


def render_case_list(cases: List[Case], status_filter: list, priority_filter: list):
    """Render the case list."""
    # Filter cases
    filtered_cases = [
        c for c in cases 
        if c.status.value in status_filter and c.priority.value in priority_filter
    ]
    
    if not filtered_cases:
        st.info("No cases match the current filters.")
        return None
    
    st.markdown(f"### 📋 Cases ({len(filtered_cases)})")
    
    # Sort by days since last note (most urgent first)
    filtered_cases.sort(key=lambda x: -x.days_since_last_note)
    
    selected_case = None
    
    for case in filtered_cases:
        icon = get_status_icon(case)
        
        with st.expander(
            f"{icon} **{case.id}** - {case.title[:50]}...",
            expanded=False
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**Customer:** {case.customer.company}")
                st.markdown(f"**Priority:** {case.priority.value.upper()}")
            
            with col2:
                st.markdown(f"**Status:** {case.status.value}")
                st.markdown(f"**Created:** {case.created_on.strftime('%Y-%m-%d')}")
            
            with col3:
                days = case.days_since_last_note
                if days >= 7:
                    st.markdown(f"**Last Note:** :red[{days:.1f} days ago (BREACH)]")
                elif days >= 5:
                    st.markdown(f"**Last Note:** :orange[{days:.1f} days ago (WARNING)]")
                else:
                    st.markdown(f"**Last Note:** :green[{days:.1f} days ago]")
            
            st.markdown("---")
            st.markdown(f"**Description:** {case.description[:200]}...")
            
            if st.button("📊 Analyze Case", key=f"analyze_{case.id}"):
                selected_case = case
    
    return selected_case


def render_case_detail(case: Case):
    """Render detailed case view with analysis."""
    st.markdown(f"## 📄 Case Details: {case.id}")
    
    # Case info
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Title:** {case.title}
        
        **Customer:** {case.customer.company}  
        **Contact:** {case.customer.name} ({case.customer.email})
        
        **Status:** {case.status.value}  
        **Priority:** {case.priority.value.upper()}
        """)
    
    with col2:
        st.markdown(f"""
        **Created:** {case.created_on.strftime('%Y-%m-%d %H:%M')}  
        **Days Open:** {case.days_since_creation:.0f} days
        
        **Last Note:** {case.days_since_last_note:.1f} days ago
        
        **Timeline Entries:** {len(case.timeline)}
        """)
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["🎭 Sentiment Analysis", "📝 Timeline", "💬 Chat"])
    
    with tab1:
        render_sentiment_analysis(case)
    
    with tab2:
        render_timeline(case)
    
    with tab3:
        render_chat(case)


def render_sentiment_analysis(case: Case):
    """Render sentiment analysis for a case."""
    st.markdown("### Sentiment Analysis")
    
    with st.spinner("Analyzing sentiment with Azure OpenAI..."):
        result = asyncio.run(analyze_sentiment(case))
    
    if not result:
        st.warning("Unable to analyze sentiment. Please check Azure OpenAI connection.")
        return
    
    # Display results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sentiment = result.overall_sentiment.value
        if sentiment == "negative":
            st.markdown("### 😞 Negative")
            st.progress(result.sentiment_score)
        elif sentiment == "positive":
            st.markdown("### 😊 Positive")
            st.progress(result.sentiment_score)
        else:
            st.markdown("### 😐 Neutral")
            st.progress(result.sentiment_score)
        
        st.markdown(f"**Score:** {result.sentiment_score:.2f}")
    
    with col2:
        st.markdown("### 📊 Confidence")
        st.progress(result.confidence)
        st.markdown(f"**{result.confidence * 100:.0f}%**")
    
    with col3:
        trend = result.trend
        if trend == "declining":
            st.markdown("### 📉 Declining")
            st.error("Customer satisfaction is declining")
        elif trend == "improving":
            st.markdown("### 📈 Improving")
            st.success("Customer satisfaction is improving")
        else:
            st.markdown("### ➡️ Stable")
            st.info("Customer satisfaction is stable")
    
    # Key phrases
    if result.key_phrases:
        st.markdown("---")
        st.markdown("### 🔑 Key Phrases")
        
        cols = st.columns(min(len(result.key_phrases), 4))
        for i, phrase in enumerate(result.key_phrases[:8]):
            with cols[i % 4]:
                st.markdown(f"`{phrase}`")
    
    # Recommendations
    if result.recommendations:
        st.markdown("---")
        st.markdown("### 💡 Recommendations")
        
        for i, rec in enumerate(result.recommendations, 1):
            st.markdown(f"{i}. {rec}")


def render_timeline(case: Case):
    """Render case timeline."""
    st.markdown("### Case Timeline")
    
    if not case.timeline:
        st.info("No timeline entries found.")
        return
    
    for entry in reversed(case.timeline[-10:]):  # Show last 10
        entry_type = entry.entry_type.value.upper()
        
        if entry_type == "NOTE":
            icon = "📝"
        elif entry_type == "EMAIL":
            icon = "📧"
        elif entry_type == "CALL":
            icon = "📞"
        else:
            icon = "📄"
        
        with st.container():
            st.markdown(f"""
            **{icon} {entry_type}** - {entry.created_on.strftime('%Y-%m-%d %H:%M')}
            
            {entry.content[:500]}{"..." if len(entry.content) > 500 else ""}
            
            ---
            """)


def render_chat(case: Case):
    """Render chat interface for case."""
    st.markdown("### 💬 Chat with Guardian")
    st.markdown("*Ask questions about this case*")
    
    # Initialize chat history for this case
    if f"chat_{case.id}" not in st.session_state:
        st.session_state[f"chat_{case.id}"] = []
    
    chat_history = st.session_state[f"chat_{case.id}"]
    
    # Display chat history
    for message in chat_history:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-user">
                <strong>You:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-assistant">
                <strong>Guardian:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Ask about this case...")
    
    if user_input:
        # Add user message
        chat_history.append({"role": "user", "content": user_input})
        
        # Generate response (simplified for POC)
        response = generate_chat_response(case, user_input)
        chat_history.append({"role": "assistant", "content": response})
        
        st.session_state[f"chat_{case.id}"] = chat_history
        st.rerun()
    
    # Quick action buttons
    st.markdown("---")
    st.markdown("**Quick Actions:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Summarize", key=f"sum_{case.id}"):
            chat_history.append({"role": "user", "content": "Give me a summary of this case"})
            response = generate_chat_response(case, "summary")
            chat_history.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col2:
        if st.button("🎭 Sentiment", key=f"sent_{case.id}"):
            chat_history.append({"role": "user", "content": "What's the customer sentiment?"})
            response = generate_chat_response(case, "sentiment")
            chat_history.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col3:
        if st.button("💡 Recommend", key=f"rec_{case.id}"):
            chat_history.append({"role": "user", "content": "What do you recommend I do?"})
            response = generate_chat_response(case, "recommendations")
            chat_history.append({"role": "assistant", "content": response})
            st.rerun()


def generate_chat_response(case: Case, user_input: str) -> str:
    """Generate a chat response for the case."""
    # Simplified response generation for POC
    # In production, this would use the full Guardian Agent with Semantic Kernel
    
    input_lower = user_input.lower()
    
    if "summary" in input_lower or "summarize" in input_lower:
        return f"""**Case Summary for {case.id}**

**Title:** {case.title}
**Customer:** {case.customer.company} ({case.customer.name})
**Status:** {case.status.value} | **Priority:** {case.priority.value}

**Overview:** This case has been open for {case.days_since_creation:.0f} days. The last update was {case.days_since_last_note:.1f} days ago.

There are {len(case.timeline)} timeline entries documenting the interaction history.

**Description:** {case.description[:300]}..."""

    elif "sentiment" in input_lower:
        result = asyncio.run(analyze_sentiment(case))
        if result:
            return f"""**Sentiment Analysis**

😊 **Overall:** {result.overall_sentiment.value.upper()}
📊 **Score:** {result.sentiment_score:.2f} (0=negative, 1=positive)
📈 **Trend:** {result.trend}
🎯 **Confidence:** {result.confidence * 100:.0f}%

**Key Indicators:** {', '.join(result.key_phrases[:5]) if result.key_phrases else 'None detected'}"""
        else:
            return "I couldn't analyze the sentiment at this time. Please try again."

    elif "recommend" in input_lower or "suggest" in input_lower or "what should" in input_lower:
        result = asyncio.run(analyze_sentiment(case))
        if result and result.recommendations:
            recs = "\n".join([f"• {r}" for r in result.recommendations])
            return f"""**Recommended Actions for {case.id}**

Based on my analysis, here are my recommendations:

{recs}

**Compliance Note:** {"⚠️ This case is approaching the 7-day update requirement." if case.days_since_last_note >= 5 else "✅ Case is within compliance window."}"""
        else:
            return f"""**Recommendations for {case.id}**

Based on the case status:

• {"🚨 URGENT: Add a case note immediately - you're past the 7-day requirement!" if case.days_since_last_note >= 7 else ""}
• {"⚠️ Add a case note soon - approaching 7-day deadline" if 5 <= case.days_since_last_note < 7 else ""}
• Review the recent timeline entries for context
• Consider reaching out to the customer for a status update
• Document any blockers or dependencies"""

    else:
        # Generic response
        return f"""I understand you're asking about **{case.title}**.

This is a {case.priority.value} priority case for {case.customer.company}. It's been open for {case.days_since_creation:.0f} days with the last update {case.days_since_last_note:.1f} days ago.

You can ask me to:
• **Summarize** the case
• Analyze **sentiment**
• Get **recommendations**

Or ask specific questions about the case details, timeline, or customer."""


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point."""
    init_session_state()
    
    # Render header
    render_header()
    
    st.markdown("---")
    
    # Initialize services
    if not st.session_state.initialized:
        with st.spinner("🔌 Connecting to Azure services..."):
            success = asyncio.run(initialize_services())
            if not success:
                st.error("Failed to initialize. Please check your Azure configuration.")
                st.stop()
    
    # Render sidebar and get selections
    engineer_id, status_filter, priority_filter, show_compliance, show_sentiment = render_sidebar()
    
    # Load engineer if changed
    if st.session_state.current_engineer is None or st.session_state.current_engineer.id != engineer_id:
        with st.spinner(f"Loading engineer profile..."):
            engineer = asyncio.run(load_engineer(engineer_id))
            if engineer:
                st.session_state.current_engineer = engineer
                st.session_state.cases = asyncio.run(load_cases(engineer_id))
            else:
                st.error(f"Engineer {engineer_id} not found.")
                st.stop()
    
    # Welcome message
    if st.session_state.current_engineer:
        st.markdown(f"### 👋 Welcome, {st.session_state.current_engineer.name}!")
    
    # Render metrics
    if st.session_state.cases:
        render_metrics(st.session_state.cases)
    
    st.markdown("---")
    
    # Main content area
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Case list
        clicked_case = render_case_list(
            st.session_state.cases,
            status_filter,
            priority_filter
        )
        
        if clicked_case:
            st.session_state.selected_case = clicked_case
    
    with col2:
        # Case detail view
        if st.session_state.selected_case:
            render_case_detail(st.session_state.selected_case)
        else:
            st.info("👈 Select a case from the list to view details and analysis.")
            
            # Show some quick stats
            if st.session_state.cases:
                st.markdown("### 📊 Quick Overview")
                
                overdue = [c for c in st.session_state.cases if c.days_since_last_note >= 7]
                if overdue:
                    st.error(f"🚨 **{len(overdue)} case(s) require immediate attention!**")
                    for c in overdue[:3]:
                        st.markdown(f"• **{c.id}** - {c.title[:40]}... ({c.days_since_last_note:.0f} days overdue)")
                
                warning = [c for c in st.session_state.cases if 5 <= c.days_since_last_note < 7]
                if warning:
                    st.warning(f"⚠️ **{len(warning)} case(s) approaching deadline**")
                    for c in warning[:3]:
                        st.markdown(f"• **{c.id}** - {c.title[:40]}... ({c.days_since_last_note:.1f} days)")


if __name__ == "__main__":
    main()
