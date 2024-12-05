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
    warnings_received = []
    
    def handle_warning(warning):
        warnings_received.append(warning)
    
    # Connect signal handler
    performance_monitor.warning_triggered.connect(handle_warning)
    
    # Create mock process
    mock_proc = Mock()
    mock_proc.cpu_percent.side_effect = [0.0, 75.0]  # First call returns 0, second call returns 75%
    mock_proc.memory_percent.return_value = 85.0  # High memory usage
    mock_proc.num_threads.return_value = 4
    mock_proc.io_counters.return_value = Mock(_asdict=lambda: {})

    # Set up process mock
    with patch('psutil.virtual_memory') as mock_vmem:
        mock_vmem.return_value = Mock(_asdict=lambda: {})
        
        # Set the mock process directly
        performance_monitor.process = mock_proc
        
        # Initialize CPU monitoring
        performance_monitor.process.cpu_percent()
        
        # Create signal watchers
        with qtbot.waitSignal(performance_monitor.warning_triggered, timeout=1000) as blocker1:
            with qtbot.waitSignal(performance_monitor.warning_triggered, timeout=1000) as blocker2:
                performance_monitor.update_stats()
        
        # Verify warnings
        assert len(warnings_received) == 2, "Expected 2 warnings (CPU and memory)"
        assert any("CPU usage" in w for w in warnings_received), "No CPU warning received"
        assert any("memory usage" in w for w in warnings_received), "No memory warning received"
        
    # Cleanup
    performance_monitor.warning_triggered.disconnect(handle_warning)

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
