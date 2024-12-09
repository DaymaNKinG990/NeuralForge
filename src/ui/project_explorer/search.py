"""File search functionality for project explorer."""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal
from ..styles.style_manager import StyleManager
from ..styles.style_enums import StyleClass

class FileSearchBar(QWidget):
    """Search bar for filtering project files."""
    
    # Signals
    search_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize file search bar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the search bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_input)
        
        # Apply styles
        self.search_input.setStyleSheet(
            self.style_manager.get_component_style(StyleClass.LINE_EDIT)
        )
        
    def clear_search(self):
        """Clear search input."""
        self.search_input.clear()
        
    def set_focus(self):
        """Set focus to search input."""
        self.search_input.setFocus(Qt.FocusReason.OtherFocusReason)
        
    def get_search_text(self) -> str:
        """Get current search text.
        
        Returns:
            Current search text
        """
        return self.search_input.text()
