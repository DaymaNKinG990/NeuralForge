import queue
import logging
import weakref
from typing import Any, Callable, Dict, Optional, Set
from concurrent.futures import Future
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex, QWaitCondition
from PyQt6.QtWidgets import QApplication
import time
import atexit

logger = logging.getLogger(__name__)

class PreloaderThread(QThread):
    """Thread for processing preload queue"""
    
    item_complete = pyqtSignal(str, object)  # resource_id, result
    item_error = pyqtSignal(str, str)  # resource_id, error_msg
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._queue = queue.Queue()
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self._stop_requested = False
        
    def queue_item(self, resource_id: str, loader: Callable[[], Any]):
        """Add item to preload queue"""
        self._queue.put((resource_id, loader))
        self._condition.wakeOne()
        
    def stop(self):
        """Request thread to stop"""
        self._mutex.lock()
        self._stop_requested = True
        self._mutex.unlock()
        self._condition.wakeOne()
        
    def run(self):
        """Process items in the queue"""
        logger.debug("PreloaderThread started")
        
        while True:
            self._mutex.lock()
            if self._stop_requested:
                self._mutex.unlock()
                break
            self._mutex.unlock()
            
            try:
                try:
                    item = self._queue.get_nowait()
                except queue.Empty:
                    # Wait for new items or stop request
                    self._mutex.lock()
                    if not self._stop_requested:
                        self._condition.wait(self._mutex)
                    self._mutex.unlock()
                    continue
                
                resource_id, loader = item
                
                try:
                    result = loader()
                    self.item_complete.emit(resource_id, result)
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error preloading resource {resource_id}: {error_msg}")
                    self.item_error.emit(resource_id, error_msg)
                finally:
                    self._queue.task_done()
                    
            except Exception as e:
                logger.error(f"Error in preloader thread: {str(e)}", exc_info=True)
        
        logger.debug("PreloaderThread stopped")

class PreloadManager(QObject):
    """Manages preloading of resources"""
    
    _instance = None
    
    @classmethod
    def instance(cls) -> 'PreloadManager':
        """Get the global PreloadManager instance"""
        if cls._instance is None:
            # Create instance with QApplication as parent to ensure proper cleanup
            app = QApplication.instance()
            if app is None:
                raise RuntimeError("QApplication must be created before PreloadManager")
            cls._instance = PreloadManager(parent=app)
            # Register cleanup on application quit
            app.aboutToQuit.connect(cls._instance.cleanup)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance - mainly for testing"""
        if cls._instance is not None:
            cls._instance.cleanup()
            cls._instance = None
    
    preload_complete = pyqtSignal(str)  # Emitted when a resource is preloaded
    preload_error = pyqtSignal(str, str)  # Emitted on error (resource_id, error_msg)
    
    def __init__(self, parent: Optional[QObject] = None):
        if parent is None:
            raise RuntimeError("PreloadManager must have a parent QObject")
        super().__init__(parent)
        self._thread = PreloaderThread(self)
        self._mutex = QMutex()
        self._resources: Dict[str, Any] = {}
        self._futures: Dict[str, Future] = {}
        
        # Connect thread signals
        self._thread.item_complete.connect(self._on_item_complete)
        self._thread.item_error.connect(self._on_item_error)
        
        # Start thread immediately
        self._thread.start()
        logger.debug("PreloadManager initialized")
    
    def cleanup(self):
        """Clean up resources and stop thread"""
        logger.debug("PreloadManager cleanup started")
        if self._thread.isRunning():
            self._thread.stop()
            if not self._thread.wait(1000):  # Wait up to 1 second
                logger.warning("PreloadManager thread did not stop gracefully, forcing termination")
                self._thread.terminate()
                self._thread.wait()
        
        self._mutex.lock()
        try:
            # Cancel pending futures
            for future in self._futures.values():
                if not future.done():
                    future.cancel()
            self._futures.clear()
            self._resources.clear()
        finally:
            self._mutex.unlock()
        
        logger.debug("PreloadManager cleanup completed")
    
    def stop(self):
        """Stop the preload manager"""
        if self._thread.isRunning():
            logger.debug("Stopping PreloadManager thread...")
            self._thread.stop()
            
            # Give the thread a chance to stop gracefully
            if not self._thread.wait(1000):  # Wait up to 1 second
                logger.warning("PreloadManager thread did not stop gracefully, forcing termination")
                self._thread.terminate()
                self._thread.wait()  # Must still wait after terminate
            
            self._mutex.lock()
            try:
                # Cancel pending futures
                for future in self._futures.values():
                    if not future.done():
                        future.cancel()
                self._futures.clear()
                self._resources.clear()
            finally:
                self._mutex.unlock()
            
            logger.debug("PreloadManager stopped")
    
    def preload(self, resource_id: str, loader: Callable[[], Any]) -> Future:
        """Queue a resource for preloading"""
        self._mutex.lock()
        try:
            # Return existing future if already loading
            if resource_id in self._futures:
                future = self._futures[resource_id]
                self._mutex.unlock()
                return future
            
            # Create new future
            future = Future()
            self._futures[resource_id] = future
            
            # Queue the load request
            self._thread.queue_item(resource_id, loader)
            
            return future
        finally:
            self._mutex.unlock()
    
    def _on_item_complete(self, resource_id: str, result: Any):
        """Handle completed preload item"""
        self._mutex.lock()
        try:
            self._resources[resource_id] = result
            if resource_id in self._futures:
                self._futures[resource_id].set_result(result)
                del self._futures[resource_id]
            self.preload_complete.emit(resource_id)
        finally:
            self._mutex.unlock()
    
    def _on_item_error(self, resource_id: str, error_msg: str):
        """Handle preload item error"""
        self._mutex.lock()
        try:
            if resource_id in self._futures:
                self._futures[resource_id].set_exception(
                    RuntimeError(error_msg))
                del self._futures[resource_id]
            self.preload_error.emit(resource_id, error_msg)
        finally:
            self._mutex.unlock()
    
    def get_resource(self, resource_id: str) -> Optional[Any]:
        """Get a preloaded resource if available"""
        self._mutex.lock()
        try:
            return self._resources.get(resource_id)
        finally:
            self._mutex.unlock()
    
    def is_loaded(self, resource_id: str) -> bool:
        """Check if a resource is loaded"""
        self._mutex.lock()
        try:
            return resource_id in self._resources
        finally:
            self._mutex.unlock()
    
    def clear(self):
        """Clear all preloaded resources"""
        self._mutex.lock()
        try:
            self._resources.clear()
            # Cancel pending futures
            for future in self._futures.values():
                if not future.done():
                    future.cancel()
            self._futures.clear()
        finally:
            self._mutex.unlock()

class ComponentPreloader(QObject):
    """Preloader for UI components with thread-safe caching"""
    
    _instance = None
    
    @classmethod
    def instance(cls) -> 'ComponentPreloader':
        """Get the global ComponentPreloader instance"""
        if cls._instance is None:
            # Create instance with QApplication as parent
            app = QApplication.instance()
            if app is None:
                raise RuntimeError("QApplication must be created before ComponentPreloader")
            cls._instance = ComponentPreloader(parent=app)
            # Register cleanup on application quit
            app.aboutToQuit.connect(cls._instance.cleanup)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance - mainly for testing"""
        if cls._instance is not None:
            cls._instance.cleanup()
            cls._instance = None

    component_ready = pyqtSignal(str)  # Emitted when component is ready
    component_error = pyqtSignal(str, str)  # Emitted on error (component_id, error_msg)
    
    def __init__(self, parent: Optional[QObject] = None):
        if parent is None:
            raise RuntimeError("ComponentPreloader must have a parent QObject")
        super().__init__(parent)
        self._components: Dict[str, weakref.ref] = {}  # Use weak references
        self._loading: Set[str] = set()
        self._mutex = QMutex()
        self._futures: Dict[str, Future] = {}
        self._logger = logging.getLogger(__name__)
        
    def cleanup(self):
        """Clean up resources"""
        self._mutex.lock()
        try:
            self._components.clear()
            self._loading.clear()
            for future in self._futures.values():
                if not future.done():
                    future.cancel()
            self._futures.clear()
        finally:
            self._mutex.unlock()
        ComponentPreloader._instance = None
        self._logger.debug("ComponentPreloader cleanup completed")

    def preload_component(self, component_class: type, *args, **kwargs) -> Future:
        """Preload a component asynchronously"""
        component_id = f"{component_class.__module__}.{component_class.__name__}"
        
        with self._mutex:
            # Check if component exists and is still alive
            if component_id in self._components:
                component = self._components[component_id]()
                if component is not None:
                    future = Future()
                    future.set_result(component)
                    return future
                else:
                    # Remove dead reference
                    del self._components[component_id]
            
            if component_id in self._futures:
                return self._futures[component_id]
            
            future = Future()
            self._futures[component_id] = future
            
            def create_component():
                try:
                    start_time = time.time()
                    instance = component_class(*args, **kwargs)
                    
                    # Initialize but don't show
                    if hasattr(instance, 'hide'):
                        instance.hide()
                    
                    with self._mutex:
                        self._components[component_id] = weakref.ref(instance)
                        if component_id in self._futures:
                            self._futures[component_id].set_result(instance)
                            del self._futures[component_id]
                    
                    load_time = time.time() - start_time
                    self._logger.debug(
                        f"Preloaded component {component_id} in {load_time:.3f}s"
                    )
                    self.component_ready.emit(component_id)
                    
                except Exception as e:
                    error_msg = str(e)
                    self._logger.error(
                        f"Error preloading component {component_id}: {error_msg}"
                    )
                    with self._mutex:
                        if component_id in self._futures:
                            self._futures[component_id].set_exception(e)
                            del self._futures[component_id]
                    self.component_error.emit(component_id, error_msg)
            
            # Use global preload manager to create component
            preload_manager.preload(component_id, create_component)
            return future
    
    def get_component(self, component_class: type) -> Optional[Any]:
        """Get a preloaded component if available"""
        component_id = f"{component_class.__module__}.{component_class.__name__}"
        with self._mutex:
            if component_id in self._components:
                component = self._components[component_id]()
                if component is not None:
                    return component
                del self._components[component_id]
            return None
    
    def is_loaded(self, component_class: type) -> bool:
        """Check if a component is loaded"""
        component_id = f"{component_class.__module__}.{component_class.__name__}"
        with self._mutex:
            if component_id in self._components:
                component = self._components[component_id]()
                if component is not None:
                    return True
                del self._components[component_id]
            return False
    
    def clear(self):
        """Clear all preloaded components"""
        with self._mutex:
            self._components.clear()
            for future in self._futures.values():
                if not future.done():
                    future.cancel()
            self._futures.clear()

# Initialize global instances
def get_preload_manager() -> PreloadManager:
    """Get the global PreloadManager instance"""
    return PreloadManager.instance()

def get_component_preloader() -> ComponentPreloader:
    """Get the global ComponentPreloader instance"""
    return ComponentPreloader.instance()

# Global instance accessors
preload_manager = get_preload_manager
component_preloader = get_component_preloader
