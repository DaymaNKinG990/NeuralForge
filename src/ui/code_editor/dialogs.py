"""Find and replace dialogs for code editor."""
from PyQt6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QCheckBox
)
from PyQt6.QtGui import QTextDocument

class FindDialog(QDialog):
    """Dialog for finding text in the editor."""
    
    def __init__(self, editor: 'CodeEditor') -> None:
        """Initialize the find dialog.
        
        Args:
            editor: Parent editor widget
        """
        super().__init__(editor)
        self.editor = editor
        self.setWindowTitle("Find")
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Search input
        search_layout = QHBoxLayout()
        self.search_label = QLabel("Find:")
        self.search_input = QLineEdit()
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Options
        self.case_sensitive = QCheckBox("Case sensitive")
        self.whole_words = QCheckBox("Whole words")
        layout.addWidget(self.case_sensitive)
        layout.addWidget(self.whole_words)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.find_next_btn = QPushButton("Find Next")
        self.find_prev_btn = QPushButton("Find Previous")
        self.close_btn = QPushButton("Close")
        button_layout.addWidget(self.find_next_btn)
        button_layout.addWidget(self.find_prev_btn)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.find_next_btn.clicked.connect(self.find_next)
        self.find_prev_btn.clicked.connect(self.find_previous)
        self.close_btn.clicked.connect(self.close)
        
    def find_next(self):
        """Find the next occurrence of the search text."""
        self._find(QTextDocument.FindFlag(0))
        
    def find_previous(self):
        """Find the previous occurrence of the search text."""
        self._find(QTextDocument.FindFlag.FindBackward)
        
    def _find(self, direction: QTextDocument.FindFlag):
        """Find text in the specified direction.
        
        Args:
            direction: Search direction flag
        """
        flags = direction
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self.whole_words.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords
            
        text = self.search_input.text()
        if not self.editor.find(text, flags):
            # Wrap around
            cursor = self.editor.textCursor()
            cursor.movePosition(
                cursor.Start if direction == QTextDocument.FindFlag(0)
                else cursor.End
            )
            self.editor.setTextCursor(cursor)
            self.editor.find(text, flags)

class ReplaceDialog(FindDialog):
    """Dialog for finding and replacing text in the editor."""
    
    def setup_ui(self):
        """Set up the dialog UI."""
        super().setup_ui()
        
        # Add replace input
        replace_layout = QHBoxLayout()
        self.replace_label = QLabel("Replace with:")
        self.replace_input = QLineEdit()
        replace_layout.addWidget(self.replace_label)
        replace_layout.addWidget(self.replace_input)
        
        # Add replace buttons
        replace_btn_layout = QHBoxLayout()
        self.replace_btn = QPushButton("Replace")
        self.replace_all_btn = QPushButton("Replace All")
        replace_btn_layout.addWidget(self.replace_btn)
        replace_btn_layout.addWidget(self.replace_all_btn)
        
        # Insert replace widgets after search widgets
        layout = self.layout()
        layout.insertLayout(1, replace_layout)
        layout.insertLayout(4, replace_btn_layout)
        
        # Connect signals
        self.replace_btn.clicked.connect(self.replace)
        self.replace_all_btn.clicked.connect(self.replace_all)
        
    def replace(self):
        """Replace the current selection and find the next occurrence."""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
        self.find_next()
        
    def replace_all(self):
        """Replace all occurrences of the search text."""
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        
        cursor.movePosition(cursor.Start)
        self.editor.setTextCursor(cursor)
        
        count = 0
        while self.editor.find(
            self.search_input.text(),
            QTextDocument.FindFlag(0)
        ):
            cursor = self.editor.textCursor()
            cursor.insertText(self.replace_input.text())
            count += 1
            
        cursor.endEditBlock()
        
        # Show message with count of replacements
        QMessageBox.information(
            self,
            "Replace All",
            f"Replaced {count} occurrences."
        )
