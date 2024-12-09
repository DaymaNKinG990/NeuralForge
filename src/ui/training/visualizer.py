"""Training visualization widget."""
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QComboBox, QPushButton,
    QLabel, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtCharts import (
    QChart, QChartView, QLineSeries,
    QValueAxis
)
from ..styles.style_manager import StyleManager
from .metrics_panel import MetricsPanel
from .chart_panel import ChartPanel
from .progress_panel import ProgressPanel
from .data_manager import TrainingDataManager

class TrainingVisualizer(QWidget):
    """Widget for visualizing training progress."""
    
    update_requested = pyqtSignal()  # Emits when update is needed
    
    def __init__(self, parent=None):
        """Initialize training visualizer.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.data_manager = TrainingDataManager()
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the visualizer UI."""
        layout = QVBoxLayout(self)
        
        # Control panel
        controls = QHBoxLayout()
        
        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(200)
        controls.addWidget(QLabel("Model:"))
        controls.addWidget(self.model_combo)
        
        # Metric selection
        self.metric_combo = QComboBox()
        self.metric_combo.setMinimumWidth(150)
        controls.addWidget(QLabel("Metric:"))
        controls.addWidget(self.metric_combo)
        
        # Update interval
        self.update_interval = QSpinBox()
        self.update_interval.setRange(1, 60)
        self.update_interval.setValue(5)
        self.update_interval.setSuffix(" sec")
        controls.addWidget(QLabel("Update:"))
        controls.addWidget(self.update_interval)
        
        # Auto update
        self.auto_update = QCheckBox("Auto Update")
        self.auto_update.setChecked(True)
        controls.addWidget(self.auto_update)
        
        # Update button
        self.update_btn = QPushButton("Update Now")
        controls.addWidget(self.update_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Metrics panel
        self.metrics_panel = MetricsPanel(self.data_manager)
        self.tabs.addTab(self.metrics_panel, "Metrics")
        
        # Charts panel
        self.chart_panel = ChartPanel(self.data_manager)
        self.tabs.addTab(self.chart_panel, "Charts")
        
        # Progress panel
        self.progress_panel = ProgressPanel(self.data_manager)
        self.tabs.addTab(self.progress_panel, "Progress")
        
        layout.addWidget(self.tabs)
        
    def connect_signals(self):
        """Connect widget signals."""
        # Control signals
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        self.metric_combo.currentTextChanged.connect(self.on_metric_changed)
        self.update_btn.clicked.connect(self.update_data)
        
        # Data manager signals
        self.data_manager.data_updated.connect(self.on_data_updated)
        
    def set_models(self, models: List[str]):
        """Set available models.
        
        Args:
            models: List of model names
        """
        current = self.model_combo.currentText()
        self.model_combo.clear()
        self.model_combo.addItems(models)
        
        # Restore selection if possible
        index = self.model_combo.findText(current)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
            
    def set_metrics(self, metrics: List[str]):
        """Set available metrics.
        
        Args:
            metrics: List of metric names
        """
        current = self.metric_combo.currentText()
        self.metric_combo.clear()
        self.metric_combo.addItems(metrics)
        
        # Restore selection if possible
        index = self.metric_combo.findText(current)
        if index >= 0:
            self.metric_combo.setCurrentIndex(index)
            
    def on_model_changed(self, model: str):
        """Handle model change.
        
        Args:
            model: Selected model
        """
        if model:
            self.data_manager.set_current_model(model)
            self.update_data()
            
    def on_metric_changed(self, metric: str):
        """Handle metric change.
        
        Args:
            metric: Selected metric
        """
        if metric:
            self.data_manager.set_current_metric(metric)
            self.chart_panel.update_chart()
            
    def update_data(self):
        """Update training data."""
        model = self.model_combo.currentText()
        if model:
            self.update_requested.emit()
            
    def on_data_updated(self):
        """Handle data update."""
        # Update panels
        self.metrics_panel.update_display()
        self.chart_panel.update_chart()
        self.progress_panel.update_progress()
        
    def get_state(self) -> dict:
        """Get visualizer state.
        
        Returns:
            State dictionary
        """
        return {
            'model': self.model_combo.currentText(),
            'metric': self.metric_combo.currentText(),
            'update_interval': self.update_interval.value(),
            'auto_update': self.auto_update.isChecked(),
            'tab_index': self.tabs.currentIndex()
        }
        
    def set_state(self, state: dict):
        """Set visualizer state.
        
        Args:
            state: State dictionary
        """
        if 'model' in state:
            index = self.model_combo.findText(state['model'])
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
                
        if 'metric' in state:
            index = self.metric_combo.findText(state['metric'])
            if index >= 0:
                self.metric_combo.setCurrentIndex(index)
                
        if 'update_interval' in state:
            self.update_interval.setValue(state['update_interval'])
            
        if 'auto_update' in state:
            self.auto_update.setChecked(state['auto_update'])
            
        if 'tab_index' in state:
            self.tabs.setCurrentIndex(state['tab_index'])
