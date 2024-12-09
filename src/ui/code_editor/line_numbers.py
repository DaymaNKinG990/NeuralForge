"""Line number area widget for code editor."""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPaintEvent

class LineNumberArea(QWidget):
    """Widget for displaying line numbers in code editor.
    
    Attributes:
        code_editor: Reference to the parent CodeEditor widget
    """
    
    def __init__(self, editor: 'CodeEditor') -> None:
        """Initialize the line number area.
        
        Args:
            editor: Parent CodeEditor widget
        """
        super().__init__(editor)
        self.code_editor = editor
        
    def sizeHint(self) -> QSize:
        """Calculate the recommended size for the widget.
        
        Returns:
            QSize: Recommended size for the widget
        """
        return QSize(self.code_editor.line_number_area_width(), 0)
        
    def paintEvent(self, event: QPaintEvent) -> None:
        """Handle paint events for the line number area.
        
        Args:
            event: Paint event details
        """
        self.code_editor.line_number_area_paint_event(event)
