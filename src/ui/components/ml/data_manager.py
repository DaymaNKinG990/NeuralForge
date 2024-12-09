"""Data management component for ML workspace."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QFileDialog, QProgressBar, QComboBox)
from PyQt6.QtCore import pyqtSignal
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional

class DataManager(QWidget):
    """Widget for managing ML dataset operations."""
    
    data_loaded = pyqtSignal(object)  # Emitted when data is loaded
    data_preprocessed = pyqtSignal(tuple)  # Emitted when data is preprocessed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_data()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Data loading section
        load_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load Dataset")
        self.load_btn.clicked.connect(self._load_dataset)
        self.dataset_label = QLabel("No dataset loaded")
        load_layout.addWidget(self.load_btn)
        load_layout.addWidget(self.dataset_label)
        
        # Data info section
        info_layout = QVBoxLayout()
        self.info_label = QLabel("Dataset Information:")
        self.shape_label = QLabel("Shape: -")
        self.features_label = QLabel("Features: -")
        info_layout.addWidget(self.info_label)
        info_layout.addWidget(self.shape_label)
        info_layout.addWidget(self.features_label)
        
        # Preprocessing options
        preprocess_layout = QVBoxLayout()
        self.normalize_combo = QComboBox()
        self.normalize_combo.addItems(["None", "MinMax", "Standard", "Robust"])
        
        self.split_ratio_combo = QComboBox()
        self.split_ratio_combo.addItems(["70/30", "80/20", "90/10"])
        
        preprocess_layout.addWidget(QLabel("Normalization:"))
        preprocess_layout.addWidget(self.normalize_combo)
        preprocess_layout.addWidget(QLabel("Train/Test Split:"))
        preprocess_layout.addWidget(self.split_ratio_combo)
        
        # Preprocess button
        self.preprocess_btn = QPushButton("Preprocess Data")
        self.preprocess_btn.clicked.connect(self._preprocess_data)
        self.preprocess_btn.setEnabled(False)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Add all layouts
        layout.addLayout(load_layout)
        layout.addLayout(info_layout)
        layout.addLayout(preprocess_layout)
        layout.addWidget(self.preprocess_btn)
        layout.addWidget(self.progress_bar)
        
    def _initialize_data(self):
        """Initialize data storage."""
        self.data = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        
    def _load_dataset(self):
        """Load dataset from file."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Load Dataset",
                "",
                "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
            )
            
            if file_path:
                if file_path.endswith('.csv'):
                    self.data = pd.read_csv(file_path)
                else:
                    self.data = pd.read_excel(file_path)
                    
                self._update_info()
                self.preprocess_btn.setEnabled(True)
                self.data_loaded.emit(self.data)
                
        except Exception as e:
            self.logger.error(f"Error loading dataset: {str(e)}")
            self.dataset_label.setText(f"Error loading dataset: {str(e)}")
            
    def _update_info(self):
        """Update dataset information display."""
        if self.data is not None:
            self.dataset_label.setText("Dataset loaded successfully")
            self.shape_label.setText(f"Shape: {self.data.shape}")
            self.features_label.setText(f"Features: {', '.join(self.data.columns)}")
            
    def _preprocess_data(self):
        """Preprocess the loaded dataset."""
        try:
            if self.data is None:
                raise ValueError("No dataset loaded")
                
            self.progress_bar.setValue(0)
            
            # Split features and target
            X = self.data.iloc[:, :-1]  # All columns except last
            y = self.data.iloc[:, -1]   # Last column as target
            
            self.progress_bar.setValue(20)
            
            # Normalize data
            X_normalized = self._normalize_data(X)
            
            self.progress_bar.setValue(50)
            
            # Split data
            train_data = self._split_data(X_normalized, y)
            
            self.progress_bar.setValue(80)
            
            if train_data:
                self.X_train, self.X_test, self.y_train, self.y_test = train_data
                self.data_preprocessed.emit(train_data)
                
            self.progress_bar.setValue(100)
            
        except Exception as e:
            self.logger.error(f"Error preprocessing data: {str(e)}")
            self.progress_bar.setValue(0)
            
    def _normalize_data(self, X: pd.DataFrame) -> pd.DataFrame:
        """Normalize the features based on selected method."""
        method = self.normalize_combo.currentText()
        
        if method == "MinMax":
            return (X - X.min()) / (X.max() - X.min())
        elif method == "Standard":
            return (X - X.mean()) / X.std()
        elif method == "Robust":
            median = X.median()
            iqr = X.quantile(0.75) - X.quantile(0.25)
            return (X - median) / iqr
        else:
            return X
            
    def _split_data(self, X: pd.DataFrame, y: pd.Series) -> Optional[Tuple]:
        """Split data into training and testing sets."""
        ratio = float(self.split_ratio_combo.currentText().split('/')[0]) / 100
        
        try:
            from sklearn.model_selection import train_test_split
            return train_test_split(X, y, train_size=ratio, random_state=42)
        except Exception as e:
            self.logger.error(f"Error splitting data: {str(e)}")
            return None
            
    def get_training_data(self) -> Optional[Tuple]:
        """Get preprocessed training data."""
        if all(v is not None for v in [self.X_train, self.X_test, self.y_train, self.y_test]):
            return self.X_train, self.X_test, self.y_train, self.y_test
        return None
        
    def reset(self):
        """Reset data manager state."""
        try:
            self._initialize_data()
            self.dataset_label.setText("No dataset loaded")
            self.shape_label.setText("Shape: -")
            self.features_label.setText("Features: -")
            self.progress_bar.setValue(0)
            self.preprocess_btn.setEnabled(False)
        except Exception as e:
            self.logger.error(f"Error resetting data manager: {str(e)}")
