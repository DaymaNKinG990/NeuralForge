"""
Модуль для ленивой загрузки и инициализации компонентов
"""
import logging
import sys
import threading
import time
import importlib
import weakref
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Type, Union, Callable, TypeVar, Any, Optional
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import QEvent, QTimer, QObject, QThread, QMetaObject, Qt
from functools import wraps
import queue
from PyQt6.QtCore import pyqtSlot
import psutil

# Настройка логирования
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

T = TypeVar('T')

def lazy_property(fn):
    """Decorator for lazy property initialization."""
    attr_name = '_lazy_' + fn.__name__

    @property
    @wraps(fn)
    def _lazy_property(self):
        try:
            return getattr(self, attr_name)
        except AttributeError:
            value = fn(self)
            setattr(self, attr_name, value)
            return value
    return _lazy_property

def lazy_import(module_name: str) -> 'ModuleProxy':
    """Create a proxy for lazy module import.
    
    Args:
        module_name: Name of module to import
        
    Returns:
        ModuleProxy for the module
    """
    return ModuleProxy(module_name)

class ModuleProxy:
    """Proxy for lazy module loading."""
    
    def __init__(self, module_name: str):
        """Initialize module proxy.
        
        Args:
            module_name: Name of module to import
        """
        self._module_name = module_name
        self._module = None
        
    def __getattr__(self, name: str):
        if self._module is None:
            self._module = importlib.import_module(self._module_name)
        return getattr(self._module, name)

class LoadPriority(Enum):
    """Component load priorities."""
    CRITICAL = 0    # Load immediately
    HIGH = 1        # Load soon after critical
    MEDIUM = 2      # Load when convenient
    LOW = 3         # Load only when needed
    LAZY = 4        # Load on demand only

@dataclass
class ComponentMetadata:
    """Metadata for a lazy-loaded component."""
    name: str
    factory: Callable[[], Any]
    priority: LoadPriority
    dependencies: set
    size_estimate: int  # Bytes
    last_access: float
    access_count: int
    load_time: float
    is_loaded: bool
    weak_ref: Optional[weakref.ref]

class LazyWidget(QWidget):
    """Base class for widgets with lazy initialization."""
    
    def __init__(self, parent=None):
        """Initialize lazy widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._initialized = False
        self._init_error = None
        self._init_lock = threading.Lock()
        
    def initialize(self):
        """Initialize widget. Override in subclass."""
        pass
        
    def showEvent(self, event: QEvent):
        """Handle show event by initializing if needed.
        
        Args:
            event: Show event
        """
        if not self._initialized:
            with self._init_lock:
                if not self._initialized:
                    try:
                        self.initialize()
                        self._initialized = True
                    except Exception as e:
                        self._init_error = e
                        logger.error(f"Widget initialization failed: {e}")
                        raise
        super().showEvent(event)
        
    def is_initialized(self) -> bool:
        """Check if widget is initialized.
        
        Returns:
            True if initialized
        """
        return self._initialized
        
    def get_init_error(self) -> Optional[Exception]:
        """Get initialization error if any.
        
        Returns:
            Exception that occurred during initialization or None
        """
        return self._init_error

class LazyLoader:
    """Base lazy loader with simple caching."""
    
    def __init__(self):
        """Initialize lazy loader."""
        self._cache = {}
        self._lock = threading.Lock()
    
    def load(self, key: str, factory: Callable[[], T]) -> T:
        """Load an item using factory if not in cache.
        
        Args:
            key: Cache key
            factory: Factory function to create item
            
        Returns:
            Cached or newly created item
        """
        with self._lock:
            if key not in self._cache:
                self._cache[key] = factory()
            return self._cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached item or None if not found
        """
        return self._cache.get(key)
    
    def clear(self):
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
    
    def remove(self, key: str):
        """Remove item from cache.
        
        Args:
            key: Cache key
        """
        with self._lock:
            self._cache.pop(key, None)

class ResourceManager:
    """Manages system resources for component loading."""
    
    def __init__(self, memory_limit_mb: float = None):
        """Initialize resource manager.
        
        Args:
            memory_limit_mb: Maximum memory usage in MB. If None, use 75% of system memory.
        """
        self.memory_limit = (memory_limit_mb or 
                           psutil.virtual_memory().total * 0.75 / (1024 * 1024))
        self._lock = threading.Lock()
        self._current_memory = 0
        
    def can_load(self, size_mb: float) -> bool:
        """Check if there's enough memory to load a component.
        
        Args:
            size_mb: Estimated size of component in MB
            
        Returns:
            bool: True if component can be loaded
        """
        with self._lock:
            return (self._current_memory + size_mb) <= self.memory_limit
            
    def allocate(self, size_mb: float):
        """Allocate memory for a component.
        
        Args:
            size_mb: Size to allocate in MB
        """
        with self._lock:
            self._current_memory += size_mb
            
    def free(self, size_mb: float):
        """Free memory allocated to a component.
        
        Args:
            size_mb: Size to free in MB
        """
        with self._lock:
            self._current_memory = max(0, self._current_memory - size_mb)
            
    def get_usage(self) -> float:
        """Get current memory usage in MB."""
        return self._current_memory
        
    def get_available(self) -> float:
        """Get available memory in MB."""
        return self.memory_limit - self._current_memory

class PreloadManager:
    """Manages component preloading based on priority and dependencies."""
    
    def __init__(self, resource_manager: ResourceManager):
        """Initialize preload manager.
        
        Args:
            resource_manager: Resource manager instance
        """
        self.resource_manager = resource_manager
        self._preload_queue: list = []
        self._preload_thread = threading.Thread(target=self._preload_worker)
        self._stop_flag = threading.Event()
        
    def start(self):
        """Start preload worker thread."""
        self._stop_flag.clear()
        self._preload_thread.start()
        
    def stop(self):
        """Stop preload worker thread."""
        self._stop_flag.set()
        if self._preload_thread.is_alive():
            self._preload_thread.join()
            
    def queue_preload(self, component: ComponentMetadata):
        """Queue a component for preloading.
        
        Args:
            component: Component metadata
        """
        # Insert based on priority
        insert_idx = 0
        for idx, queued in enumerate(self._preload_queue):
            if component.priority.value < queued.priority.value:
                insert_idx = idx
                break
            insert_idx = idx + 1
        self._preload_queue.insert(insert_idx, component)
        
    def _preload_worker(self):
        """Background worker for preloading components."""
        while not self._stop_flag.is_set():
            try:
                if not self._preload_queue:
                    time.sleep(0.1)
                    continue
                    
                component = self._preload_queue[0]
                
                # Check if we can load it
                if not self.resource_manager.can_load(
                    component.size_estimate / (1024 * 1024)
                ):
                    time.sleep(0.1)
                    continue
                    
                # Load the component
                start_time = time.time()
                instance = component.factory()
                component.load_time = time.time() - start_time
                component.is_loaded = True
                component.weak_ref = weakref.ref(instance)
                
                # Update resource tracking
                self.resource_manager.allocate(
                    component.size_estimate / (1024 * 1024)
                )
                
                # Remove from queue
                self._preload_queue.pop(0)
                
            except Exception as e:
                logging.error(f"Error preloading component: {e}")
                time.sleep(1.0)

class ComponentLoader:
    """Enhanced component loader with dependency management."""
    
    def __init__(self):
        """Initialize component loader."""
        self.resource_manager = ResourceManager()
        self.preload_manager = PreloadManager(self.resource_manager)
        self._components: Dict[str, ComponentMetadata] = {}
        self._lock = threading.Lock()
        
        # Start preload manager
        self.preload_manager.start()
        
    def register_component(
        self,
        name: str,
        factory: Callable[[], T],
        priority: LoadPriority = LoadPriority.MEDIUM,
        dependencies: set = None,
        size_estimate: int = 1024 * 1024  # 1MB default
    ) -> None:
        """Register a component for lazy loading.
        
        Args:
            name: Component name
            factory: Factory function to create component
            priority: Load priority
            dependencies: Component dependencies
            size_estimate: Estimated memory size in bytes
        """
        with self._lock:
            self._components[name] = ComponentMetadata(
                name=name,
                factory=factory,
                priority=priority,
                dependencies=dependencies or set(),
                size_estimate=size_estimate,
                last_access=0.0,
                access_count=0,
                load_time=0.0,
                is_loaded=False,
                weak_ref=None
            )
            
            # Queue for preloading if high priority
            if priority in (LoadPriority.CRITICAL, LoadPriority.HIGH):
                self.preload_manager.queue_preload(self._components[name])
                
    def get_component(self, name: str) -> Optional[T]:
        """Get a component, loading it if necessary.
        
        Args:
            name: Component name
            
        Returns:
            Component instance or None if not found
        """
        with self._lock:
            if name not in self._components:
                return None
                
            metadata = self._components[name]
            
            # Check if already loaded
            if metadata.is_loaded:
                instance = metadata.weak_ref()
                if instance is not None:
                    metadata.last_access = time.time()
                    metadata.access_count += 1
                    return instance
                metadata.is_loaded = False
                
            # Check dependencies
            for dep in metadata.dependencies:
                if not self.is_loaded(dep):
                    self.get_component(dep)
                    
            # Check resources
            if not self.resource_manager.can_load(
                metadata.size_estimate / (1024 * 1024)
            ):
                self._free_memory()
                
            # Load component
            start_time = time.time()
            instance = metadata.factory()
            metadata.load_time = time.time() - start_time
            metadata.is_loaded = True
            metadata.weak_ref = weakref.ref(instance)
            metadata.last_access = time.time()
            metadata.access_count += 1
            
            # Update resource tracking
            self.resource_manager.allocate(
                metadata.size_estimate / (1024 * 1024)
            )
            
            return instance
            
    def is_loaded(self, name: str) -> bool:
        """Check if a component is loaded.
        
        Args:
            name: Component name
            
        Returns:
            bool: True if component is loaded
        """
        with self._lock:
            if name not in self._components:
                return False
            metadata = self._components[name]
            if not metadata.is_loaded:
                return False
            return metadata.weak_ref() is not None
            
    def unload_component(self, name: str) -> bool:
        """Unload a component.
        
        Args:
            name: Component name
            
        Returns:
            bool: True if component was unloaded
        """
        with self._lock:
            if name not in self._components:
                return False
                
            metadata = self._components[name]
            if not metadata.is_loaded:
                return False
                
            # Clear reference and run garbage collection
            metadata.weak_ref = None
            metadata.is_loaded = False
            import gc
            gc.collect()
            
            # Update resource tracking
            self.resource_manager.free(
                metadata.size_estimate / (1024 * 1024)
            )
            
            return True
            
    def _free_memory(self):
        """Free memory by unloading least important components."""
        # Sort components by importance (higher number = less important)
        def importance(metadata: ComponentMetadata) -> float:
            if not metadata.is_loaded:
                return float('inf')
            # Consider priority, access count, and recency
            priority_factor = metadata.priority.value * 10.0
            access_factor = 1.0 / (metadata.access_count + 1)
            recency_factor = time.time() - metadata.last_access
            return priority_factor + access_factor + recency_factor
            
        sorted_components = sorted(
            self._components.values(),
            key=importance
        )
        
        # Unload components until we have enough memory
        for metadata in sorted_components:
            if not metadata.is_loaded:
                continue
            self.unload_component(metadata.name)
            if self.resource_manager.get_available() > 100:  # Keep 100MB free
                break
                
    def cleanup(self):
        """Clean up resources."""
        self.preload_manager.stop()
        for name in list(self._components.keys()):
            self.unload_component(name)
            
    def get_stats(self) -> Dict[str, Any]:
        """Get loader statistics.
        
        Returns:
            Dict with statistics
        """
        return {
            'component_count': len(self._components),
            'loaded_count': sum(1 for m in self._components.values() if m.is_loaded),
            'memory_usage_mb': self.resource_manager.get_usage(),
            'memory_available_mb': self.resource_manager.get_available(),
            'average_load_time': sum(
                m.load_time for m in self._components.values() if m.is_loaded
            ) / max(1, sum(1 for m in self._components.values() if m.is_loaded))
        }

# Глобальные экземпляры
component_loader = ComponentLoader()
