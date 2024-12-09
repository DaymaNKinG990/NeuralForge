"""Text generation panel for LLM workspace."""
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging
from ..styles.theme_manager import ThemeManager
from ..styles.adaptive_styles import AdaptiveStyles
from .threads import GenerationThread

logger = logging.getLogger(__name__)

class TextGenerationPanel(QWidget):
    """Panel for text generation interface."""
    
    # Signals
    generation_started = pyqtSignal()
    generation_completed = pyqtSignal(str)
    generation_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize text generation panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.theme_manager = ThemeManager()
        self.adaptive_styles = AdaptiveStyles()
        self.generation_thread: Optional[GenerationThread] = None
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the generation panel UI."""
        layout = QVBoxLayout(self)
        
        # Input area
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter your prompt here...")
        layout.addWidget(self.input_text)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.clear_btn = QPushButton("Clear")
        
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.clear_btn)
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Output area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Generated text will appear here...")
        layout.addWidget(self.output_text)
        
        # Apply styles
        self.apply_styles()
        
    def connect_signals(self):
        """Connect widget signals to slots."""
        self.generate_btn.clicked.connect(self.start_generation)
        self.stop_btn.clicked.connect(self.stop_generation)
        self.clear_btn.clicked.connect(self.clear_output)
        
    def apply_styles(self):
        """Apply theme styles to widgets."""
        style = self.theme_manager.get_current_theme()
        self.setStyleSheet(style.get_widget_style("TextGeneration"))
        
        for text_edit in [self.input_text, self.output_text]:
            text_edit.setStyleSheet(style.get_widget_style("TextEdit"))
            
        for button in [self.generate_btn, self.stop_btn, self.clear_btn]:
            button.setStyleSheet(style.get_widget_style("Button"))
            
        self.progress_bar.setStyleSheet(style.get_widget_style("ProgressBar"))
        
    def start_generation(self):
        """Start text generation process."""
        prompt = self.input_text.toPlainText().strip()
        if not prompt:
            logger.warning("No prompt provided for generation")
            return
            
        self.generation_started.emit()
        self.generate_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        
        self.generation_thread = GenerationThread(prompt, self)
        self.generation_thread.progress.connect(self.update_progress)
        self.generation_thread.finished.connect(self.generation_finished)
        self.generation_thread.error.connect(self.generation_error.emit)
        self.generation_thread.start()
        
    def stop_generation(self):
        """Stop ongoing text generation."""
        if self.generation_thread and self.generation_thread.isRunning():
            self.generation_thread.stop()
            self.generation_thread.wait()
            self.reset_ui()
            
    def clear_output(self):
        """Clear output text area."""
        self.output_text.clear()
        
    def update_progress(self, text: str, progress: int):
        """Update generation progress.
        
        Args:
            text: Generated text
            progress: Progress percentage
        """
        self.output_text.setPlainText(text)
        if progress >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(progress)
            
    def generation_finished(self, text: str):
        """Handle completed generation.
        
        Args:
            text: Final generated text
        """
        self.output_text.setPlainText(text)
        self.reset_ui()
        self.generation_completed.emit(text)
        
    def reset_ui(self):
        """Reset UI to initial state."""
        self.generate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.hide()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
