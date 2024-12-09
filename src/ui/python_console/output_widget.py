"""Console output widget."""
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QTextCharFormat, QColor,
    QFont, QTextCursor
)

class ConsoleOutputWidget(QPlainTextEdit):
    """Widget for console output."""
    
    def __init__(self, parent=None):
        """Initialize output widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setup_widget()
        self.setup_formats()
        
    def setup_widget(self):
        """Set up the output widget."""
        # Set font
        font = QFont("Courier New")
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Make read-only
        self.setReadOnly(True)
        
        # Set background color
        self.setStyleSheet("background-color: #1E1E1E; color: #FFFFFF;")
        
    def setup_formats(self):
        """Set up text formats."""
        # Input format (white)
        self.input_format = QTextCharFormat()
        self.input_format.setForeground(QColor("#FFFFFF"))
        
        # Output format (light gray)
        self.output_format = QTextCharFormat()
        self.output_format.setForeground(QColor("#CCCCCC"))
        
        # Error format (red)
        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor("#FF6B68"))
        
    def write_input(self, text: str):
        """Write input text.
        
        Args:
            text: Input text
        """
        self.write_text(f">>> {text}\n", self.input_format)
        
    def write_output(self, text: str):
        """Write output text.
        
        Args:
            text: Output text
        """
        if text.strip():
            self.write_text(f"{text}\n", self.output_format)
            
    def write_error(self, text: str):
        """Write error text.
        
        Args:
            text: Error text
        """
        self.write_text(f"Error: {text}\n", self.error_format)
        
    def write_text(self, text: str, format: QTextCharFormat):
        """Write text with format.
        
        Args:
            text: Text to write
            format: Text format
        """
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, format)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        
    def set_font_size(self, size: int):
        """Set font size.
        
        Args:
            size: Font size
        """
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)
