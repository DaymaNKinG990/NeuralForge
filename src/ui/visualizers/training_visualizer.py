"""Training progress visualization component."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import logging

class TrainingVisualizer(QWidget):
    """Widget for visualizing training metrics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_data()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different plots
        self.tab_widget = QTabWidget()
        
        # Loss plot
        self.loss_plot = pg.PlotWidget()
        self.loss_plot.setBackground('w')
        self.loss_plot.setTitle("Training Loss", color="k")
        self.loss_plot.setLabel('left', 'Loss', color="k")
        self.loss_plot.setLabel('bottom', 'Epoch', color="k")
        self.loss_plot.showGrid(x=True, y=True)
        self.tab_widget.addTab(self.loss_plot, "Loss")
        
        # Accuracy plot
        self.accuracy_plot = pg.PlotWidget()
        self.accuracy_plot.setBackground('w')
        self.accuracy_plot.setTitle("Training Accuracy", color="k")
        self.accuracy_plot.setLabel('left', 'Accuracy (%)', color="k")
        self.accuracy_plot.setLabel('bottom', 'Epoch', color="k")
        self.accuracy_plot.showGrid(x=True, y=True)
        self.tab_widget.addTab(self.accuracy_plot, "Accuracy")
        
        # Learning rate plot
        self.lr_plot = pg.PlotWidget()
        self.lr_plot.setBackground('w')
        self.lr_plot.setTitle("Learning Rate", color="k")
        self.lr_plot.setLabel('left', 'Learning Rate', color="k")
        self.lr_plot.setLabel('bottom', 'Epoch', color="k")
        self.lr_plot.showGrid(x=True, y=True)
        self.tab_widget.addTab(self.lr_plot, "Learning Rate")
        
        layout.addWidget(self.tab_widget)
        
    def _initialize_data(self):
        """Initialize data storage."""
        self.epochs = []
        self.losses = []
        self.accuracies = []
        self.learning_rates = []
        
    def update_metrics(self, metrics: dict):
        """Update plots with new metrics."""
        try:
            # Extract metrics
            epoch = metrics.get('epoch', len(self.epochs) + 1)
            loss = metrics.get('loss', 0.0)
            accuracy = metrics.get('accuracy', 0.0)
            lr = metrics.get('learning_rate', 0.0)
            
            # Update data
            self.epochs.append(epoch)
            self.losses.append(loss)
            self.accuracies.append(accuracy * 100)  # Convert to percentage
            self.learning_rates.append(lr)
            
            # Update plots
            self._update_loss_plot()
            self._update_accuracy_plot()
            self._update_lr_plot()
            
        except Exception as e:
            self.logger.error(f"Error updating training metrics: {str(e)}")
            
    def _update_loss_plot(self):
        """Update loss plot."""
        try:
            self.loss_plot.clear()
            self.loss_plot.plot(self.epochs, self.losses, pen=pg.mkPen(color='r', width=2))
        except Exception as e:
            self.logger.error(f"Error updating loss plot: {str(e)}")
            
    def _update_accuracy_plot(self):
        """Update accuracy plot."""
        try:
            self.accuracy_plot.clear()
            self.accuracy_plot.plot(self.epochs, self.accuracies, pen=pg.mkPen(color='b', width=2))
        except Exception as e:
            self.logger.error(f"Error updating accuracy plot: {str(e)}")
            
    def _update_lr_plot(self):
        """Update learning rate plot."""
        try:
            self.lr_plot.clear()
            self.lr_plot.plot(self.epochs, self.learning_rates, pen=pg.mkPen(color='g', width=2))
        except Exception as e:
            self.logger.error(f"Error updating learning rate plot: {str(e)}")
            
    def reset(self):
        """Reset all plots and data."""
        try:
            self._initialize_data()
            self.loss_plot.clear()
            self.accuracy_plot.clear()
            self.lr_plot.clear()
        except Exception as e:
            self.logger.error(f"Error resetting training visualization: {str(e)}")
