"""General settings panel."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QCheckBox, QSpinBox, QLineEdit,
    QComboBox, QLabel
)
from .settings_manager import SettingsManager

class GeneralSettingsPanel(QWidget):
    """Panel for general application settings."""
    
    def __init__(self, settings: SettingsManager, parent=None):
        """Initialize general settings panel.
        
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
        
        # Startup settings
        self.auto_load = QCheckBox("Load last project on startup")
        form.addRow("Startup:", self.auto_load)
        
        # Project settings
        self.backup_count = QSpinBox()
        self.backup_count.setRange(0, 100)
        form.addRow("Backup copies:", self.backup_count)
        
        self.backup_interval = QSpinBox()
        self.backup_interval.setRange(1, 60)
        self.backup_interval.setSuffix(" minutes")
        form.addRow("Backup interval:", self.backup_interval)
        
        # Updates
        self.check_updates = QCheckBox("Check for updates automatically")
        form.addRow("Updates:", self.check_updates)
        
        # Language
        self.language = QComboBox()
        self.language.addItems(["English", "Spanish", "French", "German"])
        form.addRow("Language:", self.language)
        
        # Logging
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        form.addRow("Log level:", self.log_level)
        
        self.log_file = QLineEdit()
        form.addRow("Log file:", self.log_file)
        
        layout.addLayout(form)
        layout.addStretch()
        
    def load_settings(self):
        """Load current settings."""
        section = self.settings.get_section('general')
        
        self.auto_load.setChecked(
            section.get('auto_load_project', True)
        )
        self.backup_count.setValue(
            section.get('backup_count', 5)
        )
        self.backup_interval.setValue(
            section.get('backup_interval', 5)
        )
        self.check_updates.setChecked(
            section.get('check_updates', True)
        )
        
        language = section.get('language', 'English')
        index = self.language.findText(language)
        if index >= 0:
            self.language.setCurrentIndex(index)
            
        log_level = section.get('log_level', 'INFO')
        index = self.log_level.findText(log_level)
        if index >= 0:
            self.log_level.setCurrentIndex(index)
            
        self.log_file.setText(
            section.get('log_file', 'app.log')
        )
        
    def apply_settings(self):
        """Apply settings changes."""
        self.settings.set_section('general', {
            'auto_load_project': self.auto_load.isChecked(),
            'backup_count': self.backup_count.value(),
            'backup_interval': self.backup_interval.value(),
            'check_updates': self.check_updates.isChecked(),
            'language': self.language.currentText(),
            'log_level': self.log_level.currentText(),
            'log_file': self.log_file.text()
        })
