"""Integration tests for main window."""
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.ui.main_window import MainWindow

@pytest.fixture
def main_window(qtbot):
    """Create main window fixture."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def test_main_window_creation(main_window):
    """Test main window creation."""
    assert main_window is not None
    
def test_dock_widgets_creation(main_window):
    """Test dock widgets creation."""
    # Check all dock widgets are created
    assert main_window.project_explorer is not None
    assert main_window.git_panel is not None
    assert main_window.llm_workspace is not None
    assert main_window.ml_workspace is not None
    assert main_window.network_visualizer is not None
    assert main_window.output_panel is not None
    assert main_window.resource_viewer is not None
    assert main_window.console is not None
    assert main_window.training_visualizer is not None
    assert main_window.performance_monitor is not None
    
def test_dock_widget_visibility(main_window):
    """Test initial dock widget visibility."""
    # Left docks should be visible
    assert main_window.dock_manager.get_dock("project_explorer").isVisible()
    assert main_window.dock_manager.get_dock("resources").isVisible()
    
    # Bottom docks - output and console visible, git hidden
    assert main_window.dock_manager.get_dock("output").isVisible()
    assert main_window.dock_manager.get_dock("console").isVisible()
    assert not main_window.dock_manager.get_dock("git").isVisible()
    
    # Right docks should be hidden initially
    assert not main_window.dock_manager.get_dock("llm").isVisible()
    assert not main_window.dock_manager.get_dock("ml").isVisible()
    assert not main_window.dock_manager.get_dock("network").isVisible()
    assert not main_window.dock_manager.get_dock("training").isVisible()
    assert not main_window.dock_manager.get_dock("performance").isVisible()
    
def test_menu_actions(main_window):
    """Test menu actions existence."""
    # File menu
    file_menu = main_window.menu_manager.get_menu("file")
    assert file_menu is not None
    assert main_window.menu_manager.get_action("file", "new_project") is not None
    assert main_window.menu_manager.get_action("file", "open_project") is not None
    assert main_window.menu_manager.get_action("file", "close_project") is not None
    assert main_window.menu_manager.get_action("file", "settings") is not None
    assert main_window.menu_manager.get_action("file", "exit") is not None
    
    # View menu
    view_menu = main_window.menu_manager.get_menu("view")
    assert view_menu is not None
    assert main_window.menu_manager.get_action("view", "toggle_project_explorer") is not None
    assert main_window.menu_manager.get_action("view", "toggle_resources") is not None
    assert main_window.menu_manager.get_action("view", "toggle_output") is not None
    assert main_window.menu_manager.get_action("view", "toggle_console") is not None
    assert main_window.menu_manager.get_action("view", "toggle_git") is not None
    assert main_window.menu_manager.get_action("view", "toggle_llm") is not None
    assert main_window.menu_manager.get_action("view", "toggle_ml") is not None
    assert main_window.menu_manager.get_action("view", "toggle_network") is not None
    assert main_window.menu_manager.get_action("view", "toggle_training") is not None
    assert main_window.menu_manager.get_action("view", "toggle_performance") is not None
    
def test_toggle_dock_visibility(qtbot, main_window):
    """Test toggling dock widget visibility."""
    # Toggle output panel
    output_action = main_window.menu_manager.get_action("view", "toggle_output")
    assert output_action.isChecked()
    
    qtbot.mouseClick(output_action, Qt.MouseButton.LeftButton)
    assert not main_window.dock_manager.get_dock("output").isVisible()
    assert not output_action.isChecked()
    
    qtbot.mouseClick(output_action, Qt.MouseButton.LeftButton)
    assert main_window.dock_manager.get_dock("output").isVisible()
    assert output_action.isChecked()
    
def test_project_signals(main_window):
    """Test project-related signals."""
    # Check signals are connected
    assert main_window.project_explorer.project_loaded.receivers(main_window.project_explorer.project_loaded) > 0
    assert main_window.project_explorer.project_closed.receivers(main_window.project_explorer.project_closed) > 0
    
def test_settings_dialog(qtbot, main_window):
    """Test settings dialog."""
    # Open settings
    settings_action = main_window.menu_manager.get_action("file", "settings")
    qtbot.mouseClick(settings_action, Qt.MouseButton.LeftButton)
    
    # Check dialog is created
    assert main_window.settings_dialog is not None
