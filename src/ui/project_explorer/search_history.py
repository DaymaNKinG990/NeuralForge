"""Search history management for project explorer."""
from typing import List, Optional
from datetime import datetime
import json
import logging
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from ..settings.settings_manager import SettingsManager

logger = logging.getLogger(__name__)

class SearchHistoryManager(QObject):
    """Manager for search history."""
    
    history_updated = pyqtSignal()  # Emits when history changes
    
    def __init__(self, settings: SettingsManager):
        """Initialize search history manager.
        
        Args:
            settings: Settings manager instance
        """
        super().__init__()
        self.settings = settings
        self.max_history = 100  # Maximum number of history entries
        
    def add_search(self, query: str, file_type: Optional[str] = None):
        """Add search query to history.
        
        Args:
            query: Search query
            file_type: Optional file type filter
        """
        if not query.strip():
            return
            
        history = self.get_history()
        entry = {
            'query': query,
            'file_type': file_type,
            'timestamp': datetime.now().isoformat()
        }
        
        # Remove duplicate if exists
        history = [h for h in history if h['query'] != query]
        
        # Add new entry and trim history
        history.insert(0, entry)
        if len(history) > self.max_history:
            history = history[:self.max_history]
            
        self.settings.set_section('search_history', {'entries': history})
        self.history_updated.emit()
        
    def get_history(self) -> List[dict]:
        """Get search history.
        
        Returns:
            List of history entries
        """
        section = self.settings.get_section('search_history')
        return section.get('entries', [])
        
    def clear_history(self):
        """Clear search history."""
        self.settings.set_section('search_history', {'entries': []})
        self.history_updated.emit()
        
    def get_recent_queries(self, limit: Optional[int] = None) -> List[str]:
        """Get recent search queries.
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of recent queries
        """
        history = self.get_history()
        queries = [entry['query'] for entry in history]
        return queries[:limit] if limit else queries
        
    def get_popular_queries(self, limit: Optional[int] = None) -> List[str]:
        """Get most popular search queries.
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of popular queries
        """
        history = self.get_history()
        query_counts = {}
        for entry in history:
            query = entry['query']
            query_counts[query] = query_counts.get(query, 0) + 1
            
        sorted_queries = sorted(
            query_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        queries = [query for query, _ in sorted_queries]
        return queries[:limit] if limit else queries
        
    def get_file_type_stats(self) -> dict:
        """Get statistics about searched file types.
        
        Returns:
            Dictionary of file type statistics
        """
        history = self.get_history()
        type_counts = {}
        for entry in history:
            file_type = entry.get('file_type')
            if file_type:
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
                
        return type_counts
