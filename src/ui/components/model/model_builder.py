"""Model building component."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QComboBox, QSpinBox, QLineEdit, QListWidget,
                           QScrollArea, QFrame, QDoubleSpinBox)
from PyQt6.QtCore import pyqtSignal
import torch
import torch.nn as nn
import logging
from typing import List, Dict, Optional
from collections import OrderedDict

class LayerConfig:
    """Configuration for a neural network layer."""
    def __init__(self, layer_type: str, params: Dict):
        self.layer_type = layer_type
        self.params = params
        
    def create_layer(self) -> nn.Module:
        """Create a PyTorch layer from configuration."""
        try:
            layer_class = getattr(nn, self.layer_type)
            return layer_class(**self.params)
        except Exception as e:
            raise ValueError(f"Error creating layer: {str(e)}")

class ModelBuilder(QWidget):
    """Widget for building neural network models."""
    
    model_created = pyqtSignal(object)  # Emits created model
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.param_widgets = {}  # Store parameter widgets
        self._setup_ui()
        self._initialize_state()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Layer type selection
        layer_layout = QHBoxLayout()
        self.layer_combo = QComboBox()
        self.layer_combo.addItems([
            "Linear",
            "Conv2d",
            "MaxPool2d",
            "ReLU",
            "Dropout",
            "BatchNorm1d",
            "BatchNorm2d"
        ])
        layer_layout.addWidget(QLabel("Layer Type:"))
        layer_layout.addWidget(self.layer_combo)
        layout.addLayout(layer_layout)
        
        # Parameter area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.param_container = QWidget()
        self.param_layout = QVBoxLayout(self.param_container)
        scroll.setWidget(self.param_container)
        layout.addWidget(scroll)
        
        # Layer list
        self.layer_list = QListWidget()
        layout.addWidget(self.layer_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Layer")
        add_btn.clicked.connect(self._add_layer)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Layer")
        remove_btn.clicked.connect(self._remove_layer)
        button_layout.addWidget(remove_btn)
        
        create_btn = QPushButton("Create Model")
        create_btn.clicked.connect(self._create_model)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.layer_combo.currentTextChanged.connect(self._update_params_ui)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.layers = []  # Store layer configurations
        self._update_params_ui()
        
    def _update_params_ui(self):
        """Update parameter UI based on selected layer type."""
        try:
            # Clear existing parameter widgets
            for widget in self.param_widgets.values():
                self.param_layout.removeWidget(widget)
                widget.deleteLater()
            self.param_widgets.clear()
            
            layer_type = self.layer_combo.currentText()
            
            # Add parameter widgets based on layer type
            if layer_type == "Linear":
                self._add_param_widget("in_features", QSpinBox(), 1, 1024)
                self._add_param_widget("out_features", QSpinBox(), 1, 1024)
                
            elif layer_type == "Conv2d":
                self._add_param_widget("in_channels", QSpinBox(), 1, 512)
                self._add_param_widget("out_channels", QSpinBox(), 1, 512)
                self._add_param_widget("kernel_size", QSpinBox(), 1, 7)
                self._add_param_widget("stride", QSpinBox(), 1, 3)
                self._add_param_widget("padding", QSpinBox(), 0, 3)
                
            elif layer_type == "MaxPool2d":
                self._add_param_widget("kernel_size", QSpinBox(), 1, 5)
                self._add_param_widget("stride", QSpinBox(), 1, 3)
                self._add_param_widget("padding", QSpinBox(), 0, 2)
                
            elif layer_type == "Dropout":
                spin = QDoubleSpinBox()
                spin.setRange(0, 1)
                spin.setValue(0.5)
                self._add_param_widget("p", spin)
                
            elif layer_type in ["BatchNorm1d", "BatchNorm2d"]:
                self._add_param_widget("num_features", QSpinBox(), 1, 512)
                
        except Exception as e:
            self.logger.error(f"Error updating params UI: {str(e)}", exc_info=True)
            
    def _add_param_widget(self, name: str, widget: QWidget, min_val: Optional[int] = None, max_val: Optional[int] = None):
        """Add a parameter widget to the UI.
        
        Args:
            name: Parameter name
            widget: Widget for parameter input
            min_val: Minimum value for numeric widgets
            max_val: Maximum value for numeric widgets
        """
        try:
            if isinstance(widget, QSpinBox):
                if min_val is not None:
                    widget.setMinimum(min_val)
                if max_val is not None:
                    widget.setMaximum(max_val)
                    
            param_layout = QHBoxLayout()
            param_layout.addWidget(QLabel(f"{name}:"))
            param_layout.addWidget(widget)
            
            container = QWidget()
            container.setLayout(param_layout)
            self.param_layout.addWidget(container)
            self.param_widgets[name] = container
            
        except Exception as e:
            self.logger.error(f"Error adding param widget: {str(e)}", exc_info=True)
            
    def _add_layer(self):
        """Add current layer configuration to the list."""
        try:
            layer_type = self.layer_combo.currentText()
            params = {}
            
            for name, widget in self.param_widgets.items():
                param_widget = widget.layout().itemAt(1).widget()
                if isinstance(param_widget, QSpinBox):
                    if name == "p":  # Handle dropout probability
                        params[name] = param_widget.value() / 100.0
                    else:
                        params[name] = param_widget.value()
                elif isinstance(param_widget, QDoubleSpinBox):
                    params[name] = param_widget.value()
                        
            layer_config = LayerConfig(layer_type, params)
            self.layers.append(layer_config)
            
            # Update layer list
            self.layer_list.addItem(f"{layer_type}: {params}")
            
        except Exception as e:
            self.logger.error(f"Error adding layer: {str(e)}", exc_info=True)
            
    def _remove_layer(self):
        """Remove selected layer from the list."""
        try:
            current_row = self.layer_list.currentRow()
            if current_row >= 0:
                self.layer_list.takeItem(current_row)
                self.layers.pop(current_row)
        except Exception as e:
            self.logger.error(f"Error removing layer: {str(e)}", exc_info=True)
            
    def _create_model(self):
        """Create PyTorch model from layer configurations."""
        try:
            if not self.layers:
                self.logger.warning("No layers added to model")
                return
                
            # Create ordered dict of layers
            layers = OrderedDict()
            for i, config in enumerate(self.layers):
                try:
                    layer = config.create_layer()
                    layers[f"{config.layer_type}_{i}"] = layer
                except Exception as e:
                    self.logger.error(f"Error creating layer {i}: {str(e)}")
                    return
                    
            # Create sequential model
            model = nn.Sequential(layers)
            self.model_created.emit(model)
            
        except Exception as e:
            self.logger.error(f"Error creating model: {str(e)}", exc_info=True)
            
    def reset(self):
        """Reset builder state."""
        self._initialize_state()
        self.layer_list.clear()
        self.layer_combo.setCurrentIndex(0)
        self._update_params_ui()
