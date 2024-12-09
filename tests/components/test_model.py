"""Tests for model components."""
import pytest
from PyQt6.QtWidgets import QApplication
import sys
import torch
import torch.nn as nn
from src.ui.components.model.model_builder import ModelBuilder, LayerConfig
from src.ui.components.model.model_optimizer import ModelOptimizer

@pytest.fixture
def app():
    """Create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def sample_model():
    """Create sample PyTorch model."""
    return nn.Sequential(
        nn.Linear(10, 5),
        nn.ReLU(),
        nn.Linear(5, 1)
    )

class TestLayerConfig:
    """Test LayerConfig class."""
    
    def test_linear_layer_creation(self):
        """Test creating Linear layer."""
        config = LayerConfig("Linear", {"in_features": 10, "out_features": 5})
        layer = config.create_layer()
        assert isinstance(layer, nn.Linear)
        assert layer.in_features == 10
        assert layer.out_features == 5
        
    def test_invalid_layer_creation(self):
        """Test creating invalid layer."""
        config = LayerConfig("Invalid", {})
        with pytest.raises(AttributeError):
            config.create_layer()

class TestModelBuilder:
    """Test ModelBuilder component."""
    
    def test_initialization(self, app):
        """Test component initialization."""
        builder = ModelBuilder()
        assert builder is not None
        assert len(builder.layers) == 0
        
    def test_add_layer(self, app):
        """Test adding layer."""
        builder = ModelBuilder()
        
        # Set Linear layer parameters
        builder.layer_combo.setCurrentText("Linear")
        builder.param_widgets["in_features"].setValue(10)
        builder.param_widgets["out_features"].setValue(5)
        
        # Add layer
        builder._add_layer()
        assert len(builder.layers) == 1
        assert builder.layer_list.count() == 1
        
    def test_create_model(self, app):
        """Test model creation."""
        builder = ModelBuilder()
        
        # Add Linear layer
        builder.layer_combo.setCurrentText("Linear")
        builder.param_widgets["in_features"].setValue(10)
        builder.param_widgets["out_features"].setValue(5)
        builder._add_layer()
        
        # Add ReLU layer
        builder.layer_combo.setCurrentText("ReLU")
        builder._add_layer()
        
        # Create model
        model_created = False
        def on_model_created(model):
            nonlocal model_created
            assert isinstance(model, nn.Sequential)
            assert len(list(model.children())) == 2
            model_created = True
            
        builder.model_created.connect(on_model_created)
        builder._create_model()
        assert model_created

class TestModelOptimizer:
    """Test ModelOptimizer component."""
    
    def test_initialization(self, app):
        """Test component initialization."""
        optimizer = ModelOptimizer()
        assert optimizer is not None
        assert optimizer.model is None
        
    def test_set_model(self, app, sample_model):
        """Test setting model."""
        optimizer = ModelOptimizer()
        optimizer.set_model(sample_model)
        assert optimizer.model is not None
        assert optimizer.create_btn.isEnabled()
        
    def test_create_optimizer(self, app, sample_model):
        """Test optimizer creation."""
        optimizer = ModelOptimizer()
        optimizer.set_model(sample_model)
        
        # Set Adam optimizer
        optimizer.optimizer_combo.setCurrentText("Adam")
        optimizer.lr_spin.setValue(0.001)
        
        # Create optimizer
        optimizer_created = False
        def on_optimizer_created(opt):
            nonlocal optimizer_created
            assert isinstance(opt, torch.optim.Adam)
            assert opt.defaults["lr"] == 0.001
            optimizer_created = True
            
        optimizer.optimizer_created.connect(on_optimizer_created)
        optimizer._create_optimizer()
        assert optimizer_created
