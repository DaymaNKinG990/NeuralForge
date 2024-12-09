"""Tests for data processing components."""
import pytest
from PyQt6.QtWidgets import QApplication
import sys
import torch
import numpy as np
from src.ui.components.data_processing.data_preprocessor import DataPreprocessor
from src.ui.components.data_processing.data_augmentor import DataAugmentor

@pytest.fixture
def app():
    """Create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = torch.randn(100, 10)
    labels = torch.randint(0, 2, (100,))
    return data, labels

class TestDataPreprocessor:
    """Test DataPreprocessor component."""
    
    def test_initialization(self, app):
        """Test component initialization."""
        preprocessor = DataPreprocessor()
        assert preprocessor is not None
        assert preprocessor.data is None
        assert preprocessor.labels is None
        
    def test_set_data(self, app, sample_data):
        """Test setting data."""
        preprocessor = DataPreprocessor()
        data, labels = sample_data
        preprocessor.set_data(data, labels)
        assert preprocessor.data is not None
        assert preprocessor.labels is not None
        
    def test_standard_scaling(self, app, sample_data):
        """Test standard scaling preprocessing."""
        preprocessor = DataPreprocessor()
        data, labels = sample_data
        preprocessor.set_data(data, labels)
        
        # Set standard scaling
        preprocessor.scaling_combo.setCurrentText("Standard Scaling")
        preprocessor._process_data()
        
        # Check if data is scaled
        processed_data = preprocessor.scaler.transform(data)
        assert np.allclose(processed_data.mean(axis=0), 0, atol=1e-7)
        assert np.allclose(processed_data.std(axis=0), 1, atol=1e-7)
        
class TestDataAugmentor:
    """Test DataAugmentor component."""
    
    def test_initialization(self, app):
        """Test component initialization."""
        augmentor = DataAugmentor()
        assert augmentor is not None
        assert augmentor.data is None
        assert augmentor.labels is None
        
    def test_set_data(self, app, sample_data):
        """Test setting data."""
        augmentor = DataAugmentor()
        data, labels = sample_data
        augmentor.set_data(data, labels)
        assert augmentor.data is not None
        assert augmentor.labels is not None
        
    def test_noise_augmentation(self, app, sample_data):
        """Test noise augmentation."""
        augmentor = DataAugmentor()
        data, labels = sample_data
        augmentor.set_data(data, labels)
        
        # Enable noise augmentation
        augmentor.noise_check.setChecked(True)
        augmentor.noise_strength.setValue(0.1)
        
        # Perform augmentation
        original_data = data.clone()
        augmented_data = augmentor._add_noise(data)
        
        # Check if noise was added
        assert torch.any(torch.ne(augmented_data, original_data))
        assert torch.allclose(augmented_data, original_data, atol=0.2)  # Noise within bounds
