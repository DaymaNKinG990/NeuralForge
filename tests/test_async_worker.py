import pytest
from PyQt6.QtCore import QThread, Qt, QTimer, QEventLoop
from PyQt6.QtWidgets import QApplication
import time
from src.utils.performance import AsyncWorker
import logging
import sys
from weakref import ref
import gc
import traceback

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Маркируем все тесты в этом файле как требующие изоляции Qt
pytestmark = pytest.mark.qt

@pytest.fixture(scope="session")
def qapp():
    """Create the Qt Application."""
    app = QApplication.instance() or QApplication([])
    yield app
    app.quit()

@pytest.fixture
def worker(qapp):
    """Create basic worker"""
    worker = AsyncWorker(_helper_function)
    yield worker
    worker.cleanup()
    qapp.processEvents()

def _helper_wait_for_signals(qapp, timeout=3.0, interval=0.01):
    """Process Qt events for a specified duration.
    
    Args:
        qapp: QApplication instance
        timeout: Maximum time to wait in seconds
        interval: Time between event processing in seconds
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        qapp.processEvents()
        time.sleep(interval)

def _helper_wait_for_worker(qapp, worker, timeout=3.0, interval=0.01):
    """Wait for worker to complete and process events.
    
    Args:
        qapp: QApplication instance
        worker: AsyncWorker instance to wait for
        timeout: Maximum time to wait in seconds
        interval: Time between event processing in seconds
        
    Returns:
        bool: True if worker completed, False if timed out
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        qapp.processEvents()
        if not worker.isRunning():
            # Process events a bit longer to ensure all signals are delivered
            _helper_wait_for_signals(qapp, 0.1)
            return True
        time.sleep(interval)
    return False

def _helper_process_events_until(qapp, condition, timeout=3.0, interval=0.01):
    """Process events until condition is met or timeout.
    
    Args:
        qapp: QApplication instance
        condition: Callable that returns True when done waiting
        timeout: Maximum time to wait in seconds
        interval: Time between event processing in seconds
        
    Returns:
        bool: True if condition was met, False if timed out
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        qapp.processEvents()
        if condition():
            # Process events a bit longer to ensure all signals are delivered
            _helper_wait_for_signals(qapp, 0.1)
            return True
        time.sleep(interval)
    return False

def _helper_wait_for_signal(signal, timeout=3000):
    """Wait for a signal using QEventLoop.
    
    Args:
        signal: PyQt signal to wait for
        timeout: Timeout in milliseconds
        
    Returns:
        bool: True if signal received, False if timed out
    """
    loop = QEventLoop()
    received = False
    
    def on_signal(*args):
        nonlocal received
        received = True
        loop.quit()
        
    signal.connect(on_signal)
    
    try:
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(timeout)
        
        loop.exec()
        return received
    finally:
        signal.disconnect(on_signal)
        timer.stop()

def _helper_function():
    """Simple helper function for testing"""
    return "completed"

def _helper_function_with_args(x, y):
    """Helper function with arguments"""
    return x * y

def _helper_function_with_progress(progress_callback=None):
    """Helper function that reports progress"""
    if progress_callback:
        for i in range(0, 101, 20):
            progress_callback(i)
            time.sleep(0.1)  # Small delay to simulate work
    return "completed"

def _helper_error_function():
    """Helper function that raises an error"""
    raise ValueError("test error")

def _helper_long_running_function(*args, **kwargs):
    """Helper function that simulates a long running task.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments including optional progress_callback
        
    Returns:
        tuple: (args, kwargs) without progress_callback
    """
    # Small delay to simulate work
    time.sleep(0.1)
    
    # Remove progress_callback from kwargs if present
    kwargs_copy = kwargs.copy()
    if 'progress_callback' in kwargs_copy:
        del kwargs_copy['progress_callback']
        
    return (args, kwargs_copy)

def _helper_error_with_progress(progress_callback=None):
    """Helper function that reports progress then raises error"""
    if progress_callback:
        for i in range(0, 60, 20):
            progress_callback(i)
            time.sleep(0.1)
    raise ValueError("error after progress")

def _helper_stoppable_function(progress_callback=None):
    """Helper function that can be stopped"""
    if progress_callback:
        for i in range(0, 101, 10):
            progress_callback(i)
            time.sleep(0.2)  # Longer delay to allow stopping
    return "completed"

@pytest.mark.qt
def test_worker_creation(worker):
    """Test worker initialization"""
    assert isinstance(worker, QThread)
    assert worker.func == _helper_function
    assert len(worker.args) == 0
    assert len(worker.kwargs) == 0

@pytest.mark.qt
def test_worker_with_args(qapp):
    """Test worker with arguments"""
    worker = AsyncWorker(_helper_function_with_args, 5, 3)
    try:
        assert worker.args == (5, 3)
        assert len(worker.kwargs) == 0
    finally:
        worker.cleanup()
        qapp.processEvents()

@pytest.mark.qt
def test_worker_with_kwargs(qapp):
    """Test worker with keyword arguments"""
    worker = AsyncWorker(_helper_function_with_args, x=5, y=3)
    try:
        assert len(worker.args) == 0
        assert worker.kwargs == {"x": 5, "y": 3}
    finally:
        worker.cleanup()
        qapp.processEvents()

@pytest.mark.qt
def test_successful_execution(qtbot, worker, qapp):
    """Test successful function execution"""
    result = None
    
    def on_finished(res):
        nonlocal result
        result = res
        
    worker.finished.connect(on_finished)
    
    worker.start()
    _helper_process_events_until(qapp, lambda: result is not None, timeout=3.0)
    
    assert result == "completed"
    assert not worker.isRunning()

@pytest.mark.qt
def test_execution_with_args(qtbot, qapp):
    """Test execution with arguments"""
    worker = AsyncWorker(_helper_function_with_args, 5, 3)
    result = None
    
    try:
        def on_finished(res):
            nonlocal result
            result = res
        
        worker.finished.connect(on_finished)
        
        worker.start()
        _helper_process_events_until(qapp, lambda: result is not None, timeout=3.0)
        
        assert result == 15
        assert not worker.isRunning()
    finally:
        worker.cleanup()
        qapp.processEvents()

@pytest.mark.qt
def test_progress_reporting(qtbot, qapp):
    """Test progress signal emission"""
    worker = AsyncWorker(_helper_function_with_progress)
    progress_values = []
    finished = False
    
    try:
        def on_progress(value):
            progress_values.append(value)
            
        def on_finished(result):
            nonlocal finished
            finished = True
            
        worker.progress.connect(on_progress)
        worker.finished.connect(on_finished)
        
        worker.start()
        assert _helper_wait_for_worker(qapp, worker)
        _helper_wait_for_signals(qapp, 0.1)  # Wait a bit more for signals
        
        assert progress_values == [0, 20, 40, 60, 80, 100]
        assert finished
        assert not worker.isRunning()
        
    finally:
        worker.cleanup()
        qapp.processEvents()

@pytest.mark.qt
def test_error_handling(qtbot, qapp):
    """Test error signal emission"""
    worker = AsyncWorker(_helper_error_function)
    error_caught = None
    
    try:
        def on_error(error):
            nonlocal error_caught
            error_caught = error
            
        worker.error.connect(on_error)
        
        worker.start()
        _helper_process_events_until(qapp, lambda: error_caught is not None, timeout=3.0)
        
        assert isinstance(error_caught, ValueError)
        assert str(error_caught) == "test error"
        assert not worker.isRunning()
    finally:
        worker.cleanup()
        qapp.processEvents()

@pytest.mark.qt
def test_multiple_workers(qtbot, qapp):
    """Test running multiple workers simultaneously"""
    results = {}  # Use dict to ensure thread safety
    workers = []
    
    try:
        # Create workers with different arguments
        for i in range(3):
            worker = AsyncWorker(_helper_function_with_args, i, i)
            workers.append(worker)
            
            def make_handler(idx):
                def on_finished(result):
                    results[idx] = result
                return on_finished
            
            worker.finished.connect(make_handler(i))
            worker.start()
        
        # Wait for all workers to complete
        for worker in workers:
            assert _helper_wait_for_worker(qapp, worker)
        
        # Wait a bit more for signals
        _helper_wait_for_signals(qapp, 0.1)
        
        # Verify results
        assert len(results) == 3
        assert results == {0: 0, 1: 1, 2: 4}  # i * i for i in range(3)
        
    finally:
        for worker in workers:
            worker.cleanup()
            qapp.processEvents()

@pytest.mark.qt
def test_worker_cleanup(qtbot, qapp):
    """Test worker cleanup after completion"""
    worker = AsyncWorker(_helper_function)
    worker_ref = ref(worker)
    
    try:
        worker.start()
        assert _helper_wait_for_worker(qapp, worker)
        
        worker.cleanup()
        worker = None
        
        gc.collect()
        qapp.processEvents()
        
        start_time = time.time()
        while time.time() - start_time < 3.0:
            gc.collect()
            qapp.processEvents()
            if worker_ref() is None:
                break
            time.sleep(0.1)
        
        assert worker_ref() is None
        
    finally:
        if worker_ref() is not None:
            worker_ref().cleanup()
            qapp.processEvents()

@pytest.mark.qt
def test_worker_state(qtbot, qapp):
    """Test worker state transitions during execution."""
    worker = AsyncWorker(_helper_long_running_function)
    started = False
    
    try:
        # Check initial state
        assert not worker.isRunning()
        assert not worker._is_running
        assert not worker._should_stop
        
        # Connect started signal
        def on_started():
            nonlocal started
            started = True
            
        worker.started.connect(on_started)
        
        # Start worker and wait for started signal
        worker.start()
        assert _helper_wait_for_signal(worker.started), "Worker failed to emit started signal"
        
        # Verify running state
        assert started, "Worker started signal handler not called"
        assert worker._is_running, "Worker _is_running flag not set"
        assert worker.isRunning(), "Worker thread not running"
        assert not worker._should_stop, "Worker _should_stop flag incorrectly set"
        
        # Wait for completion
        assert _helper_wait_for_signal(worker.finished), "Worker failed to emit finished signal"
        
        # Verify stopped state
        assert not worker._is_running, "Worker _is_running flag not cleared"
        assert not worker.isRunning(), "Worker thread still running"
        assert not worker._should_stop, "Worker _should_stop flag incorrectly set"
        
    finally:
        worker.cleanup()
        qapp.processEvents()

@pytest.mark.qt
def test_concurrent_access(qtbot, qapp):
    """Test concurrent access to worker attributes during execution"""
    test_args = (1, 2)
    test_kwargs = {"x": 3, "y": 4}
    worker = AsyncWorker(_helper_long_running_function, *test_args, **test_kwargs)
    started = False
    finished = False
    
    try:
        # Check initial state
        assert not worker.isRunning()
        assert not worker._is_running
        assert worker.func == _helper_long_running_function
        assert worker.args == test_args
        assert worker.kwargs == test_kwargs
        
        # Connect signals before starting
        def on_started():
            nonlocal started
            started = True
            
        def on_finished(result):
            nonlocal finished
            finished = True
            
        worker.started.connect(on_started)
        worker.finished.connect(on_finished)
        
        # Start worker and wait for started signal
        worker.start()
        assert _helper_wait_for_signal(worker.started), "Worker failed to emit started signal"
            
        # Verify worker started properly
        assert started, "Worker started signal handler not called"
        assert worker._is_running, "Worker _is_running flag not set"
        assert worker.isRunning(), "Worker thread not running"
        assert not worker._should_stop
        assert worker.func == _helper_long_running_function
        assert worker.args == test_args
        assert worker.kwargs == test_kwargs
        
        # Wait for completion
        assert _helper_wait_for_signal(worker.finished), "Worker failed to emit finished signal"
            
        # Verify worker finished properly
        assert finished, "Worker finished signal handler not called"
        assert not worker._is_running, "Worker _is_running flag not cleared"
        assert not worker.isRunning(), "Worker thread still running"
        assert not worker._should_stop
        assert worker.func == _helper_long_running_function
        assert worker.args == test_args
        assert worker.kwargs == test_kwargs
        
    finally:
        worker.cleanup()
        qapp.processEvents()

@pytest.mark.qt
def test_worker_cancellation(qtbot, qapp):
    """Test worker cancellation during execution"""
    worker = AsyncWorker(_helper_stoppable_function)
    stopped = False
    progress_values = []
    
    try:
        def on_progress(value):
            progress_values.append(value)
            
        worker.progress.connect(on_progress)
        
        worker.start()
        _helper_process_events_until(qapp, lambda: worker.isRunning(), timeout=1.0)
        
        assert worker.isRunning()
        assert not worker._should_stop
        
        worker.stop()
        assert worker._should_stop
        
        _helper_process_events_until(qapp, lambda: not worker.isRunning(), timeout=3.0)
        assert not worker.isRunning()
        assert len(progress_values) > 0  # Убеждаемся что был прогресс до остановки
        
    finally:
        worker.cleanup()
        qapp.processEvents()

@pytest.mark.qt
def test_worker_restart(qtbot, qapp):
    """Test restarting a worker after completion"""
    worker = AsyncWorker(_helper_function_with_progress)
    results = []
    progress_values = []
    
    try:
        def on_progress(value):
            progress_values.append(value)
            
        def on_finished(result):
            results.append(result)
            
        worker.progress.connect(on_progress)
        worker.finished.connect(on_finished)
        
        worker.start()
        assert _helper_wait_for_worker(qapp, worker)
        _helper_wait_for_signals(qapp, 0.1)  # Wait for signals
        
        assert len(results) == 1
        assert results[0] == "completed"
        assert progress_values == [0, 20, 40, 60, 80, 100]
        assert not worker.isRunning()
        
        results.clear()
        progress_values.clear()
        
        worker.start()
        assert _helper_wait_for_worker(qapp, worker)
        _helper_wait_for_signals(qapp, 0.1)  # Wait for signals
        
        assert len(results) == 1
        assert results[0] == "completed"
        assert progress_values == [0, 20, 40, 60, 80, 100]
        assert not worker.isRunning()
        
    finally:
        worker.cleanup()
        qapp.processEvents()

@pytest.mark.qt
def test_worker_exception_details(qtbot, qapp):
    """Test detailed exception information and traceback"""
    def nested_error_function():
        def inner_function():
            raise ValueError("test error")
        return inner_function()
    
    worker = AsyncWorker(nested_error_function)
    error_info = None
    
    try:
        def on_error(error):
            nonlocal error_info
            error_info = error
            
        worker.error.connect(on_error)
        
        worker.start()
        assert _helper_wait_for_worker(qapp, worker)
        _helper_wait_for_signals(qapp, 0.1)  # Wait for signals
        
        assert isinstance(error_info, ValueError)
        assert str(error_info) == "test error"
        
        assert error_info.__traceback__ is not None
        tb_list = traceback.extract_tb(error_info.__traceback__)
        
        function_names = [frame.name for frame in tb_list]
        assert 'inner_function' in function_names
        assert 'nested_error_function' in function_names
        
        assert not worker.isRunning()
        assert not worker._should_stop
        
    finally:
        worker.cleanup()
        qapp.processEvents()

@pytest.mark.qt
def test_worker_memory_cleanup(qtbot, qapp):
    """Test memory cleanup after worker completion and error conditions"""
    def create_and_run_worker(func):
        """Helper function to create and run worker"""
        worker = AsyncWorker(func)
        worker_ref = ref(worker)
        
        try:
            # Start worker and wait for completion
            worker.start()
            assert _helper_wait_for_worker(qapp, worker)
            
            # Cleanup worker
            worker.cleanup()
            worker = None
            
            # Force garbage collection
            gc.collect()
            qapp.processEvents()
            
            # Wait for worker to be garbage collected
            start_time = time.time()
            while time.time() - start_time < 3.0:
                if worker_ref() is None:
                    break
                gc.collect()
                qapp.processEvents()
                time.sleep(0.1)
            
            assert worker_ref() is None
            
        finally:
            if worker_ref() is not None:
                worker_ref().cleanup()
                qapp.processEvents()
    
    # Test cleanup after successful completion
    create_and_run_worker(_helper_function)
    
    # Test cleanup after error
    create_and_run_worker(_helper_error_function)
    
    # Test cleanup after stop
    worker = AsyncWorker(_helper_stoppable_function)
    worker_ref = ref(worker)
    
    try:
        # Start worker and wait for it to begin
        worker.start()
        assert _helper_process_events_until(
            qapp,
            lambda: worker.isRunning(),
            timeout=3.0
        ), "Worker failed to start running"
        
        # Stop worker and wait for completion
        worker.stop()
        assert _helper_wait_for_worker(qapp, worker)
        
        # Cleanup worker
        worker.cleanup()
        worker = None
        
        # Force garbage collection
        gc.collect()
        qapp.processEvents()
        
        # Wait for worker to be garbage collected
        start_time = time.time()
        while time.time() - start_time < 3.0:
            if worker_ref() is None:
                break
            gc.collect()
            qapp.processEvents()
            time.sleep(0.1)
        
        assert worker_ref() is None
        
    finally:
        if worker_ref() is not None:
            worker_ref().cleanup()
            qapp.processEvents()

@pytest.mark.qt
def test_worker_signal_order(qtbot, qapp):
    """Test the order of signal emissions in different scenarios"""
    def check_signal_order(worker_func, expected_signals):
        worker = AsyncWorker(worker_func)
        signal_order = []
        
        try:
            def on_progress(value):
                signal_order.append(f'progress_{value}')
                
            def on_finished(result):
                signal_order.append(f'finished_{result}')
                
            def on_error(error):
                signal_order.append(f'error_{str(error)}')
            
            worker.progress.connect(on_progress)
            worker.finished.connect(on_finished)
            worker.error.connect(on_error)
            
            worker.start()
            assert _helper_wait_for_worker(qapp, worker)
            _helper_wait_for_signals(qapp, 0.1)  # Wait for signals
            
            assert signal_order == expected_signals
            
        finally:
            worker.cleanup()
            qapp.processEvents()
    
    check_signal_order(
        _helper_function_with_progress,
        ['progress_0', 'progress_20', 'progress_40', 'progress_60', 'progress_80', 'progress_100', 'finished_completed']
    )
    
    check_signal_order(
        _helper_error_function,
        ['error_test error']
    )
    
    worker = AsyncWorker(_helper_stoppable_function)
    signal_order = []
    
    try:
        worker.progress.connect(lambda v: signal_order.append(f'progress_{v}'))
        
        worker.start()
        _helper_wait_for_signals(qapp, 0.5)  # Wait for some progress
        
        worker.stop()
        assert _helper_wait_for_worker(qapp, worker)
        _helper_wait_for_signals(qapp, 0.1)  # Wait for final signals
        
        assert any(s.startswith('progress_') for s in signal_order)
        assert not worker.isRunning()
        assert worker._should_stop
        
    finally:
        worker.cleanup()
        qapp.processEvents()

@pytest.mark.qt
def test_error_handling_with_progress(qtbot, qapp):
    """Test error handling with progress updates"""
    worker = AsyncWorker(_helper_error_with_progress)  # Pass function, don't call it
    progress_values = []
    error_info = None
    signal_order = []
    
    try:
        def on_progress(value):
            progress_values.append(value)
            signal_order.append(f'progress_{value}')
            
        def on_error(error):
            nonlocal error_info
            error_info = error
            signal_order.append('error')
            
        worker.progress.connect(on_progress)
        worker.error.connect(on_error)
        
        # Start worker and wait for completion or error
        worker.start()
        assert _helper_wait_for_worker(qapp, worker)
        _helper_wait_for_signals(qapp, 0.1)  # Wait for signals
        
        # Verify progress before error
        assert len(progress_values) > 0
        assert all(0 <= v <= 100 for v in progress_values)
        
        # Verify error details
        assert isinstance(error_info, ValueError)
        assert str(error_info) == "error after progress"
        
        # Verify signal order
        assert all(s.startswith('progress_') for s in signal_order[:-1])
        assert signal_order[-1] == 'error'
        
        # Verify worker state
        assert not worker.isRunning()
        assert not worker._should_stop
        
    finally:
        worker.cleanup()
        qapp.processEvents()
