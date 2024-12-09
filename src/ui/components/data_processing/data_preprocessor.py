"""Data preprocessing component."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QComboBox, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import pyqtSignal
import numpy as np
import pandas as pd
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
                
            # Apply scaling
            scaled_data = self._apply_scaling(self.data)
            
            # Split data
            if self.labels is not None:
                X_train, X_test, y_train, y_test = train_test_split(
                    scaled_data,
                    self.labels,
                    test_size=self.test_size_spin.value(),
                    random_state=self.random_seed_spin.value()
                )
                processed_data = (X_train, X_test)
                processed_labels = (y_train, y_test)
            else:
                processed_data = scaled_data
                processed_labels = None
            
            self.preprocessing_completed.emit(processed_data, processed_labels)
            
        except Exception as e:
            self.logger.error(f"Error processing data: {str(e)}")
            
    def _apply_scaling(self, data):
        """Apply selected scaling method to data."""
        try:
            scaling_method = self.scaling_combo.currentText()
            
            if scaling_method == "Standard Scaling":
                self.scaler = StandardScaler()
            elif scaling_method == "Min-Max Scaling":
                self.scaler = MinMaxScaler()
            elif scaling_method == "Robust Scaling":
                self.scaler = RobustScaler()
            else:  # No scaling
                return data
            
            if isinstance(data, pd.DataFrame):
                return pd.DataFrame(
                    self.scaler.fit_transform(data),
                    columns=data.columns,
                    index=data.index
                )
            else:
                return self.scaler.fit_transform(data)
            
        except Exception as e:
            self.logger.error(f"Error applying scaling: {str(e)}")
            return data
            
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
