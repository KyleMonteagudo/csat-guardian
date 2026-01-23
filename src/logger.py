# =============================================================================
# CSAT Guardian - Logging Module
# =============================================================================
# This module provides comprehensive logging capabilities for the application.
# 
# Key Features:
# - Structured JSON logging for Azure Monitor integration
# - Console logging for development
# - Verbose mode for detailed debugging
# - Contextual logging with case IDs and engineer IDs
# - Error tracking with full stack traces
#
# Usage:
#     from logger import get_logger
#     logger = get_logger(__name__)
#     logger.info("Processing case", extra={"case_id": "12345"})
# =============================================================================

import logging
import sys
import traceback
from datetime import datetime
from typing import Any, Optional
from pythonjsonlogger import jsonlogger


class CSATGuardianLogFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON log formatter for CSAT Guardian.
    
    This formatter outputs logs in JSON format, which is ideal for:
    - Azure Monitor / Application Insights ingestion
    - Log aggregation systems (ELK, Splunk)
    - Structured log queries
    
    Each log entry includes:
    - timestamp: ISO 8601 formatted timestamp
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - name: Logger name (usually the module name)
    - message: The log message
    - Additional context fields (case_id, engineer_id, etc.)
    """
    
    def add_fields(
        self, 
        log_record: dict[str, Any], 
        record: logging.LogRecord, 
        message_dict: dict[str, Any]
    ) -> None:
        """
        Add custom fields to each log record.
        
        This method is called for every log entry and allows us to
        add standard fields that should appear in all logs.
        
        Args:
            log_record: The dictionary that will be serialized to JSON
            record: The original LogRecord from Python's logging module
            message_dict: Additional fields passed via the 'extra' parameter
        """
        # Call parent to get base fields
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO 8601 format for easy parsing
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add log level as a separate field for filtering
        log_record['level'] = record.levelname
        
        # Add source information for debugging
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add application identifier for multi-service environments
        log_record['application'] = 'csat-guardian'
        
        # If there's an exception, add full traceback
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }


class VerboseFilter(logging.Filter):
    """
    Filter that controls verbose logging output.
    
    When verbose mode is disabled, this filter blocks DEBUG-level
    messages to reduce log noise. When enabled, all messages pass through.
    
    Attributes:
        verbose: Whether verbose logging is enabled
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize the verbose filter.
        
        Args:
            verbose: If True, allow all log levels. If False, block DEBUG.
        """
        super().__init__()
        self.verbose = verbose
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Determine if a log record should be output.
        
        Args:
            record: The log record to evaluate
            
        Returns:
            bool: True if the record should be logged, False to suppress it
        """
        # In verbose mode, allow everything
        if self.verbose:
            return True
        
        # In non-verbose mode, suppress DEBUG messages
        return record.levelno > logging.DEBUG


def setup_logging(
    level: str = "DEBUG",
    verbose: bool = True,
    json_output: bool = False
) -> None:
    """
    Configure the application logging system.
    
    This function should be called once at application startup to
    configure all logging handlers and formatters. It sets up:
    - Console output with colored/formatted messages
    - Optional JSON output for production environments
    - Verbose filtering based on configuration
    
    Args:
        level: The minimum log level to capture (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        verbose: Enable verbose (DEBUG) logging output
        json_output: Use JSON format instead of human-readable format
        
    Example:
        # In main.py:
        from logger import setup_logging
        from config import get_config
        
        config = get_config()
        setup_logging(
            level=config.log_level,
            verbose=config.features.verbose_logging,
            json_output=False  # True in production
        )
    """
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Set the base logging level
    root_logger.setLevel(getattr(logging, level.upper(), logging.DEBUG))
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Choose formatter based on output mode
    if json_output:
        # JSON format for production/Azure Monitor
        formatter = CSATGuardianLogFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    
    # Add verbose filter
    verbose_filter = VerboseFilter(verbose=verbose)
    console_handler.addFilter(verbose_filter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Log startup message
    root_logger.info(
        f"Logging initialized: level={level}, verbose={verbose}, json={json_output}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    This is the primary way to obtain a logger in the application.
    Each module should call this with __name__ to get a properly
    namespaced logger.
    
    Args:
        name: The logger name (typically __name__ of the calling module)
        
    Returns:
        logging.Logger: A configured logger instance
        
    Example:
        # In any module:
        from logger import get_logger
        
        logger = get_logger(__name__)
        
        def process_case(case_id: str):
            logger.info(f"Processing case", extra={"case_id": case_id})
            try:
                # ... do work ...
                logger.debug(f"Case processing complete", extra={"case_id": case_id})
            except Exception as e:
                logger.error(f"Failed to process case", extra={"case_id": case_id}, exc_info=True)
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for adding context to log messages.
    
    This class allows you to add contextual information (like case_id
    or engineer_id) to all log messages within a block of code.
    
    Example:
        with LogContext(case_id="12345", engineer_id="jsmith"):
            logger.info("Processing case")  # Will include case_id and engineer_id
            do_something()
            logger.info("Case processed")   # Will also include context
    """
    
    _context: dict[str, Any] = {}
    
    def __init__(self, **kwargs: Any):
        """
        Initialize the log context with key-value pairs.
        
        Args:
            **kwargs: Context fields to add to log messages
        """
        self.new_context = kwargs
        self.previous_context: dict[str, Any] = {}
    
    def __enter__(self) -> "LogContext":
        """Enter the context, saving previous values."""
        # Save previous values for restoration
        self.previous_context = {
            k: LogContext._context.get(k) 
            for k in self.new_context.keys()
        }
        # Update context with new values
        LogContext._context.update(self.new_context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context, restoring previous values."""
        # Restore previous values or remove if they didn't exist
        for key, value in self.previous_context.items():
            if value is None:
                LogContext._context.pop(key, None)
            else:
                LogContext._context[key] = value
    
    @classmethod
    def get_context(cls) -> dict[str, Any]:
        """
        Get the current log context.
        
        Returns:
            dict: The current context fields
        """
        return cls._context.copy()


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **extra: Any
) -> None:
    """
    Log a message with automatic context injection.
    
    This function combines the global LogContext with any extra
    fields provided, making it easy to include contextual information
    in log messages.
    
    Args:
        logger: The logger to use
        level: The log level (logging.INFO, logging.DEBUG, etc.)
        message: The log message
        **extra: Additional fields to include
        
    Example:
        log_with_context(
            logger, 
            logging.INFO, 
            "Case sentiment analyzed",
            sentiment_score=0.75,
            sentiment_label="positive"
        )
    """
    # Merge global context with provided extra fields
    context = LogContext.get_context()
    context.update(extra)
    
    # Log the message with merged context
    logger.log(level, message, extra=context)


# =============================================================================
# Convenience functions for common log operations
# =============================================================================

def log_case_event(
    logger: logging.Logger,
    case_id: str,
    event: str,
    level: int = logging.INFO,
    **extra: Any
) -> None:
    """
    Log a case-related event with standard fields.
    
    This convenience function ensures consistent logging format
    for all case-related operations.
    
    Args:
        logger: The logger to use
        case_id: The DfM case ID
        event: Description of the event
        level: Log level (default: INFO)
        **extra: Additional fields
        
    Example:
        log_case_event(
            logger, 
            "12345678", 
            "Sentiment analysis complete",
            sentiment_score=0.3,
            alert_triggered=True
        )
    """
    log_with_context(
        logger,
        level,
        f"[Case {case_id}] {event}",
        case_id=case_id,
        event_type="case_event",
        **extra
    )


def log_api_call(
    logger: logging.Logger,
    service: str,
    operation: str,
    success: bool,
    duration_ms: Optional[float] = None,
    **extra: Any
) -> None:
    """
    Log an API call with standard fields.
    
    This convenience function ensures consistent logging format
    for all external API calls (DfM, Azure OpenAI, Teams, etc.)
    
    Args:
        logger: The logger to use
        service: The service name (e.g., "dfm", "azure_openai", "teams")
        operation: The operation performed (e.g., "get_case", "analyze_sentiment")
        success: Whether the call succeeded
        duration_ms: Call duration in milliseconds
        **extra: Additional fields
        
    Example:
        start = time.time()
        try:
            result = await client.get_case(case_id)
            log_api_call(
                logger, "dfm", "get_case", True,
                duration_ms=(time.time() - start) * 1000,
                case_id=case_id
            )
        except Exception as e:
            log_api_call(
                logger, "dfm", "get_case", False,
                duration_ms=(time.time() - start) * 1000,
                case_id=case_id,
                error=str(e)
            )
    """
    level = logging.INFO if success else logging.ERROR
    status = "succeeded" if success else "failed"
    
    message = f"API call to {service}.{operation} {status}"
    if duration_ms is not None:
        message += f" ({duration_ms:.1f}ms)"
    
    log_with_context(
        logger,
        level,
        message,
        service=service,
        operation=operation,
        success=success,
        duration_ms=duration_ms,
        event_type="api_call",
        **extra
    )


def log_notification(
    logger: logging.Logger,
    notification_type: str,
    recipient: str,
    case_id: str,
    success: bool,
    **extra: Any
) -> None:
    """
    Log a notification event with standard fields.
    
    This convenience function ensures consistent logging format
    for all notification events (Teams messages, emails, etc.)
    
    Args:
        logger: The logger to use
        notification_type: Type of notification (e.g., "sentiment_alert", "7day_warning")
        recipient: The engineer receiving the notification
        case_id: The related case ID
        success: Whether the notification was sent successfully
        **extra: Additional fields
        
    Example:
        log_notification(
            logger,
            "sentiment_alert",
            "jsmith@microsoft.com",
            "12345678",
            True,
            channel="teams"
        )
    """
    level = logging.INFO if success else logging.ERROR
    status = "sent" if success else "failed"
    
    log_with_context(
        logger,
        level,
        f"Notification '{notification_type}' {status} to {recipient} for case {case_id}",
        notification_type=notification_type,
        recipient=recipient,
        case_id=case_id,
        success=success,
        event_type="notification",
        **extra
    )
