"""Base class for plot components."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import logging

class PlotBase(QWidget):
    """Base class for plot components with common functionality."""
    
    def __init__(self, parent=None, figsize=(8, 6)):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui(figsize)
        
    def _setup_ui(self, figsize):
        """Setup the basic UI components."""
        layout = QVBoxLayout(self)
        self.canvas = FigureCanvas(Figure(figsize=figsize))
        layout.addWidget(self.canvas)
        self.figure = self.canvas.figure
        
    def clear_plot(self):
        """Clear the current plot."""
        self.figure.clear()
        self.canvas.draw()
        
    def save_plot(self, filepath):
        """Save the current plot to a file."""
        try:
            self.figure.savefig(filepath)
        except Exception as e:
            self.logger.error(f"Error saving plot: {str(e)}")
            
    def set_title(self, title):
        """Set the plot title."""
        try:
            self.figure.suptitle(title)
            self.canvas.draw()
        except Exception as e:
            self.logger.error(f"Error setting title: {str(e)}")
            
    def update_layout(self):
        """Update the plot layout."""
        try:
            self.figure.tight_layout()
            self.canvas.draw()
        except Exception as e:
            self.logger.error(f"Error updating layout: {str(e)}")
