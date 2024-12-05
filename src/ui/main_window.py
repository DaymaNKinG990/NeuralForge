from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QDockWidget, 
                             QMenuBar, QStatusBar, QFileDialog, QMessageBox,
                             QVBoxLayout, QWidget, QToolBar, QLabel)
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFont, QPaintEvent, QKeyEvent
from PyQt6.QtCore import Qt, QSize
from .code_editor import CodeEditor
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
from .styles.style_manager import StyleManager
from .styles.style_enums import StyleClass, ThemeType
from pathlib import Path
from typing import Union
from PyQt6.QtCore import QSettings
import logging
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            self.logger = logging.getLogger(__name__)
            self.logger.debug("MainWindow initialization started")
            
            # Basic window setup
            self.setWindowTitle("NeuroForge IDE")
            self.setMinimumSize(1200, 800)
            self.logger.debug(f"Window size set to: {self.size()}")
            
            # Ensure window is visible
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
            self.setWindowState(Qt.WindowState.WindowActive)
            
            # Store open files
            self.open_files = {}
            
            # Initialize project root
            self.project_root = Path.cwd()
            self.logger.debug(f"Project root set to: {self.project_root}")
            
            # Initialize style manager first
            self._style_manager = StyleManager()
            self.logger.debug("Style manager initialized")
            
            # Register components for lazy loading
            self._register_components()
            self.logger.debug("Components registered")
            
            # Initialize UI
            self._init_ui()
            self.logger.debug(f"UI initialized, window visible: {self.isVisible()}")
            
            self._apply_styles()
            self.logger.debug("Styles applied")
            
            # Final visibility check
            self.logger.debug(f"Final window state - Visible: {self.isVisible()}, Hidden: {self.isHidden()}, Geometry: {self.geometry()}")
            
        except Exception as e:
            self.logger.error(f"Error during MainWindow initialization: {str(e)}", exc_info=True)
            raise
            
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

    def _init_ui(self) -> None:
        """Setup the main window UI with performance monitoring."""
        try:
            # Set icon paths
            self.icon_path = Path(__file__).parent / 'resources' / 'icons'
            self.logger.debug(f"Icon path set to: {self.icon_path}")
            
            # Create central widget and layout
            central_widget = QWidget()
            layout = QVBoxLayout(central_widget)
            
            # Create tab widget for editors
            self.tab_widget = QTabWidget()
            self.tab_widget.setTabsClosable(True)
            self.tab_widget.tabCloseRequested.connect(self.close_tab)
            self.tab_widget.setDocumentMode(True)
            self.tab_widget.setMovable(True)
            layout.addWidget(self.tab_widget)
            
            # Set central widget
            self.setCentralWidget(central_widget)
            
            # Initialize dock widgets
            self._init_dock_widgets()
            
            # Setup toolbars and menus
            self.setup_tool_bar()
            self.setup_status_bar()
            self.setup_menu_bar()
            
            self.logger.debug("UI initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in _init_ui: {str(e)}", exc_info=True)
            raise
            
    def _init_dock_widgets(self) -> None:
        """Initialize all dock widgets."""
        try:
            # Project Explorer
            self.project_explorer_dock = QDockWidget("Project Explorer", self)
            self.project_explorer_dock.setObjectName("ProjectExplorer")
            self.project_explorer = ProjectExplorer(str(self.project_root), self)
            self.project_explorer_dock.setWidget(self.project_explorer)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.project_explorer_dock)
            
            # ML Workspace
            self.ml_workspace_dock = QDockWidget("ML Workspace", self)
            self.ml_workspace_dock.setObjectName("MLWorkspace")
            self.ml_workspace = MLWorkspace(self)
            self.ml_workspace_dock.setWidget(self.ml_workspace)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ml_workspace_dock)
            
            # LLM Workspace
            self.llm_workspace_dock = QDockWidget("LLM Workspace", self)
            self.llm_workspace_dock.setObjectName("LLMWorkspace")
            self.llm_workspace = LLMWorkspace(self)
            self.llm_workspace_dock.setWidget(self.llm_workspace)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.llm_workspace_dock)
            
            # Python Console
            self.python_console_dock = QDockWidget("Python Console", self)
            self.python_console_dock.setObjectName("PythonConsole")
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
        # Stop profiling
        profiler.stop_memory_tracking()
        
        # Clear caches
        cache_manager.clear()
        search_cache.clear()
        component_loader.clear_cache()
        
        # Log performance stats
        slow_ops = profiler.get_slow_operations()
        if slow_ops:
            logging.warning("Slow operations detected during session:")
            for op in slow_ops[:5]:  # Top 5 slowest
                logging.warning(
                    f"{op.function_name}: {op.total_time*1000:.2f}ms "
                    f"({op.calls} calls)"
                )
                
        memory_ops = profiler.get_memory_intensive_operations()
        if memory_ops:
            logging.warning("Memory intensive operations detected:")
            for op in memory_ops[:5]:  # Top 5 memory intensive
                memory_mb = (op.memory_peak - op.memory_start) / (1024 * 1024)
                logging.warning(
                    f"{op.function_name}: {memory_mb:.1f}MB peak usage"
                )
                
        super().closeEvent(event)

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

    def change_theme(self, theme: ThemeType):
        """Изменить тему оформления"""
        self._style_manager.set_theme(theme)
        self._apply_styles()

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
