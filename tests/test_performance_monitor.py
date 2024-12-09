"""Tests for the performance monitoring system with lazy loading and caching."""
import pytest
from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from unittest.mock import patch
from pytestqt.qtbot import QtBot

from src.ui.performance_monitor import (
    MetricType,
    MetricConfig,
    MetricsGraph,
    MetricsPanel,
    get_performance_monitor
)
from ..src.utils.lazy_loading import LoadPriority, component_loader
from ..src.utils.caching import cache

@pytest.fixture
def app(qtbot: QtBot):
    """Create a Qt application."""
    return QApplication.instance() or QApplication([])

@pytest.fixture
def metric_config():
    """Create a test metric configuration."""
    return MetricConfig(
        name="test_metric",
        type=MetricType.CPU,
        unit="%",
        color="#1f77b4",
        priority=LoadPriority.HIGH,
        update_interval=1000,
        history_length=100,
        alert_threshold=90.0,
        warning_threshold=75.0
    )

@pytest.fixture
def metrics_graph(qtbot: QtBot, app, metric_config):
    """Create a metrics graph widget."""
    graph = MetricsGraph(metric_config)
    qtbot.addWidget(graph)
    return graph

@pytest.fixture
def metrics_panel(qtbot: QtBot, app):
    """Create a metrics panel widget."""
    panel = get_performance_monitor()
    qtbot.addWidget(panel)
    return panel

def test_metric_type_enum():
    """Test MetricType enum values."""
    assert MetricType.CPU.value == "CPU Usage"
    assert MetricType.MEMORY.value == "Memory Usage"
    assert MetricType.DISK.value == "Disk Usage"
    assert MetricType.CACHE.value == "Cache Hit Rate"
    assert MetricType.UI_FRAME.value == "UI Frame Time"
    assert MetricType.UI_FPS.value == "UI FPS"
    assert MetricType.COMPONENTS.value == "Component Count"
    assert MetricType.NETWORK.value == "Network Usage"

def test_metrics_graph_creation(metrics_graph, metric_config):
    """Test metrics graph creation and initialization."""
    assert metrics_graph is not None
    assert isinstance(metrics_graph, MetricsGraph)
    assert metrics_graph.config == metric_config
    
    # Check component registration
    component = component_loader.get_component(f"metrics_graph_{metric_config.name}")
    assert component is not None
    assert component == metrics_graph
    
    # Check plot setup
    assert metrics_graph.plot_line is not None
    assert len(metrics_graph.times) == metric_config.history_length
    assert len(metrics_graph.values) == metric_config.history_length

def test_metrics_graph_update(metrics_graph):
    """Test updating metrics graph data."""
    test_value = 50.0
    metrics_graph.update_data(test_value)
    
    # Check data arrays
    assert metrics_graph.values[-1] == test_value
    
    # Check cache
    cached_value = cache.get(f"metric_{metrics_graph.config.name}_latest")
    assert cached_value == test_value

def test_metrics_graph_threshold_lines(metric_config):
    """Test threshold lines in metrics graph."""
    graph = MetricsGraph(metric_config)
    
    # Count number of plot items (should be 3: data line + 2 threshold lines)
    plot_items = [item for item in graph.plotItem.items if hasattr(item, 'pen')]
    assert len(plot_items) == 3

def test_metrics_panel_creation(metrics_panel):
    """Test metrics panel creation and initialization."""
    assert metrics_panel is not None
    assert isinstance(metrics_panel, MetricsPanel)
    
    # Check component registration
    component = component_loader.get_component("metrics_panel")
    assert component is not None
    assert component == metrics_panel
    
    # Check UI elements
    assert metrics_panel.metric_selector is not None
    assert metrics_panel.interval_spinner is not None
    assert metrics_panel.history_spinner is not None

def test_metrics_panel_add_metric(metrics_panel, qtbot: QtBot):
    """Test adding a new metric to the panel."""
    initial_graph_count = len(metrics_panel.graphs)
    
    # Select CPU metric and add it
    metrics_panel.metric_selector.setCurrentText(MetricType.CPU.value)
    qtbot.mouseClick(metrics_panel.findChild(QPushButton, ""), Qt.MouseButton.LeftButton)
    
    # Check that graph was added
    assert len(metrics_panel.graphs) == initial_graph_count + 1
    assert len(metrics_panel.timers) == initial_graph_count + 1

def test_metrics_panel_update(metrics_panel, qtbot: QtBot):
    """Test updating metrics in the panel."""
    # Add CPU metric
    metrics_panel.metric_selector.setCurrentText(MetricType.CPU.value)
    qtbot.mouseClick(metrics_panel.findChild(QPushButton, ""), Qt.MouseButton.LeftButton)
    
    # Get graph name
    graph_name = next(iter(metrics_panel.graphs.keys()))
    
    # Update metric
    metrics_panel._update_metric(graph_name)
    
    # Check that value was cached
    cached_value = cache.get(f"metric_value_{MetricType.CPU.value}")
    assert cached_value is not None

def test_metrics_panel_cleanup(metrics_panel, qtbot: QtBot):
    """Test metrics panel cleanup."""
    # Add some metrics
    metrics_panel.metric_selector.setCurrentText(MetricType.CPU.value)
    qtbot.mouseClick(metrics_panel.findChild(QPushButton, ""), Qt.MouseButton.LeftButton)
    
    metrics_panel.metric_selector.setCurrentText(MetricType.MEMORY.value)
    qtbot.mouseClick(metrics_panel.findChild(QPushButton, ""), Qt.MouseButton.LeftButton)
    
    # Cleanup
    metrics_panel.cleanup()
    
    # Check that everything was cleared
    assert len(metrics_panel.graphs) == 0
    assert len(metrics_panel.timers) == 0

def test_singleton_behavior():
    """Test performance monitor singleton behavior."""
    monitor1 = get_performance_monitor()
    monitor2 = get_performance_monitor()
    assert monitor1 is monitor2

def test_alert_thresholds(metrics_panel, qtbot: QtBot):
    """Test alert and warning thresholds."""
    # Add CPU metric
    metrics_panel.metric_selector.setCurrentText(MetricType.CPU.value)
    qtbot.mouseClick(metrics_panel.findChild(QPushButton, ""), Qt.MouseButton.LeftButton)
    
    # Get graph name
    graph_name = next(iter(metrics_panel.graphs.keys()))
    graph = metrics_panel.graphs[graph_name]
    
    # Mock high CPU usage
    with patch('psutil.cpu_percent', return_value=95.0):
        # Connect to signal
        with qtbot.waitSignal(metrics_panel.alert_triggered, timeout=1000):
            metrics_panel._update_metric(graph_name)
        
        # Check that alert was triggered
        assert metrics_panel.alert_triggered.emit.called

def test_metric_caching(metrics_panel, qtbot: QtBot):
    """Test metric value caching."""
    # Add CPU metric
    metrics_panel.metric_selector.setCurrentText(MetricType.CPU.value)
    qtbot.mouseClick(metrics_panel.findChild(QPushButton, ""), Qt.MouseButton.LeftButton)
    
    # Get graph name
    graph_name = next(iter(metrics_panel.graphs.keys()))
    
    # First update - should calculate value
    with patch('psutil.cpu_percent', return_value=50.0) as mock_cpu:
        metrics_panel._update_metric(graph_name)
        assert mock_cpu.call_count == 1
    
    # Second update - should use cached value
    with patch('psutil.cpu_percent', return_value=50.0) as mock_cpu:
        value = metrics_panel._get_metric_value(MetricType.CPU)
        assert mock_cpu.call_count == 0
        assert value == 50.0
