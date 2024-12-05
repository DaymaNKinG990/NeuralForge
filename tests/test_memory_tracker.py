import pytest
import time
from src.utils.performance import MemoryTracker, MemoryUsage

@pytest.fixture
def tracker():
    """Create a memory tracker instance"""
    return MemoryTracker()

def test_memory_usage_creation():
    """Test MemoryUsage dataclass creation"""
    usage = MemoryUsage(
        component="test_component",
        size=1024,
        timestamp=time.time()
    )
    assert usage.component == "test_component"
    assert usage.size == 1024
    assert isinstance(usage.timestamp, float)

def test_track_memory_usage(tracker):
    """Test tracking memory usage of components"""
    # Track usage for a component
    tracker.track("component1", 1024)
    
    # Verify component size is updated
    assert tracker.component_sizes["component1"] == 1024
    
    # Verify usage history is updated
    assert len(tracker.usage_history) == 1
    assert tracker.usage_history[0].component == "component1"
    assert tracker.usage_history[0].size == 1024

def test_multiple_components(tracker):
    """Test tracking multiple components"""
    components = {
        "component1": 1024,
        "component2": 2048,
        "component3": 4096
    }
    
    # Track usage for multiple components
    for component, size in components.items():
        tracker.track(component, size)
    
    # Verify all components are tracked
    assert len(tracker.component_sizes) == len(components)
    for component, size in components.items():
        assert tracker.component_sizes[component] == size

def test_update_existing_component(tracker):
    """Test updating existing component size"""
    # Initial tracking
    tracker.track("component1", 1024)
    assert tracker.component_sizes["component1"] == 1024
    
    # Update size
    tracker.track("component1", 2048)
    assert tracker.component_sizes["component1"] == 2048
    
    # Verify history has two entries
    assert len(tracker.usage_history) == 2
    assert tracker.usage_history[-1].size == 2048

def test_get_total_usage(tracker):
    """Test getting total memory usage"""
    # Track multiple components
    components = {
        "component1": 1024,
        "component2": 2048,
        "component3": 4096
    }
    
    for component, size in components.items():
        tracker.track(component, size)
    
    # Verify total usage
    total = tracker.get_total_usage()
    assert total == sum(components.values())

def test_get_component_usage(tracker):
    """Test getting specific component usage"""
    # Track component
    tracker.track("component1", 1024)
    time.sleep(0.1)  # Ensure different timestamps
    tracker.track("component1", 2048)
    
    # Get usage history
    usage = tracker.get_component_usage("component1")
    assert len(usage) == 2
    assert usage[0].size == 1024
    assert usage[1].size == 2048
    assert usage[0].timestamp < usage[1].timestamp

def test_clear_history(tracker):
    """Test clearing usage history"""
    # Add some usage data
    tracker.track("component1", 1024)
    time.sleep(0.1)
    tracker.track("component2", 2048)
    
    # Clear all history
    tracker.clear_history()
    assert len(tracker.usage_history) == 0
    
    # Component sizes should remain
    assert len(tracker.component_sizes) == 2

def test_clear_history_before_timestamp(tracker):
    """Test clearing history before specific timestamp"""
    # Add usage data at different times
    tracker.track("component1", 1024)
    time.sleep(0.1)
    mid_time = time.time()
    time.sleep(0.1)
    tracker.track("component2", 2048)
    
    # Clear history before mid_time
    tracker.clear_history(before=mid_time)
    
    # Verify only newer entries remain
    assert len(tracker.usage_history) == 1
    assert tracker.usage_history[0].component == "component2"

def test_memory_growth_tracking(tracker):
    """Test tracking memory growth over time"""
    # Simulate growing memory usage
    sizes = [1024, 2048, 4096, 8192]
    for size in sizes:
        tracker.track("growing_component", size)
        time.sleep(0.1)
    
    # Get usage history
    usage = tracker.get_component_usage("growing_component")
    
    # Verify growth pattern
    assert len(usage) == len(sizes)
    for i, size in enumerate(sizes):
        assert usage[i].size == size
        if i > 0:
            assert usage[i].timestamp > usage[i-1].timestamp

def test_multiple_component_history(tracker):
    """Test history tracking for multiple components"""
    components = ["comp1", "comp2", "comp3"]
    
    # Track each component multiple times
    for i in range(3):
        for comp in components:
            tracker.track(comp, (i + 1) * 1024)
            time.sleep(0.1)
    
    # Verify history for each component
    for comp in components:
        usage = tracker.get_component_usage(comp)
        assert len(usage) == 3
        for i, entry in enumerate(usage):
            assert entry.size == (i + 1) * 1024

def test_zero_size_tracking(tracker):
    """Test tracking zero memory usage"""
    # Track zero size
    tracker.track("zero_component", 0)
    
    # Verify tracking
    assert tracker.component_sizes["zero_component"] == 0
    assert len(tracker.usage_history) == 1
    assert tracker.usage_history[0].size == 0

def test_negative_size_handling(tracker):
    """Test handling of negative sizes"""
    # Track negative size (should be treated as 0)
    tracker.track("negative_component", -1024)
    
    # Verify size is stored as 0
    assert tracker.component_sizes["negative_component"] == 0
    assert tracker.usage_history[0].size == 0
