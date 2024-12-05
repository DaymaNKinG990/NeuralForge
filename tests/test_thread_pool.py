import pytest
import time
import concurrent.futures
from src.utils.performance import ThreadPool

def simple_task():
    """Simple test task"""
    return "done"

def task_with_args(x, y):
    """Test task with arguments"""
    return x + y

def slow_task():
    """Task that takes some time"""
    time.sleep(0.5)
    return "slow task done"

def error_task():
    """Task that raises an error"""
    raise ValueError("test error")

@pytest.fixture
def pool():
    """Create thread pool instance"""
    return ThreadPool(max_workers=2)

def test_pool_initialization():
    """Test thread pool initialization"""
    pool = ThreadPool(max_workers=4)
    assert isinstance(pool.executor, concurrent.futures.ThreadPoolExecutor)
    assert pool.executor._max_workers == 4
    assert not pool.tasks

def test_submit_task(pool):
    """Test task submission"""
    future = pool.submit("test_task", simple_task)
    assert "test_task" in pool.tasks
    assert isinstance(future, concurrent.futures.Future)

def test_task_execution(pool):
    """Test task execution"""
    future = pool.submit("test_task", simple_task)
    result = pool.get_result("test_task")
    assert result == "done"

def test_task_with_arguments(pool):
    """Test task execution with arguments"""
    future = pool.submit("math_task", task_with_args, 5, 3)
    result = pool.get_result("math_task")
    assert result == 8

def test_multiple_tasks(pool):
    """Test multiple task execution"""
    tasks = ["task1", "task2", "task3"]
    futures = []
    
    for task in tasks:
        futures.append(pool.submit(task, simple_task))
    
    results = [pool.get_result(task) for task in tasks]
    assert all(result == "done" for result in results)

def test_slow_task_timeout(pool):
    """Test timeout handling"""
    pool.submit("slow_task", slow_task)
    
    with pytest.raises(concurrent.futures.TimeoutError):
        pool.get_result("slow_task", timeout=0.1)

def test_error_handling(pool):
    """Test error handling in tasks"""
    pool.submit("error_task", error_task)
    
    with pytest.raises(ValueError) as exc_info:
        pool.get_result("error_task")
    assert str(exc_info.value) == "test error"

def test_task_cancellation(pool):
    """Test task cancellation"""
    future = pool.submit("slow_task", slow_task)
    cancelled = pool.cancel_task("slow_task")
    
    assert cancelled
    assert future.cancelled() or future.done()

def test_nonexistent_task(pool):
    """Test getting result of nonexistent task"""
    with pytest.raises(KeyError):
        pool.get_result("nonexistent")

def test_concurrent_tasks(pool):
    """Test concurrent task execution"""
    start_time = time.time()
    
    # Submit multiple slow tasks
    pool.submit("slow1", slow_task)
    pool.submit("slow2", slow_task)
    
    # Get results
    results = [
        pool.get_result("slow1"),
        pool.get_result("slow2")
    ]
    
    duration = time.time() - start_time
    # Should take ~0.5s, not ~1s since tasks run concurrently
    assert duration < 0.8
    assert all(result == "slow task done" for result in results)

def test_task_resubmission(pool):
    """Test resubmitting task with same name"""
    # Submit first task
    pool.submit("task", task_with_args, 1, 2)
    result1 = pool.get_result("task")
    assert result1 == 3
    
    # Submit second task with same name
    pool.submit("task", task_with_args, 3, 4)
    result2 = pool.get_result("task")
    assert result2 == 7

def test_pool_cleanup(pool):
    """Test pool cleanup"""
    pool.submit("test", simple_task)
    pool.get_result("test")
    
    # Cleanup should happen automatically
    pool.executor.shutdown(wait=True)
    assert not pool.tasks

def test_stress_test(pool):
    """Test pool under stress"""
    num_tasks = 50
    task_names = [f"task{i}" for i in range(num_tasks)]
    
    # Submit many tasks
    for name in task_names:
        pool.submit(name, task_with_args, 1, 1)
    
    # Get all results
    results = [pool.get_result(name) for name in task_names]
    assert all(result == 2 for result in results)

def test_mixed_task_types(pool):
    """Test mixing different types of tasks"""
    # Submit different types of tasks
    pool.submit("simple", simple_task)
    pool.submit("args", task_with_args, 1, 2)
    pool.submit("slow", slow_task)
    
    # Get results
    assert pool.get_result("simple") == "done"
    assert pool.get_result("args") == 3
    assert pool.get_result("slow") == "slow task done"

def test_exception_propagation(pool):
    """Test exception propagation from tasks"""
    def task_with_type_error():
        return 1 + "2"  # Will raise TypeError
    
    pool.submit("type_error", task_with_type_error)
    
    with pytest.raises(TypeError):
        pool.get_result("type_error")

def test_task_result_persistence(pool):
    """Test that task results persist until explicitly cleared"""
    future = pool.submit("persistent", simple_task)
    
    # Wait for task to complete
    time.sleep(0.1)
    
    # Result should still be available
    assert pool.get_result("persistent") == "done"
    
    # Result should still be available for multiple gets
    assert pool.get_result("persistent") == "done"
