"""Hyperparameter tuning component for ML workspace."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QComboBox, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import pyqtSignal
import logging
from typing import Dict, List, Optional
import optuna
import numpy as np

class HyperparameterTuner(QWidget):
    """Widget for tuning model hyperparameters."""
    
    tuning_started = pyqtSignal()
    tuning_finished = pyqtSignal(dict)  # Best parameters
    tuning_progress = pyqtSignal(dict)  # Current trial results
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_state()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Tuning method selection
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Tuning Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "Random Search",
            "Grid Search",
            "Bayesian Optimization"
        ])
        method_layout.addWidget(self.method_combo)
        
        # Number of trials
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Number of Trials:"))
        self.trials_spin = QSpinBox()
        self.trials_spin.setRange(10, 100)
        self.trials_spin.setValue(20)
        trials_layout.addWidget(self.trials_spin)
        
        # Parameter ranges
        ranges_layout = QVBoxLayout()
        ranges_layout.addWidget(QLabel("Parameter Ranges:"))
        
        # Learning rate range
        lr_layout = QHBoxLayout()
        lr_layout.addWidget(QLabel("Learning Rate:"))
        self.lr_min = QDoubleSpinBox()
        self.lr_max = QDoubleSpinBox()
        self.lr_min.setRange(0.00001, 0.1)
        self.lr_max.setRange(0.00001, 0.1)
        self.lr_min.setValue(0.0001)
        self.lr_max.setValue(0.01)
        self.lr_min.setSingleStep(0.0001)
        self.lr_max.setSingleStep(0.0001)
        lr_layout.addWidget(self.lr_min)
        lr_layout.addWidget(QLabel("to"))
        lr_layout.addWidget(self.lr_max)
        
        # Batch size range
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Batch Size:"))
        self.batch_min = QSpinBox()
        self.batch_max = QSpinBox()
        self.batch_min.setRange(8, 256)
        self.batch_max.setRange(8, 256)
        self.batch_min.setValue(16)
        self.batch_max.setValue(128)
        self.batch_min.setSingleStep(8)
        self.batch_max.setSingleStep(8)
        batch_layout.addWidget(self.batch_min)
        batch_layout.addWidget(QLabel("to"))
        batch_layout.addWidget(self.batch_max)
        
        # Dropout range
        dropout_layout = QHBoxLayout()
        dropout_layout.addWidget(QLabel("Dropout Rate:"))
        self.dropout_min = QDoubleSpinBox()
        self.dropout_max = QDoubleSpinBox()
        self.dropout_min.setRange(0.0, 0.9)
        self.dropout_max.setRange(0.0, 0.9)
        self.dropout_min.setValue(0.1)
        self.dropout_max.setValue(0.5)
        self.dropout_min.setSingleStep(0.1)
        self.dropout_max.setSingleStep(0.1)
        dropout_layout.addWidget(self.dropout_min)
        dropout_layout.addWidget(QLabel("to"))
        dropout_layout.addWidget(self.dropout_max)
        
        ranges_layout.addLayout(lr_layout)
        ranges_layout.addLayout(batch_layout)
        ranges_layout.addLayout(dropout_layout)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Tuning")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        
        self.start_btn.clicked.connect(self._start_tuning)
        self.stop_btn.clicked.connect(self._stop_tuning)
        
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)
        
        # Add all layouts
        layout.addLayout(method_layout)
        layout.addLayout(trials_layout)
        layout.addLayout(ranges_layout)
        layout.addLayout(buttons_layout)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.study = None
        self.best_params = None
        self._stop_requested = False
        
    def _create_study(self):
        """Create Optuna study based on selected method."""
        method = self.method_combo.currentText()
        
        if method == "Random Search":
            sampler = optuna.samplers.RandomSampler()
        elif method == "Grid Search":
            sampler = optuna.samplers.GridSampler({
                'learning_rate': np.linspace(
                    self.lr_min.value(),
                    self.lr_max.value(),
                    5
                ).tolist(),
                'batch_size': np.linspace(
                    self.batch_min.value(),
                    self.batch_max.value(),
                    5,
                    dtype=int
                ).tolist(),
                'dropout_rate': np.linspace(
                    self.dropout_min.value(),
                    self.dropout_max.value(),
                    5
                ).tolist()
            })
        else:  # Bayesian Optimization
            sampler = optuna.samplers.TPESampler()
            
        self.study = optuna.create_study(
            direction="minimize",
            sampler=sampler
        )
        
    def _start_tuning(self):
        """Start hyperparameter tuning."""
        try:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self._stop_requested = False
            
            self._create_study()
            self.tuning_started.emit()
            
            self.study.optimize(
                self._objective,
                n_trials=self.trials_spin.value(),
                callbacks=[self._trial_callback]
            )
            
            if not self._stop_requested:
                self.best_params = self.study.best_params
                self.tuning_finished.emit(self.best_params)
                
        except Exception as e:
            self.logger.error(f"Error in hyperparameter tuning: {str(e)}")
        finally:
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
    def _stop_tuning(self):
        """Stop hyperparameter tuning."""
        self._stop_requested = True
        
    def _objective(self, trial):
        """Objective function for optimization."""
        if self._stop_requested:
            raise optuna.exceptions.TrialPruned()
            
        params = {
            'learning_rate': trial.suggest_float(
                'learning_rate',
                self.lr_min.value(),
                self.lr_max.value(),
                log=True
            ),
            'batch_size': trial.suggest_int(
                'batch_size',
                self.batch_min.value(),
                self.batch_max.value(),
                step=8
            ),
            'dropout_rate': trial.suggest_float(
                'dropout_rate',
                self.dropout_min.value(),
                self.dropout_max.value()
            )
        }
        
        # This should be connected to the model training
        # For now, return a random value
        return np.random.random()
        
    def _trial_callback(self, study: optuna.study.Study, trial: optuna.trial.FrozenTrial):
        """Callback for trial completion."""
        try:
            progress = {
                'trial': trial.number + 1,
                'total_trials': self.trials_spin.value(),
                'best_value': study.best_value,
                'params': trial.params
            }
            self.tuning_progress.emit(progress)
        except Exception as e:
            self.logger.error(f"Error in trial callback: {str(e)}")
            
    def get_best_params(self) -> Optional[Dict]:
        """Get best parameters found during tuning."""
        return self.best_params
        
    def reset(self):
        """Reset tuner state."""
        try:
            self._initialize_state()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
        except Exception as e:
            self.logger.error(f"Error resetting tuner: {str(e)}")
