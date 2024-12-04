import cProfile
import pstats
import io
import time
import functools
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import tracemalloc

@dataclass
class ProfileResult:
    """Результаты профилирования"""
    function_name: str
    total_time: float
    calls: int
    time_per_call: float
    memory_start: int
    memory_peak: int
    timestamp: datetime

class Profiler:
    """Профилировщик для отслеживания производительности функций"""
    
    def __init__(self):
        self.results: Dict[str, List[ProfileResult]] = {}
        self.enabled = True
        self.memory_tracking = False
        self._logger = logging.getLogger(__name__)

    def start_memory_tracking(self):
        """Включить отслеживание памяти"""
        if not self.memory_tracking:
            tracemalloc.start()
            self.memory_tracking = True

    def stop_memory_tracking(self):
        """Выключить отслеживание памяти"""
        if self.memory_tracking:
            tracemalloc.stop()
            self.memory_tracking = False

    def profile(self, threshold_ms: float = 100):
        """Декоратор для профилирования функций"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not self.enabled:
                    return func(*args, **kwargs)

                # Подготовка профилировщика
                pr = cProfile.Profile()
                memory_start = 0
                if self.memory_tracking:
                    memory_start = tracemalloc.get_traced_memory()[0]

                # Запуск профилирования
                start_time = time.time()
                try:
                    result = pr.runcall(func, *args, **kwargs)
                except Exception as e:
                    self._logger.error(f"Error in profiled function {func.__name__}: {e}")
                    raise
                finally:
                    end_time = time.time()
                    
                    # Анализ результатов
                    s = io.StringIO()
                    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
                    ps.print_stats()
                    
                    total_time = end_time - start_time
                    if total_time * 1000 >= threshold_ms:
                        memory_peak = 0
                        if self.memory_tracking:
                            _, memory_peak = tracemalloc.get_traced_memory()

                        profile_result = ProfileResult(
                            function_name=func.__name__,
                            total_time=total_time,
                            calls=ps.total_calls,
                            time_per_call=total_time / ps.total_calls if ps.total_calls > 0 else 0,
                            memory_start=memory_start,
                            memory_peak=memory_peak,
                            timestamp=datetime.now()
                        )

                        if func.__name__ not in self.results:
                            self.results[func.__name__] = []
                        self.results[func.__name__].append(profile_result)

                        # Логирование медленных операций
                        if total_time * 1000 >= threshold_ms:
                            self._logger.warning(
                                f"Slow operation detected: {func.__name__} "
                                f"took {total_time*1000:.2f}ms"
                            )

                return result
            return wrapper
        return decorator

    def get_results(self, function_name: Optional[str] = None) -> List[ProfileResult]:
        """Получить результаты профилирования"""
        if function_name:
            return self.results.get(function_name, [])
        return [r for results in self.results.values() for r in results]

    def clear_results(self):
        """Очистить результаты профилирования"""
        self.results.clear()

    def get_slow_operations(self, threshold_ms: float = 100) -> List[ProfileResult]:
        """Получить список медленных операций"""
        slow_ops = []
        for results in self.results.values():
            for result in results:
                if result.total_time * 1000 >= threshold_ms:
                    slow_ops.append(result)
        return sorted(slow_ops, key=lambda x: x.total_time, reverse=True)

    def get_memory_intensive_operations(self, threshold_mb: float = 10) -> List[ProfileResult]:
        """Получить список операций с высоким потреблением памяти"""
        memory_ops = []
        for results in self.results.values():
            for result in results:
                memory_used_mb = (result.memory_peak - result.memory_start) / (1024 * 1024)
                if memory_used_mb >= threshold_mb:
                    memory_ops.append(result)
        return sorted(memory_ops, key=lambda x: x.memory_peak - x.memory_start, reverse=True)

# Глобальный экземпляр профилировщика
profiler = Profiler()
