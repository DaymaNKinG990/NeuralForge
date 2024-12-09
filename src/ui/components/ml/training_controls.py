"""Training control component for ML workspace."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QSpinBox, QDoubleSpinBox, QLabel, QProgressBar)
from PyQt6.QtCore import pyqtSignal
import logging

class TrainingControls(QWidget):
    """Widget for ML training controls."""
    
    training_started = pyqtSignal()
    training_stopped = pyqtSignal()
    hyperparameters_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Hyperparameters
        params_layout = QVBoxLayout()
        
        # Learning rate
        lr_layout = QHBoxLayout()
        lr_label = QLabel("Learning Rate:")
        self.lr_spin = QDoubleSpinBox()
        self.lr_spin.setRange(0.0001, 1.0)
        self.lr_spin.setSingleStep(0.0001)
        self.lr_spin.setValue(0.001)
        self.lr_spin.valueChanged.connect(self._on_params_changed)
        lr_layout.addWidget(lr_label)
        lr_layout.addWidget(self.lr_spin)
        
        # Batch size
        batch_layout = QHBoxLayout()
        batch_label = QLabel("Batch Size:")
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 1024)
        self.batch_spin.setValue(32)
        self.batch_spin.valueChanged.connect(self._on_params_changed)
        batch_layout.addWidget(batch_label)
        batch_layout.addWidget(self.batch_spin)
        
        # Epochs
        epochs_layout = QHBoxLayout()
        epochs_label = QLabel("Epochs:")
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 1000)
        self.epochs_spin.setValue(10)
        self.epochs_spin.valueChanged.connect(self._on_params_changed)
        epochs_layout.addWidget(epochs_label)
        epochs_layout.addWidget(self.epochs_spin)
        
        params_layout.addLayout(lr_layout)
        params_layout.addLayout(batch_layout)
        params_layout.addLayout(epochs_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Training")
        self.stop_button = QPushButton("Stop Training")
        self.stop_button.setEnabled(False)
        
        self.start_button.clicked.connect(self._on_start_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        
        # Add all to main layout
        layout.addLayout(params_layout)
        layout.addWidget(self.progress_bar)
        layout.addLayout(buttons_layout)
        
    def _on_params_changed(self):
        """Handle hyperparameter changes."""
        try:
            params = {
                'learning_rate': self.lr_spin.value(),
                'batch_size': self.batch_spin.value(),
                'epochs': self.epochs_spin.value()
            }
            self.hyperparameters_changed.emit(params)
        except Exception as e:
            self.logger.error(f"Error in parameter change: {str(e)}")
            
    def _on_start_clicked(self):
        """Handle start button click."""
        try:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.training_started.emit()
        except Exception as e:
            self.logger.error(f"Error starting training: {str(e)}")
            
    def _on_stop_clicked(self):
        """Handle stop button click."""
        try:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.training_stopped.emit()
        except Exception as e:
            self.logger.error(f"Error stopping training: {str(e)}")
            
    def update_progress(self, value: int):
        """Update progress bar value."""
        self.progress_bar.setValue(value)
        
    def reset(self):
        """Reset controls to initial state."""
        self.progress_bar.setValue(0)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
