from typing import Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, 
    QMenu, QInputDialog, QMessageBox, QPushButton,
    QHBoxLayout, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex, QDir
from PyQt6.QtGui import QAction, QKeySequence, QFileSystemModel
import shutil
from ..utils.caching import cache_manager
from .styles.style_manager import StyleManager
from .styles.style_enums import StyleClass, ColorScheme

class ProjectExplorer(QWidget):
    """Project explorer widget for managing project files and directories.
    
    Provides a tree view of the project structure with file operations like
    create, delete, rename, and search functionality.
    
    Attributes:
        file_selected: Signal emitted when a file is selected
        file_created: Signal emitted when a file is created
        file_deleted: Signal emitted when a file is deleted
        file_renamed: Signal emitted when a file is renamed
        style_manager: Manager for applying consistent styles
        cache: Cache manager for file operations
    """
    
    file_selected = pyqtSignal(str)
    file_created = pyqtSignal(str)
    file_deleted = pyqtSignal(str)
    file_renamed = pyqtSignal(str, str)  # old_path, new_path
    
    def __init__(self, project_root: str, parent: Optional[QWidget] = None) -> None:
        """Initialize the project explorer.
        
        Args:
            project_root: Root directory of the project
            parent: Parent widget
        """
        super().__init__(parent)
        self.project_root = Path(project_root)
        self.style_manager = StyleManager()
        self.cache = cache_manager
        
        self._init_ui()
        self._setup_file_system_model()
        self._setup_context_menu()
        self._apply_styles()
        
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.textChanged.connect(self._filter_files)
        search_layout.addWidget(self.search_input)
        
        # Tree view
        self.tree_view = QTreeView()
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)
        self.tree_view.doubleClicked.connect(self._on_item_double_clicked)
        
        # Add components to layout
        layout.addLayout(search_layout)
        layout.addWidget(self.tree_view)
        
    def _setup_file_system_model(self) -> None:
        """Setup the file system model for the tree view."""
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(str(self.project_root))
        
        # Set filters
        self.fs_model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
        
        # Set the model to the tree view
        self.tree_view.setModel(self.fs_model)
        self.tree_view.setRootIndex(self.fs_model.index(str(self.project_root)))
        
        # Hide unnecessary columns
        for col in range(1, self.fs_model.columnCount()):
            self.tree_view.hideColumn(col)
            
    def _setup_context_menu(self) -> None:
        """Setup the context menu for file operations."""
        self.context_menu = QMenu(self)
        
        # New file/folder actions
        new_menu = self.context_menu.addMenu("New")
        self.new_file_action = new_menu.addAction("File")
        self.new_folder_action = new_menu.addAction("Folder")
        
        # Other actions
        self.rename_action = self.context_menu.addAction("Rename")
        self.delete_action = self.context_menu.addAction("Delete")
        
        # Connect actions
        self.new_file_action.triggered.connect(self._create_file)
        self.new_folder_action.triggered.connect(self._create_folder)
        self.rename_action.triggered.connect(self._rename_item)
        self.delete_action.triggered.connect(self._delete_item)
        
        # Add shortcuts
        self.new_file_action.setShortcut(QKeySequence("Ctrl+N"))
        self.delete_action.setShortcut(QKeySequence("Delete"))
        self.rename_action.setShortcut(QKeySequence("F2"))
        
    def _apply_styles(self) -> None:
        """Apply styles to all components."""
        self.setStyleSheet(self.style_manager.get_component_style(StyleClass.PROJECT_EXPLORER))
        
    def _filter_files(self, text: str) -> None:
        """Filter files based on search text.
        
        Args:
            text: Search text to filter files
        """
        self.fs_model.setNameFilters([f'*{text}*'])
        self.fs_model.setNameFilterDisables(False)

    def _get_selected_path(self) -> Optional[Path]:
        """Get the path of the currently selected item.
        
        Returns:
            Path of selected item or None if nothing selected
        """
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            return None
        return Path(self.fs_model.filePath(indexes[0]))
        
    def _create_file(self) -> None:
        """Create a new file."""
        parent_path = self._get_selected_path() or self.project_root
        file_name, ok = QInputDialog.getText(self, "Create File", "Enter file name:")
        if ok and file_name:
            try:
                (parent_path / file_name).touch()
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Could not create file: {e}")

    def _create_folder(self) -> None:
        """Create a new folder."""
        parent_path = self._get_selected_path() or self.project_root
        folder_name, ok = QInputDialog.getText(self, "Create Folder", "Enter folder name:")
        if ok and folder_name:
            try:
                (parent_path / folder_name).mkdir()
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Could not create folder: {e}")

    def _rename_item(self) -> None:
        """Rename the selected item."""
        old_path = self._get_selected_path()
        if not old_path:
            return
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=old_path.name)
        if ok and new_name:
            new_path = old_path.parent / new_name
            try:
                old_path.rename(new_path)
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Could not rename: {e}")

    def _delete_item(self) -> None:
        """Delete the selected item."""
        path = self._get_selected_path()
        if not path:
            return
        reply = QMessageBox.question(self, "Delete", f"Are you sure you want to delete '{path.name}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Could not delete: {e}")
                
    def _on_item_double_clicked(self, index: QModelIndex) -> None:
        """Handle double-click on an item.
        
        Args:
            index: Index of clicked item
        """
        path = Path(self.fs_model.filePath(index))
        if path.is_file():
            self.file_selected.emit(str(path))
            
    def _show_context_menu(self, position) -> None:
        """Show the context menu.
        
        Args:
            position: Position to show menu at
        """
        self.context_menu.exec(self.tree_view.viewport().mapToGlobal(position))
        
    def refresh(self) -> None:
        """Refresh the file system view."""
        self.fs_model.setRootPath(str(self.project_root))
        
    def get_project_root(self) -> str:
        """Get the project root directory.
        
        Returns:
            Project root path as string
        """
        return str(self.project_root)
