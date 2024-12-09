"""Settings dialog."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget,
    QPushButton, QDialogButtonBox
)
from PyQt6.QtCore import pyqtSignal
from ..styles.style_manager import StyleManager
from .general_panel import GeneralSettingsPanel
from .editor_panel import EditorSettingsPanel
from .console_panel import ConsoleSettingsPanel
from .theme_panel import ThemeSettingsPanel
from .settings_manager import SettingsManager

class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    settings_changed = pyqtSignal()  # Emits when settings are applied
    
    def __init__(self, settings: SettingsManager, parent=None):
        """Initialize settings dialog.
        
        Args:
            settings: Settings manager
            parent: Parent widget
        """
        super().__init__(parent)
        self.settings = settings
        self.style_manager = StyleManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Settings")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Settings panels
        self.general_panel = GeneralSettingsPanel(self.settings)
        self.tabs.addTab(self.general_panel, "General")
        
        self.editor_panel = EditorSettingsPanel(self.settings)
        self.tabs.addTab(self.editor_panel, "Editor")
        
        self.console_panel = ConsoleSettingsPanel(self.settings)
        self.tabs.addTab(self.console_panel, "Console")
        
        self.theme_panel = ThemeSettingsPanel(self.settings)
        self.tabs.addTab(self.theme_panel, "Theme")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        layout.addWidget(buttons)
        
    def accept(self):
        """Accept dialog and apply settings."""
        self.apply_settings()
        super().accept()
        
    def apply_settings(self):
        """Apply settings changes."""
        # Apply panel settings
        self.general_panel.apply_settings()
        self.editor_panel.apply_settings()
        self.console_panel.apply_settings()
        self.theme_panel.apply_settings()
        
        self.settings_changed.emit()
