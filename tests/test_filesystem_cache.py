import pytest
import time
import os
from pathlib import Path
from src.utils.performance import FileSystemCache

@pytest.fixture
def cache():
    """Create cache instance"""
    return FileSystemCache(max_size=5, ttl=1)

@pytest.fixture
def test_file(tmp_path):
    """Create a temporary test file"""
    file_path = tmp_path / "test.txt"
    with open(file_path, "w") as f:
        f.write("test content")
    return file_path

def test_cache_initialization():
    """Test cache initialization"""
    cache = FileSystemCache(max_size=100, ttl=300)
    assert cache.max_size == 100
    assert cache.ttl == 300
    assert not cache.cache
    assert not cache.access_times

def test_get_file_info(cache, test_file):
    """Test getting file information"""
    info = cache.get_file_info(test_file)
    
    assert "size" in info
    assert "mtime" in info
    assert "exists" in info
    assert info["exists"] is True
    assert info["size"] > 0

def test_cache_hit(cache, test_file):
    """Test cache hit"""
    # First access - cache miss
    first_info = cache.get_file_info(test_file)
    
    # Second access - should be cache hit
    second_info = cache.get_file_info(test_file)
    
    assert first_info == second_info
    assert str(test_file) in cache.cache

def test_cache_expiration(cache, test_file):
    """Test cache entry expiration"""
    # Get initial info
    cache.get_file_info(test_file)
    
    # Wait for TTL to expire
    time.sleep(1.1)
    
    # Get info again - should be cache miss
    cache.get_file_info(test_file)
    
    # Verify access time was updated
    assert time.time() - cache.access_times[str(test_file)] < 1.0

def test_cache_size_limit(cache):
    """Test cache size limitation"""
    # Create multiple test files
    files = []
    for i in range(7):  # More than max_size
        path = Path(f"/test/file{i}.txt")
        cache.cache[str(path)] = {"exists": True, "size": 100}
        cache.access_times[str(path)] = time.time()
        files.append(path)
        
    # Trigger cleanup
    cache.cleanup()
    
    # Verify cache size is maintained
    assert len(cache.cache) <= cache.max_size
    assert len(cache.access_times) <= cache.max_size

def test_nonexistent_file(cache):
    """Test handling of nonexistent files"""
    info = cache.get_file_info("/nonexistent/file.txt")
    assert info["exists"] is False

def test_file_modification(cache, test_file):
    """Test handling of file modifications"""
    # Get initial info
    initial_info = cache.get_file_info(test_file)
    
    # Modify file
    time.sleep(0.1)  # Ensure mtime changes
    with open(test_file, "a") as f:
        f.write("\nmore content")
    
    # Get updated info
    updated_info = cache.get_file_info(test_file)
    
    assert updated_info["mtime"] > initial_info["mtime"]
    assert updated_info["size"] > initial_info["size"]

def test_concurrent_access(cache, test_file):
    """Test concurrent access to cache"""
    import threading
    
    def access_cache():
        for _ in range(100):
            cache.get_file_info(test_file)
    
    threads = [threading.Thread(target=access_cache) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    assert str(test_file) in cache.cache
    assert str(test_file) in cache.access_times

def test_cache_cleanup(cache):
    """Test cache cleanup"""
    # Add some expired entries
    old_time = time.time() - cache.ttl - 1
    for i in range(3):
        path = f"/test/old_file{i}.txt"
        cache.cache[path] = {"exists": True}
        cache.access_times[path] = old_time
    
    # Add some current entries
    for i in range(3):
        path = f"/test/new_file{i}.txt"
        cache.cache[path] = {"exists": True}
        cache.access_times[path] = time.time()
    
    # Run cleanup
    cache.cleanup()
    
    # Verify old entries are removed
    assert all(time.time() - t <= cache.ttl 
              for t in cache.access_times.values())

def test_path_normalization(cache, test_file):
    """Test path normalization handling"""
    # Test different path formats
    path_str = str(test_file)
    path_obj = Path(test_file)
    path_relative = os.path.relpath(test_file)
    
    info1 = cache.get_file_info(path_str)
    info2 = cache.get_file_info(path_obj)
    info3 = cache.get_file_info(path_relative)
    
    assert info1 == info2 == info3

def test_error_handling(cache):
    """Test error handling"""
    # Test with invalid path type
    with pytest.raises(TypeError):
        cache.get_file_info(123)
    
    # Test with empty path
    with pytest.raises(ValueError):
        cache.get_file_info("")

def test_cache_clear(cache, test_file):
    """Test cache clearing"""
    # Add some entries
    cache.get_file_info(test_file)
    assert cache.cache
    assert cache.access_times
    
    # Clear cache
    cache.cache.clear()
    cache.access_times.clear()
    
    assert not cache.cache
    assert not cache.access_times

def test_large_files(cache, tmp_path):
    """Test handling of large files"""
    large_file = tmp_path / "large.txt"
    
    # Create a relatively large file (1MB)
    with open(large_file, "wb") as f:
        f.write(b"0" * 1024 * 1024)
    
    info = cache.get_file_info(large_file)
    assert info["size"] == 1024 * 1024

def test_special_characters(cache, tmp_path):
    """Test handling of paths with special characters"""
    special_file = tmp_path / "special!@#$%^&().txt"
    with open(special_file, "w") as f:
        f.write("test")
    
    info = cache.get_file_info(special_file)
    assert info["exists"] is True
