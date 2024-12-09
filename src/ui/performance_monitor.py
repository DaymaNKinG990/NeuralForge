from typing import Optional, Dict, List, Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTabWidget, QProgressBar, 
                             QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor
import psutil
import pyqtgraph as pg
import numpy as np
import threading
import logging
from ..utils.performance import PerformanceMonitor
from ..utils.caching import cache_manager, search_cache
from ..utils.distributed_cache import distributed_cache
from ..utils.preloader import preload_manager, component_preloader
from ..utils.ui_optimizer import render_optimizer, composition_optimizer
from .styles.style_manager import StyleManager
from .styles.style_enums import StyleClass, ColorScheme

class PerformanceWidget(QWidget):
    """Real-time performance monitoring widget."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._style_manager = StyleManager()
        self._init_ui()
        self._apply_styles()
        self._is_active = True
        
    def __del__(self):
        """Clean up resources."""
        self._is_active = False
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create tabs for different metrics
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # System resources
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        
        # CPU and memory
        self.cpu_label = QLabel("CPU Usage:")
        self.cpu_label.setObjectName("statsLabel")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setObjectName("cpuBar")
        
        self.memory_label = QLabel("Memory Usage:")
        self.memory_label.setObjectName("statsLabel")
        self.memory_bar = QProgressBar()
        self.memory_bar.setObjectName("memoryBar")
        
        system_layout.addWidget(self.cpu_label)
        system_layout.addWidget(self.cpu_bar)
        system_layout.addWidget(self.memory_label)
        system_layout.addWidget(self.memory_bar)
        
        # Cache tab
        cache_tab = QWidget()
        cache_layout = QVBoxLayout(cache_tab)
        
        self.cache_label = QLabel("Cache Statistics:")
        self.cache_label.setObjectName("statsLabel")
        self.cache_stats = QLabel()
        self.cache_stats.setObjectName("statsLabel")
        
        clear_cache_btn = QPushButton("Clear All Caches")
        clear_cache_btn.clicked.connect(self.clear_caches)
        cache_layout.addWidget(self.cache_label)
        cache_layout.addWidget(self.cache_stats)
        cache_layout.addWidget(clear_cache_btn)
        
        # UI optimization tab
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)
        
        self.render_stats = QLabel()
        self.composition_stats = QLabel()
        ui_layout.addWidget(self.render_stats)
        ui_layout.addWidget(self.composition_stats)
        
        optimize_ui_btn = QPushButton("Optimize UI")
        optimize_ui_btn.clicked.connect(self.optimize_ui)
        ui_layout.addWidget(optimize_ui_btn)
        
        # Preload tab
        preload_tab = QWidget()
        preload_layout = QVBoxLayout(preload_tab)
        
        self.preload_stats = QLabel()
        preload_layout.addWidget(self.preload_stats)
        
        clear_preload_btn = QPushButton("Clear Unused Components")
        clear_preload_btn.clicked.connect(
            lambda: component_preloader.clear_unused()
        )
        preload_layout.addWidget(clear_preload_btn)
        
        # Add tabs
        tabs.addTab(system_tab, "System")
        tabs.addTab(cache_tab, "Cache")
        tabs.addTab(ui_tab, "UI")
        tabs.addTab(preload_tab, "Preload")
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)  # Update every second
        
    def _apply_styles(self) -> None:
        """Apply styles to all components."""
        self.setStyleSheet(self._style_manager.get_component_style(StyleClass.DOCK_WIDGET))
        
    def update_stats(self) -> None:
        """Update all performance metrics."""
        try:
            if not self._is_active:
                return
                
            # System resources
            try:
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                
                self.cpu_bar.setValue(int(cpu_percent))
                memory_percent = (memory.used / memory.total) * 100
                self.memory_bar.setValue(int(memory_percent))
            except Exception as e:
                self.logger.warning(f"Error updating system stats: {str(e)}")
                
            # Cache statistics
            try:
                cache_stats = cache_manager.get_stats()
                hits = cache_stats.get('hits', 0)
                misses = cache_stats.get('misses', 0)
                size = cache_stats.get('size', 0)
                
                cache_text = f"Hits: {hits}\n"
                cache_text += f"Misses: {misses}\n"
                cache_text += f"Size: {size} MB"
                self.cache_stats.setText(cache_text)
            except Exception as e:
                self.logger.warning(f"Error updating cache stats: {str(e)}")
                
            # UI statistics
            try:
                window = self.window()
                if window:
                    render_metrics = getattr(render_optimizer, '_metrics', {})
                    if render_metrics:
                        render_text = "Render Metrics:\n"
                        for key, value in render_metrics.items():
                            render_text += f"{key}: {value}\n"
                        self.render_stats.setText(render_text)
                    
                    comp_metrics = getattr(composition_optimizer, '_metrics', {})
                    if comp_metrics:
                        comp_text = "Composition Metrics:\n"
                        for key, value in comp_metrics.items():
                            comp_text += f"{key}: {value}\n"
                        self.composition_stats.setText(comp_text)
            except Exception as e:
                self.logger.warning(f"Error updating UI stats: {str(e)}")
                
            # Preload statistics
            try:
                preload_text = "Preloaded Components:\n"
                if hasattr(component_preloader, 'get_status'):
                    for comp, status in component_preloader.get_status().items():
                        preload_text += f"{comp}: {status}\n"
                else:
                    preload_text += "Status not available"
                self.preload_stats.setText(preload_text)
            except Exception as e:
                self.logger.warning(f"Error updating preload stats: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Error in update_stats: {str(e)}")
            
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
            
    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)
        self.update_timer.start()
        
    def hideEvent(self, event) -> None:
        """Handle hide event."""
        super().hideEvent(event)
        self.update_timer.stop()
