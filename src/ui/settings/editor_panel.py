"""Editor settings panel."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QCheckBox, QSpinBox, QFontComboBox,
    QComboBox
)
from .settings_manager import SettingsManager

class EditorSettingsPanel(QWidget):
    """Panel for editor settings."""
    
    def __init__(self, settings: SettingsManager, parent=None):
        """Initialize editor settings panel.
        
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
        
        # Tab settings
        self.tab_size = QSpinBox()
        self.tab_size.setRange(1, 8)
        form.addRow("Tab size:", self.tab_size)
        
        self.use_spaces = QCheckBox("Use spaces for tabs")
        form.addRow("Tabs:", self.use_spaces)
        
        # Line numbers
        self.show_line_numbers = QCheckBox("Show line numbers")
        form.addRow("Display:", self.show_line_numbers)
        
        # Code completion
        self.auto_complete = QCheckBox("Enable auto-completion")
        form.addRow("Completion:", self.auto_complete)
        
        self.complete_delay = QSpinBox()
        self.complete_delay.setRange(0, 2000)
        self.complete_delay.setSuffix(" ms")
        form.addRow("Completion delay:", self.complete_delay)
        
        # Code style
        self.code_style = QComboBox()
        self.code_style.addItems([
            "PEP 8", "Google", "NumPy", "Custom"
        ])
        form.addRow("Code style:", self.code_style)
        
        # Auto features
        self.auto_indent = QCheckBox("Auto-indent")
        form.addRow("Auto features:", self.auto_indent)
        
        self.auto_pair = QCheckBox("Auto-pair brackets/quotes")
        form.addRow("", self.auto_pair)
        
        self.auto_save = QCheckBox("Auto-save")
        form.addRow("", self.auto_save)
        
        self.save_interval = QSpinBox()
        self.save_interval.setRange(1, 60)
        self.save_interval.setSuffix(" minutes")
        form.addRow("Auto-save interval:", self.save_interval)
        
        layout.addLayout(form)
        layout.addStretch()
        
    def load_settings(self):
        """Load current settings."""
        section = self.settings.get_section('editor')
        
        # Font settings
        font_family = section.get('font_family', 'Courier New')
        index = self.font_family.findText(font_family)
        if index >= 0:
            self.font_family.setCurrentIndex(index)
            
        self.font_size.setValue(
            section.get('font_size', 12)
        )
        
        # Tab settings
        self.tab_size.setValue(
            section.get('tab_size', 4)
        )
        self.use_spaces.setChecked(
            section.get('use_spaces', True)
        )
        
        # Display settings
        self.show_line_numbers.setChecked(
            section.get('show_line_numbers', True)
        )
        
        # Completion settings
        self.auto_complete.setChecked(
            section.get('auto_complete', True)
        )
        self.complete_delay.setValue(
            section.get('complete_delay', 500)
        )
        
        # Code style
        style = section.get('code_style', 'PEP 8')
        index = self.code_style.findText(style)
        if index >= 0:
            self.code_style.setCurrentIndex(index)
            
        # Auto features
        self.auto_indent.setChecked(
            section.get('auto_indent', True)
        )
        self.auto_pair.setChecked(
            section.get('auto_pair', True)
        )
        self.auto_save.setChecked(
            section.get('auto_save', False)
        )
        self.save_interval.setValue(
            section.get('save_interval', 5)
        )
        
    def apply_settings(self):
        """Apply settings changes."""
        self.settings.set_section('editor', {
            'font_family': self.font_family.currentText(),
            'font_size': self.font_size.value(),
            'tab_size': self.tab_size.value(),
            'use_spaces': self.use_spaces.isChecked(),
            'show_line_numbers': self.show_line_numbers.isChecked(),
            'auto_complete': self.auto_complete.isChecked(),
            'complete_delay': self.complete_delay.value(),
            'code_style': self.code_style.currentText(),
            'auto_indent': self.auto_indent.isChecked(),
            'auto_pair': self.auto_pair.isChecked(),
            'auto_save': self.auto_save.isChecked(),
            'save_interval': self.save_interval.value()
        })
