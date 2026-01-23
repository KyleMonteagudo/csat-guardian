# =============================================================================
# CSAT Guardian - Case Monitor Orchestrator
# =============================================================================
# This module orchestrates the case monitoring workflow:
# 1. Scans all active cases
# 2. Runs sentiment analysis on each case
# 3. Checks for 7-day compliance violations
# 4. Generates and sends alerts
#
# The monitor can run:
# - As a one-time scan
# - As a continuous background process
# =============================================================================

import asyncio
from datetime import datetime
from typing import Optional

from config import AppConfig, get_config
from models import Case, CaseAnalysis
from clients.dfm_client import DfMClientBase, get_dfm_client
from services.sentiment_service import SentimentAnalysisService, get_sentiment_service
from services.alert_service import AlertService, get_alert_service
from database import DatabaseManager
from logger import get_logger, log_case_event

# Get logger for this module
logger = get_logger(__name__)


class CaseMonitor:
    """
    Orchestrates case monitoring and analysis.
    
    This class is responsible for:
    - Fetching cases that need to be analyzed
    - Running sentiment analysis on each case
    - Checking 7-day compliance
    - Generating alerts for at-risk cases
    - Recording metrics for reporting
    
    Usage:
        monitor = CaseMonitor(dfm_client, sentiment_service, alert_service)
        results = await monitor.run_scan()
    """
    
    def __init__(
        self,
        dfm_client: DfMClientBase,
        sentiment_service: SentimentAnalysisService,
        alert_service: AlertService,
        database: DatabaseManager,
        config: Optional[AppConfig] = None,
    ):
        """
        Initialize the case monitor.
        
        Args:
            dfm_client: Client for accessing case data
            sentiment_service: Service for sentiment analysis
            alert_service: Service for generating and sending alerts
            database: Database manager for metrics storage
            config: Application configuration
        """
        logger.info("Initializing CaseMonitor...")
        
        self.dfm_client = dfm_client
        self.sentiment_service = sentiment_service
        self.alert_service = alert_service
        self.database = database
        self.config = config or get_config()
        
        # Scan tracking
        self._scan_count = 0
        self._last_scan_time: Optional[datetime] = None
        self._is_running = False
        
        logger.info("CaseMonitor initialized")
    
    async def run_scan(self) -> dict:
        """
        Run a single monitoring scan across all cases.
        
        This method:
        1. Fetches all active cases
        2. Analyzes each case for sentiment
        3. Checks for compliance violations
        4. Generates alerts as needed
        5. Returns a summary of findings
        
        Returns:
            dict: Summary of scan results including:
                - total_cases: Number of cases analyzed
                - negative_sentiment: Cases with negative sentiment
                - compliance_warnings: Cases approaching 7-day limit
                - compliance_breaches: Cases exceeding 7-day limit
                - alerts_sent: Number of alerts generated
        """
        logger.info("=" * 60)
        logger.info("STARTING CASE MONITORING SCAN")
        logger.info("=" * 60)
        
        self._scan_count += 1
        self._last_scan_time = datetime.utcnow()
        scan_id = f"scan-{self._scan_count}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Scan ID: {scan_id}")
        
        # Initialize counters
        results = {
            "scan_id": scan_id,
            "total_cases": 0,
            "negative_sentiment": 0,
            "declining_sentiment": 0,
            "compliance_warnings": 0,
            "compliance_breaches": 0,
            "alerts_sent": 0,
            "errors": 0,
            "start_time": self._last_scan_time.isoformat(),
            "end_time": None,
            "cases_analyzed": [],
        }
        
        try:
            # Step 1: Fetch all active cases
            logger.info("Step 1: Fetching active cases...")
            cases = await self._fetch_active_cases()
            results["total_cases"] = len(cases)
            logger.info(f"Found {len(cases)} active cases to analyze")
            
            if not cases:
                logger.warning("No cases found to analyze")
                results["end_time"] = datetime.utcnow().isoformat()
                return results
            
            # Step 2: Analyze each case
            logger.info("Step 2: Analyzing cases...")
            for i, case in enumerate(cases, 1):
                logger.info(f"Analyzing case {i}/{len(cases)}: {case.id}")
                
                try:
                    # Run analysis
                    analysis = await self._analyze_case(case)
                    
                    if analysis is None:
                        logger.warning(f"No analysis returned for case {case.id}")
                        results["errors"] += 1
                        continue
                    
                    # Track results
                    case_result = {
                        "case_id": case.id,
                        "sentiment": analysis.overall_sentiment.label.value,
                        "sentiment_score": analysis.overall_sentiment.score,
                        "trend": analysis.sentiment_trend,
                        "compliance_status": analysis.compliance_status,
                        "alerts_triggered": [],
                    }
                    
                    # Count sentiment issues
                    if analysis.overall_sentiment.label.value == "negative":
                        results["negative_sentiment"] += 1
                    
                    if analysis.sentiment_trend == "declining":
                        results["declining_sentiment"] += 1
                    
                    # Count compliance issues
                    if analysis.compliance_status == "warning":
                        results["compliance_warnings"] += 1
                    elif analysis.compliance_status == "breach":
                        results["compliance_breaches"] += 1
                    
                    # Step 3: Process alerts
                    alerts = await self.alert_service.process_analysis(analysis)
                    
                    if alerts:
                        results["alerts_sent"] += len(alerts)
                        case_result["alerts_triggered"] = [a.type.value for a in alerts]
                        logger.info(f"Generated {len(alerts)} alerts for case {case.id}")
                    
                    results["cases_analyzed"].append(case_result)
                    
                    log_case_event(
                        logger,
                        case.id,
                        f"Analysis complete - Sentiment: {analysis.overall_sentiment.label.value}, "
                        f"Compliance: {analysis.compliance_status}"
                    )
                    
                except Exception as e:
                    logger.error(f"Error analyzing case {case.id}: {e}", exc_info=True)
                    results["errors"] += 1
                    continue
            
            # Step 4: Record scan metrics
            logger.info("Step 4: Recording scan metrics...")
            await self._record_metrics(results)
            
        except Exception as e:
            logger.error(f"Critical error during scan: {e}", exc_info=True)
            results["errors"] += 1
        
        # Finalize results
        results["end_time"] = datetime.utcnow().isoformat()
        
        # Log summary
        logger.info("=" * 60)
        logger.info("SCAN COMPLETE - SUMMARY")
        logger.info("=" * 60)
        logger.info(f"  Total Cases Analyzed: {results['total_cases']}")
        logger.info(f"  Negative Sentiment: {results['negative_sentiment']}")
        logger.info(f"  Declining Sentiment: {results['declining_sentiment']}")
        logger.info(f"  Compliance Warnings: {results['compliance_warnings']}")
        logger.info(f"  Compliance Breaches: {results['compliance_breaches']}")
        logger.info(f"  Alerts Sent: {results['alerts_sent']}")
        logger.info(f"  Errors: {results['errors']}")
        logger.info("=" * 60)
        
        return results
    
    async def _fetch_active_cases(self) -> list[Case]:
        """
        Fetch all active cases that should be analyzed.
        
        Returns:
            list[Case]: List of active cases
        """
        logger.debug("Fetching active cases from DfM client...")
        
        # Get all active cases from DfM
        # In production, this would use the real API
        # In POC mode, this reads from our sample database
        cases = await self.dfm_client.get_active_cases()
        
        logger.debug(f"Retrieved {len(cases)} active cases")
        
        return cases
    
    async def _analyze_case(self, case: Case) -> Optional[CaseAnalysis]:
        """
        Run full analysis on a single case.
        
        Args:
            case: The case to analyze
            
        Returns:
            CaseAnalysis: Analysis results, or None if analysis failed
        """
        logger.debug(f"Running analysis on case {case.id}...")
        
        try:
            # Use sentiment service to analyze the case
            analysis = await self.sentiment_service.analyze_case(case)
            
            logger.debug(
                f"Case {case.id} analysis complete: "
                f"sentiment={analysis.overall_sentiment.label.value}, "
                f"score={analysis.overall_sentiment.score:.2f}"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze case {case.id}: {e}")
            return None
    
    async def _record_metrics(self, results: dict):
        """
        Record scan metrics to the database for reporting.
        
        Args:
            results: The scan results to record
        """
        logger.debug("Recording scan metrics to database...")
        
        try:
            # Store scan summary metrics
            await self.database.record_metric(
                metric_name="scan_total_cases",
                metric_value=float(results["total_cases"]),
                dimension_name="scan_id",
                dimension_value=results["scan_id"],
            )
            await self.database.record_metric(
                metric_name="scan_negative_sentiment",
                metric_value=float(results["negative_sentiment"]),
                dimension_name="scan_id",
                dimension_value=results["scan_id"],
            )
            await self.database.record_metric(
                metric_name="scan_compliance_warnings",
                metric_value=float(results["compliance_warnings"]),
                dimension_name="scan_id",
                dimension_value=results["scan_id"],
            )
            await self.database.record_metric(
                metric_name="scan_compliance_breaches",
                metric_value=float(results["compliance_breaches"]),
                dimension_name="scan_id",
                dimension_value=results["scan_id"],
            )
            await self.database.record_metric(
                metric_name="scan_alerts_sent",
                metric_value=float(results["alerts_sent"]),
                dimension_name="scan_id",
                dimension_value=results["scan_id"],
            )
            
            logger.debug("Metrics recorded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to record metrics: {e}")
    
    async def run_continuous(self, interval_minutes: int = 60):
        """
        Run continuous monitoring at specified intervals.
        
        Args:
            interval_minutes: Minutes between scans (default: 60)
        """
        logger.info(f"Starting continuous monitoring (interval: {interval_minutes} minutes)")
        
        self._is_running = True
        interval_seconds = interval_minutes * 60
        
        while self._is_running:
            try:
                # Run scan
                await self.run_scan()
                
                # Wait for next scan
                logger.info(f"Next scan in {interval_minutes} minutes...")
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                logger.info("Continuous monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)
        
        self._is_running = False
        logger.info("Continuous monitoring stopped")
    
    def stop(self):
        """
        Stop continuous monitoring.
        """
        logger.info("Stopping continuous monitoring...")
        self._is_running = False
    
    @property
    def scan_count(self) -> int:
        """Get the number of scans performed."""
        return self._scan_count
    
    @property
    def last_scan_time(self) -> Optional[datetime]:
        """Get the timestamp of the last scan."""
        return self._last_scan_time


# =============================================================================
# Factory Function
# =============================================================================

async def create_monitor(
    dfm_client: Optional[DfMClientBase] = None,
    sentiment_service: Optional[SentimentAnalysisService] = None,
    alert_service: Optional[AlertService] = None,
    database: Optional[DatabaseManager] = None,
    config: Optional[AppConfig] = None,
) -> CaseMonitor:
    """
    Create a CaseMonitor with all dependencies.
    
    Args:
        dfm_client: DfM client (uses default if not provided)
        sentiment_service: Sentiment service (uses default if not provided)
        alert_service: Alert service (uses default if not provided)
        database: Database manager (uses default if not provided)
        config: Application configuration (uses default if not provided)
        
    Returns:
        CaseMonitor: A configured monitor instance
    """
    logger.info("Creating CaseMonitor with dependencies...")
    
    # Get configuration
    if config is None:
        config = get_config()
    
    # Get or create dependencies
    if dfm_client is None:
        dfm_client = await get_dfm_client()
    
    if sentiment_service is None:
        sentiment_service = get_sentiment_service()
    
    if database is None:
        database = DatabaseManager(config.database.connection_string)
        await database.initialize()
    
    if alert_service is None:
        alert_service = await get_alert_service(database=database)
    
    # Create and return monitor
    return CaseMonitor(
        dfm_client=dfm_client,
        sentiment_service=sentiment_service,
        alert_service=alert_service,
        database=database,
        config=config,
    )
