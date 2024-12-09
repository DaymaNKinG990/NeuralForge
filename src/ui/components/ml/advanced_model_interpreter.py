"""Advanced model interpretation component with enhanced features."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QComboBox, QTabWidget, QSpinBox,
                           QCheckBox, QProgressBar, QDialog, QTextEdit)
from PyQt6.QtCore import pyqtSignal, Qt
import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from typing import Optional, List, Dict, Tuple, Any
import shap
from captum.attr import (
    IntegratedGradients, DeepLift, GradientShap,
    NoiseTunnel, LayerConductance, Occlusion,
    LayerActivation, LayerGradCam, Saliency,
    InputXGradient, GuidedBackprop
)
import seaborn as sns
from sklearn.manifold import TSNE
from ..visualization.advanced_plots import PerformanceVisualization

class InterpretationSettingsDialog(QDialog):
    """Dialog for configuring interpretation settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the settings dialog UI."""
        self.setWindowTitle("Interpretation Settings")
        layout = QVBoxLayout(self)
        
        # Sample size settings
        self.sample_size = QSpinBox()
        self.sample_size.setRange(1, 10000)
        self.sample_size.setValue(1000)
        layout.addWidget(QLabel("Sample Size:"))
        layout.addWidget(self.sample_size)
        
        # Background samples for SHAP
        self.background_size = QSpinBox()
        self.background_size.setRange(1, 1000)
        self.background_size.setValue(100)
        layout.addWidget(QLabel("Background Size (SHAP):"))
        layout.addWidget(self.background_size)
        
        # Steps for Integrated Gradients
        self.ig_steps = QSpinBox()
        self.ig_steps.setRange(10, 1000)
        self.ig_steps.setValue(50)
        layout.addWidget(QLabel("Integration Steps:"))
        layout.addWidget(self.ig_steps)
        
        # Noise tunnel settings
        self.use_noise_tunnel = QCheckBox("Use Noise Tunnel")
        self.noise_samples = QSpinBox()
        self.noise_samples.setRange(1, 100)
        self.noise_samples.setValue(10)
        layout.addWidget(self.use_noise_tunnel)
        layout.addWidget(QLabel("Noise Samples:"))
        layout.addWidget(self.noise_samples)
        
        # Buttons
        buttons = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(self.ok_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)
        
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings."""
        return {
            'sample_size': self.sample_size.value(),
            'background_size': self.background_size.value(),
            'ig_steps': self.ig_steps.value(),
            'use_noise_tunnel': self.use_noise_tunnel.isChecked(),
            'noise_samples': self.noise_samples.value()
        }

class AdvancedModelInterpreter(QWidget):
    """Advanced widget for interpreting ML model decisions."""
    
    interpretation_updated = pyqtSignal(dict)
    
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
            "Layer Attribution",
            "Occlusion",
            "Grad-CAM",
            "Guided Backprop",
            "Input × Gradient",
            "Saliency Maps"
        ])
        self.method_combo.currentTextChanged.connect(self._update_interpretation)
        
        # Layer selection
        self.layer_combo = QComboBox()
        self.layer_combo.setEnabled(False)
        self.layer_combo.currentTextChanged.connect(self._update_interpretation)
        
        # Settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self._show_settings)
        
        controls_layout.addWidget(QLabel("Method:"))
        controls_layout.addWidget(self.method_combo)
        controls_layout.addWidget(QLabel("Layer:"))
        controls_layout.addWidget(self.layer_combo)
        controls_layout.addWidget(self.settings_btn)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        
        # Tabs for different visualizations
        self.tab_widget = QTabWidget()
        
        # Feature importance tab
        self.importance_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.importance_canvas, "Feature Importance")
        
        # Sample interpretation tab
        self.sample_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.sample_canvas, "Sample Interpretation")
        
        # Layer visualization tab
        self.layer_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.layer_canvas, "Layer Visualization")
        
        # Feature interactions tab
        self.interactions_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.interactions_canvas,
                             "Feature Interactions")
        
        # Interpretation summary
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        
        # Add components to layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.progress)
        layout.addWidget(self.tab_widget)
        layout.addWidget(self.summary_text)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.model = None
        self.data = None
        self.feature_names = None
        self.current_interpretation = None
        self.settings = {
            'sample_size': 1000,
            'background_size': 100,
            'ig_steps': 50,
            'use_noise_tunnel': False,
            'noise_samples': 10
        }
        
    def _show_settings(self):
        """Show settings dialog."""
        try:
            dialog = InterpretationSettingsDialog(self)
            
            # Set current settings
            dialog.sample_size.setValue(self.settings['sample_size'])
            dialog.background_size.setValue(self.settings['background_size'])
            dialog.ig_steps.setValue(self.settings['ig_steps'])
            dialog.use_noise_tunnel.setChecked(
                self.settings['use_noise_tunnel']
            )
            dialog.noise_samples.setValue(self.settings['noise_samples'])
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.settings = dialog.get_settings()
                self._update_interpretation()
                
        except Exception as e:
            self.logger.error(f"Error showing settings: {str(e)}")
            
    def _update_progress(self, value: int):
        """Update progress bar."""
        self.progress.setValue(value)
        self.progress.setVisible(value < 100)
        
    def _interpret_with_noise_tunnel(self, attributor: Any,
                                   data: torch.Tensor) -> torch.Tensor:
        """Apply noise tunnel to attribution method."""
        nt = NoiseTunnel(attributor)
        return nt.attribute(
            data,
            n_samples=self.settings['noise_samples'],
            nt_type='smoothgrad',
            stdevs=0.1
        )
        
    def _plot_feature_interactions(self, attributions: torch.Tensor):
        """Plot feature interactions using SHAP interaction values."""
        try:
            fig = self.interactions_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            # Calculate pairwise interactions
            n_features = len(self.feature_names)
            interactions = np.zeros((n_features, n_features))
            
            for i in range(n_features):
                for j in range(i+1, n_features):
                    corr = np.corrcoef(
                        attributions[:, i].numpy(),
                        attributions[:, j].numpy()
                    )[0, 1]
                    interactions[i, j] = corr
                    interactions[j, i] = corr
                    
            # Plot heatmap
            sns.heatmap(interactions,
                       xticklabels=self.feature_names,
                       yticklabels=self.feature_names,
                       cmap='coolwarm',
                       center=0,
                       ax=ax)
            ax.set_title("Feature Interaction Strength")
            
            fig.tight_layout()
            self.interactions_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error plotting interactions: {str(e)}")
            
    def _interpret_occlusion(self):
        """Interpret model using Occlusion."""
        try:
            # Create attributor
            occluder = Occlusion(self.model)
            
            # Calculate attributions
            window_shape = (1,) * len(self.data.shape[1:])
            attributions = occluder.attribute(
                self.data[:self.settings['sample_size']],
                sliding_window_shapes=window_shape
            )
            
            self._plot_attributions(attributions, "Occlusion")
            
        except Exception as e:
            self.logger.error(f"Error in Occlusion interpretation: {str(e)}")
            
    def _interpret_gradcam(self):
        """Interpret model using Grad-CAM."""
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
            gc = LayerGradCam(self.model, layer)
            
            # Calculate attributions
            attributions = gc.attribute(
                self.data[:self.settings['sample_size']]
            )
            
            self._plot_attributions(attributions, "Grad-CAM")
            
        except Exception as e:
            self.logger.error(f"Error in Grad-CAM interpretation: {str(e)}")
            
    def _interpret_guided_backprop(self):
        """Interpret model using Guided Backpropagation."""
        try:
            # Create attributor
            gbp = GuidedBackprop(self.model)
            
            # Calculate attributions
            attributions = gbp.attribute(
                self.data[:self.settings['sample_size']]
            )
            
            if self.settings['use_noise_tunnel']:
                attributions = self._interpret_with_noise_tunnel(
                    gbp, self.data[:self.settings['sample_size']]
                )
                
            self._plot_attributions(attributions, "Guided Backprop")
            
        except Exception as e:
            self.logger.error(f"Error in Guided Backprop interpretation: {str(e)}")
            
    def _interpret_input_gradient(self):
        """Interpret model using Input × Gradient."""
        try:
            # Create attributor
            ig = InputXGradient(self.model)
            
            # Calculate attributions
            attributions = ig.attribute(
                self.data[:self.settings['sample_size']]
            )
            
            if self.settings['use_noise_tunnel']:
                attributions = self._interpret_with_noise_tunnel(
                    ig, self.data[:self.settings['sample_size']]
                )
                
            self._plot_attributions(attributions, "Input × Gradient")
            
        except Exception as e:
            self.logger.error(f"Error in Input × Gradient interpretation: {str(e)}")
            
    def _interpret_saliency(self):
        """Interpret model using Saliency Maps."""
        try:
            # Create attributor
            saliency = Saliency(self.model)
            
            # Calculate attributions
            attributions = saliency.attribute(
                self.data[:self.settings['sample_size']]
            )
            
            if self.settings['use_noise_tunnel']:
                attributions = self._interpret_with_noise_tunnel(
                    saliency, self.data[:self.settings['sample_size']]
                )
                
            self._plot_attributions(attributions, "Saliency Maps")
            
        except Exception as e:
            self.logger.error(f"Error in Saliency Maps interpretation: {str(e)}")
            
    def _plot_attributions(self, attributions: torch.Tensor,
                          method_name: str):
        """Plot attribution results."""
        try:
            # Plot feature importance
            fig = self.importance_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            attr_mean = attributions.mean(0).abs()
            ax.bar(self.feature_names, attr_mean)
            ax.set_title(f"{method_name} Feature Importance")
            ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            self.importance_canvas.draw()
            
            # Plot sample interpretation
            fig = self.sample_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            
            sample_attr = attributions[0].abs()
            ax.bar(self.feature_names, sample_attr)
            ax.set_title(f"{method_name} Sample Attribution")
            ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            self.sample_canvas.draw()
            
            # Plot feature interactions
            self._plot_feature_interactions(attributions)
            
            # Update summary
            self._update_summary(attributions, method_name)
            
        except Exception as e:
            self.logger.error(f"Error plotting attributions: {str(e)}")
            
    def _update_summary(self, attributions: torch.Tensor,
                       method_name: str):
        """Update interpretation summary."""
        try:
            summary = []
            summary.append(f"Method: {method_name}")
            summary.append(f"Sample Size: {self.settings['sample_size']}")
            
            # Top influential features
            attr_mean = attributions.mean(0).abs()
            top_features = torch.argsort(attr_mean, descending=True)[:5]
            
            summary.append("\nTop 5 Influential Features:")
            for idx in top_features:
                feature_name = self.feature_names[idx]
                importance = attr_mean[idx].item()
                summary.append(f"- {feature_name}: {importance:.4f}")
                
            # Attribution statistics
            summary.append("\nAttribution Statistics:")
            summary.append(f"Mean: {attributions.mean().item():.4f}")
            summary.append(f"Std: {attributions.std().item():.4f}")
            summary.append(f"Max: {attributions.max().item():.4f}")
            summary.append(f"Min: {attributions.min().item():.4f}")
            
            self.summary_text.setText("\n".join(summary))
            
        except Exception as e:
            self.logger.error(f"Error updating summary: {str(e)}")
            
    def export_interpretation(self, filename: str):
        """Export current interpretation to file."""
        try:
            if self.current_interpretation is None:
                return
                
            data = {
                'method': self.method_combo.currentText(),
                'settings': self.settings,
                'feature_names': self.feature_names,
                'attributions': self.current_interpretation.numpy().tolist(),
                'summary': self.summary_text.toPlainText()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error exporting interpretation: {str(e)}")
            
    def load_interpretation(self, filename: str):
        """Load interpretation from file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            self.method_combo.setCurrentText(data['method'])
            self.settings = data['settings']
            self.feature_names = data['feature_names']
            self.current_interpretation = torch.tensor(data['attributions'])
            
            self._plot_attributions(self.current_interpretation,
                                  data['method'])
            self.summary_text.setText(data['summary'])
            
        except Exception as e:
            self.logger.error(f"Error loading interpretation: {str(e)}")
            
    def get_interpretation_metrics(self) -> Dict[str, float]:
        """Get quantitative metrics for current interpretation."""
        try:
            if self.current_interpretation is None:
                return {}
                
            attr = self.current_interpretation
            return {
                'mean_attribution': attr.mean().item(),
                'attribution_std': attr.std().item(),
                'max_attribution': attr.max().item(),
                'min_attribution': attr.min().item(),
                'total_effect': attr.abs().sum().item(),
                'sparsity': (attr.abs() < 1e-10).float().mean().item()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting metrics: {str(e)}")
            return {}
