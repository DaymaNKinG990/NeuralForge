"""Time series preprocessing components."""
import numpy as np
from typing import Tuple, Optional
from statsmodels.tsa.seasonal import seasonal_decompose

class TimeSeriesPreprocessor:
    """Specialized preprocessor for time series data."""
    
    def __init__(self):
        """Initialize time series preprocessor."""
        pass
    
    def create_sequences(self, data: np.ndarray, seq_length: int) -> np.ndarray:
        """Create sequences for time series prediction."""
        try:
            # Convert input to numpy array if needed
            if isinstance(data, tuple):
                data = np.array(data)
            elif not isinstance(data, np.ndarray):
                data = np.array(data)
            
            # Ensure 2D array
            if len(data.shape) == 1:
                data = data.reshape(-1, 1)
                
            n_samples = len(data) - seq_length + 1
            n_features = data.shape[1]
            
            # Pre-allocate output array
            sequences = np.zeros((n_samples, seq_length, n_features))
            
            # Fill sequences
            for i in range(n_samples):
                sequences[i] = data[i:(i + seq_length)]
            
            return sequences
        except Exception as e:
            raise ValueError(f"Error creating sequences: {str(e)}")
    
    def handle_seasonality(self, data: np.ndarray, period: int) -> np.ndarray:
        """Handle seasonality in time series data."""
        try:
            # Convert input to numpy array if needed
            if isinstance(data, tuple):
                data = np.array(data[0] if len(data) == 1 else data[0])
            elif not isinstance(data, np.ndarray):
                data = np.array(data)
                
            # Ensure 2D array
            if len(data.shape) == 1:
                data = data.reshape(-1, 1)
                
            result = seasonal_decompose(data.squeeze(), period=period, extrapolate_trend='freq')
            return result.resid.reshape(-1, 1)
        except Exception as e:
            raise ValueError(f"Error handling seasonality: {str(e)}")
    
    def extract_seasonality(self, data: np.ndarray, period: int) -> np.ndarray:
        """Extract seasonal component from time series."""
        try:
            # Convert input to numpy array if needed
            if isinstance(data, tuple):
                data = np.array(data[0] if len(data) == 1 else data[0])
            elif not isinstance(data, np.ndarray):
                data = np.array(data)
                
            # Ensure 2D array
            if len(data.shape) == 1:
                data = data.reshape(-1, 1)
                
            result = seasonal_decompose(data.squeeze(), period=period, extrapolate_trend='freq')
            return result.seasonal.reshape(-1, 1)
        except Exception as e:
            raise ValueError(f"Error extracting seasonality: {str(e)}")
    
    def remove_seasonality(self, data: np.ndarray, period: int) -> np.ndarray:
        """Remove seasonality from time series data."""
        return self.handle_seasonality(data, period)
