"""
Тесты для модуля lazy_loading
"""
import sys
import time
import logging
import threading
import pytest
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import QTimer, Qt, QEvent

from src.utils.lazy_loading import (
    LazyLoader, LazyWidget, lazy_property,
    ComponentLoader, ModuleProxy, lazy_import
)

# Настройка логирования для тестов
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Создаем форматтер для логов
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Добавляем обработчик для вывода в файл
file_handler = logging.FileHandler('test_lazy_loading.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Добавляем обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

@pytest.fixture(scope='session')
def qapp():
    """Фикстура для создания QApplication"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    app.processEvents()  # Обрабатываем оставшиеся события

@pytest.fixture
def process_events():
    """Фикстура для обработки событий Qt"""
    def _process_events():
        QApplication.processEvents()
    return _process_events

@pytest.fixture
def cleanup_widgets():
    """Фикстура для очистки виджетов после теста"""
    widgets = []
    yield widgets
    for widget in widgets:
        if widget and not widget.parent():  # Проверяем только виджеты без родителя
            widget.hide()  # Скрываем виджет перед удалением
            widget.setParent(None)  # Отвязываем от родителя
            widget.deleteLater()  # Планируем удаление
            QApplication.processEvents()  # Обрабатываем события

@pytest.fixture
def component_loader():
    """Фикстура для создания нового ComponentLoader"""
    loader = ComponentLoader()
    yield loader
    loader.clear()  # Очищаем все компоненты после теста

# Вспомогательные классы для тестов
class _DummyWidget(LazyWidget):
    """Тестовый виджет для проверки ленивой инициализации"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_called = False
        self.label = None
        logger.debug(f"Created _DummyWidget instance: {id(self)}")
        
    def initialize(self) -> bool:
        logger.info(f"Initializing _DummyWidget: {id(self)}")
        try:
            self.label = QLabel("Initialized", self)
            self.init_called = True
            return True
        except Exception as e:
            logger.error(f"Error initializing _DummyWidget: {str(e)}", exc_info=True)
            return False

class _ErrorWidget(LazyWidget):
    """Виджет с ошибкой при инициализации"""
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug(f"Created _ErrorWidget instance: {id(self)}")
        
    def initialize(self) -> bool:
        logger.error(f"_ErrorWidget {id(self)} raising test error")
        raise ValueError("Test error")

class _FailingWidget(LazyWidget):
    """Виджет с неудачной инициализацией"""
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug(f"Created _FailingWidget instance: {id(self)}")
        
    def initialize(self) -> bool:
        logger.warning(f"_FailingWidget {id(self)} returning False")
        time.sleep(0.01)  # Добавляем задержку для проверки времени инициализации
        return False

class _AsyncInitWidget(LazyWidget):
    """Виджет с асинхронной инициализацией"""
    def __init__(self, delay=0.1, parent=None):
        super().__init__(parent)
        self.delay = delay
        self.init_called = False
        logger.debug(f"Created _AsyncInitWidget instance: {id(self)}, delay={delay}")
        
    def initialize(self) -> bool:
        logger.info(f"Starting async initialization of widget {id(self)} with delay {self.delay}")
        time.sleep(self.delay)
        self.init_called = True
        logger.info(f"Completed async initialization of widget {id(self)}")
        return True

class _RecursiveWidget(LazyWidget):
    """Виджет с рекурсивной инициализацией других виджетов"""
    def __init__(self, child_count=2, parent=None):
        super().__init__(parent)
        self.child_count = child_count
        self.children = []
        logger.debug(f"Created _RecursiveWidget instance: {id(self)}, child_count={child_count}")
        
    def initialize(self) -> bool:
        logger.info(f"Starting recursive initialization of widget {id(self)} with {self.child_count} children")
        try:
            # Create and initialize all child widgets first
            for i in range(self.child_count):
                logger.debug(f"Creating child widget {i+1}/{self.child_count}")
                child = _DummyWidget(self)
                child.hide()  # Ensure it's hidden
                
                # Initialize the child
                child._do_initialize()
                if child.get_init_error():
                    logger.error(f"Child widget {id(child)} failed to initialize: {child.get_init_error()}")
                    return False
                    
                self.children.append(child)
                
            logger.info(f"Completed recursive initialization of widget {id(self)}")
            return True
            
        except Exception as e:
            logger.error(f"Error in recursive initialization: {str(e)}", exc_info=True)
            return False
            
    def showEvent(self, event: QEvent):
        """Override showEvent to show children after parent is shown"""
        try:
            super().showEvent(event)
            # Only show children if we're being shown
            if event.isAccepted() and self.isVisible():
                for child in self.children:
                    child.show()
        except Exception as e:
            logger.error(f"Error in recursive show event: {str(e)}", exc_info=True)
            event.ignore()

# Тесты
def test_module_loading_error():
    """Тест обработки ошибки при загрузке несуществующего модуля"""
    loader = LazyLoader()
    
    with pytest.raises(ImportError) as exc_info:
        loader.load_module('nonexistent_module')
    
    assert "No module named 'nonexistent_module'" in str(exc_info.value)
    assert not loader.is_loaded('nonexistent_module')

def test_lazy_module_loading():
    """Тест ленивой загрузки модулей"""
    loader = LazyLoader()
    
    # Загружаем модуль и замеряем время
    start_time = time.time()
    module = loader.load_module('os')
    load_time = time.time() - start_time
    
    # Проверяем загруженный модуль
    assert isinstance(module, ModuleProxy)
    assert module._module is not None
    assert hasattr(module, 'path')
    
    # Проверяем статистику загрузки
    stats = loader.get_load_stats()
    assert 'os' in stats
    assert stats['os'] >= 0  # Время загрузки должно быть неотрицательным

def test_lazy_widget_initialization(qapp, process_events, cleanup_widgets):
    """Test lazy widget initialization"""
    logger.info("Starting test_lazy_widget_initialization")
    
    # Создаем виджет
    widget = _DummyWidget()
    cleanup_widgets.append(widget)
    logger.debug(f"Created test widget: {id(widget)}")
    
    # Проверяем начальное состояние
    assert not widget.is_initialized()
    assert not widget.init_called
    assert widget.get_init_time() == 0.0
    logger.debug("Initial widget state verified")
    
    # Показываем виджет
    logger.info("Showing widget")
    widget.show()
    process_events()
    
    # Проверяем состояние после инициализации
    assert widget.is_initialized()
    assert widget.init_called
    assert widget.get_init_time() > 0
    logger.debug(f"Widget initialized successfully, init_time: {widget.get_init_time()}")
    
    logger.info("Completed test_lazy_widget_initialization")

def test_concurrent_initialization(qapp, process_events, cleanup_widgets):
    """Тест одновременной инициализации нескольких виджетов"""
    logger.info("Starting test_concurrent_initialization")
    
    # Создаем виджеты
    widgets = [_AsyncInitWidget(delay=0.05) for _ in range(3)]
    logger.debug(f"Created {len(widgets)} async widgets")
    
    for widget in widgets:
        cleanup_widgets.append(widget)
        widget.show()
        logger.debug(f"Showed widget {id(widget)}")
    
    # Проверяем инициализацию
    logger.info("Processing events for initialization")
    process_events()
    time.sleep(0.1)
    process_events()
    
    # Проверяем результаты
    for i, widget in enumerate(widgets):
        logger.debug(f"Checking widget {i+1}/{len(widgets)}: {id(widget)}")
        assert widget.is_initialized()
        assert widget.init_called
        assert widget.get_init_time() > 0
        assert widget.get_init_error() is None
        logger.debug(f"Widget {i+1} initialization verified, init_time: {widget.get_init_time()}")
    
    logger.info("Completed test_concurrent_initialization")

def test_lazy_widget_initialization_error(qapp, process_events, cleanup_widgets):
    """Test widget initialization error"""
    logger.info("Starting test_lazy_widget_initialization_error")
    
    # Создаем виджет
    widget = _ErrorWidget()
    cleanup_widgets.append(widget)
    logger.debug(f"Created test widget: {id(widget)}")
    
    # Проверяем начальное состояние
    assert not widget.is_initialized()
    assert widget.get_init_time() == 0.0
    assert widget.get_init_error() is None
    logger.debug("Initial widget state verified")
    
    # Пытаемся инициализировать виджет
    logger.info("Attempting widget initialization")
    success = widget._do_initialize()
    process_events()
    
    # Проверяем состояние после ошибки
    assert not success, "Initialization should fail"
    assert not widget.is_initialized()
    assert isinstance(widget.get_init_error(), ValueError)
    assert str(widget.get_init_error()) == "Test error"
    assert widget.get_init_time() > 0
    logger.debug("Error state verified")
    
    logger.info("Completed test_lazy_widget_initialization_error")

def test_lazy_widget_initialization_failure(qapp, process_events, cleanup_widgets):
    """Тест неудачной инициализации виджета"""
    logger.info("Starting test_lazy_widget_initialization_failure")
    
    class _FailingWidget(LazyWidget):
        def initialize(self):
            logger.warning(f"{self.__class__.__name__} returning False")
            time.sleep(0.01)  # Добавляем задержку для проверки времени инициализации
            return False
    
    # Создаем виджет
    widget = _FailingWidget()
    cleanup_widgets.append(widget)
    logger.debug(f"Created test widget: {id(widget)}")
    
    # Проверяем начальное состояние
    assert not widget.is_initialized()
    assert widget.get_init_error() is None
    assert widget.get_init_time() == 0.0
    logger.debug("Initial widget state verified")
    
    # Пытаемся инициализировать виджет
    logger.info("Attempting widget initialization")
    success = widget._do_initialize()
    process_events()
    
    # Проверяем результаты
    assert not success, "Initialization should fail"
    assert not widget.is_initialized()
    assert widget.get_init_error() is None  # Нет ошибки, просто неудачная инициализация
    assert widget.get_init_time() > 0, f"Init time should be > 0, got {widget.get_init_time()}"
    logger.info("Test completed successfully")

def test_component_loader(qapp, process_events, cleanup_widgets, component_loader):
    """Test component loader"""
    logger.info("Starting test_component_loader")
    
    # Регистрируем тестовый компонент
    component_loader.register_component("test", _DummyWidget)
    logger.debug("Registered test component")
    
    # Создаем экземпляр
    widget = component_loader.get_component("test")
    cleanup_widgets.append(widget)
    logger.debug(f"Created test component instance: {id(widget)}")
    
    # Проверяем кэширование
    widget2 = component_loader.get_component("test")
    assert widget2 is widget
    logger.debug("Component caching works correctly")
    
    # Проверяем очистку кэша
    component_loader.clear_cache()
    logger.debug("Cleared component loader cache")
    widget3 = component_loader.get_component("test")
    assert widget3 is not widget
    logger.debug("Component loader cache cleared correctly")
    
    logger.info("Completed test_component_loader")

def test_component_loader_factory(qapp, process_events, cleanup_widgets, component_loader):
    """Test component loader with factory function"""
    logger.info("Starting test_component_loader_factory")
    
    def factory(parent=None):
        return _DummyWidget(parent)
    
    component_loader.register_component("factory_test", factory)
    logger.debug("Registered factory test component")
    
    widget = component_loader.get_component("factory_test")
    cleanup_widgets.append(widget)
    logger.debug(f"Created factory test component instance: {id(widget)}")
    
    assert isinstance(widget, _DummyWidget)
    logger.debug("Factory test component created correctly")
    
    logger.info("Completed test_component_loader_factory")

def test_component_loader_clear_cache(qapp, process_events, cleanup_widgets, component_loader):
    """Test clearing component loader cache"""
    logger.info("Starting test_component_loader_clear_cache")
    
    component_loader.register_component("test", _DummyWidget)
    logger.debug("Registered test component")
    
    widget1 = component_loader.get_component("test")
    cleanup_widgets.append(widget1)
    logger.debug(f"Created test component instance 1: {id(widget1)}")
    
    component_loader.clear_cache()
    logger.debug("Cleared component loader cache")
    widget2 = component_loader.get_component("test")
    cleanup_widgets.append(widget2)
    logger.debug(f"Created test component instance 2: {id(widget2)}")
    
    # Should be different instances after cache clear
    assert widget1 is not widget2
    logger.debug("Component loader cache cleared correctly")
    
    logger.info("Completed test_component_loader_clear_cache")

def test_lazy_property_decorator():
    """Test lazy property decorator"""
    logger.info("Starting test_lazy_property_decorator")
    
    class TestClass:
        def __init__(self):
            self.init_count = 0
            
        @lazy_property
        def lazy_value(self):
            logger.debug("Initializing lazy_value")
            self.init_count += 1
            return 42
    
    obj = TestClass()
    logger.debug("Created test object")
    
    # Access property
    logger.info("Accessing lazy_value")
    assert obj.lazy_value == 42
    assert obj.init_count == 1
    logger.debug("Lazy_value accessed correctly")
    
    # Access again - should use cached value
    logger.info("Accessing lazy_value again")
    assert obj.lazy_value == 42
    assert obj.init_count == 1
    logger.debug("Lazy_value cached correctly")
    
    logger.info("Completed test_lazy_property_decorator")

def test_module_proxy():
    """Test module proxy functionality"""
    logger.info("Starting test_module_proxy")
    
    # Create proxy for json module
    json_proxy = ModuleProxy("json")
    logger.debug("Created json module proxy")
    
    # Access module through proxy
    logger.info("Accessing json module through proxy")
    assert json_proxy.dumps({"test": 123}) == '{"test": 123}'
    logger.debug("Json module accessed correctly")
    
    # Test caching
    assert json_proxy._module is not None
    logger.debug("Json module cached correctly")
    
    logger.info("Completed test_module_proxy")

def test_lazy_import():
    """Test lazy import functionality"""
    logger.info("Starting test_lazy_import")
    
    json = lazy_import("json")
    logger.debug("Created json lazy import")
    
    # Module should not be loaded yet
    assert isinstance(json, ModuleProxy)
    assert json._module is None
    logger.debug("Json module not loaded yet")
    
    # Access should trigger load
    logger.info("Accessing json module")
    assert json.dumps({"test": 123}) == '{"test": 123}'
    assert json._module is not None
    logger.debug("Json module loaded correctly")
    
    logger.info("Completed test_lazy_import")

def test_thread_safety():
    """Тест потокобезопасности загрузки модулей"""
    logger.info("Starting test_thread_safety")
    
    loader = LazyLoader()
    loader.clear()  # Очищаем кэш перед тестом
    
    threads = []
    results = []
    
    def load_module():
        try:
            start_time = time.time()
            module = loader.load_module('json')
            load_time = time.time() - start_time
            results.append((module, load_time))
        except Exception as e:
            results.append(e)
    
    # Создаем несколько потоков для загрузки одного и того же модуля
    for _ in range(5):
        thread = threading.Thread(target=load_module)
        threads.append(thread)
    
    logger.debug(f"Created {len(threads)} threads to load json module")
    
    # Запускаем все потоки
    for thread in threads:
        thread.start()
    
    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()
    
    # Проверяем результаты
    assert all(isinstance(r, tuple) for r in results)
    modules, times = zip(*results)
    
    # Проверяем, что все потоки получили один и тот же объект модуля
    assert all(m is modules[0] for m in modules)
    
    # Проверяем время загрузки
    total_time = sum(times)
    assert total_time > 0

def test_recursive_widget_initialization(qapp, process_events, cleanup_widgets):
    """Тест рекурсивной инициализации виджетов"""
    logger.info("Starting test_recursive_widget_initialization")
    
    # Create widget but don't show it yet
    widget = _RecursiveWidget(child_count=3)
    cleanup_widgets.append(widget)
    logger.debug(f"Created recursive widget: {id(widget)}")
    
    # Initialize widget first
    widget._do_initialize()
    assert not widget.get_init_error(), f"Initialization failed: {widget.get_init_error()}"
    assert widget.is_initialized()
    assert len(widget.children) == 3
    logger.debug("Recursive widget initialized correctly")
    
    # Now show the widget
    widget.show()
    process_events()
    
    # Verify all children are shown and initialized
    for child in widget.children:
        assert child.isVisible()
        assert child.is_initialized()
        assert child.init_called
        assert child.get_init_error() is None
        assert child.label is not None
        assert child.label.text() == "Initialized"
        logger.debug(f"Child widget {id(child)} verified")
    
    logger.info("Completed test_recursive_widget_initialization")

def test_widget_reinitialization(qapp, process_events, cleanup_widgets):
    """Тест повторной инициализации виджета"""
    logger.info("Starting test_widget_reinitialization")
    
    widget = _DummyWidget()
    cleanup_widgets.append(widget)
    logger.debug(f"Created test widget: {id(widget)}")
    
    # Первая инициализация
    logger.info("Initializing widget")
    widget.show()
    process_events()
    assert widget.is_initialized()
    init_time_1 = widget.get_init_time()
    logger.debug(f"Widget initialized, init_time: {init_time_1}")
    
    # Скрываем и снова показываем виджет
    logger.info("Hiding and showing widget again")
    widget.hide()
    widget.show()
    process_events()
    
    # Проверяем, что повторной инициализации не произошло
    assert widget.is_initialized()
    assert widget.get_init_time() == init_time_1
    logger.debug("Widget not reinitialized")
    
    logger.info("Completed test_widget_reinitialization")

def test_component_loader_error_handling(qapp, process_events, cleanup_widgets, component_loader):
    """Тест обработки ошибок в ComponentLoader"""
    logger.info("Starting test_component_loader_error_handling")
    
    # Регистрируем компонент с ошибкой
    component_loader.register_component("error_widget", _ErrorWidget)
    logger.debug("Registered error widget component")
    
    # Получаем компонент и пытаемся его инициализировать
    widget = component_loader.get_component("error_widget")
    cleanup_widgets.append(widget)
    
    # Пытаемся инициализировать виджет
    success = widget._do_initialize()
    process_events()
    
    # Проверяем результаты
    assert not success, "Initialization should fail"
    assert not widget.is_initialized()
    assert isinstance(widget.get_init_error(), ValueError)
    assert str(widget.get_init_error()) == "Test error"
    
    # Проверяем очистку кэша после ошибки
    assert "error_widget" not in component_loader._instances
    logger.debug("Component loader cache cleared after error")
    
    logger.info("Completed test_component_loader_error_handling")

def test_lazy_property_with_error():
    """Тест декоратора lazy_property с ошибкой"""
    logger.info("Starting test_lazy_property_with_error")
    
    class TestClass:
        @lazy_property
        def error_property(self):
            logger.debug("Initializing error_property")
            raise ValueError("Property error")
    
    obj = TestClass()
    logger.debug("Created test object")
    
    with pytest.raises(ValueError):
        _ = obj.error_property
    
    logger.debug("Lazy property error handled correctly")
    
    logger.info("Completed test_lazy_property_with_error")

def test_module_proxy_invalid_attribute():
    """Тест доступа к несуществующему атрибуту через ModuleProxy"""
    logger.info("Starting test_module_proxy_invalid_attribute")
    
    proxy = ModuleProxy("os")
    logger.debug("Created os module proxy")
    
    with pytest.raises(AttributeError):
        _ = proxy.nonexistent_attribute
    
    logger.debug("Module proxy invalid attribute handled correctly")
    
    logger.info("Completed test_module_proxy_invalid_attribute")

def test_concurrent_module_loading(qapp, process_events):
    """Тест параллельной загрузки модулей"""
    loader = LazyLoader()
    threads = []
    results = []
    
    def load_module():
        try:
            start_time = time.time()
            module = loader.load_module('os')
            load_time = time.time() - start_time
            results.append((module, load_time))
        except Exception as e:
            results.append(e)
    
    # Создаем несколько потоков для загрузки одного и того же модуля
    for _ in range(5):
        thread = threading.Thread(target=load_module)
        threads.append(thread)
        thread.start()
    
    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()
    
    # Проверяем результаты
    assert all(isinstance(r, tuple) for r in results)
    modules, times = zip(*results)
    
    # Проверяем, что все потоки получили один и тот же объект модуля
    assert all(m is modules[0] for m in modules)
    
    # Проверяем время загрузки
    total_time = sum(times)
    assert total_time > 0

def test_concurrent_widget_initialization(qapp, process_events, cleanup_widgets):
    """Тест параллельной инициализации виджетов"""
    class TestWidget(LazyWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._init_count = 0
            self._init_complete = threading.Event()
        
        def initialize(self):
            self._init_count += 1
            time.sleep(0.01)  # Короткая задержка для имитации работы
            self._init_complete.set()
            return True
        
        def get_init_count(self):
            return self._init_count
        
        def wait_for_init(self, timeout=1.0):
            return self._init_complete.wait(timeout)
    
    widget = TestWidget()
    cleanup_widgets.append(widget)
    widget.hide()  # Скрываем виджет, чтобы не открывалось окно
    
    threads = []
    
    def init_widget():
        try:
            widget._do_initialize()  # Вызываем напрямую _do_initialize вместо show()
            process_events()
        except Exception as e:
            logger.error(f"Error in thread: {str(e)}", exc_info=True)
    
    # Создаем несколько потоков для инициализации виджета
    for _ in range(5):
        thread = threading.Thread(target=init_widget)
        threads.append(thread)
        thread.start()
    
    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()
    
    # Ждем завершения инициализации
    assert widget.wait_for_init(), "Widget initialization timed out"
    
    # Проверяем, что инициализация произошла только один раз
    assert widget.get_init_count() == 1, f"Widget was initialized {widget.get_init_count()} times instead of once"
    assert widget.is_initialized()
    assert widget.get_init_error() is None

def test_widget_initialization_error(qapp, process_events, cleanup_widgets):
    """Тест обработки ошибок при инициализации виджета"""
    class ErrorWidget(LazyWidget):
        def initialize(self):
            logger.error(f"{self.__class__.__name__} raising test error")
            raise ValueError("Test error")
    
    widget = ErrorWidget()
    cleanup_widgets.append(widget)
    widget.hide()  # Скрываем виджет, чтобы не открывалось окно
    
    # Пытаемся инициализировать виджет напрямую
    success = widget._do_initialize()
    process_events()
    
    # Проверяем состояние виджета
    assert not success, "Initialization should return False on error"
    assert not widget.is_initialized()
    assert isinstance(widget.get_init_error(), ValueError)
    assert str(widget.get_init_error()) == "Test error"

def test_widget_initialization_failure(qapp, process_events, cleanup_widgets):
    """Тест обработки неудачной инициализации виджета"""
    class FailureWidget(LazyWidget):
        def initialize(self):
            logger.warning(f"{self.__class__.__name__} returning False")
            return False
    
    widget = FailureWidget()
    cleanup_widgets.append(widget)
    widget.hide()  # Скрываем виджет, чтобы не открывалось окно
    
    # Пытаемся инициализировать виджет напрямую
    success = widget._do_initialize()
    process_events()
    
    # Проверяем состояние виджета
    assert not success, "Initialization should return False"
    assert not widget.is_initialized()
    assert widget.get_init_error() is None

def test_widget_reinitialization(qapp, process_events, cleanup_widgets):
    """Тест повторной инициализации виджета после ошибки"""
    class RetryWidget(LazyWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.attempt = 0
        
        def initialize(self):
            self.attempt += 1
            if self.attempt == 1:
                logger.info(f"[TEST] {self.__class__.__name__}: First attempt intentionally fails (attempt {self.attempt})")
                raise ValueError("First attempt fails (expected test behavior)")
            logger.info(f"[TEST] {self.__class__.__name__}: Second attempt succeeds (attempt {self.attempt})")
            return True
    
    logger.info("[TEST] Starting widget reinitialization test")
    widget = RetryWidget()
    cleanup_widgets.append(widget)
    widget.hide()  # Скрываем виджет, чтобы не открывалось окно
    
    # Первая попытка должна завершиться ошибкой
    logger.info("[TEST] Attempting first initialization (expected to fail)")
    success = widget._do_initialize()
    process_events()
    
    assert not success, "First initialization should fail"
    assert not widget.is_initialized()
    assert isinstance(widget.get_init_error(), ValueError)
    assert "expected test behavior" in str(widget.get_init_error())
    logger.info("[TEST] First initialization failed as expected")
    
    # Вторая попытка должна быть успешной
    logger.info("[TEST] Attempting second initialization (expected to succeed)")
    success = widget._do_initialize()
    process_events()
    
    assert success, "Second initialization should succeed"
    assert widget.is_initialized()
    assert widget.get_init_error() is None
    assert widget.attempt == 2
    logger.info("[TEST] Second initialization succeeded as expected")

def test_component_loader_error_handling(qapp, process_events, cleanup_widgets, component_loader):
    """Тест обработки ошибок в ComponentLoader"""
    logger.info("Starting test_component_loader_error_handling")
    
    # Регистрируем компонент с ошибкой
    component_loader.register_component("error_widget", _ErrorWidget)
    logger.debug("Registered error widget component")
    
    # Пытаемся получить компонент
    with pytest.raises(ValueError):
        widget = component_loader.get_component("error_widget")
        cleanup_widgets.append(widget)
        widget.show()
        process_events()
    
    # Проверяем очистку кэша после ошибки
    assert "error_widget" not in component_loader._instances
    logger.debug("Component loader cache cleared after error")
    
    logger.info("Completed test_component_loader_error_handling")

def test_lazy_property_with_error():
    """Тест декоратора lazy_property с ошибкой"""
    logger.info("Starting test_lazy_property_with_error")
    
    class TestClass:
        @lazy_property
        def error_property(self):
            logger.debug("Initializing error_property")
            raise ValueError("Property error")
    
    obj = TestClass()
    logger.debug("Created test object")
    
    with pytest.raises(ValueError):
        _ = obj.error_property
    
    logger.debug("Lazy property error handled correctly")
    
    logger.info("Completed test_lazy_property_with_error")

def test_module_proxy_invalid_attribute():
    """Тест доступа к несуществующему атрибуту через ModuleProxy"""
    logger.info("Starting test_module_proxy_invalid_attribute")
    
    proxy = ModuleProxy("os")
    logger.debug("Created os module proxy")
    
    with pytest.raises(AttributeError):
        _ = proxy.nonexistent_attribute
    
    logger.debug("Module proxy invalid attribute handled correctly")
    
    logger.info("Completed test_module_proxy_invalid_attribute")

def test_concurrent_module_loading(qapp, process_events):
    """Тест параллельной загрузки модулей"""
    loader = LazyLoader()
    threads = []
    results = []
    
    def load_module():
        try:
            start_time = time.time()
            module = loader.load_module('os')
            load_time = time.time() - start_time
            results.append((module, load_time))
        except Exception as e:
            results.append(e)
    
    # Создаем несколько потоков для загрузки одного и того же модуля
    for _ in range(5):
        thread = threading.Thread(target=load_module)
        threads.append(thread)
        thread.start()
    
    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()
    
    # Проверяем результаты
    assert all(isinstance(r, tuple) for r in results)
    modules, times = zip(*results)
    
    # Проверяем, что все потоки получили один и тот же объект модуля
    assert all(m is modules[0] for m in modules)
    
    # Проверяем время загрузки
    total_time = sum(times)
    assert total_time > 0

def test_concurrent_widget_initialization(qapp, process_events, cleanup_widgets):
    """Тест параллельной инициализации виджетов"""
    class TestWidget(LazyWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._init_count = 0
            self._init_complete = threading.Event()
        
        def initialize(self):
            self._init_count += 1
            time.sleep(0.01)  # Короткая задержка для имитации работы
            self._init_complete.set()
            return True
        
        def get_init_count(self):
            return self._init_count
        
        def wait_for_init(self, timeout=1.0):
            return self._init_complete.wait(timeout)
    
    widget = TestWidget()
    cleanup_widgets.append(widget)
    widget.hide()  # Скрываем виджет, чтобы не открывалось окно
    
    threads = []
    
    def init_widget():
        try:
            widget._do_initialize()  # Вызываем напрямую _do_initialize вместо show()
            process_events()
        except Exception as e:
            logger.error(f"Error in thread: {str(e)}", exc_info=True)
    
    # Создаем несколько потоков для инициализации виджета
    for _ in range(5):
        thread = threading.Thread(target=init_widget)
        threads.append(thread)
        thread.start()
    
    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()
    
    # Ждем завершения инициализации
    assert widget.wait_for_init(), "Widget initialization timed out"
    
    # Проверяем, что инициализация произошла только один раз
    assert widget.get_init_count() == 1, f"Widget was initialized {widget.get_init_count()} times instead of once"
    assert widget.is_initialized()
    assert widget.get_init_error() is None
