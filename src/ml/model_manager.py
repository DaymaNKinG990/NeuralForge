import torch
import torch.nn as nn
from typing import Dict, List, Optional
import json
from pathlib import Path

class ModelManager:
    def __init__(self):
        self.current_model: Optional[nn.Module] = None
        self.model_config: Dict = {}
        self.training_history: List[Dict] = []
        
    def create_model(self, config: Dict) -> nn.Module:
        """Create a new neural network model based on configuration.
        
        Args:
            config: Configuration dictionary for model layers
        
        Returns:
            nn.Module: Constructed neural network model
        """
        layers = []
        input_size = config['input_size']
        
        for layer_config in config['layers']:
            layer_type = layer_config['type']
            if layer_type == 'linear':
                layers.append(nn.Linear(input_size, layer_config['output_size']))
                input_size = layer_config['output_size']
                if layer_config.get('activation') == 'relu':
                    layers.append(nn.ReLU())
                elif layer_config.get('activation') == 'sigmoid':
                    layers.append(nn.Sigmoid())
                elif layer_config.get('activation') == 'tanh':
                    layers.append(nn.Tanh())
            elif layer_type == 'dropout':
                layers.append(nn.Dropout(layer_config['p']))
                
        self.current_model = nn.Sequential(*layers)
        self.model_config = config
        return self.current_model
    
    def save_model(self, path: str) -> None:
        """Save the current model and its configuration.
        
        Args:
            path: File path to save the model
        
        Raises:
            ValueError: If no model is available to save
        """
        if not self.current_model:
            raise ValueError("No model to save")
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save model state
        torch.save({
            'model_state': self.current_model.state_dict(),
            'config': self.model_config,
            'training_history': self.training_history
        }, path)
        
    def load_model(self, path: str) -> nn.Module:
        """Load a model from file.
        
        Args:
            path: File path to load the model from
        
        Returns:
            nn.Module: Loaded neural network model
        
        Raises:
            FileNotFoundError: If the model file does not exist
        """
        if not Path(path).exists():
            raise FileNotFoundError(f"Model file not found: {path}")
            
        checkpoint = torch.load(path)
        self.model_config = checkpoint['config']
        self.training_history = checkpoint['training_history']
        
        # Recreate the model architecture
        self.current_model = self.create_model(self.model_config)
        # Load the saved state
        self.current_model.load_state_dict(checkpoint['model_state'])
        
        return self.current_model
    
    def train_model(self, 
                   train_data: torch.Tensor,
                   train_labels: torch.Tensor,
                   epochs: int = 10,
                   learning_rate: float = 0.001,
                   batch_size: int = 32) -> List[Dict]:
        """Train the current model.
        
        Args:
            train_data: Training data tensor
            train_labels: Training labels tensor
            epochs: Number of training epochs
            learning_rate: Learning rate for the optimizer
            batch_size: Batch size for training
        
        Returns:
            List[Dict]: Training history with loss at each epoch
        """
        if not self.current_model:
            raise ValueError("No model to train")
            
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.current_model.parameters(), lr=learning_rate)
        
        n_batches = len(train_data) // batch_size
        history = []
        
        for epoch in range(epochs):
            total_loss = 0
            for i in range(n_batches):
                start_idx = i * batch_size
                end_idx = start_idx + batch_size
                
                batch_data = train_data[start_idx:end_idx]
                batch_labels = train_labels[start_idx:end_idx]
                
                optimizer.zero_grad()
                outputs = self.current_model(batch_data)
                loss = criterion(outputs, batch_labels)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                
            avg_loss = total_loss / n_batches
            history.append({
                'epoch': epoch + 1,
                'loss': avg_loss
            })
            
        self.training_history.extend(history)
        return history
    
    def evaluate_model(self, 
                      test_data: torch.Tensor,
                      test_labels: torch.Tensor) -> Dict:
        """Evaluate the current model.
        
        Args:
            test_data: Test data tensor
            test_labels: Test labels tensor
        
        Returns:
            Dict: Evaluation result with loss and predictions
        """
        if not self.current_model:
            raise ValueError("No model to evaluate")
            
        self.current_model.eval()
        with torch.no_grad():
            outputs = self.current_model(test_data)
            loss = nn.MSELoss()(outputs, test_labels)
            
        return {
            'loss': loss.item(),
            'predictions': outputs.numpy()
        }
