from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QPushButton, QLabel, QSpinBox, QComboBox,
                             QCheckBox, QFontComboBox, QColorDialog,
                             QGroupBox, QFormLayout, QWidget)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont, QColor, QPalette
import logging

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initializing SettingsDialog")
        
        self.settings = QSettings('NeuroForge', 'IDE')
        self.logger.debug("QSettings initialized")
        
        try:
            self.setup_ui()
            self.logger.debug("UI setup completed")
            
            self.load_settings()
            self.logger.debug("Settings loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error in SettingsDialog initialization: {str(e)}", exc_info=True)
            raise
            
    def setup_ui(self):
        """Setup the settings dialog UI."""
        try:
            self.setWindowTitle("Settings")
            self.setMinimumWidth(500)
            
            layout = QVBoxLayout(self)
            
            # Create tab widget
            tab_widget = QTabWidget(self)
            layout.addWidget(tab_widget)
            
            # Editor settings tab
            editor_tab = QWidget(tab_widget)
            editor_layout = QVBoxLayout(editor_tab)
            
            # Font settings
            font_group = QGroupBox("Font Settings", editor_tab)
            font_layout = QFormLayout()
            
            self.font_family = QFontComboBox(font_group)
            font_layout.addRow("Font Family:", self.font_family)
            
            self.font_size = QSpinBox(font_group)
            self.font_size.setRange(8, 72)
            font_layout.addRow("Font Size:", self.font_size)
            
            font_group.setLayout(font_layout)
            editor_layout.addWidget(font_group)
            
            # Color settings
            color_group = QGroupBox("Color Settings", editor_tab)
            color_layout = QFormLayout()
            
            # Background color
            bg_layout = QHBoxLayout()
            self.bg_color_preview = QLabel(color_group)
            self.bg_color_preview.setFixedSize(20, 20)
            self.bg_color_preview.setStyleSheet("background-color: #2D2D2D; border: 1px solid gray;")
            bg_layout.addWidget(self.bg_color_preview)
            
            self.bg_color_button = QPushButton("Choose Background Color", color_group)
            self.bg_color_button.clicked.connect(self.choose_background_color)
            bg_layout.addWidget(self.bg_color_button)
            color_layout.addRow("Background Color:", bg_layout)
            
            # Text color
            text_layout = QHBoxLayout()
            self.text_color_preview = QLabel(color_group)
            self.text_color_preview.setFixedSize(20, 20)
            self.text_color_preview.setStyleSheet("background-color: #FFFFFF; border: 1px solid gray;")
            text_layout.addWidget(self.text_color_preview)
            
            self.text_color_button = QPushButton("Choose Text Color", color_group)
            self.text_color_button.clicked.connect(self.choose_text_color)
            text_layout.addWidget(self.text_color_button)
            color_layout.addRow("Text Color:", text_layout)
            
            color_group.setLayout(color_layout)
            editor_layout.addWidget(color_group)
            
            # Editor behavior
            behavior_group = QGroupBox("Editor Behavior", editor_tab)
            behavior_layout = QFormLayout()
            
            self.auto_indent = QCheckBox(behavior_group)
            behavior_layout.addRow("Auto Indent:", self.auto_indent)
            
            self.line_numbers = QCheckBox(behavior_group)
            behavior_layout.addRow("Show Line Numbers:", self.line_numbers)
            
            self.tab_width = QSpinBox(behavior_group)
            self.tab_width.setRange(2, 8)
            behavior_layout.addRow("Tab Width:", self.tab_width)
            
            behavior_group.setLayout(behavior_layout)
            editor_layout.addWidget(behavior_group)
            
            # Add editor tab to tab widget
            tab_widget.addTab(editor_tab, "Editor")
            
            # ML settings tab
            ml_tab = QWidget(tab_widget)
            ml_layout = QVBoxLayout(ml_tab)
            
            # Training settings
            training_group = QGroupBox("Training Settings", ml_tab)
            training_layout = QFormLayout()
            
            self.default_epochs = QSpinBox(training_group)
            self.default_epochs.setRange(1, 1000)
            training_layout.addRow("Default Epochs:", self.default_epochs)
            
            self.default_batch_size = QSpinBox(training_group)
            self.default_batch_size.setRange(1, 1024)
            training_layout.addRow("Default Batch Size:", self.default_batch_size)
            
            self.default_learning_rate = QDoubleSpinBox(training_group)
            self.default_learning_rate.setRange(0.0001, 1.0)
            self.default_learning_rate.setSingleStep(0.0001)
            training_layout.addRow("Default Learning Rate:", self.default_learning_rate)
            
            training_group.setLayout(training_layout)
            ml_layout.addWidget(training_group)
            
            # Framework settings
            framework_group = QGroupBox("Framework Settings", ml_tab)
            framework_layout = QFormLayout()
            
            self.default_framework = QComboBox(framework_group)
            self.default_framework.addItems(['PyTorch', 'TensorFlow'])
            framework_layout.addRow("Default Framework:", self.default_framework)
            
            framework_group.setLayout(framework_layout)
            ml_layout.addWidget(framework_group)
            
            # Add ML tab to tab widget
            tab_widget.addTab(ml_tab, "Machine Learning")
            
            # Add buttons
            button_layout = QHBoxLayout()
            self.ok_button = QPushButton("OK", self)
            self.ok_button.clicked.connect(self.accept)
            self.cancel_button = QPushButton("Cancel", self)
            self.cancel_button.clicked.connect(self.reject)
            
            button_layout.addStretch()
            button_layout.addWidget(self.ok_button)
            button_layout.addWidget(self.cancel_button)
            
            layout.addLayout(button_layout)
            
        except Exception as e:
            self.logger.error(f"Error in setup_ui: {str(e)}", exc_info=True)
            raise
            
    def choose_background_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.bg_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")
            
    def choose_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")
            
    def load_settings(self):
        """Load settings from QSettings."""
        try:
            self.logger.debug("Starting to load settings")
            
            # Editor settings
            font_family = self.settings.value('editor/font_family', 'Consolas')
            self.font_family.setCurrentText(font_family)
            self.logger.debug(f"Loaded font family: {font_family}")
            
            font_size = int(self.settings.value('editor/font_size', 11))
            self.font_size.setValue(font_size)
            self.logger.debug(f"Loaded font size: {font_size}")
            
            # Color settings
            bg_color = self.settings.value('editor/background_color', '#2D2D2D')
            self.bg_color_preview.setStyleSheet(f"background-color: {bg_color}; border: 1px solid gray;")
            self.logger.debug(f"Loaded background color: {bg_color}")
            
            text_color = self.settings.value('editor/text_color', '#FFFFFF')
            self.text_color_preview.setStyleSheet(f"background-color: {text_color}; border: 1px solid gray;")
            self.logger.debug(f"Loaded text color: {text_color}")
            
            # Editor behavior
            auto_indent = self.settings.value('editor/auto_indent', True, type=bool)
            self.auto_indent.setChecked(auto_indent)
            self.logger.debug(f"Loaded auto indent: {auto_indent}")
            
            show_line_numbers = self.settings.value('editor/show_line_numbers', True, type=bool)
            self.line_numbers.setChecked(show_line_numbers)
            self.logger.debug(f"Loaded show line numbers: {show_line_numbers}")
            
            tab_width = self.settings.value('editor/tab_width', 4, type=int)
            self.tab_width.setValue(tab_width)
            self.logger.debug(f"Loaded tab width: {tab_width}")
            
            # ML settings
            default_epochs = int(self.settings.value('ml/default_epochs', 10))
            self.default_epochs.setValue(default_epochs)
            self.logger.debug(f"Loaded default epochs: {default_epochs}")
            
            default_batch_size = int(self.settings.value('ml/default_batch_size', 32))
            self.default_batch_size.setValue(default_batch_size)
            self.logger.debug(f"Loaded default batch size: {default_batch_size}")
            
            default_learning_rate = float(self.settings.value('ml/default_learning_rate', 0.001))
            self.default_learning_rate.setValue(default_learning_rate)
            self.logger.debug(f"Loaded default learning rate: {default_learning_rate}")
            
            default_framework = self.settings.value('ml/default_framework', 'PyTorch')
            self.default_framework.setCurrentText(default_framework)
            self.logger.debug(f"Loaded default framework: {default_framework}")
            
            self.logger.debug("Settings loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading settings: {str(e)}", exc_info=True)
            raise
            
    def save_settings(self):
        """Save settings to QSettings."""
        try:
            self.logger.debug("Starting to save settings")
            
            # Editor settings
            font_family = self.font_family.currentText()
            self.settings.setValue('editor/font_family', font_family)
            self.logger.debug(f"Saved font family: {font_family}")
            
            font_size = self.font_size.value()
            self.settings.setValue('editor/font_size', font_size)
            self.logger.debug(f"Saved font size: {font_size}")
            
            # Color settings
            bg_color = self.bg_color_preview.palette().color(QPalette.ColorRole.Window).name()
            self.settings.setValue('editor/background_color', bg_color)
            self.logger.debug(f"Saved background color: {bg_color}")
            
            text_color = self.text_color_preview.palette().color(QPalette.ColorRole.Window).name()
            self.settings.setValue('editor/text_color', text_color)
            self.logger.debug(f"Saved text color: {text_color}")
            
            # Editor behavior
            auto_indent = self.auto_indent.isChecked()
            self.settings.setValue('editor/auto_indent', auto_indent)
            self.logger.debug(f"Saved auto indent: {auto_indent}")
            
            show_line_numbers = self.line_numbers.isChecked()
            self.settings.setValue('editor/show_line_numbers', show_line_numbers)
            self.logger.debug(f"Saved show line numbers: {show_line_numbers}")
            
            tab_width = self.tab_width.value()
            self.settings.setValue('editor/tab_width', tab_width)
            self.logger.debug(f"Saved tab width: {tab_width}")
            
            # ML settings
            default_epochs = self.default_epochs.value()
            self.settings.setValue('ml/default_epochs', default_epochs)
            self.logger.debug(f"Saved default epochs: {default_epochs}")
            
            default_batch_size = self.default_batch_size.value()
            self.settings.setValue('ml/default_batch_size', default_batch_size)
            self.logger.debug(f"Saved default batch size: {default_batch_size}")
            
            default_learning_rate = self.default_learning_rate.value()
            self.settings.setValue('ml/default_learning_rate', default_learning_rate)
            self.logger.debug(f"Saved default learning rate: {default_learning_rate}")
            
            default_framework = self.default_framework.currentText()
            self.settings.setValue('ml/default_framework', default_framework)
            self.logger.debug(f"Saved default framework: {default_framework}")
            
            self.settings.sync()
            self.logger.debug("Settings saved and synced successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {str(e)}", exc_info=True)
            raise
