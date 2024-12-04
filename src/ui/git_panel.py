from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit,
                             QDialog, QDialogButtonBox, QTextEdit, QMenu,
                             QTabWidget, QSplitter, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex, QSize, QThread, QTimer
from PyQt6.QtGui import QIcon, QColor, QBrush
from ..utils.git_manager import GitManager, FileStatus, GitFile
from .dialogs.clone_dialog import CloneDialog
from .dialogs.remote_manager_dialog import RemoteManagerDialog
from pathlib import Path
from .styles.style_manager import StyleManager
from .styles.style_enums import StyleClass
from typing import Optional

class CommitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Commit Changes")
        self.setup_ui()

    def setup_ui(self):
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

        self.setStyleSheet("""
            QDialog {
                background: #2D2D2D;
            }
            QTextEdit {
                background: #1E1E1E;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                border-radius: 3px;
            }
            QPushButton {
                background: #0E639C;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #1177BB;
            }
            QPushButton:pressed {
                background: #0D5789;
            }
        """)

class GitPanel(QWidget):
    """Panel for Git operations."""
    
    def __init__(self, project_path: Path, parent: Optional[QWidget] = None):
        """Initialize GitPanel.
        
        Args:
            project_path: Path to the project root directory
            parent: Parent widget
        """
        super().__init__(parent)
        
        if not isinstance(project_path, Path):
            project_path = Path(project_path)
            
        if not project_path.is_dir():
            raise ValueError(f"Project path does not exist: {project_path}")
            
        # Create GitManager in the main thread
        self.git_manager = GitManager(project_path, parent=self)
        self.style_manager = StyleManager()
        
        self.setup_ui()
        self.connect_signals()
        
        # Initial refresh
        QTimer.singleShot(0, self.refresh_status)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Get icons path relative to this file's location
        current_dir = Path(__file__).parent
        icons_path = current_dir / 'resources' / 'icons'

        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet(self.style_manager.get_component_style(StyleClass.TOOL_BAR))
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)

        # Branch selector
        self.branch_label = QLabel("Branch:")
        self.branch_label.setStyleSheet(self.style_manager.get_component_style(StyleClass.LABEL))
        self.branch_button = QPushButton()
        self.branch_button.setIcon(QIcon(str(icons_path / "git-branch.svg")))
        self.branch_button.setStyleSheet(self.style_manager.get_component_style(StyleClass.BUTTON))
        self.update_branch_button()

        # Git operations
        self.remote_btn = QPushButton("Remotes")
        self.clone_btn = QPushButton(QIcon(str(icons_path / "git-clone.svg")), "")
        self.commit_btn = QPushButton(QIcon(str(icons_path / "git-commit.svg")), "")
        self.push_btn = QPushButton(QIcon(str(icons_path / "git-push.svg")), "")
        self.pull_btn = QPushButton(QIcon(str(icons_path / "git-pull.svg")), "")
        
        for btn in [self.clone_btn, self.commit_btn, self.push_btn, self.pull_btn]:
            btn.setStyleSheet(self.style_manager.get_component_style(StyleClass.BUTTON))
            btn.setIconSize(QSize(16, 16))

        toolbar_layout.addWidget(self.branch_label)
        toolbar_layout.addWidget(self.branch_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.remote_btn)
        toolbar_layout.addWidget(self.clone_btn)
        toolbar_layout.addWidget(self.commit_btn)
        toolbar_layout.addWidget(self.push_btn)
        toolbar_layout.addWidget(self.pull_btn)

        layout.addWidget(toolbar)

        # Changes tree
        self.changes_tree = QTreeWidget()
        self.changes_tree.setHeaderLabels(["File", "Status"])
        self.changes_tree.setStyleSheet(self.style_manager.get_component_style(StyleClass.TREE_VIEW))
        layout.addWidget(self.changes_tree)

        # Status bar
        self.status_label = QLabel()
        self.status_label.setStyleSheet(self.style_manager.get_component_style(StyleClass.STATUS_BAR))
        layout.addWidget(self.status_label)

    def connect_signals(self):
        self.git_manager.status_changed.connect(self.refresh_status)
        self.git_manager.error_occurred.connect(self.show_error)
        self.git_manager.operation_success.connect(self.show_success)
        
        self.branch_button.clicked.connect(self.show_branch_menu)
        self.remote_btn.clicked.connect(self.show_remote_manager)
        self.clone_btn.clicked.connect(self.clone_repository)
        self.commit_btn.clicked.connect(self.commit_changes)
        self.push_btn.clicked.connect(self.push_changes)
        self.pull_btn.clicked.connect(self.pull_changes)
        
        self.changes_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.changes_tree.customContextMenuRequested.connect(self.show_context_menu)

    def refresh_status(self):
        """Refresh the status of files in the Git repository."""
        self.changes_tree.clear()
        
        try:
            # Create root items for staged and unstaged changes
            staged = QTreeWidgetItem(["Staged Changes"])
            unstaged = QTreeWidgetItem(["Unstaged Changes"])
            
            # Get status from git manager
            files = self.git_manager.get_status()
            
            # Add files to appropriate sections
            for git_file in files:
                # Convert Path to string for display
                file_path = str(git_file.path)
                status_name = git_file.status.name if hasattr(git_file.status, 'name') else str(git_file.status)
                
                # Create item with file path and status
                item = QTreeWidgetItem([file_path, status_name])
                
                # Set color based on status
                if git_file.status == FileStatus.MODIFIED:
                    item.setForeground(0, QBrush(QColor("#FFA500")))  # Orange
                elif git_file.status == FileStatus.ADDED:
                    item.setForeground(0, QBrush(QColor("#00FF00")))  # Green
                elif git_file.status == FileStatus.DELETED:
                    item.setForeground(0, QBrush(QColor("#FF0000")))  # Red
                elif git_file.status == FileStatus.UNTRACKED:
                    item.setForeground(0, QBrush(QColor("#808080")))  # Gray
                
                # Add to appropriate section
                if git_file.staged:
                    staged.addChild(item)
                else:
                    unstaged.addChild(item)
            
            # Add root items to tree
            self.changes_tree.addTopLevelItem(staged)
            self.changes_tree.addTopLevelItem(unstaged)
            
            # Expand root items
            staged.setExpanded(True)
            unstaged.setExpanded(True)
            
            # Update branch button
            self.update_branch_button()
            
            # Emit success signal
            self.git_manager.operation_success.emit("Status refreshed successfully")
            
        except Exception as e:
            self.git_manager.error_occurred.emit(str(e))

    def update_branch_button(self):
        """Update branch button text with current branch"""
        try:
            branch_name = self.git_manager.get_current_branch()
            self.branch_button.setText(branch_name)
        except Exception as e:
            self.git_manager.error_occurred.emit(f"Failed to update branch: {str(e)}")
            self.branch_button.setText("main")  # Fallback to main

    def show_branch_menu(self):
        """Show branch selection menu"""
        try:
            menu = QMenu(self)
            branches = self.git_manager.get_branches()
            
            if not branches:  # If no branches exist
                no_branches = menu.addAction("No branches")
                no_branches.setEnabled(False)
            else:
                for branch in branches:
                    action = menu.addAction(branch)
                    action.triggered.connect(lambda checked, b=branch: self.switch_branch(b))
            
            # Add branch management options
            menu.addSeparator()
            new_branch = menu.addAction("New Branch...")
            new_branch.triggered.connect(self.create_new_branch)
            
            # Show menu at button
            menu.exec(self.branch_button.mapToGlobal(self.branch_button.rect().bottomLeft()))
            
        except Exception as e:
            self.git_manager.error_occurred.emit(f"Failed to show branch menu: {str(e)}")

    def create_new_branch(self):
        """Create a new branch"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Branch")
        layout = QVBoxLayout(dialog)

        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter branch name...")
        layout.addWidget(name_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted and name_input.text():
            self.git_manager.create_branch(name_input.text())

    def switch_branch(self, branch_name: str):
        """Switch to selected branch"""
        self.git_manager.switch_branch(branch_name)

    def clone_repository(self):
        """Show clone dialog"""
        dialog = CloneDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_status()

    def commit_changes(self):
        """Show commit dialog and create commit"""
        dialog = CommitDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            message = dialog.message_edit.toPlainText()
            if message:
                self.git_manager.commit(message)

    def push_changes(self):
        """Push changes to remote"""
        self.git_manager.push()

    def pull_changes(self):
        """Pull changes from remote"""
        self.git_manager.pull()

    def show_remote_manager(self):
        """Show remote manager dialog"""
        dialog = RemoteManagerDialog(self.git_manager, self)
        dialog.exec()

    def show_context_menu(self, position):
        """Show context menu for files"""
        item = self.changes_tree.itemAt(position)
        if not item or not item.parent():
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                color: #CCCCCC;
                border: 1px solid #454545;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background: #094771;
            }
        """)

        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        parent_text = item.parent().text(0)

        if parent_text == "Staged Changes":
            unstage_action = menu.addAction("Unstage")
            unstage_action.triggered.connect(lambda: self.git_manager.unstage_file(file_path))
        else:
            stage_action = menu.addAction("Stage")
            stage_action.triggered.connect(lambda: self.git_manager.stage_file(file_path))
            
            discard_action = menu.addAction("Discard Changes")
            discard_action.triggered.connect(lambda: self.git_manager.discard_changes(file_path))

        menu.exec(self.changes_tree.viewport().mapToGlobal(position))

    def show_error(self, message: str):
        """Show error message in status bar"""
        self.status_label.setStyleSheet("""
            QLabel {
                color: #FF6B68;
                padding: 5px;
                background: #2D2D2D;
            }
        """)
        self.status_label.setText(message)

    def show_success(self, message: str):
        """Show success message in status bar"""
        self.status_label.setStyleSheet("""
            QLabel {
                color: #89D185;
                padding: 5px;
                background: #2D2D2D;
            }
        """)
        self.status_label.setText(message)
