"""Toolbar management functionality."""
from PyQt6.QtWidgets import QToolBar
from PyQt6.QtGui import QAction
from typing import Optional, Dict, Callable
import logging

class ToolbarManager:
    """Manages application toolbars."""
    
    def __init__(self, parent):
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.toolbars: Dict[str, QToolBar] = {}
        self.actions: Dict[str, QAction] = {}
        
    def create_toolbar(self, name: str, title: str) -> Optional[QToolBar]:
        """Create a new toolbar.
        
        Args:
            name: Internal name for the toolbar
            title: Display title for the toolbar
            
        Returns:
            QToolBar if created successfully, None otherwise
        """
        try:
            toolbar = QToolBar(title, self.parent)
            toolbar.setMovable(True)
            toolbar.setFloatable(True)
            
            self.parent.addToolBar(toolbar)
            self.toolbars[name] = toolbar
            
            return toolbar
            
        except Exception as e:
            self.logger.error(f"Error creating toolbar {name}: {str(e)}")
            return None
            
    def add_action(self,
                   toolbar_name: str,
                   action_name: str,
                   text: str,
                   callback: Callable,
                   icon_name: Optional[str] = None,
                   tooltip: Optional[str] = None) -> Optional[QAction]:
        """Add an action to a toolbar.
        
        Args:
            toolbar_name: Name of the toolbar to add to
            action_name: Internal name for the action
            text: Display text for the action
            callback: Function to call when action triggered
            icon_name: Optional icon name
            tooltip: Optional tooltip text
            
        Returns:
            QAction if created successfully, None otherwise
        """
        try:
            if toolbar_name not in self.toolbars:
                self.logger.error(f"Toolbar {toolbar_name} not found")
                return None
                
            action = QAction(text, self.parent)
            action.triggered.connect(callback)
            
            if icon_name:
                icon = self.parent._load_icon(icon_name)
                if icon:
                    action.setIcon(icon)
                    
            if tooltip:
                action.setToolTip(tooltip)
                
            self.toolbars[toolbar_name].addAction(action)
            self.actions[action_name] = action
            
            return action
            
        except Exception as e:
            self.logger.error(f"Error adding action {action_name}: {str(e)}")
            return None
            
    def add_separator(self, toolbar_name: str):
        """Add a separator to a toolbar.
        
        Args:
            toolbar_name: Name of the toolbar to add separator to
        """
        if toolbar_name in self.toolbars:
            self.toolbars[toolbar_name].addSeparator()
            
    def setup_default_toolbars(self):
        """Setup default application toolbars."""
        # Main toolbar
        main_toolbar = self.create_toolbar('main', 'Main')
        
        # File actions
        self.add_action('main', 'new_file', 'New File', self.parent._new_file,
                       'new.svg', 'Create new file (Ctrl+N)')
        self.add_action('main', 'open_file', 'Open File', self.parent._open_file_dialog,
                       'open.svg', 'Open file (Ctrl+O)')
        self.add_action('main', 'save_file', 'Save File', self.parent._save_current_file,
                       'save.svg', 'Save current file (Ctrl+S)')
        self.add_separator('main')
        
        # Edit actions
        self.add_action('main', 'undo', 'Undo', self.parent._undo,
                       'undo.svg', 'Undo last action (Ctrl+Z)')
        self.add_action('main', 'redo', 'Redo', self.parent._redo,
                       'redo.svg', 'Redo last action (Ctrl+Y)')
        self.add_separator('main')
        
        # Run actions
        self.add_action('main', 'run', 'Run', self.parent.run_current_file,
                       'run.svg', 'Run current file (F5)')
        self.add_action('main', 'debug', 'Debug', self.parent.debug_current_file,
                       'debug.svg', 'Debug current file (F9)')
