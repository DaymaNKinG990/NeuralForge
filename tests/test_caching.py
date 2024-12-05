import pytest
import time
import os
import shutil
from src.utils.caching import CacheManager, SearchCache, CacheEntry

@pytest.fixture
def cache_manager():
    """Create a test cache manager with smaller limits"""
    manager = CacheManager(max_size_mb=1, max_entries=10)
    yield manager
    # Cleanup
    manager.clear()
    if os.path.exists("cache"):
        shutil.rmtree("cache")

@pytest.fixture
def search_cache():
    """Create a test search cache"""
    cache = SearchCache()
    yield cache
    # Cleanup
    cache.clear()
    if os.path.exists("cache"):
        shutil.rmtree("cache")

def test_basic_cache_operations(cache_manager):
    """Test basic set/get operations"""
    # Test setting and getting
    assert cache_manager.set("test_key", "test_value")
    assert cache_manager.get("test_key") == "test_value"
    
    # Test non-existent key
    assert cache_manager.get("non_existent") is None
    
    # Test overwriting
    assert cache_manager.set("test_key", "new_value")
    assert cache_manager.get("test_key") == "new_value"

def test_cache_expiry(cache_manager):
    """Test TTL functionality"""
    # Set with 1 second TTL
    assert cache_manager.set("expire_key", "expire_value", ttl=1)
    assert cache_manager.get("expire_key") == "expire_value"
    
    # Wait for expiry
    time.sleep(1.1)
    assert cache_manager.get("expire_key") is None

def test_cache_capacity(cache_manager):
    """Test cache capacity limits"""
    # Fill cache to capacity
    large_data = "x" * 500_000  # 500KB
    assert cache_manager.set("large_key1", large_data)
    assert cache_manager.set("large_key2", large_data)
    
    # This should fail as it exceeds max size
    assert not cache_manager.set("large_key3", "x" * 1_100_000)
    
    # Verify first entries
    assert cache_manager.get("large_key1") is not None
    assert cache_manager.get("large_key2") is not None

def test_cache_entry_count(cache_manager):
    """Test maximum entry count"""
    # Add max_entries + 1 items
    for i in range(11):
        cache_manager.set(f"key_{i}", f"value_{i}")
    
    # Verify oldest entry was removed
    assert cache_manager.get("key_0") is None
    assert cache_manager.get("key_10") is not None

def test_persistent_cache(cache_manager):
    """Test disk persistence"""
    # Set with persistence
    assert cache_manager.set("persist_key", "persist_value", persist=True)
    
    # Clear memory cache
    cache_manager.clear()
    
    # Should still be available from disk
    assert cache_manager.get("persist_key") == "persist_value"

def test_cache_stats(cache_manager):
    """Test cache statistics"""
    cache_manager.set("stats_key", "stats_value")
    cache_manager.get("stats_key")
    cache_manager.get("stats_key")
    
    stats = cache_manager.get_stats()
    assert stats["entry_count"] == 1
    assert stats["total_size"] > 0
    assert stats["hit_rate"] > 0

def test_search_cache_operations(search_cache):
    """Test search cache specific operations"""
    results = ["result1", "result2"]
    context = {"filter": "test"}
    
    # Cache search results
    search_cache.cache_search_results("test query", results, context)
    
    # Retrieve with same context
    cached = search_cache.get_search_results("test query", context)
    assert cached == results
    
    # Different context should miss
    assert search_cache.get_search_results("test query", {"filter": "other"}) is None

def test_cache_clear(cache_manager):
    """Test cache clearing"""
    # Add some entries
    cache_manager.set("clear_key1", "value1")
    cache_manager.set("clear_key2", "value2")
    
    # Clear cache
    cache_manager.clear()
    
    # Verify all entries are gone
    assert cache_manager.get("clear_key1") is None
    assert cache_manager.get("clear_key2") is None

def test_cache_error_handling(cache_manager):
    """Test error handling"""
    # Test with un-pickle-able object
    class UnpickleableObject:
        def __getstate__(self):
            raise pickle.PickleError("Cannot pickle")
    
    # Should return False but not raise
    assert not cache_manager.set("error_key", UnpickleableObject())
    
    # Should handle None values
    assert cache_manager.set("none_key", None)
    assert cache_manager.get("none_key") is None
