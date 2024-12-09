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
        self._logger.info(
            "Cache manager initialized",
            extra={
                "max_size_mb": max_size_mb,
                "max_entries": max_entries,
                "cache_dir": self._disk_cache_dir
            }
        )
        
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        with self._lock:
            entry = self.entries.get(key)
            if entry:
                current_time = time.time()
                
                # Проверяем срок действия
                if entry.expiry and current_time > entry.expiry:
                    self._logger.debug(
                        f"Cache entry expired: {key}",
                        extra={
                            "key": key,
                            "expiry_time": entry.expiry,
                            "current_time": current_time,
                            "ttl_remaining": entry.expiry - current_time
                        }
                    )
                    del self.entries[key]
                    return None
                    
                # Обновляем статистику доступа
                entry.last_access = current_time
                entry.access_count += 1
                self._logger.debug(
                    f"Cache hit: {key}",
                    extra={
                        "key": key,
                        "access_count": entry.access_count,
                        "size": entry.size,
                        "age": current_time - entry.last_access
                    }
                )
                return entry.value
                
            # Пробуем получить из дискового кэша
            self._logger.debug(
                f"Cache miss (memory): {key}, trying disk cache",
                extra={"key": key}
            )
            disk_value = self._get_from_disk(key)
            if disk_value is not None:
                self._logger.debug(
                    f"Disk cache hit: {key}",
                    extra={"key": key}
                )
                # Помещаем значение в память
                self.set(key, disk_value)
            else:
                self._logger.debug(
                    f"Complete cache miss: {key}",
                    extra={"key": key}
                )
            return disk_value
        
    def set(self, key: str, value: Any, ttl: Optional[float] = None,
            persist: bool = False) -> bool:
        """Сохранить значение в кэш"""
        try:
            # Оцениваем размер значения
            size = self._estimate_size(value)
            
            with self._lock:
                # Проверяем, хватает ли места
                if size > self.max_size:
                    self._logger.warning(
                        f"Value too large for cache: {key}",
                        extra={
                            "key": key,
                            "value_size": size,
                            "max_size": self.max_size,
                            "current_usage": sum(e.size for e in self.entries.values())
                        }
                    )
                    return False
                    
                # Освобождаем место если нужно
                self._ensure_capacity(size)
                
                # Создаем запись
                expiry = time.time() + ttl if ttl else None
                entry = CacheEntry(
                    key=key,
                    value=value,
                    expiry=expiry,
                    size=size,
                    last_access=time.time(),
                    access_count=0
                )
                
                self.entries[key] = entry
                self._logger.info(
                    f"Cache entry set: {key}",
                    extra={
                        "key": key,
                        "size": size,
                        "ttl": ttl,
                        "persist": persist,
                        "expiry": expiry,
                        "total_entries": len(self.entries),
                        "total_size": sum(e.size for e in self.entries.values())
                    }
                )
                
                # Асинхронно сохраняем на диск если нужно
                if persist:
                    self._executor.submit(self._save_to_disk, key, entry)
                    
                return True
        except Exception as e:
            self._logger.error(
                f"Error setting cache entry: {key}",
                exc_info=True,
                extra={
                    "key": key,
                    "error_type": type(e).__name__,
                    "error_msg": str(e)
                }
            )
            return False
            
    def _ensure_capacity(self, required_size: int):
        """Освобождаем место в кэше"""
        current_size = sum(entry.size for entry in self.entries.values())
        removed_entries = []
        
        while (len(self.entries) >= self.max_entries or 
               current_size + required_size > self.max_size):
            if not self.entries:
                self._logger.error(
                    "Cannot free enough cache space",
                    extra={
                        "required_size": required_size,
                        "current_size": current_size,
                        "max_size": self.max_size
                    }
                )
                raise ValueError("Cannot free enough cache space")
                
            # Удаляем наименее используемые записи
            entry_to_remove = min(
                self.entries.items(),
                key=lambda x: (x[1].access_count, -x[1].last_access)
            )
            
            removed_entries.append({
                "key": entry_to_remove[0],
                "size": entry_to_remove[1].size,
                "access_count": entry_to_remove[1].access_count,
                "last_access": entry_to_remove[1].last_access
            })
            
            del self.entries[entry_to_remove[0]]
            current_size -= entry_to_remove[1].size
            
        if removed_entries:
            self._logger.info(
                "Removed cache entries to ensure capacity",
                extra={
                    "removed_count": len(removed_entries),
                    "freed_space": sum(e["size"] for e in removed_entries),
                    "removed_entries": removed_entries,
                    "current_size": current_size,
                    "required_size": required_size
                }
            )
            
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
            if not os.path.exists(cache_file):
                return None
                
            start_time = time.time()
            with open(cache_file, 'rb') as f:
                try:
                    entry = pickle.load(f)
                    if not isinstance(entry, CacheEntry):
                        self._logger.error(
                            f"Invalid cache entry format: {key}",
                            extra={"key": key, "type": type(entry)}
                        )
                        os.remove(cache_file)
                        return None
                        
                    load_time = time.time() - start_time
                    
                    # Check expiry
                    if entry.expiry and time.time() > entry.expiry:
                        self._logger.debug(
                            f"Disk cache entry expired: {key}",
                            extra={
                                "key": key,
                                "expiry_time": entry.expiry,
                                "file_size": os.path.getsize(cache_file)
                            }
                        )
                        os.remove(cache_file)
                        return None
                        
                    self._logger.debug(
                        f"Loaded from disk cache: {key}",
                        extra={
                            "key": key,
                            "load_time": load_time,
                            "file_size": os.path.getsize(cache_file),
                            "entry_size": entry.size
                        }
                    )
                    return entry.value
                except (pickle.UnpicklingError, AttributeError, EOFError) as e:
                    self._logger.error(
                        f"Error unpickling cache entry: {key}",
                        exc_info=True,
                        extra={"key": key, "error": str(e)}
                    )
                    os.remove(cache_file)
                    return None
                    
        except OSError as e:
            self._logger.error(
                f"Error reading from disk cache: {key}",
                exc_info=True,
                extra={
                    "key": key,
                    "error_type": type(e).__name__,
                    "error_msg": str(e)
                }
            )
            try:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
            except OSError:
                pass
        return None
        
    def _save_to_disk(self, key: str, entry: CacheEntry):
        """Сохранить значение в дисковый кэш"""
        try:
            start_time = time.time()
            cache_file = os.path.join(self._disk_cache_dir, f"{key}.cache")
            temp_file = cache_file + '.tmp'
            
            with open(temp_file, 'wb') as f:
                pickle.dump(entry, f)
            os.replace(temp_file, cache_file)
            
            save_time = time.time() - start_time
            self._logger.debug(
                f"Saved to disk cache: {key}",
                extra={
                    "key": key,
                    "save_time": save_time,
                    "file_size": os.path.getsize(cache_file),
                    "entry_size": entry.size
                }
            )
        except (OSError, pickle.PicklingError) as e:
            self._logger.error(
                f"Error writing to disk cache: {key}",
                exc_info=True,
                extra={
                    "key": key,
                    "error_type": type(e).__name__,
                    "error_msg": str(e),
                    "entry_size": entry.size
                }
            )
            try:
                os.remove(temp_file)
            except OSError:
                pass
            
    def _get_disk_cache_size(self) -> int:
        """Получить размер дискового кэша"""
        try:
            total_size = 0
            if os.path.exists(self._disk_cache_dir):
                for file in os.listdir(self._disk_cache_dir):
                    if file.endswith('.cache'):
                        try:
                            file_path = os.path.join(self._disk_cache_dir, file)
                            total_size += os.path.getsize(file_path)
                        except OSError as e:
                            self._logger.error(
                                f"Error getting cache file size: {file}",
                                exc_info=True,
                                extra={"file": file, "error": str(e)}
                            )
            return total_size
        except Exception as e:
            self._logger.error(
                "Error calculating disk cache size",
                exc_info=True,
                extra={"error": str(e)}
            )
            return 0

    def clear(self, older_than: Optional[float] = None):
        """Очистить кэш"""
        with self._lock:
            initial_memory_entries = len(self.entries)
            initial_memory_size = sum(e.size for e in self.entries.values())
            
            if older_than is None:
                self.entries.clear()
                # Очищаем дисковый кэш
                disk_files_removed = 0
                disk_size_freed = 0
                
                if os.path.exists(self._disk_cache_dir):
                    for file in os.listdir(self._disk_cache_dir):
                        if file.endswith('.cache'):
                            try:
                                file_path = os.path.join(self._disk_cache_dir, file)
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                disk_files_removed += 1
                                disk_size_freed += file_size
                            except OSError as e:
                                self._logger.error(
                                    f"Error removing cache file: {file}",
                                    exc_info=True,
                                    extra={"file": file, "error": str(e)}
                                )
                
                self._logger.info(
                    "Cache cleared completely",
                    extra={
                        "memory_entries_removed": initial_memory_entries,
                        "memory_size_freed": initial_memory_size,
                        "disk_files_removed": disk_files_removed,
                        "disk_size_freed": disk_size_freed
                    }
                )
            else:
                current_time = time.time()
                # Очищаем память
                old_entries = {
                    k: v for k, v in self.entries.items()
                    if v.last_access <= current_time - older_than
                }
                for k in old_entries:
                    del self.entries[k]
                
                # Очищаем диск
                disk_files_removed = 0
                disk_size_freed = 0
                
                if os.path.exists(self._disk_cache_dir):
                    for file in os.listdir(self._disk_cache_dir):
                        if file.endswith('.cache'):
                            try:
                                file_path = os.path.join(self._disk_cache_dir, file)
                                if os.path.getmtime(file_path) <= current_time - older_than:
                                    file_size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    disk_files_removed += 1
                                    disk_size_freed += file_size
                            except OSError as e:
                                self._logger.error(
                                    f"Error removing old cache file: {file}",
                                    exc_info=True,
                                    extra={"file": file, "error": str(e)}
                                )
                
                self._logger.info(
                    "Old cache entries cleared",
                    extra={
                        "older_than": older_than,
                        "memory_entries_removed": len(old_entries),
                        "memory_size_freed": sum(e.size for e in old_entries.values()),
                        "disk_files_removed": disk_files_removed,
                        "disk_size_freed": disk_size_freed
                    }
                )
                
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        with self._lock:
            try:
                entries = list(self.entries.values())
                total_size = sum(entry.size for entry in entries)
                total_hits = sum(entry.access_count for entry in entries)
                avg_access_count = total_hits / len(entries) if entries else 0
                
                disk_size = self._get_disk_cache_size()
                
                return {
                    'entries_count': len(self.entries),
                    'total_size': total_size,
                    'total_hits': total_hits,
                    'size_limit': self.max_size,
                    'utilization': (total_size / self.max_size * 100) 
                                 if self.max_size > 0 else 0,
                    'disk_cache_size': disk_size,
                    'avg_access_count': avg_access_count,
                    'memory_utilization': len(self.entries) / self.max_entries * 100
                                        if self.max_entries > 0 else 0
                }
            except Exception as e:
                self._logger.error(
                    "Error getting cache stats",
                    exc_info=True,
                    extra={"error": str(e)}
                )
                return {
                    'entries_count': 0,
                    'total_size': 0,
                    'total_hits': 0,
                    'size_limit': self.max_size,
                    'utilization': 0,
                    'disk_cache_size': 0,
                    'avg_access_count': 0,
                    'memory_utilization': 0
                }

    def clear_model_cache(self, model_name: str) -> None:
        """Clear cache entries for a specific model"""
        with self._lock:
            keys_to_remove = [
                key for key in list(self.entries.keys())
                if key.startswith(f"model_{model_name}_")
            ]
            for key in keys_to_remove:
                del self.entries[key]
            self._logger.info(f"Cleared cache for model: {model_name}")

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
