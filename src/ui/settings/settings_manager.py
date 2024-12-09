"""Settings manager for application configuration."""
from typing import Any, Dict, Optional
from pathlib import Path
import json
import logging
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class SettingsManager(QObject):
    """Manager for application settings."""
    
    settings_changed = pyqtSignal(str, object)  # section, value
    
    def __init__(self, settings_dir: Path):
        """Initialize settings manager.
        
        Args:
            settings_dir: Directory for settings files
        """
        super().__init__()
        self.settings_dir = settings_dir
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        self.settings: Dict[str, Dict] = {}
        self.load_settings()
        
    def load_settings(self):
        """Load all settings files."""
        try:
            # Load each JSON file in settings directory
            for file in self.settings_dir.glob('*.json'):
                section = file.stem
                with open(file, 'r') as f:
                    self.settings[section] = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load settings: {str(e)}")
            self.settings = {}
            
    def save_settings(self, section: Optional[str] = None):
        """Save settings to files.
        
        Args:
            section: Specific section to save, or all if None
        """
        try:
            if section:
                # Save specific section
                if section in self.settings:
                    file = self.settings_dir / f"{section}.json"
                    with open(file, 'w') as f:
                        json.dump(self.settings[section], f, indent=2)
            else:
                # Save all sections
                for section, data in self.settings.items():
                    file = self.settings_dir / f"{section}.json"
                    with open(file, 'w') as f:
                        json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save settings: {str(e)}")
            
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get setting value.
        
        Args:
            section: Settings section
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        try:
            return self.settings.get(section, {}).get(key, default)
        except Exception:
            return default
            
    def set(self, section: str, key: str, value: Any):
        """Set setting value.
        
        Args:
            section: Settings section
            key: Setting key
            value: Setting value
        """
        if section not in self.settings:
            self.settings[section] = {}
            
        self.settings[section][key] = value
        self.save_settings(section)
        self.settings_changed.emit(f"{section}.{key}", value)
        
    def get_section(self, section: str) -> Dict:
        """Get entire settings section.
        
        Args:
            section: Settings section
            
        Returns:
            Section settings dictionary
        """
        return self.settings.get(section, {})
        
    def set_section(self, section: str, data: Dict):
        """Set entire settings section.
        
        Args:
            section: Settings section
            data: Section data
        """
        self.settings[section] = data
        self.save_settings(section)
        self.settings_changed.emit(section, data)
        
    def delete(self, section: str, key: str):
        """Delete setting.
        
        Args:
            section: Settings section
            key: Setting key
        """
        if section in self.settings and key in self.settings[section]:
            del self.settings[section][key]
            self.save_settings(section)
            self.settings_changed.emit(f"{section}.{key}", None)
            
    def clear_section(self, section: str):
        """Clear entire settings section.
        
        Args:
            section: Settings section
        """
        if section in self.settings:
            del self.settings[section]
            file = self.settings_dir / f"{section}.json"
            if file.exists():
                file.unlink()
            self.settings_changed.emit(section, None)
