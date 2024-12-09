"""Integration tests for ML workflow."""
import pytest
from PyQt6.QtWidgets import QApplication
import sys
import torch
import numpy as np
import pandas as pd
from src.ui.ml_workspace import MLWorkspace

@pytest.fixture
def app():
    """Create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def workspace(app):
    """Create MLWorkspace instance."""
    return MLWorkspace()

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = torch.randn(100, 10)
    labels = torch.randint(0, 2, (100,))
    return data, labels

def test_data_loading_to_preprocessing(workspace, sample_data):
    """Test data flow from loading to preprocessing."""
    data, labels = sample_data
    
    # Track preprocessing completion
    preprocessing_completed = False
    def on_preprocessing_completed(processed_data, processed_labels):
        nonlocal preprocessing_completed
        assert processed_data is not None
        assert processed_labels is not None
        preprocessing_completed = True
        
    # Connect signals
    workspace.data_preprocessor.preprocessing_completed.connect(
        on_preprocessing_completed
    )
    
    # Load data
    workspace._on_data_loaded(data, labels)
    
    # Trigger preprocessing
    workspace.data_preprocessor._process_data()
    
    assert preprocessing_completed

def test_model_creation_to_optimization(workspace, sample_data):
    """Test model flow from creation to optimization."""
    # Track optimization completion
    optimization_completed = False
    def on_optimizer_created(optimizer):
        nonlocal optimization_completed
        assert optimizer is not None
        optimization_completed = True
        
    # Connect signals
    workspace.model_optimizer.optimizer_created.connect(
        on_optimizer_created
    )
    
    # Create model
    workspace.model_builder.layer_combo.setCurrentText("Linear")
    workspace.model_builder.param_widgets["in_features"].setValue(10)
    workspace.model_builder.param_widgets["out_features"].setValue(5)
    workspace.model_builder._add_layer()
    workspace.model_builder._create_model()
    
    # Configure optimizer
    workspace.model_optimizer.optimizer_combo.setCurrentText("Adam")
    workspace.model_optimizer.lr_spin.setValue(0.001)
    workspace.model_optimizer._create_optimizer()
    
    assert optimization_completed

def test_training_workflow(workspace, sample_data):
    """Test complete training workflow."""
    data, labels = sample_data
    
    # Track training steps
    training_steps = []
    def on_training_step(metrics):
        nonlocal training_steps
        training_steps.append(metrics)
    
    # Connect signals
    workspace.model_manager.training_step.connect(on_training_step)
    
    # Load data
    workspace._on_data_loaded(data, labels)
    
    # Create model
    workspace.model_builder.layer_combo.setCurrentText("Linear")
    workspace.model_builder.param_widgets["in_features"].setValue(data.shape[1])
    workspace.model_builder.param_widgets["out_features"].setValue(32)
    workspace.model_builder._add_layer()
    
    workspace.model_builder.layer_combo.setCurrentText("ReLU")
    workspace.model_builder._add_layer()
    
    workspace.model_builder.layer_combo.setCurrentText("Linear")
    workspace.model_builder.param_widgets["in_features"].setValue(32)
    workspace.model_builder.param_widgets["out_features"].setValue(1)
    workspace.model_builder._add_layer()
    workspace.model_builder._create_model()
    
    # Configure optimizer
    workspace.model_optimizer.optimizer_combo.setCurrentText("Adam")
    workspace.model_optimizer.lr_spin.setValue(0.001)
    workspace.model_optimizer._create_optimizer()
    
    # Start training
    workspace._on_training_started()
    
    # Simulate training steps
    for i in range(5):
        metrics = {
            'train_loss': 1.0 - i * 0.1,
            'val_loss': 1.1 - i * 0.1
        }
        workspace.model_manager.training_step.emit(metrics)
        workspace._on_training_step(metrics)
        
    assert len(training_steps) == 5
    assert training_steps[0]['train_loss'] > training_steps[-1]['train_loss']

def test_analysis_workflow(workspace, sample_data):
    """Test analysis workflow."""
    data, labels = sample_data
    
    # Track analysis updates
    analysis_updated = False
    def on_analysis_updated(analysis_data):
        nonlocal analysis_updated
        assert analysis_data is not None
        analysis_updated = True
        
    # Connect signals
    workspace.data_analyzer.analysis_updated.connect(on_analysis_updated)
    
    # Load data and trigger analysis
    workspace._on_data_loaded(data, labels)
    workspace.data_analyzer.plot_combo.setCurrentText("Distribution Analysis")
    workspace.data_analyzer._update_plot()
    
    assert analysis_updated

def test_interpretation_workflow(workspace, sample_data):
    """Test model interpretation workflow."""
    data, labels = sample_data
    
    # Track interpretation updates
    interpretation_updated = False
    def on_interpretation_updated(interpretation_data):
        nonlocal interpretation_updated
        assert interpretation_data is not None
        assert 'method' in interpretation_data
        assert 'feature_importance' in interpretation_data
        interpretation_updated = True
        
    # Connect signals
    workspace.model_interpreter.interpretation_updated.connect(
        on_interpretation_updated
    )
    
    # Create and set model
    workspace.model_builder.layer_combo.setCurrentText("Linear")
    workspace.model_builder.param_widgets["in_features"].setValue(data.shape[1])
    workspace.model_builder.param_widgets["out_features"].setValue(32)
    workspace.model_builder._add_layer()
    
    workspace.model_builder.layer_combo.setCurrentText("ReLU")
    workspace.model_builder._add_layer()
    
    workspace.model_builder.layer_combo.setCurrentText("Linear")
    workspace.model_builder.param_widgets["in_features"].setValue(32)
    workspace.model_builder.param_widgets["out_features"].setValue(1)
    workspace.model_builder._add_layer()
    
    model = workspace.model_builder._create_model()
    if model is None:
        pytest.fail("Failed to create model")
    model.eval()  # Set model to evaluation mode
    
    # Convert data to float32 for better compatibility
    data = data.float()
    
    # Set data in interpreter
    workspace.model_interpreter.set_data(
        data,
        [f"Feature {i}" for i in range(data.shape[1])]
    )
    workspace.model_interpreter.set_model(model)
    
    # Trigger interpretation
    workspace.model_interpreter.method_combo.setCurrentText("SHAP Values")
    workspace.model_interpreter._update_interpretation()
    
    assert interpretation_updated
