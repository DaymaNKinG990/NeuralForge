from typing import Optional, Dict, List, Tuple
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTabWidget, QProgressBar, 
                             QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor
import psutil
import pyqtgraph as pg
import numpy as np
from ..utils.performance import PerformanceMonitor
from ..utils.caching import cache_manager, search_cache
from ..utils.distributed_cache import distributed_cache
from ..utils.preloader import preload_manager, component_preloader
from ..utils.ui_optimizer import render_optimizer, composition_optimizer
from .styles.style_manager import StyleManager
from .styles.style_enums import StyleClass, ColorScheme

class PerformanceWidget(QWidget):
    """Real-time performance monitoring widget.
    
    Monitors and displays system resources including CPU usage, memory consumption,
    GPU utilization, and disk I/O. Provides real-time graphs and statistics.
    
    Attributes:
        update_interval: Interval in milliseconds between updates
        style_manager: Manager for applying consistent styles
        cache: Cache manager for performance data
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the performance monitor.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._style_manager = StyleManager()
        self._init_ui()
        self._apply_styles()
        
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Создаем вкладки для разных метрик
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Системные ресурсы
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        
        # CPU и память
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
        
        # Кэширование
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
        
        # UI оптимизации
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)
        
        self.render_stats = QLabel()
        self.composition_stats = QLabel()
        ui_layout.addWidget(self.render_stats)
        ui_layout.addWidget(self.composition_stats)
        
        optimize_ui_btn = QPushButton("Optimize UI")
        optimize_ui_btn.clicked.connect(self.optimize_ui)
        ui_layout.addWidget(optimize_ui_btn)
        
        # Предзагрузка
        preload_tab = QWidget()
        preload_layout = QVBoxLayout(preload_tab)
        
        self.preload_stats = QLabel()
        preload_layout.addWidget(self.preload_stats)
        
        clear_preload_btn = QPushButton("Clear Unused Components")
        clear_preload_btn.clicked.connect(
            lambda: component_preloader.clear_unused()
        )
        preload_layout.addWidget(clear_preload_btn)
        
        # Добавляем вкладки
        tabs.addTab(system_tab, "System")
        tabs.addTab(cache_tab, "Cache")
        tabs.addTab(ui_tab, "UI")
        tabs.addTab(preload_tab, "Preload")
        
        # Таймер обновления
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)  # Обновление каждую секунду
        
    def _apply_styles(self) -> None:
        """Apply styles to all components."""
        self.setStyleSheet(self._style_manager.get_component_style(StyleClass.DOCK_WIDGET))
        
    def update_stats(self) -> None:
        """Update all performance metrics."""
        # Системные ресурсы
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        self.cpu_bar.setValue(int(cpu_percent))
        
        memory_percent = (memory.used / memory.total) * 100
        self.memory_bar.setValue(int(memory_percent))
        
        # Статистика кэширования
        cache_stats = cache_manager.get_stats()
        hits = cache_stats.get('hits', 0)
        misses = cache_stats.get('misses', 0)
        size = cache_stats.get('size', 0)

        cache_text = f"Hits: {hits}\n"
        cache_text += f"Misses: {misses}\n"
        cache_text += f"Size: {size} MB"
        self.cache_stats.setText(cache_text)
        
        # UI статистика
        window = self.window()
        if window:
            render_metrics = render_optimizer._metrics
            slow_widgets = [
                w.__class__.__name__ 
                for w, m in render_metrics.items() 
                if m.paint_time > 16
            ]
            
            self.render_stats.setText(
                f"Slow Rendering Widgets: {', '.join(slow_widgets) if slow_widgets else 'None'}\n"
                f"Total Widgets: {len(render_metrics)}"
            )
            
        # Статистика предзагрузки
        preload_stats = preload_manager.get_loading_stats()
        slow_loads = [
            f"{mod}: {time:.1f}s"
            for mod, time in preload_stats.items()
            if time > 0.1
        ]
        
        self.preload_stats.setText(
            f"Preloaded Modules: {len(preload_stats)}\n"
            f"Slow Loads:\n" + "\n".join(slow_loads)
        )
        
    def clear_caches(self) -> None:
        """Clear all caches."""
        cache_manager.clear()
        search_cache.clear()
        distributed_cache.clear()
        
    def optimize_ui(self) -> None:
        """Optimize UI."""
        window = self.window()
        if window:
            # Оптимизируем все виджеты
            for widget in window.findChildren(QWidget):
                render_optimizer.register_widget(widget)
                composition_optimizer.optimize_layout(widget)
                
    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)
        self.update_timer.start()
        
    def hideEvent(self, event) -> None:
        """Handle hide event."""
        super().hideEvent(event)
        self.update_timer.stop()
