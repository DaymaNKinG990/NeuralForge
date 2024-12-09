"""Training metrics panel."""
from typing import Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from .data_manager import TrainingDataManager

class MetricsPanel(QWidget):
    """Panel for displaying training metrics."""
    
    def __init__(self, data_manager: TrainingDataManager, parent=None):
        """Initialize metrics panel.
        
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
        
        # Metrics table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Metric", "Current", "Best", "Worst"
        ])
        
        # Set column stretch
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 4):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
        layout.addWidget(self.table)
        
    def update_display(self):
        """Update metrics display."""
        metrics = self.data_manager.get_current_metrics()
        if not metrics:
            self.table.setRowCount(0)
            return
            
        # Update table
        self.table.setRowCount(len(metrics))
        for row, (name, values) in enumerate(metrics.items()):
            # Metric name
            self.table.setItem(
                row, 0,
                QTableWidgetItem(name)
            )
            
            # Current value
            current = values.get('current', 'N/A')
            self.table.setItem(
                row, 1,
                QTableWidgetItem(str(current))
            )
            
            # Best value
            best = values.get('best', 'N/A')
            item = QTableWidgetItem(str(best))
            if current == best:
                item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 2, item)
            
            # Worst value
            worst = values.get('worst', 'N/A')
            item = QTableWidgetItem(str(worst))
            if current == worst:
                item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 3, item)
            
    def get_state(self) -> dict:
        """Get panel state.
        
        Returns:
            State dictionary
        """
        return {
            'column_widths': [
                self.table.columnWidth(i)
                for i in range(self.table.columnCount())
            ]
        }
        
    def set_state(self, state: dict):
        """Set panel state.
        
        Args:
            state: State dictionary
        """
        if 'column_widths' in state:
            for i, width in enumerate(state['column_widths']):
                self.table.setColumnWidth(i, width)
