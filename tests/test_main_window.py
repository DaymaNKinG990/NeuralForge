import pytest
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QDockWidget, QDoubleSpinBox
from PyQt6.QtCore import Qt
from src.ui.main_window import MainWindow
from src.ui.code_editor import CodeEditor
from src.ui.project_explorer import ProjectExplorer
from unittest.mock import MagicMock, patch

@pytest.fixture
def main_window(qtbot):
    with patch('src.ui.main_window.profiler'):  # Mock the profiler
        window = MainWindow()
        qtbot.addWidget(window)
        return window

def test_window_initialization(main_window):
    """Test basic window initialization"""
    assert isinstance(main_window, QMainWindow)
    assert main_window.windowTitle() == "NeuroForge IDE"
    assert main_window.minimumSize().width() >= 1200
    assert main_window.minimumSize().height() >= 800

def test_central_widget_setup(main_window):
    """Test central widget and tab setup"""
    assert isinstance(main_window.central_widget, QTabWidget)
    assert main_window.central_widget.tabPosition() == QTabWidget.TabPosition.North

def test_dock_widgets_setup(main_window):
    """Test dock widgets initialization"""
    # Check project explorer dock
    project_explorer_dock = main_window.findChild(QDockWidget, "Project Explorer")
    assert project_explorer_dock is not None
    assert project_explorer_dock.windowTitle() == "Project Explorer"
    
    # Check git panel dock
    git_panel_dock = main_window.findChild(QDockWidget, "Git")
    assert git_panel_dock is not None
    assert git_panel_dock.windowTitle() == "Git"

@pytest.mark.parametrize("file_path", [
    "test.py",
    "test.txt",
    "test.md"
])
def test_open_file(main_window, qtbot, file_path):
    with patch('src.ui.main_window.QFileDialog.getOpenFileName', return_value=(file_path, '')):
        main_window.open_file()
        assert main_window.central_widget.currentWidget().document().toPlainText() == ""

def test_save_file(main_window, qtbot, tmp_path):
    """Test file saving functionality"""
    # Create a temporary file
    test_file = tmp_path / "test.py"
    test_file.write_text("initial content")
    
    # Mock file dialog
    with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName',
              return_value=(str(test_file), "Python Files (*.py)")):
        # Trigger save action
        main_window.save_file()
        
        # Verify file exists
        assert test_file.exists()

def test_style_application(main_window):
    """Test style manager initialization and application"""
    assert hasattr(main_window, '_style_manager')
    # Add more specific style checks based on your StyleManager implementation
