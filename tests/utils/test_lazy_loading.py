"""Tests for lazy loading utilities."""
import pytest
import threading
import time
from src.utils.lazy_loading import LazyLoader, ComponentLoader, LoadPriority

def test_lazy_loader_creation():
    """Test lazy loader creation."""
    loader = LazyLoader()
    assert loader is not None
    assert loader._cache == {}

def test_lazy_loader_load():
    """Test lazy loading of items."""
    loader = LazyLoader()
    
    # Test loading new item
    value = loader.load("test", lambda: "test_value")
    assert value == "test_value"
    assert "test" in loader._cache
    
    # Test loading cached item
    counter = [0]
    def factory():
        counter[0] += 1
        return "factory_value"
    
    # First load should call factory
    value1 = loader.load("factory", factory)
    assert value1 == "factory_value"
    assert counter[0] == 1
    
    # Second load should use cache
    value2 = loader.load("factory", factory)
    assert value2 == "factory_value"
    assert counter[0] == 1  # Factory not called again

def test_lazy_loader_get():
    """Test getting items from loader."""
    loader = LazyLoader()
    
    # Test getting non-existent item
    assert loader.get("missing") is None
    
    # Test getting existing item
    loader.load("test", lambda: "test_value")
    assert loader.get("test") == "test_value"

def test_lazy_loader_clear():
    """Test clearing loader cache."""
    loader = LazyLoader()
    
    # Add some items
    loader.load("test1", lambda: "value1")
    loader.load("test2", lambda: "value2")
    assert len(loader._cache) == 2
    
    # Clear cache
    loader.clear()
    assert len(loader._cache) == 0
    assert loader.get("test1") is None
    assert loader.get("test2") is None

def test_lazy_loader_remove():
    """Test removing items from loader."""
    loader = LazyLoader()
    
    # Add items
    loader.load("test1", lambda: "value1")
    loader.load("test2", lambda: "value2")
    
    # Remove one item
    loader.remove("test1")
    assert loader.get("test1") is None
    assert loader.get("test2") == "value2"
    
    # Remove non-existent item
    loader.remove("missing")  # Should not raise error

def test_lazy_loader_thread_safety():
    """Test thread safety of lazy loader."""
    loader = LazyLoader()
    results = []
    
    def worker(key):
        value = loader.load(key, lambda: f"value_{key}")
        results.append(value)
    
    # Create threads
    threads = [
        threading.Thread(target=worker, args=(f"key_{i}",))
        for i in range(10)
    ]
    
    # Start threads
    for thread in threads:
        thread.start()
    
    # Wait for threads
    for thread in threads:
        thread.join()
    
    # Check results
    assert len(results) == 10
    assert len(loader._cache) == 10
    for i in range(10):
        assert f"value_key_{i}" in results

def test_component_loader_integration():
    """Test integration between LazyLoader and ComponentLoader."""
    lazy_loader = LazyLoader()
    component_loader = ComponentLoader()
    
    # Register component using lazy loader
    def create_component():
        return "test_component"
    
    component_loader.register_component(
        "test",
        lambda: lazy_loader.load("test", create_component),
        priority=LoadPriority.HIGH
    )
    
    # Get component
    component = component_loader.get_component("test")
    assert component == "test_component"
    
    # Check it's in both loaders
    assert lazy_loader.get("test") == "test_component"
    assert component_loader.is_loaded("test")
