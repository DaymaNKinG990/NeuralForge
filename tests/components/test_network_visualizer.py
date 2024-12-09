"""Tests for Network Visualizer components."""
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter
from src.ui.network_visualizer.visualizer import NetworkVisualizer
from src.ui.network_visualizer.graph import NetworkGraph
from src.ui.network_visualizer.node import NetworkNode
from src.ui.network_visualizer.edge import NetworkEdge

@pytest.fixture
def network_visualizer(qtbot):
    """Create network visualizer fixture."""
    visualizer = NetworkVisualizer()
    qtbot.addWidget(visualizer)
    return visualizer

@pytest.fixture
def network_graph():
    """Create network graph fixture."""
    return NetworkGraph()

@pytest.fixture
def sample_network(network_graph):
    """Create sample network with nodes and edges."""
    # Create input layer
    input_node = NetworkNode("Input", node_type="input")
    network_graph.add_node(input_node)
    
    # Create hidden layer
    hidden_nodes = [
        NetworkNode(f"Hidden_{i}", node_type="hidden")
        for i in range(3)
    ]
    for node in hidden_nodes:
        network_graph.add_node(node)
        network_graph.add_edge(NetworkEdge(input_node, node))
    
    # Create output layer
    output_node = NetworkNode("Output", node_type="output")
    network_graph.add_node(output_node)
    for hidden_node in hidden_nodes:
        network_graph.add_edge(NetworkEdge(hidden_node, output_node))
    
    return network_graph

def test_visualizer_creation(network_visualizer):
    """Test network visualizer creation."""
    assert network_visualizer is not None
    assert network_visualizer.graph is not None
    assert network_visualizer.zoom_slider is not None
    assert network_visualizer.layout_combo is not None

def test_graph_creation(network_graph):
    """Test network graph creation."""
    assert network_graph is not None
    assert len(network_graph.nodes) == 0
    assert len(network_graph.edges) == 0

def test_node_creation():
    """Test network node creation."""
    node = NetworkNode("test_node", node_type="hidden")
    assert node.name == "test_node"
    assert node.node_type == "hidden"
    assert isinstance(node.position, QPointF)

def test_edge_creation():
    """Test network edge creation."""
    source = NetworkNode("source")
    target = NetworkNode("target")
    edge = NetworkEdge(source, target)
    assert edge.source == source
    assert edge.target == target

def test_add_node(network_graph):
    """Test adding node to graph."""
    node = NetworkNode("test_node")
    network_graph.add_node(node)
    assert len(network_graph.nodes) == 1
    assert node in network_graph.nodes

def test_add_edge(network_graph):
    """Test adding edge to graph."""
    source = NetworkNode("source")
    target = NetworkNode("target")
    network_graph.add_node(source)
    network_graph.add_node(target)
    
    edge = NetworkEdge(source, target)
    network_graph.add_edge(edge)
    assert len(network_graph.edges) == 1
    assert edge in network_graph.edges

def test_sample_network(sample_network):
    """Test sample network structure."""
    # Count nodes by type
    node_types = {"input": 0, "hidden": 0, "output": 0}
    for node in sample_network.nodes:
        node_types[node.node_type] += 1
    
    assert node_types["input"] == 1
    assert node_types["hidden"] == 3
    assert node_types["output"] == 1
    
    # Check edges
    assert len(sample_network.edges) == 6  # 1->3 + 3->1 = 6 edges

def test_node_selection(network_visualizer, qtbot):
    """Test node selection in visualizer."""
    # Add a node
    node = NetworkNode("test_node")
    network_visualizer.graph.add_node(node)
    
    # Simulate node click
    with qtbot.waitSignal(network_visualizer.node_selected):
        network_visualizer.select_node(node)
    
    assert network_visualizer.selected_node == node

def test_zoom_control(network_visualizer):
    """Test zoom control functionality."""
    initial_scale = network_visualizer.scale_factor
    
    # Zoom in
    network_visualizer.zoom_slider.setValue(
        network_visualizer.zoom_slider.value() + 10
    )
    assert network_visualizer.scale_factor > initial_scale
    
    # Zoom out
    network_visualizer.zoom_slider.setValue(
        network_visualizer.zoom_slider.value() - 20
    )
    assert network_visualizer.scale_factor < initial_scale

def test_layout_change(network_visualizer, sample_network):
    """Test layout algorithm change."""
    # Set graph
    network_visualizer.set_graph(sample_network)
    
    # Store initial positions
    initial_positions = {
        node: node.position
        for node in sample_network.nodes
    }
    
    # Change layout
    network_visualizer.layout_combo.setCurrentText("Force Directed")
    network_visualizer.apply_layout()
    
    # Check if positions changed
    positions_changed = False
    for node in sample_network.nodes:
        if node.position != initial_positions[node]:
            positions_changed = True
            break
    
    assert positions_changed

def test_node_movement(network_visualizer, qtbot):
    """Test node movement."""
    node = NetworkNode("test_node")
    network_visualizer.graph.add_node(node)
    
    initial_pos = node.position
    new_pos = initial_pos + QPointF(100, 100)
    
    # Simulate node drag
    network_visualizer.begin_node_drag(node)
    network_visualizer.update_node_position(new_pos)
    network_visualizer.end_node_drag()
    
    assert node.position == new_pos

def test_graph_export(network_visualizer, sample_network, tmp_path):
    """Test graph export functionality."""
    network_visualizer.set_graph(sample_network)
    
    # Export to file
    export_path = tmp_path / "network.png"
    network_visualizer.export_to_image(str(export_path))
    assert export_path.exists()

def test_graph_import(network_visualizer, tmp_path):
    """Test graph import functionality."""
    # Create test graph file
    graph_file = tmp_path / "test_graph.json"
    graph_data = {
        "nodes": [
            {"name": "input", "type": "input"},
            {"name": "hidden", "type": "hidden"},
            {"name": "output", "type": "output"}
        ],
        "edges": [
            {"source": "input", "target": "hidden"},
            {"source": "hidden", "target": "output"}
        ]
    }
    graph_file.write_text(str(graph_data))
    
    # Import graph
    network_visualizer.import_from_file(str(graph_file))
    assert len(network_visualizer.graph.nodes) == 3
    assert len(network_visualizer.graph.edges) == 2
