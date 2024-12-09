"""File and directory actions for project explorer."""
from pathlib import Path
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QMessageBox, QInputDialog,
    QFileDialog
)
import shutil
import logging

logger = logging.getLogger(__name__)

class ProjectActions(QWidget):
    """Widget for handling file and directory operations."""
    
    def __init__(self, parent=None):
        """Initialize file actions.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
    def create_file(self, parent_path: Path) -> bool:
        """Create new file.
        
        Args:
            parent_path: Parent directory path
            
        Returns:
            True if file was created successfully
        """
        file_name, ok = QInputDialog.getText(
            self,
            "Create New File",
            "Enter file name:"
        )
        
        if ok and file_name:
            try:
                new_file_path = parent_path / file_name
                if new_file_path.exists():
                    QMessageBox.warning(
                        self,
                        "File Exists",
                        f"File {file_name} already exists!"
                    )
                    return False
                    
                new_file_path.touch()
                logger.info(f"Created new file: {new_file_path}")
                return True
                
            except Exception as e:
                logger.error(f"Error creating file: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create file: {str(e)}"
                )
                return False
                
        return False
        
    def create_directory(self, parent_path: Path) -> bool:
        """Create new directory.
        
        Args:
            parent_path: Parent directory path
            
        Returns:
            True if directory was created successfully
        """
        dir_name, ok = QInputDialog.getText(
            self,
            "Create New Directory",
            "Enter directory name:"
        )
        
        if ok and dir_name:
            try:
                new_dir_path = parent_path / dir_name
                if new_dir_path.exists():
                    QMessageBox.warning(
                        self,
                        "Directory Exists",
                        f"Directory {dir_name} already exists!"
                    )
                    return False
                    
                new_dir_path.mkdir()
                logger.info(f"Created new directory: {new_dir_path}")
                return True
                
            except Exception as e:
                logger.error(f"Error creating directory: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create directory: {str(e)}"
                )
                return False
                
        return False
        
    def delete_items(self, paths: List[Path]) -> bool:
        """Delete files and directories.
        
        Args:
            paths: List of paths to delete
            
        Returns:
            True if all items were deleted successfully
        """
        if not paths:
            return False
            
        items_str = "\n".join(str(p) for p in paths)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete:\n{items_str}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                for path in paths:
                    if path.is_file():
                        path.unlink()
                    else:
                        shutil.rmtree(path)
                        
                logger.info(f"Deleted items: {items_str}")
                return True
                
            except Exception as e:
                logger.error(f"Error deleting items: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete items: {str(e)}"
                )
                return False
                
        return False
        
    def rename_item(self, path: Path) -> bool:
        """Rename file or directory.
        
        Args:
            path: Path to rename
            
        Returns:
            True if item was renamed successfully
        """
        new_name, ok = QInputDialog.getText(
            self,
            "Rename",
            "Enter new name:",
            text=path.name
        )
        
        if ok and new_name and new_name != path.name:
            try:
                new_path = path.parent / new_name
                if new_path.exists():
                    QMessageBox.warning(
                        self,
                        "Item Exists",
                        f"An item named {new_name} already exists!"
                    )
                    return False
                    
                path.rename(new_path)
                logger.info(f"Renamed {path} to {new_path}")
                return True
                
            except Exception as e:
                logger.error(f"Error renaming item: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to rename item: {str(e)}"
                )
                return False
                
        return False
        
    def move_file(self, source: Path, target: Path) -> bool:
        """Move file or directory.
        
        Args:
            source: Source path
            target: Target directory path
            
        Returns:
            True if item was moved successfully
        """
        try:
            if source.is_dir():
                shutil.move(str(source), str(target))
            else:
                new_path = target / source.name
                source.rename(new_path)
            logger.info(f"Moved {source} to {target}")
            return True
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to move item: {str(e)}"
            )
            logger.error(f"Move error: {str(e)}")
            return False
            
    def copy_file(self, source: Path, target: Path) -> bool:
        """Copy file or directory.
        
        Args:
            source: Source path
            target: Target directory path
            
        Returns:
            True if item was copied successfully
        """
        try:
            if source.is_dir():
                shutil.copytree(str(source), str(target / source.name))
            else:
                shutil.copy2(str(source), str(target))
            logger.info(f"Copied {source} to {target}")
            return True
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to copy item: {str(e)}"
            )
            logger.error(f"Copy error: {str(e)}")
            return False
