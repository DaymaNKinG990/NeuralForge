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

# DataPreprocessor Tests
def test_preprocessor_initialization(app):
    """Test preprocessor component initialization."""
    preprocessor = DataPreprocessor()
    assert preprocessor is not None
    assert preprocessor.data is None
    assert preprocessor.labels is None

def test_preprocessor_set_data(app, sample_data):
    """Test setting data in preprocessor."""
    preprocessor = DataPreprocessor()
    data, labels = sample_data
    preprocessor.set_data(data, labels)
    assert preprocessor.data is not None
    assert preprocessor.labels is not None

def test_standard_scaling(app, sample_data):
    """Test standard scaling preprocessing."""
    preprocessor = DataPreprocessor()
    data, labels = sample_data
    preprocessor.set_data(data, labels)
    
    # Set standard scaling
    preprocessor.scaling_combo.setCurrentText("Standard Scaling")
    preprocessor._process_data()
    
    # Check scaled data
    assert preprocessor.processed_data is not None
    X_train, X_test = preprocessor.processed_data
    
    # Check that both train and test data are properly scaled
    # Mean should be close to 0 and std close to 1 for each feature
    # Using unbiased=True to match scikit-learn's behavior
    assert torch.allclose(X_train.mean(dim=0), torch.zeros(X_train.size(1)), atol=1e-6)
    assert torch.allclose(X_train.std(dim=0, unbiased=True), torch.ones(X_train.size(1)), atol=1e-6)
    assert torch.allclose(X_test.mean(dim=0), torch.zeros(X_test.size(1)), atol=1e-6)
    assert torch.allclose(X_test.std(dim=0, unbiased=True), torch.ones(X_test.size(1)), atol=1e-6)

# DataAugmentor Tests
def test_augmentor_initialization(app):
    """Test augmentor component initialization."""
    augmentor = DataAugmentor()
    assert augmentor is not None
    assert augmentor.data is None
    assert augmentor.labels is None

def test_augmentor_set_data(app, sample_data):
    """Test setting data in augmentor."""
    augmentor = DataAugmentor()
    data, labels = sample_data
    augmentor.set_data(data, labels)
    assert augmentor.data is not None
    assert augmentor.labels is not None

def test_noise_augmentation(app, sample_data):
    """Test noise augmentation."""
    augmentor = DataAugmentor()
    data, labels = sample_data
    augmentor.set_data(data, labels)
    
    # Set noise augmentation
    augmentor.augmentation_combo.setCurrentText("Add Noise")
    augmentor.noise_std.setValue(0.1)
    augmentor._augment_data()
    
    # Check augmented data
    assert augmentor.augmented_data is not None
    assert augmentor.augmented_data.shape == data.shape
    assert not torch.allclose(augmentor.augmented_data, data)
