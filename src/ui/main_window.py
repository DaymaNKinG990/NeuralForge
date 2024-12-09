from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QDockWidget, 
                             QMenuBar, QStatusBar, QFileDialog, QMessageBox,
                             QVBoxLayout, QWidget, QToolBar, QLabel, QApplication)
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFont, QPaintEvent, QKeyEvent
from PyQt6.QtCore import Qt, QSize, QSettings, QTimer
from .code_editor import CodeEditor
from .components.file_tree_view import FileTreeView
from .project_explorer import ProjectExplorer
from .ml_workspace import MLWorkspace
from .llm_workspace import LLMWorkspace
from .python_console import PythonConsole
from .settings_dialog import SettingsDialog
from .git_panel import GitPanel
from .performance_monitor import PerformanceWidget
from ..utils.performance import (
    performance_monitor, file_cache, thread_pool, memory_tracker,
    AsyncWorker
)
from ..utils.caching import cache_manager, search_cache
from ..utils.lazy_loading import lazy_import, LazyWidget, component_loader
from ..utils.profiler import profiler
from .styles.theme_manager import ThemeManager
from .styles.adaptive_styles import AdaptiveStyles
from pathlib import Path
from typing import Union, Optional, Dict
import logging
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            self.logger = logging.getLogger(__name__)
            self.logger.debug("MainWindow initialization started")
            
            # Initialize theme manager
            self._theme_manager = ThemeManager()
            self._setup_theme()
            
            # Basic window setup
            self.setWindowTitle("NeuroForge IDE")
            self.setMinimumSize(1200, 800)
            self.logger.debug(f"Window size set to: {self.size()}")
            
            # Ensure window is visible
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
            self.setWindowState(Qt.WindowState.WindowActive)
            
            # Store open files and settings
            self.open_files = {}
            self._settings = QSettings('NeuralForge', 'IDE')
            
            # Initialize project root
            self.project_root = Path.cwd()
            self.logger.debug(f"Project root set to: {self.project_root}")
            
            # Setup UI components
            self._setup_ui()
            self._setup_actions()
            self._setup_menus()
            self._setup_toolbars()
            self._setup_statusbar()
            self._restore_window_state()
            
            self.logger.debug("MainWindow initialization completed")
            
        except Exception as e:
            self.logger.error(f"Error initializing MainWindow: {str(e)}", exc_info=True)
            raise

    def _setup_theme(self):
        """Настройка темы интерфейса"""
        # Apply theme to application palette
        self.setPalette(self._theme_manager.get_palette())
        
        # Apply base styles
        base_style = AdaptiveStyles.get_base_style(self._theme_manager)
        self.setStyleSheet(base_style)

    def _setup_ui(self):
        """Setup UI components"""
        try:
            # Track UI state
            self._ui_initialized = False
            self._workspace_states = {}
            
            # Create a container widget first
            container = QWidget()
            if not container:
                raise RuntimeError("Failed to create container widget")
            self.setCentralWidget(container)
            
            # Create layout for container
            layout = QVBoxLayout(container)
            layout.setContentsMargins(2, 2, 2, 2)  # Reduce margins
            layout.setSpacing(1)  # Minimal spacing between widgets
            
            # Central widget setup with error handling
            self.central_widget = QTabWidget()
            self.central_widget.setTabsClosable(True)
            self.central_widget.setMovable(True)
            self.central_widget.setDocumentMode(True)
            self.central_widget.setContentsMargins(0, 0, 0, 0)  # No margins
            self.central_widget.tabCloseRequested.connect(self._on_tab_close_requested)
            
            # Create file tree dock widget with language icons
            file_dock = QDockWidget("Files", self)
            file_dock.setObjectName("FilesDock")
            file_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea |
                                    Qt.DockWidgetArea.RightDockWidgetArea)
            file_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                                QDockWidget.DockWidgetFeature.DockWidgetFloatable)
            
            # Create file tree view with language icons
            self.file_tree = FileTreeView()
            self.file_tree.setContentsMargins(0, 0, 0, 0)  # No margins
            self.file_tree.file_selected.connect(self._on_file_selected)
            file_dock.setWidget(self.file_tree)
            
            # Add dock widget to main window
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, file_dock)
            
            layout.addWidget(self.central_widget)
            
            # Setup dock widgets with state tracking using QTimer
            QTimer.singleShot(0, self._setup_project_explorer)
            QTimer.singleShot(0, lambda: self._track_workspace_state('project_explorer'))
            
            QTimer.singleShot(100, self._setup_ml_workspace)
            QTimer.singleShot(100, lambda: self._track_workspace_state('ml_workspace'))
            
            QTimer.singleShot(200, self._setup_llm_workspace)
            QTimer.singleShot(200, lambda: self._track_workspace_state('llm_workspace'))
            
            QTimer.singleShot(300, self._setup_git_panel)
            QTimer.singleShot(300, lambda: self._track_workspace_state('git_panel'))
            
            QTimer.singleShot(400, self._setup_performance_monitor)
            QTimer.singleShot(400, lambda: self._track_workspace_state('performance_monitor'))
            
            QTimer.singleShot(500, self._setup_python_console)
            QTimer.singleShot(500, lambda: self._track_workspace_state('python_console'))
            
            # Apply component-specific styles
            QTimer.singleShot(600, self._apply_component_styles)
            
            QTimer.singleShot(700, self._mark_ui_initialized)
            
            QTimer.singleShot(800, self._setup_dock_layout)
            
        except Exception as e:
            self.logger.error(f"Error during UI setup: {str(e)}", exc_info=True)
            raise
            
    def _mark_ui_initialized(self):
        """Mark UI as initialized after all components are set up"""
        self._ui_initialized = True
        self.logger.debug("UI setup completed successfully")

    def _apply_component_styles(self):
        """Применение стилей к компонентам"""
        try:
            # Code editor style
            code_editor_style = AdaptiveStyles.get_code_editor_style(self._theme_manager)
            for widget in self.findChildren(CodeEditor):
                widget.setStyleSheet(code_editor_style)
            
            # Project explorer style
            if hasattr(self, 'project_explorer'):
                explorer_style = AdaptiveStyles.get_project_explorer_style(self._theme_manager)
                self.project_explorer.setStyleSheet(explorer_style)
            
            # Performance monitor style
            if hasattr(self, 'performance_widget'):
                monitor_style = AdaptiveStyles.get_performance_monitor_style(self._theme_manager)
                self.performance_widget.setStyleSheet(monitor_style)
            
            # Network visualizer style
            visualizer_style = AdaptiveStyles.get_network_visualizer_style(self._theme_manager)
            for workspace in self.findChildren(MLWorkspace):
                if hasattr(workspace, 'network_visualizer'):
                    workspace.network_visualizer.setStyleSheet(visualizer_style)
                    
        except Exception as e:
            self.logger.error(f"Error applying component styles: {str(e)}", exc_info=True)

    def _create_dock_widget(self, title: str, widget: QWidget, area: Qt.DockWidgetArea) -> QDockWidget:
        """Create a dock widget with theme support"""
        dock = QDockWidget(title, self)
        dock.setObjectName(f"{title.replace(' ', '')}Dock")
        dock.setWidget(widget)
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                        QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        
        # Set minimum sizes to prevent docks from becoming too small
        widget.setMinimumWidth(200)
        widget.setMinimumHeight(100)
        
        # Set content margins
        if hasattr(widget, 'layout'):
            if widget.layout():
                widget.layout().setContentsMargins(2, 2, 2, 2)
                widget.layout().setSpacing(1)
        
        self.addDockWidget(area, dock)
        return dock

    def _setup_dock_layout(self):
        """Setup initial dock widget layout"""
        try:
            # Split docks vertically in the right area
            self.splitDockWidget(self.ml_workspace_dock, 
                               self.llm_workspace_dock, 
                               Qt.Orientation.Vertical)
            
            # Split docks vertically in the left area
            self.splitDockWidget(self.project_explorer_dock,
                               self.git_dock,
                               Qt.Orientation.Vertical)
            
            # Add performance monitor to bottom
            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea,
                             self.performance_dock)
            
            # Add console to bottom
            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea,
                             self.console_dock)
            
            # Tab the bottom docks together
            self.tabifyDockWidget(self.performance_dock, self.console_dock)
            
        except Exception as e:
            self.logger.error(f"Error setting up dock layout: {str(e)}")

    def toggle_theme(self):
        """Переключение между темной и светлой темой"""
        current_type = self._settings.value('theme/type', 'dark')
        new_type = 'light' if current_type == 'dark' else 'dark'
        self._theme_manager.set_theme(new_type)
        self._setup_theme()
        self._apply_component_styles()
        self._settings.setValue('theme/type', new_type)

    def showEvent(self, event) -> None:
        """Override show event to add debugging"""
        super().showEvent(event)
        self.logger.debug(f"Show event - Window becoming visible")
        self.logger.debug(f"Window state after show: Visible={self.isVisible()}, Hidden={self.isHidden()}, Geometry={self.geometry()}")
        
    def hideEvent(self, event) -> None:
        """Override hide event to add debugging"""
        super().hideEvent(event)
        self.logger.debug(f"Hide event - Window becoming hidden")
        self.logger.debug(f"Window state after hide: Visible={self.isVisible()}, Hidden={self.isHidden()}, Geometry={self.geometry()}")
        
    def _register_components(self):
        """Register all lazy-loaded components."""
        try:
            component_loader.register_component(
                "project_explorer",
                lambda parent: ProjectExplorer(self.project_root, parent)
            )
            component_loader.register_component(
                "git_panel",
                lambda parent: GitPanel(self.project_root, parent=parent)
            )
            component_loader.register_component(
                "performance_monitor",
                lambda parent: PerformanceWidget(parent)
            )
            component_loader.register_component(
                "python_console",
                lambda parent: PythonConsole(parent)
            )
        except Exception as e:
            self.logger.error(f"Error registering components: {str(e)}", exc_info=True)
            raise

    def _init_dock_widgets(self) -> None:
        """Initialize all dock widgets."""
        try:
            # Project Explorer
            self.project_explorer_dock = QDockWidget("Project Explorer", self)
            self.project_explorer_dock.setObjectName("ProjectExplorerDock")
            self.project_explorer = ProjectExplorer(str(self.project_root), self)
            self.project_explorer_dock.setWidget(self.project_explorer)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.project_explorer_dock)
            
            # ML Workspace
            self.ml_workspace_dock = QDockWidget("ML Workspace", self)
            self.ml_workspace_dock.setObjectName("MLWorkspaceDock")
            self.ml_workspace = MLWorkspace(self)
            self.ml_workspace_dock.setWidget(self.ml_workspace)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ml_workspace_dock)
            
            # LLM Workspace
            self.llm_workspace_dock = QDockWidget("LLM Workspace", self)
            self.llm_workspace_dock.setObjectName("LLMWorkspaceDock")
            self.llm_workspace = LLMWorkspace(self)
            self.llm_workspace_dock.setWidget(self.llm_workspace)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.llm_workspace_dock)
            
            # Python Console
            self.python_console_dock = QDockWidget("Python Console", self)
            self.python_console_dock.setObjectName("PythonConsoleDock")
            self.python_console = PythonConsole(self)
            self.python_console_dock.setWidget(self.python_console)
            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.python_console_dock)
            
            # Git Panel
            self._init_git_panel()
            
            self.logger.debug("Dock widgets initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error in _init_dock_widgets: {str(e)}", exc_info=True)
            raise
            
    def _init_git_panel(self) -> None:
        """Initialize Git panel."""
        try:
            git_dock = QDockWidget("Git", self)
            git_dock.setObjectName("GitDock")
            self.git_panel = GitPanel(self.project_root, parent=self)
            git_dock.setWidget(self.git_panel)
            git_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                   Qt.DockWidgetArea.RightDockWidgetArea)
            git_dock.setWindowIcon(QIcon(str(self.icon_path / 'dock.svg')))
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, git_dock)
        except Exception as e:
            self.logger.error(f"Failed to initialize Git panel: {e}")
            
    def setup_tool_bar(self) -> None:
        """Setup the main toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # Add actions
        new_file_action = QAction(self._load_icon('code.svg'), "New File", self)
        new_file_action.setShortcut(QKeySequence.StandardKey.New)
        new_file_action.triggered.connect(self.new_file)
        toolbar.addAction(new_file_action)
        
        open_action = QAction(self._load_icon('folder.svg'), "Open File", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file_dialog)
        toolbar.addAction(open_action)
        
        save_action = QAction(self._load_icon('save.svg'), "Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        run_action = QAction(self._load_icon('play.svg'), "Run", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.run_current_file)
        toolbar.addAction(run_action)
        
        debug_action = QAction(self._load_icon('debug.svg'), "Debug", self)
        debug_action.setShortcut("F9")
        debug_action.triggered.connect(self.debug_current_file)
        toolbar.addAction(debug_action)
        
    def setup_status_bar(self) -> None:
        """Setup the status bar with cursor position and encoding information."""
        status_bar = QStatusBar()
        
        # Add status items
        self.cursor_position_label = QLabel("Ln 1, Col 1")
        status_bar.addPermanentWidget(self.cursor_position_label)
        
        self.encoding_label = QLabel("UTF-8")
        status_bar.addPermanentWidget(self.encoding_label)
        
        self.setStatusBar(status_bar)
        
    def setup_menu_bar(self) -> None:
        """Setup the main menu bar."""
        try:
            menubar = self.menuBar()
            
            # File Menu
            file_menu = menubar.addMenu('&File')
            
            new_action = file_menu.addAction('&New File')
            new_action.setShortcut('Ctrl+N')
            new_action.triggered.connect(self.new_file)
            
            open_action = file_menu.addAction('&Open File')
            open_action.setShortcut('Ctrl+O')
            open_action.triggered.connect(self.open_file_dialog)
            
            save_action = file_menu.addAction('&Save')
            save_action.setShortcut('Ctrl+S')
            save_action.triggered.connect(self.save_file)
            
            save_as_action = file_menu.addAction('Save &As...')
            save_as_action.setShortcut('Ctrl+Shift+S')
            save_as_action.triggered.connect(self.save_file_as)
            
            file_menu.addSeparator()
            
            exit_action = file_menu.addAction('E&xit')
            exit_action.setShortcut('Alt+F4')
            exit_action.triggered.connect(self.close)
            
            # Edit Menu
            edit_menu = menubar.addMenu('&Edit')
            
            undo_action = edit_menu.addAction('&Undo')
            undo_action.setShortcut('Ctrl+Z')
            
            redo_action = edit_menu.addAction('&Redo')
            redo_action.setShortcut('Ctrl+Y')
            
            edit_menu.addSeparator()
            
            cut_action = edit_menu.addAction('Cu&t')
            cut_action.setShortcut('Ctrl+X')
            
            copy_action = edit_menu.addAction('&Copy')
            copy_action.setShortcut('Ctrl+C')
            
            paste_action = edit_menu.addAction('&Paste')
            paste_action.setShortcut('Ctrl+V')
            
            # Tools Menu
            tools_menu = menubar.addMenu('&Tools')
            
            settings_action = tools_menu.addAction('&Settings')
            settings_action.triggered.connect(self.show_settings)
            
            # Help Menu
            help_menu = menubar.addMenu('&Help')
            
            about_action = help_menu.addAction('&About')
            about_action.triggered.connect(self.show_about)
            
            self.logger.debug("Menu bar setup completed")
            
        except Exception as e:
            self.logger.error(f"Error setting up menu bar: {str(e)}", exc_info=True)
            raise
            
    def show_settings(self):
        """Show the settings dialog."""
        try:
            self.logger.debug("Opening settings dialog")
            from .settings_dialog import SettingsDialog
            
            dialog = SettingsDialog(self)
            self.logger.debug("Settings dialog created")
            
            if dialog.exec():
                self.logger.debug("Settings dialog accepted, applying settings")
                self.apply_settings()
            else:
                self.logger.debug("Settings dialog cancelled")
                
        except Exception as e:
            self.logger.error(f"Error showing settings dialog: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open settings: {str(e)}")
            
    def apply_settings(self):
        """Apply settings from QSettings to the application."""
        try:
            self.logger.debug("Starting to apply settings")
            settings = QSettings('NeuroForge', 'IDE')
            
            # Apply font settings
            font_family = settings.value('editor/font_family', 'Consolas')
            font_size = int(settings.value('editor/font_size', 11))
            font = QFont(font_family, font_size)
            self.logger.debug(f"Applying font: {font_family}, size: {font_size}")
            
            # Apply color settings
            bg_color = settings.value('editor/background_color', '#2D2D2D')
            text_color = settings.value('editor/text_color', '#FFFFFF')
            self.logger.debug(f"Applying colors - background: {bg_color}, text: {text_color}")
            
            # Apply editor behavior settings
            auto_indent = settings.value('editor/auto_indent', True, type=bool)
            show_line_numbers = settings.value('editor/show_line_numbers', True, type=bool)
            tab_width = settings.value('editor/tab_width', 4, type=int)
            self.logger.debug(f"Editor behavior - auto indent: {auto_indent}, line numbers: {show_line_numbers}, tab width: {tab_width}")
            
            # Apply settings to all open editors
            editor_count = self.tab_widget.count()
            self.logger.debug(f"Applying settings to {editor_count} open editors")
            
            for i in range(editor_count):
                editor = self.tab_widget.widget(i)
                editor_name = self.tab_widget.tabText(i)
                self.logger.debug(f"Applying settings to editor: {editor_name}")
                
                try:
                    if hasattr(editor, 'setFont'):
                        editor.setFont(font)
                        
                    if hasattr(editor, 'setPalette'):
                        palette = editor.palette()
                        palette.setColor(QPalette.ColorRole.Base, QColor(bg_color))
                        palette.setColor(QPalette.ColorRole.Text, QColor(text_color))
                        editor.setPalette(palette)
                        
                    if hasattr(editor, 'setAutoIndent'):
                        editor.setAutoIndent(auto_indent)
                        
                    if hasattr(editor, 'setShowLineNumbers'):
                        editor.setShowLineNumbers(show_line_numbers)
                        
                    if hasattr(editor, 'setTabWidth'):
                        editor.setTabWidth(tab_width)
                        
                    self.logger.debug(f"Successfully applied all settings to editor: {editor_name}")
                    
                except Exception as e:
                    self.logger.error(f"Error applying settings to editor {editor_name}: {str(e)}")
            
            self.logger.debug("Settings applied successfully to all editors")
            
        except Exception as e:
            self.logger.error(f"Error applying settings: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {str(e)}")
            
    def new_project(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if dir_path:
            self.project_explorer.set_root_path(dir_path)
            
    def open_project(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Open Project")
        if dir_path:
            self.project_explorer.set_root_path(dir_path)
            
    def new_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "New File")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    pass
                self.open_file(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create file: {str(e)}")
                
    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if file_path:
            self.open_file(file_path)
            
    def open_file(self, file_path: Union[str, Path]) -> None:
        """Open a file in the editor.
        
        Args:
            file_path: Path to the file to open
        """
        try:
            # Convert to Path object if string
            file_path = Path(file_path) if isinstance(file_path, str) else file_path
            
            # Check if file is already open
            if str(file_path) in self.open_files:
                self.tab_widget.setCurrentWidget(self.open_files[str(file_path)])
                return
                
            # Create new editor
            editor = CodeEditor(self)
            
            try:
                # Read file content if it exists
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    editor.setPlainText(content)
                else:
                    # Create empty file
                    file_path.touch()
                
                # Add to tab widget
                file_name = file_path.name
                index = self.tab_widget.addTab(editor, file_name)
                self.tab_widget.setCurrentIndex(index)
                
                # Store file info
                self.open_files[str(file_path)] = editor
                editor.file_path = file_path
                
                self.logger.info(f"File opened successfully: {file_path}")
                
            except Exception as e:
                self.logger.error(f"Error reading file {file_path}: {str(e)}")
                QMessageBox.critical(self, "Error", f"Could not open file: {str(e)}")
                editor.deleteLater()
                
        except Exception as e:
            self.logger.error(f"Error in open_file: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def save_file(self) -> None:
        """Save the current file in the editor."""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, CodeEditor):
            file_path = None
            for path, editor in self.open_files.items():
                if editor == current_widget:
                    file_path = path
                    break
                    
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(current_widget.toPlainText())
                    self.statusBar().showMessage(f"File saved: {file_path}", 2000)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
            else:
                self.save_file_as()

    def save_file_as(self) -> None:
        """Save the current file with a new name."""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, CodeEditor):
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File As")
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(current_widget.toPlainText())
                    current_widget.file_path = file_path
                    self.statusBar().showMessage(f"File saved as: {file_path}", 2000)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

    def save_current_file(self):
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, CodeEditor):
            file_path = None
            for path, editor in self.open_files.items():
                if editor == current_widget:
                    file_path = path
                    break
                    
            if file_path:
                try:
                    with open(file_path, 'w') as f:
                        f.write(current_widget.toPlainText())
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
                    
    def save_all_files(self):
        for file_path, editor in self.open_files.items():
            try:
                with open(file_path, 'w') as f:
                    f.write(editor.toPlainText())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save {file_path}: {str(e)}")
                
    def close_tab(self, index):
        # Don't close ML workspace tab
        if self.tab_widget.widget(index) == self.ml_workspace or self.tab_widget.widget(index) == self.llm_workspace:
            return
            
        # Remove from open files
        widget = self.tab_widget.widget(index)
        for file_path, editor in list(self.open_files.items()):
            if editor == widget:
                del self.open_files[file_path]
                break
                
        self.tab_widget.removeTab(index)
        
    def show_about(self):
        """Show the about dialog"""
        # TODO: Implement about dialog
        
    def on_command_executed(self, command, output):
        """Handle Python console command execution"""
        # Add command to history
        self.console.add_to_history(command)

    def closeEvent(self, event):
        """Clean up resources before closing"""
        try:
            # Save window state
            self._settings.setValue("windowState", self.saveState())
            self._settings.setValue("geometry", self.saveGeometry())
            
            # Clean up workspaces
            if hasattr(self, '_ml_workspace'):
                self._ml_workspace.cleanup()
            if hasattr(self, '_llm_workspace'):
                self._llm_workspace.cleanup()
                
            # Close all files
            self.close_all_tabs()
            
            # Clean up dock widgets
            for dock in self.findChildren(QDockWidget):
                if hasattr(dock.widget(), 'cleanup'):
                    dock.widget().cleanup()
                dock.close()
                
            # Clean up resources
            if hasattr(self, '_theme_manager'):
                self._theme_manager.cleanup()
            
            self.logger.debug("MainWindow cleanup completed")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Error during MainWindow cleanup: {str(e)}", exc_info=True)
            event.accept()  # Still close even if cleanup fails

    def _track_workspace_state(self, workspace_name: str):
        """Track the state of a workspace"""
        try:
            widget = getattr(self, f'_{workspace_name}', None)
            if widget:
                self._workspace_states[workspace_name] = {
                    'initialized': True,
                    'visible': widget.isVisible(),
                    'enabled': widget.isEnabled()
                }
            self.logger.debug(f"Tracked state for workspace: {workspace_name}")
        except Exception as e:
            self.logger.error(f"Error tracking workspace state: {str(e)}", exc_info=True)

    def run_current_file(self) -> None:
        """Run the current file in the editor."""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, CodeEditor):
            file_path = None
            for path, editor in self.open_files.items():
                if editor == current_widget:
                    file_path = path
                    break
            
            if file_path:
                # Logic to run the file, e.g., using subprocess
                try:
                    import subprocess
                    subprocess.run(["python", file_path], check=True)
                    self.statusBar().showMessage(f"Running: {file_path}", 2000)
                except subprocess.CalledProcessError as e:
                    QMessageBox.critical(self, "Error", f"Failed to run file: {str(e)}")

    def debug_current_file(self) -> None:
        """Debug the current file in the editor."""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, CodeEditor):
            file_path = None
            for path, editor in self.open_files.items():
                if editor == current_widget:
                    file_path = path
                    break
            
            if file_path:
                # Logic to debug the file, e.g., using subprocess with pdb
                try:
                    import subprocess
                    subprocess.run(["python", "-m", "pdb", file_path], check=True)
                    self.statusBar().showMessage(f"Debugging: {file_path}", 2000)
                except subprocess.CalledProcessError as e:
                    QMessageBox.critical(self, "Error", f"Failed to debug file: {str(e)}")

    def _apply_styles(self):
        """Применение стилей к главному окну"""
        # Применяем базовые стили
        self.setStyleSheet(self._style_manager.get_base_style())
        
        # Применяем стили к дочерним виджетам
        if hasattr(self, 'performance_monitor'):
            self.performance_monitor.setStyleSheet(
                self._style_manager.get_component_style(StyleClass.DOCK_WIDGET)
            )
        
        if hasattr(self, 'project_explorer'):
            self.project_explorer.setStyleSheet(
                self._style_manager.get_component_style(StyleClass.TREE_VIEW)
            )
        
        if hasattr(self, 'editor'):
            self.editor.setStyleSheet(
                self._style_manager.get_component_style(StyleClass.TAB_WIDGET)
            )
            
    @property
    def style_manager(self):
        """Get the style manager instance.
        
        Returns:
            StyleManager: The style manager for this window
        """
        return self._style_manager

    def change_theme(self, theme: str):
        """
        Change the application theme
        
        Args:
            theme (str): Theme name ('dark' or 'light')
        """
        if theme not in ['dark', 'light']:
            self.logger.warning(f"Invalid theme type: {theme}")
            return
            
        self._theme_manager.set_theme(theme)
        self._setup_theme()
        self._apply_component_styles()
        self._settings.setValue('theme/type', theme)

    def _on_tab_close_requested(self, index: int):
        """
        Handle tab close request
        
        Args:
            index (int): Index of the tab to close
        """
        try:
            # Get the widget at the specified index
            widget = self.central_widget.widget(index)
            if not widget:
                return
                
            # If it's a code editor, check for unsaved changes
            if isinstance(widget, CodeEditor):
                if widget.document().isModified():
                    response = QMessageBox.question(
                        self,
                        "Unsaved Changes",
                        f"The file has unsaved changes. Do you want to save before closing?",
                        QMessageBox.StandardButton.Save | 
                        QMessageBox.StandardButton.Discard | 
                        QMessageBox.StandardButton.Cancel
                    )
                    
                    if response == QMessageBox.StandardButton.Save:
                        self._save_file(widget)
                    elif response == QMessageBox.StandardButton.Cancel:
                        return
                        
                # Remove from open files tracking
                file_path = widget.file_path
                if file_path in self.open_files:
                    del self.open_files[file_path]
                    
            # Close the tab
            self.central_widget.removeTab(index)
            widget.deleteLater()
            
        except Exception as e:
            self.logger.error(f"Error closing tab: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to close tab: {str(e)}")

    def _save_file(self, editor: CodeEditor):
        """
        Save the content of a code editor
        
        Args:
            editor (CodeEditor): Editor widget to save
        """
        try:
            if not editor.file_path:
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save File",
                    str(self.project_root),
                    "Python Files (*.py);;All Files (*.*)"
                )
                if not file_path:
                    return
                editor.file_path = file_path
                
            with open(editor.file_path, 'w', encoding='utf-8') as f:
                f.write(editor.toPlainText())
            editor.document().setModified(False)
            
        except Exception as e:
            self.logger.error(f"Error saving file: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

    def close_all_tabs(self):
        """Close all open tabs with proper handling of unsaved changes"""
        while self.central_widget.count() > 0:
            self._on_tab_close_requested(0)

    def _setup_project_explorer(self):
        """Setup project explorer dock widget"""
        try:
            self.project_explorer = ProjectExplorer(self.project_root, parent=self)
            self.project_explorer_dock = self._create_dock_widget(
                "Project Explorer",
                self.project_explorer,
                Qt.DockWidgetArea.LeftDockWidgetArea
            )
            self.project_explorer.file_selected.connect(self._open_file)
            
        except Exception as e:
            self.logger.error(f"Error setting up project explorer: {str(e)}", exc_info=True)
            raise

    def _setup_git_panel(self):
        """Setup git panel dock widget"""
        try:
            self.git_panel = GitPanel(self.project_root, parent=self)
            self.git_dock = self._create_dock_widget(
                "Git",
                self.git_panel,
                Qt.DockWidgetArea.BottomDockWidgetArea
            )
            
        except Exception as e:
            self.logger.error(f"Error setting up git panel: {str(e)}", exc_info=True)
            raise

    def _setup_performance_monitor(self):
        """Setup performance monitor dock widget"""
        try:
            self.performance_widget = PerformanceWidget(parent=self)
            self.performance_dock = self._create_dock_widget(
                "Performance",
                self.performance_widget,
                Qt.DockWidgetArea.RightDockWidgetArea
            )
            
        except Exception as e:
            self.logger.error(f"Error setting up performance monitor: {str(e)}", exc_info=True)
            raise

    def _setup_python_console(self):
        """Setup Python console dock widget"""
        try:
            self.python_console = PythonConsole(parent=self)
            self.console_dock = self._create_dock_widget(
                "Python Console",
                self.python_console,
                Qt.DockWidgetArea.BottomDockWidgetArea
            )
            
        except Exception as e:
            self.logger.error(f"Error setting up Python console: {str(e)}", exc_info=True)
            raise

    def _setup_ml_workspace(self):
        """Setup ML workspace dock widget"""
        try:
            self.ml_workspace = MLWorkspace(parent=self)
            self.ml_workspace_dock = self._create_dock_widget(
                "ML Workspace",
                self.ml_workspace,
                Qt.DockWidgetArea.RightDockWidgetArea
            )
            
            # Connect ML workspace signals
            self.ml_workspace.model_changed.connect(self._on_ml_model_changed)
            self.ml_workspace.training_started.connect(self._on_training_started)
            self.ml_workspace.training_stopped.connect(self._on_training_stopped)
            
        except Exception as e:
            self.logger.error(f"Error setting up ML workspace: {str(e)}", exc_info=True)
            raise

    def _setup_llm_workspace(self):
        """Setup LLM workspace dock widget"""
        try:
            self.llm_workspace = LLMWorkspace(parent=self)
            self.llm_workspace_dock = self._create_dock_widget(
                "LLM Workspace",
                self.llm_workspace,
                Qt.DockWidgetArea.RightDockWidgetArea
            )
            
            # Connect LLM workspace signals
            self.llm_workspace.model_changed.connect(self._on_llm_model_changed)
            self.llm_workspace.generation_started.connect(self._on_generation_started)
            self.llm_workspace.generation_stopped.connect(self._on_generation_stopped)
            
        except Exception as e:
            self.logger.error(f"Error setting up LLM workspace: {str(e)}", exc_info=True)
            raise

    # ML Workspace event handlers
    def _on_ml_model_changed(self, model: str):
        """Handle ML model change"""
        self.status_bar.showMessage(f"ML Model changed to: {model}")

    def _on_training_started(self):
        """Handle ML training start"""
        self.status_bar.showMessage("ML Training started...")

    def _on_training_stopped(self):
        """Handle ML training stop"""
        self.status_bar.showMessage("ML Training stopped")

    # LLM Workspace event handlers
    def _on_llm_model_changed(self, model: str):
        """Handle LLM model change"""
        self.status_bar.showMessage(f"LLM Model changed to: {model}")

    def _on_generation_started(self):
        """Handle LLM generation start"""
        self.status_bar.showMessage("LLM Generation started...")

    def _on_generation_stopped(self):
        """Handle LLM generation stop"""
        self.status_bar.showMessage("LLM Generation stopped")

    def _open_file(self, file_path: str):
        """
        Open a file in the editor
        
        Args:
            file_path (str): Path to the file to open
        """
        try:
            # Check if file is already open
            if file_path in self.open_files:
                self.central_widget.setCurrentWidget(self.open_files[file_path])
                return
                
            # Create new editor for the file
            editor = CodeEditor(parent=self)
            editor.file_path = file_path
            
            # Load file content
            with open(file_path, 'r', encoding='utf-8') as f:
                editor.setPlainText(f.read())
                
            # Add to tracking
            self.open_files[file_path] = editor
            
            # Add new tab
            file_name = Path(file_path).name
            index = self.central_widget.addTab(editor, file_name)
            self.central_widget.setCurrentIndex(index)
            
            # Apply editor-specific styles
            editor_style = AdaptiveStyles.get_code_editor_style(self._theme_manager)
            editor.setStyleSheet(editor_style)
            
        except Exception as e:
            self.logger.error(f"Error opening file: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")

    def _load_icon(self, icon_name: str) -> QIcon:
        """Load an icon from the resources directory with comprehensive error handling.
        
        Args:
            icon_name: Name of the icon file to load (e.g., 'close.svg')
            
        Returns:
            QIcon: The loaded icon or an empty QIcon if loading fails
            
        The method performs the following checks:
        1. Validates input and file existence
        2. Checks file permissions and size
        3. Verifies file format and extension
        4. Validates icon loading and content
        """
        try:
            # 1. Input and file validation
            if not icon_name or not isinstance(icon_name, str):
                self.logger.error(f"Invalid icon name: {icon_name}")
                return QIcon()
                
            icon_path = Path(self.icon_path) / icon_name
            if not icon_path.exists():
                self.logger.warning(f"Icon file not found: {icon_path}")
                return QIcon()
                
            # 2. File permission and size checks
            try:
                if not icon_path.is_file():
                    self.logger.warning(f"Path exists but is not a file: {icon_path}")
                    return QIcon()
                    
                # Check if file is readable
                icon_path.open('rb').close()
                
                # Check file size (prevent loading extremely large files)
                if icon_path.stat().st_size > 1024 * 1024:  # Max 1MB
                    self.logger.warning(f"Icon file too large: {icon_path}")
                    return QIcon()
                    
            except (PermissionError, OSError) as e:
                self.logger.warning(f"Permission or OS error accessing icon: {icon_path}, Error: {e}")
                return QIcon()
                
            # 3. Format validation
            valid_extensions = {'.svg', '.png', '.ico', '.jpg', '.jpeg'}
            if icon_path.suffix.lower() not in valid_extensions:
                self.logger.warning(f"Unsupported icon format: {icon_path.suffix}")
                return QIcon()
                
            # 4. Load and validate icon
            icon = QIcon(str(icon_path))
            
            if icon.isNull():
                self.logger.warning(f"Icon loaded but is null: {icon_path}")
                return QIcon()
                
            # For SVG files, we don't check sizes since they're scalable
            if icon_path.suffix.lower() == '.svg':
                return icon
                
            sizes = icon.availableSizes()
            if not sizes:
                self.logger.warning(f"Icon has no available sizes: {icon_path}")
                return QIcon()
                
            self.logger.debug(f"Successfully loaded icon: {icon_name} with sizes {sizes}")
            return icon
            
        except Exception as e:
            self.logger.error(f"Unexpected error loading icon {icon_name}: {str(e)}", exc_info=True)
            return QIcon()

    def _setup_actions(self):
        """Setup all actions for menus and toolbars"""
        try:
            # File actions
            self.new_action = QAction("&New", self)
            self.new_action.setShortcut(QKeySequence.StandardKey.New)
            self.new_action.triggered.connect(self._new_file)
            
            self.open_action = QAction("&Open", self)
            self.open_action.setShortcut(QKeySequence.StandardKey.Open)
            self.open_action.triggered.connect(self._open_file_dialog)
            
            self.save_action = QAction("&Save", self)
            self.save_action.setShortcut(QKeySequence.StandardKey.Save)
            self.save_action.triggered.connect(self._save_current_file)
            
            self.save_as_action = QAction("Save &As...", self)
            self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
            self.save_as_action.triggered.connect(self._save_as)
            
            self.close_action = QAction("&Close", self)
            self.close_action.setShortcut(QKeySequence.StandardKey.Close)
            self.close_action.triggered.connect(self._close_current_tab)
            
            self.exit_action = QAction("E&xit", self)
            self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
            self.exit_action.triggered.connect(self.close)
            
            # Edit actions
            self.undo_action = QAction("&Undo", self)
            self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
            self.undo_action.triggered.connect(self._undo)
            
            self.redo_action = QAction("&Redo", self)
            self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
            self.redo_action.triggered.connect(self._redo)
            
            self.cut_action = QAction("Cu&t", self)
            self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
            self.cut_action.triggered.connect(self._cut)
            
            self.copy_action = QAction("&Copy", self)
            self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
            self.copy_action.triggered.connect(self._copy)
            
            self.paste_action = QAction("&Paste", self)
            self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
            self.paste_action.triggered.connect(self._paste)
            
            # View actions
            self.toggle_theme_action = QAction("Toggle &Theme", self)
            self.toggle_theme_action.setShortcut("Ctrl+T")
            self.toggle_theme_action.triggered.connect(self.toggle_theme)
            
        except Exception as e:
            self.logger.error(f"Error setting up actions: {str(e)}", exc_info=True)
            raise

    def _setup_menus(self):
        """Setup menu bar and menus"""
        try:
            # Create menu bar
            self.menu_bar = self.menuBar()
            
            # File menu
            self.file_menu = self.menu_bar.addMenu("&File")
            self.file_menu.addAction(self.new_action)
            self.file_menu.addAction(self.open_action)
            self.file_menu.addAction(self.save_action)
            self.file_menu.addAction(self.save_as_action)
            self.file_menu.addSeparator()
            self.file_menu.addAction(self.close_action)
            self.file_menu.addSeparator()
            self.file_menu.addAction(self.exit_action)
            
            # Edit menu
            self.edit_menu = self.menu_bar.addMenu("&Edit")
            self.edit_menu.addAction(self.undo_action)
            self.edit_menu.addAction(self.redo_action)
            self.edit_menu.addSeparator()
            self.edit_menu.addAction(self.cut_action)
            self.edit_menu.addAction(self.copy_action)
            self.edit_menu.addAction(self.paste_action)
            
            # View menu
            self.view_menu = self.menu_bar.addMenu("&View")
            self.view_menu.addAction(self.toggle_theme_action)
            
        except Exception as e:
            self.logger.error(f"Error setting up menus: {str(e)}", exc_info=True)
            raise

    def _setup_toolbars(self):
        """Setup toolbars"""
        try:
            # Main toolbar
            self.main_toolbar = QToolBar("Main", self)
            self.main_toolbar.setObjectName("MainToolbar")
            self.addToolBar(self.main_toolbar)
            self.main_toolbar.addAction(self.new_action)
            self.main_toolbar.addAction(self.open_action)
            self.main_toolbar.addAction(self.save_action)
            
            # Edit toolbar
            self.edit_toolbar = QToolBar("Edit", self)
            self.edit_toolbar.setObjectName("EditToolbar")
            self.addToolBar(self.edit_toolbar)
            self.edit_toolbar.addAction(self.undo_action)
            self.edit_toolbar.addAction(self.redo_action)
            self.edit_toolbar.addAction(self.cut_action)
            self.edit_toolbar.addAction(self.copy_action)
            self.edit_toolbar.addAction(self.paste_action)
            
        except Exception as e:
            self.logger.error(f"Error setting up toolbars: {str(e)}", exc_info=True)
            raise

    def _setup_statusbar(self):
        """Setup status bar"""
        try:
            self.status_bar = self.statusBar()
            self.status_bar.showMessage("Ready")
            
        except Exception as e:
            self.logger.error(f"Error setting up status bar: {str(e)}", exc_info=True)
            raise

    def _restore_window_state(self):
        """Restore window state from settings"""
        try:
            geometry = self._settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
                
            state = self._settings.value("windowState")
            if state:
                self.restoreState(state)
                
        except Exception as e:
            self.logger.error(f"Error restoring window state: {str(e)}", exc_info=True)

    # Action handlers
    def _new_file(self):
        """Create a new file"""
        try:
            editor = CodeEditor(parent=self)
            index = self.central_widget.addTab(editor, "Untitled")
            self.central_widget.setCurrentIndex(index)
            editor_style = AdaptiveStyles.get_code_editor_style(self._theme_manager)
            editor.setStyleSheet(editor_style)
            
        except Exception as e:
            self.logger.error(f"Error creating new file: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to create new file: {str(e)}")

    def _open_file_dialog(self):
        """Show open file dialog"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open File",
                str(self.project_root),
                "Python Files (*.py);;All Files (*.*)"
            )
            if file_path:
                self._open_file(file_path)
                
        except Exception as e:
            self.logger.error(f"Error showing open file dialog: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open file dialog: {str(e)}")

    def _save_current_file(self):
        """Save current file"""
        try:
            current_widget = self.central_widget.currentWidget()
            if isinstance(current_widget, CodeEditor):
                self._save_file(current_widget)
                
        except Exception as e:
            self.logger.error(f"Error saving current file: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

    def _save_as(self):
        """Save current file with new name"""
        try:
            current_widget = self.central_widget.currentWidget()
            if isinstance(current_widget, CodeEditor):
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save File As",
                    str(self.project_root),
                    "Python Files (*.py);;All Files (*.*)"
                )
                if file_path:
                    current_widget.file_path = file_path
                    self._save_file(current_widget)
                    file_name = Path(file_path).name
                    self.central_widget.setTabText(
                        self.central_widget.currentIndex(),
                        file_name
                    )
                    
        except Exception as e:
            self.logger.error(f"Error saving file as: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

    def _close_current_tab(self):
        """Close current tab"""
        current_index = self.central_widget.currentIndex()
        if current_index >= 0:
            self._on_tab_close_requested(current_index)

    def _undo(self):
        """Undo last action in current editor"""
        current_widget = self.central_widget.currentWidget()
        if isinstance(current_widget, CodeEditor):
            current_widget.undo()

    def _redo(self):
        """Redo last undone action in current editor"""
        current_widget = self.central_widget.currentWidget()
        if isinstance(current_widget, CodeEditor):
            current_widget.redo()

    def _cut(self):
        """Cut selected text in current editor"""
        current_widget = self.central_widget.currentWidget()
        if isinstance(current_widget, CodeEditor):
            current_widget.cut()

    def _copy(self):
        """Copy selected text in current editor"""
        current_widget = self.central_widget.currentWidget()
        if isinstance(current_widget, CodeEditor):
            current_widget.copy()

    def _paste(self):
        """Paste text in current editor"""
        current_widget = self.central_widget.currentWidget()
        if isinstance(current_widget, CodeEditor):
            current_widget.paste()

    def _on_file_selected(self, file_path: str):
        """Handle file selection from tree view.
        
        Args:
            file_path: Path to selected file
        """
        try:
            if not file_path:
                self.logger.warning("No file path provided")
                return
                
            if not Path(file_path).is_file():
                self.logger.warning(f"Not a file: {file_path}")
                return
                
            # Check if file is already open
            if file_path in self.open_files:
                self.central_widget.setCurrentWidget(self.open_files[file_path])
                return
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                self.logger.error(f"Error reading file {file_path}: {str(e)}")
                QMessageBox.critical(self, "Error", f"Could not read file: {str(e)}")
                return
                
            # Create new editor for the file
            editor = CodeEditor()
            editor.setPlainText(content)
            
            # Add editor to tab widget
            file_name = Path(file_path).name
            index = self.central_widget.addTab(editor, file_name)
            self.central_widget.setCurrentIndex(index)
            
            # Store reference to open file
            self.open_files[file_path] = editor
            
            self.status_bar.showMessage(f"Opened: {file_path}")
            self.logger.debug(f"Successfully opened file: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error handling file selection: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Could not open file: {str(e)}")
