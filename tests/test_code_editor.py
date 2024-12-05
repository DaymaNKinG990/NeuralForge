import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QPalette, QColor
from src.ui.code_editor import CodeEditor
from src.utils.distributed_cache import get_distributed_cache
from src.utils.preloader import PreloadManager, ComponentPreloader
from src.ui.styles.style_manager import StyleManager
from src.ui.styles.style_enums import StyleClass, ThemeType
import gc

# Reset global instances before tests
@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Create the QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global instances before each test."""
    # Get fresh test instance of distributed cache
    test_cache = get_distributed_cache(test_mode=True)
    test_cache._initialized = False  # Force reinitialization
    
    # Reset preloader globals
    PreloadManager._instance = None
    ComponentPreloader._instance = None
    
    yield
    
    # Cleanup after test
    if hasattr(test_cache, '_server') and test_cache._server:
        test_cache._server.close()
    test_cache._running = False
    gc.collect()

@pytest.fixture
def code_editor(qtbot, qapp, reset_globals):
    """Create a CodeEditor instance for testing."""
    editor = None
    try:
        editor = CodeEditor()
        editor.setWindowTitle("Test Editor")
        editor.resize(800, 600)
        
        # Add to qtbot before showing
        qtbot.addWidget(editor)
        
        # Show and wait for window to be exposed
        editor.show()
        with qtbot.waitExposed(editor):
            qapp.processEvents()
            qtbot.wait(100)  # Additional wait for initialization
        
        yield editor
        
    finally:
        # Cleanup
        if editor:
            try:
                if editor.isVisible():
                    editor.hide()
                if editor.highlighter:
                    editor.highlighter.setDocument(None)
                    editor.highlighter.deleteLater()
                if editor.line_number_area:
                    editor.line_number_area.deleteLater()
                editor.close()
                editor.deleteLater()
                qtbot.wait(100)
                qapp.processEvents()
            except RuntimeError:
                pass  # Object may already be deleted
        gc.collect()

def test_editor_initialization(code_editor, qtbot):
    """Test that the editor initializes correctly."""
    assert code_editor is not None
    assert code_editor.isVisible()
    assert code_editor.line_number_area is not None
    assert code_editor.line_number_area.isVisible()

def test_text_manipulation(code_editor, qtbot):
    """Test basic text manipulation."""
    test_text = "Hello, World!"

    # Set text and verify
    code_editor.setPlainText(test_text)
    qtbot.wait(50)  # Wait for text to be set
    assert code_editor.toPlainText() == test_text

    # Test text selection
    cursor = code_editor.textCursor()
    
    # Move cursor to start without selection
    cursor.movePosition(QTextCursor.MoveOperation.Start, QTextCursor.MoveMode.MoveAnchor)
    code_editor.setTextCursor(cursor)
    qtbot.wait(50)
    
    # Select to end
    cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
    code_editor.setTextCursor(cursor)
    qtbot.wait(50)

    # Verify selection
    assert code_editor.textCursor().selectedText() == test_text
    
    # Test cursor position
    assert code_editor.textCursor().position() == len(test_text)
    assert code_editor.textCursor().anchor() == 0

def test_syntax_highlighting(code_editor, qtbot):
    """Test syntax highlighting functionality."""
    test_code = "def test_function():\n    pass"
    code_editor.setPlainText(test_code)
    qtbot.wait(50)  # Wait for highlighting

    # Get format of first word (should be highlighted as keyword)
    cursor = code_editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 3)  # Select "def"
    
    # Get the format for the selected text
    format = cursor.charFormat()
    assert format is not None, "No format found for keyword 'def'"
    
    # Verify the text is highlighted as a keyword
    assert format.foreground().color() != code_editor.palette().text().color(), "Keyword 'def' not highlighted"

def test_line_numbers(code_editor, qtbot):
    """Test line number area functionality."""
    test_text = "Line 1\nLine 2\nLine 3"
    code_editor.setPlainText(test_text)
    qtbot.wait(50)  # Wait for text to be set
    
    # Verify line number area is visible and has correct width
    assert code_editor.line_number_area.isVisible()
    assert code_editor.line_number_area.width() > 0

def test_indentation(code_editor, qtbot):
    """Test auto-indentation functionality."""
    # Type a function definition and press enter
    code_editor.setPlainText("def test_function():")
    qtbot.wait(50)  # Wait for text to be set

    # Move cursor to end and press enter
    cursor = code_editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
    code_editor.setTextCursor(cursor)
    qtbot.keyClick(code_editor, Qt.Key.Key_Return)
    qtbot.wait(50)  # Wait for indentation to be applied
    
    # Check that indentation was added
    text = code_editor.toPlainText()
    assert text.endswith("\n    "), "Expected 4 spaces indentation after function definition"

def test_code_editor_palette(code_editor):
    """Test that code editor palette is set correctly."""
    palette = code_editor.palette()
    style_manager = StyleManager()
    
    # Check background color
    bg_color = palette.color(QPalette.ColorRole.Base)
    expected_bg = QColor(style_manager.get_color(StyleClass.EDITOR_BACKGROUND))
    assert bg_color == expected_bg
    
    # Check text color
    text_color = palette.color(QPalette.ColorRole.Text)
    expected_text = QColor(style_manager.get_color(StyleClass.FOREGROUND))
    assert text_color == expected_text

def test_line_number_area(code_editor):
    """Test that line number area is created and visible."""
    assert code_editor.line_number_area is not None
    assert code_editor.line_number_area.isVisible()

    # Check line number area palette
    style_manager = StyleManager()
    style_manager.set_theme(ThemeType.DARK)  # Use dark theme for consistent testing
    line_number_style = style_manager.get_component_style(StyleClass.LINE_NUMBER_AREA)
    
    palette = code_editor.line_number_area.palette()
    assert palette is not None
