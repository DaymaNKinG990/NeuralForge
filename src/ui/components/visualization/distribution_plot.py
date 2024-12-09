"""Distribution plot component."""
from .plot_base import PlotBase
import seaborn as sns
from scipy import stats
import numpy as np

class DistributionPlot(PlotBase):
    """Component for plotting data distributions."""
    
    def plot_distribution(self, data, feature_name=None):
        """Plot distribution analysis."""
        try:
            self.clear_plot()
            
            # Create subplots for different distribution views
            gs = self.figure.add_gridspec(2, 2)
            ax1 = self.figure.add_subplot(gs[0, 0])  # Histogram
            ax2 = self.figure.add_subplot(gs[0, 1])  # Box plot
            ax3 = self.figure.add_subplot(gs[1, :])  # QQ plot
            
            # Histogram with KDE
            sns.histplot(data=data, kde=True, ax=ax1)
            ax1.set_title("Distribution with KDE")
            if feature_name:
                ax1.set_xlabel(feature_name)
            
            # Box plot
            sns.boxplot(data=data, ax=ax2)
            ax2.set_title("Box Plot")
            if feature_name:
                ax2.set_ylabel(feature_name)
            
            # QQ plot
            stats.probplot(data, dist="norm", plot=ax3)
            ax3.set_title("Q-Q Plot")
            
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting distribution: {str(e)}")
            
    def plot_correlation_matrix(self, data, method='pearson'):
        """Plot correlation matrix."""
        try:
            self.clear_plot()
            
            ax = self.figure.add_subplot(111)
            corr = data.corr(method=method.lower())
            sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
            ax.set_title(f"{method.capitalize()} Correlation Matrix")
            
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting correlation matrix: {str(e)}")
            
    def plot_feature_importance(self, features, importance, title="Feature Importance"):
        """Plot feature importance."""
        try:
            self.clear_plot()
            
            ax = self.figure.add_subplot(111)
            ax.bar(features, importance)
            ax.set_title(title)
            ax.tick_params(axis='x', rotation=45)
            
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error plotting feature importance: {str(e)}")

    def update_metrics(self, metrics):
        """Update plot with training metrics."""
        try:
            self.clear_plot()
            
            # Convert metrics to numpy array for plotting
            if isinstance(metrics, (list, tuple)):
                if all(isinstance(m, dict) for m in metrics):
                    metrics_data = np.array([list(m.values()) for m in metrics])
                else:
                    metrics_data = np.array(metrics)
            elif isinstance(metrics, dict):
                metrics_data = np.array([list(metrics.values())])
            else:
                # Handle single value metrics
                metrics_data = np.array([[float(metrics)]])
            
            # Create subplots for metrics visualization
            gs = self.figure.add_gridspec(2, 1)
            ax1 = self.figure.add_subplot(gs[0])  # Loss plot
            ax2 = self.figure.add_subplot(gs[1])  # Accuracy plot
            
            # Plot training metrics
            steps = range(1, len(metrics_data) + 1)
            ax1.plot(steps, metrics_data[:, 0], 'b-', label='Loss')
            ax1.set_title('Training Loss')
            ax1.set_xlabel('Step')
            ax1.set_ylabel('Loss')
            ax1.grid(True)
            ax1.legend()
            
            if metrics_data.shape[1] > 1:  # If accuracy data exists
                ax2.plot(steps, metrics_data[:, 1], 'g-', label='Accuracy')
                ax2.set_title('Training Accuracy')
                ax2.set_xlabel('Step')
                ax2.set_ylabel('Accuracy')
                ax2.grid(True)
                ax2.legend()
            
            self.update_layout()
            
        except Exception as e:
            self.logger.error(f"Error updating metrics plot: {str(e)}", exc_info=True)
