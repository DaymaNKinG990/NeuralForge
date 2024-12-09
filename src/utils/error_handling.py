"""Error handling utilities."""
import logging
import traceback
from typing import Optional, Any, Dict, List
from enum import Enum
import sys
import torch

class ErrorLevel(Enum):
    """Error severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class MLError(Exception):
    """Base class for ML-related errors."""
    
    def __init__(self, message: str,
                 error_code: str,
                 level: ErrorLevel = ErrorLevel.ERROR,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.level = level
        self.details = details or {}
        
    def __str__(self) -> str:
        return f"{self.level.value} [{self.error_code}]: {super().__str__()}"

class DataError(MLError):
    """Errors related to data handling."""
    pass

class ModelError(MLError):
    """Errors related to model operations."""
    pass

class ValidationError(MLError):
    """Errors related to validation."""
    pass

class ErrorHandler:
    """Central error handling system."""
    
    def __init__(self):
        """Initialize error handler."""
        self.logger = logging.getLogger(__name__)
        self.error_history: List[Dict[str, Any]] = []
        
    def handle_error(self, error: Exception,
                    context: Optional[Dict[str, Any]] = None) -> None:
        """Handle and log an error."""
        error_info = self._create_error_info(error, context)
        self._log_error(error_info)
        self._store_error(error_info)
        self._handle_critical_error(error_info)
        
    def _create_error_info(self, error: Exception,
                          context: Optional[Dict[str, Any]] = None
                          ) -> Dict[str, Any]:
        """Create detailed error information."""
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'timestamp': self._get_timestamp()
        }
        
        if isinstance(error, MLError):
            error_info.update({
                'error_code': error.error_code,
                'level': error.level.value,
                'details': error.details
            })
            
        return error_info
        
    def _log_error(self, error_info: Dict[str, Any]) -> None:
        """Log error with appropriate severity."""
        level = error_info.get('level', ErrorLevel.ERROR.value)
        message = (
            f"Error: {error_info['type']}\n"
            f"Message: {error_info['message']}\n"
            f"Context: {error_info['context']}"
        )
        
        if level == ErrorLevel.INFO.value:
            self.logger.info(message)
        elif level == ErrorLevel.WARNING.value:
            self.logger.warning(message)
        elif level == ErrorLevel.ERROR.value:
            self.logger.error(message)
        else:  # CRITICAL
            self.logger.critical(message)
            
    def _store_error(self, error_info: Dict[str, Any]) -> None:
        """Store error in history."""
        self.error_history.append(error_info)
        if len(self.error_history) > 1000:  # Limit history size
            self.error_history.pop(0)
            
    def _handle_critical_error(self,
                             error_info: Dict[str, Any]) -> None:
        """Handle critical errors."""
        if error_info.get('level') == ErrorLevel.CRITICAL.value:
            # Perform emergency cleanup
            self._cleanup()
            # Optionally exit
            sys.exit(1)
            
    def _cleanup(self) -> None:
        """Perform cleanup operations."""
        try:
            # Release GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            # Close file handles
            for handler in self.logger.handlers:
                handler.close()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

class ErrorMonitor:
    """Monitor and analyze errors."""
    
    def __init__(self, error_handler: ErrorHandler):
        """Initialize error monitor."""
        self.error_handler = error_handler
        self.error_counts: Dict[str, int] = {}
        self.error_patterns: Dict[str, List[Dict[str, Any]]] = {}
        
    def analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns."""
        self._update_error_counts()
        self._identify_patterns()
        return self._generate_report()
        
    def _update_error_counts(self) -> None:
        """Update error occurrence counts."""
        self.error_counts = {}
        for error in self.error_handler.error_history:
            error_type = error['type']
            self.error_counts[error_type] = (
                self.error_counts.get(error_type, 0) + 1
            )
            
    def _identify_patterns(self) -> None:
        """Identify common error patterns."""
        self.error_patterns = {}
        for error in self.error_handler.error_history:
            error_type = error['type']
            if error_type not in self.error_patterns:
                self.error_patterns[error_type] = []
            self.error_patterns[error_type].append(error)
            
    def _generate_report(self) -> Dict[str, Any]:
        """Generate error analysis report."""
        return {
            'total_errors': len(self.error_handler.error_history),
            'error_counts': self.error_counts,
            'most_common_error': max(self.error_counts.items(),
                                   key=lambda x: x[1])[0],
            'error_patterns': {
                error_type: len(patterns)
                for error_type, patterns in self.error_patterns.items()
            }
        }

# Example usage:
def example_usage():
    # Initialize error handling system
    error_handler = ErrorHandler()
    error_monitor = ErrorMonitor(error_handler)
    
    try:
        # Simulate data error
        raise DataError(
            message="Invalid data format",
            error_code="DATA_001",
            level=ErrorLevel.ERROR,
            details={'format': 'CSV', 'issue': 'Missing columns'}
        )
    except Exception as e:
        error_handler.handle_error(e, {'operation': 'data_loading'})
        
    try:
        # Simulate model error
        raise ModelError(
            message="GPU out of memory",
            error_code="MODEL_001",
            level=ErrorLevel.CRITICAL,
            details={'available_memory': '4GB', 'required_memory': '6GB'}
        )
    except Exception as e:
        error_handler.handle_error(e, {'operation': 'model_training'})
        
    # Analyze errors
    analysis = error_monitor.analyze_errors()
    print("Error Analysis:", analysis)
