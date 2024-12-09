"""Advanced visualization components."""
from .plot_base import PlotBase
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from sklearn.metrics import confusion_matrix, roc_curve, precision_recall_curve
import torch
import torch.nn as nn
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class FeatureVisualization(PlotBase):
    """Advanced feature visualization component."""
    
    def plot_feature_interactions(self, data, feature_names=None):
        """Plot pairwise feature interactions."""
        try:
            self.clear_plot()
            if feature_names is None:
                feature_names = [f"Feature {i}" for i in range(data.shape[1])]
                
            # Create pair plot
            df = pd.DataFrame(data, columns=feature_names)
            sns.pairplot(df, diag_kind='kde')
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting feature interactions: {str(e)}")
            
    def plot_feature_importance_heatmap(self, importance_matrix, feature_names=None):
        """Plot feature importance heatmap across different metrics."""
        try:
            self.clear_plot()
            ax = self.figure.add_subplot(111)
            
            if feature_names is None:
                feature_names = [f"Feature {i}" for i in range(importance_matrix.shape[1])]
                
            sns.heatmap(importance_matrix, 
                       xticklabels=feature_names,
                       yticklabels=['Correlation', 'Mutual Info', 'SHAP', 'Permutation'],
                       annot=True, cmap='viridis', ax=ax)
            
            ax.set_title("Feature Importance Comparison")
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting importance heatmap: {str(e)}")
            
    def plot_dimensionality_reduction(self, data, labels=None, method='tsne'):
        """Plot dimensionality reduction visualization."""
        try:
            self.clear_plot()
            
            if method.lower() == 'tsne':
                reducer = TSNE(n_components=2, random_state=42)
            else:  # PCA
                reducer = PCA(n_components=2)
                
            reduced_data = reducer.fit_transform(data)
            
            ax = self.figure.add_subplot(111)
            scatter = ax.scatter(reduced_data[:, 0], reduced_data[:, 1],
                               c=labels if labels is not None else None,
                               cmap='viridis')
                               
            if labels is not None:
                self.figure.colorbar(scatter)
                
            ax.set_title(f"{method.upper()} Visualization")
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting dimensionality reduction: {str(e)}")

class ModelVisualization(PlotBase):
    """Advanced model visualization component."""
    
    def plot_attention_weights(self, attention_weights, heads=None):
        """Plot attention weights for transformer models."""
        try:
            self.clear_plot()
            
            if heads is None:
                heads = range(attention_weights.shape[0])
                
            n_heads = len(heads)
            fig = make_subplots(rows=1, cols=n_heads,
                              subplot_titles=[f"Head {h}" for h in heads])
                              
            for i, head in enumerate(heads, 1):
                weights = attention_weights[head].numpy()
                fig.add_trace(
                    go.Heatmap(z=weights, colorscale='Viridis'),
                    row=1, col=i
                )
                
            fig.update_layout(title="Attention Weights by Head")
            # Convert plotly figure to matplotlib
            self.figure = plt.figure(figsize=(15, 5))
            self.figure.add_subplot(111).imshow(weights)
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting attention weights: {str(e)}")
            
    def plot_layer_activations_3d(self, activations, layer_name=None):
        """Plot 3D visualization of layer activations."""
        try:
            self.clear_plot()
            
            ax = self.figure.add_subplot(111, projection='3d')
            
            if len(activations.shape) == 2:
                # For dense layers
                x = np.arange(activations.shape[0])
                y = np.arange(activations.shape[1])
                X, Y = np.meshgrid(x, y)
                ax.plot_surface(X, Y, activations.T, cmap='viridis')
                
            elif len(activations.shape) == 4:
                # For conv layers, show first channel
                act_map = activations[0, 0].numpy()
                x = np.arange(act_map.shape[0])
                y = np.arange(act_map.shape[1])
                X, Y = np.meshgrid(x, y)
                ax.plot_surface(X, Y, act_map, cmap='viridis')
                
            ax.set_title(f"Layer Activations{f' - {layer_name}' if layer_name else ''}")
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting 3D activations: {str(e)}")
            
    def plot_gradient_flow_animated(self, gradient_history):
        """Plot animated gradient flow over training."""
        try:
            self.clear_plot()
            
            ax = self.figure.add_subplot(111)
            lines = []
            
            for gradients in gradient_history:
                line, = ax.plot(range(len(gradients)), gradients)
                lines.append([line])
                
            ani = animation.ArtistAnimation(self.figure, lines, 
                                          interval=200, blit=True)
                                          
            ax.set_title("Gradient Flow Over Training")
            ax.set_xlabel("Layers")
            ax.set_ylabel("Gradient Magnitude")
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting animated gradient flow: {str(e)}")

class PerformanceVisualization(PlotBase):
    """Model performance visualization component."""
    
    def plot_confusion_matrix(self, y_true, y_pred, labels=None):
        """Plot confusion matrix with additional metrics."""
        try:
            self.clear_plot()
            
            cm = confusion_matrix(y_true, y_pred)
            ax = self.figure.add_subplot(111)
            
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                       xticklabels=labels, yticklabels=labels)
                       
            ax.set_title("Confusion Matrix")
            ax.set_xlabel("Predicted")
            ax.set_ylabel("True")
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting confusion matrix: {str(e)}")
            
    def plot_roc_curves(self, y_true, y_scores, class_names=None):
        """Plot ROC curves for multi-class classification."""
        try:
            self.clear_plot()
            
            if class_names is None:
                class_names = [f"Class {i}" for i in range(y_scores.shape[1])]
                
            ax = self.figure.add_subplot(111)
            
            for i, class_name in enumerate(class_names):
                fpr, tpr, _ = roc_curve(y_true == i, y_scores[:, i])
                ax.plot(fpr, tpr, label=class_name)
                
            ax.plot([0, 1], [0, 1], 'k--')
            ax.set_title("ROC Curves")
            ax.set_xlabel("False Positive Rate")
            ax.set_ylabel("True Positive Rate")
            ax.legend()
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting ROC curves: {str(e)}")
            
    def plot_precision_recall(self, y_true, y_scores, class_names=None):
        """Plot precision-recall curves."""
        try:
            self.clear_plot()
            
            if class_names is None:
                class_names = [f"Class {i}" for i in range(y_scores.shape[1])]
                
            ax = self.figure.add_subplot(111)
            
            for i, class_name in enumerate(class_names):
                precision, recall, _ = precision_recall_curve(y_true == i, 
                                                           y_scores[:, i])
                ax.plot(recall, precision, label=class_name)
                
            ax.set_title("Precision-Recall Curves")
            ax.set_xlabel("Recall")
            ax.set_ylabel("Precision")
            ax.legend()
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting precision-recall curves: {str(e)}")
            
    def plot_training_metrics(self, metrics_history):
        """Plot multiple training metrics over time."""
        try:
            self.clear_plot()
            
            n_metrics = len(metrics_history)
            fig = make_subplots(rows=n_metrics, cols=1,
                              subplot_titles=list(metrics_history.keys()))
                              
            for i, (metric_name, values) in enumerate(metrics_history.items(), 1):
                fig.add_trace(
                    go.Scatter(y=values, name=metric_name),
                    row=i, col=1
                )
                
            fig.update_layout(height=200*n_metrics, title="Training Metrics")
            # Convert plotly figure to matplotlib
            self.figure = plt.figure(figsize=(10, 2*n_metrics))
            for i, (metric_name, values) in enumerate(metrics_history.items(), 1):
                ax = self.figure.add_subplot(n_metrics, 1, i)
                ax.plot(values)
                ax.set_title(metric_name)
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting training metrics: {str(e)}")
