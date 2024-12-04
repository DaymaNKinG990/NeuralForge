from typing import Any, Dict, Optional, List, Tuple
import time
import json
import os
import pickle
from dataclasses import dataclass
from datetime import datetime
import threading
import logging
from concurrent.futures import ThreadPoolExecutor

@dataclass
class CacheEntry:
    """Элемент кэша с метаданными"""
    key: str
    value: Any
    expiry: float
    size: int
    last_access: float
    access_count: int

class CacheManager:
    """Менеджер кэширования с различными стратегиями"""
    
    def __init__(self, max_size_mb: float = 100, max_entries: int = 1000):
        self.max_size = max_size_mb * 1024 * 1024  # Конвертируем в байты
        self.max_entries = max_entries
        self.entries: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._disk_cache_dir = "cache"
        self._logger = logging.getLogger(__name__)
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        # Создаем директорию для дискового кэша
        os.makedirs(self._disk_cache_dir, exist_ok=True)
        
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        with self._lock:
            entry = self.entries.get(key)
            if entry:
                current_time = time.time()
                
                # Проверяем срок действия
                if entry.expiry and current_time > entry.expiry:
                    self._logger.debug(f"Cache entry expired: {key}")
                    del self.entries[key]
                    return None
                    
                # Обновляем статистику доступа
                entry.last_access = current_time
                entry.access_count += 1
                return entry.value
                
        # Пробуем получить из дискового кэша
        return self._get_from_disk(key)
        
    def set(self, key: str, value: Any, ttl: Optional[float] = None,
            persist: bool = False) -> bool:
        """Сохранить значение в кэш"""
        try:
            # Оцениваем размер значения
            size = self._estimate_size(value)
            
            with self._lock:
                # Проверяем, хватает ли места
                if size > self.max_size:
                    self._logger.warning(f"Value too large for cache: {size} bytes")
                    return False
                    
                # Освобождаем место если нужно
                self._ensure_capacity(size)
                
                # Создаем запись
                entry = CacheEntry(
                    key=key,
                    value=value,
                    expiry=time.time() + ttl if ttl else None,
                    size=size,
                    last_access=time.time(),
                    access_count=0
                )
                
                self.entries[key] = entry
                
                # Асинхронно сохраняем на диск если нужно
                if persist:
                    self._executor.submit(self._save_to_disk, key, entry)
                    
                return True
        except Exception as e:
            self._logger.error(f"Error setting cache entry: {e}")
            return False
            
    def _ensure_capacity(self, required_size: int):
        """Освобождаем место в кэше"""
        current_size = sum(entry.size for entry in self.entries.values())
        
        while (len(self.entries) >= self.max_entries or 
               current_size + required_size > self.max_size):
            if not self.entries:
                raise ValueError("Cannot free enough cache space")
                
            # Удаляем наименее используемые записи
            entry_to_remove = min(
                self.entries.items(),
                key=lambda x: (x[1].access_count, -x[1].last_access)
            )
            
            del self.entries[entry_to_remove[0]]
            current_size -= entry_to_remove[1].size
            
    def _estimate_size(self, value: Any) -> int:
        """Оценить размер значения в байтах"""
        try:
            return len(pickle.dumps(value))
        except Exception:
            return len(str(value).encode())
            
    def _get_from_disk(self, key: str) -> Optional[Any]:
        """Получить значение из дискового кэша"""
        try:
            cache_file = os.path.join(self._disk_cache_dir, f"{key}.cache")
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                    if entry.expiry and time.time() > entry.expiry:
                        os.remove(cache_file)
                        return None
                    return entry.value
        except Exception as e:
            self._logger.error(f"Error reading from disk cache: {e}")
        return None
        
    def _save_to_disk(self, key: str, entry: CacheEntry):
        """Сохранить значение в дисковый кэш"""
        try:
            cache_file = os.path.join(self._disk_cache_dir, f"{key}.cache")
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            self._logger.error(f"Error writing to disk cache: {e}")
            
    def clear(self, older_than: Optional[float] = None):
        """Очистить кэш"""
        with self._lock:
            if older_than is None:
                self.entries.clear()
            else:
                current_time = time.time()
                self.entries = {
                    k: v for k, v in self.entries.items()
                    if v.last_access > current_time - older_than
                }
                
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        with self._lock:
            total_size = sum(entry.size for entry in self.entries.values())
            total_hits = sum(entry.access_count for entry in self.entries.values())
            
            return {
                'entries_count': len(self.entries),
                'total_size': total_size,
                'size_limit': self.max_size,
                'utilization': total_size / self.max_size * 100 if self.max_size > 0 else 0,
                'total_hits': total_hits,
                'disk_cache_size': self._get_disk_cache_size()
            }
            
    def _get_disk_cache_size(self) -> int:
        """Получить размер дискового кэша"""
        total_size = 0
        for file in os.listdir(self._disk_cache_dir):
            if file.endswith('.cache'):
                total_size += os.path.getsize(os.path.join(self._disk_cache_dir, file))
        return total_size

class SearchCache(CacheManager):
    """Специализированный кэш для результатов поиска"""
    
    def __init__(self):
        super().__init__(max_size_mb=50, max_entries=500)
        
    def cache_search_results(self, query: str, results: List[Any],
                           context: Dict[str, Any] = None):
        """Кэшировать результаты поиска"""
        cache_key = self._make_cache_key(query, context)
        self.set(cache_key, results, ttl=3600)  # Кэшируем на 1 час
        
    def get_search_results(self, query: str,
                          context: Dict[str, Any] = None) -> Optional[List[Any]]:
        """Получить кэшированные результаты поиска"""
        cache_key = self._make_cache_key(query, context)
        return self.get(cache_key)
        
    def _make_cache_key(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Создать ключ кэша для поискового запроса"""
        if context:
            # Сортируем ключи контекста для консистентности
            context_str = json.dumps(context, sort_keys=True)
            return f"search:{query}:{context_str}"
        return f"search:{query}"

# Глобальные экземпляры кэшей
cache_manager = CacheManager()
search_cache = SearchCache()
