"""Error handling utilities."""
import logging
import traceback
from typing import Optional, Any, Dict, List
from enum import Enum
import sys
import torch
from datetime import datetime
from collections import defaultdict
from typing import Union

class ErrorLevel(Enum):
    """Error severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class MLError(Exception):
    """Base class for ML-related errors."""
    
    def __init__(self, message: str, error_code: str, level: ErrorLevel = ErrorLevel.ERROR, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.level = level
        self.details = details or {}
        super().__init__(f"{level.value} [{error_code}]: {message}")

class DataError(MLError):
    """Exception raised for data-related errors."""
    def __init__(self, message: str, error_code: str = "DATA_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code=error_code, level=ErrorLevel.ERROR, details=details)

class ModelError(MLError):
    """Errors related to model operations."""
    def __init__(self, message: str,
                 error_code: str = "MODEL_ERROR",
                 level: ErrorLevel = ErrorLevel.ERROR,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, level, details)

class ValidationError(MLError):
    """Errors related to validation."""
    def __init__(self, message: str,
                 error_code: str = "VALIDATION_ERROR",
                 level: ErrorLevel = ErrorLevel.WARNING,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, level, details)

class ErrorHandler:
    """Central error handling system."""
    
    def __init__(self):
        """Initialize error handler."""
        self.logger = logging.getLogger(__name__)
        self.monitors = []
        
    def register_monitor(self, monitor):
        """Register an error monitor."""
        self.monitors.append(monitor)
        
    def handle_error(self, error: MLError):
        """Handle an error occurrence."""
        error_info = {
            'timestamp': datetime.now(),
            'message': error.message,
            'error_code': error.error_code,
            'level': error.level,
            'details': error.details,
            'traceback': traceback.format_exc(),
            'type': error.__class__.__name__
        }
        
        # Log the error
        self.logger.error(str(error), exc_info=True)
        
        # Notify monitors
        for monitor in self.monitors:
            monitor.log_error(error_info)
            
        # Re-raise the error for proper exception handling
        raise error

class ErrorMonitor:
    """Monitor and analyze errors."""
    
    def __init__(self, error_handler: ErrorHandler):
        """Initialize error monitor."""
        self.error_handler = error_handler
        self.error_history = []
        self.error_counts = defaultdict(int)
        self.error_patterns = {}
        error_handler.register_monitor(self)
        
    def log_error(self, error_info: Dict[str, Any]):
        """Log an error occurrence."""
        self.error_history.append(error_info)
        self._update_error_counts()
        self._identify_patterns()
        
    def _update_error_counts(self):
        """Update error occurrence counts."""
        self.error_counts.clear()
        for error in self.error_history:
            error_type = error['type']
            self.error_counts[error_type.lower()] += 1
            self.error_counts['total_errors'] += 1
            
    def _identify_patterns(self):
        """Identify common error patterns."""
        if not self.error_history:
            return
            
        # Group errors by type
        error_groups = defaultdict(list)
        for error in self.error_history:
            error_groups[error['error_code']].append(error)
            
        # Find patterns in each group
        for code, errors in error_groups.items():
            if len(errors) >= 2:  # Pattern requires at least 2 occurrences
                self.error_patterns[code] = {
                    'count': len(errors),
                    'frequency': len(errors) / len(self.error_history),
                    'last_occurrence': max(e['timestamp'] for e in errors)
                }
                
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        stats = {
            'total_errors': self.error_counts['total_errors'],
            'data_errors': self.error_counts['dataerror'],
            'model_errors': self.error_counts['modelerror'],
            'validation_errors': self.error_counts['validationerror'],
            'patterns': self.error_patterns
        }
        return stats

# Example usage:
def example_usage():
    # Initialize error handling system
    error_handler = ErrorHandler()
    error_monitor = ErrorMonitor(error_handler)
    
    try:
        # Simulate data error
        raise DataError(
            message="Invalid data format",
            error_code="DATA_001"
        )
    except Exception as e:
        error_handler.handle_error(e)
        
    try:
        # Simulate model error
        raise ModelError(
            message="GPU out of memory",
            error_code="MODEL_001",
            level=ErrorLevel.CRITICAL,
            details={'available_memory': '4GB', 'required_memory': '6GB'}
        )
    except Exception as e:
        error_handler.handle_error(e)
        
    # Analyze errors
    analysis = error_monitor.get_error_stats()
    print("Error Analysis:", analysis)
