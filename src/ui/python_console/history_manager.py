"""Console history management."""
from typing import List, Optional
from PyQt6.QtCore import QObject, pyqtSignal

class ConsoleHistoryManager(QObject):
    """Manager for console command history."""
    
    history_item = pyqtSignal(str)  # Emits history item
    
    def __init__(self, max_items: int = 1000):
        """Initialize history manager.
        
        Args:
            max_items: Maximum history items
        """
        super().__init__()
        self.max_items = max_items
        self.items: List[str] = []
        self.current_index: Optional[int] = None
        
    def add_item(self, item: str):
        """Add item to history.
        
        Args:
            item: History item
        """
        # Don't add empty items or duplicates
        if not item.strip() or (self.items and item == self.items[-1]):
            return
            
        self.items.append(item)
        if len(self.items) > self.max_items:
            self.items.pop(0)
            
        self.current_index = None
        
    def get_previous(self) -> Optional[str]:
        """Get previous history item.
        
        Returns:
            Previous item or None
        """
        if not self.items:
            return None
            
        if self.current_index is None:
            self.current_index = len(self.items) - 1
        elif self.current_index > 0:
            self.current_index -= 1
            
        item = self.items[self.current_index]
        self.history_item.emit(item)
        return item
        
    def get_next(self) -> Optional[str]:
        """Get next history item.
        
        Returns:
            Next item or None
        """
        if not self.items or self.current_index is None:
            return None
            
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            item = self.items[self.current_index]
            self.history_item.emit(item)
            return item
        else:
            self.current_index = None
            self.history_item.emit("")
            return ""
            
    def clear(self):
        """Clear history."""
        self.items.clear()
        self.current_index = None
        
    def get_items(self) -> List[str]:
        """Get all history items.
        
        Returns:
            List of history items
        """
        return self.items.copy()
        
    def set_items(self, items: List[str]):
        """Set history items.
        
        Args:
            items: History items
        """
        self.items = items[-self.max_items:]
        self.current_index = None
