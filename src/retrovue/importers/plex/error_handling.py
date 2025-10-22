"""
Enhanced error handling and recovery system for robust content ingestion.

Provides error classification, retry logic, recovery strategies, and comprehensive logging.
"""

import logging
import time
import random
from typing import Dict, Any, List, Optional, Callable, Type
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import traceback

logger = logging.getLogger("retrovue.plex")


class ErrorType(Enum):
    """Classification of different error types."""
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    FILE_ACCESS_ERROR = "file_access_error"
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"
    PARSING_ERROR = "parsing_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"           # Minor issues that don't affect core functionality
    MEDIUM = "medium"     # Issues that may affect some operations
    HIGH = "high"         # Issues that significantly impact functionality
    CRITICAL = "critical" # Issues that prevent core operations


@dataclass
class ErrorContext:
    """Context information for an error."""
    operation: str
    item_id: Optional[str] = None
    item_title: Optional[str] = None
    server_id: Optional[int] = None
    library_id: Optional[int] = None
    file_path: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    context: ErrorContext
    timestamp: datetime
    retry_count: int = 0
    resolved: bool = False
    resolution_strategy: Optional[str] = None
    stack_trace: Optional[str] = None


class RetryStrategy:
    """Retry strategy configuration."""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, exponential_base: float = 2.0,
                 jitter: bool = True):
        """
        Initialize retry strategy.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a retry attempt.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        if attempt <= 0:
            return 0
        
        # Exponential backoff
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.jitter:
            jitter_factor = random.uniform(0.5, 1.5)
            delay *= jitter_factor
        
        return delay


class ErrorHandler:
    """Enhanced error handling and recovery system."""
    
    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """
        Initialize error handler.
        
        Args:
            logger_instance: Optional logger instance
        """
        self.logger = logger_instance or logger
        self.error_records: List[ErrorRecord] = []
        self.retry_strategies: Dict[ErrorType, RetryStrategy] = self._get_default_retry_strategies()
        self.recovery_strategies: Dict[ErrorType, Callable] = self._get_default_recovery_strategies()
    
    def _get_default_retry_strategies(self) -> Dict[ErrorType, RetryStrategy]:
        """Get default retry strategies for different error types."""
        return {
            ErrorType.NETWORK_ERROR: RetryStrategy(max_attempts=5, base_delay=2.0),
            ErrorType.TIMEOUT_ERROR: RetryStrategy(max_attempts=3, base_delay=5.0),
            ErrorType.FILE_ACCESS_ERROR: RetryStrategy(max_attempts=2, base_delay=1.0),
            ErrorType.DATABASE_ERROR: RetryStrategy(max_attempts=3, base_delay=1.0),
            ErrorType.AUTHENTICATION_ERROR: RetryStrategy(max_attempts=1, base_delay=0.0),
            ErrorType.VALIDATION_ERROR: RetryStrategy(max_attempts=1, base_delay=0.0),
            ErrorType.PARSING_ERROR: RetryStrategy(max_attempts=1, base_delay=0.0),
            ErrorType.UNKNOWN_ERROR: RetryStrategy(max_attempts=2, base_delay=2.0),
        }
    
    def _get_default_recovery_strategies(self) -> Dict[ErrorType, Callable]:
        """Get default recovery strategies for different error types."""
        return {
            ErrorType.NETWORK_ERROR: self._recover_network_error,
            ErrorType.AUTHENTICATION_ERROR: self._recover_auth_error,
            ErrorType.FILE_ACCESS_ERROR: self._recover_file_access_error,
            ErrorType.DATABASE_ERROR: self._recover_database_error,
            ErrorType.VALIDATION_ERROR: self._recover_validation_error,
            ErrorType.PARSING_ERROR: self._recover_parsing_error,
            ErrorType.TIMEOUT_ERROR: self._recover_timeout_error,
            ErrorType.UNKNOWN_ERROR: self._recover_unknown_error,
        }
    
    def classify_error(self, exception: Exception, context: ErrorContext) -> ErrorType:
        """
        Classify an exception into an error type.
        
        Args:
            exception: The exception that occurred
            context: Context information
            
        Returns:
            Classified error type
        """
        exception_type = type(exception).__name__
        exception_message = str(exception).lower()
        
        # Network-related errors
        if any(keyword in exception_message for keyword in ['connection', 'network', 'timeout', 'unreachable']):
            return ErrorType.NETWORK_ERROR
        
        # Authentication errors
        if any(keyword in exception_message for keyword in ['auth', 'token', 'unauthorized', 'forbidden']):
            return ErrorType.AUTHENTICATION_ERROR
        
        # File access errors
        if any(keyword in exception_message for keyword in ['file', 'path', 'permission', 'not found', 'access denied']):
            return ErrorType.FILE_ACCESS_ERROR
        
        # Database errors
        if any(keyword in exception_message for keyword in ['database', 'sql', 'constraint', 'integrity']):
            return ErrorType.DATABASE_ERROR
        
        # Validation errors
        if any(keyword in exception_message for keyword in ['validation', 'invalid', 'format', 'codec']):
            return ErrorType.VALIDATION_ERROR
        
        # Parsing errors
        if any(keyword in exception_message for keyword in ['parse', 'json', 'xml', 'decode']):
            return ErrorType.PARSING_ERROR
        
        # Timeout errors
        if 'timeout' in exception_message:
            return ErrorType.TIMEOUT_ERROR
        
        return ErrorType.UNKNOWN_ERROR
    
    def get_error_severity(self, error_type: ErrorType, context: ErrorContext) -> ErrorSeverity:
        """
        Determine error severity based on type and context.
        
        Args:
            error_type: Type of error
            context: Context information
            
        Returns:
            Error severity level
        """
        # Critical errors
        if error_type in [ErrorType.AUTHENTICATION_ERROR]:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if error_type in [ErrorType.DATABASE_ERROR, ErrorType.NETWORK_ERROR]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if error_type in [ErrorType.FILE_ACCESS_ERROR, ErrorType.TIMEOUT_ERROR]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        if error_type in [ErrorType.VALIDATION_ERROR, ErrorType.PARSING_ERROR]:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def handle_error(self, exception: Exception, context: ErrorContext, 
                    operation_func: Optional[Callable] = None) -> ErrorRecord:
        """
        Handle an error with classification, logging, and recovery.
        
        Args:
            exception: The exception that occurred
            context: Context information
            operation_func: Optional function to retry
            
        Returns:
            Error record with handling details
        """
        error_type = self.classify_error(exception, context)
        severity = self.get_error_severity(error_type, context)
        
        # Create error record
        error_record = ErrorRecord(
            error_type=error_type,
            severity=severity,
            message=str(exception),
            context=context,
            timestamp=datetime.now(),
            stack_trace=traceback.format_exc()
        )
        
        # Log error
        self._log_error(error_record)
        
        # Attempt recovery if possible
        if operation_func and self._should_retry(error_record):
            recovery_result = self._attempt_recovery(error_record, operation_func)
            if recovery_result:
                error_record.resolved = True
                error_record.resolution_strategy = "retry_success"
            else:
                error_record.retry_count += 1
        
        # Store error record
        self.error_records.append(error_record)
        
        return error_record
    
    def _should_retry(self, error_record: ErrorRecord) -> bool:
        """Determine if an error should be retried."""
        if error_record.resolved:
            return False
        
        retry_strategy = self.retry_strategies.get(error_record.error_type)
        if not retry_strategy:
            return False
        
        return error_record.retry_count < retry_strategy.max_attempts
    
    def _attempt_recovery(self, error_record: ErrorRecord, operation_func: Callable) -> bool:
        """
        Attempt to recover from an error.
        
        Args:
            error_record: Error record to recover from
            operation_func: Function to retry
            
        Returns:
            True if recovery was successful
        """
        try:
            # Get retry strategy
            retry_strategy = self.retry_strategies.get(error_record.error_type)
            if not retry_strategy:
                return False
            
            # Calculate delay
            delay = retry_strategy.get_delay(error_record.retry_count)
            if delay > 0:
                self.logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            
            # Attempt recovery strategy
            recovery_func = self.recovery_strategies.get(error_record.error_type)
            if recovery_func:
                recovery_func(error_record)
            
            # Retry operation
            result = operation_func()
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Recovery attempt failed: {e}")
            return False
    
    def _log_error(self, error_record: ErrorRecord):
        """Log error with appropriate level."""
        log_message = f"Error in {error_record.context.operation}: {error_record.message}"
        
        if error_record.context.item_title:
            log_message += f" (Item: {error_record.context.item_title})"
        
        if error_record.context.file_path:
            log_message += f" (File: {error_record.context.file_path})"
        
        # Log with appropriate level based on severity
        if error_record.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_record.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_record.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    # Recovery strategy implementations
    def _recover_network_error(self, error_record: ErrorRecord):
        """Recovery strategy for network errors."""
        self.logger.info("Attempting network error recovery...")
        # Could implement connection reset, proxy switching, etc.
    
    def _recover_auth_error(self, error_record: ErrorRecord):
        """Recovery strategy for authentication errors."""
        self.logger.info("Attempting authentication error recovery...")
        # Could implement token refresh, re-authentication, etc.
    
    def _recover_file_access_error(self, error_record: ErrorRecord):
        """Recovery strategy for file access errors."""
        self.logger.info("Attempting file access error recovery...")
        # Could implement path resolution, permission fixes, etc.
    
    def _recover_database_error(self, error_record: ErrorRecord):
        """Recovery strategy for database errors."""
        self.logger.info("Attempting database error recovery...")
        # Could implement connection reset, transaction rollback, etc.
    
    def _recover_validation_error(self, error_record: ErrorRecord):
        """Recovery strategy for validation errors."""
        self.logger.info("Attempting validation error recovery...")
        # Could implement data cleaning, format conversion, etc.
    
    def _recover_parsing_error(self, error_record: ErrorRecord):
        """Recovery strategy for parsing errors."""
        self.logger.info("Attempting parsing error recovery...")
        # Could implement format detection, encoding fixes, etc.
    
    def _recover_timeout_error(self, error_record: ErrorRecord):
        """Recovery strategy for timeout errors."""
        self.logger.info("Attempting timeout error recovery...")
        # Could implement timeout adjustment, connection pooling, etc.
    
    def _recover_unknown_error(self, error_record: ErrorRecord):
        """Recovery strategy for unknown errors."""
        self.logger.info("Attempting unknown error recovery...")
        # Generic recovery strategies
    
    def get_error_summary(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get summary of errors within a time window.
        
        Args:
            time_window: Optional time window to filter errors
            
        Returns:
            Error summary dictionary
        """
        if time_window:
            cutoff_time = datetime.now() - time_window
            recent_errors = [e for e in self.error_records if e.timestamp >= cutoff_time]
        else:
            recent_errors = self.error_records
        
        summary = {
            'total_errors': len(recent_errors),
            'by_type': {},
            'by_severity': {},
            'resolved_errors': len([e for e in recent_errors if e.resolved]),
            'unresolved_errors': len([e for e in recent_errors if not e.resolved]),
            'recent_errors': recent_errors[-10:] if recent_errors else []
        }
        
        # Count by type
        for error in recent_errors:
            error_type = error.error_type.value
            if error_type not in summary['by_type']:
                summary['by_type'][error_type] = 0
            summary['by_type'][error_type] += 1
        
        # Count by severity
        for error in recent_errors:
            severity = error.severity.value
            if severity not in summary['by_severity']:
                summary['by_severity'][severity] = 0
            summary['by_severity'][severity] += 1
        
        return summary
    
    def clear_old_errors(self, max_age: timedelta = timedelta(days=7)):
        """Clear old error records to prevent memory buildup."""
        cutoff_time = datetime.now() - max_age
        self.error_records = [e for e in self.error_records if e.timestamp >= cutoff_time]
        self.logger.info(f"Cleared old error records, {len(self.error_records)} remaining")

