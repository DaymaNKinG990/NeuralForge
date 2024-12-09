from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QTextEdit, QSpinBox, QProgressBar,
    QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
import logging
from ..utils.caching import cache_manager
from .styles.theme_manager import ThemeManager
from .styles.adaptive_styles import AdaptiveStyles

logger = logging.getLogger(__name__)

class LLMWorkspace(QWidget):
    """LLM workspace widget for text generation and model management.
    
    Provides model selection, parameter configuration, and text generation interface.
    
    Signals:
        model_changed: Emitted when model selection changes
        generation_started: Emitted when text generation starts
        generation_stopped: Emitted when text generation stops
        generation_complete: Emitted when generation is complete with result
    """
    
    model_changed = pyqtSignal(str)
    generation_started = pyqtSignal()
    generation_stopped = pyqtSignal()
    generation_complete = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the LLM workspace.
        
        Args:
            parent: Parent widget
        """
        try:
            super().__init__(parent)
            
            # Initialize managers and state
            self._theme_manager = ThemeManager()
            self.cache = cache_manager
            self._generation_active = False
            self._model_loaded = False
            self._current_model = None
            self._generation_thread = None
            
            # Initialize UI and connections
            self._init_ui()
            self._apply_styles()
            self._connect_signals()
            
            logger.debug("LLMWorkspace initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLMWorkspace: {str(e)}", exc_info=True)
            raise

    def cleanup(self) -> None:
        """Clean up resources before destruction."""
        try:
            # Stop any active generation
            if self._generation_active:
                self._on_stop()
                
            # Wait for thread to finish
            if self._generation_thread and self._generation_thread.isRunning():
                self._generation_thread.stop()
                self._generation_thread.wait()
                
            # Clear caches if a model was loaded
            if hasattr(self, 'cache') and self._current_model:
                try:
                    self.cache.clear_model_cache(self._current_model)
                except AttributeError:
                    logger.warning("Cache manager does not support model cache clearing")
                
            # Reset state
            self._generation_active = False
            self._model_loaded = False
            self._current_model = None
            self._generation_thread = None
            
            logger.debug("LLMWorkspace cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during LLMWorkspace cleanup: {str(e)}", exc_info=True)

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        try:
            layout = QVBoxLayout()
            self.setLayout(layout)
            
            # Model selection
            model_layout = QHBoxLayout()
            self.model_selector = QComboBox()
            self.model_selector.addItems([
                "GPT-2",
                "BLOOM",
                "LLaMA-7B",
                "CodeLLaMA"
            ])
            model_layout.addWidget(QLabel("Model:"))
            model_layout.addWidget(self.model_selector)
            
            # Generation parameters
            param_layout = QVBoxLayout()
            
            # Temperature slider
            temp_layout = QHBoxLayout()
            self.temperature = QSlider(Qt.Orientation.Horizontal)
            self.temperature.setRange(0, 100)  # 0.0 to 1.0
            self.temperature.setValue(70)  # Default 0.7
            self.temp_label = QLabel("Temperature: 0.7")
            temp_layout.addWidget(self.temp_label)
            temp_layout.addWidget(self.temperature)
            
            # Max length
            length_layout = QHBoxLayout()
            self.max_length = QSpinBox()
            self.max_length.setRange(1, 2048)
            self.max_length.setValue(256)
            length_layout.addWidget(QLabel("Max Length:"))
            length_layout.addWidget(self.max_length)
            
            param_layout.addLayout(temp_layout)
            param_layout.addLayout(length_layout)
            
            # Input/Output text areas
            self.input_text = QTextEdit()
            self.input_text.setPlaceholderText("Enter prompt here...")
            self.output_text = QTextEdit()
            self.output_text.setReadOnly(True)
            self.output_text.setPlaceholderText("Generated text will appear here...")
            
            # Progress bar
            self.progress = QProgressBar()
            self.progress.setVisible(False)
            
            # Control buttons
            button_layout = QHBoxLayout()
            self.generate_btn = QPushButton("Generate")
            self.stop_btn = QPushButton("Stop")
            self.stop_btn.setEnabled(False)
            self.clear_btn = QPushButton("Clear")
            button_layout.addWidget(self.generate_btn)
            button_layout.addWidget(self.stop_btn)
            button_layout.addWidget(self.clear_btn)
            
            # Add all components to main layout
            layout.addLayout(model_layout)
            layout.addLayout(param_layout)
            layout.addWidget(QLabel("Input:"))
            layout.addWidget(self.input_text)
            layout.addWidget(QLabel("Output:"))
            layout.addWidget(self.output_text)
            layout.addWidget(self.progress)
            layout.addLayout(button_layout)
            
        except Exception as e:
            logger.error(f"Error initializing UI: {e}", exc_info=True)
            raise

    def _apply_styles(self) -> None:
        """Apply theme-based styles to components"""
        try:
            # Get styles from adaptive styles
            base_style = AdaptiveStyles.get_base_style(self._theme_manager)
            text_style = AdaptiveStyles.get_text_style(self._theme_manager)
            button_style = AdaptiveStyles.get_button_style(self._theme_manager)
            
            # Apply styles
            self.setStyleSheet(base_style)
            self.input_text.setStyleSheet(text_style)
            self.output_text.setStyleSheet(text_style)
            self.generate_btn.setStyleSheet(button_style)
            self.stop_btn.setStyleSheet(button_style)
            self.clear_btn.setStyleSheet(button_style)
            
        except Exception as e:
            logger.error(f"Error applying styles: {e}", exc_info=True)

    def _connect_signals(self) -> None:
        """Connect widget signals to slots"""
        try:
            self.model_selector.currentTextChanged.connect(self._on_model_changed)
            self.generate_btn.clicked.connect(self._on_generate)
            self.stop_btn.clicked.connect(self._on_stop)
            self.clear_btn.clicked.connect(self._on_clear)
            self.temperature.valueChanged.connect(self._update_temp_label)
            
        except Exception as e:
            logger.error(f"Error connecting signals: {e}", exc_info=True)

    def _on_model_changed(self, model: str) -> None:
        """Handle model selection changes.
        
        Args:
            model: Name of the selected model
        """
        try:
            if self._generation_active:
                logger.warning("Cannot change model while generation is active")
                return
                
            # Unload previous model
            if self._current_model:
                self.cache.clear_model_cache(self._current_model)
                
            # Load new model configuration
            config = self._get_model_config(model)
            if not config:
                logger.error(f"Failed to load configuration for model: {model}")
                return
                
            # Update UI with model-specific settings
            self.max_length.setRange(1, config.get('max_length', 2048))
            self.max_length.setValue(config.get('default_length', 256))
            self.temperature.setValue(int(config.get('default_temp', 0.7) * 100))
            
            # Update state
            self._current_model = model
            self._model_loaded = True
            
            # Emit signal
            self.model_changed.emit(model)
            logger.debug(f"Model changed to: {model}")
            
        except Exception as e:
            logger.error(f"Error changing model: {str(e)}", exc_info=True)
            self._model_loaded = False

    def _on_generate(self) -> None:
        """Handle generate button click."""
        try:
            if not self._model_loaded:
                logger.error("No model loaded")
                return
                
            if self._generation_active:
                logger.warning("Generation already in progress")
                return
                
            prompt = self.input_text.toPlainText().strip()
            if not prompt:
                logger.warning("Empty prompt")
                return
                
            # Update state
            self._generation_active = True
            self._stop_requested = False
            
            # Update UI
            self.progress.setVisible(True)
            self.progress.setValue(0)
            self.generate_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            # Start generation in thread
            self._start_generation_thread(prompt)
            
            # Emit signal
            self.generation_started.emit()
            logger.debug("Generation started")
            
        except Exception as e:
            logger.error(f"Error starting generation: {str(e)}", exc_info=True)
            self._reset_generation_state()

    def _on_stop(self) -> None:
        """Handle stop button click."""
        try:
            if self._generation_thread and self._generation_thread.isRunning():
                self._generation_thread.stop()
                self._generation_active = False
                self.generation_stopped.emit()
                self._reset_generation_state()
                
        except Exception as e:
            logger.error(f"Error stopping generation: {str(e)}", exc_info=True)

    def _on_clear(self) -> None:
        """Handle clear button click."""
        try:
            self.input_text.clear()
            self.output_text.clear()
            
        except Exception as e:
            logger.error(f"Error clearing text: {e}", exc_info=True)

    def _reset_generation_state(self) -> None:
        """Reset generation state and UI."""
        try:
            # Reset state
            self._generation_active = False
            self._stop_requested = False
            
            # Reset UI
            self.progress.setVisible(False)
            self.progress.setValue(0)
            self.generate_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
            logger.debug("Generation state reset")
            
        except Exception as e:
            logger.error(f"Error resetting generation state: {str(e)}", exc_info=True)

    def _update_temp_label(self, value: int) -> None:
        """Update temperature label when slider changes.
        
        Args:
            value: New slider value (0-100)
        """
        try:
            temp = value / 100.0
            self.temp_label.setText(f"Temperature: {temp:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating temperature label: {e}", exc_info=True)

    def _get_model_config(self, model: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific model.
        
        Args:
            model: Name of the model
            
        Returns:
            Dictionary with model configuration or None if not found
        """
        configs = {
            "GPT-2": {"max_length": 1024, "default_length": 256, "default_temp": 0.7},
            "BLOOM": {"max_length": 2048, "default_length": 256, "default_temp": 0.8},
            "LLaMA-7B": {"max_length": 2048, "default_length": 256, "default_temp": 0.7},
            "CodeLLaMA": {"max_length": 2048, "default_length": 256, "default_temp": 0.6}
        }
        return configs.get(model)

    def update_generation(self, text: str, progress: int = -1) -> None:
        """Update the output text and progress bar.
        
        Args:
            text: Generated text to append
            progress: Progress percentage (-1 for completion)
        """
        try:
            self.output_text.setPlainText(text)
            
            if progress >= 0:
                self.progress.setValue(progress)
            else:
                self._reset_generation_state()
                self.generation_complete.emit(text)
                
        except Exception as e:
            logger.error(f"Error updating generation: {e}", exc_info=True)

    def _start_generation_thread(self, prompt: str) -> None:
        """Start generation in a separate thread."""
        try:
            if self._generation_thread and self._generation_thread.isRunning():
                self._generation_thread.stop()
                self._generation_thread.wait()
            
            self._generation_thread = GenerationThread(prompt, self)
            
            # Connect thread signals
            self._generation_thread.progress.connect(self.update_generation)
            self._generation_thread.finished.connect(self._on_generation_complete)
            self._generation_thread.error.connect(self._on_generation_error)
            
            self._generation_thread.start()
            self._generation_active = True
            self.generation_started.emit()
            
        except Exception as e:
            logger.error(f"Error starting generation thread: {str(e)}", exc_info=True)

    def _on_generation_complete(self, text: str) -> None:
        """Handle generation completion."""
        self._generation_active = False
        self.generation_complete.emit(text)
        self._reset_generation_state()
        
    def _on_generation_error(self, error_msg: str) -> None:
        """Handle generation error."""
        self._generation_active = False
        self.generation_stopped.emit()
        self._reset_generation_state()
        self.output_text.append(f"Error: {error_msg}")
        
    def closeEvent(self, event) -> None:
        """Handle widget close event"""
        try:
            if self._generation_active:
                self._on_stop()
            super().closeEvent(event)
            
        except Exception as e:
            logger.error(f"Error in close event: {e}", exc_info=True)
            event.accept()

class GenerationThread(QThread):
    # Define signals for thread communication
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, prompt: str, workspace: LLMWorkspace) -> None:
        super().__init__()
        self.prompt = prompt
        self._stop_requested = False
        
    def stop(self):
        self._stop_requested = True
        
    def run(self) -> None:
        try:
            # Simulate generation process
            for i in range(100):
                if self._stop_requested:
                    break
                self.progress.emit(f"Generating... {i+1}%\n", i+1)
                self.msleep(50)  # Increased sleep time for stability
            self.finished.emit("Generation complete!")
            
        except Exception as e:
            error_msg = f"Error in generation thread: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)
