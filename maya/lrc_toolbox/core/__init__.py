"""
Core Module

This module contains the core business logic and data models
for the LRC Toolbox application.
"""

from .models import (
    # Enums
    ProjectType,
    TemplateType,
    RenderLayerElement,
    RenderLayerVariance,

    # Data Models
    ProjectInfo,
    VersionInfo,
    TemplateInfo,
    FileInfo,
    NavigationContext,
    RenderLayerInfo,
    LightInfo,
    ImportOptions,
    ExportOptions,

    # Type Aliases
    TemplatePackageList,
    FileList,
    LightList,
    RenderLayerList
)

from .project_manager import ProjectManager
from .version_manager import VersionManager
from .template_manager import TemplateManager
from .light_manager import LightManager
from .render_setup_api import RenderSetupAPI

__all__ = [
    # Enums
    "ProjectType",
    "TemplateType",
    "RenderLayerElement",
    "RenderLayerVariance",

    # Data Models
    "ProjectInfo",
    "VersionInfo",
    "TemplateInfo",
    "FileInfo",
    "NavigationContext",
    "RenderLayerInfo",
    "LightInfo",
    "ImportOptions",
    "ExportOptions",

    # Type Aliases
    "TemplatePackageList",
    "FileList",
    "LightList",
    "RenderLayerList",

    # Manager Classes
    "ProjectManager",
    "VersionManager",
    "TemplateManager",
    "LightManager",
    "RenderSetupAPI"
]

__all__ = [
    # Will be added as modules are implemented
    # "ProjectManager",
    # "VersionManager",
    # "TemplateManager",
    # "LightManager",
    # "RenderSetupAPI",
    # "ProjectInfo",
    # "VersionInfo",
    # "TemplateInfo",
    # "FileInfo"
]
