"""Experiment tracking component for ML workspace."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import pyqtSignal
import logging
from typing import Dict, List, Optional
import json
import os
from datetime import datetime

class ExperimentTracker(QWidget):
    """Widget for tracking ML experiments."""
    
    experiment_selected = pyqtSignal(dict)  # Emitted when experiment is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_state()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Experiments table
        self.table = QTableWidget(0, 5)  # id, name, model, metrics, date
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Model", "Metrics", "Date"
        ])
        
        # Adjust column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("Load Experiment")
        self.delete_btn = QPushButton("Delete")
        self.export_btn = QPushButton("Export")
        
        self.load_btn.clicked.connect(self._load_experiment)
        self.delete_btn.clicked.connect(self._delete_experiment)
        self.export_btn.clicked.connect(self._export_experiments)
        
        self.load_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.load_btn)
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addWidget(self.export_btn)
        
        # Add components to layout
        layout.addWidget(self.table)
        layout.addLayout(buttons_layout)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.experiments = []
        self.selected_experiment = None
        self._load_experiments()
        
    def _load_experiments(self):
        """Load experiments from storage."""
        try:
            experiments_file = "experiments.json"
            if os.path.exists(experiments_file):
                with open(experiments_file, 'r') as f:
                    self.experiments = json.load(f)
                self._update_table()
                
        except Exception as e:
            self.logger.error(f"Error loading experiments: {str(e)}")
            
    def _save_experiments(self):
        """Save experiments to storage."""
        try:
            with open("experiments.json", 'w') as f:
                json.dump(self.experiments, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving experiments: {str(e)}")
            
    def _update_table(self):
        """Update experiments table."""
        try:
            self.table.setRowCount(0)
            
            for exp in self.experiments:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Add experiment data
                self.table.setItem(row, 0, QTableWidgetItem(str(exp['id'])))
                self.table.setItem(row, 1, QTableWidgetItem(exp['name']))
                self.table.setItem(row, 2, QTableWidgetItem(exp['model']))
                
                # Format metrics
                metrics = exp['metrics']
                metrics_str = ", ".join([f"{k}: {v:.4f}" for k, v in metrics.items()])
                self.table.setItem(row, 3, QTableWidgetItem(metrics_str))
                
                self.table.setItem(row, 4, QTableWidgetItem(exp['date']))
                
        except Exception as e:
            self.logger.error(f"Error updating table: {str(e)}")
            
    def _on_selection_changed(self):
        """Handle experiment selection change."""
        try:
            selected_items = self.table.selectedItems()
            if selected_items:
                row = selected_items[0].row()
                self.selected_experiment = self.experiments[row]
                self.load_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
            else:
                self.selected_experiment = None
                self.load_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                
        except Exception as e:
            self.logger.error(f"Error handling selection change: {str(e)}")
            
    def _load_experiment(self):
        """Load selected experiment."""
        try:
            if self.selected_experiment:
                self.experiment_selected.emit(self.selected_experiment)
                
        except Exception as e:
            self.logger.error(f"Error loading experiment: {str(e)}")
            
    def _delete_experiment(self):
        """Delete selected experiment."""
        try:
            if self.selected_experiment:
                self.experiments.remove(self.selected_experiment)
                self._save_experiments()
                self._update_table()
                
        except Exception as e:
            self.logger.error(f"Error deleting experiment: {str(e)}")
            
    def _export_experiments(self):
        """Export experiments to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"experiments_export_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.experiments, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error exporting experiments: {str(e)}")
            
    def add_experiment(self, experiment: Dict):
        """Add new experiment."""
        try:
            # Generate unique ID
            exp_id = max([exp['id'] for exp in self.experiments], default=0) + 1
            
            # Add timestamp
            experiment['id'] = exp_id
            experiment['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.experiments.append(experiment)
            self._save_experiments()
            self._update_table()
            
        except Exception as e:
            self.logger.error(f"Error adding experiment: {str(e)}")
            
    def get_experiments(self) -> List[Dict]:
        """Get all experiments."""
        return self.experiments
        
    def get_selected_experiment(self) -> Optional[Dict]:
        """Get currently selected experiment."""
        return self.selected_experiment
        
    def reset(self):
        """Reset tracker state."""
        try:
            self._initialize_state()
            self.load_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
        except Exception as e:
            self.logger.error(f"Error resetting tracker: {str(e)}")
