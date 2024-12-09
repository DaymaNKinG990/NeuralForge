"""Output panel component."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit,
    QToolBar, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor

class OutputPanel(QWidget):
    """Panel for displaying output and logs."""
    
    def __init__(self, parent=None):
        """Initialize output panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QToolBar()
        self.status_label = QLabel()
        toolbar.addWidget(self.status_label)
        layout.addWidget(toolbar)
        
        # Output text
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.output)
        
        # Set default format
        self.default_format = QTextCharFormat()
        self.default_format.setForeground(QColor(200, 200, 200))
        
        # Set error format
        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor(255, 100, 100))
        
        # Set warning format
        self.warning_format = QTextCharFormat()
        self.warning_format.setForeground(QColor(255, 200, 100))
        
        # Set success format
        self.success_format = QTextCharFormat()
        self.success_format.setForeground(QColor(100, 255, 100))
        
    def clear(self):
        """Clear output text."""
        self.output.clear()
        
    def append_text(self, text: str, format: QTextCharFormat = None):
        """Append text with optional format.
        
        Args:
            text: Text to append
            format: Text format to use
        """
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        if format:
            cursor.insertText(text, format)
        else:
            cursor.insertText(text, self.default_format)
            
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()
        
    def append_error(self, text: str):
        """Append error text.
        
        Args:
            text: Error text
        """
        self.append_text(text, self.error_format)
        
    def append_warning(self, text: str):
        """Append warning text.
        
        Args:
            text: Warning text
        """
        self.append_text(text, self.warning_format)
        
    def append_success(self, text: str):
        """Append success text.
        
        Args:
            text: Success text
        """
        self.append_text(text, self.success_format)
        
    def set_status(self, text: str):
        """Set status text.
        
        Args:
            text: Status text
        """
        self.status_label.setText(text)
