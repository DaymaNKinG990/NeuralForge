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
from .components.ml.experiment_tracker import ExperimentTracker
from .components.ml.data_analyzer import DataAnalyzer
from .components.ml.model_interpreter import ModelInterpreter

import logging
import torch
import torch.nn as nn
import pandas as pd
import numpy as np

class MLWorkspace(QWidget):
    """Machine Learning Workspace window."""
    
    # Signals
    model_changed = pyqtSignal(str)  # Emits model name
    training_started = pyqtSignal()
    training_stopped = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._theme_manager = ThemeManager()
        self._setup_theme()
        self._setup_ui()
        self._connect_signals()
        
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
            
            # Model builder
            self.model_builder = ModelBuilder(parent=self)
            model_layout.addWidget(self.model_builder)
            
            # Model management tab widget
            model_tab_widget = QTabWidget()
            model_tab_widget.addTab(ModelManager(parent=self), "Model Manager")
            model_tab_widget.addTab(ModelBuilder(parent=self), "Builder")
            model_tab_widget.addTab(ModelOptimizer(parent=self), "Optimizer")
            model_tab_widget.addTab(ModelInterpreter(parent=self), "Interpreter")
            model_layout.addWidget(model_tab_widget)
            
            self.tab_widget.addTab(model_tab, "Model")
            
            # Data management tab
            data_tab = QWidget()
            data_layout = QVBoxLayout(data_tab)
            data_layout.setContentsMargins(2, 2, 2, 2)
            data_layout.setSpacing(1)
            
            # Data management tab widget
            data_tab_widget = QTabWidget()
            data_tab_widget.addTab(DataManager(parent=self), "Data Manager")
            data_tab_widget.addTab(DataPreprocessor(parent=self), "Preprocessor")
            data_tab_widget.addTab(DataAugmentor(parent=self), "Augmentor")
            data_tab_widget.addTab(DataAnalyzer(parent=self), "Analyzer")
            data_layout.addWidget(data_tab_widget)
            
            self.tab_widget.addTab(data_tab, "Data")
            
            # Visualization tab
            viz_tab = QWidget()
            viz_layout = QVBoxLayout(viz_tab)
            viz_layout.setContentsMargins(2, 2, 2, 2)
            viz_layout.setSpacing(1)
            
            # Training and visualization tab widget
            train_tab = QTabWidget()
            train_tab.addTab(HyperparameterTuner(parent=self), "Tuning")
            train_tab.addTab(ExperimentTracker(parent=self), "Experiments")
            train_tab.addTab(DistributionPlot(parent=self), "Distributions")
            train_tab.addTab(ModelPlot(parent=self), "Model Plot")
            viz_layout.addWidget(train_tab)
            
            self.tab_widget.addTab(viz_tab, "Visualization")
            
            # Add tab widget to main layout
            layout.addWidget(self.tab_widget)
            
            # Set minimum sizes
            self.setMinimumWidth(300)
            self.setMinimumHeight(400)
            
            # Set the layout
            self.setLayout(layout)
            
        except Exception as e:
            self.logger.error(f"Error initializing ML workspace UI: {str(e)}")
            raise
            
    def _connect_signals(self):
        """Connect all signals."""
        try:
            # Connect model builder signals
            if hasattr(self, 'model_builder'):
                self.model_builder.model_created.connect(self._on_model_created)
                self.model_builder.model_updated.connect(self._on_model_updated)
                
        except Exception as e:
            self.logger.error(f"Error connecting signals: {str(e)}")
            
    def _on_model_created(self, model_name):
        """Handle model creation."""
        self.model_changed.emit(model_name)
        
    def _on_model_updated(self, model_name):
        """Handle model updates."""
        self.model_changed.emit(model_name)
        
    def cleanup(self):
        """Clean up resources."""
        try:
            # Clean up any resources, stop threads, etc.
            pass
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
