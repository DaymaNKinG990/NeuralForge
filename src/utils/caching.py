"""Enhanced caching system with lazy loading integration and metric-specific optimizations."""
from typing import Any, Callable, Dict, Optional, TypeVar, Generic, List, Set
from dataclasses import dataclass, field
import time
import weakref
import threading
import logging
import psutil
from enum import Enum
from .lazy_loading import LoadPriority, component_loader
from functools import wraps

T = TypeVar('T')

class CacheEventType(Enum):
    """Cache event types for monitoring."""
    HIT = "hit"
    MISS = "miss"
    EVICT = "evict"
    EXPIRE = "expire"
    PREFETCH = "prefetch"
    MEMORY_PRESSURE = "memory_pressure"

@dataclass
class CacheEvent:
    """Cache event for monitoring."""
    type: CacheEventType
    key: str
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""
    value: T
    expiry: float
    last_access: float = field(default_factory=time.time)
    access_count: int = 0
    size_estimate: int = 0
    priority: LoadPriority = LoadPriority.MEDIUM
    weak_ref: Optional[weakref.ref] = None
    metric_type: Optional[str] = None
    prefetch: bool = False

class CacheManager:
    """Manages cache configuration and monitoring."""
    
    def __init__(self):
        """Initialize cache manager."""
        self._caches: Dict[str, 'Cache'] = {}
        self._monitors: List[Callable[[CacheEvent], None]] = []
        self._lock = threading.Lock()
    
    def register_cache(self, name: str, cache: 'Cache'):
        """Register a cache instance."""
        with self._lock:
            self._caches[name] = cache
    
    def get_cache(self, name: str) -> Optional['Cache']:
        """Get a registered cache by name."""
        return self._caches.get(name)
    
    def add_monitor(self, monitor: Callable[[CacheEvent], None]):
        """Add a cache event monitor."""
        self._monitors.append(monitor)
    
    def notify_event(self, event: CacheEvent):
        """Notify monitors of cache event."""
        for monitor in self._monitors:
            try:
                monitor(event)
            except Exception as e:
                logging.error(f"Cache monitor error: {e}")

class Cache:
    """Enhanced cache with lazy loading support and metric optimizations."""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 3600,
        cleanup_interval: float = 300,
        memory_limit_mb: Optional[float] = None
    ):
        """Initialize cache.
        
        Args:
            max_size: Maximum number of entries
            default_ttl: Default time-to-live in seconds
            cleanup_interval: Cleanup interval in seconds
            memory_limit_mb: Memory limit in MB
        """
        self._entries: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cleanup_interval = cleanup_interval
        self._memory_limit = (memory_limit_mb or 
                           psutil.virtual_memory().total * 0.1 / (1024 * 1024))
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
        self._current_memory = 0
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker)
        self._cleanup_thread.daemon = True
        self._cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        self._maybe_cleanup()
        
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                cache_manager.notify_event(CacheEvent(CacheEventType.MISS, key))
                return None
                
            if time.time() > entry.expiry:
                self._remove_entry(key)
                cache_manager.notify_event(
                    CacheEvent(CacheEventType.EXPIRE, key)
                )
                return None
                
            entry.last_access = time.time()
            entry.access_count += 1
            cache_manager.notify_event(CacheEvent(CacheEventType.HIT, key))
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        priority: LoadPriority = LoadPriority.MEDIUM,
        size_estimate: Optional[int] = None,
        metric_type: Optional[str] = None,
        prefetch: bool = False
    ):
        """Set cache entry."""
        self._maybe_cleanup()
        
        with self._lock:
            # Check memory limit
            if self._current_memory >= self._memory_limit:
                self._evict_entries()
            
            # Create entry
            entry = CacheEntry(
                value=value,
                expiry=time.time() + (ttl or self._default_ttl),
                size_estimate=size_estimate or 1024,
                priority=priority,
                metric_type=metric_type,
                prefetch=prefetch
            )
            
            # Update memory usage
            self._current_memory += entry.size_estimate
            
            # Store entry
            self._entries[key] = entry
            
            # Evict if over size limit
            if len(self._entries) > self._max_size:
                self._evict_entries()
    
    def _maybe_cleanup(self):
        """Run cleanup if needed."""
        if (time.time() - self._last_cleanup) > self._cleanup_interval:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up expired entries."""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._entries.items()
                if current_time > entry.expiry
            ]
            
            for key in expired_keys:
                self._remove_entry(key)
                cache_manager.notify_event(
                    CacheEvent(CacheEventType.EXPIRE, key)
                )
            
            self._last_cleanup = current_time
    
    def _cleanup_worker(self):
        """Background cleanup worker."""
        while True:
            time.sleep(self._cleanup_interval)
            try:
                self._cleanup()
            except Exception as e:
                logging.error(f"Cache cleanup error: {e}")
    
    def _remove_entry(self, key: str):
        """Remove cache entry."""
        entry = self._entries.pop(key, None)
        if entry:
            self._current_memory -= entry.size_estimate
    
    def _evict_entries(self):
        """Evict entries based on priority and usage."""
        if not self._entries:
            return
            
        # Sort entries by importance
        entries = sorted(
            self._entries.items(),
            key=lambda x: (
                x[1].priority.value,
                -x[1].access_count,
                -x[1].last_access
            )
        )
        
        # Remove least important entries
        removed = 0
        target = len(self._entries) // 2  # Remove half
        
        for key, _ in entries[:target]:
            self._remove_entry(key)
            cache_manager.notify_event(
                CacheEvent(CacheEventType.EVICT, key)
            )
            removed += 1
            
            if self._current_memory < self._memory_limit:
                break

def cache_result(
    ttl: Optional[float] = None,
    priority: LoadPriority = LoadPriority.MEDIUM,
    metric_type: Optional[str] = None
):
    """Cache function results.
    
    Args:
        ttl: Time-to-live in seconds
        priority: Cache priority
        metric_type: Type of metric for optimization
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = f"{func.__module__}.{func.__name__}:{args}:{kwargs}"
            
            # Check cache
            result = cache.get(key)
            if result is not None:
                return result
                
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(
                key,
                result,
                ttl=ttl,
                priority=priority,
                metric_type=metric_type
            )
            
            return result
        return wrapper
    return decorator

# Global instances
cache_manager = CacheManager()
cache = Cache()
cache_manager.register_cache("default", cache)
