"""Data preprocessing component."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QComboBox, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import pyqtSignal
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.model_selection import train_test_split
import logging

class DataPreprocessor(QWidget):
    """Widget for data preprocessing operations."""
    
    preprocessing_completed = pyqtSignal(object, object)  # Emits processed data and labels
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_state()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Scaling method selection
        scaling_layout = QHBoxLayout()
        self.scaling_combo = QComboBox()
        self.scaling_combo.addItems([
            "Standard Scaling",
            "Min-Max Scaling",
            "Robust Scaling",
            "No Scaling"
        ])
        scaling_layout.addWidget(QLabel("Scaling Method:"))
        scaling_layout.addWidget(self.scaling_combo)
        
        # Train-test split controls
        split_layout = QHBoxLayout()
        self.test_size_spin = QDoubleSpinBox()
        self.test_size_spin.setRange(0.1, 0.5)
        self.test_size_spin.setSingleStep(0.1)
        self.test_size_spin.setValue(0.2)
        split_layout.addWidget(QLabel("Test Size:"))
        split_layout.addWidget(self.test_size_spin)
        
        # Random seed
        seed_layout = QHBoxLayout()
        self.random_seed_spin = QSpinBox()
        self.random_seed_spin.setRange(0, 9999)
        self.random_seed_spin.setValue(42)
        seed_layout.addWidget(QLabel("Random Seed:"))
        seed_layout.addWidget(self.random_seed_spin)
        
        # Process button
        self.process_btn = QPushButton("Process Data")
        self.process_btn.clicked.connect(self._process_data)
        
        # Add all layouts
        layout.addLayout(scaling_layout)
        layout.addLayout(split_layout)
        layout.addLayout(seed_layout)
        layout.addWidget(self.process_btn)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.data = None
        self.labels = None
        self.scaler = None
        self.processed_data = None
        self.processed_labels = None
        
    def set_data(self, data, labels=None):
        """Set data for preprocessing."""
        try:
            self.data = data
            self.labels = labels
            self.process_btn.setEnabled(True)
        except Exception as e:
            self.logger.error(f"Error setting data: {str(e)}")
            
    def _process_data(self):
        """Process the data according to selected options."""
        try:
            if self.data is None:
                return
                
            # Apply scaling to training data first
            X_train, X_test, y_train, y_test = train_test_split(
                self.data,
                self.labels,
                test_size=self.test_size_spin.value(),
                random_state=self.random_seed_spin.value()
            )
            
            # Scale training data and fit scaler
            X_train_scaled = self._apply_scaling(X_train)
            
            # Scale test data using the same scaler
            X_test_scaled = self._apply_scaling(X_test)
            
            self.processed_data = (X_train_scaled, X_test_scaled)
            self.processed_labels = (y_train, y_test)
            
            # Emit the processed data
            self.preprocessing_completed.emit(self.processed_data, self.processed_labels)
            
        except Exception as e:
            self.logger.error(f"Error processing data: {str(e)}")
            raise
            
    def _apply_scaling(self, data):
        """Apply selected scaling method to data."""
        try:
            scaling_method = self.scaling_combo.currentText()
            
            if scaling_method == "No Scaling":
                return data
                
            # Convert to numpy for sklearn, ensuring double precision
            if isinstance(data, torch.Tensor):
                data_np = data.numpy().astype(np.float64)
            else:
                data_np = np.asarray(data, dtype=np.float64)
                
            # Reshape if needed (sklearn expects 2D array)
            original_shape = data_np.shape
            if len(data_np.shape) == 1:
                data_np = data_np.reshape(-1, 1)
                
            # Create and fit scaler if not already fitted
            if self.scaler is None:
                if scaling_method == "Standard Scaling":
                    self.scaler = StandardScaler(copy=True)
                elif scaling_method == "Min-Max Scaling":
                    self.scaler = MinMaxScaler(copy=True)
                elif scaling_method == "Robust Scaling":
                    self.scaler = RobustScaler(copy=True)
                    
                # Fit the scaler on training data
                self.scaler.fit(data_np)
                
            # Transform the data
            scaled_data = self.scaler.transform(data_np)
            
            # Reshape back if needed
            if len(original_shape) == 1:
                scaled_data = scaled_data.reshape(-1)
                
            # Convert back to tensor if needed, maintaining precision
            if isinstance(data, torch.Tensor):
                scaled_data = torch.from_numpy(scaled_data.astype(np.float32)).to(data.dtype)
                
            return scaled_data
            
        except Exception as e:
            self.logger.error(f"Error applying scaling: {str(e)}")
            raise
            
    def get_scaler(self):
        """Get the fitted scaler."""
        return self.scaler
        
    def reset(self):
        """Reset preprocessor state."""
        self._initialize_state()
        self.scaling_combo.setCurrentIndex(0)
        self.test_size_spin.setValue(0.2)
        self.random_seed_spin.setValue(42)
        self.process_btn.setEnabled(False)
