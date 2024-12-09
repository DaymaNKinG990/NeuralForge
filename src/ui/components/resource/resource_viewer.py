"""Resource viewer component."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView,
    QToolBar, QLabel, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDir
from PyQt6.QtGui import QAction, QFileSystemModel
import os
import shutil

class ResourceViewer(QWidget):
    """Widget for viewing and managing project resources."""
    
    resource_selected = pyqtSignal(str)  # Path to selected resource
    
    def __init__(self, parent=None):
        """Initialize resource viewer.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the viewer UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QToolBar()
        self.path_label = QLabel()
        toolbar.addWidget(self.path_label)
        layout.addWidget(toolbar)
        
        # Resource tree
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.clicked.connect(self._on_item_clicked)
        
        # Hide unnecessary columns
        self.tree.hideColumn(1)  # Size
        self.tree.hideColumn(2)  # Type
        self.tree.hideColumn(3)  # Date Modified
        
        layout.addWidget(self.tree)
        
    def set_root_path(self, path: str):
        """Set root path for resource tree.
        
        Args:
            path: Root path
        """
        self.model.setRootPath(path)
        self.tree.setRootIndex(self.model.index(path))
        self.path_label.setText(path)
        
    def _show_context_menu(self, position):
        """Show context menu for resource tree.
        
        Args:
            position: Menu position
        """
        index = self.tree.indexAt(position)
        if not index.isValid():
            return
            
        path = self.model.filePath(index)
        
        menu = QMenu()
        
        # Add actions
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self._open_resource(path))
        menu.addAction(open_action)
        
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._rename_resource(path))
        menu.addAction(rename_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._delete_resource(path))
        menu.addAction(delete_action)
        
        menu.exec(self.tree.viewport().mapToGlobal(position))
        
    def _on_item_clicked(self, index):
        """Handle item click.
        
        Args:
            index: Item index
        """
        path = self.model.filePath(index)
        self.resource_selected.emit(path)
        
    def _open_resource(self, path: str):
        """Open resource.
        
        Args:
            path: Resource path
        """
        # Emit signal to open resource
        self.resource_selected.emit(path)
        
    def _rename_resource(self, path: str):
        """Rename resource.
        
        Args:
            path: Resource path
        """
        # TODO: Implement rename dialog
        pass
        
    def _delete_resource(self, path: str):
        """Delete resource.
        
        Args:
            path: Resource path
        """
        reply = QMessageBox.question(
            self,
            "Delete Resource",
            f"Are you sure you want to delete {os.path.basename(path)}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete resource: {str(e)}"
                )
