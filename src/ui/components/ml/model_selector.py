"""Model selection component for ML workspace."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import pyqtSignal
import logging

class ModelSelector(QWidget):
    """Widget for selecting ML models."""
    
    model_changed = pyqtSignal(str)  # Emitted when model selection changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Model selection
        model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "Convolutional Neural Network",
            "Recurrent Neural Network",
            "Transformer",
            "Custom Architecture"
        ])
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        
        layout.addWidget(model_label)
        layout.addWidget(self.model_combo)
        
    def _on_model_changed(self, model: str):
        """Handle model selection change."""
        try:
            self.model_changed.emit(model)
        except Exception as e:
            self.logger.error(f"Error in model change: {str(e)}")
            
    def get_current_model(self) -> str:
        """Get currently selected model."""
        return self.model_combo.currentText()
        
    def set_model(self, model: str):
        """Set current model selection."""
        index = self.model_combo.findText(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
