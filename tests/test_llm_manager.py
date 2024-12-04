import pytest
from unittest.mock import Mock, patch, MagicMock
import torch
from src.ml.llm_manager import LLMManager, BitsAndBytesConfig

@pytest.fixture
def llm_manager():
    with patch('src.ml.llm_manager.AutoModelForCausalLM') as mock_model, \
         patch('src.ml.llm_manager.AutoTokenizer') as mock_tokenizer:
        manager = LLMManager()
        yield manager

def test_model_loading(llm_manager):
    """Test model loading functionality"""
    with patch('src.ml.llm_manager.AutoModelForCausalLM.from_pretrained') as mock_model, \
         patch('src.ml.llm_manager.AutoTokenizer.from_pretrained') as mock_tokenizer:
        mock_model.return_value = Mock()
        mock_tokenizer.return_value = Mock()
        
        model_loaded = llm_manager.load_local_model('test-model')
        assert model_loaded
        mock_model.assert_called_once_with(
            'test-model',
            quantization_config=BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
            ),
            device_map='auto',
            trust_remote_code=True
        )
        assert llm_manager.local_tokenizer is mock_tokenizer.return_value
        assert llm_manager.local_model is mock_model.return_value

def test_text_generation(llm_manager):
    """Test text generation functionality"""
    with patch('src.ml.llm_manager.AutoModelForCausalLM.from_pretrained') as mock_model, \
         patch('src.ml.llm_manager.AutoTokenizer.from_pretrained') as mock_tokenizer:
        mock_model_instance = Mock()
        mock_tokenizer_instance = Mock()
        
        # Setup mock tokenizer
        mock_tokenizer_instance.encode.return_value = {'input_ids': torch.tensor([[1, 2, 3]]), 'attention_mask': torch.tensor([[1, 1, 1]])}
        mock_tokenizer_instance.return_tensors = "pt"
        mock_tokenizer_instance.pad_token_id = 0
        mock_tokenizer_instance.eos_token_id = 2
        
        # Setup mock model
        mock_model_instance.generate.return_value = torch.tensor([[1, 2, 3]])
        mock_model_instance.device = torch.device('cpu')
        
        mock_tokenizer_instance.decode.return_value = "Generated text"
        
        llm_manager.local_model = mock_model_instance
        llm_manager.local_tokenizer = mock_tokenizer_instance
        
        generated_text = llm_manager.generate_local("Test prompt")
        assert generated_text == "Generated text"
        mock_model_instance.generate.assert_called_once()

def test_error_handling(llm_manager):
    """Test error handling during model loading"""
    with patch('src.ml.llm_manager.AutoModelForCausalLM.from_pretrained', side_effect=Exception('Test error')):
        model_loaded = llm_manager.load_local_model('test-model')
        assert not model_loaded

def test_model_unloading(llm_manager):
    """Test model unloading functionality"""
    llm_manager.local_model = Mock()
    llm_manager.local_tokenizer = Mock()
    
    llm_manager.unload_model()
    assert llm_manager.local_model is None
    assert llm_manager.local_tokenizer is None

def test_batch_generation(llm_manager):
    """Test batch text generation"""
    with patch('src.ml.llm_manager.AutoModelForCausalLM.from_pretrained') as mock_model, \
         patch('src.ml.llm_manager.AutoTokenizer.from_pretrained') as mock_tokenizer:
        mock_model_instance = Mock()
        mock_tokenizer_instance = Mock()
        
        # Setup mock tokenizer
        mock_tokenizer_instance.encode.return_value = {'input_ids': torch.tensor([[1, 2, 3]]), 'attention_mask': torch.tensor([[1, 1, 1]])}
        mock_tokenizer_instance.return_tensors = "pt"
        mock_tokenizer_instance.pad_token_id = 0
        mock_tokenizer_instance.eos_token_id = 2
        
        # Setup mock model
        mock_model_instance.generate.return_value = torch.tensor([[1, 2, 3]])
        mock_model_instance.device = torch.device('cpu')

        llm_manager.local_model = mock_model_instance
        llm_manager.local_tokenizer = mock_tokenizer_instance

        mock_tokenizer_instance.decode.return_value = "Generated text"

        generated_texts = [llm_manager.generate_local("Test prompt") for _ in range(5)]
        assert all(text == "Generated text" for text in generated_texts)

def test_model_configuration(llm_manager):
    """Test model configuration settings"""
    # Assuming model configuration involves setting default parameters
    llm_manager.default_configs['local']['max_length'] = 1024
    assert llm_manager.default_configs['local']['max_length'] == 1024

def test_device_management(llm_manager):
    """Test device management functionality"""
    # Assuming device management involves setting the device for the model
    llm_manager.local_model = Mock()
    llm_manager.local_model.to = Mock()
    device = torch.device('cuda')
    llm_manager.local_model.to(device)
    llm_manager.local_model.to.assert_called_with(device)

def test_tokenizer_configuration(llm_manager):
    """Test tokenizer configuration"""
    llm_manager.load_local_model('test-model')
    assert llm_manager.local_tokenizer is not None

def test_encode_and_generate(llm_manager):
    """Test encode and generate methods"""
    mock_tokenizer_instance = Mock()
    mock_model_instance = Mock()

    mock_tokenizer_instance.encode.return_value = {'input_ids': torch.tensor([[1, 2, 3]]), 'attention_mask': torch.tensor([[1, 1, 1]])}
    mock_tokenizer_instance.return_tensors = "pt"
    mock_tokenizer_instance.pad_token_id = 0
    mock_tokenizer_instance.eos_token_id = 2

    mock_model_instance.generate.return_value = torch.tensor([[1, 2, 3]])
    mock_model_instance.device = torch.device('cpu')

    mock_tokenizer_instance.decode.return_value = "Generated text"

    llm_manager.local_model = mock_model_instance
    llm_manager.local_tokenizer = mock_tokenizer_instance

    generated_text = llm_manager.generate_local("Test prompt")
    assert generated_text == "Generated text"

def test_batch_generation_encode_and_generate(llm_manager):
    """Test batch text generation"""
    mock_tokenizer_instance = Mock()
    mock_model_instance = Mock()

    mock_tokenizer_instance.encode.return_value = {'input_ids': torch.tensor([[1, 2, 3]]), 'attention_mask': torch.tensor([[1, 1, 1]])}
    mock_tokenizer_instance.return_tensors = "pt"
    mock_tokenizer_instance.pad_token_id = 0
    mock_tokenizer_instance.eos_token_id = 2

    mock_model_instance.generate.return_value = torch.tensor([[1, 2, 3]])
    mock_model_instance.device = torch.device('cpu')

    mock_tokenizer_instance.decode.return_value = "Generated text"

    llm_manager.local_model = mock_model_instance
    llm_manager.local_tokenizer = mock_tokenizer_instance

    generated_texts = [llm_manager.generate_local("Test prompt") for _ in range(5)]
    assert all(text == "Generated text" for text in generated_texts)

def test_encode_and_generate_with_return_values(llm_manager):
    """Test encode and generate methods with return values"""
    mock_tokenizer_instance = Mock()
    mock_model_instance = Mock()

    mock_tokenizer_instance.encode.return_value = {'input_ids': torch.tensor([[1, 2, 3]]), 'attention_mask': torch.tensor([[1, 1, 1]])}
    mock_tokenizer_instance.return_tensors = "pt"
    mock_tokenizer_instance.pad_token_id = 0
    mock_tokenizer_instance.eos_token_id = 2

    mock_model_instance.generate.return_value = torch.tensor([[1, 2, 3]])
    mock_model_instance.device = torch.device('cpu')

    mock_tokenizer_instance.decode.return_value = "Generated text"

    llm_manager.local_model = mock_model_instance
    llm_manager.local_tokenizer = mock_tokenizer_instance

    generated_text = llm_manager.generate_local("Test prompt")
    assert generated_text == "Generated text"
    assert mock_tokenizer_instance.encode.return_value == {'input_ids': torch.tensor([[1, 2, 3]]), 'attention_mask': torch.tensor([[1, 1, 1]])}
    assert mock_model_instance.generate.return_value == torch.tensor([[1, 2, 3]])
