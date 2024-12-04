from typing import Optional, Dict, List
import pathlib
from pathlib import Path
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline,
    BitsAndBytesConfig
)
from dotenv import load_dotenv
import openai
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class LLMManager:
    """Manager for handling different types of LLM models (local and API-based)"""
    
    def __init__(self):
        load_dotenv()
        self.local_model = None
        self.local_tokenizer = None
        self.model_name = None
        self.api_key = pathlib.Path('.env').parent / '.env'
        if self.api_key.exists():
            with open(self.api_key, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY'):
                        self.api_key = line.split('=')[1].strip()
                        break
        if self.api_key:
            openai.api_key = self.api_key
            
        # Default configurations
        self.default_configs = {
            'local': {
                'max_length': 2048,
                'temperature': 0.7,
                'top_p': 0.95,
                'quantization': '4bit'
            },
            'api': {
                'max_tokens': 2048,
                'temperature': 0.7,
                'top_p': 0.95,
                'model': 'gpt-3.5-turbo'
            }
        }
        
        self.logger = logging.getLogger(self.__class__.__name__)

    def load_local_model(self, model_name: str, quantization: str = '4bit') -> bool:
        """
        Load a local HuggingFace model with optional quantization.
        
        Args:
            model_name: Name or path of the model
            quantization: Quantization type ('4bit', '8bit', or None)
        
        Returns:
            bool: True if the model is successfully loaded, False otherwise
        """
        self.logger.debug(f"Loading local model: {model_name} with quantization: {quantization}")
        try:
            # Configure quantization
            if quantization == '4bit':
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16
                )
            elif quantization == '8bit':
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True
                )
            else:
                quantization_config = None
                
            # Load model and tokenizer
            self.model_name = model_name
            self.local_tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            self.local_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                device_map="auto",
                trust_remote_code=True
            )
            
            self.logger.info(f"Model {model_name} loaded successfully.")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            return False
            
    def generate_local(self, 
                      prompt: str,
                      max_length: Optional[int] = None,
                      temperature: Optional[float] = None,
                      top_p: Optional[float] = None) -> str:
        """
        Generate text using local model.
        
        Args:
            prompt: Input text
            max_length: Maximum length of generated text
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
        
        Returns:
            str: Generated text
        """
        self.logger.debug(f"Generating text with prompt: {prompt[:30]}...")
        if not self.local_model or not self.local_tokenizer:
            self.logger.error("No local model loaded")
            raise ValueError("No local model loaded")
            
        # Use default values if not specified
        max_length = max_length or self.default_configs['local']['max_length']
        temperature = temperature or self.default_configs['local']['temperature']
        top_p = top_p or self.default_configs['local']['top_p']
        
        try:
            inputs = self.local_tokenizer(prompt, return_tensors="pt").to(self.local_model.device)
            
            outputs = self.local_model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.local_tokenizer.eos_token_id
            )
            generated_text = self.local_tokenizer.decode(outputs[0], skip_special_tokens=True)
            self.logger.info("Text generation successful.")
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return ""
            
    def generate_api(self,
                    prompt: str,
                    model: Optional[str] = None,
                    max_tokens: Optional[int] = None,
                    temperature: Optional[float] = None,
                    top_p: Optional[float] = None) -> str:
        """
        Generate text using OpenAI API.
        
        Args:
            prompt: Input text
            model: Model name (e.g., 'gpt-3.5-turbo')
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
        
        Returns:
            str: Generated text
        """
        self.logger.debug(f"Generating text with prompt: {prompt[:30]}...")
        if not self.api_key:
            self.logger.error("OpenAI API key not found")
            raise ValueError("OpenAI API key not found")
            
        # Use default values if not specified
        model = model or self.default_configs['api']['model']
        max_tokens = max_tokens or self.default_configs['api']['max_tokens']
        temperature = temperature or self.default_configs['api']['temperature']
        top_p = top_p or self.default_configs['api']['top_p']
        
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )
            generated_text = response.choices[0].message.content
            self.logger.info("Text generation successful.")
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {str(e)}")
            return ""
            
    def get_available_local_models(self, cache_dir: Optional[Path] = None) -> List[str]:
        """Get list of downloaded local models.
        
        Args:
            cache_dir: Directory to search for models
        
        Returns:
            List[str]: List of model names
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            
        models = []
        cache_path = cache_dir
        
        if cache_path.exists():
            for model_dir in cache_path.glob("**/models--*"):
                model_name = model_dir.name.replace("models--", "").replace("--", "/")
                models.append(model_name)
                
        return models
        
    def get_model_info(self) -> Dict:
        """Get information about currently loaded model"""
        if not self.local_model:
            return {}
            
        return {
            "name": self.model_name,
            "parameters": sum(p.numel() for p in self.local_model.parameters()),
            "device": self.local_model.device,
            "dtype": str(next(self.local_model.parameters()).dtype),
            "is_quantized": hasattr(self.local_model, "is_quantized") and self.local_model.is_quantized
        }
        
    def unload_model(self) -> None:
        """Unload the current local model to free memory"""
        if self.local_model:
            del self.local_model
            del self.local_tokenizer
            torch.cuda.empty_cache()
            self.local_model = None
            self.local_tokenizer = None
            self.model_name = None
            self.logger.info("Model unloaded successfully.")
