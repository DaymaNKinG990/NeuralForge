from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QObject
import importlib
import sys
import time
import threading
import logging
from functools import wraps

T = TypeVar('T')

class LazyLoader:
    """Ленивая загрузка модулей и компонентов"""
    
    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}
        self._loading_times: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._logger = logging.getLogger(__name__)
        
    def load_module(self, module_path: str) -> Any:
        """Загрузить модуль при первом обращении"""
        with self._lock:
            if module_path in self._loaded_modules:
                return self._loaded_modules[module_path]
                
            try:
                start_time = time.time()
                module = importlib.import_module(module_path)
                load_time = time.time() - start_time
                
                self._loaded_modules[module_path] = module
                self._loading_times[module_path] = load_time
                
                self._logger.debug(f"Loaded module {module_path} in {load_time:.3f}s")
                return module
            except ImportError as e:
                self._logger.error(f"Error loading module {module_path}: {e}")
                raise
                
    def get_loading_stats(self) -> Dict[str, float]:
        """Получить статистику времени загрузки"""
        return dict(self._loading_times)

class LazyWidget(QWidget):
    """Базовый класс для виджетов с ленивой инициализацией"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._initialized = False
        self._init_time: Optional[float] = None
        
    def showEvent(self, event):
        """Инициализируем виджет при первом показе"""
        if not self._initialized:
            start_time = time.time()
            self.lazy_init()
            self._init_time = time.time() - start_time
            self._initialized = True
        super().showEvent(event)
        
    def lazy_init(self):
        """Переопределить для инициализации"""
        pass
        
    def get_init_time(self) -> Optional[float]:
        """Получить время инициализации"""
        return self._init_time

def lazy_property(func: Callable[..., T]) -> property:
    """Декоратор для ленивой инициализации свойств"""
    attr_name = f"_lazy_{func.__name__}"
    
    @property
    @wraps(func)
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
        
    return wrapper

class ComponentLoader:
    """Загрузчик UI компонентов"""
    
    def __init__(self):
        self._components: Dict[str, Union[Type[QWidget], Callable[[Optional[QWidget]], QWidget]]] = {}
        self._instances: Dict[str, Dict[QWidget, QWidget]] = {}  
        self._logger = logging.getLogger(__name__)
        
    def register_component(self, name: str, 
                         component: Union[Type[QWidget], Callable[[Optional[QWidget]], QWidget]]) -> None:
        """Зарегистрировать компонент
        
        Args:
            name: Имя компонента
            component: Класс компонента или фабричная функция для его создания
        """
        self._components[name] = component
        
    def get_component(self, name: str, parent: Optional[QWidget] = None) -> Optional[QWidget]:
        """Получить или создать экземпляр компонента
        
        Args:
            name: Имя компонента
            parent: Родительский виджет
            
        Returns:
            Экземпляр компонента или None если компонент не найден
        """
        if name not in self._components:
            self._logger.error(f"Component {name} not registered")
            return None
            
        # Initialize the instances dictionary for this component if it doesn't exist
        if name not in self._instances:
            self._instances[name] = {}
            
        # Use parent as key, None if no parent
        parent_key = parent if parent else None
        
        if parent_key not in self._instances[name]:
            try:
                component = self._components[name]
                if callable(component):
                    if isinstance(component, type):
                        # Если component - это класс
                        instance = component(parent)
                    else:
                        # Если component - это фабричная функция
                        instance = component(parent)
                else:
                    raise ValueError(f"Component {name} is not callable")
                    
                self._instances[name][parent_key] = instance
                self._logger.debug(f"Created component {name} with parent {parent}")
                
            except Exception as e:
                self._logger.error(f"Error creating component {name}: {e}", exc_info=True)
                return None
                
        return self._instances[name][parent_key]
        
    def clear_cache(self) -> None:
        """Очистить кэш экземпляров"""
        self._instances.clear()

class ModuleProxy:
    """Прокси для ленивой загрузки модулей"""
    
    def __init__(self, module_path: str):
        self._module_path = module_path
        self._module = None
        
    def __getattr__(self, name: str) -> Any:
        if self._module is None:
            self._module = LazyLoader().load_module(self._module_path)
        return getattr(self._module, name)

def lazy_import(module_path: str) -> ModuleProxy:
    """Создать прокси для ленивой загрузки модуля"""
    return ModuleProxy(module_path)

# Глобальные экземпляры
lazy_loader = LazyLoader()
component_loader = ComponentLoader()
