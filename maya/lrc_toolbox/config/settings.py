"""
Settings management for LRC Toolbox

Handles loading, saving, and managing user settings with
support for template management and naming conventions.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from .defaults import DEFAULT_SETTINGS


class Settings:
    """
    Settings manager for LRC Toolbox configuration.
    
    Handles loading and saving user preferences, with fallback
    to default settings when user settings are not available.
    """
    
    def __init__(self, settings_file: Optional[str] = None):
        """
        Initialize settings manager.
        
        Args:
            settings_file: Path to settings file. If None, uses default location.
        """
        self._settings: Dict[str, Any] = DEFAULT_SETTINGS.copy()
        self._settings_file = settings_file or self._get_default_settings_path()
        self._load_settings()
    
    def _get_default_settings_path(self) -> str:
        """
        Get the default settings file path.
        
        Returns:
            Path to the default settings file
        """
        # Use user's home directory for settings
        home_dir = Path.home()
        settings_dir = home_dir / ".lrc_toolbox"
        settings_dir.mkdir(exist_ok=True)
        
        return str(settings_dir / "settings.json")
    
    def _load_settings(self) -> None:
        """Load settings from file, falling back to defaults if needed."""
        try:
            if os.path.exists(self._settings_file):
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                    
                # Merge user settings with defaults
                self._merge_settings(self._settings, user_settings)
                print(f"Settings loaded from: {self._settings_file}")
            else:
                print("No user settings found, using defaults")
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            print("Using default settings")
    
    def _merge_settings(self, defaults: Dict[str, Any], user: Dict[str, Any]) -> None:
        """
        Recursively merge user settings with defaults.
        
        Args:
            defaults: Default settings dictionary
            user: User settings dictionary
        """
        for key, value in user.items():
            if key in defaults:
                if isinstance(defaults[key], dict) and isinstance(value, dict):
                    self._merge_settings(defaults[key], value)
                else:
                    defaults[key] = value
            else:
                defaults[key] = value
    
    def save_settings(self) -> bool:
        """
        Save current settings to file.
        
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._settings_file), exist_ok=True)
            
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            
            print(f"Settings saved to: {self._settings_file}")
            return True
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value using dot notation.
        
        Args:
            key: Setting key (e.g., "project.project_root")
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        keys = key.split('.')
        value = self._settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value using dot notation.
        
        Args:
            key: Setting key (e.g., "project.project_root")
            value: Value to set
        """
        keys = key.split('.')
        settings = self._settings
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        
        # Set the final value
        settings[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all settings.
        
        Returns:
            Complete settings dictionary
        """
        return self._settings.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        self._settings = DEFAULT_SETTINGS.copy()
    
    def get_project_root(self) -> str:
        """Get the project root directory."""
        return self.get("project.project_root", "V:/SWA/all")
    
    def get_template_settings(self) -> Dict[str, Any]:
        """Get template management settings."""
        return self.get("templates", {})
    
    def get_naming_settings(self) -> Dict[str, Any]:
        """Get naming convention settings."""
        return self.get("naming", {})
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """Get UI configuration settings."""
        return self.get("ui", {})


# Global settings instance
settings = Settings()
