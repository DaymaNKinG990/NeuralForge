from typing import Dict, Optional, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QScrollArea, QFrame)
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PyQt6.QtCore import Qt, QRectF
import networkx as nx
import math
from .styles.style_manager import StyleManager
from .styles.style_enums import ColorScheme, StyleClass

class NetworkView(QWidget):
    """Network visualization view for neural network architectures."""
    
    def __init__(self) -> None:
        """Initialize the network view."""
        super().__init__()
        self.graph: Optional[nx.DiGraph] = None
        self.node_positions: Dict[str, tuple[float, float]] = {}
        self.node_colors: Dict[str, str] = {}
        self.scale_factor: float = 1.0
        self.offset_x: float = 0
        self.offset_y: float = 0
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Apply theme styles
        self.style_manager = StyleManager()
        self.setStyleSheet(f"""
            QWidget {{
                background: {ColorScheme.ML_BACKGROUND.value};
            }}
        """)

    def update_graph(self, graph: nx.DiGraph, positions: Dict[str, tuple[float, float]], colors: Dict[str, str]) -> None:
        """Update the graph data.
        
        Args:
            graph: Directed graph representing the network
            positions: Dictionary of node positions
            colors: Dictionary of node colors
        """
        self.graph = graph
        self.node_positions = positions
        self.node_colors = colors
        self.update()
        
    def paintEvent(self, event) -> None:
        """Handle the paint event to draw the network visualization.
        
        Args:
            event: Paint event
        """
        if not self.graph:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate scaling to fit the view
        margin = 50
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin
        
        # Find the bounds of the graph
        min_x = min(pos[0] for pos in self.node_positions.values())
        max_x = max(pos[0] for pos in self.node_positions.values())
        min_y = min(pos[1] for pos in self.node_positions.values())
        max_y = max(pos[1] for pos in self.node_positions.values())
        
        # Calculate scaling factors
        scale_x = width / (max_x - min_x) if max_x != min_x else 1
        scale_y = height / (max_y - min_y) if max_y != min_y else 1
        scale = min(scale_x, scale_y)
        
        # Draw edges
        pen = QPen(QColor("#4B4B4B"))
        pen.setWidth(2)
        painter.setPen(pen)
        
        for edge in self.graph.edges():
            start_pos = self.node_positions[edge[0]]
            end_pos = self.node_positions[edge[1]]
            
            # Transform coordinates
            x1 = margin + (start_pos[0] - min_x) * scale
            y1 = margin + (start_pos[1] - min_y) * scale
            x2 = margin + (end_pos[0] - min_x) * scale
            y2 = margin + (end_pos[1] - min_y) * scale
            
            # Draw arrow
            path = QPainterPath()
            path.moveTo(x1, y1)
            
            # Calculate control points for curved edges
            ctrl_x = (x1 + x2) / 2
            ctrl_y = (y1 + y2) / 2
            path.quadTo(ctrl_x, ctrl_y, x2, y2)
            
            painter.drawPath(path)
            
            # Draw arrowhead
            angle = math.atan2(y2 - y1, x2 - x1)
            arrow_size = 10
            arrow_angle = math.pi / 6  # 30 degrees
            
            # Calculate arrowhead points
            point1_x = x2 - arrow_size * math.cos(angle + arrow_angle)
            point1_y = y2 - arrow_size * math.sin(angle + arrow_angle)
            point2_x = x2 - arrow_size * math.cos(angle - arrow_angle)
            point2_y = y2 - arrow_size * math.sin(angle - arrow_angle)
            
            arrow_path = QPainterPath()
            arrow_path.moveTo(x2, y2)
            arrow_path.lineTo(point1_x, point1_y)
            arrow_path.lineTo(point2_x, point2_y)
            arrow_path.closeSubpath()
            
            painter.fillPath(arrow_path, QBrush(QColor("#4B4B4B")))
            
        # Draw nodes
        node_radius = 30
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        
        for node in self.graph.nodes():
            pos = self.node_positions[node]
            x = margin + (pos[0] - min_x) * scale
            y = margin + (pos[1] - min_y) * scale
            
            # Draw node circle
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(self.node_colors.get(node, "#D4D4D4"))))
            painter.drawEllipse(QRectF(x - node_radius, y - node_radius,
                                     2 * node_radius, 2 * node_radius))
                                     
            # Draw node border
            painter.setPen(QPen(QColor("#2D2D2D"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(x - node_radius, y - node_radius,
                                     2 * node_radius, 2 * node_radius))
                                     
            # Draw node label
            painter.setPen(QPen(QColor("#FFFFFF")))
            label = node.split('_')[0]  # Show only the layer type
            rect = painter.fontMetrics().boundingRect(label)
            painter.drawText(int(x - rect.width()/2),
                           int(y + rect.height()/2),
                           label)
                           
    def mousePressEvent(self, event) -> None:
        self.last_pos = event.pos()
        
    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.pos() - self.last_pos
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self.last_pos = event.pos()
            self.update()
            
    def wheelEvent(self, event) -> None:
        factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        self.scale_factor *= factor
        self.update()

class NetworkVisualizer(QWidget):
    """Main network visualization widget."""
    
    def __init__(self) -> None:
        """Initialize the network visualizer."""
        super().__init__()
        self.graph: nx.DiGraph = nx.DiGraph()
        self.node_positions: Dict[str, tuple[float, float]] = {}
        self.node_colors: Dict[str, str] = {}
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Control panel
        control_panel = QFrame()
        control_panel.setStyleSheet("""
            QFrame {
                background: #2D2D2D;
                border-bottom: 1px solid #1E1E1E;
            }
        """)
        control_layout = QHBoxLayout(control_panel)
        
        # Layout type selector
        layout_label = QLabel("Layout:")
        layout_label.setStyleSheet("color: #CCCCCC;")
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Hierarchical", "Circular", "Spring"])
        self.layout_combo.setStyleSheet("""
            QComboBox {
                background: #3C3C3C;
                color: #CCCCCC;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(resources/icons/dropdown.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background: #3C3C3C;
                color: #CCCCCC;
                selection-background-color: #094771;
            }
        """)
        self.layout_combo.currentTextChanged.connect(self.update_layout)
        
        # Zoom controls
        zoom_in_btn = QPushButton("+")
        zoom_out_btn = QPushButton("-")
        fit_btn = QPushButton("Fit")
        
        for btn in [zoom_in_btn, zoom_out_btn, fit_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: #0E639C;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    min-width: 30px;
                }
                QPushButton:hover {
                    background: #1177BB;
                }
                QPushButton:pressed {
                    background: #0D5789;
                }
            """)
            
        zoom_in_btn.clicked.connect(lambda: self.zoom(1.2))
        zoom_out_btn.clicked.connect(lambda: self.zoom(0.8))
        fit_btn.clicked.connect(self.fit_to_view)
        
        control_layout.addWidget(layout_label)
        control_layout.addWidget(self.layout_combo)
        control_layout.addStretch()
        control_layout.addWidget(zoom_out_btn)
        control_layout.addWidget(zoom_in_btn)
        control_layout.addWidget(fit_btn)
        
        # Network view
        self.view = NetworkView()
        
        layout.addWidget(control_panel)
        layout.addWidget(self.view)
        
        # Apply theme styles
        self.style_manager = StyleManager()
        self.setStyleSheet(f"""
            QWidget {{
                background: {ColorScheme.ML_BACKGROUND.value};
                border: 1px solid {ColorScheme.ML_BORDER.value};
            }}
        """)
        
    def set_network(self, model: Any) -> None:
        """Update visualization with new model.
        
        Args:
            model: The neural network model to visualize
        """
        self.graph.clear()
        self.node_positions.clear()
        self.node_colors.clear()
        
        # Create nodes and edges from model
        prev_layer = None
        for name, layer in model.named_modules():
            if len(name.split('.')) > 1:  # Skip nested modules
                continue
                
            # Add node
            self.graph.add_node(name)
            
            # Set node color based on layer type
            layer_type = layer.__class__.__name__
            if 'Conv' in layer_type:
                self.node_colors[name] = ColorScheme.SYNTAX_CLASS.value
            elif 'Linear' in layer_type:
                self.node_colors[name] = ColorScheme.SYNTAX_FUNCTION.value
            elif any(x in layer_type for x in ['ReLU', 'Sigmoid', 'Tanh']):
                self.node_colors[name] = ColorScheme.SYNTAX_KEYWORD.value
            elif 'Pool' in layer_type:
                self.node_colors[name] = ColorScheme.SYNTAX_OPERATOR.value
            else:
                self.node_colors[name] = ColorScheme.FOREGROUND.value
                
            # Add edge from previous layer
            if prev_layer is not None:
                self.graph.add_edge(prev_layer, name)
            prev_layer = name
            
        self.update_layout()
        
    def update_layout(self) -> None:
        """Update the network layout."""
        if not self.graph:
            return
            
        # Calculate node positions using spring layout
        pos = nx.spring_layout(self.graph)
        self.node_positions = {node: (x, y) for node, (x, y) in pos.items()}
        self.view.graph = self.graph
        self.view.node_positions = self.node_positions
        self.view.node_colors = self.node_colors
        self.view.update()
        
    def zoom(self, factor: float) -> None:
        """Zoom the view by the given factor"""
        self.view.scale(factor, factor)
        
    def fit_to_view(self) -> None:
        """Fit the network visualization to the view"""
        self.view.fit_in_view(self.view.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
