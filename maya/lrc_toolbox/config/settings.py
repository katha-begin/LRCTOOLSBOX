"""
Settings management for LRC Toolbox

Handles loading, saving, and managing user settings with
support for template management and naming conventions.
"""

import json
import os
from typing import Dict, Any, Optional, List
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

    def get_persistence_settings(self) -> Dict[str, Any]:
        """Get persistence configuration settings."""
        return self.get("persistence", {})

    def get_session_settings(self) -> Dict[str, Any]:
        """Get session management settings."""
        return self.get("session", {})

    def save_navigation_context(self, context: Dict[str, Any]) -> None:
        """Save navigation context to settings."""
        try:
            # Get current contexts and add new one
            contexts = self.get("persistence.navigation_context.recent_contexts", [])

            # Remove duplicate if exists
            contexts = [c for c in contexts if c.get("display_name") != context.get("display_name")]

            # Add new context at the beginning
            contexts.insert(0, context)

            # Limit history
            limit = self.get("persistence.navigation_context.context_history_limit", 10)
            contexts = contexts[:limit]

            # Save back to settings
            self.set("persistence.navigation_context.recent_contexts", contexts)
            self.set("persistence.navigation_context.last_context", context)

            # Auto-save if enabled
            if self.get("session.save_on_context_change", True):
                self.save_settings()

            print(f"📍 Navigation context saved: {context.get('display_name', 'Unknown')}")

        except Exception as e:
            print(f"⚠️ Error saving navigation context: {e}")

    def get_last_navigation_context(self) -> Optional[Dict[str, Any]]:
        """Get the last used navigation context."""
        return self.get("persistence.navigation_context.last_context")

    def get_navigation_context_history(self) -> List[Dict[str, Any]]:
        """Get navigation context history."""
        return self.get("persistence.navigation_context.recent_contexts", [])

    def add_recent_project(self, project_root: str, project_name: str = None) -> None:
        """Add a project to recent projects list."""
        try:
            recent_projects = self.get("persistence.project_memory.recent_projects", [])

            # Create project entry
            project_entry = {
                "root": project_root,
                "name": project_name or os.path.basename(project_root),
                "last_accessed": self._get_current_timestamp()
            }

            # Remove duplicate if exists
            recent_projects = [p for p in recent_projects if p.get("root") != project_root]

            # Add new project at the beginning
            recent_projects.insert(0, project_entry)

            # Limit recent projects
            limit = self.get("persistence.project_memory.max_recent_projects", 5)
            recent_projects = recent_projects[:limit]

            # Save back to settings
            self.set("persistence.project_memory.recent_projects", recent_projects)
            self.set("persistence.project_memory.last_project_root", project_root)

            # Auto-save
            self.save_settings()
            print(f"📁 Recent project added: {project_name or project_root}")

        except Exception as e:
            print(f"⚠️ Error adding recent project: {e}")

    def get_recent_projects(self) -> List[Dict[str, Any]]:
        """Get list of recent projects."""
        return self.get("persistence.project_memory.recent_projects", [])

    def get_last_project_root(self) -> str:
        """Get the last used project root."""
        return self.get("persistence.project_memory.last_project_root",
                       self.get("project.project_root", "V:/SWA/all"))

    def save_widget_state(self, widget_name: str, state: Dict[str, Any]) -> None:
        """Save widget state to settings."""
        try:
            self.set(f"persistence.widget_states.{widget_name}", state)
            print(f"💾 Widget state saved: {widget_name}")
        except Exception as e:
            print(f"⚠️ Error saving widget state for {widget_name}: {e}")

    def get_widget_state(self, widget_name: str) -> Dict[str, Any]:
        """Get widget state from settings."""
        return self.get(f"persistence.widget_states.{widget_name}", {})

    def save_file_operation_directory(self, operation_type: str, directory: str) -> None:
        """Save last directory for file operations."""
        try:
            self.set(f"persistence.file_operations.last_{operation_type}_directory", directory)
            print(f"📁 Last {operation_type} directory saved: {directory}")
        except Exception as e:
            print(f"⚠️ Error saving {operation_type} directory: {e}")

    def get_file_operation_directory(self, operation_type: str) -> str:
        """Get last directory for file operations."""
        return self.get(f"persistence.file_operations.last_{operation_type}_directory", "")

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.now().isoformat()

    def clear_navigation_history(self) -> None:
        """Clear navigation context history."""
        self.set("persistence.navigation_context.recent_contexts", [])
        self.set("persistence.navigation_context.last_context", None)
        self.save_settings()
        print("🗑️ Navigation history cleared")

    def clear_recent_projects(self) -> None:
        """Clear recent projects list."""
        self.set("persistence.project_memory.recent_projects", [])
        self.save_settings()
        print("🗑️ Recent projects cleared")


# Global settings instance
settings = Settings()
