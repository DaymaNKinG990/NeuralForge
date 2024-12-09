"""Python code interpreter."""
import sys
import traceback
from io import StringIO
from typing import Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal
import logging

logger = logging.getLogger(__name__)

class PythonInterpreter(QObject):
    """Python code interpreter."""
    
    output_written = pyqtSignal(str)  # Emits standard output
    error_written = pyqtSignal(str)  # Emits error output
    
    def __init__(self):
        """Initialize interpreter."""
        super().__init__()
        self.locals: Dict[str, Any] = {}
        self.stdout = StringIO()
        self.stderr = StringIO()
        
    def execute(self, code: str):
        """Execute Python code.
        
        Args:
            code: Code to execute
        """
        # Save original stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        try:
            # Redirect output
            sys.stdout = self.stdout
            sys.stderr = self.stderr
            
            # Execute code
            exec(code, self.locals)
            
            # Get output
            output = self.stdout.getvalue()
            if output:
                self.output_written.emit(output)
                
            error = self.stderr.getvalue()
            if error:
                self.error_written.emit(error)
                
        except Exception as e:
            # Handle execution error
            error = traceback.format_exc()
            self.error_written.emit(error)
            logger.error(f"Code execution error: {error}")
            
        finally:
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # Clear buffers
            self.stdout = StringIO()
            self.stderr = StringIO()
            
    def interrupt(self):
        """Interrupt execution."""
        # TODO: Implement execution interruption
        pass
        
    def get_state(self) -> dict:
        """Get interpreter state.
        
        Returns:
            State dictionary
        """
        return {
            'locals': {
                k: str(v) for k, v in self.locals.items()
                if not k.startswith('_')
            }
        }
        
    def set_state(self, state: dict):
        """Set interpreter state.
        
        Args:
            state: State dictionary
        """
        if 'locals' in state:
            # Only restore simple types
            for k, v in state['locals'].items():
                try:
                    self.locals[k] = eval(v)
                except:
                    pass
