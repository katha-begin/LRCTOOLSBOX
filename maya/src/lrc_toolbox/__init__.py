"""
LRC Toolbox - Maya Lighting and Render Setup Management Tool

A modular architecture for managing lighting workflows, render setup templates,
and asset/shot navigation in Maya with enhanced template management system.
"""

__version__ = "2.0.0"
__author__ = "LRC Toolbox Team"

# Import main components for easy access
from .ui.main_window import RenderSetupUI
from .core.project_manager import ProjectManager
from .core.version_manager import VersionManager
from .core.template_manager import TemplateManager
from .core.light_manager import LightManager
from .core.render_setup_api import RenderSetupAPI

__all__ = [
    "RenderSetupUI",
    "ProjectManager", 
    "VersionManager",
    "TemplateManager",
    "LightManager",
    "RenderSetupAPI"
]
