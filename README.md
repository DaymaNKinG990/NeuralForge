# NeuralForge IDE

Modern, Python-based Integrated Development Environment for Neural Network and Machine Learning Development.

## Features
- 🧠 AI-powered code completion and suggestions
- 🔧 Integrated Neural Network development tools
- 📝 Advanced code editor with Python syntax highlighting
- 🎨 Modern PyQt6-based user interface with customizable themes
- 🚀 Built-in Python console and debugging tools
- 📊 Neural network visualization tools
- 🔄 Support for popular ML frameworks (PyTorch, TensorFlow)
- 🎯 Advanced hyperparameter optimization
- 📈 Comprehensive experiment tracking
- 🔍 Model interpretation and analysis
- 🎨 Advanced visualization capabilities
- 🚄 GPU acceleration support
- 📦 Multiple model architectures
- ⚡ Asynchronous task execution with progress tracking
- 🔄 Git integration for version control
- 🔍 Git integration for version control
- ⚡ Asynchronous task execution with progress tracking
- 🎯 Advanced memory and performance optimization

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/neuroforge.git
cd neuroforge

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Requirements
- Python 3.8+
- PyQt6
- PyTorch/TensorFlow (optional, for ML features)
- Git (for version control features)
- Other dependencies listed in requirements.txt

## Project Structure
```
neuroforge/
├── src/                    # Source code
│   ├── ui/                # User interface components
│   │   ├── dialogs/      # Dialog windows
│   │   ├── resources/    # Icons and resources
│   │   ├── styles/       # UI themes and styles
│   │   ├── main_window.py
│   │   ├── code_editor.py
│   │   └── settings_dialog.py
│   ├── ml/               # Machine learning components
│   │   └── llm_manager.py
│   └── utils/            # Utility functions
│       ├── performance.py    # Performance optimization
│       ├── git_manager.py    # Git integration
│       ├── distributed_cache.py
│       └── preloader.py
├── tests/                # Test suite
│   ├── test_async_worker.py
│   ├── test_code_editor.py
│   └── test_git_manager.py
├── main.py              # Application entry point
├── requirements.txt     # Project dependencies
├── pytest.ini          # Test configuration
└── README.md
```

## Core Components

### AsyncWorker
The `AsyncWorker` class provides a robust framework for executing tasks asynchronously:

```python
from src.utils.performance import AsyncWorker

# Create a worker
def long_running_task(progress_callback=None):
    # Do work...
    if progress_callback:
        progress_callback(50)  # Report 50% progress
    return "result"

worker = AsyncWorker(long_running_task)

# Connect signals
worker.started.connect(on_started)
worker.finished.connect(on_finished)
worker.error.connect(on_error)
worker.progress.connect(on_progress)

# Start the worker
worker.start()
```

### Code Editor
Advanced code editing with syntax highlighting and AI suggestions:

```python
from src.ui.code_editor import CodeEditor

editor = CodeEditor()
editor.set_language("python")
editor.set_theme("dark")
editor.enable_ai_completion(True)
```

### Git Integration
Built-in Git support for version control:

```python
from src.utils.git_manager import GitManager

git = GitManager()
git.init_repo()
git.add_files(["main.py"])
git.commit("Initial commit")
git.push_to_remote("origin", "main")
```

### Model Training and Optimization
The `ModelTrainer` class provides an integrated solution for model training and hyperparameter optimization:

```python
from src.ui.components.ml.model_trainer import ModelTrainer

# Initialize trainer
trainer = ModelTrainer()

# Set data and model
trainer.set_data(train_loader, val_loader)
trainer.set_model_type("Transformer")

# Start training with hyperparameter optimization
trainer.train(n_trials=50)
```

### Advanced Hyperparameter Tuning
The `AdvancedHyperparameterTuner` supports multiple optimization methods:

```python
from src.ui.components.ml.advanced_hyperparameter_tuner import AdvancedHyperparameterTuner

# Initialize tuner
tuner = AdvancedHyperparameterTuner()

# Configure parameter ranges
tuner.set_parameter_ranges(
    learning_rate=(0.0001, 0.01),
    batch_size=(16, 256),
    dropout_rate=(0.1, 0.5)
)

# Start optimization
best_params = tuner.optimize(n_trials=50)
```

### Experiment Tracking
The `AdvancedExperimentTracker` provides comprehensive experiment management:

```python
from src.ui.components.ml.advanced_experiment_tracker import AdvancedExperimentTracker

# Initialize tracker
tracker = AdvancedExperimentTracker()

# Log experiment
tracker.add_experiment({
    'name': 'experiment_1',
    'parameters': params,
    'metrics': metrics,
    'tags': ['transformer', 'production']
})

# Get best experiment
best_exp = tracker.get_experiment_by_metric('val_accuracy', best='max')
```

### Model Architectures
Multiple pre-built architectures available:

```python
from src.ui.components.model.advanced_architectures import (
    TransformerBlock, ResidualBlock, LSTMWithAttention,
    DenseNet, UNet, GAN
)

# Create transformer model
transformer = TransformerBlock(
    embed_dim=512,
    num_heads=8,
    ff_dim=2048,
    dropout=0.1
)

# Create U-Net for image segmentation
unet = UNet(
    in_channels=3,
    out_channels=1,
    features=[64, 128, 256, 512]
)
```

### Model Interpretation
The `AdvancedModelInterpreter` provides multiple interpretation methods:

```python
from src.ui.components.ml.advanced_model_interpreter import AdvancedModelInterpreter

# Initialize interpreter
interpreter = AdvancedModelInterpreter(model)

# Get feature attributions
attributions = interpreter.compute_feature_importance(
    input_data,
    method='integrated_gradients'
)

# Visualize layer activations
interpreter.visualize_layer_activations(input_data)
```

## Development Guide

### Setting Up Development Environment
1. Clone the repository
2. Create a virtual environment
3. Install development dependencies:
```bash
pip install -r requirements.txt
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_async_worker.py

# Run with coverage
pytest --cov=src tests/
```

### Code Style
We follow PEP 8 guidelines with these additions:
- Maximum line length: 100 characters
- Use type hints for function parameters
- Document all public functions and classes

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Building Documentation
```bash
# Install documentation dependencies
pip install sphinx sphinx-rtd-theme

# Build documentation
cd docs
make html
```

## Performance Optimization

### Memory Management
- Use `distributed_cache.py` for efficient caching
- Implement lazy loading with `preloader.py`
- Monitor memory usage with built-in profiler

### Threading
- Use `AsyncWorker` for long-running tasks
- Implement progress reporting
- Handle thread cleanup properly

## Troubleshooting

### Common Issues
1. PyQt6 Installation Errors
   - Solution: Install Qt dependencies first
   
2. Git Integration Issues
   - Solution: Verify Git installation and credentials

3. Performance Issues
   - Solution: Check AsyncWorker usage and memory profiler

## License
MIT License - see LICENSE file for details

## Support
- GitHub Issues: Report bugs and request features
- Documentation: [Link to docs]
- Community: [Link to community]
