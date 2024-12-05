from typing import Optional, Dict, Set
from PyQt6.QtWidgets import (
    QPlainTextEdit, QWidget, QTextEdit, QVBoxLayout, QMenu,
    QDialog, QLabel, QLineEdit, QPushButton, QHBoxLayout,
    QCheckBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import (
    Qt, QRect, QSize, pyqtSignal, QPoint,
    QTimer, QThread
)
from PyQt6.QtGui import (
    QColor, QPainter, QTextFormat, QTextCharFormat,
    QSyntaxHighlighter, QTextDocument, QTextCursor,
    QPaintEvent, QKeyEvent, QKeySequence, QTextFormat,
    QFont, QFontMetrics, QPen, QPalette
)
from pathlib import Path
import re
import chardet
from ..utils.performance import PerformanceMonitor
from .styles.style_manager import StyleManager
from .styles.style_enums import StyleClass, ColorScheme

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
        
        # Built-ins
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor(ColorScheme.SYNTAX_BUILTIN.value))
        builtins = [
            'abs', 'all', 'any', 'bin', 'bool', 'bytes', 'callable', 'chr',
            'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir',
            'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format',
            'frozenset', 'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex',
            'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
            'list', 'locals', 'map', 'max', 'memoryview', 'min', 'next',
            'object', 'oct', 'open', 'ord', 'pow', 'print', 'property', 'range',
            'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted',
            'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars',
            'zip'
        ]
        rules[r'\b(' + '|'.join(builtins) + r')\b'] = builtin_format
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(ColorScheme.SYNTAX_STRING.value))
        rules[r'"[^"\\]*(\\.[^"\\]*)*"'] = string_format
        rules[r"'[^'\\]*(\\.[^'\\]*)*'"] = string_format
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(ColorScheme.SYNTAX_NUMBER.value))
        rules[r'\b\d+\b'] = number_format
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(ColorScheme.SYNTAX_COMMENT.value))
        comment_format.setFontItalic(True)
        rules[r'#[^\n]*'] = comment_format
        
        # Function definitions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(ColorScheme.SYNTAX_FUNCTION.value))
        rules[r'\bdef\s+([A-Za-z_][A-Za-z0-9_]*)\b'] = function_format
        
        # Class definitions
        class_format = QTextCharFormat()
        class_format.setForeground(QColor(ColorScheme.SYNTAX_CLASS.value))
        class_format.setFontWeight(QFont.Weight.Bold)
        rules[r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\b'] = class_format
        
        # Decorators
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor(ColorScheme.SYNTAX_DECORATOR.value))
        rules[r'@[A-Za-z_][A-Za-z0-9_]*'] = decorator_format
        
        # Operators
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor(ColorScheme.SYNTAX_OPERATOR.value))
        operators = [
            '=', '==', '!=', '<', '<=', '>', '>=', r'\+', '-', r'\*', '/',
            '//', r'\*\*', '%', '@', r'\+=', '-=', r'\*=', '/=', '//=',
            r'\*\*=', '%=', '@=', '&=', r'\|=', r'\^=', '>>=', '<<=', r'\+\+'
        ]
        rules[r'(' + '|'.join(operators) + r')'] = operator_format
        
        # Constants
        constant_format = QTextCharFormat()
        constant_format.setForeground(QColor(ColorScheme.SYNTAX_CONSTANT.value))
        rules[r'\b[A-Z_][A-Z0-9_]*\b'] = constant_format
        
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
        
    def _init_ui(self):
        """Initialize the editor UI components."""
        # Set default font
        font = QFont("Consolas", 10)
        font.setFixedPitch(True)
        self.setFont(font)
        
        # Set line wrapping
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Set up line numbers
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self._emit_cursor_position)
        
        # Set tab stop width
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        
        # Initial highlighting
        self.highlight_current_line()
        
    def _apply_styles(self):
        """Apply default styles to the editor."""
        # Set background color
        palette = self.palette()
        bg_color = QColor(self.style_manager.get_color(StyleClass.EDITOR_BACKGROUND))
        palette.setColor(QPalette.ColorRole.Base, bg_color)
        self.setPalette(palette)
        
        # Set text color
        text_color = QColor(self.style_manager.get_color(StyleClass.FOREGROUND))
        palette.setColor(QPalette.ColorRole.Text, text_color)
        self.setPalette(palette)
        
        # Set line number area background
        line_number_palette = self.line_number_area.palette()
        line_number_bg = QColor(ColorScheme.LINE_NUMBER_BG.value)
        line_number_fg = QColor(ColorScheme.LINE_NUMBER_FG.value)
        line_number_palette.setColor(QPalette.ColorRole.Base, line_number_bg)
        line_number_palette.setColor(QPalette.ColorRole.Text, line_number_fg)
        self.line_number_area.setPalette(line_number_palette)
        
        # Set selection color
        selection_color = QColor(self.style_manager.get_color(StyleClass.EDITOR_SELECTION))
        palette.setColor(QPalette.ColorRole.Highlight, selection_color)
        self.setPalette(palette)

    def _connect_signals(self) -> None:
        """Connect editor signals to slots."""
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self._emit_cursor_position)
        self.textChanged.connect(self.highlight_matching_brackets)
        
    def _emit_cursor_position(self) -> None:
        """Emit the current cursor position."""
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.cursor_position_changed.emit(line, column)
        
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
            self.line_number_area.update(0, rect.y(), 
                                       self.line_number_area.width(), rect.height())
            
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
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(self.style_manager.get_color(StyleClass.EDITOR_CURRENT_LINE))
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            
            self.setExtraSelections([selection])
        
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

    def highlight_matching_brackets(self):
        """Highlight matching brackets in the editor."""
        cursor = self.textCursor()
        
        # Clear existing bracket selections
        self.bracket_selections = []
        
        # Get current position
        pos = cursor.position()
        block = cursor.block()
        text = block.text()
        
        # Check for brackets at current position and position-1
        positions_to_check = [pos - block.position()]
        if pos > 0:
            positions_to_check.append(pos - block.position() - 1)
            
        for check_pos in positions_to_check:
            if 0 <= check_pos < len(text):
                char = text[check_pos]
                if char in '([{':
                    # Find matching closing bracket
                    cursor.setPosition(block.position() + check_pos)
                    if cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor):
                        self.bracket_selections.append(QTextEdit.ExtraSelection())
                        self.bracket_selections[-1].cursor = cursor
                        self.bracket_selections[-1].format.setBackground(QColor("#3E4451"))
                        
                    # Find and highlight closing bracket
                    doc = self.document()
                    pos = block.position() + check_pos
                    stack = [char]
                    pos += 1
                    
                    while pos < doc.characterCount() and stack:
                        cursor = QTextCursor(doc)
                        cursor.setPosition(pos)
                        char = cursor.document().characterAt(pos)
                        
                        if char in '([{':
                            stack.append(char)
                        elif char in ')]}':
                            if (char == ')' and stack[-1] == '(' or
                                char == ']' and stack[-1] == '[' or
                                char == '}' and stack[-1] == '{'):
                                stack.pop()
                                if not stack:  # Found matching bracket
                                    cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)
                                    self.bracket_selections.append(QTextEdit.ExtraSelection())
                                    self.bracket_selections[-1].cursor = cursor
                                    self.bracket_selections[-1].format.setBackground(QColor("#3E4451"))
                                    break
                        pos += 1
                        
                elif char in ')]}':
                    # Find matching opening bracket
                    cursor.setPosition(block.position() + check_pos)
                    if cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor):
                        self.bracket_selections.append(QTextEdit.ExtraSelection())
                        self.bracket_selections[-1].cursor = cursor
                        self.bracket_selections[-1].format.setBackground(QColor("#3E4451"))
                        
                    # Find and highlight opening bracket
                    doc = self.document()
                    pos = block.position() + check_pos
                    stack = [char]
                    pos -= 1
                    
                    while pos >= 0 and stack:
                        cursor = QTextCursor(doc)
                        cursor.setPosition(pos)
                        char = cursor.document().characterAt(pos)
                        
                        if char in ')]}':
                            stack.append(char)
                        elif char in '([{':
                            if (char == '(' and stack[-1] == ')' or
                                char == '[' and stack[-1] == ']' or
                                char == '{' and stack[-1] == '}'):
                                stack.pop()
                                if not stack:  # Found matching bracket
                                    cursor.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)
                                    self.bracket_selections.append(QTextEdit.ExtraSelection())
                                    self.bracket_selections[-1].cursor = cursor
                                    self.bracket_selections[-1].format.setBackground(QColor("#3E4451"))
                                    break
                        pos -= 1
        
        # Apply all selections
        if self.bracket_selections:
            all_selections = self.extraSelections()
            all_selections.extend(self.bracket_selections)
            self.setExtraSelections(all_selections)

    def show_find_dialog(self) -> None:
        """Show the find dialog."""
        dialog = FindDialog(self)
        dialog.exec()

    def show_replace_dialog(self) -> None:
        """Show the find and replace dialog."""
        dialog = ReplaceDialog(self)
        dialog.exec()

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

    def show_context_menu(self, pos):
        """Show the context menu at the given position.
        
        Args:
            pos: Position to show menu at
        """
        menu = QMenu(self)
        
        # Add standard actions
        menu.addAction("Cut", self.cut)
        menu.addAction("Copy", self.copy)
        menu.addAction("Paste", self.paste)
        menu.addSeparator()
        menu.addAction("Select All", self.selectAll)
        
        # Show menu at cursor position
        menu.exec(self.mapToGlobal(pos))

    def line_number_area_paint_event(self, event: QPaintEvent) -> None:
        """Paint the line number area.
        
        Args:
            event: Paint event details
        """
        painter = QPainter(self.line_number_area)
        bg_color = QColor(ColorScheme.LINE_NUMBER_BG.value)
        painter.fillRect(event.rect(), bg_color)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        font_metrics = self.fontMetrics()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(ColorScheme.LINE_NUMBER_FG.value))
                # Create a QRect for the text area
                text_rect = QRect(0, top, self.line_number_area.width(), font_metrics.height())
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def closeEvent(self, event):
        """Handle cleanup when editor is closed."""
        try:
            # Cleanup highlighter
            if hasattr(self, 'highlighter') and self.highlighter:
                self.highlighter.setDocument(None)
                self.highlighter.deleteLater()
            
            # Cleanup line number area
            if hasattr(self, 'line_number_area') and self.line_number_area:
                self.line_number_area.deleteLater()
            
            # Call parent's closeEvent
            super().closeEvent(event)
        except RuntimeError:
            pass  # Object may already be deleted

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
