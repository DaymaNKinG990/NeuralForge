"""Tests for visualization components."""
import pytest
from PyQt6.QtWidgets import QApplication
import sys
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from src.ui.components.visualization.plot_base import PlotBase
from src.ui.components.visualization.distribution_plot import DistributionPlot
from src.ui.components.visualization.model_plot import ModelPlot

@pytest.fixture
def app():
    """Create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return np.random.randn(100, 5)

@pytest.fixture
def sample_model():
    """Create sample PyTorch model."""
    return nn.Sequential(
        nn.Linear(10, 5),
        nn.ReLU(),
        nn.Linear(5, 1)
    )

class TestPlotBase:
    """Test PlotBase component."""
    
    def test_initialization(self, app):
        """Test component initialization."""
        plot = PlotBase()
        assert plot is not None
        assert plot.canvas is not None
        assert plot.figure is not None
        
    def test_clear_plot(self, app):
        """Test plot clearing."""
        plot = PlotBase()
        ax = plot.figure.add_subplot(111)
        ax.plot([1, 2, 3], [1, 2, 3])
        plot.clear_plot()
        assert len(plot.figure.axes) == 0
        
    def test_set_title(self, app):
        """Test setting plot title."""
        plot = PlotBase()
        title = "Test Plot"
        plot.set_title(title)
        assert plot.figure._suptitle.get_text() == title

class TestDistributionPlot:
    """Test DistributionPlot component."""
    
    def test_initialization(self, app):
        """Test component initialization."""
        plot = DistributionPlot()
        assert plot is not None
        assert isinstance(plot, PlotBase)
        
    def test_plot_distribution(self, app, sample_data):
        """Test distribution plotting."""
        plot = DistributionPlot()
        plot.plot_distribution(sample_data[:, 0], "Feature 1")
        assert len(plot.figure.axes) > 0
        
    def test_plot_correlation_matrix(self, app, sample_data):
        """Test correlation matrix plotting."""
        plot = DistributionPlot()
        df = pd.DataFrame(sample_data)
        plot.plot_correlation_matrix(df)
        assert len(plot.figure.axes) > 0

class TestModelPlot:
    """Test ModelPlot component."""
    
    def test_initialization(self, app):
        """Test component initialization."""
        plot = ModelPlot()
        assert plot is not None
        assert isinstance(plot, PlotBase)
        
    def test_plot_layer_weights(self, app, sample_model):
        """Test layer weights plotting."""
        plot = ModelPlot()
        plot.plot_layer_weights(sample_model)
        assert len(plot.figure.axes) > 0
        
    def test_plot_loss_curve(self, app):
        """Test loss curve plotting."""
        plot = ModelPlot()
        losses = [0.5, 0.4, 0.3, 0.2, 0.1]
        val_losses = [0.6, 0.5, 0.4, 0.3, 0.2]
        plot.plot_loss_curve(losses, val_losses)
        assert len(plot.figure.axes) > 0
        ax = plot.figure.axes[0]
        assert len(ax.lines) == 2  # Training and validation curves
