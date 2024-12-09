"""Tests for advanced components."""
import pytest
import torch
import numpy as np
from src.ui.components.visualization.advanced_plots import (
    FeatureVisualization,
    ModelVisualization,
    PerformanceVisualization
)
from src.ui.components.data_processing.advanced_preprocessing import (
    AdvancedPreprocessor,
    TimeSeriesPreprocessor,
    TextPreprocessor,
    ImagePreprocessor
)
from src.ui.components.model.advanced_architectures import (
    TransformerBlock,
    ResidualBlock,
    LSTMWithAttention,
    DenseNet,
    UNet,
    GAN
)
from src.utils.error_handling import (
    ErrorHandler,
    ErrorMonitor,
    DataError,
    ModelError
)

# Fixtures
@pytest.fixture
def advanced_preprocessor():
    return AdvancedPreprocessor()

@pytest.fixture
def sample_data():
    return np.random.randn(100, 10)

@pytest.fixture
def timeseries_processor():
    return TimeSeriesPreprocessor()

@pytest.fixture
def sample_timeseries():
    return np.random.randn(1000, 1)

@pytest.fixture
def error_handler():
    return ErrorHandler()

@pytest.fixture
def error_monitor(error_handler):
    monitor = ErrorMonitor(error_handler)
    return monitor

# Advanced Preprocessing Tests
def test_handle_missing_values(advanced_preprocessor, sample_data):
    """Test missing value imputation."""
    # Create data with missing values
    data = sample_data.copy()
    data[0:10, 0] = np.nan
    
    # Test different imputation strategies
    imputed_mean = advanced_preprocessor.handle_missing_values(data, 'mean')
    imputed_median = advanced_preprocessor.handle_missing_values(data, 'median')
    
    assert not np.any(np.isnan(imputed_mean))
    assert not np.any(np.isnan(imputed_median))
    assert np.allclose(imputed_mean[0:10, 0], np.mean(data[10:, 0]))
    assert np.allclose(imputed_median[0:10, 0], np.median(data[10:, 0]))

def test_feature_scaling(advanced_preprocessor, sample_data):
    """Test feature scaling methods."""
    # Test different scaling methods
    scaled_standard = advanced_preprocessor.scale_features(sample_data, 'standard')
    scaled_minmax = advanced_preprocessor.scale_features(sample_data, 'minmax')
    
    assert np.allclose(scaled_standard.mean(axis=0), 0, atol=1e-7)
    assert np.allclose(scaled_standard.std(axis=0), 1, atol=1e-7)
    assert np.all(scaled_minmax >= 0) and np.all(scaled_minmax <= 1)

# Time Series Processing Tests
def test_create_sequences(timeseries_processor, sample_timeseries):
    """Test sequence creation."""
    seq_length = 10
    sequences = timeseries_processor.create_sequences(sample_timeseries, seq_length)
    
    assert sequences.shape[1] == seq_length
    assert sequences.shape[0] == len(sample_timeseries) - seq_length + 1

def test_handle_seasonality(timeseries_processor, sample_timeseries):
    """Test seasonality handling."""
    period = 24  # e.g., hourly data with daily seasonality
    deseasonalized = timeseries_processor.handle_seasonality(sample_timeseries, period)
    seasonal_component = timeseries_processor.extract_seasonality(sample_timeseries, period)
    
    assert deseasonalized.shape == sample_timeseries.shape
    assert seasonal_component.shape == sample_timeseries.shape

# Advanced Architectures Tests
def test_transformer_block():
    """Test transformer block."""
    batch_size = 32
    seq_length = 10
    d_model = 64
    
    block = TransformerBlock(d_model=d_model, nhead=8)
    x = torch.randn(batch_size, seq_length, d_model)
    output = block(x)
    
    assert output.shape == (batch_size, seq_length, d_model)

def test_residual_block():
    """Test residual block."""
    batch_size = 32
    channels = 64
    
    block = ResidualBlock(in_channels=channels, out_channels=channels)
    x = torch.randn(batch_size, channels, 28, 28)
    output = block(x)
    
    assert output.shape == x.shape

def test_lstm_attention():
    """Test LSTM with attention."""
    batch_size = 32
    seq_length = 10
    input_size = 20
    hidden_size = 64
    
    model = LSTMWithAttention(input_size=input_size, hidden_size=hidden_size)
    x = torch.randn(batch_size, seq_length, input_size)
    output, attention = model(x)
    
    assert output.shape == (batch_size, hidden_size)
    assert attention.shape == (batch_size, seq_length)

def test_unet():
    """Test U-Net architecture."""
    batch_size = 8
    channels = 3
    height = width = 256
    
    model = UNet(in_channels=channels, out_channels=1)
    x = torch.randn(batch_size, channels, height, width)
    output = model(x)
    
    assert output.shape == (batch_size, 1, height, width)

def test_gan():
    """Test GAN architecture."""
    batch_size = 32
    latent_dim = 100
    img_channels = 3
    img_size = 64
    
    gan = GAN(latent_dim=latent_dim, img_channels=img_channels)
    noise = torch.randn(batch_size, latent_dim)
    fake_images = gan.generator(noise)
    disc_output = gan.discriminator(fake_images)
    
    assert fake_images.shape == (batch_size, img_channels, img_size, img_size)
    assert disc_output.shape == (batch_size, 1)

# Error Handling Tests
def test_error_handling(error_handler):
    """Test basic error handling."""
    # Test data error handling
    with pytest.raises(DataError):
        error_handler.handle_error(DataError("Missing values detected"))
    
    # Test model error handling
    with pytest.raises(ModelError):
        error_handler.handle_error(ModelError("Invalid model configuration"))

def test_error_monitoring(error_handler, error_monitor):
    """Test error monitoring and analysis."""
    # Generate some errors
    errors = [
        DataError("Missing values"),
        ModelError("Convergence failure"),
        DataError("Invalid format")
    ]
    
    for error in errors:
        try:
            error_handler.handle_error(error)
        except (DataError, ModelError):
            pass
    
    # Check error statistics
    stats = error_monitor.get_error_stats()
    assert stats["total_errors"] == len(errors)
    assert stats["data_errors"] == 2
    assert stats["model_errors"] == 1
