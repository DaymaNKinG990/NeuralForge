"""Training chart panel."""
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtCharts import (
    QChart, QChartView, QLineSeries,
    QValueAxis, QLogValueAxis
)
from .data_manager import TrainingDataManager

class ChartPanel(QWidget):
    """Panel for displaying training charts."""
    
    def __init__(self, data_manager: TrainingDataManager, parent=None):
        """Initialize chart panel.
        
        Args:
            data_manager: Training data manager
            parent: Parent widget
        """
        super().__init__(parent)
        self.data_manager = data_manager
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        
        # Chart controls
        controls = QHBoxLayout()
        
        # Scale type
        self.log_scale = QCheckBox("Logarithmic Scale")
        self.log_scale.stateChanged.connect(self.update_chart)
        controls.addWidget(self.log_scale)
        
        # Moving average
        controls.addWidget(QLabel("Moving Average:"))
        self.avg_window = QComboBox()
        self.avg_window.addItems(['None', '5', '10', '20', '50'])
        self.avg_window.currentTextChanged.connect(self.update_chart)
        controls.addWidget(self.avg_window)
        
        # Show range
        controls.addWidget(QLabel("Show Range:"))
        self.show_range = QComboBox()
        self.show_range.addItems(['All', 'Last 100', 'Last 500', 'Last 1000'])
        self.show_range.currentTextChanged.connect(self.update_chart)
        controls.addWidget(self.show_range)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Chart view
        self.chart = QChart()
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(self.chart_view.renderHint())
        layout.addWidget(self.chart_view)
        
        # Initialize axes
        self.x_axis = QValueAxis()
        self.y_axis = QValueAxis()
        self.log_y_axis = QLogValueAxis()
        
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)
        
    def update_chart(self):
        """Update chart display."""
        # Clear current series
        self.chart.removeAllSeries()
        
        # Get data
        data = self.data_manager.get_current_data()
        if not data:
            return
            
        # Apply range filter
        range_text = self.show_range.currentText()
        if range_text != 'All':
            limit = int(range_text.split()[-1])
            data = data[-limit:]
            
        # Create series
        series = QLineSeries()
        series.setName(self.data_manager.current_metric)
        
        # Add data points
        x_values = []
        y_values = []
        for i, point in enumerate(data):
            x = point.get('step', i)
            y = point.get('value', 0)
            x_values.append(x)
            y_values.append(y)
            series.append(x, y)
            
        self.chart.addSeries(series)
        
        # Apply moving average if selected
        avg_text = self.avg_window.currentText()
        if avg_text != 'None':
            window = int(avg_text)
            avg_series = QLineSeries()
            avg_series.setName(f"{window}-point Average")
            
            # Calculate moving average
            for i in range(len(x_values)):
                start = max(0, i - window + 1)
                avg = sum(y_values[start:i+1]) / (i - start + 1)
                avg_series.append(x_values[i], avg)
                
            self.chart.addSeries(avg_series)
            
        # Update axes
        if self.log_scale.isChecked():
            # Remove linear axis
            self.chart.removeAxis(self.y_axis)
            
            # Add logarithmic axis if not already added
            if self.log_y_axis not in self.chart.axes():
                self.chart.addAxis(self.log_y_axis, Qt.AlignmentFlag.AlignLeft)
                
            # Update axis range
            min_y = min(y for y in y_values if y > 0)
            max_y = max(y_values)
            self.log_y_axis.setRange(min_y, max_y)
            
            # Attach series to axes
            series.attachAxis(self.x_axis)
            series.attachAxis(self.log_y_axis)
            if avg_text != 'None':
                avg_series.attachAxis(self.x_axis)
                avg_series.attachAxis(self.log_y_axis)
        else:
            # Remove logarithmic axis
            self.chart.removeAxis(self.log_y_axis)
            
            # Add linear axis if not already added
            if self.y_axis not in self.chart.axes():
                self.chart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)
                
            # Update axis range
            min_y = min(y_values)
            max_y = max(y_values)
            range_y = max_y - min_y
            self.y_axis.setRange(min_y - 0.1 * range_y, max_y + 0.1 * range_y)
            
            # Attach series to axes
            series.attachAxis(self.x_axis)
            series.attachAxis(self.y_axis)
            if avg_text != 'None':
                avg_series.attachAxis(self.x_axis)
                avg_series.attachAxis(self.y_axis)
                
        # Update x-axis
        min_x = min(x_values)
        max_x = max(x_values)
        self.x_axis.setRange(min_x, max_x)
        
    def get_state(self) -> dict:
        """Get panel state.
        
        Returns:
            State dictionary
        """
        return {
            'log_scale': self.log_scale.isChecked(),
            'avg_window': self.avg_window.currentText(),
            'show_range': self.show_range.currentText()
        }
        
    def set_state(self, state: dict):
        """Set panel state.
        
        Args:
            state: State dictionary
        """
        if 'log_scale' in state:
            self.log_scale.setChecked(state['log_scale'])
            
        if 'avg_window' in state:
            index = self.avg_window.findText(state['avg_window'])
            if index >= 0:
                self.avg_window.setCurrentIndex(index)
                
        if 'show_range' in state:
            index = self.show_range.findText(state['show_range'])
            if index >= 0:
                self.show_range.setCurrentIndex(index)
