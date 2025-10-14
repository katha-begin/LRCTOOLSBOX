"""
Session Manager for LRC Toolbox

Handles session state persistence, auto-saving, and crash recovery.
"""

import json
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

try:
    from PySide2 import QtCore
except ImportError:
    try:
        from PySide6 import QtCore
    except ImportError:
        QtCore = None

from .settings import settings


class SessionManager(QtCore.QObject if QtCore else object):
    """
    Session manager for handling application state persistence.

    Provides auto-saving, crash recovery, and session state management.
    """

    # Signals (only if Qt is available)
    if QtCore:
        session_saved = QtCore.Signal(str)  # Emitted when session is saved
        session_restored = QtCore.Signal(dict)  # Emitted when session is restored
        auto_save_triggered = QtCore.Signal()  # Emitted when auto-save triggers

    def __init__(self, parent: Optional[QtCore.QObject] = None):
        """
        Initialize session manager.

        Args:
            parent: Parent QObject if using Qt
        """
        if QtCore:
            super().__init__(parent)

        self._session_data = {}
        self._session_file_path = self._get_session_file_path()
        self._auto_save_timer = None
        self._is_auto_save_enabled = False

        self._setup_auto_save()

    def _get_session_file_path(self) -> str:
        """Get the session file path."""
        session_dir = Path.home() / ".lrc_toolbox" / "sessions"
        session_dir.mkdir(parents=True, exist_ok=True)

        session_file_name = settings.get("session.session_file_name", "session.json")
        return str(session_dir / session_file_name)

    def _setup_auto_save(self) -> None:
        """Setup auto-save timer if Qt is available."""
        if not QtCore:
            return

        auto_save_interval = settings.get("session.auto_save_interval", 30)  # seconds

        if auto_save_interval > 0:
            self._auto_save_timer = QtCore.QTimer()
            self._auto_save_timer.timeout.connect(self._auto_save)
            self._auto_save_timer.start(auto_save_interval * 1000)  # Convert to milliseconds
            self._is_auto_save_enabled = True
            print(f"Auto-save enabled with {auto_save_interval}s interval")

    def save_session(self, session_data: Dict[str, Any] = None) -> bool:
        """
        Save current session state.

        Args:
            session_data: Session data to save. If None, uses current session data.

        Returns:
            True if save successful, False otherwise
        """
        try:
            if session_data is not None:
                self._session_data = session_data

            # Add timestamp and metadata
            save_data = {
                "timestamp": datetime.now().isoformat(),
                "version": settings.get("version", "2.0.0"),
                "session_data": self._session_data,
                "metadata": {
                    "save_reason": "manual",
                    "platform": os.name,
                    "process_id": os.getpid()
                }
            }

            # Create backup of existing session
            self._create_session_backup()

            # Save session data
            with open(self._session_file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            print(f"Session saved to: {self._session_file_path}")

            # Emit signal if Qt is available
            if QtCore and hasattr(self, 'session_saved'):
                self.session_saved.emit(self._session_file_path)

            return True

        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def load_session(self) -> Optional[Dict[str, Any]]:
        """
        Load session state from file.

        Returns:
            Session data if successful, None otherwise
        """
        try:
            if not os.path.exists(self._session_file_path):
                print("No session file found")
                return None

            with open(self._session_file_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            self._session_data = save_data.get("session_data", {})
            timestamp = save_data.get("timestamp", "Unknown")

            print(f"Session loaded from: {timestamp}")

            # Emit signal if Qt is available
            if QtCore and hasattr(self, 'session_restored'):
                self.session_restored.emit(self._session_data)

            return self._session_data

        except Exception as e:
            print(f"Error loading session: {e}")
            return None

    def _auto_save(self) -> None:
        """Auto-save current session."""
        if not self._session_data:
            return  # Nothing to save

        try:
            # Create auto-save data
            save_data = {
                "timestamp": datetime.now().isoformat(),
                "version": settings.get("version", "2.0.0"),
                "session_data": self._session_data,
                "metadata": {
                    "save_reason": "auto_save",
                    "platform": os.name,
                    "process_id": os.getpid()
                }
            }

            # Save to auto-save file
            auto_save_path = self._session_file_path.replace('.json', '_autosave.json')
            with open(auto_save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            print(f" Auto-saved session at {datetime.now().strftime('%H:%M:%S')}")

            # Emit signal if Qt is available
            if QtCore and hasattr(self, 'auto_save_triggered'):
                self.auto_save_triggered.emit()

        except Exception as e:
            print(f" Auto-save error: {e}")

    def _create_session_backup(self) -> None:
        """Create backup of existing session file."""
        try:
            if os.path.exists(self._session_file_path):
                backup_count = settings.get("session.session_backup_count", 3)

                # Rotate existing backups
                for i in range(backup_count - 1, 0, -1):
                    old_backup = f"{self._session_file_path}.bak{i}"
                    new_backup = f"{self._session_file_path}.bak{i + 1}"

                    if os.path.exists(old_backup):
                        if os.path.exists(new_backup):
                            os.remove(new_backup)
                        os.rename(old_backup, new_backup)

                # Create new backup
                backup_path = f"{self._session_file_path}.bak1"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(self._session_file_path, backup_path)

        except Exception as e:
            print(f" Error creating session backup: {e}")

    def update_session_data(self, key: str, value: Any) -> None:
        """
        Update session data.

        Args:
            key: Data key
            value: Data value
        """
        self._session_data[key] = value

    def get_session_data(self, key: str, default: Any = None) -> Any:
        """
        Get session data.

        Args:
            key: Data key
            default: Default value if key not found

        Returns:
            Session data value or default
        """
        return self._session_data.get(key, default)

    def clear_session(self) -> None:
        """Clear current session data."""
        self._session_data.clear()
        print(" Session data cleared")

    def has_crash_recovery_data(self) -> bool:
        """Check if crash recovery data is available."""
        auto_save_path = self._session_file_path.replace('.json', '_autosave.json')
        return os.path.exists(auto_save_path)

    def load_crash_recovery_data(self) -> Optional[Dict[str, Any]]:
        """Load crash recovery data."""
        try:
            auto_save_path = self._session_file_path.replace('.json', '_autosave.json')

            if not os.path.exists(auto_save_path):
                return None

            with open(auto_save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            recovery_data = save_data.get("session_data", {})
            timestamp = save_data.get("timestamp", "Unknown")

            print(f" Crash recovery data found from: {timestamp}")
            return recovery_data

        except Exception as e:
            print(f" Error loading crash recovery data: {e}")
            return None

    def cleanup_auto_save_files(self) -> None:
        """Clean up auto-save files."""
        try:
            auto_save_path = self._session_file_path.replace('.json', '_autosave.json')
            if os.path.exists(auto_save_path):
                os.remove(auto_save_path)
                print(" Auto-save files cleaned up")
        except Exception as e:
            print(f" Error cleaning up auto-save files: {e}")

    def enable_auto_save(self, enabled: bool = True) -> None:
        """Enable or disable auto-save."""
        if not QtCore or not self._auto_save_timer:
            return

        if enabled and not self._is_auto_save_enabled:
            self._auto_save_timer.start()
            self._is_auto_save_enabled = True
            print(" Auto-save enabled")
        elif not enabled and self._is_auto_save_enabled:
            self._auto_save_timer.stop()
            self._is_auto_save_enabled = False
            print(" Auto-save disabled")

    def get_session_info(self) -> Dict[str, Any]:
        """Get session manager information."""
        return {
            "session_file_path": self._session_file_path,
            "auto_save_enabled": self._is_auto_save_enabled,
            "session_data_keys": list(self._session_data.keys()),
            "has_crash_recovery": self.has_crash_recovery_data(),
            "auto_save_interval": settings.get("session.auto_save_interval", 30)
        }


# Global session manager instance
session_manager = SessionManager()