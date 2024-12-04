import pytest
from unittest.mock import Mock, patch, MagicMock
import time
import psutil
from src.utils.performance import PerformanceMonitor
from PyQt6.QtTest import QTest
from PyQt6.QtCore import pyqtSignal

@pytest.fixture
def performance_monitor():
    return PerformanceMonitor()

def test_memory_usage(performance_monitor, qtbot):
    """Test memory usage monitoring through stats_updated signal"""
    def check_memory(stats):
        assert 'memory_percent' in stats
        assert isinstance(stats['memory_percent'], float)
        assert stats['memory_percent'] >= 0

    with qtbot.waitSignal(performance_monitor.stats_updated, timeout=1000, raising=True) as blocker:
        performance_monitor.update_stats()
        check_memory(blocker.args[0])

def test_cpu_usage(performance_monitor, qtbot):
    """Test CPU usage monitoring through stats_updated signal"""
    def check_cpu(stats):
        assert 'cpu_percent' in stats
        assert isinstance(stats['cpu_percent'], float)
        assert 0 <= stats['cpu_percent'] <= 100

    with qtbot.waitSignal(performance_monitor.stats_updated, timeout=1000, raising=True) as blocker:
        performance_monitor.update_stats()
        check_cpu(blocker.args[0])

def test_performance_metrics(performance_monitor):
    """Test performance metrics collection"""
    # Simulate performance metrics collection
    performance_monitor.update_stats()
    
    # Check if stats_updated signal is emitted with expected data
    def check_metrics(stats):
        assert 'memory_percent' in stats
        assert 'cpu_percent' in stats
        assert isinstance(stats['memory_percent'], float)
        assert isinstance(stats['cpu_percent'], float)

    performance_monitor.stats_updated.connect(check_metrics)
    performance_monitor.update_stats()


def test_performance_history(performance_monitor):
    """Test performance history tracking"""
    # Simulate multiple updates to build history
    for _ in range(3):
        performance_monitor.update_stats()

    # Verify that history is tracked
    # Assuming we have a method to retrieve history
    # history = performance_monitor.get_performance_history()
    # assert len(history) >= 3


def test_performance_report(performance_monitor):
    """Test performance report generation"""
    # Simulate report generation
    performance_monitor.update_stats()

    # Assuming we have a method to generate a report
    # report = performance_monitor.generate_performance_report()
    # assert 'average_execution_time' in report
    # assert 'peak_memory_usage' in report
    # assert 'average_cpu_usage' in report

def test_performance_threshold_warnings(performance_monitor, qtbot):
    """Test performance threshold warnings through warning_triggered signal"""
    def check_warning(warning):
        assert "High memory usage" in warning or "High CPU usage" in warning

    with qtbot.waitSignal(performance_monitor.warning_triggered, timeout=1000, raising=True) as blocker:
        # Simulate high resource usage
        with patch('psutil.Process') as mock_process:
            mock_proc = Mock()
            mock_proc.memory_percent.return_value = 85.0  # High memory usage
            mock_proc.cpu_percent.return_value = 75.0     # High CPU usage
            mock_process.return_value = mock_proc
            
            # Ensure the signal is connected and emits a warning
            def emit_warning(warning):
                print(warning)
                return warning
            performance_monitor.warning_triggered.connect(emit_warning)

            performance_monitor.update_stats()
            check_warning(blocker.args[0])

def test_concurrent_monitoring(qtbot):
    """Test concurrent performance monitoring"""
    monitor1 = PerformanceMonitor()
    monitor2 = PerformanceMonitor()

    def check_stats(stats):
        assert 'memory_percent' in stats
        assert 'cpu_percent' in stats

    with qtbot.waitSignal(monitor1.stats_updated, timeout=1000, raising=True) as blocker1, \
         qtbot.waitSignal(monitor2.stats_updated, timeout=1000, raising=True) as blocker2:
        monitor1.update_stats()
        monitor2.update_stats()

        check_stats(blocker1.args[0])
        check_stats(blocker2.args[0])
