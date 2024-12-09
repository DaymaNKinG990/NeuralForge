"""Real-time performance monitoring and optimization widget."""

from typing import Optional, Dict, List, Tuple, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTabWidget, QProgressBar, 
                             QFrame, QScrollArea, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QPainter, QColor, QPen
import psutil
import pyqtgraph as pg
import numpy as np
import threading
import logging
import time
from dataclasses import dataclass
from enum import Enum
from ..utils.lazy_loading import LoadPriority, component_loader
from ..utils.caching import cache

class MetricType(Enum):
    """Types of performance metrics."""
    CPU = "CPU Usage"
    MEMORY = "Memory Usage"
    DISK = "Disk Usage"
    CACHE = "Cache Hit Rate"
    UI_FRAME = "UI Frame Time"
    UI_FPS = "UI FPS"
    COMPONENTS = "Component Count"
    NETWORK = "Network Usage"

@dataclass
class MetricConfig:
    """Configuration for a performance metric."""
    name: str
    type: MetricType
    unit: str
    color: str
    priority: LoadPriority
    update_interval: int  # milliseconds
    history_length: int  # number of data points
    alert_threshold: Optional[float] = None
    warning_threshold: Optional[float] = None

class MetricsGraph(pg.PlotWidget):
    """Graph widget for displaying performance metrics."""
    
    def __init__(self, config: MetricConfig, parent: Optional[QWidget] = None):
        """Initialize metrics graph.
        
        Args:
            config: Metric configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config
        self._setup_graph()
        self._init_data()
        
        # Register with component loader
        component_loader.register_component(
            f"metrics_graph_{config.name}",
            lambda: self,
            priority=config.priority,
            size_estimate=config.history_length * 8  # 8 bytes per data point
        )
        
    def _setup_graph(self):
        """Setup graph appearance and behavior."""
        self.setBackground('w')
        self.setTitle(self.config.name)
        self.setLabel('left', self.config.type.value, units=self.config.unit)
        self.setLabel('bottom', 'Time', units='s')
        self.showGrid(x=True, y=True)
        
        # Add plot line
        pen = pg.mkPen(color=self.config.color, width=2)
        self.plot_line = self.plot([], [], pen=pen)
        
        # Add threshold lines if configured
        if self.config.alert_threshold is not None:
            alert_pen = pg.mkPen(color='r', width=1, style=Qt.PenStyle.DashLine)
            self.addLine(y=self.config.alert_threshold, pen=alert_pen)
            
        if self.config.warning_threshold is not None:
            warning_pen = pg.mkPen(color='y', width=1, style=Qt.PenStyle.DashLine)
            self.addLine(y=self.config.warning_threshold, pen=warning_pen)
            
    def _init_data(self):
        """Initialize data arrays."""
        self.times = np.zeros(self.config.history_length)
        self.values = np.zeros(self.config.history_length)
        self.start_time = time.time()
        
    def update_data(self, value: float):
        """Update graph with new data point.
        
        Args:
            value: New metric value
        """
        # Roll arrays and add new data
        self.times[:-1] = self.times[1:]
        self.values[:-1] = self.values[1:]
        
        self.times[-1] = time.time() - self.start_time
        self.values[-1] = value
        
        # Update plot
        self.plot_line.setData(self.times, self.values)
        
        # Cache latest value
        cache.set(
            f"metric_{self.config.name}_latest",
            value,
            weak=True,
            priority=self.config.priority
        )
        
    def get_latest_value(self) -> Optional[float]:
        """Get latest metric value.
        
        Returns:
            Latest value or None if no data
        """
        # Try cache first
        value = cache.get(f"metric_{self.config.name}_latest")
        if value is not None:
            return value
            
        # Fall back to array
        return self.values[-1] if len(self.values) > 0 else None

class MetricsPanel(QWidget):
    """Panel for displaying multiple performance metrics."""
    
    # Signals
    alert_triggered = pyqtSignal(str, float)  # metric name, value
    warning_triggered = pyqtSignal(str, float)  # metric name, value
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize metrics panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.graphs: Dict[str, MetricsGraph] = {}
        self.timers: Dict[str, QTimer] = {}
        self._setup_ui()
        
        # Register with component loader
        component_loader.register_component(
            "metrics_panel",
            lambda: self,
            priority=LoadPriority.HIGH,
            size_estimate=1024 * 1024  # 1MB estimate
        )
        
    def _setup_ui(self):
        """Setup panel UI."""
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Metric selector
        self.metric_selector = QComboBox()
        for metric_type in MetricType:
            self.metric_selector.addItem(metric_type.value)
        controls_layout.addWidget(QLabel("Add Metric:"))
        controls_layout.addWidget(self.metric_selector)
        
        # Update interval
        self.interval_spinner = QSpinBox()
        self.interval_spinner.setRange(100, 10000)  # 100ms to 10s
        self.interval_spinner.setValue(1000)
        self.interval_spinner.setSingleStep(100)
        controls_layout.addWidget(QLabel("Update Interval (ms):"))
        controls_layout.addWidget(self.interval_spinner)
        
        # History length
        self.history_spinner = QSpinBox()
        self.history_spinner.setRange(10, 1000)
        self.history_spinner.setValue(100)
        self.history_spinner.setSingleStep(10)
        controls_layout.addWidget(QLabel("History Length:"))
        controls_layout.addWidget(self.history_spinner)
        
        # Add button
        add_button = QPushButton("Add")
        add_button.clicked.connect(self._add_metric)
        controls_layout.addWidget(add_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Graphs container
        self.graphs_layout = QVBoxLayout()
        layout.addLayout(self.graphs_layout)
        
    def _add_metric(self):
        """Add new metric graph."""
        metric_type = MetricType(self.metric_selector.currentText())
        config = MetricConfig(
            name=f"{metric_type.value}_{len(self.graphs)}",
            type=metric_type,
            unit=self._get_unit(metric_type),
            color=self._get_color(len(self.graphs)),
            priority=LoadPriority.MEDIUM,
            update_interval=self.interval_spinner.value(),
            history_length=self.history_spinner.value(),
            alert_threshold=self._get_alert_threshold(metric_type),
            warning_threshold=self._get_warning_threshold(metric_type)
        )
        
        # Create and add graph
        graph = MetricsGraph(config, self)
        self.graphs[config.name] = graph
        self.graphs_layout.addWidget(graph)
        
        # Setup update timer
        timer = QTimer(self)
        timer.timeout.connect(lambda: self._update_metric(config.name))
        timer.start(config.update_interval)
        self.timers[config.name] = timer
        
    def _update_metric(self, name: str):
        """Update metric with new value.
        
        Args:
            name: Metric name
        """
        if name not in self.graphs:
            return
            
        graph = self.graphs[name]
        value = self._get_metric_value(graph.config.type)
        
        # Update graph
        graph.update_data(value)
        
        # Check thresholds
        if (graph.config.alert_threshold is not None and 
            value >= graph.config.alert_threshold):
            self.alert_triggered.emit(name, value)
            
        elif (graph.config.warning_threshold is not None and 
              value >= graph.config.warning_threshold):
            self.warning_triggered.emit(name, value)
            
    def _get_metric_value(self, metric_type: MetricType) -> float:
        """Get current value for metric type.
        
        Args:
            metric_type: Type of metric
            
        Returns:
            Current metric value
        """
        # Try cache first
        cache_key = f"metric_value_{metric_type.value}"
        value = cache.get(cache_key)
        if value is not None:
            return value
            
        # Calculate value
        if metric_type == MetricType.CPU:
            value = psutil.cpu_percent()
        elif metric_type == MetricType.MEMORY:
            value = psutil.virtual_memory().percent
        elif metric_type == MetricType.DISK:
            value = psutil.disk_usage('/').percent
        elif metric_type == MetricType.CACHE:
            # Get cache hit rate from cache manager
            value = cache.get_hit_rate() * 100
        elif metric_type == MetricType.UI_FRAME:
            # Get UI frame time
            value = self._get_ui_frame_time()
        elif metric_type == MetricType.UI_FPS:
            # Calculate FPS from frame time
            frame_time = self._get_ui_frame_time()
            value = 1000 / frame_time if frame_time > 0 else 0
        elif metric_type == MetricType.COMPONENTS:
            # Get number of loaded components
            value = len(component_loader.get_loaded_components())
        elif metric_type == MetricType.NETWORK:
            # Get network usage
            net_io = psutil.net_io_counters()
            value = (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024  # MB
            
        # Cache value
        cache.set(
            cache_key,
            value,
            weak=True,
            priority=LoadPriority.LOW
        )
        
        return value
        
    def _get_ui_frame_time(self) -> float:
        """Get current UI frame time.
        
        Returns:
            Frame time in milliseconds
        """
        # Try cache first
        value = cache.get("ui_frame_time")
        if value is not None:
            return value
            
        # Calculate frame time
        start = time.perf_counter()
        QApplication.processEvents()
        value = (time.perf_counter() - start) * 1000
        
        # Cache value
        cache.set(
            "ui_frame_time",
            value,
            weak=True,
            priority=LoadPriority.LOW
        )
        
        return value
        
    def _get_unit(self, metric_type: MetricType) -> str:
        """Get unit for metric type.
        
        Args:
            metric_type: Type of metric
            
        Returns:
            Unit string
        """
        units = {
            MetricType.CPU: "%",
            MetricType.MEMORY: "%",
            MetricType.DISK: "%",
            MetricType.CACHE: "%",
            MetricType.UI_FRAME: "ms",
            MetricType.UI_FPS: "fps",
            MetricType.COMPONENTS: "",
            MetricType.NETWORK: "MB"
        }
        return units.get(metric_type, "")
        
    def _get_color(self, index: int) -> str:
        """Get color for graph index.
        
        Args:
            index: Graph index
            
        Returns:
            Color string
        """
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', 
                 '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        return colors[index % len(colors)]
        
    def _get_alert_threshold(self, metric_type: MetricType) -> Optional[float]:
        """Get alert threshold for metric type.
        
        Args:
            metric_type: Type of metric
            
        Returns:
            Alert threshold or None
        """
        thresholds = {
            MetricType.CPU: 90.0,
            MetricType.MEMORY: 90.0,
            MetricType.DISK: 95.0,
            MetricType.CACHE: 50.0,
            MetricType.UI_FRAME: 100.0,
            MetricType.UI_FPS: 20.0
        }
        return thresholds.get(metric_type)
        
    def _get_warning_threshold(self, metric_type: MetricType) -> Optional[float]:
        """Get warning threshold for metric type.
        
        Args:
            metric_type: Type of metric
            
        Returns:
            Warning threshold or None
        """
        thresholds = {
            MetricType.CPU: 75.0,
            MetricType.MEMORY: 75.0,
            MetricType.DISK: 80.0,
            MetricType.CACHE: 70.0,
            MetricType.UI_FRAME: 50.0,
            MetricType.UI_FPS: 30.0
        }
        return thresholds.get(metric_type)
        
    def cleanup(self):
        """Clean up resources."""
        # Stop timers
        for timer in self.timers.values():
            timer.stop()
            
        # Clear graphs
        for graph in self.graphs.values():
            graph.clear()
            
        self.graphs.clear()
        self.timers.clear()

# Global instance
_metrics_panel = None

def get_performance_monitor(parent: Optional[QWidget] = None) -> MetricsPanel:
    """Get or create metrics panel instance.
    
    Args:
        parent: Parent widget
        
    Returns:
        MetricsPanel instance
    """
    global _metrics_panel
    if _metrics_panel is None:
        _metrics_panel = MetricsPanel(parent)
    return _metrics_panel

class PerformanceMonitor(QWidget):
    """Main performance monitoring widget."""
    
    # Signals
    interval_changed = pyqtSignal(int)
    history_changed = pyqtSignal(int)
    export_requested = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the performance monitor."""
        super().__init__(parent)
        
        # Register with component loader
        component_loader.register_component(
            "performance_monitor",
            lambda: self,
            priority=LoadPriority.CRITICAL,
            dependencies={"metrics_graph", "metrics_panel"},
            size_estimate=10 * 1024 * 1024  # 10MB estimate
        )
        
        # Initialize metrics storage
        self.current_metrics = {}
        self.metrics_history = []
        
        # Initialize metrics
        self.metrics = {
            'cpu': MetricConfig(
                name='cpu',
                type=MetricType.CPU,
                unit='%',
                color='b',
                priority=LoadPriority.HIGH,
                update_interval=1000,
                history_length=60,
                alert_threshold=90.0,
                warning_threshold=75.0
            ),
            'memory': MetricConfig(
                name='memory',
                type=MetricType.MEMORY,
                unit='%',
                color='r',
                priority=LoadPriority.HIGH,
                update_interval=1000,
                history_length=60,
                alert_threshold=90.0,
                warning_threshold=75.0
            ),
            'disk': MetricConfig(
                name='disk',
                type=MetricType.DISK,
                unit='%',
                color='g',
                priority=LoadPriority.MEDIUM,
                update_interval=5000,
                history_length=30,
                alert_threshold=95.0,
                warning_threshold=80.0
            )
        }
        
        # Setup UI
        self._init_ui()
        
        # Connect to performance tracker
        self.tracker = PerformanceTracker()
        self.tracker.metrics_updated.connect(self.update_metrics)
        
    def _init_ui(self):
        """Initialize the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Overview tab
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        
        # Add metrics panel
        self.metrics_panel = get_performance_monitor()
        overview_layout.addWidget(self.metrics_panel)
        
        # Add controls
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        
        # Update interval control
        interval_label = QLabel("Update Interval (ms):")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(100, 10000)
        self.interval_spinbox.setValue(1000)
        self.interval_spinbox.valueChanged.connect(self.interval_changed)
        
        # History length control
        history_label = QLabel("History Length:")
        self.history_spinbox = QSpinBox()
        self.history_spinbox.setRange(10, 1000)
        self.history_spinbox.setValue(100)
        self.history_spinbox.valueChanged.connect(self.history_changed)
        
        # Export button
        self.export_button = QPushButton("Export Data")
        self.export_button.clicked.connect(self.export_requested)
        
        # Add controls to layout
        controls_layout.addWidget(interval_label)
        controls_layout.addWidget(self.interval_spinbox)
        controls_layout.addWidget(history_label)
        controls_layout.addWidget(self.history_spinbox)
        controls_layout.addWidget(self.export_button)
        controls_layout.addStretch()
        
        overview_layout.addWidget(controls_widget)
        
        # Graphs tab
        graphs_widget = QWidget()
        graphs_layout = QVBoxLayout(graphs_widget)
        
        # Create graphs
        self.cpu_graph = MetricsGraph(self.metrics['cpu'])
        self.memory_graph = MetricsGraph(self.metrics['memory'])
        self.disk_graph = MetricsGraph(self.metrics['disk'])
        
        # Add graphs to layout
        for graph in [self.cpu_graph, self.memory_graph, self.disk_graph]:
            graphs_layout.addWidget(graph)
        
        # Add tabs
        self.tab_widget.addTab(overview_widget, "Overview")
        self.tab_widget.addTab(graphs_widget, "Graphs")
        
        # Add tab widget to main layout
        layout.addWidget(self.tab_widget)
        
        # Initialize metrics displays
        for config in self.metrics.values():
            self.metrics_panel._add_metric()
            
    def update_metrics(self, metrics: Dict):
        """Update displayed metrics."""
        # Store metrics
        self.current_metrics = metrics
        self.metrics_history.append(metrics)
        
        # Trim history if needed
        max_history = self.history_spinbox.value()
        if len(self.metrics_history) > max_history:
            self.metrics_history = self.metrics_history[-max_history:]
        
        # Update panel
        self.metrics_panel._update_metric('cpu')
        self.metrics_panel._update_metric('memory')
        self.metrics_panel._update_metric('disk')
        
        # Update graphs
        self.cpu_graph.update_data(metrics.get('cpu_usage', 0))
        self.memory_graph.update_data(metrics.get('memory_usage', 0))
        self.disk_graph.update_data(metrics.get('disk_usage', 0))
        
    def export_data(self):
        """Export metrics data to CSV."""
        if not self.metrics_history:
            return
        
        # Convert metrics history to DataFrame
        df = pd.DataFrame(self.metrics_history)
        
        # Add timestamp column
        df['timestamp'] = pd.date_range(
            end=pd.Timestamp.now(),
            periods=len(df),
            freq=f"{self.interval_spinbox.value()}ms"
        )
        
        # Save to CSV
        df.to_csv('performance_metrics.csv', index=False)
        
    def set_update_interval(self, interval_ms: int):
        """Set the update interval for metrics collection."""
        self.tracker.set_update_interval(interval_ms)
        for graph in [self.cpu_graph, self.memory_graph, self.disk_graph]:
            graph.update_interval = interval_ms

class PerformanceWidget(QWidget):
    """Enhanced real-time performance monitoring widget."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._style_manager = StyleManager()
        self._metrics_collector = PerformanceMonitor(self)
        self._metrics_history: List[PerformanceMetrics] = []
        self._history_limit = 3600  # Store 1 hour of history by default
        self._init_ui()
        self._setup_metrics_collector()
        self._apply_styles()
        
    def _init_ui(self) -> None:
        """Initialize the enhanced UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        self.setLayout(layout)
        
        # Add control panel
        self._setup_control_panel()
        
        # Create tabs for different metrics
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs)
        
        # Setup all tabs
        self._setup_system_tab()
        self._setup_cache_tab()
        self._setup_ui_tab()
        self._setup_graphs_tab()
        self._setup_analysis_tab()
        
    def _setup_control_panel(self):
        """Setup monitoring control panel"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        control_layout = QHBoxLayout(control_frame)
        
        # Update interval control
        interval_label = QLabel("Update Interval:")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(1)
        self.interval_spin.setSuffix(" sec")
        self.interval_spin.valueChanged.connect(self._on_interval_changed)
        
        # History length control
        history_label = QLabel("History Length:")
        self.history_combo = QComboBox()
        self.history_combo.addItems(["1 Hour", "6 Hours", "24 Hours"])
        self.history_combo.currentTextChanged.connect(self._on_history_changed)
        
        # Export button
        export_btn = QPushButton("Export Data")
        export_btn.clicked.connect(self.export_performance_data)
        
        control_layout.addWidget(interval_label)
        control_layout.addWidget(self.interval_spin)
        control_layout.addWidget(history_label)
        control_layout.addWidget(self.history_combo)
        control_layout.addWidget(export_btn)
        control_layout.addStretch()
        
        self.layout().addWidget(control_frame)
        
    def _setup_analysis_tab(self):
        """Setup performance analysis tab"""
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        
        # Analysis options
        options_frame = QFrame()
        options_layout = QHBoxLayout(options_frame)
        
        self.analysis_combo = QComboBox()
        self.analysis_combo.addItems([
            "System Performance",
            "Cache Efficiency",
            "UI Bottlenecks",
            "Memory Leaks",
            "Component Loading"
        ])
        
        analyze_btn = QPushButton("Run Analysis")
        analyze_btn.clicked.connect(self._run_performance_analysis)
        
        options_layout.addWidget(self.analysis_combo)
        options_layout.addWidget(analyze_btn)
        
        # Analysis results
        self.analysis_results = QLabel()
        self.analysis_results.setWordWrap(True)
        
        # Recommendations
        self.recommendations = QLabel()
        self.recommendations.setWordWrap(True)
        
        analysis_layout.addWidget(options_frame)
        analysis_layout.addWidget(self.analysis_results)
        analysis_layout.addWidget(self.recommendations)
        
        self.tabs.addTab(analysis_tab, "Analysis")
        
    def _setup_metrics_collector(self):
        """Setup metrics collection"""
        self._metrics_collector.interval_changed.connect(self._on_interval_changed)
        self._metrics_collector.history_changed.connect(self._on_history_changed)
        self._metrics_collector.export_requested.connect(self.export_performance_data)
        
    def _on_interval_changed(self, value: int):
        """Handle update interval change"""
        self._metrics_collector.set_update_interval(value * 1000)
        
    def _on_history_changed(self, text: str):
        """Handle history length change"""
        hours = int(text.split()[0])
        self._history_limit = hours * 3600
        
        # Trim existing history if needed
        while len(self._metrics_history) > self._history_limit:
            self._metrics_history.pop(0)
            
    def export_performance_data(self):
        """Export performance data to file"""
        try:
            import pandas as pd
            from datetime import datetime
            
            # Convert metrics to DataFrame
            data = []
            for m in self._metrics_history:
                data.append({
                    'timestamp': datetime.fromtimestamp(m.update_timestamp),
                    'cpu_usage': m.cpu_usage,
                    'memory_usage': m.memory_usage,
                    'disk_usage': m.disk_usage,
                    'cache_hit_rate': m.cache_hit_rate,
                    'ui_frame_time': m.ui_frame_time,
                    'ui_fps': m.ui_fps,
                    'component_count': m.component_count
                })
                
            df = pd.DataFrame(data)
            
            # Save to file
            filename = f"performance_data_{int(time.time())}.csv"
            df.to_csv(filename, index=False)
            self.logger.info(f"Exported performance data to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            
    def _setup_system_tab(self):
        """Setup system resources monitoring tab"""
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        system_layout.setContentsMargins(4, 4, 4, 4)
        system_layout.setSpacing(8)
        
        # CPU section
        cpu_frame = QFrame()
        cpu_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        cpu_layout = QVBoxLayout(cpu_frame)
        
        self.cpu_label = QLabel("CPU Usage")
        self.cpu_label.setObjectName("statsLabel")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setObjectName("cpuBar")
        self.cpu_bar.setTextVisible(True)
        self.cpu_details = QLabel()
        
        cpu_layout.addWidget(self.cpu_label)
        cpu_layout.addWidget(self.cpu_bar)
        cpu_layout.addWidget(self.cpu_details)
        
        # Memory section
        memory_frame = QFrame()
        memory_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        memory_layout = QVBoxLayout(memory_frame)
        
        self.memory_label = QLabel("Memory Usage")
        self.memory_label.setObjectName("statsLabel")
        self.memory_bar = QProgressBar()
        self.memory_bar.setObjectName("memoryBar")
        self.memory_bar.setTextVisible(True)
        self.memory_details = QLabel()
        
        memory_layout.addWidget(self.memory_label)
        memory_layout.addWidget(self.memory_bar)
        memory_layout.addWidget(self.memory_details)
        
        # Disk section
        disk_frame = QFrame()
        disk_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        disk_layout = QVBoxLayout(disk_frame)
        
        self.disk_label = QLabel("Disk Usage")
        self.disk_label.setObjectName("statsLabel")
        self.disk_bar = QProgressBar()
        self.disk_bar.setObjectName("diskBar")
        self.disk_bar.setTextVisible(True)
        self.disk_details = QLabel()
        
        disk_layout.addWidget(self.disk_label)
        disk_layout.addWidget(self.disk_bar)
        disk_layout.addWidget(self.disk_details)
        
        # Add all sections to system tab
        system_layout.addWidget(cpu_frame)
        system_layout.addWidget(memory_frame)
        system_layout.addWidget(disk_frame)
        system_layout.addStretch()
        
        self.tabs.addTab(system_tab, "System")
        
    def _setup_cache_tab(self):
        """Setup cache statistics tab"""
        cache_tab = QWidget()
        cache_layout = QVBoxLayout(cache_tab)
        cache_layout.setContentsMargins(4, 4, 4, 4)
        cache_layout.setSpacing(8)
        
        # Cache statistics frame
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        stats_layout = QVBoxLayout(stats_frame)
        
        self.cache_label = QLabel("Cache Statistics")
        self.cache_label.setObjectName("statsLabel")
        self.cache_stats = QLabel()
        self.cache_stats.setObjectName("statsLabel")
        self.cache_stats.setWordWrap(True)
        
        stats_layout.addWidget(self.cache_label)
        stats_layout.addWidget(self.cache_stats)
        
        # Cache controls frame
        controls_frame = QFrame()
        controls_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        controls_layout = QHBoxLayout(controls_frame)
        
        clear_cache_btn = QPushButton("Clear All Caches")
        clear_cache_btn.clicked.connect(self.clear_caches)
        optimize_cache_btn = QPushButton("Optimize Caches")
        optimize_cache_btn.clicked.connect(self.optimize_caches)
        
        controls_layout.addWidget(clear_cache_btn)
        controls_layout.addWidget(optimize_cache_btn)
        
        # Add frames to cache tab
        cache_layout.addWidget(stats_frame)
        cache_layout.addWidget(controls_frame)
        cache_layout.addStretch()
        
        self.tabs.addTab(cache_tab, "Cache")
        
    def _setup_ui_tab(self):
        """Setup UI performance tab"""
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)
        ui_layout.setContentsMargins(4, 4, 4, 4)
        ui_layout.setSpacing(8)
        
        # UI statistics frame
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        stats_layout = QVBoxLayout(stats_frame)
        
        self.render_stats = QLabel()
        self.render_stats.setWordWrap(True)
        self.composition_stats = QLabel()
        self.composition_stats.setWordWrap(True)
        
        stats_layout.addWidget(self.render_stats)
        stats_layout.addWidget(self.composition_stats)
        
        # UI controls frame
        controls_frame = QFrame()
        controls_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        controls_layout = QHBoxLayout(controls_frame)
        
        optimize_ui_btn = QPushButton("Optimize UI")
        optimize_ui_btn.clicked.connect(self.optimize_ui)
        analyze_ui_btn = QPushButton("Analyze UI")
        analyze_ui_btn.clicked.connect(self.analyze_ui)
        
        controls_layout.addWidget(optimize_ui_btn)
        controls_layout.addWidget(analyze_ui_btn)
        
        # Add frames to UI tab
        ui_layout.addWidget(stats_frame)
        ui_layout.addWidget(controls_frame)
        ui_layout.addStretch()
        
        self.tabs.addTab(ui_tab, "UI Performance")
        
    def _setup_graphs_tab(self):
        """Setup performance graphs tab"""
        graphs_tab = QWidget()
        graphs_layout = QVBoxLayout(graphs_tab)
        graphs_layout.setContentsMargins(4, 4, 4, 4)
        graphs_layout.setSpacing(8)
        
        # Initialize plots
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        
        # CPU usage plot
        self.cpu_plot = pg.PlotWidget(title="CPU Usage Over Time")
        self.cpu_plot.setLabel('left', 'Usage', '%')
        self.cpu_plot.setLabel('bottom', 'Time', 's')
        self.cpu_curve = self.cpu_plot.plot(pen='b')
        self.cpu_data = []
        
        # Memory usage plot
        self.memory_plot = pg.PlotWidget(title="Memory Usage Over Time")
        self.memory_plot.setLabel('left', 'Usage', 'MB')
        self.memory_plot.setLabel('bottom', 'Time', 's')
        self.memory_curve = self.memory_plot.plot(pen='r')
        self.memory_data = []
        
        # Add plots to layout
        graphs_layout.addWidget(self.cpu_plot)
        graphs_layout.addWidget(self.memory_plot)
        
        self.tabs.addTab(graphs_tab, "Graphs")
        
    def _update_performance_graphs(self):
        """Update performance graphs"""
        try:
            # Keep only last 60 seconds of data
            max_points = 60
            
            if len(self.cpu_data) > max_points:
                self.cpu_data = self.cpu_data[-max_points:]
            if len(self.memory_data) > max_points:
                self.memory_data = self.memory_data[-max_points:]
                
            # Update plot data
            x_data = list(range(len(self.cpu_data)))
            self.cpu_curve.setData(x=x_data, y=self.cpu_data)
            self.memory_curve.setData(x=x_data, y=self.memory_data)
            
        except Exception as e:
            self.logger.error(f"Error updating graphs: {str(e)}", exc_info=True)
            
    def _update_analysis(self):
        """Update analysis tab"""
        try:
            # Update analysis results
            self._run_performance_analysis()
            
        except Exception as e:
            self.logger.error(f"Error updating analysis: {str(e)}", exc_info=True)
            
    def clear_caches(self) -> None:
        """Clear all caches."""
        try:
            cache_manager.clear()
            search_cache.clear()
            distributed_cache.clear()
        except Exception as e:
            self.logger.error(f"Error clearing caches: {str(e)}")
            
    def optimize_ui(self) -> None:
        """Run UI optimization."""
        try:
            window = self.window()
            if window:
                render_optimizer.optimize(window)
                composition_optimizer.optimize(window)
        except Exception as e:
            self.logger.error(f"Error optimizing UI: {str(e)}")
            
    def optimize_caches(self):
        """Optimize cache usage"""
        try:
            cache_manager.optimize()
            distributed_cache.optimize()
            search_cache.optimize()
            self.update_cache_stats()
            self.logger.info("Cache optimization completed")
        except Exception as e:
            self.logger.error(f"Error optimizing caches: {str(e)}", exc_info=True)
            
    def analyze_ui(self):
        """Analyze UI performance"""
        try:
            render_stats = render_optimizer.analyze()
            composition_stats = composition_optimizer.analyze()
            self.render_stats.setText(f"Render Analysis:\n{render_stats}")
            self.composition_stats.setText(f"Composition Analysis:\n{composition_stats}")
            self.logger.info("UI analysis completed")
        except Exception as e:
            self.logger.error(f"Error analyzing UI: {str(e)}", exc_info=True)
            
    def _apply_styles(self) -> None:
        """Apply styles to all components."""
        self.setStyleSheet(self._style_manager.get_component_style(StyleClass.DOCK_WIDGET))
        
    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)
        self._metrics_collector.show()
        
    def hideEvent(self, event) -> None:
        """Handle hide event."""
        super().hideEvent(event)
        self._metrics_collector.hide()
