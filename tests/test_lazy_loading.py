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
    ComponentLoader, ModuleProxy, lazy_import,
    LoadPriority,
    ComponentMetadata,
    ResourceManager,
    PreloadManager,
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
        logger.debug("Creating new QApplication")
        app = QApplication(sys.argv)
    yield app
    app.processEvents()  # Обрабатываем оставшиеся события

@pytest.fixture
def process_events():
    """Фикстура для обработки событий Qt"""
    def _process():
        logger.debug("Processing Qt events")
        QApplication.processEvents()
    yield _process

@pytest.fixture
def cleanup_widgets():
    """Фикстура для очистки виджетов после теста"""
    widgets = []
    yield widgets
    logger.debug(f"Cleaning up {len(widgets)} widgets")
    for widget in widgets:
        try:
            if hasattr(widget, 'cleanup'):
                widget.cleanup()
            if not widget.isHidden():
                widget.hide()
            widget.deleteLater()
        except Exception as e:
            logger.error(f"Error cleaning up widget: {str(e)}")

# Вспомогательные классы для тестов
class _DummyWidget(LazyWidget):
    """Тестовый виджет для проверки ленивой инициализации"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_called = False
        self.label = None
        logger.debug(f"Created _DummyWidget instance: {id(self)}")
        
    def initialize(self) -> bool:
        logger.debug(f"Initializing _DummyWidget {id(self)}")
        self.init_called = True
        self.label = QLabel("Initialized", self)
        time.sleep(0.1)  # Имитация долгой инициализации
        logger.debug(f"_DummyWidget {id(self)} initialization complete")
        return True

class _ErrorWidget(LazyWidget):
    """Виджет с ошибкой при инициализации"""
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug(f"Created _ErrorWidget instance: {id(self)}")
        
    def initialize(self) -> bool:
        logger.debug(f"Initializing _ErrorWidget {id(self)} (will raise error)")
        raise ValueError("Test error")

class _FailingWidget(LazyWidget):
    """Виджет с неудачной инициализацией"""
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug(f"Created _FailingWidget instance: {id(self)}")
        
    def initialize(self) -> bool:
        logger.debug(f"Initializing _FailingWidget {id(self)} (will return False)")
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
    logger.info("Starting test_module_loading_error")
    
    loader = LazyLoader()
    
    with pytest.raises(ImportError) as exc_info:
        loader.load_module('nonexistent_module')
    
    assert "No module named 'nonexistent_module'" in str(exc_info.value)
    assert not loader.is_loaded('nonexistent_module')

def test_lazy_module_loading():
    """Тест ленивой загрузки модулей"""
    logger.info("Starting test_lazy_module_loading")
    
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
    
    # Create widget
    widget = _DummyWidget()
    cleanup_widgets.append(widget)
    widget.hide()
    
    # Check initial state
    assert not widget.init_called
    assert not widget.is_initialized()
    assert widget.get_init_error() is None
    
    # Initialize
    logger.debug("Attempting widget initialization")
    success = widget._do_initialize()
    process_events()
    
    # Check final state
    assert success, "Initialization should succeed"
    assert widget.init_called, "Initialize method should be called"
    assert widget.is_initialized(), "Widget should be marked as initialized"
    assert widget.get_init_error() is None, "No error should be set"
    assert widget.get_init_time() > 0, "Init time should be recorded"
    
    logger.info("test_lazy_widget_initialization completed successfully")

def test_lazy_widget_initialization_error(qapp, process_events, cleanup_widgets):
    """Test widget initialization error"""
    logger.info("Starting test_lazy_widget_initialization_error")
    
    # Create widget
    widget = _ErrorWidget()
    cleanup_widgets.append(widget)
    widget.hide()
    
    # Check initial state
    assert not widget.is_initialized()
    assert widget.get_init_error() is None
    
    # Try to initialize
    logger.debug("Attempting widget initialization (expecting error)")
    success = widget._do_initialize()
    process_events()
    
    # Check error state
    assert not success, "Initialization should fail"
    assert not widget.is_initialized()
    assert isinstance(widget.get_init_error(), ValueError)
    assert str(widget.get_init_error()) == "Test error"
    
    logger.info("test_lazy_widget_initialization_error completed successfully")

def test_lazy_widget_initialization_failure(qapp, process_events, cleanup_widgets):
    """Test widget initialization failure"""
    logger.info("Starting test_lazy_widget_initialization_failure")
    
    # Create widget
    widget = _FailingWidget()
    cleanup_widgets.append(widget)
    widget.hide()
    
    # Check initial state
    assert not widget.is_initialized()
    assert widget.get_init_error() is None
    
    # Try to initialize
    logger.debug("Attempting widget initialization (expecting failure)")
    success = widget._do_initialize()
    process_events()
    
    # Check failure state
    assert not success, "Initialization should fail"
    assert not widget.is_initialized()
    assert isinstance(widget.get_init_error(), RuntimeError)
    assert "Widget initialization returned False" in str(widget.get_init_error())
    
    logger.info("test_lazy_widget_initialization_failure completed successfully")

def test_concurrent_widget_initialization(qapp, process_events, cleanup_widgets):
    """Test concurrent widget initialization"""
    logger.info("Starting test_concurrent_widget_initialization")
    
    class TestWidget(LazyWidget):
        def initialize(self):
            logger.debug(f"Initializing TestWidget {id(self)}")
            time.sleep(0.1)  # Simulate work
            logger.debug(f"TestWidget {id(self)} initialization complete")
            return True
    
    # Create widgets
    widgets = []
    for i in range(3):
        widget = TestWidget()
        widgets.append(widget)
        cleanup_widgets.append(widget)
        widget.hide()
    
    # Initialize concurrently
    logger.debug("Starting concurrent initialization")
    threads = []
    for widget in widgets:
        thread = threading.Thread(target=widget._do_initialize)
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    logger.debug("Waiting for initialization to complete")
    for thread in threads:
        thread.join(timeout=5.0)
    process_events()
    
    # Verify all widgets initialized
    for widget in widgets:
        logger.debug(f"Checking widget {id(widget)} initialization status")
        assert widget.wait_for_init(), "Widget initialization timed out"
        assert widget.is_initialized(), "Widget should be initialized"
        assert widget.get_init_error() is None, "No error should be present"
    
    logger.info("test_concurrent_widget_initialization completed successfully")

def test_module_loading_error():
    """Test module loading error"""
    logger.info("Starting test_module_loading_error")
    
    # Try to load non-existent module
    logger.debug("Attempting to load non-existent module")
    with pytest.raises(ImportError) as exc_info:
        module = lazy_import("nonexistent_module")
        _ = module.some_attribute  # This should trigger the import
    
    assert "No module named" in str(exc_info.value)
    logger.info("test_module_loading_error completed successfully")

def test_component_loader_error_handling(qapp, process_events, cleanup_widgets, component_loader):
    """Test error handling in ComponentLoader"""
    logger.info("Starting test_component_loader_error_handling")
    
    # Try to register invalid component
    logger.debug("Attempting to register None component")
    with pytest.raises(ValueError) as exc_info:
        component_loader.register_component("test", None)
    assert "Component cannot be None" in str(exc_info.value)
    
    # Try to get non-existent component
    logger.debug("Attempting to get non-existent component")
    with pytest.raises(ValueError) as exc_info:
        component_loader.get_component("nonexistent")
    assert "not registered" in str(exc_info.value)
    
    logger.info("test_component_loader_error_handling completed successfully")

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
    """Test widget reinitialization after failure"""
    logger.info("Starting test_widget_reinitialization")
    
    class RetryWidget(LazyWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.attempt = 0
            
        def initialize(self) -> bool:
            self.attempt += 1
            if self.attempt == 1:
                logger.info("[TEST] RetryWidget: First attempt intentionally fails")
                raise ValueError("First attempt fails (expected test behavior)")
            logger.info(f"[TEST] RetryWidget: Attempt {self.attempt} succeeds")
            time.sleep(0.001)  # Добавляем небольшую задержку для измеримого времени инициализации
            return True
    
    # Create widget
    widget = RetryWidget()
    cleanup_widgets.append(widget)
    widget.hide()
    
    # First attempt - should fail
    logger.info("[TEST] Attempting first initialization (expected to fail)")
    success = widget._do_initialize()
    process_events()
    
    # Check error state
    assert not success, "First initialization should fail"
    assert not widget.is_initialized()
    assert isinstance(widget.get_init_error(), ValueError)
    assert "First attempt fails (expected test behavior)" in str(widget.get_init_error())
    
    # Check that we recorded time even for failed attempt
    failed_init_time = widget.get_init_time()
    assert failed_init_time > 0, f"Failed initialization time should be > 0, got {failed_init_time}"
    logger.debug(f"Failed initialization took {failed_init_time:.6f}s")
    
    # Reset and retry
    logger.info("[TEST] Resetting widget initialization")
    widget.reset_initialization()
    assert not widget.is_initialized()
    assert widget.get_init_error() is None
    
    # Second attempt - should succeed
    logger.info("[TEST] Attempting second initialization (should succeed)")
    success = widget._do_initialize()
    process_events()
    
    # Check success state
    assert success, "Second initialization should succeed"
    assert widget.is_initialized()
    assert widget.get_init_error() is None
    
    # Check initialization time
    init_time = widget.get_init_time()
    assert init_time > 0, f"Initialization time should be > 0, got {init_time}"
    assert init_time >= 0.001, f"Initialization time should be >= 0.001s, got {init_time}"
    logger.debug(f"Successful initialization took {init_time:.6f}s")
    
    logger.info("test_widget_reinitialization completed successfully")

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

def test_concurrent_module_loading():
    """Test concurrent module loading"""
    logger.info("Starting test_concurrent_module_loading")
    
    # Create proxies for standard modules
    modules = [
        lazy_import("os"),
        lazy_import("sys"),
        lazy_import("time")
    ]
    
    # Access module attributes to trigger loading
    logger.debug("Starting concurrent module loading")
    threads = []
    for module in modules:
        thread = threading.Thread(target=lambda m: getattr(m, "__name__"), args=(module,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    logger.debug("Waiting for module loading to complete")
    for thread in threads:
        thread.join(timeout=5.0)
    
    # Check results
    total_time = 0
    for module in modules:
        assert module.is_loaded(), "Module should be loaded"
        assert module.get_load_error() is None, "No error should be present"
        load_time = module.get_load_time()
        assert load_time > 0, f"Load time should be > 0, got {load_time}"
        total_time += load_time
        logger.debug(f"Module loaded in {load_time:.3f}s")
    
    logger.debug(f"Total loading time: {total_time:.3f}s")
    assert total_time > 0, "Total loading time should be > 0"
    
    logger.info("test_concurrent_module_loading completed successfully")

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
    """Test widget initialization error"""
    logger.info("Starting test_widget_initialization_error")
    
    # Create widget
    widget = _ErrorWidget()
    cleanup_widgets.append(widget)
    widget.hide()
    
    # Check initial state
    assert not widget.is_initialized()
    assert widget.get_init_error() is None
    
    # Try to initialize
    logger.debug("Attempting widget initialization (expecting error)")
    success = widget._do_initialize()
    process_events()
    
    # Check error state
    assert not success, "Initialization should fail"
    assert not widget.is_initialized()
    assert isinstance(widget.get_init_error(), ValueError)
    assert str(widget.get_init_error()) == "Test error"
    
    logger.info("test_widget_initialization_error completed successfully")

def test_widget_initialization_failure(qapp, process_events, cleanup_widgets):
    """Test widget initialization failure"""
    logger.info("Starting test_widget_initialization_failure")
    
    # Create widget
    widget = _FailingWidget()
    cleanup_widgets.append(widget)
    widget.hide()
    
    # Check initial state
    assert not widget.is_initialized()
    assert widget.get_init_error() is None
    
    # Try to initialize
    logger.debug("Attempting widget initialization (expecting failure)")
    success = widget._do_initialize()
    process_events()
    
    # Check failure state
    assert not success, "Initialization should fail"
    assert not widget.is_initialized()
    assert isinstance(widget.get_init_error(), RuntimeError)
    assert "Widget initialization returned False" in str(widget.get_init_error())
    
    logger.info("test_widget_initialization_failure completed successfully")

def test_widget_reinitialization(qapp, process_events, cleanup_widgets):
    """Test widget reinitialization after failure"""
    logger.info("Starting test_widget_reinitialization")
    
    class RetryWidget(LazyWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.attempt = 0
            
        def initialize(self) -> bool:
            self.attempt += 1
            if self.attempt == 1:
                logger.info("[TEST] RetryWidget: First attempt intentionally fails")
                raise ValueError("First attempt fails (expected test behavior)")
            logger.info(f"[TEST] RetryWidget: Attempt {self.attempt} succeeds")
            return True
    
    # Create widget
    widget = RetryWidget()
    cleanup_widgets.append(widget)
    widget.hide()
    
    # First attempt - should fail
    logger.info("[TEST] Attempting first initialization (expected to fail)")
    with pytest.raises(ValueError) as exc_info:
        widget._do_initialize()
    process_events()
    
    # Check error state
    assert str(exc_info.value) == "First attempt fails (expected test behavior)"
    assert not widget.is_initialized()
    assert isinstance(widget.get_init_error(), ValueError)
    assert str(widget.get_init_error()) == "First attempt fails (expected test behavior)"
    
    # Reset and retry
    logger.info("[TEST] Resetting widget initialization")
    widget.reset_initialization()
    assert not widget.is_initialized()
    assert widget.get_init_error() is None
    
    # Second attempt - should succeed
    logger.info("[TEST] Attempting second initialization (should succeed)")
    success = widget._do_initialize()
    process_events()
    
    # Check success state
    assert success, "Second initialization should succeed"
    assert widget.is_initialized()
    assert widget.get_init_error() is None
    assert widget.get_init_time() > 0
    
    logger.info("test_widget_reinitialization completed successfully")

def test_thread_safety(qapp, process_events, cleanup_widgets):
    """Test thread safety of widget initialization"""
    logger.info("Starting test_thread_safety")
    
    class ThreadTestWidget(LazyWidget):
        def initialize(self) -> bool:
            logger.debug(f"Initializing in thread: {QThread.currentThread().objectName()}")
            assert QThread.currentThread() == QApplication.instance().thread()
            return True
    
    # Create widget in main thread
    widget = ThreadTestWidget()
    cleanup_widgets.append(widget)
    widget.hide()
    
    # Try to initialize from another thread
    logger.debug("Attempting initialization from worker thread")
    thread = threading.Thread(target=widget._do_initialize)
    thread.start()
    thread.join(timeout=5.0)
    process_events()
    
    # Check results
    assert widget.is_initialized()
    assert widget.get_init_error() is None
    assert widget.get_init_time() > 0
    
    logger.info("test_thread_safety completed successfully")

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

class TestLoadPriority:
    """Tests for LoadPriority enum."""
    
    def test_priority_ordering(self):
        """Test priority values are correctly ordered."""
        assert LoadPriority.CRITICAL.value < LoadPriority.HIGH.value
        assert LoadPriority.HIGH.value < LoadPriority.MEDIUM.value
        assert LoadPriority.MEDIUM.value < LoadPriority.LOW.value
        assert LoadPriority.LOW.value < LoadPriority.LAZY.value

class TestComponentMetadata:
    """Tests for ComponentMetadata class."""
    
    def test_metadata_creation(self):
        """Test creating component metadata."""
        factory = Mock()
        metadata = ComponentMetadata(
            name="test_component",
            factory=factory,
            priority=LoadPriority.MEDIUM,
            dependencies=set(),
            size_estimate=1024,
            last_access=0.0,
            access_count=0,
            load_time=0.0,
            is_loaded=False,
            weak_ref=None
        )
        
        assert metadata.name == "test_component"
        assert metadata.factory == factory
        assert metadata.priority == LoadPriority.MEDIUM
        assert metadata.dependencies == set()
        assert metadata.size_estimate == 1024
        assert metadata.last_access == 0.0
        assert metadata.access_count == 0
        assert metadata.load_time == 0.0
        assert not metadata.is_loaded
        assert metadata.weak_ref is None

class TestResourceManager:
    """Tests for ResourceManager class."""
    
    @pytest.fixture
    def resource_manager(self):
        """Create ResourceManager instance."""
        return ResourceManager(memory_limit_mb=100)
        
    def test_memory_limit(self, resource_manager):
        """Test memory limit enforcement."""
        assert resource_manager.can_load(50)  # 50MB
        assert not resource_manager.can_load(150)  # Over limit
        
    def test_memory_allocation(self, resource_manager):
        """Test memory allocation and deallocation."""
        initial_available = resource_manager.get_available()
        
        # Allocate memory
        resource_manager.allocate(30)  # 30MB
        assert resource_manager.get_usage() == 30
        assert resource_manager.get_available() == initial_available - 30
        
        # Free memory
        resource_manager.free(20)  # Free 20MB
        assert resource_manager.get_usage() == 10
        assert resource_manager.get_available() == initial_available - 10
        
    def test_memory_overflow_protection(self, resource_manager):
        """Test protection against memory overflow."""
        resource_manager.allocate(50)
        assert not resource_manager.can_load(60)  # Would exceed limit

class TestPreloadManager:
    """Tests for PreloadManager class."""
    
    @pytest.fixture
    def preload_manager(self):
        """Create PreloadManager instance."""
        resource_manager = ResourceManager(memory_limit_mb=100)
        return PreloadManager(resource_manager)
        
    def test_queue_preload(self, preload_manager):
        """Test queuing components for preloading."""
        component1 = ComponentMetadata(
            name="high_priority",
            factory=Mock(),
            priority=LoadPriority.HIGH,
            dependencies=set(),
            size_estimate=1024,
            last_access=0.0,
            access_count=0,
            load_time=0.0,
            is_loaded=False,
            weak_ref=None
        )
        
        component2 = ComponentMetadata(
            name="low_priority",
            factory=Mock(),
            priority=LoadPriority.LOW,
            dependencies=set(),
            size_estimate=1024,
            last_access=0.0,
            access_count=0,
            load_time=0.0,
            is_loaded=False,
            weak_ref=None
        )
        
        preload_manager.queue_preload(component2)
        preload_manager.queue_preload(component1)
        
        # High priority should be first
        assert preload_manager._preload_queue[0].name == "high_priority"
        
    def test_preload_worker(self, preload_manager):
        """Test preload worker functionality."""
        mock_component = Mock()
        component = ComponentMetadata(
            name="test_component",
            factory=lambda: mock_component,
            priority=LoadPriority.HIGH,
            dependencies=set(),
            size_estimate=1024,
            last_access=0.0,
            access_count=0,
            load_time=0.0,
            is_loaded=False,
            weak_ref=None
        )
        
        preload_manager.queue_preload(component)
        preload_manager.start()
        time.sleep(0.1)  # Allow worker to process
        preload_manager.stop()
        
        assert len(preload_manager._preload_queue) == 0

class TestComponentLoader:
    """Tests for ComponentLoader class."""
    
    @pytest.fixture
    def loader(self):
        """Create ComponentLoader instance."""
        return ComponentLoader()
        
    def test_register_component(self, loader):
        """Test component registration."""
        mock_component = Mock()
        factory = lambda: mock_component
        
        loader.register_component(
            "test_component",
            factory,
            priority=LoadPriority.HIGH,
            dependencies={"dep1"},
            size_estimate=1024
        )
        
        assert "test_component" in loader._components
        metadata = loader._components["test_component"]
        assert metadata.name == "test_component"
        assert metadata.priority == LoadPriority.HIGH
        assert metadata.dependencies == {"dep1"}
        assert metadata.size_estimate == 1024
        
    def test_get_component(self, loader):
        """Test component loading."""
        mock_component = Mock()
        factory = lambda: mock_component
        
        loader.register_component(
            "test_component",
            factory,
            priority=LoadPriority.MEDIUM
        )
        
        component = loader.get_component("test_component")
        assert component == mock_component
        
        metadata = loader._components["test_component"]
        assert metadata.is_loaded
        assert metadata.access_count == 1
        assert metadata.weak_ref() == mock_component
        
    def test_dependency_loading(self, loader):
        """Test loading components with dependencies."""
        mock_dep = Mock()
        mock_component = Mock()
        
        loader.register_component(
            "dependency",
            lambda: mock_dep,
            priority=LoadPriority.HIGH
        )
        
        loader.register_component(
            "test_component",
            lambda: mock_component,
            priority=LoadPriority.MEDIUM,
            dependencies={"dependency"}
        )
        
        component = loader.get_component("test_component")
        assert component == mock_component
        assert loader.is_loaded("dependency")
        
    def test_memory_management(self, loader):
        """Test memory management during loading."""
        # Register a large component
        large_component = Mock()
        loader.register_component(
            "large_component",
            lambda: large_component,
            priority=LoadPriority.LOW,
            size_estimate=80 * 1024 * 1024  # 80MB
        )
        
        # Register several small components
        small_components = []
        for i in range(5):
            component = Mock()
            small_components.append(component)
            loader.register_component(
                f"small_component_{i}",
                lambda c=component: c,
                priority=LoadPriority.MEDIUM,
                size_estimate=10 * 1024 * 1024  # 10MB
            )
            
        # Load all small components
        for i in range(5):
            loader.get_component(f"small_component_{i}")
            
        # Try to load large component - should trigger memory cleanup
        loader.get_component("large_component")
        
        # Verify some small components were unloaded
        loaded_count = sum(1 for i in range(5) 
                         if loader.is_loaded(f"small_component_{i}"))
        assert loaded_count < 5
        
    def test_component_unloading(self, loader):
        """Test component unloading."""
        mock_component = Mock()
        loader.register_component(
            "test_component",
            lambda: mock_component,
            priority=LoadPriority.LOW
        )
        
        loader.get_component("test_component")
        assert loader.is_loaded("test_component")
        
        success = loader.unload_component("test_component")
        assert success
        assert not loader.is_loaded("test_component")
        
    def test_stats_collection(self, loader):
        """Test statistics collection."""
        mock_component = Mock()
        loader.register_component(
            "test_component",
            lambda: mock_component
        )
        
        loader.get_component("test_component")
        stats = loader.get_stats()
        
        assert stats["component_count"] == 1
        assert stats["loaded_count"] == 1
        assert stats["memory_usage_mb"] > 0
        assert stats["memory_available_mb"] > 0
        assert stats["average_load_time"] >= 0

def test_global_component_loader():
    """Test global component loader instance."""
    assert isinstance(component_loader, ComponentLoader)
    
    # Test basic functionality
    mock_component = Mock()
    component_loader.register_component(
        "global_test",
        lambda: mock_component
    )
    
    loaded = component_loader.get_component("global_test")
    assert loaded == mock_component
    
    # Cleanup
    component_loader.cleanup()
