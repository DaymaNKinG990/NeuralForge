"""Tests for ML Workspace components."""
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.ui.ml_workspace.workspace import MLWorkspace
from src.ui.ml_workspace.model_config import ModelConfigPanel
from src.ui.ml_workspace.training_control import TrainingControlPanel

@pytest.fixture
def ml_workspace(qtbot):
    """Create ML workspace fixture."""
    workspace = MLWorkspace()
    qtbot.addWidget(workspace)
    return workspace

@pytest.fixture
def model_config(qtbot):
    """Create model configuration panel fixture."""
    config = ModelConfigPanel()
    qtbot.addWidget(config)
    return config

@pytest.fixture
def training_control(qtbot):
    """Create training control panel fixture."""
    control = TrainingControlPanel()
    qtbot.addWidget(control)
    return control

def test_ml_workspace_creation(ml_workspace):
    """Test ML workspace creation."""
    assert ml_workspace is not None
    assert ml_workspace.model_config is not None
    assert ml_workspace.training_control is not None
    assert ml_workspace.metrics_display is not None

def test_model_config_panel(model_config):
    """Test model configuration panel."""
    # Test layer configuration
    model_config.add_layer("Dense", {"units": 64, "activation": "relu"})
    layers = model_config.get_layers()
    assert len(layers) == 1
    assert layers[0]["type"] == "Dense"
    assert layers[0]["config"]["units"] == 64
    
    # Test optimizer configuration
    model_config.set_optimizer("Adam", {"learning_rate": 0.001})
    optimizer = model_config.get_optimizer()
    assert optimizer["type"] == "Adam"
    assert optimizer["config"]["learning_rate"] == 0.001
    
    # Test loss configuration
    model_config.set_loss("categorical_crossentropy")
    assert model_config.get_loss() == "categorical_crossentropy"

def test_training_control_panel(training_control):
    """Test training control panel."""
    # Test training parameters
    training_control.set_epochs(10)
    assert training_control.get_epochs() == 10
    
    training_control.set_batch_size(32)
    assert training_control.get_batch_size() == 32
    
    # Test validation split
    training_control.set_validation_split(0.2)
    assert training_control.get_validation_split() == 0.2

def test_training_state(training_control, qtbot):
    """Test training state management."""
    # Initial state
    assert not training_control.is_training()
    assert training_control.start_button.isEnabled()
    assert not training_control.stop_button.isEnabled()
    
    # Start training
    with qtbot.waitSignal(training_control.training_started):
        qtbot.mouseClick(training_control.start_button, Qt.MouseButton.LeftButton)
    
    assert training_control.is_training()
    assert not training_control.start_button.isEnabled()
    assert training_control.stop_button.isEnabled()
    
    # Stop training
    with qtbot.waitSignal(training_control.training_stopped):
        qtbot.mouseClick(training_control.stop_button, Qt.MouseButton.LeftButton)
    
    assert not training_control.is_training()
    assert training_control.start_button.isEnabled()
    assert not training_control.stop_button.isEnabled()

def test_metrics_display(ml_workspace):
    """Test metrics display functionality."""
    metrics = {
        "loss": 0.5,
        "accuracy": 0.85,
        "val_loss": 0.6,
        "val_accuracy": 0.82
    }
    
    ml_workspace.metrics_display.update_metrics(metrics)
    displayed_metrics = ml_workspace.metrics_display.get_current_metrics()
    
    assert displayed_metrics["loss"] == 0.5
    assert displayed_metrics["accuracy"] == 0.85
    assert displayed_metrics["val_loss"] == 0.6
    assert displayed_metrics["val_accuracy"] == 0.82

def test_model_saving(ml_workspace, tmp_path):
    """Test model saving functionality."""
    # Configure a simple model
    ml_workspace.model_config.add_layer("Dense", {"units": 10, "activation": "softmax"})
    ml_workspace.model_config.set_optimizer("Adam", {"learning_rate": 0.001})
    ml_workspace.model_config.set_loss("categorical_crossentropy")
    
    # Save model configuration
    save_path = tmp_path / "model_config.json"
    ml_workspace.save_model_config(str(save_path))
    assert save_path.exists()
    
    # Load model configuration
    ml_workspace.load_model_config(str(save_path))
    loaded_layers = ml_workspace.model_config.get_layers()
    assert len(loaded_layers) == 1
    assert loaded_layers[0]["type"] == "Dense"

def test_training_callbacks(training_control):
    """Test training callbacks."""
    # Test epoch end callback
    epoch_metrics = {
        "loss": 0.4,
        "accuracy": 0.9
    }
    training_control.on_epoch_end(1, epoch_metrics)
    
    history = training_control.get_training_history()
    assert len(history) == 1
    assert history[0]["epoch"] == 1
    assert history[0]["metrics"] == epoch_metrics

def test_model_validation(model_config):
    """Test model configuration validation."""
    # Test invalid layer configuration
    with pytest.raises(ValueError):
        model_config.add_layer("Dense", {"units": -1})
    
    # Test invalid optimizer configuration
    with pytest.raises(ValueError):
        model_config.set_optimizer("Adam", {"learning_rate": -0.1})
    
    # Test invalid loss function
    with pytest.raises(ValueError):
        model_config.set_loss("invalid_loss")
