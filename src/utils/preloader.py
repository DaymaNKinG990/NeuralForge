from typing import List, Dict, Set, Optional, Any
import threading
import queue
import time
import logging
import zlib
import pickle
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class PreloadTask:
    """Задача предварительной загрузки"""
    module_path: str
    priority: int
    dependencies: List[str]
    estimated_size: int
    compression_level: int = 6

class PreloadManager:
    """Менеджер предварительной загрузки"""
    
    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._task_queue = queue.PriorityQueue()
        self._loaded_modules: Set[str] = set()
        self._compressed_cache: Dict[str, bytes] = {}
        self._loading_stats: Dict[str, float] = {}
        self._logger = logging.getLogger(__name__)
        
        # Запускаем обработчик очереди
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(
            target=self._process_queue,
            daemon=True
        )
        self._worker_thread.start()
        
    def schedule_preload(self, task: PreloadTask):
        """Запланировать предварительную загрузку"""
        # Проверяем зависимости
        missing_deps = [
            dep for dep in task.dependencies
            if dep not in self._loaded_modules
        ]
        
        if missing_deps:
            # Добавляем зависимости с повышенным приоритетом
            for dep in missing_deps:
                dep_task = PreloadTask(
                    module_path=dep,
                    priority=task.priority - 1,
                    dependencies=[],
                    estimated_size=0
                )
                self._task_queue.put((dep_task.priority, dep_task))
                
        self._task_queue.put((task.priority, task))
        
    def get_compressed(self, module_path: str) -> Optional[bytes]:
        """Получить сжатые данные из кэша"""
        return self._compressed_cache.get(module_path)
        
    def get_loading_stats(self) -> Dict[str, float]:
        """Получить статистику загрузки"""
        return dict(self._loading_stats)
        
    def _process_queue(self):
        """Обработка очереди загрузки"""
        while not self._stop_event.is_set():
            try:
                priority, task = self._task_queue.get(timeout=1.0)
                
                # Пропускаем уже загруженные
                if task.module_path in self._loaded_modules:
                    continue
                    
                # Проверяем зависимости
                deps_ready = all(
                    dep in self._loaded_modules
                    for dep in task.dependencies
                )
                
                if not deps_ready:
                    # Возвращаем в очередь с пониженным приоритетом
                    self._task_queue.put((priority + 1, task))
                    continue
                    
                # Запускаем загрузку
                self._executor.submit(
                    self._load_and_compress,
                    task
                )
                
            except queue.Empty:
                continue
                
    def _load_and_compress(self, task: PreloadTask):
        """Загрузка и сжатие модуля"""
        try:
            start_time = time.time()
            
            # Загружаем модуль
            module = __import__(task.module_path, fromlist=['*'])
            
            # Сериализуем и сжимаем
            data = pickle.dumps(module)
            compressed = zlib.compress(
                data,
                level=task.compression_level
            )
            
            # Сохраняем в кэш
            self._compressed_cache[task.module_path] = compressed
            self._loaded_modules.add(task.module_path)
            
            load_time = time.time() - start_time
            self._loading_stats[task.module_path] = load_time
            
            compression_ratio = len(compressed) / len(data)
            self._logger.debug(
                f"Preloaded {task.module_path} in {load_time:.3f}s "
                f"(compression ratio: {compression_ratio:.2f})"
            )
            
        except Exception as e:
            self._logger.error(
                f"Error preloading {task.module_path}: {e}"
            )
            
    def stop(self):
        """Остановка менеджера"""
        self._stop_event.set()
        self._worker_thread.join()
        self._executor.shutdown()

class ComponentPreloader:
    """Предварительная загрузка компонентов UI"""
    
    def __init__(self):
        self._preloaded: Dict[str, Any] = {}
        self._usage_stats: Dict[str, int] = defaultdict(int)
        self._logger = logging.getLogger(__name__)
        
    def preload_component(self, component_class: type, *args, **kwargs):
        """Предварительная загрузка компонента"""
        key = f"{component_class.__module__}.{component_class.__name__}"
        
        if key not in self._preloaded:
            try:
                start_time = time.time()
                instance = component_class(*args, **kwargs)
                
                # Инициализируем, но не показываем
                if hasattr(instance, 'hide'):
                    instance.hide()
                    
                self._preloaded[key] = instance
                
                load_time = time.time() - start_time
                self._logger.debug(
                    f"Preloaded component {key} in {load_time:.3f}s"
                )
                
            except Exception as e:
                self._logger.error(
                    f"Error preloading component {key}: {e}"
                )
                
    def get_component(self, component_class: type) -> Optional[Any]:
        """Получить предзагруженный компонент"""
        key = f"{component_class.__module__}.{component_class.__name__}"
        
        if key in self._preloaded:
            self._usage_stats[key] += 1
            return self._preloaded[key]
            
        return None
        
    def clear_unused(self, threshold: int = 0):
        """Очистить неиспользуемые компоненты"""
        for key, count in list(self._usage_stats.items()):
            if count <= threshold:
                if key in self._preloaded:
                    del self._preloaded[key]
                del self._usage_stats[key]

# Глобальные экземпляры
preload_manager = PreloadManager()
component_preloader = ComponentPreloader()
