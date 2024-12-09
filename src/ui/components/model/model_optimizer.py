"""Model optimization component."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QComboBox, QDoubleSpinBox)
from PyQt6.QtCore import pyqtSignal
import torch.optim as optim
import logging

class ModelOptimizer(QWidget):
    """Widget for configuring model optimization."""
    
    optimizer_created = pyqtSignal(object)  # Emits created optimizer
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_state()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Optimizer selection
        optimizer_layout = QHBoxLayout()
        self.optimizer_combo = QComboBox()
        self.optimizer_combo.addItems([
            "Adam",
            "SGD",
            "RMSprop",
            "AdamW"
        ])
        optimizer_layout.addWidget(QLabel("Optimizer:"))
        optimizer_layout.addWidget(self.optimizer_combo)
        
        # Learning rate
        lr_layout = QHBoxLayout()
        self.lr_spin = QDoubleSpinBox()
        self.lr_spin.setRange(0.00001, 1.0)
        self.lr_spin.setSingleStep(0.0001)
        self.lr_spin.setDecimals(6)  # Allow more decimal places
        self.lr_spin.setValue(0.001)
        lr_layout.addWidget(QLabel("Learning Rate:"))
        lr_layout.addWidget(self.lr_spin)
        
        # Weight decay
        wd_layout = QHBoxLayout()
        self.wd_spin = QDoubleSpinBox()
        self.wd_spin.setRange(0, 0.1)
        self.wd_spin.setSingleStep(0.001)
        self.wd_spin.setDecimals(6)  # Allow more decimal places
        self.wd_spin.setValue(0)
        wd_layout.addWidget(QLabel("Weight Decay:"))
        wd_layout.addWidget(self.wd_spin)
        
        # Momentum (for SGD)
        momentum_layout = QHBoxLayout()
        self.momentum_spin = QDoubleSpinBox()
        self.momentum_spin.setRange(0, 1.0)
        self.momentum_spin.setSingleStep(0.1)
        self.momentum_spin.setDecimals(6)  # Allow more decimal places
        self.momentum_spin.setValue(0.9)
        self.momentum_spin.setEnabled(False)
        momentum_layout.addWidget(QLabel("Momentum:"))
        momentum_layout.addWidget(self.momentum_spin)
        
        # Create button
        self.create_btn = QPushButton("Create Optimizer")
        self.create_btn.clicked.connect(self._create_optimizer)
        
        # Add all layouts
        layout.addLayout(optimizer_layout)
        layout.addLayout(lr_layout)
        layout.addLayout(wd_layout)
        layout.addLayout(momentum_layout)
        layout.addWidget(self.create_btn)
        
        # Connect signals
        self.optimizer_combo.currentTextChanged.connect(self._update_ui)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.model = None
        
    def set_model(self, model):
        """Set model for optimization."""
        try:
            self.model = model
            self.create_btn.setEnabled(True)
        except Exception as e:
            self.logger.error(f"Error setting model: {str(e)}", exc_info=True)
            
    def _update_ui(self):
        """Update UI based on selected optimizer."""
        try:
            optimizer = self.optimizer_combo.currentText()
            self.momentum_spin.setEnabled(optimizer == "SGD")
        except Exception as e:
            self.logger.error(f"Error updating UI: {str(e)}", exc_info=True)
            
    def _create_optimizer(self):
        """Create optimizer with selected configuration."""
        try:
            if self.model is None:
                return
                
            optimizer_type = self.optimizer_combo.currentText()
            
            # Get parameters, ensuring they are float values
            lr = float(self.lr_spin.value())
            weight_decay = float(self.wd_spin.value())
            
            params = {
                "lr": lr,
                "weight_decay": weight_decay
            }
            
            if optimizer_type == "SGD":
                params["momentum"] = float(self.momentum_spin.value())
                
            optimizer = None
            if optimizer_type == "Adam":
                optimizer = optim.Adam(self.model.parameters(), **params)
            elif optimizer_type == "SGD":
                optimizer = optim.SGD(self.model.parameters(), **params)
            elif optimizer_type == "RMSprop":
                optimizer = optim.RMSprop(self.model.parameters(), **params)
            elif optimizer_type == "AdamW":
                optimizer = optim.AdamW(self.model.parameters(), **params)
                
            if optimizer:
                self.optimizer_created.emit(optimizer)
            
        except Exception as e:
            self.logger.error(f"Error creating optimizer: {str(e)}", exc_info=True)
            
    def reset(self):
        """Reset optimizer state."""
        self._initialize_state()
        self.optimizer_combo.setCurrentIndex(0)
        self.lr_spin.setValue(0.001)
        self.wd_spin.setValue(0)
        self.momentum_spin.setValue(0.9)
        self.create_btn.setEnabled(False)
