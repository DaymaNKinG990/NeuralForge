"""Console settings panel."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QCheckBox, QSpinBox, QFontComboBox,
    QComboBox
)
from .settings_manager import SettingsManager

class ConsoleSettingsPanel(QWidget):
    """Panel for console settings."""
    
    def __init__(self, settings: SettingsManager, parent=None):
        """Initialize console settings panel.
        
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
        
        # Font settings
        self.font_family = QFontComboBox()
        form.addRow("Font:", self.font_family)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        form.addRow("Font size:", self.font_size)
        
        # History settings
        self.history_size = QSpinBox()
        self.history_size.setRange(0, 10000)
        form.addRow("History size:", self.history_size)
        
        self.save_history = QCheckBox("Save history between sessions")
        form.addRow("History:", self.save_history)
        
        # Output settings
        self.buffer_size = QSpinBox()
        self.buffer_size.setRange(100, 1000000)
        self.buffer_size.setSingleStep(1000)
        self.buffer_size.setSuffix(" lines")
        form.addRow("Buffer size:", self.buffer_size)
        
        self.wrap_lines = QCheckBox("Wrap long lines")
        form.addRow("Display:", self.wrap_lines)
        
        # Color scheme
        self.color_scheme = QComboBox()
        self.color_scheme.addItems([
            "Default", "Light", "Dark", "Solarized",
            "Monokai", "Custom"
        ])
        form.addRow("Color scheme:", self.color_scheme)
        
        # Auto features
        self.auto_scroll = QCheckBox("Auto-scroll to bottom")
        form.addRow("Auto features:", self.auto_scroll)
        
        self.auto_indent = QCheckBox("Auto-indent")
        form.addRow("", self.auto_indent)
        
        # Python settings
        self.show_warnings = QCheckBox("Show Python warnings")
        form.addRow("Python:", self.show_warnings)
        
        self.auto_import = QCheckBox("Auto-import common modules")
        form.addRow("", self.auto_import)
        
        layout.addLayout(form)
        layout.addStretch()
        
    def load_settings(self):
        """Load current settings."""
        section = self.settings.get_section('console')
        
        # Font settings
        font_family = section.get('font_family', 'Courier New')
        index = self.font_family.findText(font_family)
        if index >= 0:
            self.font_family.setCurrentIndex(index)
            
        self.font_size.setValue(
            section.get('font_size', 12)
        )
        
        # History settings
        self.history_size.setValue(
            section.get('history_size', 1000)
        )
        self.save_history.setChecked(
            section.get('save_history', True)
        )
        
        # Output settings
        self.buffer_size.setValue(
            section.get('buffer_size', 10000)
        )
        self.wrap_lines.setChecked(
            section.get('wrap_lines', True)
        )
        
        # Color scheme
        scheme = section.get('color_scheme', 'Default')
        index = self.color_scheme.findText(scheme)
        if index >= 0:
            self.color_scheme.setCurrentIndex(index)
            
        # Auto features
        self.auto_scroll.setChecked(
            section.get('auto_scroll', True)
        )
        self.auto_indent.setChecked(
            section.get('auto_indent', True)
        )
        
        # Python settings
        self.show_warnings.setChecked(
            section.get('show_warnings', True)
        )
        self.auto_import.setChecked(
            section.get('auto_import', False)
        )
        
    def apply_settings(self):
        """Apply settings changes."""
        self.settings.set_section('console', {
            'font_family': self.font_family.currentText(),
            'font_size': self.font_size.value(),
            'history_size': self.history_size.value(),
            'save_history': self.save_history.isChecked(),
            'buffer_size': self.buffer_size.value(),
            'wrap_lines': self.wrap_lines.isChecked(),
            'color_scheme': self.color_scheme.currentText(),
            'auto_scroll': self.auto_scroll.isChecked(),
            'auto_indent': self.auto_indent.isChecked(),
            'show_warnings': self.show_warnings.isChecked(),
            'auto_import': self.auto_import.isChecked()
        })
