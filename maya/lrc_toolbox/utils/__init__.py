"""
Utilities Module

This module contains utility functions and helper classes
for file operations, naming conventions, regex tools, and Maya helpers.
"""

from .file_operations import (
    FileOperations,
    copy_file,
    move_file,
    delete_file,
    create_backup,
    get_file_info
)

from .naming_conventions import (
    NamingConventions,
    NamingPattern,
    validate_render_layer,
    validate_light_name,
    generate_layer_name
)

from .regex_tools import (
    RegexTools,
    dag_to_regex,
    validate_regex,
    test_regex,
    get_common_patterns
)

from .maya_helpers import (
    MayaHelpers,
    get_selected,
    select_lights,
    rename_selected
)

from .context_detector import (
    ContextDetector,
    context_detector
)

__all__ = [
    # File Operations
    "FileOperations",
    "copy_file",
    "move_file",
    "delete_file",
    "create_backup",
    "get_file_info",

    # Naming Conventions
    "NamingConventions",
    "NamingPattern",
    "validate_render_layer",
    "validate_light_name",
    "generate_layer_name",

    # Regex Tools
    "RegexTools",
    "dag_to_regex",
    "validate_regex",
    "test_regex",
    "get_common_patterns",

    # Maya Helpers
    "MayaHelpers",
    "get_selected",
    "select_lights",
    "rename_selected",

    # Context Detection
    "ContextDetector",
    "context_detector"
]
