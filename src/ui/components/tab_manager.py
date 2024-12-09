"""Tab management functionality."""
from PyQt6.QtWidgets import QTabWidget, QWidget
from ..code_editor import CodeEditor
from pathlib import Path
from typing import Optional, Dict
import logging

class TabManager(QTabWidget):
    """Manages editor tabs and file handling."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.open_files: Dict[str, CodeEditor] = {}
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup tab widget UI."""
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        
    def open_file(self, file_path: Path) -> Optional[CodeEditor]:
        """Open a file in a new tab.
        
        Args:
            file_path: Path to the file to open
            
        Returns:
            CodeEditor if file opened successfully, None otherwise
        """
        try:
            str_path = str(file_path)
            
            # Check if already open
            if str_path in self.open_files:
                self.setCurrentWidget(self.open_files[str_path])
                return self.open_files[str_path]
                
            # Create new editor
            editor = CodeEditor(self)
            editor.file_path = file_path
            
            # Load file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    editor.setPlainText(f.read())
            except Exception as e:
                self.logger.error(f"Error reading file {file_path}: {str(e)}")
                return None
                
            # Add to tab widget
            self.open_files[str_path] = editor
            self.addTab(editor, file_path.name)
            self.setCurrentWidget(editor)
            
            return editor
            
        except Exception as e:
            self.logger.error(f"Error opening file {file_path}: {str(e)}")
            return None
            
    def save_current_file(self) -> bool:
        """Save the current file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        editor = self.currentWidget()
        if not isinstance(editor, CodeEditor):
            return False
            
        return self._save_file(editor)
        
    def _save_file(self, editor: CodeEditor) -> bool:
        """Save the content of a code editor.
        
        Args:
            editor: Editor widget to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            if not editor.file_path:
                return False
                
            with open(editor.file_path, 'w', encoding='utf-8') as f:
                f.write(editor.toPlainText())
                
            editor.document().setModified(False)
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving file {editor.file_path}: {str(e)}")
            return False
            
    def close_tab(self, index: int) -> bool:
        """Close a tab.
        
        Args:
            index: Index of the tab to close
            
        Returns:
            bool: True if closed successfully, False otherwise
        """
        try:
            widget = self.widget(index)
            if not isinstance(widget, CodeEditor):
                return False
                
            # Remove from open files
            if str(widget.file_path) in self.open_files:
                del self.open_files[str(widget.file_path)]
                
            # Remove tab
            self.removeTab(index)
            widget.deleteLater()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing tab {index}: {str(e)}")
            return False
