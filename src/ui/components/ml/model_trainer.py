"""Model trainer component integrating hyperparameter tuning and experiment tracking."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QComboBox, QProgressBar, QTabWidget)
from PyQt6.QtCore import pyqtSignal, Qt
import logging
from typing import Dict, Optional, Any, List
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from datetime import datetime

from .advanced_hyperparameter_tuner import AdvancedHyperparameterTuner
from .advanced_experiment_tracker import AdvancedExperimentTracker
from ..model.advanced_architectures import (TransformerBlock, ResidualBlock,
                                          LSTMWithAttention, DenseNet, UNet, GAN)

class ModelTrainer(QWidget):
    """Widget for training models with hyperparameter tuning and experiment tracking."""
    
    training_started = pyqtSignal()
    training_finished = pyqtSignal()
    training_progress = pyqtSignal(dict)  # Epoch metrics
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_state()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model Architecture:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "Transformer",
            "ResNet",
            "LSTM with Attention",
            "DenseNet",
            "U-Net",
            "GAN"
        ])
        model_layout.addWidget(self.model_combo)
        
        # Tabs for different components
        tabs = QTabWidget()
        
        # Hyperparameter tuning tab
        self.tuner = AdvancedHyperparameterTuner()
        tabs.addTab(self.tuner, "Hyperparameter Tuning")
        
        # Experiment tracking tab
        self.tracker = AdvancedExperimentTracker()
        tabs.addTab(self.tracker, "Experiment Tracking")
        
        # Progress section
        progress_layout = QVBoxLayout()
        self.epoch_progress = QProgressBar()
        self.batch_progress = QProgressBar()
        progress_layout.addWidget(QLabel("Epoch Progress:"))
        progress_layout.addWidget(self.epoch_progress)
        progress_layout.addWidget(QLabel("Batch Progress:"))
        progress_layout.addWidget(self.batch_progress)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        self.train_btn = QPushButton("Train Model")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        
        self.train_btn.clicked.connect(self._start_training)
        self.stop_btn.clicked.connect(self._stop_training)
        
        buttons_layout.addWidget(self.train_btn)
        buttons_layout.addWidget(self.stop_btn)
        
        # Add all layouts
        layout.addLayout(model_layout)
        layout.addWidget(tabs)
        layout.addLayout(progress_layout)
        layout.addLayout(buttons_layout)
        
        # Connect signals
        self.tuner.tuning_started.connect(self._on_tuning_started)
        self.tuner.tuning_finished.connect(self._on_tuning_finished)
        self.tuner.tuning_progress.connect(self._on_tuning_progress)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.model = None
        self.optimizer = None
        self.criterion = None
        self.train_loader = None
        self.val_loader = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._stop_requested = False
        
    def _create_model(self, params: Dict[str, Any]) -> nn.Module:
        """Create model based on selected architecture and parameters."""
        model_type = self.model_combo.currentText()
        
        if model_type == "Transformer":
            return TransformerBlock(
                embed_dim=512,
                num_heads=8,
                ff_dim=2048,
                dropout=params['dropout_rate']
            )
        elif model_type == "ResNet":
            layers = []
            in_channels = 3
            for _ in range(4):  # 4 residual blocks
                layers.append(ResidualBlock(in_channels, 64))
                in_channels = 64
            return nn.Sequential(*layers)
        elif model_type == "LSTM with Attention":
            return LSTMWithAttention(
                input_size=512,
                hidden_size=256,
                num_layers=2,
                dropout=params['dropout_rate']
            )
        elif model_type == "DenseNet":
            return DenseNet(
                growth_rate=32,
                num_layers=[6, 12, 24, 16],
                num_classes=10
            )
        elif model_type == "U-Net":
            return UNet(
                in_channels=3,
                out_channels=1
            )
        else:  # GAN
            return GAN(
                latent_dim=100,
                channels=3
            )
            
    def _train_epoch(self, epoch: int, params: Dict[str, Any]) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for batch_idx, (data, target) in enumerate(self.train_loader):
            if self._stop_requested:
                break
                
            data, target = data.to(self.device), target.to(self.device)
            
            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.criterion(output, target)
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            
            # Update batch progress
            progress = (batch_idx + 1) / len(self.train_loader) * 100
            self.batch_progress.setValue(int(progress))
            
        avg_loss = total_loss / len(self.train_loader)
        return {
            'epoch': epoch,
            'train_loss': avg_loss,
            'learning_rate': params['learning_rate']
        }
        
    def _validate(self) -> Dict[str, float]:
        """Validate the model."""
        self.model.eval()
        val_loss = 0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, target in self.val_loader:
                if self._stop_requested:
                    break
                    
                data, target = data.to(self.device), target.to(self.device)
                output = self.model(data)
                val_loss += self.criterion(output, target).item()
                
                _, predicted = output.max(1)
                total += target.size(0)
                correct += predicted.eq(target).sum().item()
                
        avg_val_loss = val_loss / len(self.val_loader)
        accuracy = 100. * correct / total
        
        return {
            'val_loss': avg_val_loss,
            'val_accuracy': accuracy
        }
        
    def _objective(self, trial):
        """Objective function for hyperparameter optimization."""
        params = {
            'learning_rate': trial.suggest_float(
                'learning_rate',
                self.tuner.lr_min.value(),
                self.tuner.lr_max.value(),
                log=True
            ),
            'batch_size': trial.suggest_int(
                'batch_size',
                self.tuner.batch_min.value(),
                self.tuner.batch_max.value(),
                step=8
            ),
            'dropout_rate': trial.suggest_float(
                'dropout_rate',
                self.tuner.dropout_min.value(),
                self.tuner.dropout_max.value()
            )
        }
        
        # Create model and optimizer
        self.model = self._create_model(params).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=params['learning_rate'])
        self.criterion = nn.CrossEntropyLoss()
        
        # Train for a few epochs
        n_epochs = 5
        best_val_loss = float('inf')
        
        for epoch in range(n_epochs):
            if self._stop_requested:
                break
                
            train_metrics = self._train_epoch(epoch, params)
            val_metrics = self._validate()
            
            # Update experiment tracker
            metrics = {**train_metrics, **val_metrics}
            self.tracker.add_experiment({
                'name': f"Trial_{trial.number}_Epoch_{epoch}",
                'parameters': params,
                'metrics': metrics,
                'timestamp': datetime.now().isoformat(),
                'model_type': self.model_combo.currentText()
            })
            
            # Report value for hyperparameter optimization
            if val_metrics['val_loss'] < best_val_loss:
                best_val_loss = val_metrics['val_loss']
                
        return best_val_loss
        
    def _start_training(self):
        """Start model training with hyperparameter tuning."""
        try:
            self.train_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self._stop_requested = False
            
            # Connect the objective function to the tuner
            self.tuner._objective = self._objective
            
            # Start hyperparameter tuning
            self.tuner._start_tuning()
            
        except Exception as e:
            self.logger.error(f"Error starting training: {str(e)}")
        finally:
            self.train_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
    def _stop_training(self):
        """Stop training."""
        self._stop_requested = True
        self.tuner._stop_tuning()
        
    def _on_tuning_started(self):
        """Handle tuning started signal."""
        self.training_started.emit()
        
    def _on_tuning_finished(self, best_params: Dict):
        """Handle tuning finished signal."""
        try:
            # Create final model with best parameters
            self.model = self._create_model(best_params).to(self.device)
            
            # Add final experiment
            self.tracker.add_experiment({
                'name': "Final_Model",
                'parameters': best_params,
                'metrics': self._validate(),
                'timestamp': datetime.now().isoformat(),
                'model_type': self.model_combo.currentText(),
                'is_final': True
            })
            
            self.training_finished.emit()
            
        except Exception as e:
            self.logger.error(f"Error in tuning finished handler: {str(e)}")
            
    def _on_tuning_progress(self, progress: Dict):
        """Handle tuning progress signal."""
        self.training_progress.emit(progress)
        self.epoch_progress.setValue(
            int(progress['trial'] / progress['total_trials'] * 100)
        )
        
    def set_data(self, train_loader: DataLoader, val_loader: DataLoader):
        """Set the data loaders."""
        self.train_loader = train_loader
        self.val_loader = val_loader
