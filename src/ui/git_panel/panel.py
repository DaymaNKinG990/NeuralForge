"""Main Git panel module for version control operations."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QInputDialog, 
    QListWidget, QSplitter, QTabWidget, QMenu,
    QProgressDialog, QApplication
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QCursor
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import threading
import time

from .dialogs import (
    CommitDialog, CloneDialog, RemoteManagerDialog,
    StashDialog, MergeConflictDialog
)
from .widgets import (
    GitStatusTree, GitToolbar, GitHistoryView,
    GitBranchView, GitStashView
)
from ...utils.git_manager import GitManager, GitFile, FileStatus
from ...utils.caching import cache_result
from ..styles.style_manager import StyleManager

class GitPanel(QWidget):
    """Main Git panel widget with enhanced Git functionality."""
    
    # Signals for Git operations
    operation_started = pyqtSignal(str)
    operation_completed = pyqtSignal(str)
    operation_failed = pyqtSignal(str, str)
    repository_changed = pyqtSignal(Path)
    branch_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize Git panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.git_manager = GitManager()
        self.style_manager = StyleManager()
        self.setup_ui()
        self.connect_signals()
        self.setup_auto_refresh()
        
    def setup_ui(self):
        """Set up the enhanced panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Git toolbar with extended functionality
        self.toolbar = GitToolbar()
        layout.addWidget(self.toolbar)
        
        # Main splitter for flexible layout
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Branch and status information
        self.left_tabs = QTabWidget()
        self.branch_view = GitBranchView()
        self.status_tree = GitStatusTree()
        self.stash_view = GitStashView()
        
        self.left_tabs.addTab(self.branch_view, "Branches")
        self.left_tabs.addTab(self.status_tree, "Changes")
        self.left_tabs.addTab(self.stash_view, "Stashes")
        
        # Right side: History and details
        self.right_tabs = QTabWidget()
        self.history_view = GitHistoryView()
        
        self.right_tabs.addTab(self.history_view, "History")
        
        self.main_splitter.addWidget(self.left_tabs)
        self.main_splitter.addWidget(self.right_tabs)
        
        layout.addWidget(self.main_splitter)
        
    def connect_signals(self):
        """Connect widget signals to slots with enhanced error handling."""
        # Toolbar signals
        self.toolbar.branch_clicked.connect(self.show_branch_dialog)
        self.toolbar.remote_clicked.connect(self.show_remote_manager)
        self.toolbar.clone_clicked.connect(self.show_clone_dialog)
        self.toolbar.commit_clicked.connect(self.show_commit_dialog)
        self.toolbar.push_clicked.connect(self.push_changes)
        self.toolbar.pull_clicked.connect(self.pull_changes)
        self.toolbar.stash_clicked.connect(self.show_stash_dialog)
        self.toolbar.settings_clicked.connect(self.show_git_settings)
        
        # Status tree signals
        self.status_tree.file_staged.connect(self.stage_file)
        self.status_tree.file_unstaged.connect(self.unstage_file)
        self.status_tree.files_dropped.connect(self.handle_dropped_files)
        
        # Branch view signals
        self.branch_view.branch_selected.connect(self.checkout_branch)
        self.branch_view.branch_created.connect(self.create_branch)
        self.branch_view.branch_deleted.connect(self.delete_branch)
        self.branch_view.branch_merged.connect(self.merge_branch)
        
        # History view signals
        self.history_view.commit_selected.connect(self.show_commit_details)
        self.history_view.commit_checkout.connect(self.checkout_commit)
        self.history_view.commit_cherry_pick.connect(self.cherry_pick_commit)
        
        # Operation signals
        self.operation_started.connect(self.show_progress)
        self.operation_completed.connect(self.hide_progress)
        self.operation_failed.connect(self.show_error)
        
    def setup_auto_refresh(self):
        """Set up automatic refresh of Git status."""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
        
    @cache_result(ttl=5)  # Cache results for 5 seconds
    def get_repository_status(self) -> Dict:
        """Get cached repository status."""
        return self.git_manager.get_status()
        
    def refresh_all(self):
        """Refresh all Git-related views."""
        try:
            self.refresh_status()
            self.branch_view.refresh()
            self.history_view.refresh()
            self.stash_view.refresh()
        except Exception as e:
            self.show_error("Refresh Error", str(e))
            
    def execute_git_operation(self, operation_name: str, func, *args, **kwargs):
        """Execute a Git operation with progress feedback.
        
        Args:
            operation_name: Name of the operation
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        self.operation_started.emit(operation_name)
        
        try:
            result = func(*args, **kwargs)
            self.operation_completed.emit(operation_name)
            self.refresh_all()
            return result
        except Exception as e:
            self.operation_failed.emit(operation_name, str(e))
            raise
            
    def show_progress(self, operation: str):
        """Show progress dialog for long operations.
        
        Args:
            operation: Operation name
        """
        self.progress = QProgressDialog(
            f"Executing {operation}...",
            "Cancel",
            0,
            0,
            self
        )
        self.progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress.show()
        QApplication.processEvents()
        
    def hide_progress(self, operation: str):
        """Hide progress dialog.
        
        Args:
            operation: Operation name
        """
        if hasattr(self, 'progress'):
            self.progress.close()
            
    def show_error(self, operation: str, error: str):
        """Show error message.
        
        Args:
            operation: Failed operation
            error: Error message
        """
        QMessageBox.critical(
            self,
            f"{operation} Failed",
            f"Error during {operation.lower()}: {error}"
        )
        
    def show_stash_dialog(self):
        """Show stash management dialog."""
        dialog = StashDialog(self.git_manager, self)
        if dialog.exec():
            self.refresh_all()
            
    def show_git_settings(self):
        """Show Git settings dialog."""
        # Implementation for Git settings dialog
        pass
        
    def handle_dropped_files(self, files: List[Path]):
        """Handle files dropped onto status tree.
        
        Args:
            files: List of file paths
        """
        try:
            for file in files:
                self.git_manager.stage_file(file)
            self.refresh_status()
        except Exception as e:
            self.show_error("File Drop", str(e))
            
    def checkout_commit(self, commit_hash: str):
        """Checkout specific commit.
        
        Args:
            commit_hash: Commit hash to checkout
        """
        self.execute_git_operation(
            "Checkout Commit",
            self.git_manager.checkout_commit,
            commit_hash
        )
        
    def cherry_pick_commit(self, commit_hash: str):
        """Cherry-pick commit to current branch.
        
        Args:
            commit_hash: Commit hash to cherry-pick
        """
        self.execute_git_operation(
            "Cherry-pick",
            self.git_manager.cherry_pick,
            commit_hash
        )
        
    def create_branch(self, name: str, start_point: Optional[str] = None):
        """Create new branch.
        
        Args:
            name: Branch name
            start_point: Starting point for branch
        """
        self.execute_git_operation(
            "Create Branch",
            self.git_manager.create_branch,
            name,
            start_point
        )
        
    def delete_branch(self, name: str, force: bool = False):
        """Delete branch.
        
        Args:
            name: Branch name
            force: Force deletion
        """
        self.execute_git_operation(
            "Delete Branch",
            self.git_manager.delete_branch,
            name,
            force
        )
        
    def merge_branch(self, source: str):
        """Merge branch into current branch.
        
        Args:
            source: Source branch name
        """
        try:
            result = self.execute_git_operation(
                "Merge Branch",
                self.git_manager.merge_branch,
                source
            )
            
            if result.has_conflicts:
                dialog = MergeConflictDialog(
                    self.git_manager,
                    result.conflicts,
                    self
                )
                dialog.exec()
                
            self.refresh_all()
        except Exception as e:
            self.show_error("Merge", str(e))
            
    def show_context_menu(self, position: QCursor):
        """Show context menu for Git operations.
        
        Args:
            position: Menu position
        """
        menu = QMenu(self)
        
        # Add context-specific actions
        selected_items = self.status_tree.selectedItems()
        if selected_items:
            menu.addAction("Stage Selected", self.stage_selected)
            menu.addAction("Unstage Selected", self.unstage_selected)
            menu.addAction("Revert Selected", self.revert_selected)
            
        # Add general actions
        menu.addSeparator()
        menu.addAction("Refresh", self.refresh_all)
        menu.addAction("Clean Working Directory", self.clean_working_dir)
        
        menu.exec(position)
        
    def set_repository(self, repo_path: Path):
        """Set the current Git repository.
        
        Args:
            repo_path: Path to Git repository
        """
        try:
            self.git_manager.set_repository(repo_path)
            self.refresh_status()
            self.update_branch_display()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Repository Error",
                f"Failed to set repository: {str(e)}"
            )
            
    def refresh_status(self):
        """Refresh Git status display."""
        try:
            status = self.git_manager.get_status()
            self.status_tree.update_status(status)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Status Error",
                f"Failed to get Git status: {str(e)}"
            )
            
    def update_branch_display(self):
        """Update current branch display."""
        try:
            branch = self.git_manager.get_current_branch()
            self.toolbar.set_branch(branch)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Branch Error",
                f"Failed to get current branch: {str(e)}"
            )
            
    def show_branch_dialog(self):
        """Show branch management dialog."""
        try:
            branches = self.git_manager.get_branches()
            current = self.git_manager.get_current_branch()
            
            branch, ok = QInputDialog.getItem(
                self,
                "Switch Branch",
                "Select branch:",
                branches,
                branches.index(current),
                False
            )
            
            if ok and branch:
                self.git_manager.checkout_branch(branch)
                self.update_branch_display()
                self.refresh_status()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Branch Error",
                f"Failed to manage branches: {str(e)}"
            )
            
    def show_remote_manager(self):
        """Show remote manager dialog."""
        dialog = RemoteManagerDialog(self.git_manager, self)
        dialog.exec()
        
    def show_clone_dialog(self):
        """Show clone repository dialog."""
        dialog = CloneDialog(self)
        if dialog.exec():
            url = dialog.url_input.text().strip()
            path = dialog.dir_input.text().strip()
            
            try:
                self.git_manager.clone_repository(url, path)
                self.set_repository(Path(path))
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Clone Error",
                    f"Failed to clone repository: {str(e)}"
                )
                
    def show_commit_dialog(self):
        """Show commit changes dialog."""
        dialog = CommitDialog(self)
        if dialog.exec():
            message = dialog.message_edit.toPlainText().strip()
            
            try:
                self.git_manager.commit(message)
                self.refresh_status()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Commit Error",
                    f"Failed to commit changes: {str(e)}"
                )
                
    def push_changes(self):
        """Push committed changes to remote."""
        try:
            self.git_manager.push()
            QMessageBox.information(
                self,
                "Push Successful",
                "Changes pushed to remote repository."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Push Error",
                f"Failed to push changes: {str(e)}"
            )
            
    def pull_changes(self):
        """Pull changes from remote."""
        try:
            self.git_manager.pull()
            self.refresh_status()
            QMessageBox.information(
                self,
                "Pull Successful",
                "Changes pulled from remote repository."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Pull Error",
                f"Failed to pull changes: {str(e)}"
            )
            
    def stage_file(self, git_file: GitFile):
        """Stage a file for commit.
        
        Args:
            git_file: Git file to stage
        """
        try:
            self.git_manager.stage_file(git_file.path)
            self.refresh_status()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Stage Error",
                f"Failed to stage file: {str(e)}"
            )
            
    def unstage_file(self, git_file: GitFile):
        """Unstage a file from commit.
        
        Args:
            git_file: Git file to unstage
        """
        try:
            self.git_manager.unstage_file(git_file.path)
            self.refresh_status()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Unstage Error",
                f"Failed to unstage file: {str(e)}"
            )
