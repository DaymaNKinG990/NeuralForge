"""Training progress panel."""
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QProgressBar,
    QLabel, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt
from .data_manager import TrainingDataManager

class ProgressPanel(QWidget):
    """Panel for displaying training progress."""
    
    def __init__(self, data_manager: TrainingDataManager, parent=None):
        """Initialize progress panel.
        
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
        
        # Progress section
        progress_frame = QFrame()
        progress_frame.setFrameStyle(
            QFrame.Shape.StyledPanel | QFrame.Shadow.Raised
        )
        progress_layout = QGridLayout(progress_frame)
        
        # Epoch progress
        progress_layout.addWidget(QLabel("Epoch:"), 0, 0)
        self.epoch_label = QLabel()
        progress_layout.addWidget(self.epoch_label, 0, 1)
        
        self.epoch_progress = QProgressBar()
        self.epoch_progress.setTextVisible(True)
        progress_layout.addWidget(self.epoch_progress, 0, 2)
        
        # Batch progress
        progress_layout.addWidget(QLabel("Batch:"), 1, 0)
        self.batch_label = QLabel()
        progress_layout.addWidget(self.batch_label, 1, 1)
        
        self.batch_progress = QProgressBar()
        self.batch_progress.setTextVisible(True)
        progress_layout.addWidget(self.batch_progress, 1, 2)
        
        layout.addWidget(progress_frame)
        
        # Stats section
        stats_frame = QFrame()
        stats_frame.setFrameStyle(
            QFrame.Shape.StyledPanel | QFrame.Shadow.Raised
        )
        stats_layout = QGridLayout(stats_frame)
        
        # Training time
        stats_layout.addWidget(QLabel("Training Time:"), 0, 0)
        self.time_label = QLabel()
        stats_layout.addWidget(self.time_label, 0, 1)
        
        # Remaining time
        stats_layout.addWidget(QLabel("Remaining:"), 1, 0)
        self.remaining_label = QLabel()
        stats_layout.addWidget(self.remaining_label, 1, 1)
        
        # Speed
        stats_layout.addWidget(QLabel("Speed:"), 2, 0)
        self.speed_label = QLabel()
        stats_layout.addWidget(self.speed_label, 2, 1)
        
        # Memory usage
        stats_layout.addWidget(QLabel("Memory:"), 3, 0)
        self.memory_label = QLabel()
        stats_layout.addWidget(self.memory_label, 3, 1)
        
        layout.addWidget(stats_frame)
        
        # Status section
        status_frame = QFrame()
        status_frame.setFrameStyle(
            QFrame.Shape.StyledPanel | QFrame.Shadow.Raised
        )
        status_layout = QVBoxLayout(status_frame)
        
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_frame)
        
        layout.addStretch()
        
    def update_progress(self):
        """Update progress display."""
        progress = self.data_manager.get_current_progress()
        if not progress:
            self.clear_display()
            return
            
        # Update epoch progress
        epoch = progress.get('epoch', 0)
        total_epochs = progress.get('total_epochs', 0)
        if total_epochs:
            self.epoch_label.setText(f"{epoch}/{total_epochs}")
            self.epoch_progress.setMaximum(total_epochs)
            self.epoch_progress.setValue(epoch)
        else:
            self.epoch_label.setText(str(epoch))
            self.epoch_progress.setMaximum(0)
            
        # Update batch progress
        batch = progress.get('batch', 0)
        total_batches = progress.get('total_batches', 0)
        if total_batches:
            self.batch_label.setText(f"{batch}/{total_batches}")
            self.batch_progress.setMaximum(total_batches)
            self.batch_progress.setValue(batch)
        else:
            self.batch_label.setText(str(batch))
            self.batch_progress.setMaximum(0)
            
        # Update stats
        self.time_label.setText(
            self.format_time(progress.get('training_time', 0))
        )
        self.remaining_label.setText(
            self.format_time(progress.get('remaining_time', 0))
        )
        self.speed_label.setText(
            f"{progress.get('speed', 0):.2f} samples/sec"
        )
        self.memory_label.setText(
            self.format_memory(progress.get('memory_used', 0))
        )
        
        # Update status
        status = progress.get('status', '')
        self.status_label.setText(status)
        
    def clear_display(self):
        """Clear progress display."""
        self.epoch_label.clear()
        self.epoch_progress.setMaximum(0)
        self.epoch_progress.setValue(0)
        
        self.batch_label.clear()
        self.batch_progress.setMaximum(0)
        self.batch_progress.setValue(0)
        
        self.time_label.clear()
        self.remaining_label.clear()
        self.speed_label.clear()
        self.memory_label.clear()
        self.status_label.clear()
        
    def format_time(self, seconds: float) -> str:
        """Format time in seconds.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        if seconds < 0:
            return "Unknown"
            
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
            
    def format_memory(self, bytes: int) -> str:
        """Format memory size.
        
        Args:
            bytes: Memory size in bytes
            
        Returns:
            Formatted memory string
        """
        if bytes < 0:
            return "Unknown"
            
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} TB"
