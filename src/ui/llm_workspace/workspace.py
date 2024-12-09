"""Main LLM workspace module."""
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
import logging
from ...utils.caching import cache_result
from .model_config import ModelConfigPanel
from .generation import TextGenerationPanel

logger = logging.getLogger(__name__)

class LLMWorkspace(QWidget):
    """LLM workspace widget for text generation and model management."""
    
    # Signals
    model_changed = pyqtSignal(str)
    generation_started = pyqtSignal()
    generation_completed = pyqtSignal(str)
    generation_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize LLM workspace.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        self.load_cached_config()
        
    def setup_ui(self):
        """Set up the workspace UI."""
        layout = QVBoxLayout(self)
        
        # Model configuration panel
        self.config_panel = ModelConfigPanel()
        layout.addWidget(self.config_panel)
        
        # Text generation panel
        self.generation_panel = TextGenerationPanel()
        layout.addWidget(self.generation_panel)
        
    def connect_signals(self):
        """Connect widget signals to slots."""
        # Model configuration signals
        self.config_panel.model_changed.connect(self.model_changed.emit)
        self.config_panel.config_changed.connect(self.cache_config)
        
        # Generation signals
        self.generation_panel.generation_started.connect(self.generation_started.emit)
        self.generation_panel.generation_completed.connect(self.generation_completed.emit)
        self.generation_panel.generation_error.connect(self.generation_error.emit)
        
    def get_model_config(self) -> Dict[str, Any]:
        """Get current model configuration.
        
        Returns:
            Dictionary of model configuration parameters
        """
        return self.config_panel.get_config()
        
    def set_model_config(self, config: Dict[str, Any]):
        """Set model configuration.
        
        Args:
            config: Dictionary of configuration parameters
        """
        self.config_panel.set_config(config)
        
    @cache_result()
    def cache_config(self, config: Dict[str, Any]):
        """Cache current model configuration.
        
        Args:
            config: Configuration to cache
        """
        logger.debug(f"Caching model config: {config}")
        
    def load_cached_config(self):
        """Load cached model configuration."""
        try:
            cached_config = cache_result.get_cache("model_config")
            if cached_config:
                self.set_model_config(cached_config)
        except Exception as e:
            logger.error(f"Error loading cached config: {str(e)}")
            
    def stop_generation(self):
        """Stop ongoing text generation."""
        self.generation_panel.stop_generation()
