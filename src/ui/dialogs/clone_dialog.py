from typing import Optional, Tuple
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                          QLineEdit, QPushButton, QFileDialog, QMessageBox)
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
        self.style_manager = StyleManager()
        self.git_manager = GitManager()
        
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
                border: 1px solid {ColorScheme.INPUT_BORDER_FOCUS.value};
            }}
        """)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        
        # Target directory input
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Target Directory:")
        dir_label.setStyleSheet(f"color: {ColorScheme.FOREGROUND.value};")
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Select directory to clone into...")
        self.dir_input.setStyleSheet(f"""
            QLineEdit {{
                background: {ColorScheme.INPUT_BACKGROUND.value};
                color: {ColorScheme.FOREGROUND.value};
                border: 1px solid {ColorScheme.INPUT_BORDER.value};
                padding: 5px;
                border-radius: 3px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ColorScheme.INPUT_BORDER_FOCUS.value};
            }}
        """)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ColorScheme.BUTTON_BACKGROUND.value};
                color: {ColorScheme.FOREGROUND.value};
                border: 1px solid {ColorScheme.BUTTON_BORDER.value};
                padding: 5px 10px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background: {ColorScheme.BUTTON_HOVER.value};
            }}
            QPushButton:pressed {{
                background: {ColorScheme.BUTTON_PRESSED.value};
            }}
        """)
        browse_btn.clicked.connect(self._browse_directory)
        
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(browse_btn)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ColorScheme.BUTTON_BACKGROUND.value};
                color: {ColorScheme.FOREGROUND.value};
                border: 1px solid {ColorScheme.BUTTON_BORDER.value};
                padding: 5px 15px;
                border-radius: 3px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: {ColorScheme.BUTTON_HOVER.value};
            }}
            QPushButton:pressed {{
                background: {ColorScheme.BUTTON_PRESSED.value};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        
        clone_btn = QPushButton("Clone")
        clone_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ColorScheme.PRIMARY_BUTTON.value};
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: {ColorScheme.PRIMARY_BUTTON_HOVER.value};
            }}
            QPushButton:pressed {{
                background: {ColorScheme.PRIMARY_BUTTON_PRESSED.value};
            }}
        """)
        clone_btn.clicked.connect(self._handle_clone)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(clone_btn)
        
        # Add all layouts
        layout.addLayout(url_layout)
        layout.addLayout(dir_layout)
        layout.addLayout(button_layout)
        
        # Set dialog style
        self.setStyleSheet(f"""
            QDialog {{
                background: {ColorScheme.DIALOG_BACKGROUND.value};
                min-width: 500px;
            }}
        """)
        
    def _browse_directory(self) -> None:
        """Open file dialog to select target directory.
        
        This method opens a file dialog for the user to select a target directory.
        The selected directory path is then set as the text of the target directory input field.
        """
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Target Directory",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.dir_input.setText(directory)
    
    def _validate_inputs(self) -> Tuple[bool, Optional[str]]:
        """Validate user inputs.
        
        This method checks if the user inputs are valid. It checks for the following conditions:
        - Repository URL is not empty
        - Target directory is not empty
        - Repository URL ends with '.git'
        - Target directory exists
        - Target directory is a directory
        - Target directory is empty
        
        Args:
            None
        
        Returns:
            Tuple containing:
                - Boolean indicating if inputs are valid
                - Error message if inputs are invalid, None otherwise
        """
        url = self.url_input.text().strip()
        directory = self.dir_input.text().strip()
        
        if not url:
            return False, "Please enter a repository URL"
        
        if not directory:
            return False, "Please select a target directory"
        
        if not url.endswith('.git'):
            return False, "Invalid repository URL. Must end with .git"
        
        target_path = Path(directory)
        if not target_path.exists():
            return False, "Target directory does not exist"
        
        if not target_path.is_dir():
            return False, "Selected path is not a directory"
        
        if any(target_path.iterdir()):
            return False, "Target directory must be empty"
        
        return True, None
        
    def _handle_clone(self) -> None:
        """Handle repository cloning process."""
        is_valid, error_msg = self._validate_inputs()
        
        if not is_valid:
            QMessageBox.warning(
                self,
                "Invalid Input",
                error_msg,
                QMessageBox.StandardButton.Ok
            )
            return
            
        url = self.url_input.text().strip()
        directory = self.dir_input.text().strip()
        
        try:
            self.git_manager.clone_repository(url, directory)
            self.clone_completed.emit(directory)
            self.accept()
            
        except GitError as e:
            QMessageBox.critical(
                self,
                "Clone Failed",
                f"Failed to clone repository:\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
