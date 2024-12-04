from PyQt6.QtCore import Qt
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#FF6B6B"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "False", "finally", "for",
            "from", "global", "if", "import", "in", "is", "lambda", "None",
            "nonlocal", "not", "or", "pass", "raise", "return", "True",
            "try", "while", "with", "yield"
        ]
        self.add_keywords(keywords, keyword_format)
        
        # Built-in functions
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#4ECDC4"))
        builtins = [
            "abs", "all", "any", "bin", "bool", "chr", "dict", "dir",
            "enumerate", "eval", "exec", "filter", "float", "format",
            "frozenset", "getattr", "globals", "hasattr", "hash", "help",
            "hex", "id", "input", "int", "isinstance", "issubclass", "iter",
            "len", "list", "locals", "map", "max", "min", "next", "object",
            "oct", "open", "ord", "pow", "print", "property", "range",
            "repr", "reversed", "round", "set", "setattr", "slice",
            "sorted", "staticmethod", "str", "sum", "super", "tuple",
            "type", "vars", "zip"
        ]
        self.add_keywords(builtins, builtin_format)
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#F7D794"))
        self.add_pattern(r'\b\d+\b', number_format)
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#96CEB4"))
        self.add_pattern(r'"[^"\\]*(\\.[^"\\]*)*"', string_format)
        self.add_pattern(r"'[^'\\]*(\\.[^'\\]*)*'", string_format)
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#95A5A6"))
        comment_format.setFontItalic(True)
        self.add_pattern(r'#[^\n]*', comment_format)
        
        # Decorators
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#E056FD"))
        self.add_pattern(r'@\w+', decorator_format)
        
    def add_keywords(self, keywords, format):
        for word in keywords:
            pattern = r'\b' + word + r'\b'
            self.add_pattern(pattern, format)
            
    def add_pattern(self, pattern, format):
        from PyQt6.QtCore import QRegularExpression
        self.highlighting_rules.append((QRegularExpression(pattern), format))
        
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
