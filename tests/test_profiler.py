import pytest
import time
from src.utils.profiler import Profiler, ProfileResult
from datetime import datetime
import tracemalloc

@pytest.fixture
def profiler():
    """Create a test profiler"""
    prof = Profiler()
    yield prof
    # Cleanup
    prof.clear_results()
    if prof.memory_tracking:
        prof.stop_memory_tracking()

def simulate_work(duration: float = 0.1):
    """Helper function to simulate work"""
    start = time.time()
    while time.time() - start < duration:
        _ = [i * i for i in range(1000)]

def test_basic_profiling(profiler):
    """Test basic profiling functionality"""
    @profiler.profile(threshold_ms=50)
    def test_function():
        simulate_work(0.1)
        return "test"

    # Run profiled function
    result = test_function()
    assert result == "test"

    # Check profiling results
    results = profiler.get_results("test_function")
    assert len(results) == 1
    assert isinstance(results[0], ProfileResult)
    assert results[0].function_name == "test_function"
    assert results[0].total_time >= 0.1
    assert results[0].calls > 0

def test_memory_tracking(profiler):
    """Test memory tracking functionality"""
    profiler.start_memory_tracking()

    @profiler.profile(threshold_ms=0)  # Set threshold to 0 to ensure capture
    def allocate_memory():
        # Allocate some memory
        large_list = [0] * 1000000
        return len(large_list)

    # Run function and check results
    size = allocate_memory()
    assert size == 1000000

    results = profiler.get_results("allocate_memory")
    assert len(results) == 1
    assert results[0].memory_peak > results[0].memory_start

    # Cleanup
    profiler.stop_memory_tracking()
    assert not profiler.memory_tracking

def test_profiler_disabled(profiler):
    """Test profiler when disabled"""
    profiler.enabled = False

    @profiler.profile()
    def test_function():
        return "test"

    result = test_function()
    assert result == "test"
    assert len(profiler.get_results("test_function")) == 0

def test_slow_operations(profiler):
    """Test detection of slow operations"""
    @profiler.profile(threshold_ms=50)
    def slow_function():
        simulate_work(0.2)

    @profiler.profile(threshold_ms=50)
    def fast_function():
        simulate_work(0.01)

    slow_function()
    fast_function()

    slow_ops = profiler.get_slow_operations(threshold_ms=50)
    assert len(slow_ops) == 1
    assert slow_ops[0].function_name == "slow_function"
    assert slow_ops[0].total_time >= 0.2

def test_memory_intensive_operations(profiler):
    """Test detection of memory intensive operations"""
    profiler.start_memory_tracking()

    @profiler.profile(threshold_ms=0)
    def memory_intensive():
        large_list = [0] * 2000000
        return len(large_list)

    @profiler.profile(threshold_ms=0)
    def memory_light():
        small_list = [0] * 100
        return len(small_list)

    memory_intensive()
    memory_light()

    memory_ops = profiler.get_memory_intensive_operations(threshold_mb=1)
    assert len(memory_ops) > 0
    assert memory_ops[0].function_name == "memory_intensive"

def test_error_handling(profiler):
    """Test error handling in profiled functions"""
    @profiler.profile()
    def error_function():
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        error_function()

    # Results should still be recorded
    results = profiler.get_results("error_function")
    assert len(results) == 1

def test_multiple_calls(profiler):
    """Test profiling of multiple function calls"""
    @profiler.profile(threshold_ms=0)
    def test_function():
        simulate_work(0.01)

    # Call function multiple times
    for _ in range(3):
        test_function()

    results = profiler.get_results("test_function")
    assert len(results) == 3

def test_clear_results(profiler):
    """Test clearing profiling results"""
    @profiler.profile(threshold_ms=0)
    def test_function():
        simulate_work(0.01)

    test_function()
    assert len(profiler.get_results()) > 0

    profiler.clear_results()
    assert len(profiler.get_results()) == 0

def test_nested_profiling(profiler):
    """Test nested profiled functions"""
    @profiler.profile(threshold_ms=0)
    def outer_function():
        inner_function()
        return "outer"

    @profiler.profile(threshold_ms=0)
    def inner_function():
        simulate_work(0.01)
        return "inner"

    outer_function()

    # Both functions should be profiled
    assert len(profiler.get_results("outer_function")) > 0
    assert len(profiler.get_results("inner_function")) > 0

def test_profiler_thresholds(profiler):
    """Test different profiling thresholds"""
    @profiler.profile(threshold_ms=200)  # High threshold
    def fast_function():
        simulate_work(0.01)

    @profiler.profile(threshold_ms=1)  # Low threshold
    def another_fast_function():
        simulate_work(0.01)

    fast_function()
    another_fast_function()

    # Only the second function should be recorded due to threshold
    assert len(profiler.get_results("fast_function")) == 0
    assert len(profiler.get_results("another_fast_function")) > 0
