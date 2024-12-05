import pytest
from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRect, QPoint, QTimer
from PyQt6.QtGui import QPaintEvent, QRegion
from src.utils.ui_optimizer import RenderOptimizer, CompositionOptimizer, RenderMetrics
import time

@pytest.fixture
def app():
    """Create QApplication instance"""
    return QApplication([])

@pytest.fixture
def widget(app):
    """Create a test widget"""
    widget = QWidget()
    widget.resize(100, 100)
    return widget

@pytest.fixture
def render_optimizer():
    """Create RenderOptimizer instance"""
    return RenderOptimizer()

@pytest.fixture
def composition_optimizer():
    """Create CompositionOptimizer instance"""
    return CompositionOptimizer()

def test_render_metrics_creation():
    """Test RenderMetrics creation and attributes"""
    metrics = RenderMetrics(
        paint_time=1.0,
        frame_count=10,
        last_paint=time.time(),
        visible_area=0.5,
        complexity=100
    )
    assert metrics.paint_time == 1.0
    assert metrics.frame_count == 10
    assert metrics.visible_area == 0.5
    assert metrics.complexity == 100

def test_widget_registration(render_optimizer, widget):
    """Test widget registration in RenderOptimizer"""
    render_optimizer.register_widget(widget)
    assert widget in render_optimizer._metrics
    metrics = render_optimizer._metrics[widget]
    assert isinstance(metrics, RenderMetrics)
    assert metrics.frame_count == 0
    assert 0 <= metrics.visible_area <= 1.0

def test_update_request(render_optimizer, widget):
    """Test update request handling"""
    render_optimizer.register_widget(widget)
    render_optimizer._throttled_widgets.add(widget)
    
    # Test region update
    region = QRect(0, 0, 50, 50)
    render_optimizer.request_update(widget, region)
    assert len(render_optimizer._update_regions[widget]) == 1
    assert render_optimizer._batch_timer.isActive()

def test_batch_updates(render_optimizer, widget):
    """Test batch update processing"""
    render_optimizer.register_widget(widget)
    render_optimizer._throttled_widgets.add(widget)
    
    # Add multiple regions
    regions = [QRect(0, 0, 50, 50), QRect(25, 25, 50, 50)]
    for region in regions:
        render_optimizer.request_update(widget, region)
    
    # Process updates
    render_optimizer._process_batched_updates()
    assert not render_optimizer._update_regions
    assert not render_optimizer._batch_timer.isActive()

def test_visible_area_calculation(render_optimizer, widget):
    """Test visible area calculation"""
    render_optimizer.register_widget(widget)
    
    # Fully visible
    widget.show()
    area = render_optimizer._calculate_visible_area(widget)
    assert area == 1.0
    
    # Hidden
    widget.hide()
    area = render_optimizer._calculate_visible_area(widget)
    assert area == 0.0

def test_complexity_estimation(render_optimizer, widget):
    """Test rendering complexity estimation"""
    # Add child widgets to increase complexity
    layout = QVBoxLayout(widget)
    for i in range(3):
        layout.addWidget(QLabel(f"Label {i}"))
    
    complexity = render_optimizer._estimate_complexity(widget)
    assert complexity > 0
    
    # Test with translucent background
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    translucent_complexity = render_optimizer._estimate_complexity(widget)
    assert translucent_complexity > complexity

def test_throttling(render_optimizer, widget):
    """Test throttling application"""
    render_optimizer.register_widget(widget)
    assert widget not in render_optimizer._throttled_widgets
    
    render_optimizer._apply_throttling(widget)
    assert widget in render_optimizer._throttled_widgets

def test_complexity_reduction(render_optimizer, widget):
    """Test complexity reduction"""
    render_optimizer.register_widget(widget)
    render_optimizer._reduce_complexity(widget)
    
    assert widget.property("no-animations") is True
    assert widget.property("simplified-style") is True

def test_visibility_optimization(render_optimizer, widget):
    """Test visibility optimization"""
    render_optimizer.register_widget(widget)
    widget.show()
    
    # Test with visible widget
    render_optimizer._optimize_visibility(widget)
    assert widget.mask() is not None
    
    # Test with throttled widget
    render_optimizer._throttled_widgets.add(widget)
    render_optimizer._optimize_visibility(widget)
    assert render_optimizer._batch_timer.interval() == 32

def test_composition_optimization(composition_optimizer, widget):
    """Test composition optimization"""
    composition_optimizer.optimize_layout(widget)
    
    # Test widget attributes
    assert widget.testAttribute(Qt.WidgetAttribute.WA_WState_CachedGeometry)
    assert widget.testAttribute(Qt.WidgetAttribute.WA_UpdatesDisabled)
    assert not widget.testAttribute(Qt.WidgetAttribute.WA_PaintOnScreen)
    assert widget.testAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

def test_paint_metrics(render_optimizer, widget):
    """Test paint metrics collection"""
    render_optimizer.register_widget(widget)
    metrics = render_optimizer._metrics[widget]
    
    # Simulate paint event
    render_optimizer._pre_paint(widget)
    time.sleep(0.01)  # Simulate painting
    render_optimizer._post_paint(widget)
    
    assert metrics.paint_time > 0
    assert metrics.frame_count == 1
    assert metrics.last_paint > 0

def test_widget_optimization(render_optimizer, widget):
    """Test widget optimization"""
    render_optimizer.register_widget(widget)
    metrics = render_optimizer._metrics[widget]
    
    # Simulate slow rendering
    metrics.paint_time = 20  # >16ms
    metrics.complexity = 2000  # >1000
    metrics.visible_area = 0.1  # <20%
    
    render_optimizer.optimize_widget(widget)
    
    assert widget in render_optimizer._throttled_widgets
    assert widget.property("simplified-style") is True
    assert widget.mask() is not None

def test_error_handling(render_optimizer, widget):
    """Test error handling in optimizer"""
    # Test unregistered widget
    render_optimizer.optimize_widget(widget)  # Should not raise error
    
    # Test invalid region
    render_optimizer.register_widget(widget)
    render_optimizer.request_update(widget, QRect(-1, -1, 0, 0))  # Should handle invalid rect

def test_performance_monitoring(render_optimizer, widget, caplog):
    """Test performance monitoring and logging"""
    render_optimizer.register_widget(widget)
    metrics = render_optimizer._metrics[widget]
    
    # Simulate very slow rendering
    render_optimizer._pre_paint(widget)
    time.sleep(0.04)  # >32ms
    render_optimizer._post_paint(widget)
    
    assert any("Slow rendering detected" in record.message 
              for record in caplog.records)
