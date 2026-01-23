# =============================================================================
# CSAT Guardian - Conversational Agent
# =============================================================================
# This module implements the conversational AI agent using Semantic Kernel.
#
# The agent allows engineers to:
# - Ask questions about specific cases
# - Request case summaries
# - Get troubleshooting suggestions
# - Understand why a customer seems frustrated
# - Get help with response drafting
#
# The agent uses Semantic Kernel's plugin system to access:
# - Case data (via DfM client)
# - Sentiment analysis
# - Recommendation generation
# =============================================================================

import uuid
from datetime import datetime
from typing import Optional

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function

from config import AppConfig, get_config
from models import (
    Case, Engineer, ConversationSession, ConversationMessage
)
from clients.dfm_client import DfMClientBase, get_dfm_client
from services.sentiment_service import SentimentAnalysisService, get_sentiment_service
from logger import get_logger, log_case_event

# Get logger for this module
logger = get_logger(__name__)


# =============================================================================
# Semantic Kernel Plugin: Case Operations
# =============================================================================

class CasePlugin:
    """
    Semantic Kernel plugin for case operations.
    
    This plugin provides functions that the AI agent can call to:
    - Get case details
    - Get case summaries
    - Get case sentiment analysis
    - List cases for an engineer
    
    The plugin acts as a bridge between the conversational AI
    and the application's data and services.
    """
    
    def __init__(
        self,
        dfm_client: DfMClientBase,
        sentiment_service: SentimentAnalysisService,
        current_engineer_id: str,
    ):
        """
        Initialize the case plugin.
        
        Args:
            dfm_client: Client for accessing case data
            sentiment_service: Service for sentiment analysis
            current_engineer_id: The ID of the engineer in this conversation
        """
        self.dfm_client = dfm_client
        self.sentiment_service = sentiment_service
        self.current_engineer_id = current_engineer_id
        logger.debug(f"CasePlugin initialized for engineer: {current_engineer_id}")
    
    @kernel_function(
        name="get_case_summary",
        description="Get a summary of a specific case including title, status, priority, and recent activity"
    )
    async def get_case_summary(self, case_id: str) -> str:
        """
        Get a summary of a specific case.
        
        Args:
            case_id: The case identifier
            
        Returns:
            str: A formatted case summary
        """
        logger.info(f"CasePlugin.get_case_summary called for case: {case_id}")
        
        try:
            # Fetch the case
            case = await self.dfm_client.get_case(case_id)
            
            if case is None:
                return f"Case {case_id} not found."
            
            # Security check: only allow access to cases assigned to this engineer
            if case.owner.id != self.current_engineer_id:
                logger.warning(
                    f"Engineer {self.current_engineer_id} attempted to access "
                    f"case {case_id} owned by {case.owner.id}"
                )
                return f"You don't have access to case {case_id}. You can only view cases assigned to you."
            
            # Build summary
            summary = f"""📋 **Case Summary: {case_id}**

**Title:** {case.title}
**Status:** {case.status.value}
**Priority:** {case.priority.value}
**Created:** {case.created_on.strftime('%Y-%m-%d')} ({case.days_since_creation:.0f} days ago)
**Last Updated:** {case.modified_on.strftime('%Y-%m-%d')} ({case.days_since_last_update:.1f} days ago)
**Days Since Last Note:** {case.days_since_last_note:.1f}

**Customer:** {case.customer.company or 'Unknown'}

**Description:**
{case.description[:300]}{'...' if len(case.description) > 300 else ''}

**Timeline Entries:** {len(case.timeline)} total
"""
            
            # Add recent timeline entries
            if case.timeline:
                summary += "\n**Recent Activity:**\n"
                for entry in case.timeline[-3:]:
                    summary += f"• [{entry.entry_type.value}] {entry.created_on.strftime('%Y-%m-%d')}: {entry.content[:100]}...\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting case summary: {e}", exc_info=True)
            return f"Error retrieving case {case_id}: {str(e)}"
    
    @kernel_function(
        name="analyze_case_sentiment",
        description="Analyze the sentiment of a case to understand if the customer is happy, neutral, or frustrated"
    )
    async def analyze_case_sentiment(self, case_id: str) -> str:
        """
        Analyze the sentiment of a specific case.
        
        Args:
            case_id: The case identifier
            
        Returns:
            str: A sentiment analysis report
        """
        logger.info(f"CasePlugin.analyze_case_sentiment called for case: {case_id}")
        
        try:
            # Fetch the case
            case = await self.dfm_client.get_case(case_id)
            
            if case is None:
                return f"Case {case_id} not found."
            
            # Security check
            if case.owner.id != self.current_engineer_id:
                return f"You don't have access to case {case_id}."
            
            # Perform sentiment analysis
            analysis = await self.sentiment_service.analyze_case(case)
            
            # Format the result
            result = f"""🎭 **Sentiment Analysis: Case {case_id}**

**Overall Sentiment:** {analysis.overall_sentiment.label.value.upper()}
**Score:** {analysis.overall_sentiment.score:.2f} (0=negative, 1=positive)
**Confidence:** {analysis.overall_sentiment.confidence:.0%}
**Trend:** {analysis.sentiment_trend}

"""
            
            if analysis.overall_sentiment.key_phrases:
                result += "**Key Phrases Indicating Sentiment:**\n"
                for phrase in analysis.overall_sentiment.key_phrases[:5]:
                    result += f'• "{phrase}"\n'
                result += "\n"
            
            if analysis.overall_sentiment.concerns:
                result += "**Customer Concerns Identified:**\n"
                for concern in analysis.overall_sentiment.concerns[:5]:
                    result += f"• {concern}\n"
                result += "\n"
            
            # Compliance status
            result += f"**7-Day Compliance:** {analysis.compliance_status.upper()}\n"
            result += f"**Days Since Last Note:** {analysis.days_since_last_note:.1f}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing case sentiment: {e}", exc_info=True)
            return f"Error analyzing case {case_id}: {str(e)}"
    
    @kernel_function(
        name="get_recommendations",
        description="Get specific recommendations for how to handle a case and improve customer satisfaction"
    )
    async def get_recommendations(self, case_id: str) -> str:
        """
        Get recommendations for handling a case.
        
        Args:
            case_id: The case identifier
            
        Returns:
            str: Recommendations for the engineer
        """
        logger.info(f"CasePlugin.get_recommendations called for case: {case_id}")
        
        try:
            # Fetch the case
            case = await self.dfm_client.get_case(case_id)
            
            if case is None:
                return f"Case {case_id} not found."
            
            # Security check
            if case.owner.id != self.current_engineer_id:
                return f"You don't have access to case {case_id}."
            
            # Get recommendations from sentiment analysis
            analysis = await self.sentiment_service.analyze_case(case)
            
            result = f"""💡 **Recommendations for Case {case_id}**

Based on the case analysis, here are suggested actions:

"""
            
            if analysis.recommendations:
                for i, rec in enumerate(analysis.recommendations, 1):
                    result += f"{i}. {rec}\n"
            else:
                result += "• Review the case timeline for recent updates\n"
                result += "• Reach out to the customer with a status update\n"
                result += "• Consider if escalation to a specialist is needed\n"
            
            # Add compliance-specific recommendations
            if analysis.compliance_status == "warning":
                result += "\n⚠️ **Compliance Alert:** This case is approaching the 7-day update requirement. Please add a case note soon."
            elif analysis.compliance_status == "breach":
                result += "\n🚨 **Compliance Alert:** This case has exceeded the 7-day update requirement. Please add a case note immediately."
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}", exc_info=True)
            return f"Error getting recommendations for case {case_id}: {str(e)}"
    
    @kernel_function(
        name="list_my_cases",
        description="List all cases assigned to the current engineer"
    )
    async def list_my_cases(self) -> str:
        """
        List all cases assigned to the current engineer.
        
        Returns:
            str: A list of cases
        """
        logger.info(f"CasePlugin.list_my_cases called for engineer: {self.current_engineer_id}")
        
        try:
            # Fetch cases for this engineer
            cases = await self.dfm_client.get_cases_by_owner(self.current_engineer_id)
            
            if not cases:
                return "You don't have any cases assigned to you."
            
            result = f"📂 **Your Cases ({len(cases)} total)**\n\n"
            
            for case in cases:
                # Indicator for cases needing attention
                indicator = ""
                if case.days_since_last_note >= 7:
                    indicator = "🚨 "
                elif case.days_since_last_note >= 5:
                    indicator = "⚠️ "
                
                result += (
                    f"{indicator}**{case.id}** - {case.title[:50]}"
                    f"{'...' if len(case.title) > 50 else ''}\n"
                    f"   Status: {case.status.value} | "
                    f"Priority: {case.priority.value} | "
                    f"Last note: {case.days_since_last_note:.0f} days ago\n\n"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing cases: {e}", exc_info=True)
            return f"Error listing cases: {str(e)}"


# =============================================================================
# Conversational Agent
# =============================================================================

class CSATGuardianAgent:
    """
    The CSAT Guardian conversational agent.
    
    This agent:
    - Maintains conversation context with engineers
    - Uses Semantic Kernel for natural language understanding
    - Calls plugins to access case data and services
    - Provides helpful responses and recommendations
    
    Usage:
        agent = CSATGuardianAgent(engineer, dfm_client, sentiment_service, config)
        response = await agent.chat("Tell me about case 12345")
        print(response)
    """
    
    def __init__(
        self,
        engineer: Engineer,
        dfm_client: DfMClientBase,
        sentiment_service: SentimentAnalysisService,
        config: Optional[AppConfig] = None,
    ):
        """
        Initialize the CSAT Guardian agent for a specific engineer.
        
        Args:
            engineer: The engineer interacting with the agent
            dfm_client: Client for case data access
            sentiment_service: Service for sentiment analysis
            config: Application configuration
        """
        logger.info(f"Initializing CSATGuardianAgent for engineer: {engineer.name}")
        
        self.engineer = engineer
        self.config = config or get_config()
        
        # Create conversation session
        self.session = ConversationSession(
            id=str(uuid.uuid4()),
            engineer=engineer,
        )
        
        # Initialize Semantic Kernel
        self.kernel = Kernel()
        
        # Add Azure OpenAI service if configured
        if self.config.azure_openai.endpoint:
            logger.debug("Adding Azure OpenAI chat completion service...")
            self.kernel.add_service(
                AzureChatCompletion(
                    deployment_name=self.config.azure_openai.deployment,
                    endpoint=self.config.azure_openai.endpoint,
                    api_key=self.config.azure_openai.api_key,
                    api_version=self.config.azure_openai.api_version,
                )
            )
        else:
            logger.warning("Azure OpenAI not configured - agent will have limited functionality")
        
        # Add case plugin
        self.case_plugin = CasePlugin(
            dfm_client=dfm_client,
            sentiment_service=sentiment_service,
            current_engineer_id=engineer.id,
        )
        self.kernel.add_plugin(self.case_plugin, "case")
        
        # Initialize chat history with system prompt
        self.chat_history = ChatHistory()
        self.chat_history.add_system_message(self._get_system_prompt())
        
        logger.info("CSATGuardianAgent initialized successfully")
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt that defines the agent's behavior.
        
        Returns:
            str: The system prompt
        """
        return f"""You are CSAT Guardian, an AI assistant that helps support engineers improve customer satisfaction.

You are currently helping {self.engineer.name}.

Your capabilities:
1. Summarize cases assigned to the engineer
2. Analyze customer sentiment to identify frustrated or unhappy customers
3. Provide specific recommendations for handling difficult situations
4. Help with response drafting and communication strategies
5. Track 7-day case note compliance

Important rules:
- You can ONLY discuss cases assigned to {self.engineer.name}
- You CANNOT modify case data or send messages to customers
- You provide SUGGESTIONS - the engineer makes all decisions
- Be concise and actionable in your responses
- If asked about cases not assigned to this engineer, politely decline

When an engineer asks about a case, use your available functions to:
1. Get the case summary first
2. Then provide analysis or recommendations as needed

Be helpful, professional, and focused on improving the customer experience."""
    
    async def chat(self, message: str) -> str:
        """
        Process a message from the engineer and generate a response.
        
        Args:
            message: The engineer's message
            
        Returns:
            str: The agent's response
        """
        logger.info(f"Agent received message from {self.engineer.name}: {message[:50]}...")
        
        # Add message to session
        self.session.add_message("engineer", message)
        
        # Add to chat history
        self.chat_history.add_user_message(message)
        
        try:
            # Check if Azure OpenAI is configured
            if not self.config.azure_openai.endpoint:
                response = self._generate_fallback_response(message)
            else:
                # Use Semantic Kernel to generate response with function calling
                from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
                from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
                
                settings = OpenAIChatPromptExecutionSettings(
                    function_choice_behavior=FunctionChoiceBehavior.Auto(),
                    max_tokens=1000,
                    temperature=0.7,
                )
                
                result = await self.kernel.invoke_prompt(
                    prompt="{{$chat_history}}",
                    settings=settings,
                    chat_history=self.chat_history,
                )
                
                response = str(result)
            
            # Add response to session
            self.session.add_message("agent", response)
            
            # Add to chat history
            self.chat_history.add_assistant_message(response)
            
            logger.debug(f"Agent response: {response[:100]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            error_response = (
                "I apologize, but I encountered an error processing your request. "
                "Please try again or rephrase your question."
            )
            self.session.add_message("agent", error_response)
            return error_response
    
    def _generate_fallback_response(self, message: str) -> str:
        """
        Generate a fallback response when Azure OpenAI is not configured.
        
        Args:
            message: The engineer's message
            
        Returns:
            str: A helpful fallback response
        """
        message_lower = message.lower()
        
        # Check for common intents
        if "case" in message_lower and any(c.isdigit() for c in message):
            # Extract case ID
            import re
            case_ids = re.findall(r'case[- ]?(\d+)', message_lower)
            if not case_ids:
                case_ids = re.findall(r'\b(\d{5,})\b', message)
            
            if case_ids:
                return (
                    f"I'd like to help you with case {case_ids[0]}, but Azure OpenAI "
                    "is not configured. Please set up your Azure OpenAI credentials "
                    "in the .env file to enable full conversational capabilities."
                )
        
        if "list" in message_lower or "my cases" in message_lower:
            return (
                "To list your cases, I need Azure OpenAI to be configured. "
                "Please set up your credentials in the .env file. "
                "In the meantime, you can run the main monitoring scan to see your cases."
            )
        
        return (
            "I'm CSAT Guardian, here to help you improve customer satisfaction. "
            "However, Azure OpenAI is not currently configured, so my capabilities are limited. "
            "Please configure your Azure OpenAI credentials in the .env file to enable:\n"
            "• Case summaries and analysis\n"
            "• Sentiment detection\n"
            "• Personalized recommendations\n"
            "• Natural conversation"
        )
    
    def get_session(self) -> ConversationSession:
        """
        Get the current conversation session.
        
        Returns:
            ConversationSession: The conversation session with all messages
        """
        return self.session


# =============================================================================
# Factory Function
# =============================================================================

async def create_agent(
    engineer: Engineer,
    dfm_client: Optional[DfMClientBase] = None,
    sentiment_service: Optional[SentimentAnalysisService] = None,
    config: Optional[AppConfig] = None,
) -> CSATGuardianAgent:
    """
    Create a CSAT Guardian agent for an engineer.
    
    Args:
        engineer: The engineer to create the agent for
        dfm_client: DfM client (uses default if not provided)
        sentiment_service: Sentiment service (uses default if not provided)
        config: Application configuration (uses default if not provided)
        
    Returns:
        CSATGuardianAgent: A configured agent instance
    """
    logger.info(f"Creating CSAT Guardian agent for {engineer.name}")
    
    # Get dependencies
    if dfm_client is None:
        dfm_client = await get_dfm_client()
    
    if sentiment_service is None:
        sentiment_service = get_sentiment_service()
    
    if config is None:
        config = get_config()
    
    # Create and return agent
    return CSATGuardianAgent(
        engineer=engineer,
        dfm_client=dfm_client,
        sentiment_service=sentiment_service,
        config=config,
    )
