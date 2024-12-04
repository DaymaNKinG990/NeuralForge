import pytest
from unittest.mock import Mock, patch
from src.ml.model_manager import ModelManager
import torch.nn as nn
import torch

@pytest.fixture
def model_manager():
    with patch('src.ml.model_manager.torch') as mock_torch:
        manager = ModelManager()
        yield manager

def test_model_loading(model_manager):
    with patch('src.ml.model_manager.Path.exists', return_value=True):
        with patch('src.ml.model_manager.torch.load') as mock_load:
            mock_load.return_value = {
                'config': {
                    'input_size': 10,
                    'layers': [
                        {'type': 'linear', 'output_size': 20, 'activation': 'relu'},
                        {'type': 'dropout', 'p': 0.5},
                        {'type': 'linear', 'output_size': 10, 'activation': 'sigmoid'}
                    ]
                },
                'training_history': Mock(),
                'model_state': {
                    '0.weight': torch.rand(20, 10),
                    '0.bias': torch.rand(20),
                    '3.weight': torch.rand(10, 20),
                    '3.bias': torch.rand(10)
                }
            }
            
            model = model_manager.load_model('test_model.pth')
            assert model is not None
            mock_load.assert_called_once_with('test_model.pth')

def test_model_saving(model_manager):
    with patch('src.ml.model_manager.torch') as mock_torch:
        model_manager.current_model = Mock()
        model_manager.save_model('test_model.pth')
        mock_torch.save.assert_called_once()

def test_create_model(model_manager):
    config = {
        'input_size': 10,
        'layers': [
            {'type': 'linear', 'output_size': 20, 'activation': 'relu'},
            {'type': 'dropout', 'p': 0.5},
            {'type': 'linear', 'output_size': 10, 'activation': 'sigmoid'}
        ]
    }
    model = model_manager.create_model(config)
    assert isinstance(model, nn.Sequential)
    assert len(model) == 5  # Linear, ReLU, Dropout, Linear, Sigmoid
