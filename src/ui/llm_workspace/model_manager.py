"""Model management and history tracking."""
from typing import Dict, List, Optional
from pathlib import Path
import json
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QDoubleSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from ..styles.style_manager import StyleManager
from ..styles.style_enums import StyleClass

logger = logging.getLogger(__name__)

class ModelHistory:
    """Class for tracking model usage history."""
    
    def __init__(self, history_file: Path):
        """Initialize model history.
        
        Args:
            history_file: Path to history JSON file
        """
        self.history_file = history_file
        self.history: List[Dict] = []
        self.load_history()
        
    def load_history(self):
        """Load history from file."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load history: {str(e)}")
            self.history = []
            
    def save_history(self):
        """Save history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {str(e)}")
            
    def add_entry(self, model: str, prompt: str, response: str, 
                 config: Dict, duration: float):
        """Add new history entry.
        
        Args:
            model: Model name
            prompt: Input prompt
            response: Generated response
            config: Model configuration
            duration: Generation duration in seconds
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'prompt': prompt,
            'response': response,
            'config': config,
            'duration': duration
        }
        self.history.append(entry)
        self.save_history()
        
    def get_entries(self, limit: Optional[int] = None) -> List[Dict]:
        """Get history entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of history entries
        """
        entries = sorted(
            self.history,
            key=lambda x: x['timestamp'],
            reverse=True
        )
        return entries[:limit] if limit else entries

class ModelConfigDialog(QDialog):
    """Dialog for editing model configurations."""
    
    def __init__(self, config: Dict, parent=None):
        """Initialize config dialog.
        
        Args:
            config: Initial configuration
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config.copy()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Edit Model Configuration")
        layout = QFormLayout(self)
        
        # Model name
        self.name_edit = QLineEdit(self.config.get('name', ''))
        layout.addRow("Name:", self.name_edit)
        
        # API endpoint
        self.endpoint_edit = QLineEdit(self.config.get('endpoint', ''))
        layout.addRow("API Endpoint:", self.endpoint_edit)
        
        # Max tokens
        self.tokens_spin = QSpinBox()
        self.tokens_spin.setRange(1, 32000)
        self.tokens_spin.setValue(self.config.get('max_tokens', 2048))
        layout.addRow("Max Tokens:", self.tokens_spin)
        
        # Temperature
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(self.config.get('temperature', 0.7))
        layout.addRow("Temperature:", self.temp_spin)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addRow(button_layout)
        
        # Connect signals
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
    def get_config(self) -> Dict:
        """Get edited configuration.
        
        Returns:
            Updated configuration dictionary
        """
        return {
            'name': self.name_edit.text(),
            'endpoint': self.endpoint_edit.text(),
            'max_tokens': self.tokens_spin.value(),
            'temperature': self.temp_spin.value()
        }

class ModelManagerWidget(QWidget):
    """Widget for managing model configurations and history."""
    
    config_updated = pyqtSignal(dict)  # Emits when config is updated
    
    def __init__(self, config_dir: Path, parent=None):
        """Initialize model manager.
        
        Args:
            config_dir: Directory for config and history files
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.config_dir = config_dir
        self.config_file = config_dir / 'model_config.json'
        self.history = ModelHistory(config_dir / 'model_history.json')
        self.configs: Dict[str, Dict] = {}
        self.load_configs()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the manager UI."""
        layout = QVBoxLayout(self)
        
        # Config section
        config_label = QLabel("Model Configurations")
        config_label.setStyleSheet(
            self.style_manager.get_component_style(StyleClass.LABEL)
        )
        layout.addWidget(config_label)
        
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(5)
        self.config_table.setHorizontalHeaderLabels([
            "Name", "Endpoint", "Max Tokens", "Temperature", "Actions"
        ])
        layout.addWidget(self.config_table)
        
        # Config buttons
        config_buttons = QHBoxLayout()
        self.add_config_btn = QPushButton("Add Configuration")
        self.add_config_btn.clicked.connect(self.add_config)
        config_buttons.addWidget(self.add_config_btn)
        layout.addLayout(config_buttons)
        
        # History section
        history_label = QLabel("Generation History")
        history_label.setStyleSheet(
            self.style_manager.get_component_style(StyleClass.LABEL)
        )
        layout.addWidget(history_label)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Timestamp", "Model", "Prompt", "Response", 
            "Duration", "Config"
        ])
        layout.addWidget(self.history_table)
        
        # Refresh tables
        self.refresh_tables()
        
    def load_configs(self):
        """Load model configurations."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.configs = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load configs: {str(e)}")
            self.configs = {}
            
    def save_configs(self):
        """Save model configurations."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.configs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save configs: {str(e)}")
            
    def refresh_tables(self):
        """Refresh configuration and history tables."""
        # Refresh config table
        self.config_table.setRowCount(len(self.configs))
        for row, (name, config) in enumerate(self.configs.items()):
            self.config_table.setItem(row, 0, QTableWidgetItem(name))
            self.config_table.setItem(row, 1, QTableWidgetItem(config['endpoint']))
            self.config_table.setItem(row, 2, QTableWidgetItem(str(config['max_tokens'])))
            self.config_table.setItem(row, 3, QTableWidgetItem(str(config['temperature'])))
            
            # Add action buttons
            actions = QWidget()
            action_layout = QHBoxLayout(actions)
            edit_btn = QPushButton("Edit")
            delete_btn = QPushButton("Delete")
            
            edit_btn.clicked.connect(lambda _, n=name: self.edit_config(n))
            delete_btn.clicked.connect(lambda _, n=name: self.delete_config(n))
            
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            self.config_table.setCellWidget(row, 4, actions)
            
        # Refresh history table
        entries = self.history.get_entries()
        self.history_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.history_table.setItem(row, 0, QTableWidgetItem(entry['timestamp']))
            self.history_table.setItem(row, 1, QTableWidgetItem(entry['model']))
            self.history_table.setItem(row, 2, QTableWidgetItem(entry['prompt'][:50] + '...'))
            self.history_table.setItem(row, 3, QTableWidgetItem(entry['response'][:50] + '...'))
            self.history_table.setItem(row, 4, QTableWidgetItem(f"{entry['duration']:.2f}s"))
            self.history_table.setItem(row, 5, QTableWidgetItem(str(entry['config'])))
            
    def add_config(self):
        """Add new model configuration."""
        config = {
            'name': '',
            'endpoint': '',
            'max_tokens': 2048,
            'temperature': 0.7
        }
        
        dialog = ModelConfigDialog(config, self)
        if dialog.exec():
            new_config = dialog.get_config()
            name = new_config.pop('name')
            if name in self.configs:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Configuration '{name}' already exists"
                )
                return
                
            self.configs[name] = new_config
            self.save_configs()
            self.refresh_tables()
            self.config_updated.emit({name: new_config})
            
    def edit_config(self, name: str):
        """Edit existing model configuration.
        
        Args:
            name: Configuration name
        """
        if name not in self.configs:
            return
            
        config = self.configs[name].copy()
        config['name'] = name
        
        dialog = ModelConfigDialog(config, self)
        if dialog.exec():
            new_config = dialog.get_config()
            new_name = new_config.pop('name')
            
            if new_name != name and new_name in self.configs:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Configuration '{new_name}' already exists"
                )
                return
                
            if new_name != name:
                del self.configs[name]
                
            self.configs[new_name] = new_config
            self.save_configs()
            self.refresh_tables()
            self.config_updated.emit({new_name: new_config})
            
    def delete_config(self, name: str):
        """Delete model configuration.
        
        Args:
            name: Configuration name
        """
        if name not in self.configs:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete configuration '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.configs[name]
            self.save_configs()
            self.refresh_tables()
            self.config_updated.emit({})
            
    def add_history_entry(self, model: str, prompt: str, response: str,
                         config: Dict, duration: float):
        """Add new history entry.
        
        Args:
            model: Model name
            prompt: Input prompt
            response: Generated response
            config: Model configuration
            duration: Generation duration in seconds
        """
        self.history.add_entry(model, prompt, response, config, duration)
        self.refresh_tables()
