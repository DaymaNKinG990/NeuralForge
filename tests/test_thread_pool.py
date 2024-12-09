import pytest
import time
import concurrent.futures
import threading
from src.utils.performance import ThreadPool

def simple_task():
    """Simple test task"""
    return "done"

def task_with_args(x, y):
    """Test task with arguments"""
    return x + y

def slow_task():
    """Task that takes some time"""
    time.sleep(0.1)  # Reduced sleep time for faster tests
    return "slow task done"

def error_task():
    """Task that raises an error"""
    raise ValueError("test error")

@pytest.fixture
def pool():
    """Create thread pool instance"""
    pool = ThreadPool(max_workers=2)
    yield pool
    pool.shutdown(wait=True)  # Ensure cleanup after each test

def test_pool_initialization():
    """Test thread pool initialization"""
    pool = ThreadPool(max_workers=4)
    assert isinstance(pool.executor, concurrent.futures.ThreadPoolExecutor)
    assert pool.max_workers == 4
    assert not pool.tasks
    pool.shutdown(wait=True)

def test_submit_task(pool):
    """Test task submission"""
    future = pool.submit("test_task", simple_task)
    assert isinstance(future, concurrent.futures.Future)
    assert "test_task" in pool.tasks
    result = pool.get_result("test_task")
    assert result == "done"

def test_task_with_arguments(pool):
    """Test task execution with arguments"""
    future = pool.submit("math_task", task_with_args, 5, 3)
    result = pool.get_result("math_task")
    assert result == 8

def test_multiple_tasks(pool):
    """Test multiple task execution"""
    futures = []
    for i in range(5):
        future = pool.submit(f"task_{i}", task_with_args, i, i)
        futures.append((f"task_{i}", future))
    
    # Wait for all tasks to complete
    for name, future in futures:
        result = pool.get_result(name)
        assert result == int(name.split("_")[1]) * 2

def test_slow_task_timeout(pool):
    """Test timeout handling"""
    pool.submit("slow_task", slow_task)
    result = pool.get_result("slow_task", timeout=0.05)
    assert result is None  # Should timeout
    
    # Wait for task to complete
    result = pool.get_result("slow_task")
    assert result == "slow task done"

def test_error_handling(pool):
    """Test error handling in tasks"""
    pool.submit("error_task", error_task)
    result = pool.get_result("error_task")
    assert result is None

def test_task_cancellation(pool):
    """Test task cancellation"""
    future = pool.submit("slow_task", slow_task)
    assert pool.cancel_task("slow_task")
    assert "slow_task" not in pool.tasks

def test_nonexistent_task(pool):
    """Test getting result of nonexistent task"""
    assert pool.get_result("nonexistent") is None
    assert not pool.cancel_task("nonexistent")

def test_concurrent_tasks(pool):
    """Test concurrent task execution"""
    event = threading.Event()
    results = []
    
    def synchronized_task(i):
        event.wait()  # Wait for signal
        return i * 2
    
    # Submit tasks but they won't start until event is set
    futures = []
    for i in range(4):
        future = pool.submit(f"task_{i}", synchronized_task, i)
        futures.append((f"task_{i}", future))
    
    # Start all tasks simultaneously
    event.set()
    
    # Collect results
    for name, future in futures:
        result = pool.get_result(name)
        results.append(result)
    
    assert sorted(results) == [0, 2, 4, 6]

def test_task_resubmission(pool):
    """Test resubmitting task with same name"""
    # Submit first task
    pool.submit("task", task_with_args, 1, 2)
    assert pool.get_result("task") == 3
    
    # Resubmit with same name
    pool.submit("task", task_with_args, 3, 4)
    assert pool.get_result("task") == 7

def test_shutdown_behavior(pool):
    """Test pool shutdown behavior"""
    # Submit a task
    pool.submit("task", simple_task)
    
    # Shutdown the pool
    pool.shutdown(wait=True)
    
    # Try to submit after shutdown
    future = pool.submit("new_task", simple_task)
    assert future is None

def test_cleanup_completed_tasks(pool):
    """Test automatic cleanup of completed tasks"""
    # Submit and complete a task
    pool.submit("task", simple_task)
    result = pool.get_result("task")
    assert result == "done"
    assert "task" not in pool.tasks  # Should be cleaned up
