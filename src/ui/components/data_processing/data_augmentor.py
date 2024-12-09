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
        
        # Augmentation methods
        self.noise_check = QCheckBox("Add Gaussian Noise")
        self.noise_strength = QDoubleSpinBox()
        self.noise_strength.setRange(0.01, 1.0)
        self.noise_strength.setValue(0.1)
        
        self.rotation_check = QCheckBox("Random Rotation")
        self.rotation_angle = QDoubleSpinBox()
        self.rotation_angle.setRange(0, 180)
        self.rotation_angle.setValue(30)
        
        self.flip_check = QCheckBox("Random Flip")
        
        self.scale_check = QCheckBox("Random Scaling")
        self.scale_factor = QDoubleSpinBox()
        self.scale_factor.setRange(0.5, 2.0)
        self.scale_factor.setValue(1.2)
        
        # Add controls to layout
        for control in [
            (self.noise_check, self.noise_strength),
            (self.rotation_check, self.rotation_angle),
            (self.flip_check, None),
            (self.scale_check, self.scale_factor)
        ]:
            h_layout = QHBoxLayout()
            h_layout.addWidget(control[0])
            if control[1]:
                h_layout.addWidget(control[1])
            layout.addLayout(h_layout)
        
        # Augment button
        self.augment_btn = QPushButton("Augment Data")
        self.augment_btn.clicked.connect(self._augment_data)
        layout.addWidget(self.augment_btn)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.data = None
        self.labels = None
        
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
            
            if self.noise_check.isChecked():
                augmented_data = self._add_noise(augmented_data)
                
            if self.rotation_check.isChecked():
                augmented_data = self._rotate_data(augmented_data)
                
            if self.flip_check.isChecked():
                augmented_data = self._flip_data(augmented_data)
                
            if self.scale_check.isChecked():
                augmented_data = self._scale_data(augmented_data)
            
            # Combine original and augmented data
            combined_data = torch.cat([self.data, augmented_data])
            if augmented_labels is not None:
                combined_labels = torch.cat([self.labels, augmented_labels])
            else:
                combined_labels = None
            
            self.augmentation_completed.emit(combined_data, combined_labels)
            
        except Exception as e:
            self.logger.error(f"Error augmenting data: {str(e)}")
            
    def _add_noise(self, data):
        """Add Gaussian noise to data."""
        try:
            noise = torch.randn_like(data) * self.noise_strength.value()
            return data + noise
        except Exception as e:
            self.logger.error(f"Error adding noise: {str(e)}")
            return data
            
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
        self.noise_check.setChecked(False)
        self.rotation_check.setChecked(False)
        self.flip_check.setChecked(False)
        self.scale_check.setChecked(False)
        self.augment_btn.setEnabled(False)
