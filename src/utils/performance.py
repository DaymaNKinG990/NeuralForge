from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Set
from functools import lru_cache
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer
from pathlib import Path
import time
import psutil
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
from dataclasses import dataclass
from queue import Queue
import inspect
import logging

T = TypeVar('T')

class PerformanceMonitor(QObject):
    """Monitor system resources and IDE performance"""
    stats_updated = pyqtSignal(dict)
    warning_triggered = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._process = None  # Initialize as None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        # Thresholds for warnings
        self.memory_threshold = 80  # Percentage
        self.cpu_threshold = 70     # Percentage
        
    @property
    def process(self):
        """Get the process instance, creating it if needed"""
        if self._process is None:
            self._process = psutil.Process()
            # Initialize CPU monitoring
            self._process.cpu_percent()
        return self._process
    
    @process.setter
    def process(self, value):
        """Set the process instance (useful for testing)"""
        self._process = value

    def update_stats(self):
        """Update performance statistics"""
        try:
            # Get process stats
            memory_percent = self.process.memory_percent()
            cpu_percent = self.process.cpu_percent()
            stats = {
                'memory_percent': memory_percent,
                'cpu_percent': cpu_percent,
                'num_threads': self.process.num_threads(),
                'io_counters': self.process.io_counters()._asdict(),
                'system_memory': psutil.virtual_memory()._asdict()
            }
            
            # Check thresholds and emit warnings first
            if memory_percent > self.memory_threshold:
                warning_msg = f"High memory usage: {memory_percent:.1f}%"
                self.warning_triggered.emit(warning_msg)
                
            if cpu_percent > self.cpu_threshold:
                warning_msg = f"High CPU usage: {cpu_percent:.1f}%"
                self.warning_triggered.emit(warning_msg)
                
            # Then emit updated stats
            self.stats_updated.emit(stats)
            
        except Exception as e:
            logging.error(f"Error updating performance stats: {str(e)}", exc_info=True)

class AsyncWorker(QThread):
    """Worker for running operations asynchronously.
    
    Signals:
        started: Emitted when the worker starts running
        finished(result): Emitted with the result when work is complete
        error(exception): Emitted when an error occurs
        progress(int): Emitted to report progress (0-100)
    """
    started = pyqtSignal()
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)
    progress = pyqtSignal(int)
    
    def __init__(self, func: Callable[..., T], *args, **kwargs):
        """Initialize worker with function and arguments.
        
        Args:
            func: Function to run asynchronously
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        """
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._is_running = False
        self._should_stop = False
        
    def start(self):
        """Start the worker thread."""
        if not self.isRunning():
            self._should_stop = False
            super().start()
        
    def run(self):
        """Execute the worker function in a separate thread."""
        try:
            # Set state and emit started signal
            self._is_running = True
            self.started.emit()
            
            # Check if function accepts progress_callback
            sig = inspect.signature(self.func)
            if 'progress_callback' in sig.parameters:
                self.kwargs['progress_callback'] = self.progress.emit
                
            # Run function and emit result
            result = self.func(*self.args, **self.kwargs)
            if not self._should_stop:
                self.finished.emit(result)
        except Exception as e:
            if not self._should_stop:
                self.error.emit(e)
        finally:
            self._is_running = False
            
    def stop(self):
        """Safely stop the worker and wait for it to finish."""
        if self._is_running:
            self._should_stop = True
            self.wait()  # Wait for worker to finish
            
    def cleanup(self):
        """Clean up worker resources and disconnect signals."""
        if self.isRunning():
            self.stop()  # Stop if still running
            
        # Disconnect all signals
        try:
            self.started.disconnect()
            self.finished.disconnect()
            self.error.disconnect()
            self.progress.disconnect()
        except:
            pass
            
        self.deleteLater()
            
    def __del__(self):
        """Cleanup when worker is deleted."""
        try:
            self.cleanup()
        except:
            pass

class FileSystemCache:
    """Cache for file system operations with TTL and size limits."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300) -> None:
        """Initialize file system cache.
        
        Args:
            max_size: Maximum number of entries to cache
            ttl: Time to live in seconds for cache entries
        """
        if not isinstance(max_size, int) or max_size <= 0:
            raise ValueError("max_size must be a positive integer")
        if not isinstance(ttl, (int, float)) or ttl <= 0:
            raise ValueError("ttl must be a positive number")
            
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self._lock = threading.Lock()
        
        # Start cleanup timer
        self._cleanup_timer = QTimer()
        self._cleanup_timer.timeout.connect(self.cleanup)
        self._cleanup_timer.start(60000)  # Cleanup every minute

    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Validate and normalize path.
        
        Args:
            path: Path to validate
            
        Returns:
            Normalized Path object
            
        Raises:
            TypeError: If path is not str or Path
            ValueError: If path is empty
        """
        if not isinstance(path, (str, Path)):
            raise TypeError("Path must be string or Path object")
        if isinstance(path, str) and not path.strip():
            raise ValueError("Path cannot be empty")
        return Path(path) if isinstance(path, str) else path

    def get_file_info(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Get cached file information.
        
        Args:
            path: Path to file to get info for
            
        Returns:
            Dict containing file information
        """
        try:
            path = self._validate_path(path)
        except (TypeError, ValueError) as e:
            raise  # Re-raise validation errors
            
        with self._lock:
            current_time = time.time()
            path_str = str(path)
            
            # Check cache and verify file hasn't been modified
            if path_str in self.cache:
                cached_info = self.cache[path_str]
                if current_time - self.access_times[path_str] < self.ttl:
                    try:
                        if cached_info['exists']:
                            stat = path.stat()
                            if (stat.st_mtime == cached_info['mtime'] and 
                                stat.st_size == cached_info['size']):
                                self.access_times[path_str] = current_time
                                return cached_info
                    except (OSError, FileNotFoundError):
                        pass  # File was deleted or can't be accessed
                        
            # Update cache
            try:
                stat = path.stat()
                info = {
                    'size': stat.st_size,
                    'mtime': stat.st_mtime,
                    'exists': True
                }
            except FileNotFoundError:
                info = {'exists': False, 'mtime': 0, 'size': 0}
            except OSError as e:
                info = {'exists': False, 'error': str(e), 'mtime': 0, 'size': 0}
                
            self.cache[path_str] = info
            self.access_times[path_str] = current_time
            self._ensure_size_limit()
            return info

    def _ensure_size_limit(self):
        """Ensure cache size is within limits"""
        while len(self.cache) > self.max_size:
            oldest = min(self.access_times.items(), key=lambda x: x[1])[0]
            del self.cache[oldest]
            del self.access_times[oldest]

    def cleanup(self):
        """Remove expired entries"""
        with self._lock:
            current_time = time.time()
            expired = [
                path for path, access_time in self.access_times.items()
                if current_time - access_time > self.ttl
            ]
            
            for path in expired:
                del self.cache[path]
                del self.access_times[path]
                
            self._ensure_size_limit()

class ThreadPool:
    """Thread pool for parallel task execution."""
    
    def __init__(self, max_workers: Optional[int] = None) -> None:
        """Initialize thread pool.
        
        Args:
            max_workers: Maximum number of worker threads. Defaults to 2x CPU cores.
        """
        self.max_workers = max_workers or (psutil.cpu_count() or 1) * 2
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.tasks: Dict[str, Future] = {}
        self._lock = threading.Lock()
        self._shutdown = False
        
    def submit(self, name: str, func: Callable[..., T], *args, **kwargs) -> Optional[Future]:
        """Submit task to thread pool.
        
        Args:
            name: Unique name for the task
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Future object or None if pool is shutdown
        """
        if self._shutdown:
            return None
            
        with self._lock:
            # Cancel existing task with same name if any
            self.cancel_task(name)
            
            try:
                future = self.executor.submit(func, *args, **kwargs)
                self.tasks[name] = future
                return future
            except Exception as e:
                logging.error(f"Error submitting task {name}: {e}")
                return None
    
    def get_result(self, name: str, timeout: Optional[float] = None) -> Optional[Any]:
        """Get result of task.
        
        Args:
            name: Task name
            timeout: Maximum time to wait for result
            
        Returns:
            Task result or None if task failed/not found
        """
        with self._lock:
            future = self.tasks.get(name)
            if not future:
                return None
                
        try:
            if future.done():
                return future.result(timeout=0)  # Don't wait if done
            elif timeout is not None:
                return future.result(timeout=timeout)
            else:
                return future.result()  # Wait indefinitely
        except TimeoutError:
            return None
        except Exception as e:
            logging.error(f"Error in task {name}: {e}")
            return None
        finally:
            with self._lock:
                # Cleanup completed task
                if name in self.tasks and future.done():
                    del self.tasks[name]
    
    def cancel_task(self, name: str) -> bool:
        """Cancel task if possible.
        
        Args:
            name: Task name
            
        Returns:
            True if task was cancelled
        """
        with self._lock:
            future = self.tasks.get(name)
            if future and not future.done():
                cancelled = future.cancel()
                if cancelled:
                    del self.tasks[name]
                return cancelled
            return False
    
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the thread pool.
        
        Args:
            wait: Wait for pending tasks to complete
        """
        self._shutdown = True
        with self._lock:
            if wait:
                # Cancel all pending tasks
                for name, future in list(self.tasks.items()):
                    if not future.done():
                        future.cancel()
            self.executor.shutdown(wait=wait)
            self.tasks.clear()

@dataclass
class MemoryUsage:
    """Track memory usage of components"""
    component: str
    size: int
    timestamp: float

class MemoryTracker:
    """Track and optimize memory usage"""
    def __init__(self):
        self.usage_history: List[MemoryUsage] = []
        self.component_sizes: Dict[str, int] = {}
        
    def track(self, component: str, size: int):
        """Track memory usage of component"""
        self.usage_history.append(MemoryUsage(
            component=component,
            size=size,
            timestamp=time.time()
        ))
        self.component_sizes[component] = size
        
    def get_total_usage(self) -> int:
        """Get total memory usage"""
        return sum(self.component_sizes.values())
        
    def get_component_usage(self, component: str) -> int:
        """Get memory usage of specific component"""
        return self.component_sizes.get(component, 0)
        
    def clear_history(self, before: float = None):
        """Clear usage history"""
        if before is None:
            self.usage_history.clear()
        else:
            self.usage_history = [
                usage for usage in self.usage_history
                if usage.timestamp >= before
            ]

# Global instances
performance_monitor = PerformanceMonitor()
file_cache = FileSystemCache()
thread_pool = ThreadPool()
memory_tracker = MemoryTracker()
