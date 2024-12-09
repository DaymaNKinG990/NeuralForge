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
            # Convert model to evaluation mode
            self.model.eval()
            
            # Create background data
            background = self.data[:100].clone()  # Use first 100 samples as background
            
            # Create explainer
            def model_wrapper(x):
                # Convert numpy array to tensor
                if isinstance(x, np.ndarray):
                    x = torch.tensor(x, dtype=torch.float32)
                return self.model(x).detach().numpy()
                
            # Create a wrapper that handles batches
            def batch_predictor(x):
                if len(x.shape) == 1:
                    x = x.reshape(1, -1)
                return model_wrapper(x)
            
            # Convert background data to numpy for SHAP
            background_np = background.detach().numpy()
            
            # Initialize explainer with background data
            explainer = shap.KernelExplainer(
                batch_predictor,
                background_np,
                link="identity"
            )
            
            # Calculate SHAP values for a subset of data
            sample_data = self.data[:10].detach().numpy()  # Use 10 samples for visualization
            shap_values = explainer.shap_values(sample_data)
            
            # Convert shap_values to numpy array if it's a list
            if isinstance(shap_values, list):
                shap_values = np.array(shap_values[0])
            elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) > 2:
                shap_values = shap_values[0]  # Take first output for multi-output models
            
            # Plot feature importance
            fig = self.importance_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            # Calculate mean absolute SHAP values for feature importance
            feature_importance = np.mean(np.abs(shap_values), axis=0)
            if len(feature_importance.shape) > 1:
                feature_importance = feature_importance.mean(axis=1)  # Reduce to 1D array
            ax.bar(self.feature_names, feature_importance)
            ax.set_title("SHAP Feature Importance")
            ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            self.importance_canvas.draw()
            
            # Plot sample interpretation
            fig = self.sample_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            # Plot SHAP values for first sample
            sample_shap = shap_values[0]  # Get first sample's SHAP values
            if len(sample_shap.shape) > 1:
                sample_shap = sample_shap.mean(axis=1)  # Reduce to 1D if needed
            ax.barh(self.feature_names, sample_shap)
            ax.set_title("SHAP Values for First Sample")
            
            fig.tight_layout()
            self.sample_canvas.draw()
            
            # Emit interpretation results
            interpretation_results = {
                'method': 'SHAP Values',
                'feature_importance': feature_importance.tolist(),
                'sample_interpretation': sample_shap.tolist(),
                'feature_names': self.feature_names,
                'expected_value': explainer.expected_value if np.isscalar(explainer.expected_value) 
                                else explainer.expected_value.tolist()
            }
            self.interpretation_updated.emit(interpretation_results)
            
        except Exception as e:
            self.logger.error(f"Error in SHAP interpretation: {str(e)}", exc_info=True)
            
    def _interpret_integrated_gradients(self):
        """Interpret model using Integrated Gradients."""
        try:
            # Create attributor
            ig = IntegratedGradients(self.model)
            
            # Calculate attributions
            attributions, delta = ig.attribute(
                self.data[:1000],
                n_steps=50,
                return_convergence_delta=True
            )
            
            # Plot feature importance
            fig = self.importance_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            # Calculate mean absolute attribution for each feature
            feature_importance = torch.mean(torch.abs(attributions), dim=0)
            ax.bar(self.feature_names, feature_importance.detach().numpy())
            ax.set_title("Integrated Gradients Feature Importance")
            ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            self.importance_canvas.draw()
            
            # Plot sample interpretation
            fig = self.sample_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            # Plot attribution for a single sample
            sample_attr = attributions[0].detach().numpy()
            ax.bar(self.feature_names, sample_attr)
            ax.set_title("Sample Attribution")
            ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            self.sample_canvas.draw()
            
            # Emit interpretation results
            interpretation_data = {
                'method': 'Integrated Gradients',
                'feature_importance': feature_importance.detach().numpy().tolist(),
                'sample_attribution': sample_attr.tolist(),
                'convergence_delta': delta.mean().item()
            }
            self.interpretation_updated.emit(interpretation_data)
            
        except Exception as e:
            self.logger.error(f"Error in Integrated Gradients interpretation: {str(e)}", exc_info=True)
            
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
