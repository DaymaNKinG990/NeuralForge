"""Менеджер тем для адаптивного интерфейса"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, ClassVar
import json
import os
import logging
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import QSettings, Qt
import threading

logger = logging.getLogger(__name__)

class ColorRole(Enum):
    """Роли цветов в теме"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    BACKGROUND = "background"
    SURFACE = "surface"
    ERROR = "error"
    ON_PRIMARY = "on_primary"
    ON_SECONDARY = "on_secondary"
    ON_BACKGROUND = "on_background"
    ON_SURFACE = "on_surface"
    ON_ERROR = "on_error"
    BORDER = "border"
    SHADOW = "shadow"
    ACCENT = "accent"

@dataclass
class ThemeColors:
    """Цвета темы"""
    primary: str
    secondary: str
    background: str
    surface: str
    error: str
    on_primary: str
    on_secondary: str
    on_background: str
    on_surface: str
    on_error: str
    border: str
    shadow: str
    accent: str

    def __post_init__(self):
        """Validate color values after initialization"""
        for field, value in self.__dict__.items():
            if not isinstance(value, str):
                raise ValueError(f"Color value for {field} must be a string")
            if not value.startswith("#") or len(value) != 7:
                raise ValueError(f"Invalid color format for {field}. Must be #RRGGBB")
            try:
                int(value[1:], 16)
            except ValueError:
                raise ValueError(f"Invalid hex color value for {field}")

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'ThemeColors':
        """Create ThemeColors from dictionary with validation"""
        required_fields = cls.__annotations__.keys()
        missing_fields = required_fields - data.keys()
        if missing_fields:
            raise ValueError(f"Missing required color fields: {missing_fields}")
        return cls(**data)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary"""
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "background": self.background,
            "surface": self.surface,
            "error": self.error,
            "on_primary": self.on_primary,
            "on_secondary": self.on_secondary,
            "on_background": self.on_background,
            "on_surface": self.on_surface,
            "on_error": self.on_error,
            "border": self.border,
            "shadow": self.shadow,
            "accent": self.accent
        }

class ThemeManager:
    """Менеджер тем приложения"""

    DARK_THEME: ClassVar[ThemeColors] = ThemeColors(
        primary="#2196F3",
        secondary="#03DAC6",
        background="#121212",
        surface="#1E1E1E",
        error="#CF6679",
        on_primary="#000000",
        on_secondary="#000000",
        on_background="#FFFFFF",
        on_surface="#FFFFFF",
        on_error="#000000",
        border="#323232",
        shadow="#000000",
        accent="#BB86FC"
    )

    LIGHT_THEME: ClassVar[ThemeColors] = ThemeColors(
        primary="#6200EE",
        secondary="#03DAC6",
        background="#FFFFFF",
        surface="#F5F5F5",
        error="#B00020",
        on_primary="#FFFFFF",
        on_secondary="#000000",
        on_background="#000000",
        on_surface="#000000",
        on_error="#FFFFFF",
        border="#E0E0E0",
        shadow="#757575",
        accent="#018786"
    )

    THEMES_DIR = os.path.join(os.path.dirname(__file__), "themes")

    def __init__(self):
        """Initialize theme manager"""
        try:
            # Ensure themes directory exists
            os.makedirs(self.THEMES_DIR, exist_ok=True)
            
            # Initialize settings and state
            self._settings = QSettings('NeuralForge', 'IDE')
            self._current_theme = self._load_theme()
            self._custom_themes = self._load_custom_themes()
            self._theme_cache = {}
            self._cache_lock = threading.Lock()
            
            logger.debug("ThemeManager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ThemeManager: {str(e)}", exc_info=True)
            raise

    def _load_theme(self) -> ThemeColors:
        """Load current theme from settings"""
        try:
            theme_type = self._settings.value('theme/type', 'dark')
            custom_name = self._settings.value('theme/custom_name', '')
            
            if theme_type == 'custom' and custom_name:
                # Load custom theme
                custom_themes = self._load_custom_themes()
                if custom_name in custom_themes:
                    return custom_themes[custom_name]
                logger.warning(f"Custom theme {custom_name} not found, falling back to dark theme")
                
            # Return default theme
            return self.DARK_THEME if theme_type == 'dark' else self.LIGHT_THEME
            
        except Exception as e:
            logger.error(f"Error loading theme: {str(e)}", exc_info=True)
            return self.DARK_THEME  # Fallback to dark theme

    def _load_custom_themes(self) -> Dict[str, ThemeColors]:
        """Load custom themes from file"""
        try:
            themes_file = os.path.join(self.THEMES_DIR, "custom_themes.json")
            if not os.path.exists(themes_file):
                return {}
                
            with open(themes_file, 'r') as f:
                data = json.load(f)
                
            themes = {}
            for name, colors in data.items():
                try:
                    themes[name] = ThemeColors(**colors)
                except Exception as e:
                    logger.error(f"Error loading custom theme {name}: {str(e)}")
                    
            return themes
            
        except Exception as e:
            logger.error(f"Error loading custom themes: {str(e)}", exc_info=True)
            return {}

    def _save_custom_themes(self) -> None:
        """Save custom themes to file"""
        try:
            themes_file = os.path.join(self.THEMES_DIR, "custom_themes.json")
            data = {
                name: vars(colors)
                for name, colors in self._custom_themes.items()
            }
            
            with open(themes_file, 'w') as f:
                json.dump(data, f, indent=4)
                
            logger.debug("Custom themes saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving custom themes: {str(e)}", exc_info=True)

    def get_color(self, role: ColorRole) -> str:
        """Get color for specified role"""
        try:
            if not isinstance(role, ColorRole):
                raise ValueError(f"Invalid color role: {role}")
                
            # Check cache first
            cache_key = (role, id(self._current_theme))
            with self._cache_lock:
                if cache_key in self._theme_cache:
                    return self._theme_cache[cache_key]
                
            # Get color from theme
            color = getattr(self._current_theme, role.value)
            
            # Validate color format
            if not color.startswith('#') or len(color) != 7:
                raise ValueError(f"Invalid color format for role {role}: {color}")
                
            # Cache the result
            with self._cache_lock:
                self._theme_cache[cache_key] = color
                
            return color
            
        except Exception as e:
            logger.error(f"Error getting color for role {role}: {str(e)}", exc_info=True)
            return "#000000"  # Fallback to black

    def get_qcolor(self, role: ColorRole) -> QColor:
        """Get QColor for specified role"""
        try:
            color_str = self.get_color(role)
            return QColor(color_str)
            
        except Exception as e:
            logger.error(f"Error getting QColor for role {role}: {str(e)}", exc_info=True)
            return QColor("#000000")  # Fallback to black

    def set_theme(self, theme_type: str, custom_name: Optional[str] = None) -> None:
        """Set current theme"""
        try:
            if theme_type not in ['light', 'dark', 'custom']:
                raise ValueError(f"Invalid theme type: {theme_type}")
                
            if theme_type == 'custom':
                if not custom_name:
                    raise ValueError("Custom theme name required")
                if custom_name not in self._custom_themes:
                    raise ValueError(f"Custom theme not found: {custom_name}")
                    
            # Update settings
            self._settings.setValue('theme/type', theme_type)
            if custom_name:
                self._settings.setValue('theme/custom_name', custom_name)
                
            # Update current theme
            self._current_theme = self._load_theme()
            
            # Clear cache
            with self._cache_lock:
                self._theme_cache.clear()
                
            logger.debug(f"Theme changed to: {theme_type} {custom_name or ''}")
            
        except Exception as e:
            logger.error(f"Error setting theme: {str(e)}", exc_info=True)
            raise

    def add_custom_theme(self, name: str, colors: ThemeColors) -> None:
        """Add custom theme"""
        try:
            if not name:
                raise ValueError("Theme name cannot be empty")
                
            if name in self._custom_themes:
                raise ValueError(f"Theme {name} already exists")
                
            # Validate colors
            if not isinstance(colors, ThemeColors):
                raise ValueError("Invalid theme colors")
                
            self._custom_themes[name] = colors
            self._save_custom_themes()
            
            logger.debug(f"Custom theme added: {name}")
            
        except Exception as e:
            logger.error(f"Error adding custom theme: {str(e)}", exc_info=True)
            raise

    def remove_custom_theme(self, name: str) -> None:
        """Remove custom theme"""
        try:
            if name not in self._custom_themes:
                raise ValueError(f"Theme {name} not found")
                
            del self._custom_themes[name]
            self._save_custom_themes()
            
            # Reset to default if current theme was removed
            if self._settings.value('theme/type') == 'custom' and \
               self._settings.value('theme/custom_name') == name:
                self.set_theme('dark')
                
            logger.debug(f"Custom theme removed: {name}")
            
        except Exception as e:
            logger.error(f"Error removing custom theme: {str(e)}", exc_info=True)
            raise

    def get_palette(self) -> QPalette:
        """Get Qt palette for current theme"""
        try:
            palette = QPalette()
            
            # Set window colors
            palette.setColor(QPalette.ColorRole.Window, self.get_qcolor(ColorRole.BACKGROUND))
            palette.setColor(QPalette.ColorRole.WindowText, self.get_qcolor(ColorRole.ON_BACKGROUND))
            
            # Set widget colors
            palette.setColor(QPalette.ColorRole.Base, self.get_qcolor(ColorRole.SURFACE))
            palette.setColor(QPalette.ColorRole.Text, self.get_qcolor(ColorRole.ON_SURFACE))
            
            # Set button colors
            palette.setColor(QPalette.ColorRole.Button, self.get_qcolor(ColorRole.PRIMARY))
            palette.setColor(QPalette.ColorRole.ButtonText, self.get_qcolor(ColorRole.ON_PRIMARY))
            
            # Set highlight colors
            palette.setColor(QPalette.ColorRole.Highlight, self.get_qcolor(ColorRole.ACCENT))
            palette.setColor(QPalette.ColorRole.HighlightedText, self.get_qcolor(ColorRole.ON_PRIMARY))
            
            return palette
            
        except Exception as e:
            logger.error(f"Error creating palette: {str(e)}", exc_info=True)
            return QPalette()  # Return default palette
            
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Save any pending changes
            self._save_custom_themes()
            
            # Clear cache
            with self._cache_lock:
                self._theme_cache.clear()
                
            logger.debug("ThemeManager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during ThemeManager cleanup: {str(e)}", exc_info=True)
