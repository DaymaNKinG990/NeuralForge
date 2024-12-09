"""Tests for the main window of the NeuralForge application."""
import os
import pytest
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.ui.main_window import MainWindow
from src.utils.settings import Settings
from src.utils.theme_manager import ThemeManager
from src.utils.project_manager import ProjectManager
from src.utils.git_manager import GitManager
from src.utils.performance_tracker import PerformanceTracker

@pytest.fixture
def app(qtbot):
    """Create a Qt application."""
    return QApplication.instance() or QApplication([])

@pytest.fixture
def main_window(qtbot, app):
    """Create the main window."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def test_main_window_creation(main_window):
    """Test that the main window is created correctly."""
    assert isinstance(main_window, QMainWindow)
    assert main_window.windowTitle() == "NeuralForge"
    assert main_window.size().width() >= 1200
    assert main_window.size().height() >= 800

def test_managers_initialization(main_window):
    """Test that all managers are initialized correctly."""
    assert isinstance(main_window.settings, Settings)
    assert isinstance(main_window.theme_manager, ThemeManager)
    assert isinstance(main_window.project_manager, ProjectManager)
    assert isinstance(main_window.git_manager, GitManager)
    assert isinstance(main_window.performance_tracker, PerformanceTracker)

def test_ui_components_initialization(main_window):
    """Test that all UI components are initialized correctly."""
    # Test dock manager
    assert main_window.dock_manager is not None
    assert len(main_window.dock_manager.dock_widgets) > 0
    
    # Test menu manager
    assert main_window.menu_manager is not None
    assert main_window.menuBar() is not None
    
    # Test tab manager
    assert main_window.tab_manager is not None
    
    # Test toolbar manager
    assert main_window.toolbar_manager is not None
    assert len(main_window.toolBar().actions()) > 0

def test_central_widget_initialization(main_window):
    """Test that the central widget is initialized correctly."""
    assert main_window.centralWidget() is not None
    assert main_window.main_splitter is not None
    assert main_window.project_explorer is not None
    assert main_window.code_editor is not None

def test_dock_widgets_initialization(main_window):
    """Test that all dock widgets are initialized correctly."""
    # Test performance monitor
    assert main_window.performance_monitor is not None
    assert main_window.performance_monitor.isVisible()
    
    # Test Python console
    assert main_window.python_console is not None
    assert main_window.python_console.isVisible()
    
    # Test Git panel
    assert main_window.git_panel is not None
    assert main_window.git_panel.isVisible()
    
    # Test LLM workspace
    assert main_window.llm_workspace is not None
    assert main_window.llm_workspace.isVisible()
    
    # Test ML workspace
    assert main_window.ml_workspace is not None
    assert main_window.ml_workspace.isVisible()
    
    # Test Network visualizer
    assert main_window.network_visualizer is not None
    assert main_window.network_visualizer.isVisible()
    
    # Test Training visualizer
    assert main_window.training_visualizer is not None
    assert main_window.training_visualizer.isVisible()

def test_theme_toggle(main_window, qtbot):
    """Test theme toggling functionality."""
    initial_theme = main_window.settings.value('theme/type', 'dark')
    main_window.toggle_theme()
    new_theme = main_window.settings.value('theme/type', 'dark')
    assert initial_theme != new_theme
    assert new_theme in ['dark', 'light']

def test_project_loading(main_window, tmp_path, qtbot):
    """Test project loading functionality."""
    # Create a temporary project
    project_path = tmp_path / "test_project"
    project_path.mkdir()
    
    # Load project
    main_window.project_loaded.emit(str(project_path))
    
    # Check window title
    assert main_window.windowTitle() == f"NeuralForge - {project_path}"
    
    # Check project explorer
    assert main_window.project_explorer.root_path == str(project_path)
    
    # Check performance tracking
    assert main_window.performance_tracker.is_tracking

def test_project_closing(main_window, qtbot):
    """Test project closing functionality."""
    # Close project
    main_window.project_closed.emit()
    
    # Check window title
    assert main_window.windowTitle() == "NeuralForge"
    
    # Check project explorer
    assert main_window.project_explorer.model().rowCount() == 0
    
    # Check performance tracking
    assert not main_window.performance_tracker.is_tracking

def test_settings_change(main_window, qtbot):
    """Test settings change handling."""
    new_settings = {
        'theme/type': 'light',
        'editor/font_family': 'Consolas',
        'editor/font_size': 12
    }
    
    # Change settings
    main_window.settings_changed.emit(new_settings)
    
    # Check settings were applied
    assert main_window.settings.value('theme/type') == 'light'
    assert main_window.settings.value('editor/font_family') == 'Consolas'
    assert main_window.settings.value('editor/font_size') == 12

def test_window_close_handling(main_window, qtbot, monkeypatch):
    """Test window close event handling."""
    # Mock QMessageBox.question to return Yes
    def mock_question(*args, **kwargs):
        return QMessageBox.StandardButton.Yes
    monkeypatch.setattr(QMessageBox, 'question', mock_question)
    
    # Trigger close event
    main_window.close()
    
    # Check performance tracking stopped
    assert not main_window.performance_tracker.is_tracking

def test_performance_monitoring(main_window, qtbot):
    """Test performance monitoring functionality."""
    # Start monitoring
    main_window.performance_tracker.start_tracking()
    assert main_window.performance_tracker.is_tracking
    
    # Generate some metrics
    test_metrics = {
        'cpu_usage': 50.0,
        'memory_usage': 1024,
        'disk_usage': 512
    }
    main_window.performance_tracker.metrics_updated.emit(test_metrics)
    
    # Check metrics were updated in monitor
    assert main_window.performance_monitor.current_metrics == test_metrics

def test_keyboard_shortcuts(main_window, qtbot):
    """Test keyboard shortcuts."""
    # Test new file shortcut
    QTest.keySequence(main_window, QKeySequence.StandardKey.New)
    assert main_window.tab_manager.count() > 0
    
    # Test save shortcut
    QTest.keySequence(main_window, QKeySequence.StandardKey.Save)
    
    # Test close tab shortcut
    QTest.keySequence(main_window, QKeySequence.StandardKey.Close)
    assert main_window.tab_manager.count() == 0

def test_drag_and_drop(main_window, qtbot, tmp_path):
    """Test drag and drop functionality."""
    # Create a test file
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    # Simulate drag and drop
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(str(test_file))])
    
    drag_event = QDragEnterEvent(
        QPoint(0, 0),
        Qt.DropAction.CopyAction,
        mime_data,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    main_window.dragEnterEvent(drag_event)
    assert drag_event.isAccepted()
    
    drop_event = QDropEvent(
        QPoint(0, 0),
        Qt.DropAction.CopyAction,
        mime_data,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    main_window.dropEvent(drop_event)
    
    # Check file was opened
    assert str(test_file) in main_window.open_files

def test_memory_management(main_window, qtbot):
    """Test memory management during widget creation and destruction."""
    import gc
    import weakref
    
    # Create a reference to track
    widget_ref = weakref.ref(main_window.code_editor)
    
    # Delete widget
    main_window.code_editor.deleteLater()
    main_window.code_editor = None
    
    # Force garbage collection
    QApplication.processEvents()
    gc.collect()
    
    # Check widget was properly destroyed
    assert widget_ref() is None

def test_error_handling(main_window, qtbot, caplog):
    """Test error handling in various scenarios."""
    # Test invalid file open
    main_window._open_file("nonexistent_file.py")
    assert "Could not read file" in caplog.text
    
    # Test invalid settings
    main_window.settings_changed.emit({'invalid_key': 'invalid_value'})
    assert "Invalid setting" in caplog.text
    
    # Test invalid theme
    main_window.set_theme('invalid_theme')
    assert "Invalid theme type" in caplog.text

def test_main_window_creation_lazy(main_window):
    """Test main window creation with lazy loading."""
    assert main_window is not None
    assert main_window.windowTitle() == "NeuralForge"
    assert main_window.isVisible()

def test_dock_manager_lazy(main_window):
    """Test dock manager functionality with lazy loading."""
    # Check dock manager initialization
    assert main_window.dock_manager is not None
    
    # Verify dock registration with component loader
    component = component_loader.get_component("dock_manager")
    assert component is not None
    assert component == main_window.dock_manager
    
    # Test dock widget operations
    dock = main_window.dock_manager.get_dock("output")
    assert dock is not None
    assert dock.isVisible()
    
    main_window.dock_manager.hide_dock("output")
    assert not dock.isVisible()
    
    main_window.dock_manager.show_dock("output")
    assert dock.isVisible()
    
    main_window.dock_manager.toggle_dock("output")
    assert not dock.isVisible()

def test_menu_manager_lazy(main_window):
    """Test menu manager functionality with lazy loading."""
    # Check menu manager initialization
    assert main_window.menu_manager is not None
    
    # Verify menu manager registration with component loader
    component = component_loader.get_component("menu_manager")
    assert component is not None
    assert component == main_window.menu_manager
    
    # Test menu actions
    action = main_window.menu_manager.get_action("view", "toggle_output")
    assert action is not None
    assert action.isCheckable()
    assert action.isChecked()

def test_project_operations_lazy(main_window, tmp_path):
    """Test project operations with lazy loading."""
    # Create test project
    project_path = tmp_path / "test_project"
    project_path.mkdir()
    
    # Test new project
    main_window._on_new_project()
    assert main_window.windowTitle() == "NeuralForge"
    
    # Test open project
    main_window._on_open_project()
    assert main_window.windowTitle() == "NeuralForge"
    
    # Test close project
    main_window._on_close_project()
    assert main_window.windowTitle() == "NeuralForge"

def test_window_state_caching_lazy(main_window):
    """Test window state caching with lazy loading."""
    # Save window state
    state = main_window.dock_manager.save_state()
    cache.set("window_state", state, priority=LoadPriority.HIGH)
    
    # Verify state is cached
    cached_state = cache.get("window_state")
    assert cached_state is not None
    assert cached_state == state
    
    # Test state restoration
    main_window.dock_manager.restore_state(cached_state)
    new_state = main_window.dock_manager.save_state()
    assert new_state == cached_state

def test_performance_monitor_lazy(main_window):
    """Test performance monitor integration with lazy loading."""
    # Check performance monitor initialization
    assert main_window.performance_monitor is not None
    
    # Test visibility toggling
    dock = main_window.dock_manager.get_dock("performance")
    assert dock is not None
    assert not dock.isVisible()  # Should be hidden by default
    
    main_window.dock_manager.show_dock("performance")
    assert dock.isVisible()

def test_resource_viewer_lazy(main_window):
    """Test resource viewer integration with lazy loading."""
    # Check resource viewer initialization
    assert main_window.resource_viewer is not None
    
    # Test visibility
    dock = main_window.dock_manager.get_dock("resources")
    assert dock is not None
    assert dock.isVisible()  # Should be visible by default

def test_code_editor_lazy(main_window):
    """Test code editor integration with lazy loading."""
    # Check code editor initialization
    assert main_window.code_editor is not None
    assert main_window.centralWidget() == main_window.code_editor

def test_output_panel_lazy(main_window):
    """Test output panel integration with lazy loading."""
    # Check output panel initialization
    assert main_window.output_panel is not None
    
    # Test visibility
    dock = main_window.dock_manager.get_dock("output")
    assert dock is not None
    assert dock.isVisible()  # Should be visible by default

def test_theme_manager_lazy(main_window):
    """Test theme manager integration with lazy loading."""
    # Check theme manager initialization
    assert main_window.theme_manager is not None
    
    # Test theme toggle
    action = main_window.menu_manager.get_action("view", "toggle_theme")
    assert action is not None
    action.trigger()  # Toggle theme

def test_singleton_behavior_lazy():
    """Test main window singleton behavior with lazy loading."""
    window1 = get_main_window()
    window2 = get_main_window()
    assert window1 is window2  # Should return same instance

def test_component_registration_lazy(main_window):
    """Test component registration with lazy loading."""
    # Check main window registration
    component = component_loader.get_component("main_window")
    assert component is not None
    assert component == main_window
    assert component_loader.get_priority("main_window") == LoadPriority.CRITICAL

def test_cleanup_lazy(main_window):
    """Test cleanup on window close with lazy loading."""
    # Save initial state
    initial_state = main_window.dock_manager.save_state()
    
    # Close window
    main_window.close()
    
    # Verify state was saved to cache
    cached_state = cache.get("window_state")
    assert cached_state is not None
    assert cached_state == initial_state
