"""Syntax highlighting for code editor."""
from typing import Dict
from PyQt6.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QTextDocument,
    QColor, QFont
)
from ..styles.style_enums import ColorScheme

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
        self.highlighting_rules = self._create_highlighting_rules()
        
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
            'zip', '__import__'
        ]
        rules[r'\b(' + '|'.join(builtins) + r')\b'] = builtin_format
        
        # String literals
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(ColorScheme.SYNTAX_STRING.value))
        rules[r'"[^"\\]*(\\.[^"\\]*)*"'] = string_format
        rules[r"'[^'\\]*(\\.[^'\\]*)*'"] = string_format
        rules[r'""".*?"""'] = string_format
        rules[r"'''.*?'''"] = string_format
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(ColorScheme.SYNTAX_NUMBER.value))
        rules[r'\b\d+\b'] = number_format
        rules[r'\b0[xX][0-9a-fA-F]+\b'] = number_format
        rules[r'\b\d+\.\d*\b'] = number_format
        rules[r'\b\.\d+\b'] = number_format
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(ColorScheme.SYNTAX_COMMENT.value))
        rules[r'#[^\n]*'] = comment_format
        
        # Decorators
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor(ColorScheme.SYNTAX_DECORATOR.value))
        rules[r'@\w+'] = decorator_format
        
        # Function definitions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(ColorScheme.SYNTAX_FUNCTION.value))
        rules[r'\bdef\s+(\w+)'] = function_format
        
        # Class definitions
        class_format = QTextCharFormat()
        class_format.setForeground(QColor(ColorScheme.SYNTAX_CLASS.value))
        rules[r'\bclass\s+(\w+)'] = class_format
        
        return rules
        
    def highlightBlock(self, text: str) -> None:
        """Apply syntax highlighting to a block of text.
        
        Args:
            text: Text block to highlight
        """
        for pattern, format in self.highlighting_rules.items():
            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)
