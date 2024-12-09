"""Main application window with enhanced lazy loading and caching."""
from typing import Dict, Optional, Set
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QDockWidget, QMenuBar,
    QStatusBar, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging
from pathlib import Path
from ..utils.lazy_loading import LoadPriority, component_loader
from ..utils.caching import cache
from .performance_monitor import get_performance_monitor
from .project_explorer.explorer import ProjectExplorer
from .code_editor import CodeEditor
from .components.output.output_panel import OutputPanel
from .components.resource.resource_viewer import ResourceViewer
from .styles.theme_manager import ThemeManager
from .git_panel import GitPanel
from .llm_workspace import LLMWorkspace
from .ml_workspace import MLWorkspace
from .network_visualizer import NetworkVisualizer
from .python_console.console_widget import ConsoleWidget
from .settings.dialog import SettingsDialog
from .training.visualizer import TrainingVisualizer

class DockManager:
    """Manages dock widgets with lazy loading."""
    
    def __init__(self, main_window: QMainWindow):
        """Initialize dock manager.
        
        Args:
            main_window: Parent main window
        """
        self.main_window = main_window
        self._docks: Dict[str, QDockWidget] = {}
        self._dock_states: Dict[str, bool] = {}
        
        # Register with component loader
        component_loader.register_component(
            "dock_manager",
            lambda: self,
            priority=LoadPriority.HIGH,
            size_estimate=1024 * 1024  # 1MB estimate
        )
        
    def register_dock(
        self,
        name: str,
        widget: QWidget,
        title: str,
        area: Qt.DockWidgetArea,
        visible: bool = True
    ):
        """Register a dock widget.
        
        Args:
            name: Unique dock identifier
            widget: Widget to dock
            title: Dock title
            area: Dock area
            visible: Initial visibility
        """
        dock = QDockWidget(title, self.main_window)
        dock.setWidget(widget)
        dock.setObjectName(name)
        
        # Store in cache for quick access
        cache.set(
            f"dock_{name}",
            dock,
            weak=True,
            priority=LoadPriority.HIGH
        )
        
        self._docks[name] = dock
        self._dock_states[name] = visible
        self.main_window.addDockWidget(area, dock)
        
        if not visible:
            dock.hide()
            
    def get_dock(self, name: str) -> Optional[QDockWidget]:
        """Get dock widget by name.
        
        Args:
            name: Dock identifier
            
        Returns:
            Dock widget or None if not found
        """
        # Try cache first
        dock = cache.get(f"dock_{name}")
        if dock is not None:
            return dock
            
        # Fall back to stored docks
        return self._docks.get(name)
        
    def show_dock(self, name: str):
        """Show dock widget.
        
        Args:
            name: Dock identifier
        """
        if dock := self.get_dock(name):
            dock.show()
            self._dock_states[name] = True
            
    def hide_dock(self, name: str):
        """Hide dock widget.
        
        Args:
            name: Dock identifier
        """
        if dock := self.get_dock(name):
            dock.hide()
            self._dock_states[name] = False
            
    def toggle_dock(self, name: str):
        """Toggle dock visibility.
        
        Args:
            name: Dock identifier
        """
        if dock := self.get_dock(name):
            if dock.isVisible():
                self.hide_dock(name)
            else:
                self.show_dock(name)
                
    def save_state(self) -> Dict:
        """Save dock states.
        
        Returns:
            Dict with dock states
        """
        return {
            'states': self._dock_states.copy(),
            'geometry': self.main_window.saveGeometry().data()
        }
        
    def restore_state(self, state: Dict):
        """Restore dock states.
        
        Args:
            state: Previously saved state
        """
        if not state:
            return
            
        # Restore geometry
        if geometry := state.get('geometry'):
            self.main_window.restoreGeometry(geometry)
            
        # Restore dock states
        if states := state.get('states'):
            for name, visible in states.items():
                if visible:
                    self.show_dock(name)
                else:
                    self.hide_dock(name)

class MenuManager:
    """Manages application menus with lazy loading."""
    
    def __init__(self, main_window: QMainWindow):
        """Initialize menu manager.
        
        Args:
            main_window: Parent main window
        """
        self.main_window = main_window
        self.menubar = main_window.menuBar()
        self._menus: Dict[str, Dict] = {}
        
        # Register with component loader
        component_loader.register_component(
            "menu_manager",
            lambda: self,
            priority=LoadPriority.HIGH,
            size_estimate=512 * 1024  # 512KB estimate
        )
        
    def create_menu(self, name: str, title: str) -> None:
        """Create a new menu.
        
        Args:
            name: Menu identifier
            title: Menu title
        """
        menu = self.menubar.addMenu(title)
        self._menus[name] = {
            'menu': menu,
            'actions': {}
        }
        
    def add_action(
        self,
        menu_name: str,
        action_name: str,
        text: str,
        callback,
        shortcut: str = None,
        checkable: bool = False,
        checked: bool = False
    ) -> None:
        """Add action to menu.
        
        Args:
            menu_name: Menu identifier
            action_name: Action identifier
            text: Action text
            callback: Action callback
            shortcut: Optional keyboard shortcut
            checkable: Whether action is checkable
            checked: Initial checked state
        """
        if menu_name not in self._menus:
            return
            
        menu_data = self._menus[menu_name]
        action = menu_data['menu'].addAction(text)
        
        if shortcut:
            action.setShortcut(shortcut)
        if checkable:
            action.setCheckable(True)
            action.setChecked(checked)
            
        action.triggered.connect(callback)
        menu_data['actions'][action_name] = action
        
    def get_action(self, menu_name: str, action_name: str):
        """Get menu action.
        
        Args:
            menu_name: Menu identifier
            action_name: Action identifier
            
        Returns:
            Action or None if not found
        """
        return self._menus.get(menu_name, {}).get('actions', {}).get(action_name)

class MainWindow(QMainWindow):
    """Enhanced main application window."""
    
    # Signals
    project_loaded = pyqtSignal(str)  # Project path
    project_closed = pyqtSignal()
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        # Register with component loader
        component_loader.register_component(
            "main_window",
            lambda: self,
            priority=LoadPriority.CRITICAL,
            size_estimate=20 * 1024 * 1024  # 20MB estimate
        )
        
        self._init_window()
        self._init_managers()
        self._init_central_widget()
        self._init_docks()
        self._init_menus()
        self._init_statusbar()
        self._init_theme()
        
        # Show window
        self.show()
        
    def _init_window(self):
        """Initialize window properties."""
        self.setWindowTitle("NeuralForge")
        self.setMinimumSize(800, 600)
        
    def _init_managers(self):
        """Initialize component managers."""
        # Create managers
        self.dock_manager = DockManager(self)
        self.menu_manager = MenuManager(self)
        self.theme_manager = ThemeManager(self)
        self.settings_dialog = None
        
        # Initialize project explorer
        self.project_explorer = None  # Will be initialized in _init_docks
        
        # Connect signals
        self.project_loaded = pyqtSignal(str)
        self.project_closed = pyqtSignal()
        
    def _init_central_widget(self):
        """Initialize central widget."""
        self.code_editor = CodeEditor(self)
        self.setCentralWidget(self.code_editor)
        
    def _init_docks(self):
        """Initialize dock widgets."""
        # Project Explorer
        self.project_explorer = ProjectExplorer(self)
        self.dock_manager.register_dock(
            "project_explorer",
            self.project_explorer,
            "Project Explorer",
            Qt.DockWidgetArea.LeftDockWidgetArea
        )
        
        # Connect project explorer signals
        self.project_explorer.project_loaded.connect(self._on_project_loaded)
        self.project_explorer.project_closed.connect(self._on_project_closed)
        
        # Git Panel
        self.git_panel = GitPanel(self)
        self.dock_manager.register_dock(
            "git",
            self.git_panel,
            "Git",
            Qt.DockWidgetArea.BottomDockWidgetArea,
            visible=False
        )
        
        # LLM Workspace
        self.llm_workspace = LLMWorkspace(self)
        self.dock_manager.register_dock(
            "llm",
            self.llm_workspace,
            "LLM Workspace",
            Qt.DockWidgetArea.RightDockWidgetArea,
            visible=False
        )
        
        # ML Workspace
        self.ml_workspace = MLWorkspace(self)
        self.dock_manager.register_dock(
            "ml",
            self.ml_workspace,
            "ML Workspace",
            Qt.DockWidgetArea.RightDockWidgetArea,
            visible=False
        )
        
        # Network Visualizer
        self.network_visualizer = NetworkVisualizer(self)
        self.dock_manager.register_dock(
            "network",
            self.network_visualizer,
            "Network Visualizer",
            Qt.DockWidgetArea.RightDockWidgetArea,
            visible=False
        )
        
        # Output panel
        self.output_panel = OutputPanel(self)
        self.dock_manager.register_dock(
            "output",
            self.output_panel,
            "Output",
            Qt.DockWidgetArea.BottomDockWidgetArea
        )
        
        # Resource viewer
        self.resource_viewer = ResourceViewer(self)
        self.dock_manager.register_dock(
            "resources",
            self.resource_viewer,
            "Resources",
            Qt.DockWidgetArea.LeftDockWidgetArea
        )
        
        # Python Console
        self.console = ConsoleWidget(self)
        self.dock_manager.register_dock(
            "console",
            self.console,
            "Python Console",
            Qt.DockWidgetArea.BottomDockWidgetArea
        )
        
        # Training Visualizer
        self.training_visualizer = TrainingVisualizer(self)
        self.dock_manager.register_dock(
            "training",
            self.training_visualizer,
            "Training Progress",
            Qt.DockWidgetArea.RightDockWidgetArea,
            visible=False
        )
        
        # Performance monitor
        self.performance_monitor = get_performance_monitor(self)
        self.dock_manager.register_dock(
            "performance",
            self.performance_monitor,
            "Performance",
            Qt.DockWidgetArea.RightDockWidgetArea,
            visible=False
        )
        
    def _init_menus(self):
        """Initialize menus."""
        # File menu
        self.menu_manager.create_menu("file", "&File")
        self.menu_manager.add_action(
            "file", "new_project",
            "New Project...",
            self._on_new_project,
            "Ctrl+Shift+N"
        )
        self.menu_manager.add_action(
            "file", "open_project",
            "Open Project...",
            self._on_open_project,
            "Ctrl+Shift+O"
        )
        self.menu_manager.add_action(
            "file", "close_project",
            "Close Project",
            self._on_close_project
        )
        self.menu_manager.add_action(
            "file", "settings",
            "Settings...",
            self._on_settings,
            "Ctrl+,"
        )
        self.menu_manager.add_action(
            "file", "exit",
            "Exit",
            self.close,
            "Alt+F4"
        )
        
        # View menu
        self.menu_manager.create_menu("view", "&View")
        
        # Left dock widgets
        self.menu_manager.add_action(
            "view", "toggle_project_explorer",
            "Project Explorer",
            lambda: self.dock_manager.toggle_dock("project_explorer"),
            checkable=True,
            checked=True
        )
        self.menu_manager.add_action(
            "view", "toggle_resources",
            "Resource Viewer",
            lambda: self.dock_manager.toggle_dock("resources"),
            checkable=True,
            checked=True
        )
        
        # Bottom dock widgets
        self.menu_manager.add_action(
            "view", "toggle_output",
            "Output Panel",
            lambda: self.dock_manager.toggle_dock("output"),
            checkable=True,
            checked=True
        )
        self.menu_manager.add_action(
            "view", "toggle_console",
            "Python Console",
            lambda: self.dock_manager.toggle_dock("console"),
            checkable=True,
            checked=True
        )
        self.menu_manager.add_action(
            "view", "toggle_git",
            "Git Panel",
            lambda: self.dock_manager.toggle_dock("git"),
            checkable=True,
            checked=False
        )
        
        # Right dock widgets
        self.menu_manager.add_action(
            "view", "toggle_llm",
            "LLM Workspace",
            lambda: self.dock_manager.toggle_dock("llm"),
            checkable=True,
            checked=False
        )
        self.menu_manager.add_action(
            "view", "toggle_ml",
            "ML Workspace",
            lambda: self.dock_manager.toggle_dock("ml"),
            checkable=True,
            checked=False
        )
        self.menu_manager.add_action(
            "view", "toggle_network",
            "Network Visualizer",
            lambda: self.dock_manager.toggle_dock("network"),
            checkable=True,
            checked=False
        )
        self.menu_manager.add_action(
            "view", "toggle_training",
            "Training Progress",
            lambda: self.dock_manager.toggle_dock("training"),
            checkable=True,
            checked=False
        )
        self.menu_manager.add_action(
            "view", "toggle_performance",
            "Performance Monitor",
            lambda: self.dock_manager.toggle_dock("performance"),
            checkable=True,
            checked=False
        )
        
    def _init_statusbar(self):
        """Initialize status bar."""
        self.statusBar().showMessage("Ready")
        
    def _init_theme(self):
        """Initialize theme."""
        self.theme_manager.apply_theme()
        
    def _on_new_project(self):
        """Handle new project action."""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            directory = dialog.selectedFiles()[0]
            self.project_explorer.create_project(Path(directory))
            
    def _on_open_project(self):
        """Handle open project action."""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            directory = dialog.selectedFiles()[0]
            self.project_explorer.open_project(Path(directory))
            
    def _on_close_project(self):
        """Handle close project action."""
        self.project_explorer.close_project()
        
    def _on_project_loaded(self, path: str):
        """Handle project loaded event.
        
        Args:
            path: Project path
        """
        self.setWindowTitle(f"NeuralForge - {path}")
        self.statusBar().showMessage(f"Project loaded: {path}")
        self.project_loaded.emit(path)
        
    def _on_project_closed(self):
        """Handle project closed event."""
        self.setWindowTitle("NeuralForge")
        self.statusBar().showMessage("Project closed")
        self.project_closed.emit()
        
    def _on_settings(self):
        """Handle settings action."""
        dialog = SettingsDialog(self)
        dialog.exec()
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Save window state
        state = self.dock_manager.save_state()
        cache.set(
            "window_state",
            state,
            priority=LoadPriority.HIGH
        )
        
        # Close project
        self.project_explorer.close_project()
        
        # Accept close event
        event.accept()

# Create global instance
main_window = None

def get_main_window() -> MainWindow:
    """Get or create main window instance."""
    global main_window
    if main_window is None:
        main_window = MainWindow()
    return main_window
