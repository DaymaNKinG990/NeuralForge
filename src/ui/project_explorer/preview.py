"""File preview widget for project explorer."""
from typing import Optional
from pathlib import Path
import mimetypes
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QTextEdit, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QImage, QTextCharFormat, QSyntaxHighlighter
from PyQt6.QtCore import Qt, pyqtSignal
from ..styles.style_manager import StyleManager
from ..styles.style_enums import StyleClass

logger = logging.getLogger(__name__)

class SyntaxHighlighter(QSyntaxHighlighter):
    """Basic syntax highlighter for code preview."""
    
    def __init__(self, parent=None):
        """Initialize syntax highlighter.
        
        Args:
            parent: Parent text document
        """
        super().__init__(parent)
        self.setup_formats()
        
    def setup_formats(self):
        """Set up text formats for different syntax elements."""
        # Keywords
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(Qt.GlobalColor.blue)
        self.keyword_format.setFontWeight(700)
        
        self.keywords = [
            'def', 'class', 'import', 'from', 'return',
            'if', 'else', 'elif', 'for', 'while', 'try',
            'except', 'finally', 'with', 'as', 'lambda',
            'yield', 'break', 'continue', 'pass', 'raise'
        ]
        
        # Strings
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(Qt.GlobalColor.darkGreen)
        
        # Comments
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(Qt.GlobalColor.darkGray)
        self.comment_format.setFontItalic(True)
        
    def highlightBlock(self, text: str):
        """Highlight text block.
        
        Args:
            text: Text to highlight
        """
        # Keywords
        for word in text.split():
            if word in self.keywords:
                index = text.index(word)
                self.setFormat(index, len(word), self.keyword_format)
                
        # Strings
        in_string = False
        quote_char = None
        for i, char in enumerate(text):
            if char in ["'", '"']:
                if not in_string:
                    in_string = True
                    quote_char = char
                    start = i
                elif char == quote_char:
                    in_string = False
                    self.setFormat(start, i - start + 1, self.string_format)
                    
        # Comments
        if '#' in text:
            index = text.index('#')
            self.setFormat(index, len(text) - index, self.comment_format)

class FilePreviewWidget(QWidget):
    """Widget for previewing file contents."""
    
    preview_ready = pyqtSignal()  # Emits when preview is loaded
    
    def __init__(self, parent=None):
        """Initialize file preview widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.current_path: Optional[Path] = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the preview UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # File info
        self.info_label = QLabel()
        self.info_label.setStyleSheet(
            self.style_manager.get_component_style(StyleClass.LABEL)
        )
        layout.addWidget(self.info_label)
        
        # Preview area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.scroll_area)
        
        # Preview widgets
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.highlighter = SyntaxHighlighter(self.text_preview.document())
        
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Ignored
        )
        
        # Hide previews initially
        self.text_preview.hide()
        self.image_preview.hide()
        
    def set_file(self, path: Path):
        """Set file to preview.
        
        Args:
            path: File path
        """
        self.current_path = path
        if not path.exists():
            self.show_error("File does not exist")
            return
            
        try:
            # Update file info
            size = path.stat().st_size
            mime_type, _ = mimetypes.guess_type(str(path))
            self.info_label.setText(
                f"File: {path.name}\n"
                f"Size: {self.format_size(size)}\n"
                f"Type: {mime_type or 'Unknown'}"
            )
            
            # Show preview based on mime type
            if mime_type:
                if mime_type.startswith('text/'):
                    self.show_text_preview(path)
                elif mime_type.startswith('image/'):
                    self.show_image_preview(path)
                else:
                    self.show_error("Preview not supported for this file type")
            else:
                # Try to read as text if mime type unknown
                self.show_text_preview(path)
                
        except Exception as e:
            logger.error(f"Failed to preview file: {str(e)}")
            self.show_error(f"Failed to preview file: {str(e)}")
            
    def show_text_preview(self, path: Path):
        """Show text file preview.
        
        Args:
            path: Text file path
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.text_preview.setPlainText(content)
            self.scroll_area.setWidget(self.text_preview)
            self.text_preview.show()
            self.image_preview.hide()
            self.preview_ready.emit()
            
        except UnicodeDecodeError:
            self.show_error("File is not valid text")
            
    def show_image_preview(self, path: Path):
        """Show image file preview.
        
        Args:
            path: Image file path
        """
        image = QImage(str(path))
        if image.isNull():
            self.show_error("Failed to load image")
            return
            
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.scroll_area.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_preview.setPixmap(scaled_pixmap)
        self.scroll_area.setWidget(self.image_preview)
        self.text_preview.hide()
        self.image_preview.show()
        self.preview_ready.emit()
        
    def show_error(self, message: str):
        """Show error message.
        
        Args:
            message: Error message
        """
        self.info_label.setText(f"Error: {message}")
        self.text_preview.hide()
        self.image_preview.hide()
        
    def format_size(self, size: int) -> str:
        """Format file size in human-readable format.
        
        Args:
            size: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
