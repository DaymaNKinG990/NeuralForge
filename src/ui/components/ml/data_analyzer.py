"""Data analysis component for ML workspace."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QComboBox, QTabWidget)
from PyQt6.QtCore import pyqtSignal
import logging
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from typing import Optional, List, Dict
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

class DataAnalyzer(QWidget):
    """Widget for analyzing and visualizing dataset characteristics."""
    
    analysis_updated = pyqtSignal(dict)  # Emitted when analysis is updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._initialize_state()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Analysis controls
        controls_layout = QHBoxLayout()
        
        # Plot type selection
        self.plot_combo = QComboBox()
        self.plot_combo.addItems([
            "Distribution Analysis",
            "Correlation Matrix",
            "Feature Importance",
            "Dimensionality Reduction",
            "Outlier Detection"
        ])
        self.plot_combo.currentTextChanged.connect(self._update_plot)
        
        # Additional options
        self.options_combo = QComboBox()
        self.options_combo.currentTextChanged.connect(self._update_plot)
        
        controls_layout.addWidget(QLabel("Analysis Type:"))
        controls_layout.addWidget(self.plot_combo)
        controls_layout.addWidget(QLabel("Options:"))
        controls_layout.addWidget(self.options_combo)
        
        # Tabs for different visualizations
        self.tab_widget = QTabWidget()
        
        # Distribution tab
        self.dist_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.dist_canvas, "Distribution")
        
        # Correlation tab
        self.corr_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.corr_canvas, "Correlation")
        
        # Feature importance tab
        self.feat_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.feat_canvas, "Features")
        
        # Dimensionality reduction tab
        self.dim_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.dim_canvas, "Dimensionality")
        
        # Add components to layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.tab_widget)
        
    def _initialize_state(self):
        """Initialize internal state."""
        self.data = None
        self.current_analysis = None
        self.scaler = StandardScaler()
        
    def set_data(self, data: pd.DataFrame):
        """Set data for analysis."""
        try:
            self.data = data
            self._update_options()
            self._update_plot()
        except Exception as e:
            self.logger.error(f"Error setting data: {str(e)}")
            
    def _update_options(self):
        """Update analysis options based on selected plot type."""
        try:
            plot_type = self.plot_combo.currentText()
            self.options_combo.clear()
            
            if plot_type == "Distribution Analysis":
                self.options_combo.addItems(self.data.columns)
            elif plot_type == "Correlation Matrix":
                self.options_combo.addItems(["Pearson", "Spearman", "Kendall"])
            elif plot_type == "Feature Importance":
                self.options_combo.addItems(["Variance", "Mutual Information"])
            elif plot_type == "Dimensionality Reduction":
                self.options_combo.addItems(["PCA", "t-SNE"])
            elif plot_type == "Outlier Detection":
                self.options_combo.addItems(["Z-Score", "IQR"])
                
        except Exception as e:
            self.logger.error(f"Error updating options: {str(e)}")
            
    def _update_plot(self):
        """Update plot based on selected analysis type."""
        try:
            if self.data is None:
                return
                
            plot_type = self.plot_combo.currentText()
            option = self.options_combo.currentText()
            
            if plot_type == "Distribution Analysis":
                self._plot_distribution(option)
            elif plot_type == "Correlation Matrix":
                self._plot_correlation(option)
            elif plot_type == "Feature Importance":
                self._plot_feature_importance(option)
            elif plot_type == "Dimensionality Reduction":
                self._plot_dimensionality_reduction(option)
            elif plot_type == "Outlier Detection":
                self._plot_outliers(option)
                
        except Exception as e:
            self.logger.error(f"Error updating plot: {str(e)}")
            
    def _plot_distribution(self, feature: str):
        """Plot distribution analysis."""
        try:
            fig = self.dist_canvas.figure
            fig.clear()
            
            # Create subplots for different distribution views
            gs = fig.add_gridspec(2, 2)
            ax1 = fig.add_subplot(gs[0, 0])  # Histogram
            ax2 = fig.add_subplot(gs[0, 1])  # Box plot
            ax3 = fig.add_subplot(gs[1, :])  # QQ plot
            
            # Histogram with KDE
            sns.histplot(data=self.data, x=feature, kde=True, ax=ax1)
            ax1.set_title("Distribution with KDE")
            
            # Box plot
            sns.boxplot(data=self.data, y=feature, ax=ax2)
            ax2.set_title("Box Plot")
            
            # QQ plot
            from scipy import stats
            stats.probplot(self.data[feature], dist="norm", plot=ax3)
            ax3.set_title("Q-Q Plot")
            
            fig.tight_layout()
            self.dist_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error plotting distribution: {str(e)}")
            
    def _plot_correlation(self, method: str):
        """Plot correlation matrix."""
        try:
            fig = self.corr_canvas.figure
            fig.clear()
            
            # Calculate correlation matrix
            corr = self.data.corr(method=method.lower())
            
            # Create heatmap
            ax = fig.add_subplot(111)
            sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
            ax.set_title(f"{method} Correlation Matrix")
            
            fig.tight_layout()
            self.corr_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error plotting correlation: {str(e)}")
            
    def _plot_feature_importance(self, method: str):
        """Plot feature importance analysis."""
        try:
            fig = self.feat_canvas.figure
            fig.clear()
            
            if method == "Variance":
                # Calculate variance for each feature
                importance = self.data.var()
            else:  # Mutual Information
                from sklearn.feature_selection import mutual_info_regression
                X = self.data.iloc[:, :-1]
                y = self.data.iloc[:, -1]
                importance = mutual_info_regression(X, y)
                
            # Create bar plot
            ax = fig.add_subplot(111)
            importance.plot(kind='bar', ax=ax)
            ax.set_title(f"Feature Importance ({method})")
            ax.set_xlabel("Features")
            ax.set_ylabel("Importance Score")
            
            fig.tight_layout()
            self.feat_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error plotting feature importance: {str(e)}")
            
    def _plot_dimensionality_reduction(self, method: str):
        """Plot dimensionality reduction analysis."""
        try:
            fig = self.dim_canvas.figure
            fig.clear()
            
            # Prepare data
            X = self.scaler.fit_transform(self.data)
            
            if method == "PCA":
                # Apply PCA
                pca = PCA(n_components=2)
                X_reduced = pca.fit_transform(X)
                explained_var = pca.explained_variance_ratio_
                title = f"PCA (Explained Variance: {sum(explained_var):.2%})"
            else:  # t-SNE
                # Apply t-SNE
                tsne = TSNE(n_components=2, random_state=42)
                X_reduced = tsne.fit_transform(X)
                title = "t-SNE Visualization"
                
            # Create scatter plot
            ax = fig.add_subplot(111)
            scatter = ax.scatter(X_reduced[:, 0], X_reduced[:, 1])
            ax.set_title(title)
            
            fig.tight_layout()
            self.dim_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error plotting dimensionality reduction: {str(e)}")
            
    def _plot_outliers(self, method: str):
        """Plot outlier detection analysis."""
        try:
            fig = self.dist_canvas.figure
            fig.clear()
            
            if method == "Z-Score":
                # Z-score method
                z_scores = np.abs((self.data - self.data.mean()) / self.data.std())
                outliers = (z_scores > 3).any(axis=1)
            else:  # IQR
                # IQR method
                Q1 = self.data.quantile(0.25)
                Q3 = self.data.quantile(0.75)
                IQR = Q3 - Q1
                outliers = ((self.data < (Q1 - 1.5 * IQR)) | 
                           (self.data > (Q3 + 1.5 * IQR))).any(axis=1)
                
            # Create scatter plot matrix for first few features
            pd.plotting.scatter_matrix(
                self.data.iloc[:, :4],
                figsize=(10, 10),
                c=['red' if x else 'blue' for x in outliers],
                alpha=0.5,
                diagonal='kde'
            )
            
            fig.suptitle(f"Outlier Detection ({method})")
            fig.tight_layout()
            self.dist_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Error plotting outliers: {str(e)}")
            
    def get_analysis_summary(self) -> Dict:
        """Get summary of current analysis."""
        try:
            summary = {
                'type': self.plot_combo.currentText(),
                'option': self.options_combo.currentText(),
                'timestamp': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if self.data is not None:
                summary.update({
                    'n_samples': len(self.data),
                    'n_features': len(self.data.columns),
                    'missing_values': self.data.isnull().sum().to_dict()
                })
                
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting analysis summary: {str(e)}")
            return {}
            
    def reset(self):
        """Reset analyzer state."""
        try:
            self._initialize_state()
            self.plot_combo.setCurrentIndex(0)
            self.options_combo.clear()
            
            # Clear all canvases
            for canvas in [self.dist_canvas, self.corr_canvas,
                         self.feat_canvas, self.dim_canvas]:
                canvas.figure.clear()
                canvas.draw()
                
        except Exception as e:
            self.logger.error(f"Error resetting analyzer: {str(e)}")
