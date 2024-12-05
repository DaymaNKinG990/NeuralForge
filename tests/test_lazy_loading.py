import pytest
from PyQt6.QtWidgets import QWidget, QMainWindow
from src.utils.lazy_loading import (
    LazyLoader, LazyWidget, ComponentLoader,
    lazy_property, ModuleProxy, lazy_import
)
import time
import threading

@pytest.fixture
def lazy_loader():
    """Create a test lazy loader"""
    return LazyLoader()

@pytest.fixture
def component_loader():
    """Create a test component loader"""
    loader = ComponentLoader()
    yield loader
    loader.clear_cache()

class TestWidget(LazyWidget):
    """Test widget for lazy initialization"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_called = False
        
    def initialize(self):
        self.init_called = True
        return True

class TestComponent(QWidget):
    """Test component for component loader"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initialized = True

def test_lazy_module_loading(lazy_loader):
    """Test lazy loading of modules"""
    # Load a standard library module
    json_module = lazy_loader.load_module("json")
    assert json_module is not None
    
    # Test caching
    json_module2 = lazy_loader.load_module("json")
    assert json_module is json_module2
    
    # Test loading stats
    stats = lazy_loader.get_loading_stats()
    assert "json" in stats
    assert stats["json"] > 0

def test_lazy_module_loading_error(lazy_loader):
    """Test error handling in lazy loading"""
    with pytest.raises(ImportError):
        lazy_loader.load_module("nonexistent_module")

def test_lazy_widget_initialization():
    """Test lazy widget initialization"""
    widget = TestWidget()
    assert not widget._initialized
    assert not widget.init_called
    
    # Access widget to trigger initialization
    widget.show()
    assert widget._initialized
    assert widget.init_called

def test_component_loader(component_loader):
    """Test component loader functionality"""
    # Register component
    component_loader.register_component("test", TestComponent)
    
    # Get component instance
    parent = QMainWindow()
    component1 = component_loader.get_component("test", parent)
    assert isinstance(component1, TestComponent)
    assert component1.parent() is parent
    
    # Test caching
    component2 = component_loader.get_component("test", parent)
    assert component1 is component2
    
    # Test different parent
    parent2 = QMainWindow()
    component3 = component_loader.get_component("test", parent2)
    assert component3 is not component1
    assert component3.parent() is parent2

def test_component_loader_factory(component_loader):
    """Test component loader with factory function"""
    def factory(parent=None):
        return TestComponent(parent)
    
    component_loader.register_component("factory_test", factory)
    
    component = component_loader.get_component("factory_test")
    assert isinstance(component, TestComponent)
    assert component.initialized

def test_component_loader_clear_cache(component_loader):
    """Test clearing component cache"""
    component_loader.register_component("test", TestComponent)
    parent = QMainWindow()
    
    component1 = component_loader.get_component("test", parent)
    component_loader.clear_cache()
    component2 = component_loader.get_component("test", parent)
    
    assert component1 is not component2

def test_lazy_property_decorator():
    """Test lazy property decorator"""
    class TestClass:
        def __init__(self):
            self.init_count = 0
            
        @lazy_property
        def lazy_value(self):
            self.init_count += 1
            return 42
    
    obj = TestClass()
    assert obj.init_count == 0
    
    # Access property
    assert obj.lazy_value == 42
    assert obj.init_count == 1
    
    # Access again - should use cached value
    assert obj.lazy_value == 42
    assert obj.init_count == 1

def test_module_proxy():
    """Test module proxy functionality"""
    # Create proxy for json module
    json_proxy = ModuleProxy("json")
    
    # Access module through proxy
    assert json_proxy.dumps({"test": 123}) == '{"test": 123}'
    
    # Test caching
    assert json_proxy._module is not None

def test_lazy_import():
    """Test lazy import functionality"""
    json = lazy_import("json")
    
    # Module should not be loaded yet
    assert isinstance(json, ModuleProxy)
    assert json._module is None
    
    # Access should trigger load
    assert json.dumps({"test": 123}) == '{"test": 123}'
    assert json._module is not None

def test_thread_safety(lazy_loader):
    """Test thread safety of lazy loading"""
    def load_module():
        return lazy_loader.load_module("json")
    
    # Create multiple threads to load the same module
    threads = [threading.Thread(target=load_module) for _ in range(5)]
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify only one loading time was recorded
    stats = lazy_loader.get_loading_stats()
    assert len(stats) == 1
    assert "json" in stats
