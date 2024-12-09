"""Advanced hyperparameter tuning component with enhanced features and visualization."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
                           QTableWidget, QTableWidgetItem, QDialog, QCheckBox,
                           QGroupBox, QTabWidget, QTextEdit)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
import logging
from typing import Dict, List, Optional, Any, Tuple
import optuna
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime

class TuningSettingsDialog(QDialog):
    """Dialog for configuring advanced tuning settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Tuning Settings")
        self.setMinimumWidth(500)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Early stopping settings
        early_stop_group = QGroupBox("Early Stopping")
        early_stop_layout = QVBoxLayout()
        
        self.enable_early_stop = QCheckBox("Enable Early Stopping")
        self.patience_spin = QSpinBox()
        self.patience_spin.setRange(1, 50)
        self.patience_spin.setValue(10)
        
        early_stop_layout.addWidget(self.enable_early_stop)
        early_stop_layout.addWidget(QLabel("Patience:"))
        early_stop_layout.addWidget(self.patience_spin)
        early_stop_group.setLayout(early_stop_layout)
        
        # Pruning settings
        pruning_group = QGroupBox("Pruning")
        pruning_layout = QVBoxLayout()
        
        self.enable_pruning = QCheckBox("Enable Pruning")
        self.warmup_steps_spin = QSpinBox()
        self.warmup_steps_spin.setRange(1, 100)
        self.warmup_steps_spin.setValue(5)
        
        pruning_layout.addWidget(self.enable_pruning)
        pruning_layout.addWidget(QLabel("Warmup Steps:"))
        pruning_layout.addWidget(self.warmup_steps_spin)
        pruning_group.setLayout(pruning_layout)
        
        # Parallel execution settings
        parallel_group = QGroupBox("Parallel Execution")
        parallel_layout = QVBoxLayout()
        
        self.enable_parallel = QCheckBox("Enable Parallel Execution")
        self.n_jobs_spin = QSpinBox()
        self.n_jobs_spin.setRange(1, 16)
        self.n_jobs_spin.setValue(4)
        
        parallel_layout.addWidget(self.enable_parallel)
        parallel_layout.addWidget(QLabel("Number of Jobs:"))
        parallel_layout.addWidget(self.n_jobs_spin)
        parallel_group.setLayout(parallel_layout)
        
        # Add all groups
        layout.addWidget(early_stop_group)
        layout.addWidget(pruning_group)
        layout.addWidget(parallel_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(ok_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
    def get_settings(self) -> Dict[str, Any]:
        """Get the current settings."""
        return {
            'early_stopping': {
                'enabled': self.enable_early_stop.isChecked(),
                'patience': self.patience_spin.value()
            },
            'pruning': {
                'enabled': self.enable_pruning.isChecked(),
                'warmup_steps': self.warmup_steps_spin.value()
            },
            'parallel': {
                'enabled': self.enable_parallel.isChecked(),
                'n_jobs': self.n_jobs_spin.value()
            }
        }

class AdvancedHyperparameterTuner(QWidget):
    """Advanced widget for tuning model hyperparameters with enhanced features."""
    
    tuning_started = pyqtSignal()
    tuning_finished = pyqtSignal(dict)  # Best parameters
    tuning_progress = pyqtSignal(dict)  # Current trial results
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_state()
        
    def _setup_ui(self):
        """Setup the enhanced UI components."""
        layout = QVBoxLayout(self)
        
        # Create tabs
        tabs = QTabWidget()
        
        # Basic settings tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # Tuning method selection
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Tuning Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "Random Search",
            "Grid Search",
            "Bayesian Optimization (TPE)",
            "CMA-ES",
            "NSGA-II"
        ])
        method_layout.addWidget(self.method_combo)
        
        # Number of trials
        trials_layout = QHBoxLayout()
        trials_layout.addWidget(QLabel("Number of Trials:"))
        self.trials_spin = QSpinBox()
        self.trials_spin.setRange(10, 1000)
        self.trials_spin.setValue(50)
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
        self.batch_min.setRange(8, 512)
        self.batch_max.setRange(8, 512)
        self.batch_min.setValue(16)
        self.batch_max.setValue(256)
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
        
        # Add layouts to basic tab
        basic_layout.addLayout(method_layout)
        basic_layout.addLayout(trials_layout)
        basic_layout.addLayout(ranges_layout)
        
        # Results tab
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Trial", "Value", "Learning Rate", "Batch Size", "Dropout Rate"
        ])
        results_layout.addWidget(self.results_table)
        
        # Add tabs
        tabs.addTab(basic_tab, "Settings")
        tabs.addTab(results_tab, "Results")
        
        # Advanced settings button
        self.advanced_btn = QPushButton("Advanced Settings")
        self.advanced_btn.clicked.connect(self._show_advanced_settings)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Tuning")
        self.stop_btn = QPushButton("Stop")
        self.export_btn = QPushButton("Export Results")
        self.stop_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        self.start_btn.clicked.connect(self._start_tuning)
        self.stop_btn.clicked.connect(self._stop_tuning)
        self.export_btn.clicked.connect(self._export_results)
        
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addWidget(self.advanced_btn)
        
        # Add all widgets to main layout
        layout.addWidget(tabs)
        layout.addLayout(buttons_layout)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.study = None
        self.best_params = None
        self._stop_requested = False
        self.advanced_settings = {
            'early_stopping': {'enabled': False, 'patience': 10},
            'pruning': {'enabled': False, 'warmup_steps': 5},
            'parallel': {'enabled': False, 'n_jobs': 4}
        }
        self.results_data = []
        
    def _show_advanced_settings(self):
        """Show advanced settings dialog."""
        dialog = TuningSettingsDialog(self)
        if dialog.exec():
            self.advanced_settings = dialog.get_settings()
            
    def _create_study(self):
        """Create Optuna study based on selected method."""
        method = self.method_combo.currentText()
        
        sampler = None
        if method == "Random Search":
            sampler = optuna.samplers.RandomSampler()
        elif method == "Grid Search":
            sampler = optuna.samplers.GridSampler({
                'learning_rate': np.logspace(
                    np.log10(self.lr_min.value()),
                    np.log10(self.lr_max.value()),
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
        elif method == "CMA-ES":
            sampler = optuna.samplers.CmaEsSampler()
        elif method == "NSGA-II":
            sampler = optuna.samplers.NSGAIISampler()
        else:  # Bayesian Optimization (TPE)
            sampler = optuna.samplers.TPESampler()
            
        pruner = optuna.pruners.MedianPruner(
            n_warmup_steps=self.advanced_settings['pruning']['warmup_steps']
        ) if self.advanced_settings['pruning']['enabled'] else None
        
        self.study = optuna.create_study(
            direction="minimize",
            sampler=sampler,
            pruner=pruner
        )
        
    def _start_tuning(self):
        """Start hyperparameter tuning."""
        try:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.export_btn.setEnabled(False)
            self._stop_requested = False
            self.results_data = []
            self.results_table.setRowCount(0)
            
            self._create_study()
            self.tuning_started.emit()
            
            n_jobs = self.advanced_settings['parallel']['n_jobs'] if self.advanced_settings['parallel']['enabled'] else 1
            
            self.study.optimize(
                self._objective,
                n_trials=self.trials_spin.value(),
                callbacks=[self._trial_callback],
                n_jobs=n_jobs
            )
            
            if not self._stop_requested:
                self.best_params = self.study.best_params
                self.tuning_finished.emit(self.best_params)
                self.export_btn.setEnabled(True)
                
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
            # Store results
            result = {
                'trial': trial.number + 1,
                'value': trial.value,
                'params': trial.params
            }
            self.results_data.append(result)
            
            # Update table
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(str(trial.number + 1)))
            self.results_table.setItem(row, 1, QTableWidgetItem(f"{trial.value:.6f}"))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"{trial.params['learning_rate']:.6f}"))
            self.results_table.setItem(row, 3, QTableWidgetItem(str(trial.params['batch_size'])))
            self.results_table.setItem(row, 4, QTableWidgetItem(f"{trial.params['dropout_rate']:.2f}"))
            
            # Emit progress
            progress = {
                'trial': trial.number + 1,
                'total_trials': self.trials_spin.value(),
                'best_value': study.best_value,
                'params': trial.params
            }
            self.tuning_progress.emit(progress)
            
        except Exception as e:
            self.logger.error(f"Error in trial callback: {str(e)}")
            
    def _export_results(self):
        """Export tuning results to CSV and JSON."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export to CSV
            df = pd.DataFrame(self.results_data)
            df.to_csv(f"tuning_results_{timestamp}.csv", index=False)
            
            # Export to JSON with additional metadata
            metadata = {
                'timestamp': timestamp,
                'method': self.method_combo.currentText(),
                'n_trials': self.trials_spin.value(),
                'advanced_settings': self.advanced_settings,
                'parameter_ranges': {
                    'learning_rate': {
                        'min': self.lr_min.value(),
                        'max': self.lr_max.value()
                    },
                    'batch_size': {
                        'min': self.batch_min.value(),
                        'max': self.batch_max.value()
                    },
                    'dropout_rate': {
                        'min': self.dropout_min.value(),
                        'max': self.dropout_max.value()
                    }
                },
                'results': self.results_data,
                'best_params': self.best_params
            }
            
            with open(f"tuning_results_{timestamp}.json", 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error exporting results: {str(e)}")
            
    def get_best_params(self) -> Optional[Dict]:
        """Get best parameters found during tuning."""
        return self.best_params
        
    def reset(self):
        """Reset tuner state."""
        try:
            self._initialize_state()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.results_table.setRowCount(0)
        except Exception as e:
            self.logger.error(f"Error resetting tuner: {str(e)}")
