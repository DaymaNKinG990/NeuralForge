"""Advanced code editor with line numbers and syntax highlighting."""
from typing import Optional, Dict, Set
from PyQt6.QtWidgets import (
    QPlainTextEdit, QWidget, QTextEdit, QMenu,
    QMessageBox
)
from PyQt6.QtCore import (
    Qt, QRect, pyqtSignal, QPoint,
    QTimer
)
from PyQt6.QtGui import (
    QColor, QPainter, QTextFormat, QTextCharFormat,
    QTextDocument, QTextCursor, QPaintEvent, QKeyEvent,
    QKeySequence, QFont, QFontMetrics, QPen
)
import re
import chardet
from ..styles.style_manager import StyleManager
from .line_numbers import LineNumberArea
from .syntax import PythonHighlighter
from .dialogs import FindDialog, ReplaceDialog

class CodeEditor(QPlainTextEdit):
    """Advanced code editor with line numbers, syntax highlighting, and advanced features.
    
    Attributes:
        line_number_area: Widget displaying line numbers
        highlighter: Syntax highlighter for code
        style_manager: Manager for editor styles
        zoom_level: Current zoom level of the editor
        matching_brackets: Set of matching bracket pairs
        encoding: Current file encoding
    """
    
    cursor_position_changed = pyqtSignal(int, int)
    encoding_changed = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the code editor.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Initialize basic properties
        self.zoom_level = 0
        self.matching_brackets = {'{': '}', '[': ']', '(': ')'}
        self.encoding = 'utf-8'
        
        # Create components
        self.line_number_area = LineNumberArea(self)
        self.highlighter = PythonHighlighter(self.document())
        self.style_manager = StyleManager()
        
        # Initialize UI and connect signals
        self._init_ui()
        self._apply_styles()
        self._connect_signals()
        self._setup_shortcuts()
        
    def setText(self, text: str) -> None:
        """Set the text content of the editor.
        
        This method is provided for compatibility with QTextEdit interface.
        Internally it calls setPlainText.
        
        Args:
            text: Text content to set
        """
        self.setPlainText(text)
        
    def _init_ui(self) -> None:
        """Initialize the editor UI components."""
        # Set up line numbers
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Set up font
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Set up tab behavior
        self.setTabStopDistance(
            QFontMetrics(self.font()).horizontalAdvance(' ') * 4
        )
        
    def _apply_styles(self) -> None:
        """Apply default styles to the editor."""
        self.style_manager.apply_style(self, StyleClass.CODE_EDITOR)
        
    def _connect_signals(self) -> None:
        """Connect editor signals to slots."""
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self._emit_cursor_position)
        self.cursorPositionChanged.connect(self.highlight_matching_brackets)
        
    def _emit_cursor_position(self) -> None:
        """Emit the current cursor position."""
        cursor = self.textCursor()
        self.cursor_position_changed.emit(
            cursor.blockNumber() + 1,
            cursor.positionInBlock() + 1
        )
        
    def update_line_number_area_width(self, _: int) -> None:
        """Update the editor's viewport margins when line number width changes."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        
    def line_number_area_width(self) -> int:
        """Calculate width needed for the line number area.
        
        Returns:
            int: Width in pixels for the line number area
        """
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
        
    def update_line_number_area(self, rect: QRect, dy: int) -> None:
        """Update the line number area when the editor viewport scrolls.
        
        Args:
            rect: Rectangle that needs to be updated
            dy: Amount of vertical scroll
        """
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )
            
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
            
    def resizeEvent(self, event: QPaintEvent) -> None:
        """Handle resize events to adjust line number area.
        
        Args:
            event: Resize event details
        """
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(),
                 self.line_number_area_width(), cr.height())
        )
        
    def highlight_current_line(self) -> None:
        """Highlight the current line in the editor."""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.GlobalColor.yellow).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(
                QTextFormat.Property.FullWidthSelection,
                True
            )
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
            
        self.setExtraSelections(extra_selections)
        
    def zoom_in(self) -> None:
        """Increase the font size."""
        if self.zoom_level < 20:
            self.zoom_level += 1
            font = self.font()
            font.setPointSize(font.pointSize() + 1)
            self.setFont(font)
            
    def zoom_out(self) -> None:
        """Decrease the font size."""
        if self.zoom_level > -10:
            self.zoom_level -= 1
            font = self.font()
            font.setPointSize(max(6, font.pointSize() - 1))
            self.setFont(font)
            
    def detect_encoding(self, content: bytes) -> str:
        """Detect the encoding of the given content.
        
        Args:
            content: Bytes content to analyze
            
        Returns:
            str: Detected encoding
        """
        result = chardet.detect(content)
        encoding = result['encoding'] or 'utf-8'
        if encoding != self.encoding:
            self.encoding = encoding
            self.encoding_changed.emit(encoding)
        return encoding
        
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for auto-indentation and bracket matching.
        
        Args:
            event: Key event details
        """
        if event.key() == Qt.Key.Key_Return:
            # Auto-indent
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()
            indent = re.match(r'^\s*', text).group()
            
            # Add extra indent after colon
            if text.rstrip().endswith(':'):
                indent += '    '
                
            super().keyPressEvent(event)
            self.insertPlainText(indent)
            return
            
        if event.text() in self.matching_brackets:
            # Auto-complete brackets
            cursor = self.textCursor()
            super().keyPressEvent(event)
            self.insertPlainText(self.matching_brackets[event.text()])
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            return
            
        super().keyPressEvent(event)
        
    def highlight_matching_brackets(self) -> None:
        """Highlight matching brackets in the editor."""
        extra_selections = self.extraSelections()
        
        cursor = self.textCursor()
        block = cursor.block()
        text = block.text()
        pos = cursor.positionInBlock()
        
        if pos > 0 and pos <= len(text):
            char = text[pos - 1]
            if char in self.matching_brackets:
                # Find matching closing bracket
                match_pos = self._find_matching_bracket(
                    cursor.position() - 1,
                    char,
                    self.matching_brackets[char],
                    1
                )
            elif char in self.matching_brackets.values():
                # Find matching opening bracket
                match_pos = self._find_matching_bracket(
                    cursor.position() - 1,
                    char,
                    list(self.matching_brackets.keys())[
                        list(self.matching_brackets.values()).index(char)
                    ],
                    -1
                )
            else:
                return
                
            if match_pos >= 0:
                # Highlight both brackets
                format = QTextCharFormat()
                format.setBackground(QColor(Qt.GlobalColor.green).lighter(160))
                
                cursor.setPosition(cursor.position() - 1)
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right,
                    QTextCursor.MoveMode.KeepAnchor
                )
                selection = QTextEdit.ExtraSelection()
                selection.format = format
                selection.cursor = cursor
                extra_selections.append(selection)
                
                cursor.setPosition(match_pos)
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right,
                    QTextCursor.MoveMode.KeepAnchor
                )
                selection = QTextEdit.ExtraSelection()
                selection.format = format
                selection.cursor = cursor
                extra_selections.append(selection)
                
        self.setExtraSelections(extra_selections)
        
    def _find_matching_bracket(
        self,
        pos: int,
        char: str,
        match_char: str,
        direction: int
    ) -> int:
        """Find the matching bracket position.
        
        Args:
            pos: Starting position
            char: Opening/closing bracket character
            match_char: Matching bracket character
            direction: Search direction (1 for forward, -1 for backward)
            
        Returns:
            int: Position of matching bracket or -1 if not found
        """
        count = 1
        doc = self.document()
        
        while True:
            pos += direction
            if pos < 0 or pos >= doc.characterCount():
                return -1
                
            cursor = QTextCursor(doc)
            cursor.setPosition(pos)
            current_char = cursor.block().text()[cursor.positionInBlock()]
            
            if current_char == match_char:
                count -= 1
                if count == 0:
                    return pos
            elif current_char == char:
                count += 1
                
    def show_find_dialog(self) -> None:
        """Show the find dialog."""
        dialog = FindDialog(self)
        dialog.show()
        
    def show_replace_dialog(self) -> None:
        """Show the find and replace dialog."""
        dialog = ReplaceDialog(self)
        dialog.show()
        
    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts for editor actions."""
        # Find/Replace shortcuts
        find_shortcut = QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_F)
        replace_shortcut = QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_H)
        
        find_action = self.addAction("Find")
        find_action.setShortcut(find_shortcut)
        find_action.triggered.connect(self.show_find_dialog)
        
        replace_action = self.addAction("Replace")
        replace_action.setShortcut(replace_shortcut)
        replace_action.triggered.connect(self.show_replace_dialog)
        
        # Zoom shortcuts
        zoom_in_shortcut = QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Plus)
        zoom_out_shortcut = QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Minus)
        
        zoom_in_action = self.addAction("Zoom In")
        zoom_in_action.setShortcut(zoom_in_shortcut)
        zoom_in_action.triggered.connect(self.zoom_in)
        
        zoom_out_action = self.addAction("Zoom Out")
        zoom_out_action.setShortcut(zoom_out_shortcut)
        zoom_out_action.triggered.connect(self.zoom_out)
        
    def show_context_menu(self, pos: QPoint) -> None:
        """Show the context menu at the given position.
        
        Args:
            pos: Position to show menu at
        """
        menu = QMenu(self)
        
        # Add standard actions
        menu.addAction(self.action("Cut"))
        menu.addAction(self.action("Copy"))
        menu.addAction(self.action("Paste"))
        menu.addSeparator()
        menu.addAction(self.action("Find"))
        menu.addAction(self.action("Replace"))
        menu.addSeparator()
        menu.addAction(self.action("Zoom In"))
        menu.addAction(self.action("Zoom Out"))
        
        menu.exec(self.mapToGlobal(pos))
        
    def line_number_area_paint_event(self, event: QPaintEvent) -> None:
        """Paint the line number area.
        
        Args:
            event: Paint event details
        """
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.GlobalColor.lightGray)
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(
            self.contentOffset()
        ).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.GlobalColor.black)
                painter.drawText(
                    0, top,
                    self.line_number_area.width() - 2,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number
                )
                
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1
            
    def closeEvent(self, event: QPaintEvent) -> None:
        """Handle cleanup when editor is closed.
        
        Args:
            event: Close event details
        """
        # Cleanup any resources
        self.highlighter.setDocument(None)
        super().closeEvent(event)
