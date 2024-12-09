"""Model visualization component."""
from .plot_base import PlotBase
import torch
import numpy as np
import seaborn as sns

class ModelPlot(PlotBase):
    """Component for plotting model-related visualizations."""
    
    def plot_layer_weights(self, model, layer_name=None):
        """Plot layer weights distribution."""
        try:
            self.clear_plot()
            
            if layer_name:
                # Get specific layer
                for name, module in model.named_modules():
                    if name == layer_name:
                        weights = module.weight.data.flatten().cpu().numpy()
                        break
            else:
                # Get all weights
                weights = []
                for param in model.parameters():
                    if len(param.data.size()) > 1:  # Only include weight matrices
                        weights.extend(param.data.flatten().cpu().numpy())
                weights = np.array(weights)
            
            ax = self.figure.add_subplot(111)
            sns.histplot(weights, kde=True, ax=ax)
            ax.set_title(f"Weight Distribution{f' - {layer_name}' if layer_name else ''}")
            ax.set_xlabel("Weight Value")
            ax.set_ylabel("Count")
            
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting layer weights: {str(e)}")
            
    def plot_activation_map(self, activations, layer_name=None):
        """Plot activation maps."""
        try:
            self.clear_plot()
            
            if len(activations.shape) == 4:  # Conv layer activations
                # Take first sample and average across channels
                act_map = activations[0].mean(0).cpu().numpy()
                
                ax = self.figure.add_subplot(111)
                im = ax.imshow(act_map, cmap='viridis')
                self.figure.colorbar(im)
                ax.set_title(f"Activation Map{f' - {layer_name}' if layer_name else ''}")
                
            else:  # Dense layer activations
                ax = self.figure.add_subplot(111)
                sns.heatmap(activations.cpu().numpy(), cmap='viridis', ax=ax)
                ax.set_title(f"Activation Values{f' - {layer_name}' if layer_name else ''}")
            
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting activation map: {str(e)}")
            
    def plot_gradient_flow(self, named_parameters):
        """Plot gradient flow in the network."""
        try:
            self.clear_plot()
            
            ave_grads = []
            layers = []
            for n, p in named_parameters:
                if p.requires_grad and "bias" not in n and p.grad is not None:
                    layers.append(n)
                    ave_grads.append(p.grad.abs().mean().cpu().item())
            
            ax = self.figure.add_subplot(111)
            ax.bar(np.arange(len(ave_grads)), ave_grads)
            ax.set_xticks(np.arange(len(ave_grads)))
            ax.set_xticklabels(layers, rotation=45)
            ax.set_title("Gradient Flow")
            ax.set_xlabel("Layers")
            ax.set_ylabel("Average Gradient")
            
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting gradient flow: {str(e)}")
            
    def plot_loss_curve(self, losses, val_losses=None):
        """Plot training and validation loss curves."""
        try:
            self.clear_plot()
            
            ax = self.figure.add_subplot(111)
            ax.plot(losses, label='Training Loss')
            if val_losses is not None:
                ax.plot(val_losses, label='Validation Loss')
            
            ax.set_title("Loss Curves")
            ax.set_xlabel("Epoch")
            ax.set_ylabel("Loss")
            ax.legend()
            
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting loss curve: {str(e)}")
