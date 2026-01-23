# =============================================================================
# CSAT Guardian - Sentiment Analysis Service
# =============================================================================
# This module provides sentiment analysis capabilities using Azure OpenAI.
#
# The sentiment analysis service:
# - Analyzes case descriptions for initial customer sentiment
# - Analyzes timeline entries (emails, notes) for sentiment shifts
# - Identifies key phrases indicating customer frustration
# - Generates recommendations based on detected sentiment
#
# This is the REAL Azure OpenAI integration - not mocked!
# =============================================================================

import time
from datetime import datetime
from typing import Optional

from openai import AsyncAzureOpenAI

from config import AppConfig, get_config
from models import (
    Case, TimelineEntry, SentimentResult, SentimentLabel, CaseAnalysis, AlertType
)
from logger import get_logger, log_api_call, log_case_event

# Get logger for this module
logger = get_logger(__name__)


# =============================================================================
# Prompts for Sentiment Analysis
# =============================================================================

SENTIMENT_ANALYSIS_PROMPT = """You are an expert customer sentiment analyst for a technical support organization.
Analyze the following customer communication and provide a sentiment assessment.

Customer Communication:
---
{content}
---

Analyze this communication and respond in the following JSON format:
{{
    "score": <float between 0.0 and 1.0, where 0.0 is very negative and 1.0 is very positive>,
    "label": "<positive|neutral|negative>",
    "confidence": <float between 0.0 and 1.0>,
    "key_phrases": ["<phrase 1>", "<phrase 2>", ...],
    "concerns": ["<specific concern 1>", "<specific concern 2>", ...],
    "recommendations": ["<recommended action 1>", "<recommended action 2>", ...]
}}

Key phrases should be direct quotes from the text that indicate sentiment.
Concerns should summarize what the customer is worried about.
Recommendations should be specific actions the support engineer can take.

Respond ONLY with the JSON object, no additional text."""

CASE_SUMMARY_PROMPT = """You are an expert customer support analyst. 
Summarize the following support case for a support engineer who needs a quick briefing.

Case Title: {title}

Case Description:
---
{description}
---

Timeline (most recent activity):
---
{timeline}
---

Provide a brief summary (2-3 sentences) that includes:
1. What the customer's issue is
2. Current status/sentiment
3. Any urgent concerns

Keep the summary concise and actionable."""

RECOMMENDATION_PROMPT = """You are an expert customer support coach.
Based on the following case analysis, provide specific recommendations for the support engineer.

Case Title: {title}
Overall Sentiment: {sentiment_label} (score: {sentiment_score})
Days Since Creation: {days_since_creation}
Days Since Last Update: {days_since_update}

Recent Customer Communications:
---
{recent_communications}
---

Concerns Identified:
{concerns}

Provide 3-5 specific, actionable recommendations for the engineer to improve this customer's experience.
Format as a numbered list."""


class SentimentAnalysisService:
    """
    Service for analyzing customer sentiment using Azure OpenAI.
    
    This service provides:
    - Single text sentiment analysis
    - Case-level sentiment aggregation
    - Trend detection across timeline entries
    - Recommendation generation
    
    Usage:
        service = SentimentAnalysisService(config)
        result = await service.analyze_text("Customer message here")
        print(f"Sentiment: {result.label}, Score: {result.score}")
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize the sentiment analysis service.
        
        Args:
            config: Application configuration (uses global config if not provided)
        """
        logger.info("Initializing SentimentAnalysisService")
        
        # Get configuration
        self.config = config or get_config()
        
        # Check if Azure OpenAI is configured
        if not self.config.azure_openai.endpoint:
            logger.warning("Azure OpenAI endpoint not configured")
            logger.warning("Sentiment analysis will return default values")
            self.client = None
        else:
            # Initialize Azure OpenAI client
            logger.info(f"  → Connecting to Azure OpenAI: {self.config.azure_openai.endpoint}")
            self.client = AsyncAzureOpenAI(
                azure_endpoint=self.config.azure_openai.endpoint,
                api_key=self.config.azure_openai.api_key,
                api_version=self.config.azure_openai.api_version,
            )
            logger.info("  → Azure OpenAI client initialized successfully")
        
        # Store deployment name
        self.deployment = self.config.azure_openai.deployment
        
        # Sentiment threshold from config
        self.negative_threshold = self.config.thresholds.negative_sentiment_threshold
    
    async def analyze_text(self, content: str) -> SentimentResult:
        """
        Analyze sentiment of a single piece of text.
        
        This method sends the content to Azure OpenAI for analysis
        and returns a structured sentiment result.
        
        Args:
            content: The text to analyze
            
        Returns:
            SentimentResult: The sentiment analysis result
        """
        start_time = time.time()
        logger.debug(f"Analyzing sentiment for text ({len(content)} chars)")
        
        # If Azure OpenAI is not configured, return a default result
        if self.client is None:
            logger.warning("Azure OpenAI not configured, returning default sentiment")
            return SentimentResult.from_score(
                0.5,  # Neutral score
                confidence=0.0,
                key_phrases=[],
                concerns=[],
                recommendations=["Configure Azure OpenAI for real sentiment analysis"],
            )
        
        try:
            # Build the prompt
            prompt = SENTIMENT_ANALYSIS_PROMPT.format(content=content)
            
            # Call Azure OpenAI
            logger.debug("Calling Azure OpenAI for sentiment analysis...")
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a sentiment analysis expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                max_tokens=500,
            )
            
            # Log the API call
            log_api_call(
                logger, "azure_openai", "sentiment_analysis", True,
                duration_ms=(time.time() - start_time) * 1000,
                content_length=len(content),
                tokens_used=response.usage.total_tokens if response.usage else None,
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"Azure OpenAI response: {response_text[:200]}...")
            
            # Parse JSON response
            import json
            try:
                result_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                logger.error(f"Response was: {response_text}")
                # Return neutral sentiment on parse error
                return SentimentResult.from_score(0.5, confidence=0.0)
            
            # Build SentimentResult from response
            result = SentimentResult(
                score=float(result_data.get("score", 0.5)),
                label=SentimentLabel(result_data.get("label", "neutral")),
                confidence=float(result_data.get("confidence", 0.8)),
                key_phrases=result_data.get("key_phrases", []),
                concerns=result_data.get("concerns", []),
                recommendations=result_data.get("recommendations", []),
            )
            
            logger.info(
                f"Sentiment analysis complete: {result.label.value} "
                f"(score={result.score:.2f}, confidence={result.confidence:.2f})"
            )
            
            return result
            
        except Exception as e:
            # Log the error
            log_api_call(
                logger, "azure_openai", "sentiment_analysis", False,
                duration_ms=(time.time() - start_time) * 1000,
                content_length=len(content),
                error=str(e),
            )
            logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
            
            # Return neutral sentiment on error
            return SentimentResult.from_score(0.5, confidence=0.0)
    
    async def analyze_case(self, case: Case) -> CaseAnalysis:
        """
        Perform comprehensive analysis of a case.
        
        This method:
        1. Analyzes the case description
        2. Analyzes each customer communication in the timeline
        3. Calculates overall sentiment and trend
        4. Checks compliance (7-day rule)
        5. Determines which alerts should be triggered
        
        Args:
            case: The case to analyze
            
        Returns:
            CaseAnalysis: Complete analysis of the case
        """
        start_time = time.time()
        log_case_event(logger, case.id, "Starting case analysis")
        
        # -------------------------------------------------------------------------
        # Step 1: Analyze case description
        # -------------------------------------------------------------------------
        logger.debug(f"[Case {case.id}] Analyzing case description...")
        description_sentiment = await self.analyze_text(case.description)
        
        # -------------------------------------------------------------------------
        # Step 2: Analyze customer communications from timeline
        # -------------------------------------------------------------------------
        customer_communications = [
            entry for entry in case.timeline
            if entry.is_customer_communication
        ]
        
        communication_sentiments = []
        for entry in customer_communications:
            logger.debug(f"[Case {case.id}] Analyzing timeline entry {entry.id}...")
            sentiment = await self.analyze_text(entry.content)
            communication_sentiments.append((entry.created_on, sentiment))
        
        # -------------------------------------------------------------------------
        # Step 3: Calculate overall sentiment
        # -------------------------------------------------------------------------
        if communication_sentiments:
            # Weight recent communications more heavily
            total_weight = 0
            weighted_score = 0
            
            for i, (created_on, sentiment) in enumerate(sorted(communication_sentiments, key=lambda x: x[0])):
                # More recent = higher weight
                weight = 1 + (i * 0.5)
                weighted_score += sentiment.score * weight
                total_weight += weight
            
            overall_score = weighted_score / total_weight if total_weight > 0 else 0.5
            
            # Combine key phrases and concerns from all analyses
            all_key_phrases = []
            all_concerns = []
            all_recommendations = []
            
            for _, sentiment in communication_sentiments:
                all_key_phrases.extend(sentiment.key_phrases)
                all_concerns.extend(sentiment.concerns)
                all_recommendations.extend(sentiment.recommendations)
            
            overall_sentiment = SentimentResult(
                score=overall_score,
                label=SentimentLabel.NEGATIVE if overall_score < 0.4 else (
                    SentimentLabel.POSITIVE if overall_score > 0.6 else SentimentLabel.NEUTRAL
                ),
                confidence=sum(s.confidence for _, s in communication_sentiments) / len(communication_sentiments),
                key_phrases=list(set(all_key_phrases))[:5],  # Deduplicate and limit
                concerns=list(set(all_concerns))[:5],
                recommendations=list(set(all_recommendations))[:5],
            )
        else:
            # No customer communications, use description sentiment
            overall_sentiment = description_sentiment
        
        # -------------------------------------------------------------------------
        # Step 4: Determine sentiment trend
        # -------------------------------------------------------------------------
        if len(communication_sentiments) >= 2:
            # Compare first half to second half
            midpoint = len(communication_sentiments) // 2
            first_half_avg = sum(s.score for _, s in communication_sentiments[:midpoint]) / midpoint
            second_half_avg = sum(s.score for _, s in communication_sentiments[midpoint:]) / (len(communication_sentiments) - midpoint)
            
            if second_half_avg > first_half_avg + 0.1:
                sentiment_trend = "improving"
            elif second_half_avg < first_half_avg - 0.1:
                sentiment_trend = "declining"
            else:
                sentiment_trend = "stable"
        else:
            sentiment_trend = "stable"
        
        # -------------------------------------------------------------------------
        # Step 5: Check 7-day compliance
        # -------------------------------------------------------------------------
        days_since_note = case.days_since_last_note
        warning_days = self.config.thresholds.case_update_warning_days
        breach_days = self.config.thresholds.case_update_breach_days
        
        if days_since_note >= breach_days:
            compliance_status = "breach"
        elif days_since_note >= warning_days:
            compliance_status = "warning"
        else:
            compliance_status = "compliant"
        
        logger.debug(
            f"[Case {case.id}] Compliance check: "
            f"{days_since_note:.1f} days since last note, status={compliance_status}"
        )
        
        # -------------------------------------------------------------------------
        # Step 6: Determine which alerts to trigger
        # -------------------------------------------------------------------------
        alerts_triggered = []
        
        # Negative sentiment alert
        if overall_sentiment.label == SentimentLabel.NEGATIVE:
            alerts_triggered.append(AlertType.SENTIMENT_ALERT)
            logger.info(f"[Case {case.id}] ⚠️ Negative sentiment detected!")
        
        # 7-day compliance alerts
        if compliance_status == "warning":
            alerts_triggered.append(AlertType.SEVEN_DAY_WARNING)
            logger.info(f"[Case {case.id}] ⚠️ Approaching 7-day update deadline!")
        elif compliance_status == "breach":
            alerts_triggered.append(AlertType.SEVEN_DAY_BREACH)
            logger.info(f"[Case {case.id}] 🚨 7-day update deadline BREACHED!")
        
        # Declining sentiment alert (recovery suggestion)
        if sentiment_trend == "declining":
            alerts_triggered.append(AlertType.RECOVERY_SUGGESTION)
            logger.info(f"[Case {case.id}] ⚠️ Sentiment is declining!")
        
        # -------------------------------------------------------------------------
        # Step 7: Generate case summary
        # -------------------------------------------------------------------------
        summary = await self._generate_summary(case, overall_sentiment)
        
        # -------------------------------------------------------------------------
        # Build and return CaseAnalysis
        # -------------------------------------------------------------------------
        analysis = CaseAnalysis(
            case=case,
            overall_sentiment=overall_sentiment,
            sentiment_trend=sentiment_trend,
            compliance_status=compliance_status,
            days_since_last_note=days_since_note,
            alerts_triggered=alerts_triggered,
            summary=summary,
            recommendations=overall_sentiment.recommendations,
        )
        
        duration_ms = (time.time() - start_time) * 1000
        log_case_event(
            logger, case.id, "Case analysis complete",
            sentiment_label=overall_sentiment.label.value,
            sentiment_score=overall_sentiment.score,
            compliance_status=compliance_status,
            alerts_count=len(alerts_triggered),
            duration_ms=duration_ms,
        )
        
        return analysis
    
    async def _generate_summary(self, case: Case, sentiment: SentimentResult) -> str:
        """
        Generate a brief case summary using Azure OpenAI.
        
        Args:
            case: The case to summarize
            sentiment: The overall sentiment result
            
        Returns:
            str: A brief case summary
        """
        # If Azure OpenAI is not configured, return a simple summary
        if self.client is None:
            return f"Case '{case.title}' - Sentiment: {sentiment.label.value}"
        
        try:
            # Build timeline text (last 3 entries)
            recent_timeline = case.timeline[-3:] if case.timeline else []
            timeline_text = "\n".join(
                f"[{entry.entry_type.value}] {entry.created_by}: {entry.content[:200]}..."
                for entry in recent_timeline
            )
            
            prompt = CASE_SUMMARY_PROMPT.format(
                title=case.title,
                description=case.description[:500],
                timeline=timeline_text or "No timeline entries yet.",
            )
            
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a concise technical writer."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=200,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate case summary: {e}")
            return f"Case '{case.title}' - Sentiment: {sentiment.label.value}"


# =============================================================================
# Module-level singleton for easy access
# =============================================================================

_sentiment_service: Optional[SentimentAnalysisService] = None


def get_sentiment_service(config: Optional[AppConfig] = None) -> SentimentAnalysisService:
    """
    Get the sentiment analysis service singleton.
    
    Args:
        config: Application configuration (uses global config if not provided)
        
    Returns:
        SentimentAnalysisService: The shared service instance
    """
    global _sentiment_service
    
    if _sentiment_service is None:
        _sentiment_service = SentimentAnalysisService(config)
    
    return _sentiment_service


def reset_sentiment_service() -> None:
    """Reset the sentiment service singleton."""
    global _sentiment_service
    _sentiment_service = None
    logger.debug("Sentiment service singleton reset")
