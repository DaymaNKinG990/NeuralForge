from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QFrame, QSplitter)
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QFont
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
import numpy as np
from .styles.style_manager import StyleManager
from .styles.style_enums import ColorScheme, StyleClass

class TrainingVisualizer(QWidget):
    """Widget for visualizing neural network training progress."""
    
    metric_changed = pyqtSignal(str)
    
    def __init__(self) -> None:
        """Initialize the training visualizer."""
        super().__init__()
        self.training_data: Dict[str, List[float]] = {
            'loss': [], 'accuracy': [], 
            'val_loss': [], 'val_accuracy': []
        }
        self.current_metric = 'loss'
        self.style_manager = StyleManager()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Set up the user interface, including the control panel and the splitter for the training progress and statistics views."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Control panel
        control_panel = QFrame()
        control_panel.setStyleSheet(f"""
            QFrame {{
                background: {ColorScheme.ML_BACKGROUND.value};
                border-bottom: 1px solid {ColorScheme.ML_BORDER.value};
            }}
        """)
        control_layout = QHBoxLayout(control_panel)
        
        # Metric selector
        metric_label = QLabel("Metric:")
        metric_label.setStyleSheet(f"color: {ColorScheme.FOREGROUND.value};")
        self.metric_combo = QComboBox()
        self.metric_combo.addItems(["Loss", "Accuracy"])
        self.metric_combo.currentTextChanged.connect(self._on_metric_changed)
        self.metric_combo.setStyleSheet(f"""
            QComboBox {{
                background: {ColorScheme.ML_BACKGROUND.value};
                color: {ColorScheme.FOREGROUND.value};
                border: 1px solid {ColorScheme.ML_BORDER.value};
                padding: 5px;
                border-radius: 3px;
                min-width: 100px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: {ColorScheme.ML_BACKGROUND.value};
                color: {ColorScheme.FOREGROUND.value};
                selection-background-color: {ColorScheme.ML_HEADER.value};
            }}
        """)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ColorScheme.ML_HEADER.value};
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background: {ColorScheme.ML_HEADER_HOVER.value};
            }}
            QPushButton:pressed {{
                background: {ColorScheme.ML_HEADER_PRESSED.value};
            }}
        """)
        clear_btn.clicked.connect(self.clear_data)
        
        control_layout.addWidget(metric_label)
        control_layout.addWidget(self.metric_combo)
        control_layout.addStretch()
        control_layout.addWidget(clear_btn)
        
        # Create splitter for graphs
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {ColorScheme.ML_BACKGROUND.value};
                height: 2px;
            }}
        """)
        
        # Training progress view
        self.progress_view = TrainingProgressView()
        
        # Statistics view
        self.stats_view = TrainingStatsView()
        
        splitter.addWidget(self.progress_view)
        splitter.addWidget(self.stats_view)
        
        layout.addWidget(control_panel)
        layout.addWidget(splitter)
        
        # Apply theme styles
        self.setStyleSheet(f"""
            QWidget {{
                background: {ColorScheme.ML_BACKGROUND.value};
                border: 1px solid {ColorScheme.ML_BORDER.value};
            }}
        """)
        
    def update_data(self, epoch_data: Dict[str, float]) -> None:
        """Update the training visualization with new epoch data, including the training and validation metrics.
        
        Args:
            epoch_data: Dictionary containing metric values for the current epoch
        """
        for metric, value in epoch_data.items():
            if metric in self.training_data:
                self.training_data[metric].append(value)
                
        self.progress_view.set_data(self.training_data, self.current_metric)
        self.stats_view.set_data(self.training_data, self.current_metric)
        
    def _on_metric_changed(self, metric: str) -> None:
        """Handle metric selection change.
        
        Args:
            metric: New metric selected
        """
        self.current_metric = metric.lower()
        self.progress_view.set_data(self.training_data, self.current_metric)
        self.stats_view.set_data(self.training_data, self.current_metric)
        self.metric_changed.emit(metric)
        
    def clear_data(self) -> None:
        """Clear all training data"""
        for key in self.training_data:
            self.training_data[key] = []
        self.progress_view.set_data(self.training_data, self.current_metric)
        self.stats_view.set_data(self.training_data, self.current_metric)


class TrainingProgressView(QWidget):
    """Widget for visualizing training progress metrics."""
    
    def __init__(self) -> None:
        """Initialize the training progress view."""
        super().__init__()
        self.data: Dict[str, List[float]] = {}
        self.metric: str = 'loss'
        self.style_manager = StyleManager()
        
        # Set dark theme background
        self.setStyleSheet(f"""
            QWidget {{
                background: {ColorScheme.ML_BACKGROUND.value};
            }}
        """)
        
    def set_data(self, data: Dict[str, List[float]], metric: str) -> None:
        """Set the training data and metric to display.
        
        Args:
            data: Dictionary containing training metrics data
            metric: Name of the metric to display
        """
        self.data = data
        self.metric = metric
        self.update()
        
    def paintEvent(self, event) -> None:
        """Paint the training progress visualization.
        
        Args:
            event: Paint event
        """
        if not self.data or not self.data[self.metric]:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate margins and plot area
        left_margin = 60
        right_margin = 20
        top_margin = 20
        bottom_margin = 40
        
        width = self.width() - left_margin - right_margin
        height = self.height() - top_margin - bottom_margin
        
        # Get data for current metric
        train_data = self.data[self.metric]
        val_data = self.data.get(f'val_{self.metric}', [])
        
        if not train_data:
            return
            
        # Calculate value range
        all_values = train_data + val_data
        min_val = min(all_values) if all_values else 0
        max_val = max(all_values) if all_values else 1
        value_range = max_val - min_val or 1
            
        # Draw axes
        painter.setPen(QPen(QColor(ColorScheme.ML_GRAPH_GRID.value), 1))
        
        # Y-axis
        painter.drawLine(left_margin, top_margin,
                        left_margin, height + top_margin)
                        
        # X-axis
        painter.drawLine(left_margin, height + top_margin,
                        width + left_margin, height + top_margin)
                        
        # Draw grid lines and labels
        painter.setPen(QPen(QColor(ColorScheme.ML_GRAPH_GRID.value), 1))
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        
        # Y-axis grid and labels
        num_y_lines = 5
        for i in range(num_y_lines + 1):
            y = top_margin + height * (1 - i / num_y_lines)
            painter.drawLine(left_margin - 5, y, width + left_margin, y)
            
            value = min_val + (value_range * i / num_y_lines)
            label = f"{value:.3f}"
            rect = painter.fontMetrics().boundingRect(label)
            painter.setPen(QPen(QColor(ColorScheme.FOREGROUND.value)))
            painter.drawText(left_margin - rect.width() - 10,
                           y + rect.height() // 2,
                           label)
            painter.setPen(QPen(QColor(ColorScheme.ML_GRAPH_GRID.value)))
            
        # X-axis grid and labels
        num_epochs = len(train_data)
        step = max(1, num_epochs // 10)
        for i in range(0, num_epochs, step):
            x = left_margin + (width * i / (num_epochs - 1))
            painter.drawLine(x, top_margin, x, height + top_margin)
            
            label = str(i)
            rect = painter.fontMetrics().boundingRect(label)
            painter.setPen(QPen(QColor(ColorScheme.FOREGROUND.value)))
            painter.drawText(x - rect.width() // 2,
                           height + top_margin + rect.height() + 5,
                           label)
            painter.setPen(QPen(QColor(ColorScheme.ML_GRAPH_GRID.value)))
            
        # Draw training data line
        if len(train_data) > 1:
            painter.setPen(QPen(QColor(ColorScheme.ML_GRAPH_LINE.value), 2))
            path = QPainterPath()
            
            for i, value in enumerate(train_data):
                x = left_margin + (width * i / (num_epochs - 1))
                y = top_margin + height * (1 - (value - min_val) / value_range)
                
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
                    
            painter.drawPath(path)
            
        # Draw validation data line
        if len(val_data) > 1:
            painter.setPen(QPen(QColor(ColorScheme.PERF_MEMORY_LINE.value), 2))
            path = QPainterPath()
            
            for i, value in enumerate(val_data):
                x = left_margin + (width * i / (num_epochs - 1))
                y = top_margin + height * (1 - (value - min_val) / value_range)
                
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
                    
            painter.drawPath(path)
            
        # Draw legend
        legend_x = left_margin + 10
        legend_y = top_margin + 20
        
        # Training legend
        painter.setPen(QPen(QColor(ColorScheme.ML_GRAPH_LINE.value), 2))
        painter.drawLine(legend_x, legend_y, legend_x + 20, legend_y)
        painter.setPen(QPen(QColor(ColorScheme.FOREGROUND.value)))
        painter.drawText(legend_x + 30, legend_y + 5, "Training")
        
        # Validation legend
        legend_y += 20
        painter.setPen(QPen(QColor(ColorScheme.PERF_MEMORY_LINE.value), 2))
        painter.drawLine(legend_x, legend_y, legend_x + 20, legend_y)
        painter.setPen(QPen(QColor(ColorScheme.FOREGROUND.value)))
        painter.drawText(legend_x + 30, legend_y + 5, "Validation")


class TrainingStatsView(QWidget):
    """Widget for visualizing training statistics."""
    
    def __init__(self) -> None:
        """Initialize the training statistics view."""
        super().__init__()
        self.data: Dict[str, List[float]] = {}
        self.metric: str = 'loss'
        self.style_manager = StyleManager()
        
        # Set dark theme background
        self.setStyleSheet(f"""
            QWidget {{
                background: {ColorScheme.ML_BACKGROUND.value};
            }}
        """)
        
    def set_data(self, data: Dict[str, List[float]], metric: str) -> None:
        """Set the training data and metric to display.
        
        Args:
            data: Dictionary containing training metrics data
            metric: Name of the metric to display
        """
        self.data = data
        self.metric = metric
        self.update()
        
    def paintEvent(self, event) -> None:
        """Paint the training statistics visualization.
        
        Args:
            event: Paint event
        """
        if not self.data or not self.data[self.metric]:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate statistics
        train_data = self.data[self.metric]
        val_data = self.data.get(f'val_{self.metric}', [])
        
        train_stats = {
            'Current': train_data[-1] if train_data else 0,
            'Best': min(train_data) if train_data else 0,
            'Mean': np.mean(train_data) if train_data else 0,
            'Std Dev': np.std(train_data) if train_data else 0
        }
        
        val_stats = {
            'Current': val_data[-1] if val_data else 0,
            'Best': min(val_data) if val_data else 0,
            'Mean': np.mean(val_data) if val_data else 0,
            'Std Dev': np.std(val_data) if val_data else 0
        }
        
        # Draw statistics
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        
        # Calculate column widths
        stat_width = self.width() // 5
        value_width = stat_width * 2
        
        # Draw headers
        y = 30
        painter.setPen(QPen(QColor(ColorScheme.FOREGROUND.value)))
        painter.drawText(20, y, "Statistic")
        painter.drawText(stat_width + 20, y, "Training")
        painter.drawText(stat_width + value_width + 20, y, "Validation")
        
        # Draw separator line
        y += 5
        painter.setPen(QPen(QColor(ColorScheme.ML_GRAPH_GRID.value)))
        painter.drawLine(20, y, self.width() - 20, y)
        
        # Draw statistics rows
        y += 20
        row_height = 25
        
        for stat, train_value in train_stats.items():
            val_value = val_stats[stat]
            
            painter.setPen(QPen(QColor(ColorScheme.FOREGROUND.value)))
            painter.drawText(20, y, stat)
            
            painter.setPen(QPen(QColor(ColorScheme.ML_GRAPH_LINE.value)))
            painter.drawText(stat_width + 20, y, f"{train_value:.6f}")
            
            painter.setPen(QPen(QColor(ColorScheme.PERF_MEMORY_LINE.value)))
            painter.drawText(stat_width + value_width + 20, y, f"{val_value:.6f}")
            
            y += row_height
