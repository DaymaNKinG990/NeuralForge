from typing import Optional, Tuple
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                          QLineEdit, QPushButton, QFileDialog, QMessageBox, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal
from ..styles.style_manager import StyleManager
from ..styles.style_enums import ColorScheme, StyleClass
from ...utils.git_manager import GitManager, GitError

class CloneDialog(QDialog):
    """Dialog for cloning remote Git repositories."""
    
    clone_completed = pyqtSignal(str)  # Emits repository path on successful clone
    
    def __init__(self, parent=None) -> None:
        """Initialize the clone dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # Ensure cleanup
        self.style_manager = StyleManager()
        
        # Default to user's home directory for cloning
        self.default_clone_path = Path.home() / 'Projects'
        self.default_clone_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize GitManager with default path
        self.git_manager = GitManager(self.default_clone_path)
        
        self.setWindowTitle("Clone Repository")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Repository URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("Repository URL:")
        url_label.setStyleSheet(f"color: {ColorScheme.FOREGROUND.value};")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://github.com/username/repository.git")
        self.url_input.setStyleSheet(f"""
            QLineEdit {{
                background: {ColorScheme.INPUT_BACKGROUND.value};
                color: {ColorScheme.FOREGROUND.value};
                border: 1px solid {ColorScheme.INPUT_BORDER.value};
                padding: 5px;
                border-radius: 3px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ColorScheme.INPUT_FOCUS_BORDER.value};
            }}
        """)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Directory selection
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Clone to:")
        dir_label.setStyleSheet(f"color: {ColorScheme.FOREGROUND.value};")
        self.directory_input = QLineEdit()
        self.directory_input.setText(str(self.default_clone_path))
        self.directory_input.setStyleSheet(f"""
            QLineEdit {{
                background: {ColorScheme.INPUT_BACKGROUND.value};
                color: {ColorScheme.FOREGROUND.value};
                border: 1px solid {ColorScheme.INPUT_BORDER.value};
                padding: 5px;
                border-radius: 3px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ColorScheme.INPUT_FOCUS_BORDER.value};
            }}
        """)
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_directory)
        self.browse_button.setStyleSheet(f"""
            QPushButton {{
                background: {ColorScheme.BUTTON_BACKGROUND.value};
                color: {ColorScheme.BUTTON_TEXT.value};
                border: 1px solid {ColorScheme.BUTTON_BORDER.value};
                padding: 5px 10px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background: {ColorScheme.BUTTON_HOVER.value};
            }}
            QPushButton:disabled {{
                background: {ColorScheme.BUTTON_DISABLED.value};
                color: {ColorScheme.MENU_BORDER.value};
            }}
        """)
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.directory_input)
        dir_layout.addWidget(self.browse_button)
        layout.addLayout(dir_layout)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        button_layout.addWidget(self.button_box)
        layout.addLayout(button_layout)
        
    def browse_directory(self) -> None:
        """Open directory selection dialog."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Clone Directory",
            str(self.default_clone_path),
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.directory_input.setText(directory)
            # Update GitManager with new path
            self.git_manager = GitManager(Path(directory))
            
    def validate_inputs(self) -> bool:
        """Validate user inputs before proceeding.
        
        Returns:
            bool: True if inputs are valid, False otherwise
        """
        if not self.url_input.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Please enter a repository URL")
            return False
            
        directory = Path(self.directory_input.text().strip())
        if not directory.parent.exists():
            QMessageBox.warning(self, "Invalid Directory", 
                              "The selected directory's parent does not exist")
            return False
            
        return True
        
    def accept(self) -> None:
        """Handle dialog acceptance."""
        if not self.validate_inputs():
            return
            
        try:
            # Get repository name from URL
            repo_url = self.url_input.text().strip()
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            
            # Create full clone path
            clone_path = Path(self.directory_input.text().strip()) / repo_name
            
            # Update GitManager with final path
            self.git_manager = GitManager(clone_path)
            
            # Clone repository
            self.git_manager.clone_repository(repo_url)
            
            self.clone_completed.emit(str(clone_path))
            super().accept()
            
        except GitError as e:
            QMessageBox.critical(self, "Clone Error", str(e))

    def closeEvent(self, event) -> None:
        """Handle dialog close event."""
        if self.git_manager:
            if hasattr(self.git_manager, '_repo') and self.git_manager._repo:
                self.git_manager._repo.close()
            self.git_manager._repo = None
        super().closeEvent(event)
