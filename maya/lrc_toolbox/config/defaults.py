"""
Default configuration settings for LRC Toolbox

Contains all default values for the application settings,
including template management, naming conventions, and UI preferences.
"""

from typing import Dict, Any, List

# Default project settings
DEFAULT_PROJECT_SETTINGS = {
    "project_root": "V:/SWA/all",
    "scene_structure": {
        "episodes": ["Ep01", "Ep02", "Ep03", "Ep04", "Ep05"],
        "sequences_pattern": "sq{:04d}",
        "shots_pattern": "SH{:04d}"
    },
    "asset_structure": {
        "categories": ["Sets", "Props", "Characters", "Vehicles"],
        "subcategories": {
            "Sets": ["interior", "exterior"],
            "Props": ["hero", "background", "set_dressing"],
            "Characters": ["main", "secondary", "crowd"],
            "Vehicles": ["hero", "background"]
        }
    }
}

# Default template management settings
DEFAULT_TEMPLATE_SETTINGS = {
    "template_directory": "templates",
    "template_types": {
        "master": {"icon": "🏛️", "color": "#FFD700"},
        "key": {"icon": "🔑", "color": "#FF6B35"},
        "standard": {"icon": "📋", "color": "#4ECDC4"},
        "micro": {"icon": "🎯", "color": "#95E1D3"}
    },
    "inheritance_levels": [
        "global",
        "episode", 
        "sequence",
        "shot",
        "asset"
    ],
    "auto_discovery": True,
    "template_extensions": [".json", ".ma", ".mb"]
}

# Default naming convention settings
DEFAULT_NAMING_SETTINGS = {
    "separator": "_",
    "index_padding": 3,
    "case_style": "lower",
    "light_naming": {
        "pattern": "{sequence}_{shot}_{type}_{purpose}_{index:03d}",
        "types": ["LGT", "AREA", "SPOT", "DIR", "POINT", "VOL"],
        "purposes": ["key", "fill", "rim", "bounce", "practical", "fx"]
    },
    "version_naming": {
        "pattern": "{base_name}_v{version:03d}",
        "hero_suffix": "_hero"
    }
}

# Default UI settings
DEFAULT_UI_SETTINGS = {
    "window": {
        "width": 700,
        "height": 900,
        "docking_area": "right",
        "allowed_areas": ["right", "left"],
        "tab_index": 0,
        "restore_state": True
    },
    "file_list": {
        "icons": {
            "hero": "👑",
            "template": "📋",
            "version": "📝"
        },
        "colors": {
            "hero": "#FFD700",
            "template": "#00FF00",
            "version": "#87CEEB"
        }
    },
    "refresh_interval": 5000  # milliseconds
}

# Default Maya integration settings
DEFAULT_MAYA_SETTINGS = {
    "render_setup": {
        "default_layer_name": "defaultRenderLayer",
        "collection_prefix": "collection_",
        "override_prefix": "override_"
    },
    "light_management": {
        "light_types": [
            "directionalLight",
            "areaLight", 
            "spotLight",
            "pointLight",
            "volumeLight"
        ],
        "default_attributes": [
            "intensity",
            "color",
            "temperature",
            "exposure"
        ]
    }
}

# Default persistence settings
DEFAULT_PERSISTENCE_SETTINGS = {
    "navigation_context": {
        "remember_last_context": True,
        "auto_restore_on_startup": True,
        "context_history_limit": 10
    },
    "project_memory": {
        "recent_projects": [],
        "max_recent_projects": 5,
        "auto_detect_project_changes": True,
        "last_project_root": ""
    },
    "widget_states": {
        "save_filter_states": True,
        "save_column_widths": True,
        "save_sort_orders": True,
        "restore_expanded_items": True
    },
    "file_operations": {
        "remember_last_directories": True,
        "last_import_directory": "",
        "last_export_directory": "",
        "last_template_directory": ""
    }
}

# Default session management settings
DEFAULT_SESSION_SETTINGS = {
    "auto_save_interval": 30,  # seconds
    "session_backup_count": 3,
    "restore_on_crash": True,
    "save_on_context_change": True,
    "session_file_name": "session.json"
}

# Combine all default settings
DEFAULT_SETTINGS: Dict[str, Any] = {
    "project": DEFAULT_PROJECT_SETTINGS,
    "templates": DEFAULT_TEMPLATE_SETTINGS,
    "naming": DEFAULT_NAMING_SETTINGS,
    "ui": DEFAULT_UI_SETTINGS,
    "maya": DEFAULT_MAYA_SETTINGS,
    "persistence": DEFAULT_PERSISTENCE_SETTINGS,
    "session": DEFAULT_SESSION_SETTINGS,
    "version": "2.0.0"
}
