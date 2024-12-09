"""Dock widget management functionality."""
from PyQt6.QtWidgets import QDockWidget, QWidget
from PyQt6.QtCore import Qt
from typing import Optional, Dict
from ..project_explorer import ProjectExplorer
from ..git_panel import GitPanel
from ..performance_monitor import PerformanceWidget
from ..python_console import PythonConsole
from ..ml_workspace import MLWorkspace
from ..llm_workspace import LLMWorkspace
import logging

class DockManager:
    """Manages application dock widgets."""
    
    def __init__(self, parent):
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.docks: Dict[str, QDockWidget] = {}
        
    def create_dock(self, 
                    name: str,
                    title: str,
                    widget: QWidget,
                    area: Qt.DockWidgetArea) -> Optional[QDockWidget]:
        """Create a new dock widget.
        
        Args:
            name: Internal name for the dock
            title: Display title for the dock
            widget: Widget to place in the dock
            area: Area to place the dock in
            
        Returns:
            QDockWidget if created successfully, None otherwise
        """
        try:
            dock = QDockWidget(title, self.parent)
            dock.setWidget(widget)
            dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                               Qt.DockWidgetArea.RightDockWidgetArea)
            
            self.parent.addDockWidget(area, dock)
            self.docks[name] = dock
            
            return dock
            
        except Exception as e:
            self.logger.error(f"Error creating dock {name}: {str(e)}")
            return None
            
    def setup_default_docks(self):
        """Setup default application docks."""
        try:
            # Project Explorer
            explorer = ProjectExplorer(self.parent)
            self.create_dock('explorer', 'Project Explorer', explorer,
                           Qt.DockWidgetArea.LeftDockWidgetArea)
            
            # Git Panel
            git_panel = GitPanel(self.parent)
            self.create_dock('git', 'Git', git_panel,
                           Qt.DockWidgetArea.RightDockWidgetArea)
            
            # Performance Monitor
            perf_monitor = PerformanceWidget(self.parent)
            self.create_dock('performance', 'Performance', perf_monitor,
                           Qt.DockWidgetArea.RightDockWidgetArea)
            
            # Python Console
            console = PythonConsole(self.parent)
            self.create_dock('console', 'Python Console', console,
                           Qt.DockWidgetArea.BottomDockWidgetArea)
            
            # ML Workspace
            ml_workspace = MLWorkspace(self.parent)
            self.create_dock('ml', 'ML Workspace', ml_workspace,
                           Qt.DockWidgetArea.RightDockWidgetArea)
            
            # LLM Workspace
            llm_workspace = LLMWorkspace(self.parent)
            self.create_dock('llm', 'LLM Workspace', llm_workspace,
                           Qt.DockWidgetArea.RightDockWidgetArea)
            
        except Exception as e:
            self.logger.error(f"Error setting up docks: {str(e)}")
            
    def save_state(self):
        """Save dock states to settings."""
        try:
            self.parent._settings.setValue('window/geometry', self.parent.saveGeometry())
            self.parent._settings.setValue('window/state', self.parent.saveState())
        except Exception as e:
            self.logger.error(f"Error saving dock state: {str(e)}")
            
    def restore_state(self):
        """Restore dock states from settings."""
        try:
            geometry = self.parent._settings.value('window/geometry')
            state = self.parent._settings.value('window/state')
            
            if geometry:
                self.parent.restoreGeometry(geometry)
            if state:
                self.parent.restoreState(state)
        except Exception as e:
            self.logger.error(f"Error restoring dock state: {str(e)}")
