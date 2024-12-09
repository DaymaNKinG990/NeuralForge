"""Base window functionality."""
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QSettings
from ..styles.theme_manager import ThemeManager
from ..styles.adaptive_styles import AdaptiveStyles
import logging

class WindowBase(QMainWindow):
    """Base window class with common functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_base()
        
    def _setup_base(self):
        """Setup base window configuration."""
        try:
            # Initialize theme manager
            self._theme_manager = ThemeManager()
            self._setup_theme()
            
            # Basic window setup
            self.setMinimumSize(1200, 800)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
            self.setWindowState(Qt.WindowState.WindowActive)
            
            # Settings
            self._settings = QSettings('NeuralForge', 'IDE')
            
            # Create main container
            container = QWidget()
            if not container:
                raise RuntimeError("Failed to create container widget")
            self.setCentralWidget(container)
            
            # Create layout
            self.main_layout = QVBoxLayout(container)
            
        except Exception as e:
            self.logger.error(f"Error in base setup: {str(e)}", exc_info=True)
            raise
            
    def _setup_theme(self):
        """Setup window theme."""
        # Apply theme to application palette
        self.setPalette(self._theme_manager.get_palette())
        
        # Apply base styles
        base_style = AdaptiveStyles.get_base_style(self._theme_manager)
        self.setStyleSheet(base_style)
        
    def change_theme(self, theme: str):
        """Change the application theme.
        
        Args:
            theme (str): Theme name ('dark' or 'light')
        """
        self._theme_manager.set_theme(theme)
        self._setup_theme()
        
    def toggle_theme(self):
        """Toggle between dark and light themes."""
        current_theme = self._theme_manager.current_theme
        new_theme = 'light' if current_theme == 'dark' else 'dark'
        self.change_theme(new_theme)
