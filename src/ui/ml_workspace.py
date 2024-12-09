"""Machine Learning Workspace window."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                           QSplitter, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from .styles.theme_manager import ThemeManager
from .styles.adaptive_styles import AdaptiveStyles

# Data processing components
from .components.data_processing.data_preprocessor import DataPreprocessor
from .components.data_processing.data_augmentor import DataAugmentor

# Model components
from .components.model.model_builder import ModelBuilder
from .components.model.model_optimizer import ModelOptimizer

# Visualization components
from .components.visualization.distribution_plot import DistributionPlot
from .components.visualization.model_plot import ModelPlot

# ML components
from .components.ml.data_manager import DataManager
from .components.ml.model_manager import ModelManager
from .components.ml.hyperparameter_tuner import HyperparameterTuner
from .components.ml.data_analyzer import DataAnalyzer
from .components.ml.model_interpreter import ModelInterpreter

# Tracking components
from .components.tracking.experiment_tracker import ExperimentTracker

import logging
import torch
import torch.nn as nn
import pandas as pd
import numpy as np

class MLWorkspace(QWidget):
    """Machine Learning Workspace window."""
    
    # Signals
    model_changed = pyqtSignal(object)  # Emits model instance
    data_loaded = pyqtSignal(object, object)  # Emits data and labels
    training_started = pyqtSignal()
    training_stopped = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._theme_manager = ThemeManager()
        self._setup_theme()
        self._setup_ui()
        self._connect_signals()
        self._initialize_state()
        
    def _setup_theme(self):
        """Setup theme for the workspace."""
        # Apply base styles
        base_style = AdaptiveStyles.get_base_style(self._theme_manager)
        self.setStyleSheet(base_style)
        
    def _setup_ui(self):
        """Setup the UI components."""
        try:
            # Main layout
            layout = QVBoxLayout()
            layout.setContentsMargins(2, 2, 2, 2)
            layout.setSpacing(1)
            
            # Create tab widget for different sections
            self.tab_widget = QTabWidget()
            self.tab_widget.setDocumentMode(True)
            self.tab_widget.setContentsMargins(0, 0, 0, 0)
            
            # Model building tab
            model_tab = QWidget()
            model_layout = QVBoxLayout(model_tab)
            model_layout.setContentsMargins(2, 2, 2, 2)
            model_layout.setSpacing(1)
            
            # Initialize model components
            self.model_manager = ModelManager(parent=self)
            self.model_builder = ModelBuilder(parent=self)
            self.model_optimizer = ModelOptimizer(parent=self)
            self.model_interpreter = ModelInterpreter(parent=self)
            
            # Model management tab widget
            model_tab_widget = QTabWidget()
            model_tab_widget.addTab(self.model_manager, "Model Manager")
            model_tab_widget.addTab(self.model_builder, "Builder")
            model_tab_widget.addTab(self.model_optimizer, "Optimizer")
            model_tab_widget.addTab(self.model_interpreter, "Interpreter")
            model_layout.addWidget(model_tab_widget)
            
            self.tab_widget.addTab(model_tab, "Model")
            
            # Data management tab
            data_tab = QWidget()
            data_layout = QVBoxLayout(data_tab)
            data_layout.setContentsMargins(2, 2, 2, 2)
            data_layout.setSpacing(1)
            
            # Initialize data components
            self.data_manager = DataManager(parent=self)
            self.data_preprocessor = DataPreprocessor(parent=self)
            self.data_augmentor = DataAugmentor(parent=self)
            self.data_analyzer = DataAnalyzer(parent=self)
            
            # Data management tab widget
            data_tab_widget = QTabWidget()
            data_tab_widget.addTab(self.data_manager, "Data Manager")
            data_tab_widget.addTab(self.data_preprocessor, "Preprocessor")
            data_tab_widget.addTab(self.data_augmentor, "Augmentor")
            data_tab_widget.addTab(self.data_analyzer, "Analyzer")
            data_layout.addWidget(data_tab_widget)
            
            self.tab_widget.addTab(data_tab, "Data")
            
            # Visualization tab
            viz_tab = QWidget()
            viz_layout = QVBoxLayout(viz_tab)
            viz_layout.setContentsMargins(2, 2, 2, 2)
            viz_layout.setSpacing(1)
            
            # Initialize visualization components
            self.hyperparameter_tuner = HyperparameterTuner(parent=self)
            self.experiment_tracker = ExperimentTracker(parent=self)
            self.distribution_plot = DistributionPlot(parent=self)
            self.model_plot = ModelPlot(parent=self)
            
            # Training and visualization tab widget
            train_tab = QTabWidget()
            train_tab.addTab(self.hyperparameter_tuner, "Tuning")
            train_tab.addTab(self.experiment_tracker, "Experiments")
            train_tab.addTab(self.distribution_plot, "Distributions")
            train_tab.addTab(self.model_plot, "Model Plot")
            viz_layout.addWidget(train_tab)
            
            self.tab_widget.addTab(viz_tab, "Visualization")
            
            # Add tab widget to main layout
            layout.addWidget(self.tab_widget)
            self.setLayout(layout)
            
            # Set minimum sizes
            self.setMinimumWidth(300)
            self.setMinimumHeight(400)
            
        except Exception as e:
            self.logger.error(f"Error setting up UI: {str(e)}", exc_info=True)
            
    def _initialize_state(self):
        """Initialize internal state."""
        try:
            self.current_data = None
            self.current_labels = None
            self.current_model = None
            self.training_steps = []
            
        except Exception as e:
            self.logger.error(f"Error initializing state: {str(e)}", exc_info=True)
            
    def _on_data_loaded(self, data, labels):
        """Handle data loading event."""
        try:
            self.current_data = data
            self.current_labels = labels
            
            # Update components
            self.data_preprocessor.set_data(data, labels)
            self.data_augmentor.set_data(data, labels)
            
            # Convert data to DataFrame for analysis
            if isinstance(data, (np.ndarray, torch.Tensor)):
                df = pd.DataFrame(data.numpy() if isinstance(data, torch.Tensor) else data)
                if labels is not None:
                    df['target'] = labels.numpy() if isinstance(labels, torch.Tensor) else labels
            else:
                df = pd.DataFrame(data)
                if labels is not None:
                    df['target'] = labels
                    
            self.data_analyzer.set_data(df)
            
            # Emit signal
            self.data_loaded.emit(data, labels)
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}", exc_info=True)
            
    def _on_model_created(self, model):
        """Handle model creation."""
        try:
            self.current_model = model
            
            # Update model components
            self.model_optimizer.set_model(model)
            self.model_interpreter.set_model(model)
            
            # Emit signal
            self.model_changed.emit(model)
            
        except Exception as e:
            self.logger.error(f"Error handling model creation: {str(e)}", exc_info=True)
            
    def _on_training_started(self):
        """Handle training start."""
        try:
            if self.current_model is None or self.current_data is None:
                return
                
            self.training_started.emit()
            
        except Exception as e:
            self.logger.error(f"Error starting training: {str(e)}", exc_info=True)
            
    def _on_training_step(self, metrics):
        """Handle training step."""
        try:
            # Store training step
            self.training_steps.append(metrics)
            
            # Update visualization components
            self.distribution_plot.update_metrics(metrics)
            self.experiment_tracker.log_metrics(metrics)
            
        except Exception as e:
            self.logger.error(f"Error handling training step: {str(e)}", exc_info=True)
            
    def _connect_signals(self):
        """Connect all signals."""
        try:
            # Model signals
            self.model_builder.model_created.connect(self._on_model_created)
            
            # Training signals
            if hasattr(self.model_manager, 'training_started'):
                self.model_manager.training_started.connect(self._on_training_started)
            if hasattr(self.model_manager, 'training_step'):
                self.model_manager.training_step.connect(self._on_training_step)
                
        except Exception as e:
            self.logger.error(f"Error connecting signals: {str(e)}", exc_info=True)
            
    def cleanup(self):
        """Clean up resources."""
        try:
            # Clean up any resources, stop threads, etc.
            pass
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
