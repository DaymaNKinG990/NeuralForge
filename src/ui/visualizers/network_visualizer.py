"""Network architecture visualization component."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor
import logging

class NetworkVisualizer(QWidget):
    """Widget for visualizing neural network architectures."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Create graphics view and scene
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        layout.addWidget(self.view)
        
    def visualize_network(self, model_type: str):
        """Visualize network architecture based on model type."""
        try:
            self.scene.clear()
            
            if model_type == "Convolutional Neural Network":
                self._draw_cnn()
            elif model_type == "Recurrent Neural Network":
                self._draw_rnn()
            elif model_type == "Transformer":
                self._draw_transformer()
            else:
                self._draw_custom()
                
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
        except Exception as e:
            self.logger.error(f"Error visualizing network: {str(e)}")
            
    def _draw_cnn(self):
        """Draw CNN architecture."""
        # Add CNN-specific visualization
        # Input layer -> Conv layers -> Pooling -> Dense layers -> Output
        pen = QPen(QColor("#2196F3"))
        brush = QBrush(QColor("#2196F3"))
        
        x = 0
        for i in range(5):  # Example: 5 layers
            y = -100 + i * 50
            self.scene.addRect(x, y, 30, 30, pen, brush)
            if i < 4:  # Add connections between layers
                self.scene.addLine(x + 30, y + 15, x + 70, y + 40, pen)
            x += 70
            
    def _draw_rnn(self):
        """Draw RNN architecture."""
        # Add RNN-specific visualization
        # Recurrent connections and time steps
        pen = QPen(QColor("#4CAF50"))
        brush = QBrush(QColor("#4CAF50"))
        
        x = 0
        for i in range(3):  # Example: 3 time steps
            y = 0
            self.scene.addEllipse(x, y, 30, 30, pen, brush)
            if i < 2:
                # Forward connection
                self.scene.addLine(x + 30, y + 15, x + 70, y + 15, pen)
                # Recurrent connection
                self.scene.addPath(f"M {x+15} {y-10} C {x+15} {y-40} {x+85} {y-40} {x+85} {y-10}", pen)
            x += 70
            
    def _draw_transformer(self):
        """Draw Transformer architecture."""
        # Add Transformer-specific visualization
        # Self-attention and feed-forward layers
        pen = QPen(QColor("#FF9800"))
        brush = QBrush(QColor("#FF9800"))
        
        # Encoder
        x = 0
        y = 0
        for i in range(2):  # Example: 2 encoder layers
            self.scene.addRect(x, y, 40, 60, pen, brush)
            y += 80
            
        # Decoder
        x = 100
        y = 0
        for i in range(2):  # Example: 2 decoder layers
            self.scene.addRect(x, y, 40, 60, pen, brush)
            y += 80
            
    def _draw_custom(self):
        """Draw placeholder for custom architecture."""
        pen = QPen(QColor("#9C27B0"))
        brush = QBrush(QColor("#9C27B0"))
        
        self.scene.addText("Custom Architecture\nVisualization will be updated\nbased on configuration")
        
    def reset(self):
        """Reset visualization."""
        try:
            self.scene.clear()
        except Exception as e:
            self.logger.error(f"Error resetting network visualization: {str(e)}")
