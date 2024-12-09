"""Custom widgets for Git panel."""
from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget,
    QHBoxLayout, QPushButton, QLabel, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QColor
from pathlib import Path
from typing import Dict, List
from ...utils.git_manager import GitFile, FileStatus
from ..styles.style_manager import StyleManager
from ..styles.style_enums import StyleClass

class GitStatusTree(QTreeWidget):
    """Tree widget for displaying Git status."""
    
    file_staged = pyqtSignal(GitFile)
    file_unstaged = pyqtSignal(GitFile)
    
    def __init__(self, parent=None):
        """Initialize Git status tree.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the tree widget UI."""
        self.setHeaderLabels(["File", "Status"])
        self.setStyleSheet(
            self.style_manager.get_component_style(StyleClass.TREE_VIEW)
        )
        self.setSelectionMode(
            QTreeWidget.SelectionMode.ExtendedSelection
        )
        
    def update_status(self, files: List[GitFile]):
        """Update the tree with current Git status.
        
        Args:
            files: List of Git files with status
        """
        self.clear()
        
        # Create root items for staged and unstaged changes
        staged = QTreeWidgetItem(["Staged Changes"])
        unstaged = QTreeWidgetItem(["Unstaged Changes"])
        
        # Add files to appropriate sections
        for git_file in files:
            file_path = str(git_file.path)
            status_name = git_file.status.name
            
            item = QTreeWidgetItem([file_path, status_name])
            
            # Set colors based on status
            if git_file.status == FileStatus.ADDED:
                item.setForeground(1, QColor("#28a745"))
            elif git_file.status == FileStatus.MODIFIED:
                item.setForeground(1, QColor("#f9c74f"))
            elif git_file.status == FileStatus.DELETED:
                item.setForeground(1, QColor("#e63946"))
            elif git_file.status == FileStatus.RENAMED:
                item.setForeground(1, QColor("#4cc9f0"))
                
            if git_file.staged:
                staged.addChild(item)
            else:
                unstaged.addChild(item)
                
        # Only add root items if they have children
        if staged.childCount() > 0:
            self.addTopLevelItem(staged)
            staged.setExpanded(True)
            
        if unstaged.childCount() > 0:
            self.addTopLevelItem(unstaged)
            unstaged.setExpanded(True)

class GitToolbar(QWidget):
    """Toolbar for Git operations."""
    
    branch_clicked = pyqtSignal()
    remote_clicked = pyqtSignal()
    clone_clicked = pyqtSignal()
    commit_clicked = pyqtSignal()
    push_clicked = pyqtSignal()
    pull_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize Git toolbar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the toolbar UI."""
        self.setStyleSheet(
            self.style_manager.get_component_style(StyleClass.TOOL_BAR)
        )
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Get icons path relative to this file's location
        icons_path = Path(__file__).parent.parent / 'resources' / 'icons'
        
        # Branch selector
        self.branch_label = QLabel("Branch:")
        self.branch_label.setStyleSheet(
            self.style_manager.get_component_style(StyleClass.LABEL)
        )
        self.branch_button = QPushButton()
        self.branch_button.setIcon(QIcon(str(icons_path / "git-branch.svg")))
        self.branch_button.setStyleSheet(
            self.style_manager.get_component_style(StyleClass.BUTTON)
        )
        
        # Git operations
        self.remote_btn = QPushButton("Remotes")
        self.clone_btn = QPushButton(QIcon(str(icons_path / "git-clone.svg")), "")
        self.commit_btn = QPushButton(QIcon(str(icons_path / "git-commit.svg")), "")
        self.push_btn = QPushButton(QIcon(str(icons_path / "git-push.svg")), "")
        self.pull_btn = QPushButton(QIcon(str(icons_path / "git-pull.svg")), "")
        
        for btn in [
            self.clone_btn, self.commit_btn,
            self.push_btn, self.pull_btn
        ]:
            btn.setStyleSheet(
                self.style_manager.get_component_style(StyleClass.BUTTON)
            )
            btn.setIconSize(QSize(16, 16))
            
        # Add widgets to layout
        layout.addWidget(self.branch_label)
        layout.addWidget(self.branch_button)
        layout.addStretch()
        layout.addWidget(self.remote_btn)
        layout.addWidget(self.clone_btn)
        layout.addWidget(self.commit_btn)
        layout.addWidget(self.push_btn)
        layout.addWidget(self.pull_btn)
        
        # Connect signals
        self.branch_button.clicked.connect(self.branch_clicked)
        self.remote_btn.clicked.connect(self.remote_clicked)
        self.clone_btn.clicked.connect(self.clone_clicked)
        self.commit_btn.clicked.connect(self.commit_clicked)
        self.push_btn.clicked.connect(self.push_clicked)
        self.pull_btn.clicked.connect(self.pull_clicked)
        
    def set_branch(self, branch_name: str):
        """Set the current branch name.
        
        Args:
            branch_name: Name of current branch
        """
        self.branch_button.setText(branch_name)

class GitHistoryView(QTreeWidget):
    """Tree widget for displaying Git commit history."""
    
    commit_selected = pyqtSignal(str)  # Commit hash
    commit_checkout = pyqtSignal(str)  # Commit hash
    commit_cherry_pick = pyqtSignal(str)  # Commit hash
    
    def __init__(self, parent=None):
        """Initialize Git history view.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the tree widget UI."""
        self.setHeaderLabels([
            "Hash", "Author", "Date", "Message", "Branch"
        ])
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(
            self.style_manager.get_component_style(StyleClass.TREE_VIEW)
        )
        
    def update_history(self, commits: List[Dict]):
        """Update history with commits.
        
        Args:
            commits: List of commit information
        """
        self.clear()
        for commit in commits:
            item = QTreeWidgetItem([
                commit['hash'][:8],
                commit['author'],
                commit['date'],
                commit['message'],
                commit.get('branch', '')
            ])
            self.addTopLevelItem(item)
            
    def show_context_menu(self, position):
        """Show context menu for commit operations.
        
        Args:
            position: Menu position
        """
        item = self.itemAt(position)
        if item:
            menu = QMenu(self)
            checkout_action = menu.addAction("Checkout")
            cherry_pick_action = menu.addAction("Cherry Pick")
            
            action = menu.exec(self.viewport().mapToGlobal(position))
            commit_hash = item.text(0)
            
            if action == checkout_action:
                self.commit_checkout.emit(commit_hash)
            elif action == cherry_pick_action:
                self.commit_cherry_pick.emit(commit_hash)

class GitBranchView(QTreeWidget):
    """Tree widget for displaying and managing Git branches."""
    
    branch_selected = pyqtSignal(str)  # Branch name
    branch_created = pyqtSignal(str, str)  # Branch name, start point
    branch_deleted = pyqtSignal(str, bool)  # Branch name, force
    branch_merged = pyqtSignal(str)  # Source branch
    
    def __init__(self, parent=None):
        """Initialize Git branch view.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the tree widget UI."""
        self.setHeaderLabels(["Branch", "Last Commit"])
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(
            self.style_manager.get_component_style(StyleClass.TREE_VIEW)
        )
        
    def update_branches(self, branches: List[Dict]):
        """Update branch list.
        
        Args:
            branches: List of branch information
        """
        self.clear()
        
        # Create root items for local and remote branches
        local_root = QTreeWidgetItem(["Local Branches"])
        remote_root = QTreeWidgetItem(["Remote Branches"])
        
        for branch in branches:
            item = QTreeWidgetItem([
                branch['name'],
                branch['last_commit']
            ])
            
            if branch.get('is_current'):
                item.setForeground(0, QColor("#28a745"))
                
            if branch.get('is_remote'):
                remote_root.addChild(item)
            else:
                local_root.addChild(item)
                
        if local_root.childCount() > 0:
            self.addTopLevelItem(local_root)
            local_root.setExpanded(True)
            
        if remote_root.childCount() > 0:
            self.addTopLevelItem(remote_root)
            
    def show_context_menu(self, position):
        """Show context menu for branch operations.
        
        Args:
            position: Menu position
        """
        item = self.itemAt(position)
        if item and item.parent():  # Only show menu for branch items
            menu = QMenu(self)
            checkout_action = menu.addAction("Checkout")
            merge_action = menu.addAction("Merge into Current")
            delete_action = menu.addAction("Delete")
            force_delete_action = menu.addAction("Force Delete")
            
            action = menu.exec(self.viewport().mapToGlobal(position))
            branch_name = item.text(0)
            
            if action == checkout_action:
                self.branch_selected.emit(branch_name)
            elif action == merge_action:
                self.branch_merged.emit(branch_name)
            elif action == delete_action:
                self.branch_deleted.emit(branch_name, False)
            elif action == force_delete_action:
                self.branch_deleted.emit(branch_name, True)

class GitStashView(QTreeWidget):
    """Tree widget for displaying Git stashes."""
    
    stash_selected = pyqtSignal(str)  # Stash name
    stash_applied = pyqtSignal(str)  # Stash name
    stash_popped = pyqtSignal(str)  # Stash name
    stash_dropped = pyqtSignal(str)  # Stash name
    
    def __init__(self, parent=None):
        """Initialize Git stash view.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the tree widget UI."""
        self.setHeaderLabels(["Name", "Message", "Date"])
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(
            self.style_manager.get_component_style(StyleClass.TREE_VIEW)
        )
        
    def update_stashes(self, stashes: List[Dict]):
        """Update stash list.
        
        Args:
            stashes: List of stash information
        """
        self.clear()
        for stash in stashes:
            item = QTreeWidgetItem([
                stash['name'],
                stash['message'],
                stash['date']
            ])
            self.addTopLevelItem(item)
            
    def show_context_menu(self, position):
        """Show context menu for stash operations.
        
        Args:
            position: Menu position
        """
        item = self.itemAt(position)
        if item:
            menu = QMenu(self)
            apply_action = menu.addAction("Apply")
            pop_action = menu.addAction("Pop")
            drop_action = menu.addAction("Drop")
            
            action = menu.exec(self.viewport().mapToGlobal(position))
            stash_name = item.text(0)
            
            if action == apply_action:
                self.stash_applied.emit(stash_name)
            elif action == pop_action:
                self.stash_popped.emit(stash_name)
            elif action == drop_action:
                self.stash_dropped.emit(stash_name)
