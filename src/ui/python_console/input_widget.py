"""Console input widget."""
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QKeyEvent, QTextCursor,
    QFont, QFontMetrics
)

class ConsoleInputWidget(QPlainTextEdit):
    """Widget for console input."""
    
    code_executed = pyqtSignal(str)  # Emits code when executed
    history_up = pyqtSignal()  # Emits when up key pressed
    history_down = pyqtSignal()  # Emits when down key pressed
    
    def __init__(self, parent=None):
        """Initialize input widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setup_widget()
        
    def setup_widget(self):
        """Set up the input widget."""
        # Set font
        font = QFont("Courier New")
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Set tab width
        metrics = QFontMetrics(font)
        self.setTabStopDistance(4 * metrics.horizontalAdvance(' '))
        
        # Set placeholder
        self.setPlaceholderText("Enter Python code here...")
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events.
        
        Args:
            event: Key event
        """
        # Execute on Ctrl+Enter
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.execute_current()
            return
            
        # History navigation
        if event.key() == Qt.Key.Key_Up and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.history_up.emit()
            return
        if event.key() == Qt.Key.Key_Down and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.history_down.emit()
            return
            
        # Handle tab indentation
        if event.key() == Qt.Key.Key_Tab:
            self.indent()
            return
            
        # Default handling
        super().keyPressEvent(event)
        
    def execute_current(self):
        """Execute current input."""
        code = self.toPlainText().strip()
        if code:
            self.code_executed.emit(code)
            self.clear()
            
    def indent(self):
        """Handle tab indentation."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            # Indent selection
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            
            selected_text = cursor.selectedText()
            indented_text = '    ' + selected_text.replace('\u2029', '\n    ')
            cursor.insertText(indented_text)
        else:
            # Insert spaces at cursor
            cursor.insertText('    ')
            
    def set_font_size(self, size: int):
        """Set font size.
        
        Args:
            size: Font size
        """
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)
        
        # Update tab width
        metrics = QFontMetrics(font)
        self.setTabStopDistance(4 * metrics.horizontalAdvance(' '))
        
    def get_input(self) -> str:
        """Get current input.
        
        Returns:
            Input text
        """
        return self.toPlainText()
        
    def set_input(self, text: str):
        """Set input text.
        
        Args:
            text: Input text
        """
        self.setPlainText(text)
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)
