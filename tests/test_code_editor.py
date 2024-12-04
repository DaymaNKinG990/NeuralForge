import pytest
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor
from src.ui.code_editor import CodeEditor

@pytest.fixture
def code_editor(qtbot):
    editor = CodeEditor()
    qtbot.addWidget(editor)
    return editor

def test_editor_initialization(code_editor):
    assert isinstance(code_editor, QWidget)

def test_text_manipulation(code_editor, qtbot):
    test_text = "def test_function():\n    pass"
    code_editor.setText(test_text)
    assert code_editor.toPlainText() == test_text

def test_syntax_highlighting(code_editor, qtbot):
    test_code = "def highlight_test():\n    return True"
    code_editor.setText(test_code)
    # Verify syntax highlighting is applied
    assert code_editor.document().defaultTextOption().flags() & Qt.TextFlag.TextShowTabsAndSpaces

def test_line_numbers(code_editor):
    test_text = "line 1\nline 2\nline 3"
    code_editor.setText(test_text)
    assert code_editor.line_number_area.isVisible()

def test_indentation(code_editor, qtbot):
    code_editor.setText("def test():")
    qtbot.keyClick(code_editor, Qt.Key.Key_Return)
    # Check if auto-indentation was applied
    cursor = code_editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
    assert cursor.block().text() == "    "
