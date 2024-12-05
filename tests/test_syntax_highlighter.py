import pytest
from PyQt6.QtGui import QTextDocument, QColor, QTextCursor
from PyQt6.QtCore import Qt
from src.utils.syntax_highlighter import PythonHighlighter

@pytest.fixture
def document():
    """Create a test document"""
    return QTextDocument()

@pytest.fixture
def highlighter(document):
    """Create a syntax highlighter"""
    return PythonHighlighter(document)

def get_format_at(document, position):
    """Helper to get format at position"""
    block = document.findBlock(position)
    return block.layout().additionalFormats()

def test_keyword_highlighting(document, highlighter):
    """Test highlighting of Python keywords"""
    test_code = "def test_function():\n    return True"
    document.setPlainText(test_code)
    
    # Check 'def' keyword
    formats = get_format_at(document, 0)
    assert any(f.format.foreground().color().name() == QColor("#FF6B6B").name()
              for f in formats if f.start == 0 and f.length == 3)
    
    # Check 'return' keyword
    formats = get_format_at(document, test_code.index("return"))
    assert any(f.format.foreground().color().name() == QColor("#FF6B6B").name()
              for f in formats if f.length == 6)
    
    # Check 'True' keyword
    formats = get_format_at(document, test_code.index("True"))
    assert any(f.format.foreground().color().name() == QColor("#FF6B6B").name()
              for f in formats if f.length == 4)

def test_builtin_highlighting(document, highlighter):
    """Test highlighting of built-in functions"""
    test_code = "print(len([1, 2, 3]))"
    document.setPlainText(test_code)
    
    # Check 'print' builtin
    formats = get_format_at(document, 0)
    assert any(f.format.foreground().color().name() == QColor("#4ECDC4").name()
              for f in formats if f.start == 0 and f.length == 5)
    
    # Check 'len' builtin
    formats = get_format_at(document, test_code.index("len"))
    assert any(f.format.foreground().color().name() == QColor("#4ECDC4").name()
              for f in formats if f.length == 3)

def test_number_highlighting(document, highlighter):
    """Test highlighting of numbers"""
    test_code = "x = 42\ny = 3.14"
    document.setPlainText(test_code)
    
    # Check integer
    formats = get_format_at(document, test_code.index("42"))
    assert any(f.format.foreground().color().name() == QColor("#F7D794").name()
              for f in formats if f.length == 2)
    
    # Check float
    formats = get_format_at(document, test_code.index("3.14"))
    assert any(f.format.foreground().color().name() == QColor("#F7D794").name()
              for f in formats if f.length == 4)

def test_string_highlighting(document, highlighter):
    """Test highlighting of strings"""
    test_code = 'single = \'test\'\ndouble = "test"\nescaped = "test\\"quote"'
    document.setPlainText(test_code)
    
    # Check single quotes
    formats = get_format_at(document, test_code.index("'test'"))
    assert any(f.format.foreground().color().name() == QColor("#96CEB4").name()
              for f in formats if f.length == 6)
    
    # Check double quotes
    formats = get_format_at(document, test_code.index('"test"'))
    assert any(f.format.foreground().color().name() == QColor("#96CEB4").name()
              for f in formats if f.length == 6)
    
    # Check escaped quotes
    formats = get_format_at(document, test_code.index('"test\\"quote"'))
    assert any(f.format.foreground().color().name() == QColor("#96CEB4").name()
              for f in formats if f.length == 12)

def test_comment_highlighting(document, highlighter):
    """Test highlighting of comments"""
    test_code = "x = 1  # This is a comment\n# Full line comment"
    document.setPlainText(test_code)
    
    # Check inline comment
    formats = get_format_at(document, test_code.index("#"))
    assert any(f.format.foreground().color().name() == QColor("#95A5A6").name()
              for f in formats)
    assert any(f.format.fontItalic() for f in formats)
    
    # Check full line comment
    formats = get_format_at(document, test_code.index("# Full"))
    assert any(f.format.foreground().color().name() == QColor("#95A5A6").name()
              for f in formats)
    assert any(f.format.fontItalic() for f in formats)

def test_decorator_highlighting(document, highlighter):
    """Test highlighting of decorators"""
    test_code = "@property\ndef getter(self):\n    pass"
    document.setPlainText(test_code)
    
    # Check decorator
    formats = get_format_at(document, 0)
    assert any(f.format.foreground().color().name() == QColor("#E056FD").name()
              for f in formats if f.start == 0)

def test_mixed_content(document, highlighter):
    """Test highlighting of mixed content"""
    test_code = '''@decorator
def test():
    x = 42  # Number
    print("Hello")  # String and comment
    return len([1, 2, 3])'''
    document.setPlainText(test_code)
    
    # Verify all elements are highlighted correctly
    def check_color_at(pos, color):
        formats = get_format_at(document, pos)
        return any(f.format.foreground().color().name() == color.name()
                  for f in formats)
    
    # Check decorator
    assert check_color_at(0, QColor("#E056FD"))
    
    # Check def keyword
    assert check_color_at(test_code.index("def"), QColor("#FF6B6B"))
    
    # Check number
    assert check_color_at(test_code.index("42"), QColor("#F7D794"))
    
    # Check string
    assert check_color_at(test_code.index('"Hello"'), QColor("#96CEB4"))
    
    # Check comment
    assert check_color_at(test_code.index("# Number"), QColor("#95A5A6"))
    
    # Check builtin function
    assert check_color_at(test_code.index("print"), QColor("#4ECDC4"))

def test_incremental_changes(document, highlighter):
    """Test highlighting updates with incremental changes"""
    document.setPlainText("x = 1")
    
    # Insert new content
    cursor = QTextCursor(document)
    cursor.movePosition(QTextCursor.MoveOperation.End)
    cursor.insertText("  # Comment")
    
    # Check that new content is highlighted
    formats = get_format_at(document, document.toPlainText().index("#"))
    assert any(f.format.foreground().color().name() == QColor("#95A5A6").name()
              for f in formats)

def test_syntax_error_resilience(document, highlighter):
    """Test highlighter resilience to syntax errors"""
    # Invalid Python syntax shouldn't crash the highlighter
    test_code = "def invalid syntax:\n    print('unclosed string"
    document.setPlainText(test_code)
    
    # Highlighter should still work for valid parts
    formats = get_format_at(document, 0)
    assert any(f.format.foreground().color().name() == QColor("#FF6B6B").name()
              for f in formats if f.start == 0 and f.length == 3)
