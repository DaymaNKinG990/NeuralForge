from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QMessageBox, QMenu, QInputDialog)
from PyQt6.QtCore import Qt
from ...utils.git_manager import GitManager

class RemoteManagerDialog(QDialog):
    def __init__(self, git_manager: GitManager, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.setWindowTitle("Remote Manager")
        self.setup_ui()
        self.refresh_remotes()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Remote list
        self.remotes_table = QTableWidget()
        self.remotes_table.setColumnCount(2)
        self.remotes_table.setHorizontalHeaderLabels(["Name", "URL"])
        self.remotes_table.horizontalHeader().setStretchLastSection(True)
        self.remotes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.remotes_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.remotes_table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.remotes_table)
        
        # Add remote section
        add_layout = QHBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Remote name")
        add_layout.addWidget(self.name_input)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Remote URL")
        add_layout.addWidget(self.url_input)
        
        self.add_btn = QPushButton("Add Remote")
        self.add_btn.clicked.connect(self.add_remote)
        add_layout.addWidget(self.add_btn)
        
        layout.addLayout(add_layout)
        
        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)
        
        self.setMinimumWidth(600)
        self.setStyleSheet("""
            QDialog {
                background: #2D2D2D;
            }
            QTableWidget {
                background: #1E1E1E;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                gridline-color: #3C3C3C;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background: #094771;
            }
            QHeaderView::section {
                background: #2D2D2D;
                color: #CCCCCC;
                padding: 5px;
                border: 1px solid #3C3C3C;
            }
            QLineEdit {
                background: #1E1E1E;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                border-radius: 3px;
                padding: 5px;
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
            QPushButton#close_btn {
                background: #4D4D4D;
            }
            QPushButton#close_btn:hover {
                background: #5A5A5A;
            }
        """)
        
        self.close_btn.setObjectName("close_btn")
        
    def refresh_remotes(self):
        """Refresh the remotes table"""
        self.remotes_table.setRowCount(0)
        remotes = self.git_manager.get_remotes()
        
        for row, (name, url) in enumerate(remotes.items()):
            self.remotes_table.insertRow(row)
            self.remotes_table.setItem(row, 0, QTableWidgetItem(name))
            self.remotes_table.setItem(row, 1, QTableWidgetItem(url))
            
    def add_remote(self):
        """Add a new remote"""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        
        if not name or not url:
            QMessageBox.warning(self, "Error", "Please enter both name and URL")
            return
            
        if self.git_manager.add_remote(name, url):
            self.name_input.clear()
            self.url_input.clear()
            self.refresh_remotes()
            
    def show_context_menu(self, pos):
        """Show context menu for remote"""
        item = self.remotes_table.itemAt(pos)
        if not item:
            return
            
        row = item.row()
        remote_name = self.remotes_table.item(row, 0).text()
        
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
        
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec(self.remotes_table.viewport().mapToGlobal(pos))
        
        if action == rename_action:
            self.rename_remote(remote_name)
        elif action == delete_action:
            self.delete_remote(remote_name)
            
    def rename_remote(self, old_name: str):
        """Rename a remote"""
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Remote",
            f"Enter new name for remote '{old_name}':",
            QLineEdit.EchoMode.Normal,
            old_name
        )
        
        if ok and new_name:
            if self.git_manager.rename_remote(old_name, new_name):
                self.refresh_remotes()
                
    def delete_remote(self, name: str):
        """Delete a remote"""
        reply = QMessageBox.question(
            self,
            "Delete Remote",
            f"Are you sure you want to delete remote '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.git_manager.remove_remote(name):
                self.refresh_remotes()
