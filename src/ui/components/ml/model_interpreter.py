"""Model interpretation component for ML workspace."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QComboBox, QTabWidget)
from PyQt6.QtCore import pyqtSignal
import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from typing import Optional, List, Dict
import shap
from captum.attr import (
    IntegratedGradients, DeepLift, GradientShap,
    NoiseTunnel, LayerConductance
)

class ModelInterpreter(QWidget):
    """Widget for interpreting ML model decisions."""
    
    interpretation_updated = pyqtSignal(dict)  # Emitted when interpretation is updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_state()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Interpretation controls
        controls_layout = QHBoxLayout()
        
        # Method selection
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "SHAP Values",
            "Integrated Gradients",
            "DeepLift",
            "Gradient SHAP",
            "Layer Attribution"
        ])
        self.method_combo.currentTextChanged.connect(self._update_interpretation)
        
        # Layer selection for layer attribution
        self.layer_combo = QComboBox()
        self.layer_combo.setEnabled(False)
        self.layer_combo.currentTextChanged.connect(self._update_interpretation)
        
        controls_layout.addWidget(QLabel("Method:"))
        controls_layout.addWidget(self.method_combo)
        controls_layout.addWidget(QLabel("Layer:"))
        controls_layout.addWidget(self.layer_combo)
        
        # Tabs for different visualizations
        self.tab_widget = QTabWidget()
        
        # Feature importance tab
        self.importance_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.importance_canvas, "Feature Importance")
        
        # Sample interpretation tab
        self.sample_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.sample_canvas, "Sample Interpretation")
        
        # Layer attribution tab
        self.layer_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.layer_canvas, "Layer Attribution")
        
        # Add components to layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.tab_widget)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.model = None
        self.data = None
        self.feature_names = None
        self.current_interpretation = None
        
    def set_model(self, model: nn.Module):
        """Set model for interpretation."""
        try:
            self.model = model
            self._update_layer_list()
            self._update_interpretation()
        except Exception as e:
            self.logger.error(f"Error setting model: {str(e)}")
            
    def set_data(self, data: torch.Tensor, feature_names: List[str]):
        """Set data for interpretation."""
        try:
            self.data = data
            self.feature_names = feature_names
            self._update_interpretation()
        except Exception as e:
            self.logger.error(f"Error setting data: {str(e)}")
            
    def _update_layer_list(self):
        """Update layer selection combo box."""
        try:
            self.layer_combo.clear()
            
            if self.model is not None:
                # Get all named modules
                for name, module in self.model.named_modules():
                    if isinstance(module, (nn.Linear, nn.Conv2d, nn.LSTM)):
                        self.layer_combo.addItem(name)
                        
            self.layer_combo.setEnabled(
                self.method_combo.currentText() == "Layer Attribution"
            )
            
        except Exception as e:
            self.logger.error(f"Error updating layer list: {str(e)}")
            
    def _update_interpretation(self):
        """Update interpretation based on selected method."""
        try:
            if self.model is None or self.data is None:
                return
                
            method = self.method_combo.currentText()
            
            if method == "SHAP Values":
                self._interpret_shap()
            elif method == "Integrated Gradients":
                self._interpret_integrated_gradients()
            elif method == "DeepLift":
                self._interpret_deeplift()
            elif method == "Gradient SHAP":
                self._interpret_gradient_shap()
            elif method == "Layer Attribution":
                self._interpret_layer_attribution()
                
        except Exception as e:
            self.logger.error(f"Error updating interpretation: {str(e)}")
            
    def _interpret_shap(self):
        """Interpret model using SHAP values."""
        try:
            # Create explainer
            background = self.data[:100]  # Use first 100 samples as background
            explainer = shap.DeepExplainer(self.model, background)
            
            # Calculate SHAP values
            shap_values = explainer.shap_values(self.data[:1000])
            
            # Plot feature importance
            fig = self.importance_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            shap.summary_plot(
                shap_values[0],
                self.data[:1000],
                feature_names=self.feature_names,
                show=False
            )
            ax.set_title("SHAP Feature Importance")
            
            fig.tight_layout()
            self.importance_canvas.draw()
            
            # Plot sample interpretation
            fig = self.sample_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            shap.force_plot(
                explainer.expected_value[0],
                shap_values[0][0],
                self.data[0],
                feature_names=self.feature_names,
                matplotlib=True,
                show=False
            )
            ax.set_title("SHAP Force Plot")
            
            fig.tight_layout()
            self.sample_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error in SHAP interpretation: {str(e)}")
            
    def _interpret_integrated_gradients(self):
        """Interpret model using Integrated Gradients."""
        try:
            # Create attributor
            ig = IntegratedGradients(self.model)
            
            # Calculate attributions
            attributions = ig.attribute(
                self.data[:1000],
                n_steps=50,
                return_convergence_delta=True
            )
            
            # Plot feature importance
            fig = self.importance_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            attr_mean = attributions[0].mean(0).abs()
            ax.bar(self.feature_names, attr_mean)
            ax.set_title("Integrated Gradients Feature Importance")
            ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            self.importance_canvas.draw()
            
            # Plot sample interpretation
            fig = self.sample_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            sample_attr = attributions[0][0].abs()
            ax.bar(self.feature_names, sample_attr)
            ax.set_title("Sample Attribution")
            ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            self.sample_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error in Integrated Gradients interpretation: {str(e)}")
            
    def _interpret_deeplift(self):
        """Interpret model using DeepLift."""
        try:
            # Create attributor
            dl = DeepLift(self.model)
            
            # Calculate attributions
            attributions = dl.attribute(self.data[:1000])
            
            # Plot feature importance
            fig = self.importance_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            attr_mean = attributions.mean(0).abs()
            ax.bar(self.feature_names, attr_mean)
            ax.set_title("DeepLift Feature Importance")
            ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            self.importance_canvas.draw()
            
            # Plot sample interpretation
            fig = self.sample_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            sample_attr = attributions[0].abs()
            ax.bar(self.feature_names, sample_attr)
            ax.set_title("Sample Attribution")
            ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            self.sample_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error in DeepLift interpretation: {str(e)}")
            
    def _interpret_gradient_shap(self):
        """Interpret model using Gradient SHAP."""
        try:
            # Create attributor
            gs = GradientShap(self.model)
            
            # Calculate attributions
            baseline = torch.zeros_like(self.data[:1])
            attributions = gs.attribute(
                self.data[:1000],
                baselines=baseline,
                n_samples=50
            )
            
            # Plot feature importance
            fig = self.importance_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            attr_mean = attributions.mean(0).abs()
            ax.bar(self.feature_names, attr_mean)
            ax.set_title("Gradient SHAP Feature Importance")
            ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            self.importance_canvas.draw()
            
            # Plot sample interpretation
            fig = self.sample_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            sample_attr = attributions[0].abs()
            ax.bar(self.feature_names, sample_attr)
            ax.set_title("Sample Attribution")
            ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            self.sample_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error in Gradient SHAP interpretation: {str(e)}")
            
    def _interpret_layer_attribution(self):
        """Interpret model using Layer Attribution."""
        try:
            layer_name = self.layer_combo.currentText()
            if not layer_name:
                return
                
            # Get layer
            for name, module in self.model.named_modules():
                if name == layer_name:
                    layer = module
                    break
            else:
                return
                
            # Create attributor
            lc = LayerConductance(self.model, layer)
            
            # Calculate attributions
            attributions = lc.attribute(self.data[:1000])
            
            # Plot layer attribution
            fig = self.layer_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            attr_mean = attributions.mean(0).abs()
            im = ax.imshow(attr_mean.detach().numpy(), cmap='viridis')
            ax.set_title(f"Layer Attribution: {layer_name}")
            fig.colorbar(im)
            
            fig.tight_layout()
            self.layer_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error in Layer Attribution interpretation: {str(e)}")
            
    def get_interpretation_summary(self) -> Dict:
        """Get summary of current interpretation."""
        try:
            summary = {
                'method': self.method_combo.currentText(),
                'layer': self.layer_combo.currentText(),
                'timestamp': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if self.model is not None:
                summary['model_type'] = type(self.model).__name__
                
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting interpretation summary: {str(e)}")
            return {}
            
    def reset(self):
        """Reset interpreter state."""
        try:
            self._initialize_state()
            self.method_combo.setCurrentIndex(0)
            self.layer_combo.clear()
            self.layer_combo.setEnabled(False)
            
            # Clear all canvases
            for canvas in [self.importance_canvas, self.sample_canvas,
                         self.layer_canvas]:
                canvas.figure.clear()
                canvas.draw()
                
        except Exception as e:
            self.logger.error(f"Error resetting interpreter: {str(e)}")
