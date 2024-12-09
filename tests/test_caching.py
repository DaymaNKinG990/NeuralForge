"""Tests for caching utilities."""
import pytest
import time
import threading
from src.utils.caching import CacheManager, Cache, CacheEntry, CacheEvent, CacheEventType, cache_result, LoadPriority

@pytest.fixture
def cache_manager():
    """Create cache manager fixture."""
    manager = CacheManager()
    yield manager

@pytest.fixture
def cache():
    """Create cache fixture."""
    cache = Cache(max_size=10, default_ttl=1)
    yield cache

def test_cache_manager_creation(cache_manager):
    """Test cache manager creation."""
    assert cache_manager is not None
    assert isinstance(cache_manager._caches, dict)
    assert isinstance(cache_manager._monitors, list)

def test_cache_manager_registration(cache_manager, cache):
    """Test cache registration."""
    cache_manager.register_cache("test", cache)
    assert cache_manager.get_cache("test") == cache
    assert cache_manager.get_cache("non_existent") is None

def test_cache_manager_monitoring(cache_manager):
    """Test cache event monitoring."""
    events = []
    def monitor(event):
        events.append(event)
    
    cache_manager.add_monitor(monitor)
    
    # Create event
    event = CacheEvent(CacheEventType.HIT, "test_key")
    cache_manager.notify_event(event)
    
    assert len(events) == 1
    assert events[0] == event

def test_cache_basic_operations(cache):
    """Test basic cache operations."""
    # Test set and get
    cache.set("test", "value")
    assert cache.get("test") == "value"
    
    # Test non-existent key
    assert cache.get("missing") is None
    
    # Test expiry
    cache.set("expire", "value", ttl=0.1)
    assert cache.get("expire") == "value"
    time.sleep(0.2)
    assert cache.get("expire") is None

def test_cache_memory_management(cache):
    """Test cache memory management."""
    # Fill cache
    for i in range(20):
        cache.set(f"key_{i}", "x" * 1000, size_estimate=1000)
    
    # Check size is limited
    assert len(cache._entries) <= cache._max_size
    
    # Check memory tracking
    assert cache._current_memory > 0
    assert cache._current_memory <= cache._memory_limit

def test_cache_priority(cache):
    """Test cache priority handling."""
    # Add entries with different priorities
    cache.set("critical", "value", priority=LoadPriority.CRITICAL)
    cache.set("low", "value", priority=LoadPriority.LOW)
    
    # Fill cache to trigger eviction
    for i in range(20):
        cache.set(f"key_{i}", "value")
    
    # Critical should remain, low might be evicted
    assert cache.get("critical") == "value"
    if cache.get("low") is not None:
        pytest.fail("Low priority entry should have been evicted")

def test_cache_cleanup(cache):
    """Test cache cleanup."""
    # Add expired entries
    cache.set("expire1", "value", ttl=0.1)
    cache.set("expire2", "value", ttl=0.1)
    cache.set("keep", "value", ttl=10)
    
    time.sleep(0.2)
    cache._cleanup()
    
    assert cache.get("expire1") is None
    assert cache.get("expire2") is None
    assert cache.get("keep") == "value"

def test_cache_thread_safety(cache):
    """Test thread safety."""
    def writer():
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")
            time.sleep(0.001)
    
    def reader():
        for i in range(100):
            cache.get(f"key_{i}")
            time.sleep(0.001)
    
    # Create threads
    writer_thread = threading.Thread(target=writer)
    reader_thread = threading.Thread(target=reader)
    
    # Start threads
    writer_thread.start()
    reader_thread.start()
    
    # Wait for completion
    writer_thread.join()
    reader_thread.join()
    
    # No exceptions should have been raised

@cache_result(ttl=1)
def cached_function(x):
    """Test function for cache decorator."""
    return x * 2

def test_cache_decorator():
    """Test cache decorator."""
    # First call - cache miss
    result1 = cached_function(5)
    assert result1 == 10
    
    # Second call - cache hit
    result2 = cached_function(5)
    assert result2 == 10
    
    # Different argument - cache miss
    result3 = cached_function(6)
    assert result3 == 12
    
    # Wait for expiry
    time.sleep(1.1)
    
    # Should be recomputed
    result4 = cached_function(5)
    assert result4 == 10

def test_cache_events(cache_manager, cache):
    """Test cache events."""
    events = []
    def monitor(event):
        events.append(event)
    
    cache_manager.add_monitor(monitor)
    cache_manager.register_cache("test", cache)
    
    # Generate events
    cache.set("test", "value")
    value = cache.get("test")  # Hit
    value = cache.get("missing")  # Miss
    
    # Fill cache to trigger eviction
    for i in range(20):
        cache.set(f"key_{i}", "x" * 1000, size_estimate=1000)
    
    # Check events
    event_types = [e.type for e in events]
    assert CacheEventType.HIT in event_types
    assert CacheEventType.MISS in event_types
    assert CacheEventType.EVICT in event_types
