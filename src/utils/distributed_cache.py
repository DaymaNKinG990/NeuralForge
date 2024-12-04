from typing import Any, Dict, Optional, List, Set, Tuple
import socket
import threading
import pickle
import zlib
import time
import logging
import json
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path

@dataclass
class CacheNode:
    """Узел распределенного кэша"""
    host: str
    port: int
    capacity: int
    current_load: int
    last_seen: float

class DistributedCache:
    """Распределенный кэш с поддержкой шардинга"""
    
    def __init__(self, host: str = 'localhost', port: int = 5000,
                 capacity_mb: int = 100) -> None:
        self.host = host
        self.port = port
        self.capacity = capacity_mb * 1024 * 1024  # Convert to bytes
        
        self._nodes: Dict[str, CacheNode] = {}
        self._local_cache: Dict[str, bytes] = {}
        self._node_lock = threading.Lock()
        self._cache_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._logger = logging.getLogger(__name__)
        
        # Создаем локальное хранилище
        cache_dir = Path.home() / '.neuralforge' / 'cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir = cache_dir
        
        # Запускаем сервер
        self._start_server()
        
    def _start_server(self) -> None:
        """Запуск сервера кэша"""
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.bind((self.host, self.port))
        self._server.listen(5)
        
        def accept_connections():
            while True:
                try:
                    client, addr = self._server.accept()
                    self._executor.submit(self._handle_client, client)
                except Exception as e:
                    self._logger.error(f"Connection error: {e}")
                    
        threading.Thread(target=accept_connections, daemon=True).start()
        
    def _handle_client(self, client: socket.socket) -> None:
        """Обработка клиентских запросов"""
        try:
            while True:
                data = client.recv(4096)
                if not data:
                    break
                    
                request = pickle.loads(data)
                command = request.get('command')
                
                if command == 'get':
                    key = request['key']
                    value = self.get(key)
                    client.send(pickle.dumps({'value': value}))
                    
                elif command == 'set':
                    key = request['key']
                    value = request['value']
                    ttl = request.get('ttl')
                    self.set(key, value, ttl)
                    client.send(pickle.dumps({'status': 'ok'}))
                    
                elif command == 'join':
                    node = CacheNode(
                        host=request['host'],
                        port=request['port'],
                        capacity=request['capacity'],
                        current_load=request['load'],
                        last_seen=time.time()
                    )
                    self._add_node(node)
                    client.send(pickle.dumps({'status': 'ok'}))
                    
        except Exception as e:
            self._logger.error(f"Client handler error: {e}")
        finally:
            client.close()
            
    def _add_node(self, node: CacheNode) -> None:
        """Добавление нового узла"""
        with self._node_lock:
            node_id = f"{node.host}:{node.port}"
            self._nodes[node_id] = node
            self._rebalance_cache()
            
    def _get_shard(self, key: str) -> CacheNode:
        """Определение узла для ключа"""
        if not self._nodes:
            return None
            
        # Используем консистентное хэширование
        hash_val = int(hashlib.md5(key.encode()).hexdigest(), 16)
        nodes = sorted(self._nodes.values(), key=lambda x: x.current_load)
        return nodes[hash_val % len(nodes)]
        
    def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        # Проверяем локальный кэш
        with self._cache_lock:
            if key in self._local_cache:
                return pickle.loads(zlib.decompress(self._local_cache[key]))
                
        # Проверяем файловый кэш
        file_path = self._cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"
        if file_path.exists():
            try:
                with open(file_path, 'rb') as f:
                    return pickle.loads(zlib.decompress(f.read()))
            except Exception as e:
                self._logger.error(f"Error reading cache file: {e}")
                
        # Ищем в распределенном кэше
        shard = self._get_shard(key)
        if shard:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((shard.host, shard.port))
                    request = {'command': 'get', 'key': key}
                    s.send(pickle.dumps(request))
                    response = pickle.loads(s.recv(4096))
                    return response.get('value')
            except Exception as e:
                self._logger.error(f"Error getting from shard: {e}")
                
        return None
        
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Сохранение значения в кэш"""
        compressed = zlib.compress(pickle.dumps(value))
        
        # Проверяем размер
        if len(compressed) > self.capacity:
            raise ValueError("Value too large for cache")
            
        # Сохраняем локально если есть место
        total_size = sum(len(v) for v in self._local_cache.values())
        if total_size + len(compressed) <= self.capacity:
            with self._cache_lock:
                self._local_cache[key] = compressed
                
        # Сохраняем в файл
        file_path = self._cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.cache"
        try:
            with file_path.open('wb') as f:
                f.write(compressed)
        except Exception as e:
            self._logger.error(f"Error writing cache file: {e}")
            
        # Отправляем в распределенный кэш
        shard = self._get_shard(key)
        if shard:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((shard.host, shard.port))
                    request = {
                        'command': 'set',
                        'key': key,
                        'value': value,
                        'ttl': ttl
                    }
                    s.send(pickle.dumps(request))
            except Exception as e:
                self._logger.error(f"Error setting to shard: {e}")
                
    def _rebalance_cache(self) -> None:
        """Перебалансировка кэша между узлами"""
        with self._cache_lock:
            if not self._nodes:
                return
                
            # Вычисляем целевую нагрузку
            total_capacity = sum(node.capacity for node in self._nodes.values())
            target_load = total_capacity / len(self._nodes)
            
            # Перемещаем данные между узлами
            for key, value in list(self._local_cache.items()):
                shard = self._get_shard(key)
                if shard and shard.current_load < target_load:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.connect((shard.host, shard.port))
                            request = {
                                'command': 'set',
                                'key': key,
                                'value': pickle.loads(zlib.decompress(value))
                            }
                            s.send(pickle.dumps(request))
                            del self._local_cache[key]
                    except Exception as e:
                        self._logger.error(f"Error rebalancing cache: {e}")
                        
    def clear(self) -> None:
        """Очистка кэша"""
        with self._cache_lock:
            self._local_cache.clear()
            
        # Очищаем файловый кэш
        for file in self._cache_dir.iterdir():
            try:
                file.unlink()
            except Exception as e:
                self._logger.error(f"Error clearing cache file: {e}")
                
        # Очищаем распределенный кэш
        for node in self._nodes.values():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((node.host, node.port))
                    request = {'command': 'clear'}
                    s.send(pickle.dumps(request))
            except Exception as e:
                self._logger.error(f"Error clearing shard: {e}")
                
    def join_network(self, seed_host: str, seed_port: int) -> None:
        """Присоединение к сети кэширования"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((seed_host, seed_port))
                request = {
                    'command': 'join',
                    'host': self.host,
                    'port': self.port,
                    'capacity': self.capacity,
                    'load': len(self._local_cache)
                }
                s.send(pickle.dumps(request))
        except Exception as e:
            self._logger.error(f"Error joining cache network: {e}")
            
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        local_size = sum(len(v) for v in self._local_cache.values())
        file_size = sum(f.stat().st_size for f in self._cache_dir.iterdir())
        
        return {
            'local_entries': len(self._local_cache),
            'local_size': local_size,
            'file_size': file_size,
            'nodes': len(self._nodes),
            'capacity': self.capacity,
            'utilization': (local_size + file_size) / self.capacity * 100
        }

# Глобальный экземпляр
distributed_cache = DistributedCache()
