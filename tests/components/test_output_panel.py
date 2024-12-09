"""Tests for output panel component."""
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCharFormat, QColor
from src.ui.components.output.output_panel import OutputPanel

@pytest.fixture
def output_panel(qtbot):
    """Create output panel fixture."""
    panel = OutputPanel()
    qtbot.addWidget(panel)
    return panel

def test_output_panel_creation(output_panel):
    """Test output panel creation."""
    assert output_panel is not None
    assert output_panel.output is not None
    assert output_panel.status_label is not None
    
def test_append_text(output_panel):
    """Test appending text."""
    text = "Test message"
    output_panel.append_text(text)
    assert text in output_panel.output.toPlainText()
    
def test_append_error(output_panel):
    """Test appending error text."""
    error = "Error message"
    output_panel.append_error(error)
    assert error in output_panel.output.toPlainText()
    
    # Check color
    cursor = output_panel.output.textCursor()
    cursor.movePosition(cursor.MoveOperation.Start)
    cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, len(error))
    format = cursor.charFormat()
    assert format.foreground().color() == QColor(255, 100, 100)
    
def test_append_warning(output_panel):
    """Test appending warning text."""
    warning = "Warning message"
    output_panel.append_warning(warning)
    assert warning in output_panel.output.toPlainText()
    
    # Check color
    cursor = output_panel.output.textCursor()
    cursor.movePosition(cursor.MoveOperation.Start)
    cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, len(warning))
    format = cursor.charFormat()
    assert format.foreground().color() == QColor(255, 200, 100)
    
def test_append_success(output_panel):
    """Test appending success text."""
    success = "Success message"
    output_panel.append_success(success)
    assert success in output_panel.output.toPlainText()
    
    # Check color
    cursor = output_panel.output.textCursor()
    cursor.movePosition(cursor.MoveOperation.Start)
    cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, len(success))
    format = cursor.charFormat()
    assert format.foreground().color() == QColor(100, 255, 100)
    
def test_clear(output_panel):
    """Test clearing output."""
    output_panel.append_text("Test text")
    assert output_panel.output.toPlainText() != ""
    
    output_panel.clear()
    assert output_panel.output.toPlainText() == ""
    
def test_set_status(output_panel):
    """Test setting status text."""
    status = "Test status"
    output_panel.set_status(status)
    assert output_panel.status_label.text() == status
    
def test_read_only(output_panel):
    """Test output is read-only."""
    assert output_panel.output.isReadOnly()
    
def test_line_wrap(output_panel):
    """Test line wrap mode."""
    assert output_panel.output.lineWrapMode() == output_panel.output.LineWrapMode.NoWrap
