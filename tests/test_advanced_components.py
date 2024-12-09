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

class TestAdvancedPreprocessing:
    """Test advanced preprocessing components."""
    
    @pytest.fixture
    def preprocessor(self):
        return AdvancedPreprocessor()
        
    @pytest.fixture
    def sample_data(self):
        return np.random.randn(100, 10)
        
    def test_handle_missing_values(self, preprocessor, sample_data):
        """Test missing value imputation."""
        # Create data with missing values
        data = sample_data.copy()
        data[0:10, 0] = np.nan
        
        # Test different imputation strategies
        imputed_mean = preprocessor.handle_missing_values(data, 'mean')
        imputed_median = preprocessor.handle_missing_values(data, 'median')
        
        assert not np.isnan(imputed_mean).any()
        assert not np.isnan(imputed_median).any()
        
    def test_scale_features(self, preprocessor, sample_data):
        """Test feature scaling."""
        # Test different scaling methods
        scaled_standard = preprocessor.scale_features(sample_data, 'standard')
        scaled_minmax = preprocessor.scale_features(sample_data, 'minmax')
        
        assert np.abs(scaled_standard.mean()) < 1e-10
        assert scaled_minmax.min() >= 0 and scaled_minmax.max() <= 1
        
    def test_select_features(self, preprocessor, sample_data):
        """Test feature selection."""
        labels = np.random.randint(0, 2, size=100)
        selected = preprocessor.select_features(sample_data, labels,
                                             method='kbest',
                                             k=5)
        assert selected.shape[1] == 5

class TestTimeSeriesProcessing:
    """Test time series processing components."""
    
    @pytest.fixture
    def processor(self):
        return TimeSeriesPreprocessor()
        
    @pytest.fixture
    def sample_timeseries(self):
        return np.sin(np.linspace(0, 10, 100))
        
    def test_create_sequences(self, processor, sample_timeseries):
        """Test sequence creation."""
        seq_len = 10
        target_size = 1
        X, y = processor.create_sequences(sample_timeseries,
                                        seq_len,
                                        target_size)
        
        assert len(X) == len(y)
        assert X.shape[1] == seq_len
        assert y.shape[1] == target_size
        
    def test_handle_seasonality(self, processor, sample_timeseries):
        """Test seasonality handling."""
        period = 10
        diff = processor.handle_seasonality(sample_timeseries,
                                          period,
                                          method='difference')
        ratio = processor.handle_seasonality(sample_timeseries,
                                           period,
                                           method='ratio')
                                           
        assert len(diff) == len(sample_timeseries) - period
        assert len(ratio) == len(sample_timeseries) - period

class TestAdvancedArchitectures:
    """Test advanced model architectures."""
    
    def test_transformer_block(self):
        """Test transformer block."""
        block = TransformerBlock(embed_dim=64,
                               num_heads=4,
                               ff_dim=128)
        x = torch.randn(10, 32, 64)  # (seq_len, batch_size, embed_dim)
        out = block(x)
        assert out.shape == x.shape
        
    def test_residual_block(self):
        """Test residual block."""
        block = ResidualBlock(in_channels=64,
                            out_channels=128,
                            stride=2)
        x = torch.randn(1, 64, 32, 32)
        out = block(x)
        assert out.shape == (1, 128, 16, 16)
        
    def test_lstm_attention(self):
        """Test LSTM with attention."""
        model = LSTMWithAttention(input_size=10,
                                hidden_size=20,
                                num_layers=2)
        x = torch.randn(32, 15, 10)  # (batch_size, seq_len, input_size)
        out, (h_n, c_n) = model(x)
        assert out.shape == (32, 20)
        assert h_n.shape == (2, 32, 20)
        
    def test_unet(self):
        """Test U-Net architecture."""
        model = UNet(in_channels=3, out_channels=1)
        x = torch.randn(1, 3, 256, 256)
        out = model(x)
        assert out.shape == (1, 1, 256, 256)
        
    def test_gan(self):
        """Test GAN architecture."""
        model = GAN(latent_dim=100, channels=3)
        z = torch.randn(32, 100, 1, 1)
        x_fake = model.generate(z)
        d_out = model.discriminate(x_fake)
        assert x_fake.shape == (32, 3, 32, 32)
        assert d_out.shape == (32, 1, 1, 1)

class TestErrorHandling:
    """Test error handling system."""
    
    @pytest.fixture
    def error_handler(self):
        return ErrorHandler()
        
    @pytest.fixture
    def error_monitor(self, error_handler):
        return ErrorMonitor(error_handler)
        
    def test_error_handling(self, error_handler):
        """Test basic error handling."""
        try:
            raise DataError("Test error", "TEST_001")
        except Exception as e:
            error_handler.handle_error(e)
            
        assert len(error_handler.error_history) == 1
        assert error_handler.error_history[0]['type'] == 'DataError'
        
    def test_error_monitoring(self, error_handler, error_monitor):
        """Test error monitoring and analysis."""
        # Generate some errors
        for _ in range(3):
            try:
                raise DataError("Data error", "DATA_001")
            except Exception as e:
                error_handler.handle_error(e)
                
        for _ in range(2):
            try:
                raise ModelError("Model error", "MODEL_001")
            except Exception as e:
                error_handler.handle_error(e)
                
        analysis = error_monitor.analyze_errors()
        assert analysis['total_errors'] == 5
        assert analysis['error_counts']['DataError'] == 3
        assert analysis['error_counts']['ModelError'] == 2
