"""Menu management functionality."""
from PyQt6.QtWidgets import QMenuBar, QMenu
from PyQt6.QtGui import QAction, QKeySequence
from typing import Optional, Dict, Callable
import logging

class MenuManager:
    """Manages application menus and actions."""
    
    def __init__(self, parent):
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.menu_bar = QMenuBar(parent)
        self.menus: Dict[str, QMenu] = {}
        self.actions: Dict[str, QAction] = {}
        
    def create_menu(self, name: str, title: str) -> Optional[QMenu]:
        """Create a new menu.
        
        Args:
            name: Internal name for the menu
            title: Display title for the menu
            
        Returns:
            QMenu if created successfully, None otherwise
        """
        try:
            menu = self.menu_bar.addMenu(title)
            self.menus[name] = menu
            return menu
        except Exception as e:
            self.logger.error(f"Error creating menu {name}: {str(e)}")
            return None
            
    def add_action(self, 
                   menu_name: str,
                   action_name: str,
                   text: str,
                   callback: Callable,
                   shortcut: Optional[str] = None,
                   icon_name: Optional[str] = None) -> Optional[QAction]:
        """Add an action to a menu.
        
        Args:
            menu_name: Name of the menu to add to
            action_name: Internal name for the action
            text: Display text for the action
            callback: Function to call when action triggered
            shortcut: Optional keyboard shortcut
            icon_name: Optional icon name
            
        Returns:
            QAction if created successfully, None otherwise
        """
        try:
            if menu_name not in self.menus:
                self.logger.error(f"Menu {menu_name} not found")
                return None
                
            action = QAction(text, self.parent)
            action.triggered.connect(callback)
            
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
                
            if icon_name:
                icon = self.parent._load_icon(icon_name)
                if icon:
                    action.setIcon(icon)
                    
            self.menus[menu_name].addAction(action)
            self.actions[action_name] = action
            
            return action
            
        except Exception as e:
            self.logger.error(f"Error adding action {action_name}: {str(e)}")
            return None
            
    def add_separator(self, menu_name: str):
        """Add a separator to a menu.
        
        Args:
            menu_name: Name of the menu to add separator to
        """
        if menu_name in self.menus:
            self.menus[menu_name].addSeparator()
            
    def setup_default_menus(self):
        """Setup default application menus."""
        # File menu
        file_menu = self.create_menu('file', '&File')
        self.add_action('file', 'new_file', 'New File', self.parent._new_file, 'Ctrl+N', 'new.svg')
        self.add_action('file', 'open_file', 'Open File...', self.parent._open_file_dialog, 'Ctrl+O', 'open.svg')
        self.add_separator('file')
        self.add_action('file', 'save', 'Save', self.parent._save_current_file, 'Ctrl+S', 'save.svg')
        self.add_action('file', 'save_as', 'Save As...', self.parent._save_as, 'Ctrl+Shift+S', 'save-as.svg')
        self.add_separator('file')
        self.add_action('file', 'close_tab', 'Close Tab', self.parent._close_current_tab, 'Ctrl+W', 'close.svg')
        self.add_action('file', 'exit', 'Exit', self.parent.close, 'Alt+F4')
        
        # Edit menu
        edit_menu = self.create_menu('edit', '&Edit')
        self.add_action('edit', 'undo', 'Undo', self.parent._undo, 'Ctrl+Z', 'undo.svg')
        self.add_action('edit', 'redo', 'Redo', self.parent._redo, 'Ctrl+Y', 'redo.svg')
        self.add_separator('edit')
        self.add_action('edit', 'cut', 'Cut', self.parent._cut, 'Ctrl+X', 'cut.svg')
        self.add_action('edit', 'copy', 'Copy', self.parent._copy, 'Ctrl+C', 'copy.svg')
        self.add_action('edit', 'paste', 'Paste', self.parent._paste, 'Ctrl+V', 'paste.svg')
        
        # View menu
        view_menu = self.create_menu('view', '&View')
        self.add_action('view', 'toggle_theme', 'Toggle Theme', self.parent.toggle_theme)
        
        # Help menu
        help_menu = self.create_menu('help', '&Help')
        self.add_action('help', 'about', 'About', self.parent.show_about)
