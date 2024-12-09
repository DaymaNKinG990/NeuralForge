"""Code editor package with advanced features."""
from .editor import CodeEditor
from .line_numbers import LineNumberArea
from .syntax import PythonHighlighter
from .dialogs import FindDialog, ReplaceDialog

__all__ = [
    'CodeEditor',
    'LineNumberArea',
    'PythonHighlighter',
    'FindDialog',
    'ReplaceDialog'
]
