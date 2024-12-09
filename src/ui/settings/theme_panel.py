"""Theme settings panel."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QComboBox, QPushButton, QColorDialog,
    QLabel, QHBoxLayout
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from .settings_manager import SettingsManager

class ColorButton(QPushButton):
    """Button for color selection."""
    
    def __init__(self, color: QColor, parent=None):
        """Initialize color button.
        
        Args:
            color: Initial color
            parent: Parent widget
        """
        super().__init__(parent)
        self.color = color
        self.update_style()
        self.clicked.connect(self.choose_color)
        
    def update_style(self):
        """Update button style."""
        self.setStyleSheet(
            f"background-color: {self.color.name()};"
            f"border: 1px solid black;"
            f"min-width: 60px;"
            f"max-width: 60px;"
            f"min-height: 20px;"
            f"max-height: 20px;"
        )
        
    def choose_color(self):
        """Show color dialog."""
        color = QColorDialog.getColor(
            self.color, self, "Choose Color"
        )
        if color.isValid():
            self.color = color
            self.update_style()

class ThemeSettingsPanel(QWidget):
    """Panel for theme settings."""
    
    def __init__(self, settings: SettingsManager, parent=None):
        """Initialize theme settings panel.
        
        Args:
            settings: Settings manager
            parent: Parent widget
        """
        super().__init__(parent)
        self.settings = settings
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Theme selection
        self.theme = QComboBox()
        self.theme.addItems([
            "Light", "Dark", "High Contrast",
            "Solarized Light", "Solarized Dark",
            "Custom"
        ])
        self.theme.currentTextChanged.connect(self.on_theme_changed)
        form.addRow("Theme:", self.theme)
        
        # Color settings
        colors_layout = QVBoxLayout()
        
        # Background colors
        bg_layout = QFormLayout()
        self.bg_primary = ColorButton(QColor("#FFFFFF"))
        bg_layout.addRow("Primary:", self.bg_primary)
        
        self.bg_secondary = ColorButton(QColor("#F0F0F0"))
        bg_layout.addRow("Secondary:", self.bg_secondary)
        
        self.bg_tertiary = ColorButton(QColor("#E0E0E0"))
        bg_layout.addRow("Tertiary:", self.bg_tertiary)
        
        colors_group = QWidget()
        colors_group.setLayout(bg_layout)
        form.addRow("Background:", colors_group)
        
        # Text colors
        text_layout = QFormLayout()
        self.text_primary = ColorButton(QColor("#000000"))
        text_layout.addRow("Primary:", self.text_primary)
        
        self.text_secondary = ColorButton(QColor("#404040"))
        text_layout.addRow("Secondary:", self.text_secondary)
        
        self.text_disabled = ColorButton(QColor("#808080"))
        text_layout.addRow("Disabled:", self.text_disabled)
        
        colors_group = QWidget()
        colors_group.setLayout(text_layout)
        form.addRow("Text:", colors_group)
        
        # Accent colors
        accent_layout = QFormLayout()
        self.accent_primary = ColorButton(QColor("#0078D4"))
        accent_layout.addRow("Primary:", self.accent_primary)
        
        self.accent_secondary = ColorButton(QColor("#00B7C3"))
        accent_layout.addRow("Secondary:", self.accent_secondary)
        
        self.accent_error = ColorButton(QColor("#E81123"))
        accent_layout.addRow("Error:", self.accent_error)
        
        colors_group = QWidget()
        colors_group.setLayout(accent_layout)
        form.addRow("Accent:", colors_group)
        
        layout.addLayout(form)
        layout.addStretch()
        
        # Preview section
        preview = QLabel("Theme Preview")
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(preview)
        
        # Preview widget will be added here
        self.preview = QWidget()
        self.preview.setMinimumHeight(100)
        layout.addWidget(self.preview)
        
    def on_theme_changed(self, theme: str):
        """Handle theme change.
        
        Args:
            theme: Selected theme
        """
        if theme != "Custom":
            # Update color buttons with theme colors
            colors = self.get_theme_colors(theme)
            
            self.bg_primary.color = QColor(colors['bg_primary'])
            self.bg_secondary.color = QColor(colors['bg_secondary'])
            self.bg_tertiary.color = QColor(colors['bg_tertiary'])
            
            self.text_primary.color = QColor(colors['text_primary'])
            self.text_secondary.color = QColor(colors['text_secondary'])
            self.text_disabled.color = QColor(colors['text_disabled'])
            
            self.accent_primary.color = QColor(colors['accent_primary'])
            self.accent_secondary.color = QColor(colors['accent_secondary'])
            self.accent_error.color = QColor(colors['accent_error'])
            
            # Update button styles
            for btn in [
                self.bg_primary, self.bg_secondary, self.bg_tertiary,
                self.text_primary, self.text_secondary, self.text_disabled,
                self.accent_primary, self.accent_secondary, self.accent_error
            ]:
                btn.update_style()
                
    def get_theme_colors(self, theme: str) -> dict:
        """Get colors for theme.
        
        Args:
            theme: Theme name
            
        Returns:
            Theme colors dictionary
        """
        themes = {
            "Light": {
                "bg_primary": "#FFFFFF",
                "bg_secondary": "#F0F0F0",
                "bg_tertiary": "#E0E0E0",
                "text_primary": "#000000",
                "text_secondary": "#404040",
                "text_disabled": "#808080",
                "accent_primary": "#0078D4",
                "accent_secondary": "#00B7C3",
                "accent_error": "#E81123"
            },
            "Dark": {
                "bg_primary": "#1E1E1E",
                "bg_secondary": "#252526",
                "bg_tertiary": "#2D2D2D",
                "text_primary": "#FFFFFF",
                "text_secondary": "#CCCCCC",
                "text_disabled": "#808080",
                "accent_primary": "#0078D4",
                "accent_secondary": "#00B7C3",
                "accent_error": "#F1707B"
            },
            "High Contrast": {
                "bg_primary": "#000000",
                "bg_secondary": "#1F1F1F",
                "bg_tertiary": "#2F2F2F",
                "text_primary": "#FFFFFF",
                "text_secondary": "#FFFFFF",
                "text_disabled": "#CCCCCC",
                "accent_primary": "#FFFF00",
                "accent_secondary": "#00FF00",
                "accent_error": "#FF0000"
            }
        }
        return themes.get(theme, themes["Light"])
        
    def load_settings(self):
        """Load current settings."""
        section = self.settings.get_section('theme')
        
        # Set theme
        theme = section.get('theme', 'Light')
        index = self.theme.findText(theme)
        if index >= 0:
            self.theme.setCurrentIndex(index)
            
        # Set colors
        self.bg_primary.color = QColor(
            section.get('bg_primary', '#FFFFFF')
        )
        self.bg_secondary.color = QColor(
            section.get('bg_secondary', '#F0F0F0')
        )
        self.bg_tertiary.color = QColor(
            section.get('bg_tertiary', '#E0E0E0')
        )
        
        self.text_primary.color = QColor(
            section.get('text_primary', '#000000')
        )
        self.text_secondary.color = QColor(
            section.get('text_secondary', '#404040')
        )
        self.text_disabled.color = QColor(
            section.get('text_disabled', '#808080')
        )
        
        self.accent_primary.color = QColor(
            section.get('accent_primary', '#0078D4')
        )
        self.accent_secondary.color = QColor(
            section.get('accent_secondary', '#00B7C3')
        )
        self.accent_error.color = QColor(
            section.get('accent_error', '#E81123')
        )
        
        # Update button styles
        for btn in [
            self.bg_primary, self.bg_secondary, self.bg_tertiary,
            self.text_primary, self.text_secondary, self.text_disabled,
            self.accent_primary, self.accent_secondary, self.accent_error
        ]:
            btn.update_style()
            
    def apply_settings(self):
        """Apply settings changes."""
        self.settings.set_section('theme', {
            'theme': self.theme.currentText(),
            'bg_primary': self.bg_primary.color.name(),
            'bg_secondary': self.bg_secondary.color.name(),
            'bg_tertiary': self.bg_tertiary.color.name(),
            'text_primary': self.text_primary.color.name(),
            'text_secondary': self.text_secondary.color.name(),
            'text_disabled': self.text_disabled.color.name(),
            'accent_primary': self.accent_primary.color.name(),
            'accent_secondary': self.accent_secondary.color.name(),
            'accent_error': self.accent_error.color.name()
        })
