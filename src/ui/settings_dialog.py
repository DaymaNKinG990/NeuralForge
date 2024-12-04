from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QPushButton, QLabel, QSpinBox, QComboBox,
                             QCheckBox, QFontComboBox, QColorDialog,
                             QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont, QColor

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings('NeuroForge', 'IDE')
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Editor settings tab
        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)
        
        # Font settings
        font_group = QGroupBox("Font Settings")
        font_layout = QFormLayout()
        
        self.font_family = QFontComboBox()
        font_layout.addRow("Font Family:", self.font_family)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        font_layout.addRow("Font Size:", self.font_size)
        
        font_group.setLayout(font_layout)
        editor_layout.addWidget(font_group)
        
        # Color settings
        color_group = QGroupBox("Color Settings")
        color_layout = QFormLayout()
        
        # Background color
        bg_layout = QHBoxLayout()
        self.bg_color_preview = QLabel()
        self.bg_color_preview.setFixedSize(20, 20)
        self.bg_color_preview.setStyleSheet("background-color: #2D2D2D; border: 1px solid gray;")
        bg_layout.addWidget(self.bg_color_preview)
        
        self.bg_color_btn = QPushButton("Choose...")
        self.bg_color_btn.clicked.connect(lambda: self.choose_color('background'))
        bg_layout.addWidget(self.bg_color_btn)
        bg_layout.addStretch()
        
        color_layout.addRow("Background Color:", bg_layout)
        
        # Text color
        text_layout = QHBoxLayout()
        self.text_color_preview = QLabel()
        self.text_color_preview.setFixedSize(20, 20)
        self.text_color_preview.setStyleSheet("background-color: #FFFFFF; border: 1px solid gray;")
        text_layout.addWidget(self.text_color_preview)
        
        self.text_color_btn = QPushButton("Choose...")
        self.text_color_btn.clicked.connect(lambda: self.choose_color('text'))
        text_layout.addWidget(self.text_color_btn)
        text_layout.addStretch()
        
        color_layout.addRow("Text Color:", text_layout)
        
        color_group.setLayout(color_layout)
        editor_layout.addWidget(color_group)
        
        # Editor behavior
        behavior_group = QGroupBox("Editor Behavior")
        behavior_layout = QFormLayout()
        
        self.auto_indent = QCheckBox()
        behavior_layout.addRow("Auto Indent:", self.auto_indent)
        
        self.line_numbers = QCheckBox()
        behavior_layout.addRow("Show Line Numbers:", self.line_numbers)
        
        self.tab_width = QSpinBox()
        self.tab_width.setRange(2, 8)
        behavior_layout.addRow("Tab Width:", self.tab_width)
        
        behavior_group.setLayout(behavior_layout)
        editor_layout.addWidget(behavior_group)
        
        editor_layout.addStretch()
        tab_widget.addTab(editor_tab, "Editor")
        
        # ML settings tab
        ml_tab = QWidget()
        ml_layout = QVBoxLayout(ml_tab)
        
        # Training settings
        training_group = QGroupBox("Training Settings")
        training_layout = QFormLayout()
        
        self.default_epochs = QSpinBox()
        self.default_epochs.setRange(1, 1000)
        training_layout.addRow("Default Epochs:", self.default_epochs)
        
        self.default_batch_size = QSpinBox()
        self.default_batch_size.setRange(1, 1024)
        training_layout.addRow("Default Batch Size:", self.default_batch_size)
        
        self.default_learning_rate = QDoubleSpinBox()
        self.default_learning_rate.setRange(0.0001, 1.0)
        self.default_learning_rate.setSingleStep(0.0001)
        training_layout.addRow("Default Learning Rate:", self.default_learning_rate)
        
        training_group.setLayout(training_layout)
        ml_layout.addWidget(training_group)
        
        # Framework settings
        framework_group = QGroupBox("Framework Settings")
        framework_layout = QFormLayout()
        
        self.default_framework = QComboBox()
        self.default_framework.addItems(['PyTorch', 'TensorFlow'])
        framework_layout.addRow("Default Framework:", self.default_framework)
        
        framework_group.setLayout(framework_layout)
        ml_layout.addWidget(framework_group)
        
        ml_layout.addStretch()
        tab_widget.addTab(ml_tab, "Machine Learning")
        
        layout.addWidget(tab_widget)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def choose_color(self, color_type):
        color = QColorDialog.getColor()
        if color.isValid():
            if color_type == 'background':
                self.bg_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")
            elif color_type == 'text':
                self.text_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")
                
    def load_settings(self):
        # Editor settings
        font_family = self.settings.value('editor/font_family', 'Consolas')
        font_size = int(self.settings.value('editor/font_size', 10))
        bg_color = self.settings.value('editor/background_color', '#2D2D2D')
        text_color = self.settings.value('editor/text_color', '#FFFFFF')
        auto_indent = bool(self.settings.value('editor/auto_indent', True))
        line_numbers = bool(self.settings.value('editor/line_numbers', True))
        tab_width = int(self.settings.value('editor/tab_width', 4))
        
        self.font_family.setCurrentFont(QFont(font_family))
        self.font_size.setValue(font_size)
        self.bg_color_preview.setStyleSheet(f"background-color: {bg_color}; border: 1px solid gray;")
        self.text_color_preview.setStyleSheet(f"background-color: {text_color}; border: 1px solid gray;")
        self.auto_indent.setChecked(auto_indent)
        self.line_numbers.setChecked(line_numbers)
        self.tab_width.setValue(tab_width)
        
        # ML settings
        default_epochs = int(self.settings.value('ml/default_epochs', 10))
        default_batch_size = int(self.settings.value('ml/default_batch_size', 32))
        default_learning_rate = float(self.settings.value('ml/default_learning_rate', 0.001))
        default_framework = self.settings.value('ml/default_framework', 'PyTorch')
        
        self.default_epochs.setValue(default_epochs)
        self.default_batch_size.setValue(default_batch_size)
        self.default_learning_rate.setValue(default_learning_rate)
        self.default_framework.setCurrentText(default_framework)
        
    def save_settings(self):
        # Editor settings
        self.settings.setValue('editor/font_family', self.font_family.currentFont().family())
        self.settings.setValue('editor/font_size', self.font_size.value())
        self.settings.setValue('editor/background_color', self.bg_color_preview.styleSheet().split(':')[1].split(';')[0].strip())
        self.settings.setValue('editor/text_color', self.text_color_preview.styleSheet().split(':')[1].split(';')[0].strip())
        self.settings.setValue('editor/auto_indent', self.auto_indent.isChecked())
        self.settings.setValue('editor/line_numbers', self.line_numbers.isChecked())
        self.settings.setValue('editor/tab_width', self.tab_width.value())
        
        # ML settings
        self.settings.setValue('ml/default_epochs', self.default_epochs.value())
        self.settings.setValue('ml/default_batch_size', self.default_batch_size.value())
        self.settings.setValue('ml/default_learning_rate', self.default_learning_rate.value())
        self.settings.setValue('ml/default_framework', self.default_framework.currentText())
        
        self.accept()
