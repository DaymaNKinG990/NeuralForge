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
import pathlib
import os
from typing import Union
from PyQt6.QtCore import QSettings
import logging
import sys
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            self.logger = logging.getLogger(__name__)
            self.logger.debug("MainWindow initialization started")
            
            self.setWindowTitle("NeuroForge IDE")
            self.setMinimumSize(1200, 800)
            
            # Store open files
            self.open_files = {}
            
            # Initialize project root
            self.project_root = Path(os.getcwd())
            self.logger.debug(f"Project root set to: {self.project_root}")
            
            # Initialize style manager first
            self._style_manager = StyleManager()
            self.logger.debug("Style manager initialized")
            
            # Register components for lazy loading
            self._register_components()
            self.logger.debug("Components registered")
            
            # Initialize UI
            self._init_ui()
            self.logger.debug("UI initialized")
            
            self._apply_styles()
            self.logger.debug("Styles applied")
            
        except Exception as e:
            self.logger.error(f"Error during MainWindow initialization: {str(e)}", exc_info=True)
            raise

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
        # Create central widget with tab support
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tab widget for editors
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)
        
        layout.addWidget(self.tab_widget)
        
        # Create dock widgets
        # Project Explorer
        project_explorer = component_loader.get_component("project_explorer", self)
        project_explorer_dock = QDockWidget("Project Explorer", self)
        project_explorer_dock.setWidget(project_explorer)
        project_explorer_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                              Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, project_explorer_dock)

        # Connect signals
        if hasattr(project_explorer, 'file_opened'):
            project_explorer.file_opened.connect(self.open_file)

        # ML Tools Panel
        self.ml_tools = QTabWidget()
        self.ml_tools.setTabPosition(QTabWidget.TabPosition.South)
        
        # Add ML Workspace
        self.ml_workspace = MLWorkspace()
        self.ml_tools.addTab(self.ml_workspace, "Neural Networks")
        
        # Add LLM Workspace
        self.llm_workspace = LLMWorkspace()
        self.ml_tools.addTab(self.llm_workspace, "Language Models")
        
        ml_dock = QDockWidget("Machine Learning", self)
        ml_dock.setWidget(self.ml_tools)
        ml_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                               Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, ml_dock)
        
        # Add Git panel
        self._init_git_panel()
        
        # Add Performance Monitor
        perf_monitor = component_loader.get_component("performance_monitor", self)
        perf_dock = QDockWidget("Performance", self)
        perf_dock.setWidget(perf_monitor)
        perf_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | 
                                 Qt.DockWidgetArea.LeftDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, perf_dock)
        
        # Python Console
        python_console = component_loader.get_component("python_console")
        console_dock = QDockWidget("Python Console", self)
        console_dock.setWidget(python_console)
        console_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, console_dock)
        
        self.setup_tool_bar()
        self.setup_status_bar()
        self.setup_menu_bar()
        
    def _init_git_panel(self) -> None:
        """Initialize Git panel."""
        try:
            git_dock = QDockWidget("Git", self)
            self.git_panel = GitPanel(self.project_root, parent=self)
            git_dock.setWidget(self.git_panel)
            git_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                   Qt.DockWidgetArea.RightDockWidgetArea)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, git_dock)
        except Exception as e:
            self.logger.error(f"Failed to initialize Git panel: {e}")
            
    def setup_tool_bar(self) -> None:
        """Setup the toolbar with actions for file operations, run, and debug."""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setMovable(False)
        
        # Add actions
        new_file_action = QAction(QIcon("src/ui/resources/icons/code.svg"), "New File", self)
        new_file_action.setShortcut(QKeySequence.StandardKey.New)
        new_file_action.triggered.connect(self.new_file)
        toolbar.addAction(new_file_action)
        
        open_action = QAction(QIcon("src/ui/resources/icons/folder.svg"), "Open File", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file_dialog)
        toolbar.addAction(open_action)
        
        save_action = QAction(QIcon("src/ui/resources/icons/save.svg"), "Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        run_action = QAction(QIcon("src/ui/resources/icons/play.svg"), "Run", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.run_current_file)
        toolbar.addAction(run_action)
        
        debug_action = QAction(QIcon("src/ui/resources/icons/debug.svg"), "Debug", self)
        debug_action.setShortcut("F9")
        debug_action.triggered.connect(self.debug_current_file)
        toolbar.addAction(debug_action)
        
        self.addToolBar(toolbar)
        
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
        """Setup the menu bar with file and edit menu options."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_project_action = file_menu.addAction("New Project")
        new_project_action.triggered.connect(self.new_project)
        
        open_project_action = file_menu.addAction("Open Project")
        open_project_action.triggered.connect(self.open_project)
        
        new_file_action = file_menu.addAction("New File")
        new_file_action.triggered.connect(self.new_file)
        
        open_file_action = file_menu.addAction("Open File")
        open_file_action.triggered.connect(self.open_file_dialog)
        
        save_action = file_menu.addAction("Save")
        save_action.triggered.connect(self.save_file)
        
        save_all_action = file_menu.addAction("Save All")
        save_all_action.triggered.connect(self.save_all_files)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Undo")
        edit_menu.addAction("Redo")
        edit_menu.addSeparator()
        edit_menu.addAction("Cut")
        edit_menu.addAction("Copy")
        edit_menu.addAction("Paste")
        
        # Neural Network menu
        nn_menu = menubar.addMenu("Neural Network")
        nn_menu.addAction("New Model")
        nn_menu.addAction("Train Model")
        nn_menu.addAction("Export Model")
        
        # View menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction(self.console.parent().toggleViewAction())
        view_menu.addAction(self.project_explorer.parent().toggleViewAction())
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        settings_action = tools_menu.addAction("Settings")
        settings_action.triggered.connect(self.show_settings)
        
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
            
    def change_theme(self, theme: ThemeType):
        """Изменить тему оформления"""
        self._style_manager.set_theme(theme)
        self._apply_styles()
        
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
            
    def open_file(self, file_path: Union[str, pathlib.Path]) -> None:
        """Open a file in the editor.
        
        Args:
            file_path: Path to the file to open
        """
        file_path = pathlib.Path(file_path) if isinstance(file_path, str) else file_path
        str_path = str(file_path)
        
        # Check if file is already open
        if str_path in self.open_files:
            self.tab_widget.setCurrentWidget(self.open_files[str_path])
            return
            
        try:
            # Create new editor
            editor = CodeEditor()
            with file_path.open('r') as f:
                editor.setPlainText(f.read())
                
            # Add to open files and create new tab
            self.open_files[str_path] = editor
            tab_name = file_path.name
            self.tab_widget.addTab(editor, tab_name)
            self.tab_widget.setCurrentWidget(editor)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")

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
        
    def show_settings(self):
        """Show the settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Apply settings
            self.apply_settings()
            
    def apply_settings(self):
        """Apply settings to all components"""
        settings = QSettings()
        
        # Apply editor settings
        font_family = settings.value('editor/font_family', 'Consolas')
        font_size = int(settings.value('editor/font_size', 10))
        
        for editor in self.open_files.values():
            editor.setFont(QFont(font_family, font_size))
            
        # Apply ML workspace settings
        self.ml_workspace.apply_settings()
        
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
