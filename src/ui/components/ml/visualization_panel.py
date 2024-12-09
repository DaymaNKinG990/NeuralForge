"""Visualization component for ML workspace."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import pyqtSignal
from ...visualizers.network_visualizer import NetworkVisualizer
from ...visualizers.training_visualizer import TrainingVisualizer
import logging

class VisualizationPanel(QWidget):
    """Widget for ML visualizations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Create tab widget for visualizations
        self.tab_widget = QTabWidget()
        
        # Network architecture visualization
        self.network_viz = NetworkVisualizer()
        self.tab_widget.addTab(self.network_viz, "Network Architecture")
        
        # Training progress visualization
        self.training_viz = TrainingVisualizer()
        self.tab_widget.addTab(self.training_viz, "Training Progress")
        
        layout.addWidget(self.tab_widget)
        
    def update_network(self, model_type: str):
        """Update network architecture visualization."""
        try:
            self.network_viz.visualize_network(model_type)
        except Exception as e:
            self.logger.error(f"Error updating network visualization: {str(e)}")
            
    def update_training(self, metrics: dict):
        """Update training progress visualization."""
        try:
            self.training_viz.update_metrics(metrics)
        except Exception as e:
            self.logger.error(f"Error updating training visualization: {str(e)}")
            
    def reset(self):
        """Reset visualizations."""
        try:
            self.network_viz.reset()
            self.training_viz.reset()
        except Exception as e:
            self.logger.error(f"Error resetting visualizations: {str(e)}")
