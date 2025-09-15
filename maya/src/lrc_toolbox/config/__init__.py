"""
Config module - Configuration and settings management

Contains configuration files, default settings, and
settings management functionality.
"""

from .settings import Settings
from .defaults import DEFAULT_SETTINGS

__all__ = [
    "Settings",
    "DEFAULT_SETTINGS"
]
