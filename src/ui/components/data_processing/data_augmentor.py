"""Data augmentation component."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QComboBox, QDoubleSpinBox, QCheckBox)
from PyQt6.QtCore import pyqtSignal
import numpy as np
import torch
from torch.utils.data import Dataset
import logging

class DataAugmentor(QWidget):
    """Widget for data augmentation operations."""
    
    augmentation_completed = pyqtSignal(object, object)  # Emits augmented data and labels
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_state()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Augmentation method selection
        method_layout = QHBoxLayout()
        self.augmentation_combo = QComboBox()
        self.augmentation_combo.addItems([
            "Add Noise",
            "Random Rotation",
            "Random Flip",
            "Random Scaling"
        ])
        method_layout.addWidget(QLabel("Augmentation Method:"))
        method_layout.addWidget(self.augmentation_combo)
        layout.addLayout(method_layout)
        
        # Parameters for each method
        params_layout = QVBoxLayout()
        
        # Noise parameters
        noise_layout = QHBoxLayout()
        self.noise_std = QDoubleSpinBox()
        self.noise_std.setRange(0.01, 1.0)
        self.noise_std.setValue(0.1)
        noise_layout.addWidget(QLabel("Noise Std:"))
        noise_layout.addWidget(self.noise_std)
        params_layout.addLayout(noise_layout)
        
        # Rotation parameters
        rotation_layout = QHBoxLayout()
        self.rotation_angle = QDoubleSpinBox()
        self.rotation_angle.setRange(0, 180)
        self.rotation_angle.setValue(30)
        rotation_layout.addWidget(QLabel("Rotation Angle:"))
        rotation_layout.addWidget(self.rotation_angle)
        params_layout.addLayout(rotation_layout)
        
        # Scale parameters
        scale_layout = QHBoxLayout()
        self.scale_factor = QDoubleSpinBox()
        self.scale_factor.setRange(0.5, 2.0)
        self.scale_factor.setValue(1.2)
        scale_layout.addWidget(QLabel("Scale Factor:"))
        scale_layout.addWidget(self.scale_factor)
        params_layout.addLayout(scale_layout)
        
        layout.addLayout(params_layout)
        
        # Augment button
        self.augment_btn = QPushButton("Augment Data")
        self.augment_btn.clicked.connect(self._augment_data)
        layout.addWidget(self.augment_btn)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.data = None
        self.labels = None
        self.augmented_data = None
        self.augmented_labels = None
        
    def set_data(self, data, labels=None):
        """Set data for augmentation."""
        try:
            self.data = data
            self.labels = labels
            self.augment_btn.setEnabled(True)
        except Exception as e:
            self.logger.error(f"Error setting data: {str(e)}")
            
    def _augment_data(self):
        """Apply selected augmentation methods to data."""
        try:
            if self.data is None:
                return
                
            augmented_data = self.data.clone()
            augmented_labels = self.labels.clone() if self.labels is not None else None
            
            method = self.augmentation_combo.currentText()
            
            if method == "Add Noise":
                augmented_data = self._add_noise(augmented_data)
            elif method == "Random Rotation":
                augmented_data = self._rotate_data(augmented_data)
            elif method == "Random Flip":
                augmented_data = self._flip_data(augmented_data)
            elif method == "Random Scaling":
                augmented_data = self._scale_data(augmented_data)
            
            # Store augmented data
            self.augmented_data = augmented_data
            self.augmented_labels = augmented_labels
            
            # Emit the augmented data
            self.augmentation_completed.emit(self.augmented_data, self.augmented_labels)
            
        except Exception as e:
            self.logger.error(f"Error augmenting data: {str(e)}")
            raise
            
    def _add_noise(self, data):
        """Add Gaussian noise to data."""
        noise = torch.randn_like(data) * self.noise_std.value()
        return data + noise
            
    def _rotate_data(self, data):
        """Rotate data if applicable."""
        try:
            if len(data.shape) == 4:  # Image data
                angle = torch.rand(1) * self.rotation_angle.value()
                # Implement rotation logic here
                return data
            return data
        except Exception as e:
            self.logger.error(f"Error rotating data: {str(e)}")
            return data
            
    def _flip_data(self, data):
        """Randomly flip data if applicable."""
        try:
            if len(data.shape) >= 2:
                flip_mask = torch.rand(len(data)) > 0.5
                data[flip_mask] = torch.flip(data[flip_mask], dims=[-1])
            return data
        except Exception as e:
            self.logger.error(f"Error flipping data: {str(e)}")
            return data
            
    def _scale_data(self, data):
        """Scale data by random factor."""
        try:
            scale = torch.rand(len(data)) * (self.scale_factor.value() - 1) + 1
            return data * scale.view(-1, 1)
        except Exception as e:
            self.logger.error(f"Error scaling data: {str(e)}")
            return data
            
    def reset(self):
        """Reset augmentor state."""
        self._initialize_state()
        self.augment_btn.setEnabled(False)
