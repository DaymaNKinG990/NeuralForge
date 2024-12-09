"""Git-related dialogs for version control operations."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QDialogButtonBox, QTextEdit,
    QPushButton, QFormLayout, QListWidget,
    QMessageBox, QInputDialog, QFileDialog
)
from PyQt6.QtCore import Qt
from pathlib import Path
from typing import Optional, List
from ...utils.git_manager import GitManager

class CommitDialog(QDialog):
    """Dialog for creating Git commits."""
    
    def __init__(self, parent=None):
        """Initialize commit dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Commit Changes")
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Commit message input
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("Enter commit message...")
        self.message_edit.setMinimumWidth(400)
        self.message_edit.setMinimumHeight(100)
        layout.addWidget(self.message_edit)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class CloneDialog(QDialog):
    """Dialog for cloning Git repositories."""
    
    def __init__(self, parent=None):
        """Initialize clone dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Clone Repository")
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QFormLayout(self)
        
        # Repository URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://github.com/user/repo.git")
        layout.addRow("Repository URL:", self.url_input)
        
        # Target directory
        self.dir_input = QLineEdit()
        self.browse_btn = QPushButton("Browse...")
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.browse_btn)
        layout.addRow("Target Directory:", dir_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        # Connect signals
        self.browse_btn.clicked.connect(self.browse_directory)
        
    def browse_directory(self):
        """Show directory selection dialog."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Target Directory",
            str(Path.home())
        )
        if directory:
            self.dir_input.setText(directory)
            
    def validate_and_accept(self):
        """Validate inputs before accepting."""
        if not self.url_input.text().strip():
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter a repository URL."
            )
            return
            
        if not self.dir_input.text().strip():
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please select a target directory."
            )
            return
            
        self.accept()

class RemoteManagerDialog(QDialog):
    """Dialog for managing Git remotes."""
    
    def __init__(self, git_manager: GitManager, parent=None):
        """Initialize remote manager dialog.
        
        Args:
            git_manager: Git manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.git_manager = git_manager
        self.setWindowTitle("Remote Manager")
        self.setup_ui()
        self.refresh_remotes()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Remotes list
        self.remotes_list = QListWidget()
        layout.addWidget(self.remotes_list)
        
        # Remote details
        details_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.url_input = QLineEdit()
        details_layout.addRow("Name:", self.name_input)
        details_layout.addRow("URL:", self.url_input)
        layout.addLayout(details_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.remove_btn = QPushButton("Remove")
        self.update_btn = QPushButton("Update")
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.update_btn)
        layout.addLayout(button_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect signals
        self.add_btn.clicked.connect(self.add_remote)
        self.remove_btn.clicked.connect(self.remove_remote)
        self.update_btn.clicked.connect(self.update_remote)
        self.remotes_list.currentItemChanged.connect(self.remote_selected)
        
    def refresh_remotes(self):
        """Refresh the list of remotes."""
        self.remotes_list.clear()
        remotes = self.git_manager.get_remotes()
        for name, url in remotes.items():
            self.remotes_list.addItem(f"{name} ({url})")
            
    def remote_selected(self, current, previous):
        """Handle remote selection change."""
        if current:
            name = current.text().split(" (")[0]
            url = self.git_manager.get_remotes()[name]
            self.name_input.setText(name)
            self.url_input.setText(url)
            
    def add_remote(self):
        """Add a new remote."""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        
        if not name or not url:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter both name and URL."
            )
            return
            
        try:
            self.git_manager.add_remote(name, url)
            self.refresh_remotes()
            self.name_input.clear()
            self.url_input.clear()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to add remote: {str(e)}"
            )
            
    def remove_remote(self):
        """Remove selected remote."""
        current = self.remotes_list.currentItem()
        if not current:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a remote to remove."
            )
            return
            
        name = current.text().split(" (")[0]
        try:
            self.git_manager.remove_remote(name)
            self.refresh_remotes()
            self.name_input.clear()
            self.url_input.clear()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to remove remote: {str(e)}"
            )
            
    def update_remote(self):
        """Update selected remote."""
        current = self.remotes_list.currentItem()
        if not current:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a remote to update."
            )
            return
            
        old_name = current.text().split(" (")[0]
        new_name = self.name_input.text().strip()
        new_url = self.url_input.text().strip()
        
        if not new_name or not new_url:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter both name and URL."
            )
            return
            
        try:
            if old_name != new_name:
                self.git_manager.rename_remote(old_name, new_name)
            self.git_manager.set_remote_url(new_name, new_url)
            self.refresh_remotes()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update remote: {str(e)}"
            )

class StashDialog(QDialog):
    """Dialog for Git stash operations."""
    
    def __init__(self, git_manager: GitManager, parent=None):
        """Initialize stash dialog.
        
        Args:
            git_manager: Git manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.git_manager = git_manager
        self.setWindowTitle("Stash Manager")
        self.setup_ui()
        self.refresh_stashes()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Stash list
        self.stash_list = QListWidget()
        layout.addWidget(self.stash_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.pop_btn = QPushButton("Pop")
        self.drop_btn = QPushButton("Drop")
        self.create_btn = QPushButton("Create New")
        
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.pop_btn)
        button_layout.addWidget(self.drop_btn)
        button_layout.addWidget(self.create_btn)
        layout.addLayout(button_layout)
        
        # Connect signals
        self.apply_btn.clicked.connect(self.apply_stash)
        self.pop_btn.clicked.connect(self.pop_stash)
        self.drop_btn.clicked.connect(self.drop_stash)
        self.create_btn.clicked.connect(self.create_stash)
        
    def refresh_stashes(self):
        """Refresh stash list."""
        self.stash_list.clear()
        stashes = self.git_manager.get_stashes()
        for stash in stashes:
            self.stash_list.addItem(f"{stash.name}: {stash.message}")
            
    def get_selected_stash(self) -> Optional[str]:
        """Get selected stash name."""
        item = self.stash_list.currentItem()
        if item:
            return item.text().split(":")[0]
        return None
        
    def apply_stash(self):
        """Apply selected stash."""
        stash = self.get_selected_stash()
        if stash:
            try:
                self.git_manager.apply_stash(stash)
                self.accept()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Stash Error",
                    f"Failed to apply stash: {str(e)}"
                )
                
    def pop_stash(self):
        """Pop selected stash."""
        stash = self.get_selected_stash()
        if stash:
            try:
                self.git_manager.pop_stash(stash)
                self.accept()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Stash Error",
                    f"Failed to pop stash: {str(e)}"
                )
                
    def drop_stash(self):
        """Drop selected stash."""
        stash = self.get_selected_stash()
        if stash:
            reply = QMessageBox.question(
                self,
                "Confirm Drop",
                f"Are you sure you want to drop stash {stash}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.git_manager.drop_stash(stash)
                    self.refresh_stashes()
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Stash Error",
                        f"Failed to drop stash: {str(e)}"
                    )
                    
    def create_stash(self):
        """Create new stash."""
        message, ok = QInputDialog.getText(
            self,
            "Create Stash",
            "Enter stash message:"
        )
        if ok and message:
            try:
                self.git_manager.create_stash(message)
                self.accept()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Stash Error",
                    f"Failed to create stash: {str(e)}"
                )

class MergeConflictDialog(QDialog):
    """Dialog for resolving merge conflicts."""
    
    def __init__(self, git_manager: GitManager, conflicts: List[Path], parent=None):
        """Initialize merge conflict dialog.
        
        Args:
            git_manager: Git manager instance
            conflicts: List of conflicting files
            parent: Parent widget
        """
        super().__init__(parent)
        self.git_manager = git_manager
        self.conflicts = conflicts
        self.setWindowTitle("Resolve Merge Conflicts")
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Conflict list
        self.conflict_list = QListWidget()
        for conflict in self.conflicts:
            self.conflict_list.addItem(str(conflict))
        layout.addWidget(self.conflict_list)
        
        # Diff viewer
        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        layout.addWidget(self.diff_view)
        
        # Resolution buttons
        button_layout = QHBoxLayout()
        self.use_ours = QPushButton("Use Ours")
        self.use_theirs = QPushButton("Use Theirs")
        self.edit_file = QPushButton("Edit File")
        self.mark_resolved = QPushButton("Mark Resolved")
        
        button_layout.addWidget(self.use_ours)
        button_layout.addWidget(self.use_theirs)
        button_layout.addWidget(self.edit_file)
        button_layout.addWidget(self.mark_resolved)
        layout.addLayout(button_layout)
        
        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(self.button_box)
        
        # Connect signals
        self.conflict_list.currentItemChanged.connect(self.show_diff)
        self.use_ours.clicked.connect(self.resolve_ours)
        self.use_theirs.clicked.connect(self.resolve_theirs)
        self.edit_file.clicked.connect(self.open_editor)
        self.mark_resolved.clicked.connect(self.mark_as_resolved)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
    def show_diff(self, current, previous):
        """Show diff for selected file."""
        if current:
            file_path = Path(current.text())
            try:
                diff = self.git_manager.get_conflict_diff(file_path)
                self.diff_view.setPlainText(diff)
            except Exception as e:
                self.diff_view.setPlainText(f"Error loading diff: {str(e)}")
                
    def resolve_ours(self):
        """Resolve conflict using our version."""
        current = self.conflict_list.currentItem()
        if current:
            file_path = Path(current.text())
            try:
                self.git_manager.resolve_conflict(file_path, "ours")
                self.update_conflict_list()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Resolution Error",
                    f"Failed to resolve conflict: {str(e)}"
                )
                
    def resolve_theirs(self):
        """Resolve conflict using their version."""
        current = self.conflict_list.currentItem()
        if current:
            file_path = Path(current.text())
            try:
                self.git_manager.resolve_conflict(file_path, "theirs")
                self.update_conflict_list()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Resolution Error",
                    f"Failed to resolve conflict: {str(e)}"
                )
                
    def open_editor(self):
        """Open file in external editor."""
        current = self.conflict_list.currentItem()
        if current:
            file_path = Path(current.text())
            try:
                self.git_manager.open_in_editor(file_path)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Editor Error",
                    f"Failed to open editor: {str(e)}"
                )
                
    def mark_as_resolved(self):
        """Mark current file as resolved."""
        current = self.conflict_list.currentItem()
        if current:
            file_path = Path(current.text())
            try:
                self.git_manager.mark_resolved(file_path)
                self.update_conflict_list()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Resolution Error",
                    f"Failed to mark as resolved: {str(e)}"
                )
                
    def update_conflict_list(self):
        """Update list of conflicting files."""
        current_row = self.conflict_list.currentRow()
        self.conflict_list.clear()
        
        remaining_conflicts = [
            conflict for conflict in self.conflicts
            if self.git_manager.has_conflicts(conflict)
        ]
        
        for conflict in remaining_conflicts:
            self.conflict_list.addItem(str(conflict))
            
        if not remaining_conflicts:
            self.accept()
        elif current_row < len(remaining_conflicts):
            self.conflict_list.setCurrentRow(current_row)
