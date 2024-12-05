import pytest
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QDockWidget, QDoubleSpinBox
from PyQt6.QtCore import Qt
from src.ui.main_window import MainWindow
from src.ui.code_editor import CodeEditor
from src.ui.project_explorer import ProjectExplorer
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import os

@pytest.fixture
def main_window(qtbot):
    with patch('src.ui.main_window.profiler'):  # Mock the profiler
        window = MainWindow()
        qtbot.addWidget(window)
        return window

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

def test_window_initialization(main_window):
    """Test basic window initialization"""
    assert isinstance(main_window, QMainWindow)
    assert main_window.windowTitle() == "NeuroForge IDE"
    assert main_window.minimumSize().width() >= 1200
    assert main_window.minimumSize().height() >= 800

def test_central_widget_setup(main_window):
    """Test central widget and tab setup"""
    assert isinstance(main_window.tab_widget, QTabWidget)
    assert main_window.tab_widget.tabPosition() == QTabWidget.TabPosition.North

def test_dock_widgets_setup(main_window):
    """Test dock widgets initialization"""
    # Check project explorer dock
    project_explorer_dock = main_window.findChild(QDockWidget, "ProjectExplorer")
    assert project_explorer_dock is not None
    assert project_explorer_dock.windowTitle() == "Project Explorer"
    
    # Check ML workspace dock
    ml_workspace_dock = main_window.findChild(QDockWidget, "MLWorkspace")
    assert ml_workspace_dock is not None
    assert ml_workspace_dock.windowTitle() == "ML Workspace"
    
    # Check LLM workspace dock
    llm_workspace_dock = main_window.findChild(QDockWidget, "LLMWorkspace")
    assert llm_workspace_dock is not None
    assert llm_workspace_dock.windowTitle() == "LLM Workspace"
    
    # Check Python console dock
    python_console_dock = main_window.findChild(QDockWidget, "PythonConsole")
    assert python_console_dock is not None
    assert python_console_dock.windowTitle() == "Python Console"

@pytest.mark.parametrize("file_name", [
    "test.py",
    "test.txt",
    "test.md"
])
def test_open_file(main_window, qtbot, temp_dir, file_name):
    """Test file opening functionality"""
    file_path = temp_dir / file_name
    file_path.touch()
    
    main_window.open_file(file_path)
    current_widget = main_window.tab_widget.currentWidget()
    assert current_widget is not None
    assert isinstance(current_widget, CodeEditor)
    assert str(current_widget.file_path) == str(file_path)

def test_save_file(main_window, qtbot, temp_dir):
    """Test file saving functionality"""
    test_file = temp_dir / "test_save.py"
    test_content = "print('Hello, World!')"
    
    # Create a new file
    main_window.open_file(test_file)
    editor = main_window.tab_widget.currentWidget()
    editor.setPlainText(test_content)
    
    # Save the file
    main_window.save_file()
    
    # Verify file contents
    assert test_file.read_text() == test_content

def test_style_application(main_window):
    """Test style manager initialization and application"""
    # Verify style manager exists
    assert main_window.style_manager is not None
    
    # Verify it's the correct type
    from src.ui.styles.style_manager import StyleManager
    assert isinstance(main_window.style_manager, StyleManager)
