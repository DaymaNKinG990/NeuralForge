"""
Модуль для ленивой загрузки и инициализации компонентов
"""
import logging
import sys
import threading
import time
import importlib
from typing import Dict, Type, Union, Callable, TypeVar, Any, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QEvent, QTimer, QObject
from functools import wraps
import queue

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

class ImportTimeoutError(Exception):
    """Timeout during module import"""
    pass

class ModuleProxy:
    """Прокси для ленивой загрузки модулей"""
    
    def __init__(self, module_path: str, timeout: float = 10.0):
        self._module_path = module_path
        self._module = None
        self._lock = threading.Lock()
        self._logger = logger
        self._timeout = timeout
        self._import_queue = queue.Queue()
        self._import_thread = None
        self._import_error = None
        self._import_time = 0.0
        
    @property
    def _loaded_module(self):
        """Получить загруженный модуль, загрузить при необходимости"""
        if self._module is None:
            with self._lock:
                if self._module is None:
                    try:
                        start_time = time.time()
                        
                        # Start import in a separate thread
                        self._import_thread = threading.Thread(
                            target=self._import_module,
                            daemon=True
                        )
                        self._import_thread.start()
                        
                        # Wait for import with timeout
                        self._import_thread.join(timeout=self._timeout)
                        
                        if self._import_thread.is_alive():
                            self._import_error = ImportTimeoutError(
                                f"Import of {self._module_path} timed out after {self._timeout}s"
                            )
                            raise self._import_error
                            
                        if self._import_error:
                            raise self._import_error
                            
                        self._import_time = time.time() - start_time
                        self._logger.debug(
                            f"Module {self._module_path} imported in {self._import_time:.2f}s"
                        )
                        
                    except Exception as e:
                        self._import_error = e
                        self._logger.error(
                            f"Error importing module {self._module_path}: {str(e)}",
                            exc_info=True
                        )
                        raise
                        
        return self._module
        
    def _import_module(self):
        """Import module in separate thread"""
        try:
            self._module = importlib.import_module(self._module_path)
            self._import_queue.put(None)  # Signal success
        except Exception as e:
            self._import_error = e
            self._import_queue.put(e)  # Signal error
            
    def cleanup(self):
        """Clean up resources"""
        try:
            if self._import_thread and self._import_thread.is_alive():
                self._import_thread.join(timeout=1.0)
            self._module = None
            self._import_error = None
        except Exception as e:
            self._logger.error(f"Error cleaning up ModuleProxy: {str(e)}", exc_info=True)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._loaded_module, name)

class LazyLoader:
    """Загрузчик для ленивой загрузки модулей"""
    
    def __init__(self):
        self._cache: Dict[str, ModuleProxy] = {}
        self._loading_times: Dict[str, float] = {}
        self._logger = logger
        self._lock = threading.Lock()
        self._logger.debug("LazyLoader initialized")

    def load_module(self, module_name: str, timeout: float = 10.0) -> ModuleProxy:
        """
        Загрузить модуль
        
        Args:
            module_name: Имя модуля для загрузки
            timeout: Таймаут загрузки в секундах
            
        Returns:
            ModuleProxy: Прокси для доступа к модулю
        """
        with self._lock:
            if module_name not in self._cache:
                start_time = time.time()
                try:
                    self._cache[module_name] = ModuleProxy(module_name, timeout)
                    self._loading_times[module_name] = time.time() - start_time
                except Exception as e:
                    self._logger.error(
                        f"Error loading module {module_name}: {str(e)}",
                        extra={"module": module_name, "error": str(e)},
                        exc_info=True
                    )
                    raise
            return self._cache[module_name]

    def is_loaded(self, module_name: str) -> bool:
        """Проверить, загружен ли модуль"""
        return module_name in self._cache and self._cache[module_name]._module is not None

    def get_load_stats(self) -> Dict[str, float]:
        """Получить статистику загрузки модулей"""
        return dict(self._loading_times)

    def clear(self) -> None:
        """Очистить кэш загруженных модулей"""
        with self._lock:
            self._cache.clear()
            self._loading_times.clear()

class LazyWidget(QWidget):
    """Базовый класс для виджетов с ленивой инициализацией"""
    
    def __init__(self, parent=None):
        try:
            super().__init__(parent)
            self._initialized = False
            self._init_error = None
            self._init_time = 0.0
            self._logger = logger
            self._init_lock = threading.Lock()
            self._cleanup_handlers = []
            self._init_thread = None
            self._init_timeout = 10.0  # seconds
            
            # Connect cleanup
            self.destroyed.connect(self._on_destroyed)
            self._logger.debug(f"Created LazyWidget instance: {id(self)}")
            self.hide()
            
        except Exception as e:
            self._logger.error(f"Error initializing LazyWidget: {str(e)}", exc_info=True)
            raise
            
    def add_cleanup_handler(self, handler: Callable[[], None]):
        """Add cleanup handler to be called on widget destruction"""
        if not callable(handler):
            raise ValueError("Cleanup handler must be callable")
        self._cleanup_handlers.append(handler)
        
    def _on_destroyed(self):
        """Handle widget destruction"""
        try:
            # Run cleanup handlers
            for handler in self._cleanup_handlers:
                try:
                    handler()
                except Exception as e:
                    self._logger.error(
                        f"Error in cleanup handler: {str(e)}",
                        exc_info=True
                    )
                    
            # Clean up initialization thread
            if self._init_thread and self._init_thread.is_alive():
                try:
                    # Try graceful shutdown first
                    self._init_thread.join(timeout=1.0)
                    
                    if self._init_thread.is_alive():
                        self._logger.warning(
                            f"Init thread {id(self._init_thread)} did not terminate gracefully"
                        )
                        # We can't force thread termination in Python, just abandon it
                        self._init_thread = None
                        
                except Exception as e:
                    self._logger.error(
                        f"Error cleaning up init thread: {str(e)}",
                        exc_info=True
                    )
                    
            # Clear thread reference and other resources
            self._init_thread = None
            self._cleanup_handlers.clear()
            self._init_error = None
            
            self._logger.debug(f"LazyWidget {id(self)} destroyed")
            
        except Exception as e:
            self._logger.error(
                f"Error destroying LazyWidget: {str(e)}",
                exc_info=True
            )
            
    def showEvent(self, event: QEvent):
        """Handle show event"""
        try:
            if not self._initialized and not self._init_error:
                # Initialize synchronously before showing
                self._do_initialize()
                if self._init_error:
                    event.ignore()
                    return
            super().showEvent(event)
        except Exception as e:
            self._logger.error(f"Error in show event: {str(e)}", exc_info=True)
            event.ignore()
            
    def _do_initialize(self):
        """Perform widget initialization"""
        try:
            if self._initialized or self._init_error:
                return
                
            start_time = time.time()
            success = False
            
            try:
                # Run initialization directly
                success = self.initialize()
            except Exception as e:
                self._init_error = e
                self._logger.error(
                    f"Error in widget initialization: {str(e)}",
                    exc_info=True
                )
                return
                
            if not success:
                self._init_error = RuntimeError("Initialization returned False")
                return
                
            self._initialized = True
            self._init_time = time.time() - start_time
            self._logger.debug(
                f"Widget {id(self)} initialized in {self._init_time:.2f}s"
            )
            
        except Exception as e:
            self._init_error = e
            self._logger.error(
                f"Error initializing widget {id(self)}: {str(e)}",
                exc_info=True
            )
            
    def initialize(self) -> bool:
        """
        Initialize widget
        
        Returns:
            bool: True if initialization successful
        """
        return True

    def is_initialized(self) -> bool:
        """Check if widget is initialized"""
        return self._initialized

    def get_init_error(self) -> Optional[str]:
        """Get initialization error if any"""
        return self._init_error

    def get_init_time(self) -> float:
        """Get initialization time"""
        return self._init_time

class ComponentLoader:
    """Загрузчик для компонентов (виджетов)"""
    
    def __init__(self):
        self._components: Dict[str, Union[Type[QWidget], Callable[..., QWidget]]] = {}
        self._instances: Dict[str, QWidget] = {}
        self._logger = logger
        self._lock = threading.Lock()
        self._instance_locks: Dict[str, threading.Lock] = {}
        self._logger.debug("ComponentLoader initialized")
        
    def register_component(
            self,
            name: str,
            component: Union[Type[QWidget], Callable[..., QWidget]]
        ):
        """Register component"""
        try:
            with self._lock:
                if name in self._components:
                    raise ValueError(f"Component {name} already registered")
                    
                if not (isinstance(component, type) and issubclass(component, QWidget)) and \
                   not callable(component):
                    raise ValueError("Component must be QWidget class or factory function")
                    
                self._components[name] = component
                self._instance_locks[name] = threading.Lock()
                self._logger.debug(f"Registered component: {name}")
                
        except Exception as e:
            self._logger.error(
                f"Error registering component {name}: {str(e)}",
                exc_info=True
            )
            raise
            
    def get_component(self, name: str, parent=None) -> Optional[QWidget]:
        """Get component instance"""
        if not name:
            raise ValueError("Component name cannot be empty")
            
        try:
            # First acquire the global lock to check/create instance lock
            with self._lock:
                if name not in self._components:
                    raise ValueError(f"Component {name} not registered")
                    
                # Ensure instance lock exists
                if name not in self._instance_locks:
                    self._instance_locks[name] = threading.Lock()
                    
            # Now get the instance with proper locking
            with self._instance_locks[name]:
                try:
                    if name not in self._instances:
                        component = self._components[name]
                        try:
                            instance = component(parent)
                                
                            if not isinstance(instance, QWidget):
                                raise ValueError(
                                    f"Component {name} did not create a QWidget instance"
                                )
                                
                            self._instances[name] = instance
                            
                        except Exception as e:
                            self._logger.error(
                                f"Failed to create instance of {name}: {str(e)}",
                                exc_info=True
                            )
                            raise
                            
                    return self._instances[name]
                    
                except Exception as e:
                    # Clean up on error
                    if name in self._instances:
                        del self._instances[name]
                    raise
                    
        except Exception as e:
            self._logger.error(
                f"Error getting component {name}: {str(e)}",
                exc_info=True
            )
            raise
            
    def clear_cache(self):
        """Clear instance cache"""
        try:
            with self._lock:
                for name, instance in self._instances.items():
                    try:
                        if hasattr(instance, 'cleanup'):
                            instance.cleanup()
                        instance.deleteLater()
                    except Exception as e:
                        self._logger.error(
                            f"Error cleaning up instance {name}: {str(e)}",
                            exc_info=True
                        )
                self._instances.clear()
                
        except Exception as e:
            self._logger.error(f"Error clearing cache: {str(e)}", exc_info=True)
            
    def clear(self) -> None:
        """Clear all components and cache"""
        with self._lock:
            self._components.clear()
            self._instances.clear()
            self._instance_locks.clear()

def lazy_property(fn):
    """
    Decorator for lazy property initialization.
    
    The property value is computed on first access and then cached.
    
    Args:
        fn: Property getter function
        
    Returns:
        property: Lazy property descriptor
    """
    attr_name = '_lazy_' + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
        
    return _lazy_property

def lazy_import(module_path: str, timeout: float = 10.0) -> ModuleProxy:
    """
    Create proxy for lazy module import
    
    Args:
        module_path: Import path for the module
        timeout: Import timeout in seconds
        
    Returns:
        ModuleProxy: Proxy object for lazy loading
        
    Raises:
        ValueError: If module path is invalid
        ImportTimeoutError: If import times out
        ImportError: If module cannot be imported
    """
    if not module_path:
        raise ValueError("Module path cannot be empty")
        
    try:
        return ModuleProxy(module_path, timeout=timeout)
    except Exception as e:
        logger.error(f"Error creating lazy import for {module_path}: {str(e)}", exc_info=True)
        raise

# Глобальные экземпляры
lazy_loader = LazyLoader()
component_loader = ComponentLoader()
