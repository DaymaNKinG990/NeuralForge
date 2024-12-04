from typing import Optional, List, Dict, Any, Tuple, Set
from PyQt6.QtWidgets import (
    QPlainTextEdit, QWidget, QVBoxLayout, QMenu,
    QDialog, QLabel, QLineEdit, QPushButton, QHBoxLayout,
    QCheckBox
)
from PyQt6.QtGui import (
    QPainter, QTextFormat, QColor, QTextCursor, 
    QSyntaxHighlighter, QTextCharFormat, QFont, QFontMetrics, QPen,
    QTextDocument, QPaintEvent, QKeyEvent
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QSize, QPoint
from pathlib import Path
from ..utils.performance import PerformanceMonitor
from .styles.style_manager import StyleManager
from .styles.style_enums import StyleClass, ColorScheme
import re
import chardet

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
        self.code_editor: CodeEditor = editor
        
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

class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python code.
    
    Attributes:
        highlighting_rules: Dictionary mapping regex patterns to text formats
    """
    
    def __init__(self, parent: QTextDocument) -> None:
        """Initialize the Python syntax highlighter.
        
        Args:
            parent: Parent text document
        """
        super().__init__(parent)
        self.highlighting_rules: Dict[str, QTextCharFormat] = self._create_highlighting_rules()
        
    def _create_highlighting_rules(self) -> Dict[str, QTextCharFormat]:
        """Create syntax highlighting rules for Python.
        
        Returns:
            Dict mapping regex patterns to text formats
        """
        rules = {}
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(ColorScheme.SYNTAX_KEYWORD.value))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = [
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None',
            'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True',
            'try', 'while', 'with', 'yield'
        ]
        rules[r'\b(' + '|'.join(keywords) + r')\b'] = keyword_format
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(ColorScheme.SYNTAX_STRING.value))
        rules[r'"[^"\\]*(\\.[^"\\]*)*"'] = string_format
        rules[r"'[^'\\]*(\\.[^'\\]*)*'"] = string_format
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(ColorScheme.SYNTAX_COMMENT.value))
        rules[r'#[^\n]*'] = comment_format
        
        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(ColorScheme.SYNTAX_FUNCTION.value))
        rules[r'\bdef\s+(\w+)'] = function_format
        
        # Classes
        class_format = QTextCharFormat()
        class_format.setForeground(QColor(ColorScheme.SYNTAX_CLASS.value))
        rules[r'\bclass\s+(\w+)'] = class_format
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(ColorScheme.SYNTAX_NUMBER.value))
        rules[r'\b\d+\b'] = number_format
        
        # Decorators
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor(ColorScheme.SYNTAX_DECORATOR.value))
        rules[r'@\w+'] = decorator_format
        
        return rules
        
    def highlightBlock(self, text: str) -> None:
        """Apply syntax highlighting to a block of text.
        
        Args:
            text: Text block to highlight
        """
        for pattern, format in self.highlighting_rules.items():
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class CodeEditor(QPlainTextEdit):
    """Advanced code editor with line numbers, syntax highlighting, and advanced features.
    
    Attributes:
        line_number_area (LineNumberArea): Widget displaying line numbers
        highlighter (PythonHighlighter): Syntax highlighter for code
        style_manager (StyleManager): Manager for editor styles
        zoom_level (int): Current zoom level of the editor
        matching_brackets (Set[str]): Set of matching bracket pairs
        encoding (str): Current file encoding
    """
    
    cursor_position_changed = pyqtSignal(int, int)
    encoding_changed = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the code editor.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.highlighter = PythonHighlighter(self.document())
        self.style_manager = StyleManager()
        self.zoom_level = 0
        self.matching_brackets = {'{': '}', '[': ']', '(': ')'}
        self.encoding = 'utf-8'
        
        self._init_ui()
        self._apply_styles()
        self._connect_signals()
        self._setup_shortcuts()

    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts for editor actions."""
        # Zoom shortcuts
        self.zoom_in_action = self.addAction("Zoom In")
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.triggered.connect(self.zoom_in)
        
        self.zoom_out_action = self.addAction("Zoom Out")
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.triggered.connect(self.zoom_out)
        
        # Find/Replace shortcuts
        self.find_action = self.addAction("Find")
        self.find_action.setShortcut("Ctrl+F")
        self.find_action.triggered.connect(self.show_find_dialog)
        
        self.replace_action = self.addAction("Replace")
        self.replace_action.setShortcut("Ctrl+H")
        self.replace_action.triggered.connect(self.show_replace_dialog)

    def zoom_in(self) -> None:
        """Increase the font size."""
        if self.zoom_level < 20:  # Maximum zoom level
            self.zoom_level += 1
            font = self.font()
            font.setPointSize(font.pointSize() + 1)
            self.setFont(font)

    def zoom_out(self) -> None:
        """Decrease the font size."""
        if self.zoom_level > -10:  # Minimum zoom level
            self.zoom_level -= 1
            font = self.font()
            font.setPointSize(max(font.pointSize() - 1, 6))  # Minimum size of 6
            self.setFont(font)

    def detect_encoding(self, content: bytes) -> str:
        """Detect the encoding of the given content.
        
        Args:
            content: Bytes content to analyze
            
        Returns:
            str: Detected encoding
        """
        result = chardet.detect(content)
        self.encoding = result['encoding'] or 'utf-8'
        self.encoding_changed.emit(self.encoding)
        return self.encoding

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for auto-indentation and bracket matching.
        
        Args:
            event: Key event details
        """
        # Auto-indentation for new lines
        if event.key() == Qt.Key.Key_Return:
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()
            indent = re.match(r'^\s*', text).group()
            
            # Check if we need to increase indentation
            if text.rstrip().endswith(':'):
                indent += '    '
            
            super().keyPressEvent(event)
            self.insertPlainText(indent)
            return
            
        # Auto-close brackets
        if event.text() in self.matching_brackets:
            cursor = self.textCursor()
            super().keyPressEvent(event)
            self.insertPlainText(self.matching_brackets[event.text()])
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)
            return
            
        super().keyPressEvent(event)
        
        # Highlight matching brackets
        if event.text() in self.matching_brackets.values() or event.text() in self.matching_brackets:
            self.highlight_matching_brackets()

    def highlight_matching_brackets(self) -> None:
        """Highlight matching bracket pairs."""
        cursor = self.textCursor()
        pos = cursor.position()
        document = self.document()
        
        # Clear existing bracket selections
        for selection in cursor.document().allSelections():
            cursor.removeSelection()
        
        # Check character under cursor
        char = document.characterAt(pos - 1)
        if char in self.matching_brackets or char in self.matching_brackets.values():
            self._find_and_highlight_matching_bracket(pos - 1, char)

    def _find_and_highlight_matching_bracket(self, pos: int, char: str) -> None:
        """Find and highlight the matching bracket for the given position.
        
        Args:
            pos: Position of the first bracket
            char: Bracket character to match
        """
        document = self.document()
        if char in self.matching_brackets:
            # Search forward for closing bracket
            stack = [char]
            i = pos + 1
            while i < document.characterCount():
                c = document.characterAt(i)
                if c == char:
                    stack.append(c)
                elif c == self.matching_brackets[char]:
                    stack.pop()
                    if not stack:
                        self._highlight_bracket_pair(pos, i)
                        break
                i += 1
        else:
            # Search backward for opening bracket
            opening_bracket = next(k for k, v in self.matching_brackets.items() if v == char)
            stack = [char]
            i = pos - 1
            while i >= 0:
                c = document.characterAt(i)
                if c == char:
                    stack.append(c)
                elif c == opening_bracket:
                    stack.pop()
                    if not stack:
                        self._highlight_bracket_pair(i, pos)
                        break
                i -= 1

    def _highlight_bracket_pair(self, pos1: int, pos2: int) -> None:
        """Highlight a pair of matching brackets.
        
        Args:
            pos1: Position of first bracket
            pos2: Position of second bracket
        """
        format = QTextCharFormat()
        format.setBackground(QColor(ColorScheme.EDITOR_MATCHING_BRACKET.value))
        format.setForeground(QColor(ColorScheme.FOREGROUND.value))
        
        cursor = self.textCursor()
        
        # Highlight first bracket
        cursor.setPosition(pos1)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
        selection = QTextEdit.ExtraSelection()
        selection.format = format
        selection.cursor = cursor
        
        # Highlight second bracket
        cursor.setPosition(pos2)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
        selection2 = QTextEdit.ExtraSelection()
        selection2.format = format
        selection2.cursor = cursor
        
        self.setExtraSelections([selection, selection2])

    def show_find_dialog(self) -> None:
        """Show the find dialog."""
        dialog = FindDialog(self)
        dialog.exec()

    def show_replace_dialog(self) -> None:
        """Show the find and replace dialog."""
        dialog = ReplaceDialog(self)
        dialog.exec()

class FindDialog(QDialog):
    """Dialog for finding text in the editor."""
    
    def __init__(self, editor: CodeEditor) -> None:
        """Initialize the find dialog.
        
        Args:
            editor: Parent editor widget
        """
        super().__init__(editor)
        self.editor = editor
        self.setWindowTitle("Find")
        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Search input
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        search_layout.addWidget(QLabel("Find:"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Options
        self.case_sensitive = QCheckBox("Case sensitive")
        self.whole_words = QCheckBox("Whole words")
        layout.addWidget(self.case_sensitive)
        layout.addWidget(self.whole_words)
        
        # Buttons
        button_layout = QHBoxLayout()
        find_next = QPushButton("Find Next")
        find_prev = QPushButton("Find Previous")
        find_next.clicked.connect(self.find_next)
        find_prev.clicked.connect(self.find_previous)
        button_layout.addWidget(find_prev)
        button_layout.addWidget(find_next)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def find_next(self) -> None:
        """Find the next occurrence of the search text."""
        self._find(QTextDocument.FindFlag(0))

    def find_previous(self) -> None:
        """Find the previous occurrence of the search text."""
        self._find(QTextDocument.FindFlag.FindBackward)

    def _find(self, direction: QTextDocument.FindFlag) -> None:
        """Find text in the specified direction.
        
        Args:
            direction: Search direction flag
        """
        flags = direction
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self.whole_words.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords
            
        text = self.search_input.text()
        cursor = self.editor.textCursor()
        
        if not self.editor.find(text, flags):
            # Wrap around
            cursor = self.editor.textCursor()
            cursor.movePosition(
                QTextCursor.Start if direction == QTextDocument.FindFlag(0) else QTextCursor.End
            )
            self.editor.setTextCursor(cursor)
            self.editor.find(text, flags)

class ReplaceDialog(FindDialog):
    """Dialog for finding and replacing text in the editor."""
    
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        super().setup_ui()
        
        # Add replace input
        replace_layout = QHBoxLayout()
        self.replace_input = QLineEdit()
        replace_layout.addWidget(QLabel("Replace with:"))
        replace_layout.addWidget(self.replace_input)
        
        # Add replace buttons
        button_layout = QHBoxLayout()
        replace = QPushButton("Replace")
        replace_all = QPushButton("Replace All")
        replace.clicked.connect(self.replace)
        replace_all.clicked.connect(self.replace_all)
        button_layout.addWidget(replace)
        button_layout.addWidget(replace_all)
        
        # Insert new widgets at appropriate positions
        layout = self.layout()
        layout.insertLayout(1, replace_layout)
        layout.insertLayout(-1, button_layout)

    def replace(self) -> None:
        """Replace the current selection and find the next occurrence."""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
        self.find_next()

    def replace_all(self) -> None:
        """Replace all occurrences of the search text."""
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        
        cursor.movePosition(QTextCursor.Start)
        self.editor.setTextCursor(cursor)
        
        count = 0
        while self.editor.find(self.search_input.text()):
            cursor = self.editor.textCursor()
            cursor.insertText(self.replace_input.text())
            count += 1
            
        cursor.endEditBlock()
