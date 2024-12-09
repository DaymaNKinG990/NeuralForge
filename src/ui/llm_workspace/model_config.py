"""Model configuration panel for LLM workspace."""
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal
from ..styles.theme_manager import ThemeManager
from ..styles.adaptive_styles import AdaptiveStyles

class ModelConfigPanel(QWidget):
    """Panel for configuring LLM model parameters."""
    
    # Signals
    config_changed = pyqtSignal(dict)  # Emits when any config changes
    model_changed = pyqtSignal(str)  # Emits when model selection changes
    
    def __init__(self, parent=None):
        """Initialize model configuration panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.theme_manager = ThemeManager()
        self.adaptive_styles = AdaptiveStyles()
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the configuration panel UI."""
        layout = QVBoxLayout(self)
        
        # Model selection
        model_layout = QHBoxLayout()
        self.model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-2",
            "llama-2"
        ])
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)
        
        # Temperature control
        temp_layout = QHBoxLayout()
        self.temp_label = QLabel("Temperature:")
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(70)
        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(self.temp_slider)
        layout.addLayout(temp_layout)
        
        # Max tokens
        tokens_layout = QHBoxLayout()
        self.tokens_label = QLabel("Max Tokens:")
        self.tokens_spin = QSpinBox()
        self.tokens_spin.setRange(1, 4096)
        self.tokens_spin.setValue(2048)
        tokens_layout.addWidget(self.tokens_label)
        tokens_layout.addWidget(self.tokens_spin)
        layout.addLayout(tokens_layout)
        
        # Top P
        top_p_layout = QHBoxLayout()
        self.top_p_label = QLabel("Top P:")
        self.top_p_slider = QSlider(Qt.Orientation.Horizontal)
        self.top_p_slider.setRange(0, 100)
        self.top_p_slider.setValue(90)
        top_p_layout.addWidget(self.top_p_label)
        top_p_layout.addWidget(self.top_p_slider)
        layout.addLayout(top_p_layout)
        
        # Apply styles
        self.apply_styles()
        
    def connect_signals(self):
        """Connect widget signals to slots."""
        self.model_combo.currentTextChanged.connect(self.model_changed.emit)
        self.model_combo.currentTextChanged.connect(self.emit_config)
        self.temp_slider.valueChanged.connect(self.emit_config)
        self.tokens_spin.valueChanged.connect(self.emit_config)
        self.top_p_slider.valueChanged.connect(self.emit_config)
        
    def apply_styles(self):
        """Apply theme styles to widgets."""
        style = self.theme_manager.get_current_theme()
        self.setStyleSheet(style.get_widget_style("ModelConfig"))
        
        for label in [self.model_label, self.temp_label, 
                     self.tokens_label, self.top_p_label]:
            label.setStyleSheet(style.get_widget_style("Label"))
            
        self.model_combo.setStyleSheet(style.get_widget_style("ComboBox"))
        self.temp_slider.setStyleSheet(style.get_widget_style("Slider"))
        self.tokens_spin.setStyleSheet(style.get_widget_style("SpinBox"))
        self.top_p_slider.setStyleSheet(style.get_widget_style("Slider"))
        
    def get_config(self) -> Dict[str, Any]:
        """Get current model configuration.
        
        Returns:
            Dictionary of model configuration parameters
        """
        return {
            "model": self.model_combo.currentText(),
            "temperature": self.temp_slider.value() / 100,
            "max_tokens": self.tokens_spin.value(),
            "top_p": self.top_p_slider.value() / 100
        }
        
    def emit_config(self):
        """Emit current configuration."""
        self.config_changed.emit(self.get_config())
        
    def set_config(self, config: Dict[str, Any]):
        """Set model configuration.
        
        Args:
            config: Dictionary of configuration parameters
        """
        if "model" in config:
            index = self.model_combo.findText(config["model"])
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
                
        if "temperature" in config:
            self.temp_slider.setValue(int(config["temperature"] * 100))
            
        if "max_tokens" in config:
            self.tokens_spin.setValue(config["max_tokens"])
            
        if "top_p" in config:
            self.top_p_slider.setValue(int(config["top_p"] * 100))
