"""Project tree view widget."""
from typing import Optional
from pathlib import Path
from PyQt6.QtWidgets import QTreeView, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex
from PyQt6.QtGui import QFileSystemModel
from ..styles.style_manager import StyleManager
from ..styles.style_enums import StyleClass

class ProjectTreeView(QTreeView):
    """Tree view for project files and directories."""
    
    # Signals
    file_activated = pyqtSignal(Path)
    context_menu_requested = pyqtSignal(QModelIndex, QMenu)
    
    def __init__(self, parent=None):
        """Initialize project tree view.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.setup_ui()
        self.setup_model()
        
    def setup_ui(self):
        """Set up the tree view UI."""
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        
        # Apply styles
        self.setStyleSheet(
            self.style_manager.get_component_style(StyleClass.TREE_VIEW)
        )
        
    def setup_model(self):
        """Set up the file system model."""
        self.model = QFileSystemModel()
        self.model.setReadOnly(False)
        self.model.setNameFilterDisables(False)
        self.setModel(self.model)
        
        # Hide unnecessary columns
        for col in range(1, self.model.columnCount()):
            self.hideColumn(col)
            
    def set_root_path(self, path: Path):
        """Set root path for the tree view.
        
        Args:
            path: Root directory path
        """
        index = self.model.setRootPath(str(path))
        self.setRootIndex(index)
        
    def get_selected_paths(self) -> list[Path]:
        """Get list of selected file paths.
        
        Returns:
            List of selected paths
        """
        paths = []
        for index in self.selectedIndexes():
            if index.column() == 0:  # Only process first column
                path = Path(self.model.filePath(index))
                paths.append(path)
        return paths
        
    def show_context_menu(self, position):
        """Show context menu for selected items.
        
        Args:
            position: Menu position
        """
        index = self.indexAt(position)
        if index.isValid():
            menu = QMenu(self)
            self.context_menu_requested.emit(index, menu)
            menu.exec(self.viewport().mapToGlobal(position))
            
    def keyPressEvent(self, event):
        """Handle key press events.
        
        Args:
            event: Key event
        """
        # Handle delete key
        if event.key() == Qt.Key.Key_Delete:
            paths = self.get_selected_paths()
            if paths:
                self.parent().delete_files(paths)
        else:
            super().keyPressEvent(event)
            
    def dragEnterEvent(self, event):
        """Handle drag enter events.
        
        Args:
            event: Drag event
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        """Handle drop events.
        
        Args:
            event: Drop event
        """
        if event.mimeData().hasUrls():
            drop_index = self.indexAt(event.position().toPoint())
            target_path = Path(self.model.filePath(drop_index))
            
            if not target_path.is_dir():
                target_path = target_path.parent
                
            for url in event.mimeData().urls():
                source_path = Path(url.toLocalFile())
                if source_path.exists():
                    self.parent().move_file(source_path, target_path)
                    
            event.acceptProposedAction()
