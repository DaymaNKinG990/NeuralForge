"""File statistics for project explorer."""
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import os
import logging
from collections import defaultdict
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem,
    QLabel, QProgressBar
)
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet
from ..styles.style_manager import StyleManager

logger = logging.getLogger(__name__)

class ProjectStatistics:
    """Project statistics calculator."""
    
    def __init__(self, root_path: Path):
        """Initialize statistics calculator.
        
        Args:
            root_path: Project root path
        """
        self.root_path = root_path
        self.file_counts: Dict[str, int] = defaultdict(int)
        self.total_size = 0
        self.file_sizes: Dict[str, int] = defaultdict(int)
        self.last_modified: Dict[str, datetime] = {}
        self.line_counts: Dict[str, int] = defaultdict(int)
        
    def calculate(self):
        """Calculate project statistics."""
        try:
            for path in self.root_path.rglob('*'):
                if path.is_file():
                    ext = path.suffix.lower() or 'no_extension'
                    size = path.stat().st_size
                    modified = datetime.fromtimestamp(path.stat().st_mtime)
                    
                    # Update statistics
                    self.file_counts[ext] += 1
                    self.total_size += size
                    self.file_sizes[ext] += size
                    self.last_modified[str(path)] = modified
                    
                    # Count lines for text files
                    if self.is_text_file(path):
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                self.line_counts[ext] += sum(1 for _ in f)
                        except Exception:
                            pass
                            
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {str(e)}")
            
    def is_text_file(self, path: Path) -> bool:
        """Check if file is text file.
        
        Args:
            path: File path
            
        Returns:
            True if text file
        """
        text_extensions = {
            '.txt', '.py', '.js', '.html', '.css',
            '.json', '.xml', '.md', '.rst', '.yaml',
            '.yml', '.ini', '.conf', '.sh', '.bat'
        }
        return path.suffix.lower() in text_extensions
        
    def get_file_type_stats(self) -> List[Tuple[str, int, int, int]]:
        """Get file type statistics.
        
        Returns:
            List of (extension, count, size, lines) tuples
        """
        stats = []
        for ext in self.file_counts.keys():
            stats.append((
                ext,
                self.file_counts[ext],
                self.file_sizes[ext],
                self.line_counts[ext]
            ))
        return sorted(stats, key=lambda x: x[1], reverse=True)
        
    def get_largest_files(self, limit: int = 10) -> List[Tuple[Path, int]]:
        """Get largest files.
        
        Args:
            limit: Maximum number of files
            
        Returns:
            List of (path, size) tuples
        """
        files = []
        for path in self.root_path.rglob('*'):
            if path.is_file():
                files.append((path, path.stat().st_size))
        return sorted(files, key=lambda x: x[1], reverse=True)[:limit]
        
    def get_recently_modified(self, limit: int = 10) -> List[Tuple[Path, datetime]]:
        """Get recently modified files.
        
        Args:
            limit: Maximum number of files
            
        Returns:
            List of (path, modified) tuples
        """
        items = [
            (Path(p), dt)
            for p, dt in self.last_modified.items()
        ]
        return sorted(items, key=lambda x: x[1], reverse=True)[:limit]

class StatisticsWidget(QWidget):
    """Widget for displaying project statistics."""
    
    def __init__(self, parent=None):
        """Initialize statistics widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the statistics UI."""
        layout = QVBoxLayout(self)
        
        # Progress bar for calculation
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
        
        # Tab widget for different views
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Overview tab
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        self.overview_label = QLabel()
        overview_layout.addWidget(self.overview_label)
        self.tabs.addTab(overview_widget, "Overview")
        
        # File types tab
        types_widget = QWidget()
        types_layout = QVBoxLayout(types_widget)
        self.types_table = QTableWidget()
        self.types_table.setColumnCount(4)
        self.types_table.setHorizontalHeaderLabels([
            "Extension", "Count", "Size", "Lines"
        ])
        types_layout.addWidget(self.types_table)
        
        # Add charts
        self.type_chart = QChartView()
        self.type_chart.setMinimumHeight(200)
        types_layout.addWidget(self.type_chart)
        self.tabs.addTab(types_widget, "File Types")
        
        # Largest files tab
        largest_widget = QWidget()
        largest_layout = QVBoxLayout(largest_widget)
        self.largest_table = QTableWidget()
        self.largest_table.setColumnCount(2)
        self.largest_table.setHorizontalHeaderLabels([
            "File", "Size"
        ])
        largest_layout.addWidget(self.largest_table)
        self.tabs.addTab(largest_widget, "Largest Files")
        
        # Recent files tab
        recent_widget = QWidget()
        recent_layout = QVBoxLayout(recent_widget)
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(2)
        self.recent_table.setHorizontalHeaderLabels([
            "File", "Modified"
        ])
        recent_layout.addWidget(self.recent_table)
        self.tabs.addTab(recent_widget, "Recent Files")
        
    def update_statistics(self, stats: ProjectStatistics):
        """Update statistics display.
        
        Args:
            stats: Project statistics
        """
        # Update overview
        total_files = sum(stats.file_counts.values())
        total_lines = sum(stats.line_counts.values())
        self.overview_label.setText(
            f"Total Files: {total_files}\n"
            f"Total Size: {self.format_size(stats.total_size)}\n"
            f"Total Lines: {total_lines:,}"
        )
        
        # Update file types table and chart
        self.update_file_types(stats)
        
        # Update largest files
        self.update_largest_files(stats)
        
        # Update recent files
        self.update_recent_files(stats)
        
    def update_file_types(self, stats: ProjectStatistics):
        """Update file types display.
        
        Args:
            stats: Project statistics
        """
        # Update table
        type_stats = stats.get_file_type_stats()
        self.types_table.setRowCount(len(type_stats))
        for row, (ext, count, size, lines) in enumerate(type_stats):
            self.types_table.setItem(row, 0, QTableWidgetItem(ext))
            self.types_table.setItem(row, 1, QTableWidgetItem(str(count)))
            self.types_table.setItem(row, 2, QTableWidgetItem(self.format_size(size)))
            self.types_table.setItem(row, 3, QTableWidgetItem(f"{lines:,}"))
            
        # Update chart
        pie = QPieSeries()
        for ext, count, _, _ in type_stats[:5]:  # Top 5 types
            pie.append(f"{ext} ({count})", count)
            
        chart = QChart()
        chart.addSeries(pie)
        chart.setTitle("File Type Distribution")
        self.type_chart.setChart(chart)
        
    def update_largest_files(self, stats: ProjectStatistics):
        """Update largest files display.
        
        Args:
            stats: Project statistics
        """
        largest = stats.get_largest_files()
        self.largest_table.setRowCount(len(largest))
        for row, (path, size) in enumerate(largest):
            self.largest_table.setItem(
                row, 0,
                QTableWidgetItem(str(path.relative_to(stats.root_path)))
            )
            self.largest_table.setItem(
                row, 1,
                QTableWidgetItem(self.format_size(size))
            )
            
    def update_recent_files(self, stats: ProjectStatistics):
        """Update recent files display.
        
        Args:
            stats: Project statistics
        """
        recent = stats.get_recently_modified()
        self.recent_table.setRowCount(len(recent))
        for row, (path, modified) in enumerate(recent):
            self.recent_table.setItem(
                row, 0,
                QTableWidgetItem(str(path.relative_to(stats.root_path)))
            )
            self.recent_table.setItem(
                row, 1,
                QTableWidgetItem(modified.strftime('%Y-%m-%d %H:%M:%S'))
            )
            
    def format_size(self, size: int) -> str:
        """Format file size.
        
        Args:
            size: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
