"""Main project explorer module."""
from typing import Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QMenu,
    QMessageBox
)
from PyQt6.QtCore import pyqtSignal
import logging
from ..styles.style_manager import StyleManager
from .tree_view import ProjectTreeView
from .search import FileSearchBar
from .actions import ProjectActions

logger = logging.getLogger(__name__)

class ProjectExplorer(QWidget):
    """Project explorer widget for managing project files and directories."""
    
    # Signals
    file_activated = pyqtSignal(Path)
    file_created = pyqtSignal(Path)
    file_deleted = pyqtSignal(Path)
    file_renamed = pyqtSignal(Path, Path)  # old_path, new_path
    
    def __init__(self, parent=None):
        """Initialize project explorer.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the explorer UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search bar
        self.search_bar = FileSearchBar()
        layout.addWidget(self.search_bar)
        
        # Tree view
        self.tree_view = ProjectTreeView()
        layout.addWidget(self.tree_view)
        
        # File actions
        self.file_actions = ProjectActions()
        
    def connect_signals(self):
        """Connect widget signals to slots."""
        self.tree_view.file_activated.connect(self.file_activated.emit)
        self.tree_view.context_menu_requested.connect(self.show_context_menu)
        self.search_bar.search_changed.connect(self.filter_files)
        
    def set_project_root(self, path: Path):
        """Set project root directory.
        
        Args:
            path: Root directory path
        """
        if not path.exists():
            logger.error(f"Project root does not exist: {path}")
            QMessageBox.critical(
                self,
                "Error",
                f"Project directory does not exist: {path}"
            )
            return
            
        try:
            self.tree_view.set_root_path(path)
            logger.info(f"Set project root to: {path}")
        except Exception as e:
            logger.error(f"Failed to set project root: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to set project root: {str(e)}"
            )
            
    def show_context_menu(self, index, menu: QMenu):
        """Show context menu for tree item.
        
        Args:
            index: Item model index
            menu: Context menu to populate
        """
        path = Path(self.tree_view.model.filePath(index))
        
        # Add actions
        if path.is_dir():
            menu.addAction("New File", lambda: self.create_file(path))
            menu.addAction("New Directory", lambda: self.create_directory(path))
            
        menu.addAction("Rename", lambda: self.rename_item(path))
        menu.addAction("Delete", lambda: self.delete_files([path]))
        
        # Add copy/paste actions if items are selected
        selected = self.tree_view.get_selected_paths()
        if selected:
            menu.addSeparator()
            menu.addAction("Copy", lambda: self.copy_files(selected, path))
            if path.is_dir():
                menu.addAction("Move Here", lambda: self.move_files(selected, path))
                
    def filter_files(self, text: str):
        """Filter files based on search text.
        
        Args:
            text: Search filter text
        """
        self.tree_view.model.setNameFilters(
            [f"*{text}*"] if text else []
        )
        
    def create_file(self, parent_path: Path):
        """Create new file.
        
        Args:
            parent_path: Parent directory path
        """
        if self.file_actions.create_file(parent_path):
            self.file_created.emit(parent_path)
            
    def create_directory(self, parent_path: Path):
        """Create new directory.
        
        Args:
            parent_path: Parent directory path
        """
        if self.file_actions.create_directory(parent_path):
            self.file_created.emit(parent_path)
            
    def delete_files(self, paths: list[Path]):
        """Delete files and directories.
        
        Args:
            paths: List of paths to delete
        """
        if self.file_actions.delete_files(paths):
            for path in paths:
                self.file_deleted.emit(path)
                
    def rename_item(self, path: Path):
        """Rename file or directory.
        
        Args:
            path: Path to rename
        """
        old_path = path
        if self.file_actions.rename_item(path):
            new_path = path.parent / path.name
            self.file_renamed.emit(old_path, new_path)
            
    def move_files(self, sources: list[Path], target: Path):
        """Move files to target directory.
        
        Args:
            sources: Source paths
            target: Target directory path
        """
        for source in sources:
            if self.file_actions.move_file(source, target):
                self.file_renamed.emit(source, target / source.name)
                
    def copy_files(self, sources: list[Path], target: Path):
        """Copy files to target directory.
        
        Args:
            sources: Source paths
            target: Target directory path
        """
        for source in sources:
            if self.file_actions.copy_file(source, target):
                self.file_created.emit(target / source.name)
