"""File tree view component with language-specific icons."""
from PyQt6.QtWidgets import QTreeView, QAbstractItemView
from PyQt6.QtCore import Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QIcon, QFileSystemModel
from pathlib import Path
import os

from ..utils.file_icon_manager import FileIconManager

class FileTreeView(QTreeView):
    """Tree view component that displays files with language-specific icons."""
    
    file_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create file system model
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        
        # Set up icon manager
        self.icon_manager = FileIconManager()
        
        # Configure model to use custom icons
        self.model.iconProvider = self.icon_manager
        
        # Setup tree view properties
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAnimated(True)
        self.setIndentation(20)
        self.setSortingEnabled(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Set model and hide unnecessary columns
        self.setModel(self.model)
        self.hideColumn(1)  # Size
        self.hideColumn(2)  # Type
        self.hideColumn(3)  # Date Modified
        
        # Connect signals
        self.clicked.connect(self._on_item_clicked)
        
    def set_root_path(self, path: str):
        """Set the root path for the file tree.
        
        Args:
            path: Path to set as root
        """
        root_index = self.model.setRootPath(path)
        self.setRootIndex(root_index)
        
    def _on_item_clicked(self, index):
        """Handle item click in the tree view.
        
        Args:
            index: Index of clicked item
        """
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            self.file_selected.emit(file_path)
