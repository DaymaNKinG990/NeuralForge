"""Chat history management for LLM workspace."""
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from ..settings.settings_manager import SettingsManager

logger = logging.getLogger(__name__)

class Message:
    """Chat message class."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        """Initialize message.
        
        Args:
            role: Message role (user/assistant)
            content: Message content
            timestamp: Optional timestamp string
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
        
    def to_dict(self) -> dict:
        """Convert message to dictionary.
        
        Returns:
            Message dictionary
        """
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """Create message from dictionary.
        
        Args:
            data: Message dictionary
            
        Returns:
            Message instance
        """
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=data['timestamp']
        )

class Conversation:
    """Chat conversation class."""
    
    def __init__(self, title: str, model: str, messages: Optional[List[Message]] = None):
        """Initialize conversation.
        
        Args:
            title: Conversation title
            model: Model name
            messages: Optional list of messages
        """
        self.title = title
        self.model = model
        self.messages = messages or []
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        
    def add_message(self, message: Message):
        """Add message to conversation.
        
        Args:
            message: Message to add
        """
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()
        
    def to_dict(self) -> dict:
        """Convert conversation to dictionary.
        
        Returns:
            Conversation dictionary
        """
        return {
            'title': self.title,
            'model': self.model,
            'messages': [m.to_dict() for m in self.messages],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Conversation':
        """Create conversation from dictionary.
        
        Args:
            data: Conversation dictionary
            
        Returns:
            Conversation instance
        """
        conv = cls(
            title=data['title'],
            model=data['model']
        )
        conv.messages = [Message.from_dict(m) for m in data['messages']]
        conv.created_at = data['created_at']
        conv.updated_at = data['updated_at']
        return conv

class ChatHistoryManager(QObject):
    """Manager for chat history."""
    
    conversation_added = pyqtSignal(str)  # Emits conversation ID
    conversation_updated = pyqtSignal(str)  # Emits conversation ID
    conversation_deleted = pyqtSignal(str)  # Emits conversation ID
    
    def __init__(self, settings: SettingsManager):
        """Initialize chat history manager.
        
        Args:
            settings: Settings manager instance
        """
        super().__init__()
        self.settings = settings
        self.conversations: Dict[str, Conversation] = {}
        self.load_conversations()
        
    def load_conversations(self):
        """Load conversations from settings."""
        section = self.settings.get_section('chat_history')
        for conv_id, data in section.items():
            self.conversations[conv_id] = Conversation.from_dict(data)
            
    def save_conversations(self):
        """Save conversations to settings."""
        section = {
            conv_id: conv.to_dict()
            for conv_id, conv in self.conversations.items()
        }
        self.settings.set_section('chat_history', section)
        
    def create_conversation(self, title: str, model: str) -> str:
        """Create new conversation.
        
        Args:
            title: Conversation title
            model: Model name
            
        Returns:
            Conversation ID
        """
        conv_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.conversations[conv_id] = Conversation(title, model)
        self.save_conversations()
        self.conversation_added.emit(conv_id)
        return conv_id
        
    def add_message(self, conv_id: str, role: str, content: str):
        """Add message to conversation.
        
        Args:
            conv_id: Conversation ID
            role: Message role
            content: Message content
        """
        if conv_id not in self.conversations:
            return
            
        message = Message(role, content)
        self.conversations[conv_id].add_message(message)
        self.save_conversations()
        self.conversation_updated.emit(conv_id)
        
    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        """Get conversation by ID.
        
        Args:
            conv_id: Conversation ID
            
        Returns:
            Conversation instance or None
        """
        return self.conversations.get(conv_id)
        
    def get_conversations(self) -> List[tuple]:
        """Get all conversations.
        
        Returns:
            List of (ID, conversation) tuples
        """
        return sorted(
            self.conversations.items(),
            key=lambda x: x[1].updated_at,
            reverse=True
        )
        
    def delete_conversation(self, conv_id: str):
        """Delete conversation.
        
        Args:
            conv_id: Conversation ID
        """
        if conv_id in self.conversations:
            del self.conversations[conv_id]
            self.save_conversations()
            self.conversation_deleted.emit(conv_id)
            
    def clear_history(self):
        """Clear all conversations."""
        self.conversations.clear()
        self.save_conversations()
        
    def export_conversation(self, conv_id: str, path: Path):
        """Export conversation to file.
        
        Args:
            conv_id: Conversation ID
            path: Export file path
        """
        if conv_id not in self.conversations:
            return
            
        try:
            with open(path, 'w') as f:
                json.dump(
                    self.conversations[conv_id].to_dict(),
                    f,
                    indent=2
                )
        except Exception as e:
            logger.error(f"Failed to export conversation: {str(e)}")
            
    def import_conversation(self, path: Path) -> Optional[str]:
        """Import conversation from file.
        
        Args:
            path: Import file path
            
        Returns:
            Conversation ID if successful
        """
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
            conv = Conversation.from_dict(data)
            conv_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.conversations[conv_id] = conv
            self.save_conversations()
            self.conversation_added.emit(conv_id)
            return conv_id
            
        except Exception as e:
            logger.error(f"Failed to import conversation: {str(e)}")
            return None
