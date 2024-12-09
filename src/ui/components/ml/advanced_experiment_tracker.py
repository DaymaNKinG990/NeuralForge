"""Advanced experiment tracking component with enhanced features."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                           QComboBox, QLineEdit, QDialog, QFormLayout,
                           QTextEdit, QCheckBox, QSpinBox, QTabWidget)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
import logging
from typing import Dict, List, Optional, Any
import json
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import seaborn as sns
from ..visualization.advanced_plots import PerformanceVisualization

class ExperimentComparisonDialog(QDialog):
    """Dialog for comparing multiple experiments."""
    
    def __init__(self, experiments: List[Dict], parent=None):
        super().__init__(parent)
        self.experiments = experiments
        self.performance_viz = PerformanceVisualization()
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the comparison dialog UI."""
        self.setWindowTitle("Compare Experiments")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Tabs for different comparisons
        tabs = QTabWidget()
        
        # Metrics comparison tab
        metrics_widget = QWidget()
        metrics_layout = QVBoxLayout(metrics_widget)
        self.metrics_canvas = FigureCanvasQTAgg(plt.figure(figsize=(8, 6)))
        metrics_layout.addWidget(self.metrics_canvas)
        tabs.addTab(metrics_widget, "Metrics Comparison")
        
        # Parameters comparison tab
        params_widget = QWidget()
        params_layout = QVBoxLayout(params_widget)
        self.params_table = QTableWidget()
        params_layout.addWidget(self.params_table)
        tabs.addTab(params_widget, "Parameters Comparison")
        
        layout.addWidget(tabs)
        
        # Plot comparisons
        self._plot_metrics_comparison()
        self._show_parameters_comparison()
        
    def _plot_metrics_comparison(self):
        """Plot metrics comparison."""
        try:
            # Extract metrics
            data = []
            for exp in self.experiments:
                metrics = exp['metrics']
                metrics['Experiment'] = exp['name']
                data.append(metrics)
                
            df = pd.DataFrame(data)
            
            # Plot
            plt.clf()
            fig = self.metrics_canvas.figure
            ax = fig.add_subplot(111)
            
            # Create heatmap
            metrics_cols = [col for col in df.columns if col != 'Experiment']
            heatmap_data = df[metrics_cols].values
            sns.heatmap(heatmap_data,
                       xticklabels=metrics_cols,
                       yticklabels=df['Experiment'],
                       annot=True, cmap='viridis',
                       ax=ax)
                       
            ax.set_title("Metrics Comparison")
            self.metrics_canvas.draw()
            
        except Exception as e:
            logging.error(f"Error plotting metrics comparison: {str(e)}")
            
    def _show_parameters_comparison(self):
        """Show parameters comparison table."""
        try:
            # Get all unique parameters
            all_params = set()
            for exp in self.experiments:
                all_params.update(exp.get('parameters', {}).keys())
                
            # Setup table
            self.params_table.setRowCount(len(all_params))
            self.params_table.setColumnCount(len(self.experiments) + 1)
            
            # Set headers
            headers = ['Parameter'] + [exp['name'] for exp in self.experiments]
            self.params_table.setHorizontalHeaderLabels(headers)
            
            # Fill data
            for i, param in enumerate(sorted(all_params)):
                self.params_table.setItem(i, 0, QTableWidgetItem(param))
                for j, exp in enumerate(self.experiments):
                    value = exp.get('parameters', {}).get(param, '')
                    self.params_table.setItem(i, j+1,
                                            QTableWidgetItem(str(value)))
                                            
            # Adjust columns
            header = self.params_table.horizontalHeader()
            for i in range(len(headers)):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
                
        except Exception as e:
            logging.error(f"Error showing parameters comparison: {str(e)}")

class ExperimentFilterDialog(QDialog):
    """Dialog for filtering experiments."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the filter dialog UI."""
        self.setWindowTitle("Filter Experiments")
        layout = QFormLayout(self)
        
        # Filter controls
        self.name_filter = QLineEdit()
        self.model_filter = QLineEdit()
        self.date_from = QLineEdit()
        self.date_to = QLineEdit()
        self.metric_name = QComboBox()
        self.metric_min = QSpinBox()
        self.metric_max = QSpinBox()
        
        layout.addRow("Name contains:", self.name_filter)
        layout.addRow("Model contains:", self.model_filter)
        layout.addRow("Date from:", self.date_from)
        layout.addRow("Date to:", self.date_to)
        layout.addRow("Metric:", self.metric_name)
        layout.addRow("Min value:", self.metric_min)
        layout.addRow("Max value:", self.metric_max)
        
        # Buttons
        buttons = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.cancel_btn = QPushButton("Cancel")
        
        self.apply_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(self.apply_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addRow(buttons)
        
    def get_filters(self) -> Dict[str, Any]:
        """Get the current filter settings."""
        return {
            'name': self.name_filter.text(),
            'model': self.model_filter.text(),
            'date_from': self.date_from.text(),
            'date_to': self.date_to.text(),
            'metric': {
                'name': self.metric_name.currentText(),
                'min': self.metric_min.value(),
                'max': self.metric_max.value()
            }
        }

class AdvancedExperimentTracker(QWidget):
    """Advanced widget for tracking ML experiments."""
    
    experiment_selected = pyqtSignal(dict)
    experiments_compared = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_state()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Search and filter bar
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search experiments...")
        self.search_box.textChanged.connect(self._filter_experiments)
        
        self.filter_btn = QPushButton("Advanced Filter")
        self.filter_btn.clicked.connect(self._show_filter_dialog)
        
        search_layout.addWidget(self.search_box)
        search_layout.addWidget(self.filter_btn)
        
        # Experiments table
        self.table = QTableWidget(0, 7)  # id, name, model, metrics, params, tags, date
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Model", "Metrics", "Parameters", "Tags", "Date"
        ])
        
        # Adjust column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("Load Experiment")
        self.compare_btn = QPushButton("Compare Selected")
        self.delete_btn = QPushButton("Delete")
        self.export_btn = QPushButton("Export")
        self.tag_btn = QPushButton("Add Tags")
        
        self.load_btn.clicked.connect(self._load_experiment)
        self.compare_btn.clicked.connect(self._compare_experiments)
        self.delete_btn.clicked.connect(self._delete_experiment)
        self.export_btn.clicked.connect(self._export_experiments)
        self.tag_btn.clicked.connect(self._add_tags)
        
        self.load_btn.setEnabled(False)
        self.compare_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.tag_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.load_btn)
        buttons_layout.addWidget(self.compare_btn)
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addWidget(self.tag_btn)
        
        # Add components to layout
        layout.addLayout(search_layout)
        layout.addWidget(self.table)
        layout.addLayout(buttons_layout)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.experiments = []
        self.selected_experiments = []
        self.filters = {}
        self._load_experiments()
        
    def _filter_experiments(self):
        """Filter experiments based on search text and advanced filters."""
        try:
            search_text = self.search_box.text().lower()
            filtered_experiments = []
            
            for exp in self.experiments:
                # Check search text
                if (search_text in exp['name'].lower() or
                    search_text in exp['model'].lower() or
                    any(search_text in tag.lower()
                        for tag in exp.get('tags', []))):
                    
                    # Check advanced filters
                    if self._matches_filters(exp):
                        filtered_experiments.append(exp)
                        
            self._update_table(filtered_experiments)
            
        except Exception as e:
            self.logger.error(f"Error filtering experiments: {str(e)}")
            
    def _matches_filters(self, experiment: Dict) -> bool:
        """Check if experiment matches current filters."""
        try:
            if not self.filters:
                return True
                
            # Check name filter
            if (self.filters.get('name') and
                self.filters['name'].lower() not in
                experiment['name'].lower()):
                return False
                
            # Check model filter
            if (self.filters.get('model') and
                self.filters['model'].lower() not in
                experiment['model'].lower()):
                return False
                
            # Check date range
            if self.filters.get('date_from') or self.filters.get('date_to'):
                exp_date = datetime.strptime(experiment['date'],
                                           "%Y-%m-%d %H:%M:%S")
                if (self.filters.get('date_from') and
                    exp_date < datetime.strptime(self.filters['date_from'],
                                               "%Y-%m-%d")):
                    return False
                if (self.filters.get('date_to') and
                    exp_date > datetime.strptime(self.filters['date_to'],
                                               "%Y-%m-%d")):
                    return False
                    
            # Check metric filter
            metric_filter = self.filters.get('metric', {})
            if metric_filter.get('name'):
                metric_value = experiment['metrics'].get(metric_filter['name'])
                if metric_value is None:
                    return False
                if (metric_filter.get('min') is not None and
                    metric_value < metric_filter['min']):
                    return False
                if (metric_filter.get('max') is not None and
                    metric_value > metric_filter['max']):
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error matching filters: {str(e)}")
            return False
            
    def _show_filter_dialog(self):
        """Show advanced filter dialog."""
        try:
            dialog = ExperimentFilterDialog(self)
            
            # Set current filters
            if self.filters:
                dialog.name_filter.setText(self.filters.get('name', ''))
                dialog.model_filter.setText(self.filters.get('model', ''))
                dialog.date_from.setText(self.filters.get('date_from', ''))
                dialog.date_to.setText(self.filters.get('date_to', ''))
                
                metric_filter = self.filters.get('metric', {})
                if metric_filter.get('name'):
                    index = dialog.metric_name.findText(metric_filter['name'])
                    if index >= 0:
                        dialog.metric_name.setCurrentIndex(index)
                    dialog.metric_min.setValue(metric_filter.get('min', 0))
                    dialog.metric_max.setValue(metric_filter.get('max', 100))
                    
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.filters = dialog.get_filters()
                self._filter_experiments()
                
        except Exception as e:
            self.logger.error(f"Error showing filter dialog: {str(e)}")
            
    def _compare_experiments(self):
        """Compare selected experiments."""
        try:
            if len(self.selected_experiments) > 1:
                dialog = ExperimentComparisonDialog(self.selected_experiments,
                                                  self)
                dialog.exec()
                
        except Exception as e:
            self.logger.error(f"Error comparing experiments: {str(e)}")
            
    def _add_tags(self):
        """Add tags to selected experiments."""
        try:
            if self.selected_experiments:
                text, ok = QInputDialog.getText(
                    self, "Add Tags",
                    "Enter tags (comma-separated):",
                    QLineEdit.Normal
                )
                
                if ok and text:
                    tags = [t.strip() for t in text.split(',')]
                    for exp in self.selected_experiments:
                        if 'tags' not in exp:
                            exp['tags'] = []
                        exp['tags'].extend(tags)
                        
                    self._save_experiments()
                    self._update_table()
                    
        except Exception as e:
            self.logger.error(f"Error adding tags: {str(e)}")
            
    def add_experiment(self, experiment: Dict):
        """Add new experiment with enhanced metadata."""
        try:
            # Generate unique ID
            exp_id = max([exp['id'] for exp in self.experiments], default=0) + 1
            
            # Add metadata
            experiment.update({
                'id': exp_id,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'tags': experiment.get('tags', []),
                'parameters': experiment.get('parameters', {}),
                'notes': experiment.get('notes', ''),
                'version': experiment.get('version', '1.0')
            })
            
            self.experiments.append(experiment)
            self._save_experiments()
            self._filter_experiments()  # Update with filters
            
        except Exception as e:
            self.logger.error(f"Error adding experiment: {str(e)}")
            
    def get_experiment_by_metric(self, metric_name: str,
                               best: str = 'max') -> Optional[Dict]:
        """Get best experiment by metric."""
        try:
            if not self.experiments:
                return None
                
            filtered = [exp for exp in self.experiments
                       if metric_name in exp['metrics']]
                       
            if not filtered:
                return None
                
            if best == 'max':
                return max(filtered,
                         key=lambda x: x['metrics'][metric_name])
            else:
                return min(filtered,
                         key=lambda x: x['metrics'][metric_name])
                
        except Exception as e:
            self.logger.error(f"Error getting experiment by metric: {str(e)}")
            return None
