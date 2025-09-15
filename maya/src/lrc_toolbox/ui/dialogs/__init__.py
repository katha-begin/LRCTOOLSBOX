"""
UI Dialogs module - Dialog components

Contains dialog windows for version management, template creation,
and template inheritance operations.
"""

from .version_dialog import VersionDialog
from .template_dialog import TemplateDialog
from .inheritance_dialog import InheritanceDialog

__all__ = [
    "VersionDialog",
    "TemplateDialog",
    "InheritanceDialog"
]
