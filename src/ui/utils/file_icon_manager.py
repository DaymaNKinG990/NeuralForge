"""File icon manager for programming language icons."""
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
import os
from typing import Dict, Optional

class FileIconManager:
    """Manager for file icons based on programming languages."""
    
    def __init__(self):
        self.icons_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'resources',
            'icons',
            'languages'
        )
        self._load_icons()
        
    def _load_icons(self):
        """Load all language icons."""
        self.extension_to_icon: Dict[str, QIcon] = {}
        self.language_to_icon: Dict[str, QIcon] = {}
        
        # Map file extensions to language icons
        self.extension_map = {
            # Python
            '.py': 'python',
            '.pyw': 'python',
            '.pyx': 'python',
            '.pxd': 'python',
            '.pyi': 'python',
            # JavaScript
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            # Web
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'sass',
            '.sass': 'sass',
            '.less': 'less',
            # Java
            '.java': 'java',
            '.jar': 'java',
            '.class': 'java',
            # C/C++
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            # C#
            '.cs': 'csharp',
            # Ruby
            '.rb': 'ruby',
            '.erb': 'ruby',
            # PHP
            '.php': 'php',
            # Go
            '.go': 'go',
            # Rust
            '.rs': 'rust',
            # Swift
            '.swift': 'swift',
            # Kotlin
            '.kt': 'kotlin',
            # Scala
            '.scala': 'scala',
            # R
            '.r': 'r',
            '.R': 'r',
            # Shell
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell',
            # PowerShell
            '.ps1': 'powershell',
            # Markdown
            '.md': 'markdown',
            '.markdown': 'markdown',
            # JSON
            '.json': 'json',
            # YAML
            '.yml': 'yaml',
            '.yaml': 'yaml',
            # XML
            '.xml': 'xml',
            # SQL
            '.sql': 'sql',
            # Docker
            'Dockerfile': 'docker',
            '.dockerfile': 'docker',
            # Git
            '.git': 'git',
            '.gitignore': 'git',
            '.gitattributes': 'git',
            # Jupyter
            '.ipynb': 'jupyter',
            # Text
            '.txt': 'text',
            '.log': 'text',
            # Config
            '.conf': 'config',
            '.config': 'config',
            '.ini': 'config',
            # Binary
            '.exe': 'binary',
            '.dll': 'binary',
            '.so': 'binary',
            '.dylib': 'binary'
        }
        
        # Load icons for each language
        for ext, lang in self.extension_map.items():
            icon_path = os.path.join(self.icons_path, f"{lang}.svg")
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.extension_to_icon[ext] = icon
                self.language_to_icon[lang] = icon
                
        # Default icon for unknown file types
        default_icon_path = os.path.join(self.icons_path, "unknown.svg")
        self.default_icon = QIcon(default_icon_path) if os.path.exists(default_icon_path) else None
        
    def get_icon_for_file(self, filepath: str, size: QSize = QSize(16, 16)) -> Optional[QIcon]:
        """Get the appropriate icon for a file.
        
        Args:
            filepath: Path to the file
            size: Desired icon size
            
        Returns:
            QIcon for the file type or None if no icon found
        """
        # Get file extension
        _, ext = os.path.splitext(filepath)
        filename = os.path.basename(filepath)
        
        # Check exact filename matches first (e.g., Dockerfile)
        if filename in self.extension_map:
            lang = self.extension_map[filename]
            if lang in self.language_to_icon:
                icon = self.language_to_icon[lang]
                icon.setIsSidesEnabled(True)
                return icon
                
        # Check extension
        if ext in self.extension_to_icon:
            icon = self.extension_to_icon[ext]
            icon.setIsSidesEnabled(True)
            return icon
            
        return self.default_icon
        
    def get_icon_for_language(self, language: str, size: QSize = QSize(16, 16)) -> Optional[QIcon]:
        """Get icon for a specific programming language.
        
        Args:
            language: Programming language name
            size: Desired icon size
            
        Returns:
            QIcon for the language or None if no icon found
        """
        if language.lower() in self.language_to_icon:
            icon = self.language_to_icon[language.lower()]
            icon.setIsSidesEnabled(True)
            return icon
        return self.default_icon
