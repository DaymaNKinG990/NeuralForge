"""Model management component for ML workspace."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QFileDialog, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import pyqtSignal
import logging
from typing import Dict, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn

class ModelManager(QWidget):
    """Widget for managing ML model operations."""
    
    model_created = pyqtSignal(object)  # Emitted when model is created
    training_step = pyqtSignal(dict)    # Emitted for each training step
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_model()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Model parameters section
        params_layout = QVBoxLayout()
        
        # Hidden layers
        layers_layout = QHBoxLayout()
        layers_layout.addWidget(QLabel("Hidden Layers:"))
        self.layers_spin = QSpinBox()
        self.layers_spin.setRange(1, 10)
        self.layers_spin.setValue(2)
        layers_layout.addWidget(self.layers_spin)
        
        # Units per layer
        units_layout = QHBoxLayout()
        units_layout.addWidget(QLabel("Units per Layer:"))
        self.units_spin = QSpinBox()
        self.units_spin.setRange(8, 512)
        self.units_spin.setValue(64)
        self.units_spin.setSingleStep(8)
        units_layout.addWidget(self.units_spin)
        
        # Dropout rate
        dropout_layout = QHBoxLayout()
        dropout_layout.addWidget(QLabel("Dropout Rate:"))
        self.dropout_spin = QDoubleSpinBox()
        self.dropout_spin.setRange(0.0, 0.9)
        self.dropout_spin.setValue(0.2)
        self.dropout_spin.setSingleStep(0.1)
        dropout_layout.addWidget(self.dropout_spin)
        
        params_layout.addLayout(layers_layout)
        params_layout.addLayout(units_layout)
        params_layout.addLayout(dropout_layout)
        
        # Model controls
        controls_layout = QHBoxLayout()
        self.create_btn = QPushButton("Create Model")
        self.save_btn = QPushButton("Save Model")
        self.load_btn = QPushButton("Load Model")
        
        self.create_btn.clicked.connect(self._create_model)
        self.save_btn.clicked.connect(self._save_model)
        self.load_btn.clicked.connect(self._load_model)
        
        self.save_btn.setEnabled(False)
        
        controls_layout.addWidget(self.create_btn)
        controls_layout.addWidget(self.save_btn)
        controls_layout.addWidget(self.load_btn)
        
        # Add all layouts
        layout.addLayout(params_layout)
        layout.addLayout(controls_layout)
        
    def _initialize_model(self):
        """Initialize model storage."""
        self.model = None
        self.optimizer = None
        self.criterion = None
        
    def _create_model(self):
        """Create neural network model."""
        try:
            input_size = self._get_input_size()
            if input_size is None:
                return
                
            # Create model architecture
            layers = []
            prev_size = input_size
            
            # Hidden layers
            for _ in range(self.layers_spin.value()):
                units = self.units_spin.value()
                layers.extend([
                    nn.Linear(prev_size, units),
                    nn.ReLU(),
                    nn.Dropout(self.dropout_spin.value())
                ])
                prev_size = units
                
            # Output layer (assuming binary classification)
            layers.append(nn.Linear(prev_size, 1))
            layers.append(nn.Sigmoid())
            
            # Create model
            self.model = nn.Sequential(*layers)
            
            # Setup training components
            self.criterion = nn.BCELoss()
            self.optimizer = torch.optim.Adam(self.model.parameters())
            
            self.save_btn.setEnabled(True)
            self.model_created.emit(self.model)
            
        except Exception as e:
            self.logger.error(f"Error creating model: {str(e)}")
            
    def _save_model(self):
        """Save model to file."""
        try:
            if self.model is None:
                raise ValueError("No model to save")
                
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Model",
                "",
                "PyTorch Models (*.pth)"
            )
            
            if file_path:
                torch.save({
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                }, file_path)
                
        except Exception as e:
            self.logger.error(f"Error saving model: {str(e)}")
            
    def _load_model(self):
        """Load model from file."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Load Model",
                "",
                "PyTorch Models (*.pth)"
            )
            
            if file_path:
                self._create_model()  # Create model architecture first
                
                checkpoint = torch.load(file_path)
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                
                self.save_btn.setEnabled(True)
                self.model_created.emit(self.model)
                
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            
    def train_step(self, batch_data: Tuple[torch.Tensor, torch.Tensor]) -> Dict:
        """Perform single training step."""
        try:
            if self.model is None:
                raise ValueError("No model created")
                
            X_batch, y_batch = batch_data
            
            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(X_batch)
            loss = self.criterion(outputs, y_batch)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            # Calculate metrics
            with torch.no_grad():
                predictions = (outputs > 0.5).float()
                accuracy = (predictions == y_batch).float().mean()
                
            metrics = {
                'loss': loss.item(),
                'accuracy': accuracy.item()
            }
            
            self.training_step.emit(metrics)
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error in training step: {str(e)}")
            return None
            
    def _get_input_size(self) -> Optional[int]:
        """Get input size from data manager."""
        try:
            # This should be connected to DataManager's data
            # For now, return a default value
            return 10
        except Exception as e:
            self.logger.error(f"Error getting input size: {str(e)}")
            return None
            
    def get_model(self) -> Optional[nn.Module]:
        """Get current model."""
        return self.model
        
    def reset(self):
        """Reset model manager state."""
        try:
            self._initialize_model()
            self.save_btn.setEnabled(False)
        except Exception as e:
            self.logger.error(f"Error resetting model manager: {str(e)}")
