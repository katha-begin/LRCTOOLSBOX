"""
Core module - Business logic and data models

Contains the main business logic classes for project management,
version control, template management, and Maya API integration.
"""

from .project_manager import ProjectManager
from .version_manager import VersionManager
from .template_manager import TemplateManager
from .light_manager import LightManager
from .render_setup_api import RenderSetupAPI
from .models import ProjectInfo, VersionInfo, TemplateInfo, FileInfo

__all__ = [
    "ProjectManager",
    "VersionManager", 
    "TemplateManager",
    "LightManager",
    "RenderSetupAPI",
    "ProjectInfo",
    "VersionInfo",
    "TemplateInfo", 
    "FileInfo"
]
