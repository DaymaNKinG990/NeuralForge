"""Experiment tracking component for ML workspace."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt6.QtCore import pyqtSignal
import json
import logging
from datetime import datetime

class ExperimentTracker(QWidget):
    """Component for tracking experiment metrics and parameters."""
    
    metrics_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize ExperimentTracker."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_state()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Text area for displaying metrics
        self.metrics_display = QTextEdit()
        self.metrics_display.setReadOnly(True)
        layout.addWidget(self.metrics_display)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.metrics_history = []
        self.current_experiment = None
        
    def start_experiment(self, config: dict):
        """Start a new experiment with given configuration."""
        try:
            self.current_experiment = {
                'start_time': datetime.now().isoformat(),
                'config': config,
                'metrics': []
            }
            self.metrics_history = []
            self._update_display()
        except Exception as e:
            self.logger.error(f"Error starting experiment: {str(e)}", exc_info=True)
            
    def log_metrics(self, metrics):
        """Log metrics for current experiment."""
        try:
            if self.current_experiment is None:
                self.start_experiment({})
                
            # Convert metrics to dict if it's a single value
            if not isinstance(metrics, dict):
                metrics = {'value': metrics}
                
            # Add timestamp
            metrics['timestamp'] = datetime.now().isoformat()
            
            # Store metrics
            self.metrics_history.append(metrics)
            self.current_experiment['metrics'].append(metrics)
            
            # Update display
            self._update_display()
            
            # Emit signal
            self.metrics_updated.emit(metrics)
            
        except Exception as e:
            self.logger.error(f"Error logging metrics: {str(e)}", exc_info=True)
            
    def _update_display(self):
        """Update the metrics display."""
        try:
            if not self.metrics_history:
                return
                
            # Format latest metrics
            latest = self.metrics_history[-1]
            display_text = "Latest Metrics:\n"
            display_text += json.dumps(latest, indent=2)
            
            # Add summary of all metrics
            display_text += "\n\nMetrics History Summary:\n"
            for i, m in enumerate(self.metrics_history, 1):
                display_text += f"Step {i}: {m.get('value', m)}\n"
                
            self.metrics_display.setText(display_text)
            
        except Exception as e:
            self.logger.error(f"Error updating display: {str(e)}", exc_info=True)
            
    def get_metrics_history(self):
        """Get the full metrics history."""
        return self.metrics_history
        
    def reset(self):
        """Reset the tracker state."""
        self._initialize_state()
        self.metrics_display.clear()
