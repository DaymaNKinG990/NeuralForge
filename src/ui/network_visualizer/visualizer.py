"""Network visualization module."""
from typing import Optional, Dict, List, Tuple
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import logging

logger = logging.getLogger(__name__)

class NetworkVisualizer(QWidget):
    """Network visualization widget."""
    
    # Signals
    graph_updated = pyqtSignal()
    node_selected = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize network visualizer.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.graph = nx.Graph()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the visualizer UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create matplotlib figure
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)
        
    def set_graph(self, nodes: List[str], edges: List[Tuple[str, str]]):
        """Set graph data.
        
        Args:
            nodes: List of node names
            edges: List of (source, target) edges
        """
        try:
            self.graph.clear()
            self.graph.add_nodes_from(nodes)
            self.graph.add_edges_from(edges)
            self.draw_graph()
            self.graph_updated.emit()
        except Exception as e:
            logger.error(f"Error setting graph: {e}")
            self.error_occurred.emit(str(e))
            
    def draw_graph(self):
        """Draw the network graph."""
        try:
            self.ax.clear()
            pos = nx.spring_layout(self.graph)
            nx.draw(
                self.graph, pos,
                ax=self.ax,
                with_labels=True,
                node_color='lightblue',
                node_size=500,
                font_size=8
            )
            self.canvas.draw()
        except Exception as e:
            logger.error(f"Error drawing graph: {e}")
            self.error_occurred.emit(str(e))
            
    def clear(self):
        """Clear the visualization."""
        self.graph.clear()
        self.draw_graph()
