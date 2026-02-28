# -*- coding: utf-8 -*-
"""
Arnold & Redshift Light Renamer & Light Group Manager

A unified tool for managing lights and light groups for both Arnold and Redshift renderers.

Features:
- 3-column layout: Selection | Rename | Light Groups
- Rename lights with prefix, base name, suffix, and numbering
- Manage light groups for both Arnold (aiAov) and Redshift (rsLightGroup)
- Auto-detect renderer type and apply correct attributes
- Support mixed Arnold + Redshift scenes
- Text filters for quick light selection
- Support up to 5 indexed light groups per base name

Supported Renderers:
- Arnold: Uses 'aiAov' attribute (comma-separated groups)
- Redshift: Uses 'rsLightGroup' attribute (single group)
- Standard Maya lights: No light group support

Author: Katha
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import re
import sys
from collections import defaultdict

# -----------------------------
# Python 2/3 Compatibility
# -----------------------------
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
    text_type = unicode  # noqa: F821
    string_types = (str, unicode)  # noqa: F821
else:
    text_type = str
    string_types = (str,)

try:
    import maya.cmds as cmds
except ImportError:
    cmds = None

# -----------------------------
# Qt Compatibility Layer
# -----------------------------
try:
    # Maya 2022+ (Python 3)
    from PySide2 import QtWidgets, QtCore, QtGui
    try:
        import shiboken2 as shiboken
    except Exception:
        shiboken = None
except ImportError:
    # Older Maya (Python 2.7)
    from PySide import QtGui as QtWidgets
    from PySide import QtCore, QtGui
    try:
        import shiboken
    except Exception:
        shiboken = None


# -----------------------------
# Text Conversion Helpers
# -----------------------------
def to_text(v):
    """Convert any value to text string (unicode in Py2, str in Py3)."""
    if v is None:
        return text_type("")
    if isinstance(v, text_type):
        return v
    if PY2 and isinstance(v, str):
        try:
            return v.decode('utf-8')
        except Exception:
            return text_type(v)
    try:
        return text_type(v)
    except Exception:
        return text_type("")


def safe_format(template, *args, **kwargs):
    """Safe string formatting that works in both Py2 and Py3."""
    try:
        return to_text(template).format(*args, **kwargs)
    except Exception:
        return to_text(template)


def get_maya_main_window():
    """Get Maya main window as QWidget."""
    if shiboken is None:
        return None
    try:
        import maya.OpenMayaUI as omui
    except Exception:
        return None

    ptr = omui.MQtUtil.mainWindow()
    if ptr is None:
        return None

    try:
        if PY2:
            return shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)  # noqa: F821
        else:
            return shiboken.wrapInstance(int(ptr), QtWidgets.QWidget)
    except Exception:
        return None


# -----------------------------
# Renderer Light Types
# -----------------------------
ARNOLD_LIGHT_TYPES = [
    'aiAreaLight',        # Arnold area light
    'aiSkyDomeLight',     # Arnold sky dome/HDRI light
    'aiMeshLight',        # Arnold mesh light
    'aiPhotometricLight', # Arnold IES/photometric light
    'aiLightBlocker',     # Arnold light blocker (negative light)
    'aiLightPortal'       # Arnold light portal (interior optimization)
]

REDSHIFT_LIGHT_TYPES = [
    'RedshiftPhysicalLight',  # Redshift physical light (area/point/spot/etc)
    'RedshiftDomeLight',      # Redshift dome light (HDRI)
    'RedshiftPortalLight',    # Redshift portal light (interior optimization)
    'RedshiftIESLight'        # Redshift IES light
]

STANDARD_LIGHT_TYPES = [
    'directionalLight',   # Maya directional light
    'pointLight',         # Maya point light
    'spotLight',          # Maya spot light
    'areaLight',          # Maya area light
    'volumeLight'         # Maya volume light
]

ALL_LIGHT_TYPES = ARNOLD_LIGHT_TYPES + REDSHIFT_LIGHT_TYPES + STANDARD_LIGHT_TYPES


# -----------------------------
# Light Group Presets
# -----------------------------
LIGHT_GROUP_PRESETS = [
    'env_key',
    'env_fill',
    'env_rim',
    'env_back',
    'char_key',
    'char_fill',
    'char_rim',
    'char_back',
    'char_spec',
    'char_bounce'
]


# -----------------------------
# Helper Functions
# -----------------------------
def get_all_lights_in_scene():
    """Get all lights in Maya scene."""
    if not cmds:
        return []

    lights = []
    for light_type in ALL_LIGHT_TYPES:
        try:
            light_shapes = cmds.ls(type=light_type, long=True) or []
            for shape in light_shapes:
                try:
                    # Get transform node with fullPath to avoid ambiguous names
                    transforms = cmds.listRelatives(shape, parent=True, type='transform', fullPath=True) or []
                    if transforms:
                        # Get short name for display
                        light_transform = transforms[0].split('|')[-1]
                        if light_transform not in lights:
                            lights.append(light_transform)
                except Exception:
                    # If we can't get the transform, skip this light
                    continue
        except Exception:
            pass

    return lights


def is_arnold_light(light_name):
    """
    Check if light is an Arnold light.

    Args:
        light_name (str): Name of the light transform node

    Returns:
        bool: True if light is an Arnold light type, False otherwise

    Arnold Light Types:
        - aiAreaLight
        - aiSkyDomeLight
        - aiMeshLight
        - aiPhotometricLight
        - aiLightBlocker
        - aiLightPortal
    """
    if not cmds:
        return False

    try:
        # Use ls with long names to avoid ambiguous name errors
        full_paths = cmds.ls(light_name, long=True)
        if not full_paths:
            return False

        shapes = cmds.listRelatives(full_paths[0], shapes=True, fullPath=True) or []
        if not shapes:
            return False

        light_type = cmds.nodeType(shapes[0])
        return light_type in ARNOLD_LIGHT_TYPES
    except Exception:
        # If we can't determine, assume it's not an Arnold light
        return False


def is_redshift_light(light_name):
    """
    Check if light is a Redshift light.

    Args:
        light_name (str): Name of the light transform node

    Returns:
        bool: True if light is a Redshift light type, False otherwise

    Redshift Light Types:
        - RedshiftPhysicalLight
        - RedshiftDomeLight
        - RedshiftPortalLight
        - RedshiftIESLight
    """
    if not cmds:
        return False

    try:
        # Use ls with long names to avoid ambiguous name errors
        full_paths = cmds.ls(light_name, long=True)
        if not full_paths:
            return False

        shapes = cmds.listRelatives(full_paths[0], shapes=True, fullPath=True) or []
        if not shapes:
            return False

        light_type = cmds.nodeType(shapes[0])
        return light_type in REDSHIFT_LIGHT_TYPES
    except Exception:
        # If we can't determine, assume it's not a Redshift light
        return False


def get_light_renderer_type(light_name):
    """
    Detect which renderer the light belongs to.

    Args:
        light_name (str): Name of the light transform node

    Returns:
        str: 'arnold', 'redshift', or 'standard'

    Examples:
        >>> get_light_renderer_type('char_key_001')  # aiAreaLight
        'arnold'
        >>> get_light_renderer_type('env_fill_001')  # RedshiftPhysicalLight
        'redshift'
        >>> get_light_renderer_type('spotLight1')    # Maya spotLight
        'standard'
    """
    if is_arnold_light(light_name):
        return 'arnold'
    elif is_redshift_light(light_name):
        return 'redshift'
    else:
        return 'standard'


def get_arnold_light_group(light_name):
    """
    Get Arnold light group from light's aiAov attribute.

    Args:
        light_name (str): Name of the Arnold light transform node

    Returns:
        str: Light group name(s) from aiAov attribute (comma-separated if multiple)
             Empty string if no light group is set or light is not Arnold

    Arnold Light Group Attribute:
        - Attribute: aiAov (string)
        - Format: Comma-separated groups (e.g., "char_key,env_fill")
        - Multiple groups: Supported

    Example:
        >>> get_arnold_light_group('char_key_001')
        'char_key'
        >>> get_arnold_light_group('env_fill_002')
        'env_fill,env_rim'  # Multiple groups
    """
    if not cmds:
        return ""

    try:
        # Use ls with long names to avoid ambiguous name errors
        full_paths = cmds.ls(light_name, long=True)
        if not full_paths:
            return ""

        shapes = cmds.listRelatives(full_paths[0], shapes=True, fullPath=True) or []
        if not shapes:
            return ""

        shape = shapes[0]
        attr_name = safe_format("{0}.aiAov", shape)

        if cmds.objExists(attr_name):
            try:
                value = cmds.getAttr(attr_name) or ""
                return to_text(value)
            except Exception:
                return ""
    except Exception:
        return ""

    return ""


def get_redshift_light_group(light_name):
    """
    Get Redshift light group from light's rsLightGroup attribute.

    Args:
        light_name (str): Name of the Redshift light transform node

    Returns:
        str: Light group name from rsLightGroup attribute
             Empty string if no light group is set or light is not Redshift

    Redshift Light Group Attribute:
        - Attribute: rsLightGroup (string)
        - Format: Single group name (e.g., "char_key")
        - Multiple groups: NOT supported (Redshift limitation)

    Example:
        >>> get_redshift_light_group('char_key_001')
        'char_key'
        >>> get_redshift_light_group('env_fill_002')
        'env_fill'
    """
    if not cmds:
        return ""

    try:
        # Use ls with long names to avoid ambiguous name errors
        full_paths = cmds.ls(light_name, long=True)
        if not full_paths:
            return ""

        shapes = cmds.listRelatives(full_paths[0], shapes=True, fullPath=True) or []
        if not shapes:
            return ""

        shape = shapes[0]
        attr_name = safe_format("{0}.rsLightGroup", shape)

        if cmds.objExists(attr_name):
            try:
                value = cmds.getAttr(attr_name) or ""
                return to_text(value)
            except Exception:
                return ""
    except Exception:
        return ""

    return ""


def get_light_group(light_name):
    """
    Get light group from light (unified function for Arnold and Redshift).

    Auto-detects renderer type and retrieves the appropriate light group attribute:
    - Arnold: Uses aiAov attribute (supports multiple comma-separated groups)
    - Redshift: Uses rsLightGroup attribute (single group only)
    - Standard Maya lights: Returns empty string (no light group support)

    Args:
        light_name (str): Name of the light transform node

    Returns:
        str: Light group name(s) or empty string if not set

    Examples:
        >>> get_light_group('char_key_001')  # Arnold aiAreaLight
        'char_key'
        >>> get_light_group('env_fill_001')  # Redshift RedshiftPhysicalLight
        'env_fill'
        >>> get_light_group('spotLight1')    # Maya spotLight
        ''  # Standard lights don't support light groups
    """
    renderer = get_light_renderer_type(light_name)

    if renderer == 'arnold':
        return get_arnold_light_group(light_name)
    elif renderer == 'redshift':
        return get_redshift_light_group(light_name)
    else:
        return ""


def set_arnold_light_group(light_name, light_group):
    """
    Set Arnold light group on light's aiAov attribute.

    Args:
        light_name (str): Name of the Arnold light transform node
        light_group (str): Light group name(s) to set (comma-separated for multiple)

    Returns:
        bool: True if successfully set, False otherwise

    Arnold Light Group Attribute:
        - Attribute: aiAov (string)
        - Format: Comma-separated groups (e.g., "char_key,env_fill")
        - Multiple groups: Supported

    Example:
        >>> set_arnold_light_group('char_key_001', 'char_key')
        True
        >>> set_arnold_light_group('env_fill_002', 'env_fill,env_rim')
        True  # Multiple groups
    """
    if not cmds:
        return False

    try:
        # Use ls with long names to avoid ambiguous name errors
        full_paths = cmds.ls(light_name, long=True)
        if not full_paths:
            return False

        shapes = cmds.listRelatives(full_paths[0], shapes=True, fullPath=True) or []
        if not shapes:
            return False

        shape = shapes[0]

        # Check if it's an Arnold light
        light_type = cmds.nodeType(shape)
        if light_type not in ARNOLD_LIGHT_TYPES:
            return False

        attr_name = safe_format("{0}.aiAov", shape)

        if cmds.objExists(attr_name):
            try:
                cmds.setAttr(attr_name, light_group, type="string")
                return True
            except Exception:
                return False
    except Exception:
        return False

    return False


def set_redshift_light_group(light_name, light_group):
    """
    Set Redshift light group on light's rsLightGroup attribute.

    Args:
        light_name (str): Name of the Redshift light transform node
        light_group (str): Light group name to set (single group only)

    Returns:
        bool: True if successfully set, False otherwise

    Redshift Light Group Attribute:
        - Attribute: rsLightGroup (string)
        - Format: Single group name (e.g., "char_key")
        - Multiple groups: NOT supported (Redshift limitation)

    Note:
        If light_group contains commas (multiple groups), only the first group
        will be used due to Redshift's single-group limitation.

    Example:
        >>> set_redshift_light_group('char_key_001', 'char_key')
        True
        >>> set_redshift_light_group('env_fill_002', 'env_fill,env_rim')
        True  # Only 'env_fill' will be set (first group)
    """
    if not cmds:
        return False

    try:
        # Use ls with long names to avoid ambiguous name errors
        full_paths = cmds.ls(light_name, long=True)
        if not full_paths:
            return False

        shapes = cmds.listRelatives(full_paths[0], shapes=True, fullPath=True) or []
        if not shapes:
            return False

        shape = shapes[0]

        # Check if it's a Redshift light
        light_type = cmds.nodeType(shape)
        if light_type not in REDSHIFT_LIGHT_TYPES:
            return False

        # Redshift only supports single group, take first if multiple
        if ',' in light_group:
            light_group = light_group.split(',')[0].strip()

        attr_name = safe_format("{0}.rsLightGroup", shape)

        if cmds.objExists(attr_name):
            try:
                cmds.setAttr(attr_name, light_group, type="string")
                return True
            except Exception:
                return False
    except Exception:
        return False

    return False


def set_light_group(light_name, light_group):
    """
    Set light group on light (unified function for Arnold and Redshift).

    Auto-detects renderer type and sets the appropriate light group attribute:
    - Arnold: Sets aiAov attribute (supports multiple comma-separated groups)
    - Redshift: Sets rsLightGroup attribute (single group only, takes first if multiple)
    - Standard Maya lights: Returns False (no light group support)

    Args:
        light_name (str): Name of the light transform node
        light_group (str): Light group name(s) to set

    Returns:
        bool: True if successfully set, False otherwise

    Examples:
        >>> set_light_group('char_key_001', 'char_key')  # Arnold aiAreaLight
        True
        >>> set_light_group('env_fill_001', 'env_fill')  # Redshift RedshiftPhysicalLight
        True
        >>> set_light_group('spotLight1', 'char_key')    # Maya spotLight
        False  # Standard lights don't support light groups
    """
    renderer = get_light_renderer_type(light_name)

    if renderer == 'arnold':
        return set_arnold_light_group(light_name, light_group)
    elif renderer == 'redshift':
        return set_redshift_light_group(light_name, light_group)
    else:
        return False


def get_all_light_groups_in_scene():
    """
    Get all unique light groups in scene from both Arnold and Redshift lights.

    Scans all Arnold and Redshift lights in the scene and collects their light groups:
    - Arnold: Reads from aiAov attribute (splits comma-separated groups)
    - Redshift: Reads from rsLightGroup attribute (single group)

    Returns:
        list: Sorted list of unique light group names found in the scene

    Example:
        >>> get_all_light_groups_in_scene()
        ['char_key', 'char_fill', 'env_key', 'env_fill', 'env_rim']
    """
    if not cmds:
        return []

    light_groups = set()

    # Get Arnold light groups (aiAov attribute)
    for light_type in ARNOLD_LIGHT_TYPES:
        try:
            lights = cmds.ls(type=light_type, long=True) or []
            for light_shape in lights:
                try:
                    attr_name = safe_format("{0}.aiAov", light_shape)
                    if cmds.objExists(attr_name):
                        aov_value = cmds.getAttr(attr_name) or ""
                        if aov_value:
                            # Split by comma for multiple groups
                            groups = [g.strip() for g in aov_value.split(',') if g.strip()]
                            light_groups.update(groups)
                except Exception:
                    # Skip lights that cause errors
                    continue
        except Exception:
            pass

    # Get Redshift light groups (rsLightGroup attribute)
    for light_type in REDSHIFT_LIGHT_TYPES:
        try:
            lights = cmds.ls(type=light_type, long=True) or []
            for light_shape in lights:
                try:
                    attr_name = safe_format("{0}.rsLightGroup", light_shape)
                    if cmds.objExists(attr_name):
                        group_value = cmds.getAttr(attr_name) or ""
                        if group_value:
                            # Redshift uses single group (no comma separation)
                            light_groups.add(group_value.strip())
                except Exception:
                    # Skip lights that cause errors
                    continue
        except Exception:
            pass

    return sorted(list(light_groups))


def extract_light_group_from_name(light_name):
    """
    Extract light group from light name.

    Pattern: {prefix}_{base}_{suffix}_{number}
    Light Group: {prefix}_{base}

    Examples:
        env_key_lgt_001 → env_key
        char_fill_lgt_003 → char_fill
    """
    # Remove number suffix
    name_without_number = re.sub(r'_\d+$', '', light_name)

    # Remove type suffix (_lgt, _blk, etc.)
    name_without_suffix = re.sub(r'_(lgt|blk|vol|fx)$', '', name_without_number)

    return name_without_suffix


# -----------------------------
# Main UI Class
# -----------------------------
class ArnoldLightRenamerUI(QtWidgets.QDialog):
    """
    Arnold Light Renamer & Light Group Manager
    3-column layout: Selection | Rename | Light Groups
    """

    def __init__(self, parent=None):
        super(ArnoldLightRenamerUI, self).__init__(parent)

        self.setWindowTitle("Arnold Light Renamer & Light Group Manager")

        # Wide layout - wider than tall
        self.setMinimumSize(1200, 600)
        self.resize(1400, 700)

        # Make resizable
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        self._selection_job = None
        self._light_groups_cache = []

        self.init_ui()
        self._install_selection_job()
        self.refresh_all()

    def init_ui(self):
        """Initialize UI layout."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 4)
        main_layout.setSpacing(4)

        # Main horizontal splitter (3 columns) - THIS SHOULD EXPAND
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Column 1: Selection (20%)
        selection_widget = self.create_selection_widget()
        main_splitter.addWidget(selection_widget)

        # Column 2: Rename (30%)
        rename_widget = self.create_rename_widget()
        main_splitter.addWidget(rename_widget)

        # Column 3: Light Groups (50%)
        lightgroup_widget = self.create_lightgroup_widget()
        main_splitter.addWidget(lightgroup_widget)

        # Set initial splitter sizes (20% / 30% / 50%)
        # Based on 1400px width: 280 / 420 / 700
        main_splitter.setSizes([280, 420, 700])

        # Add main splitter with stretch factor (expands to fill space)
        main_layout.addWidget(main_splitter, 1)

        # Summary bar - fixed size, no stretch
        summary_widget = self.create_summary_widget()
        main_layout.addWidget(summary_widget, 0)

        # Close button - fixed size, no stretch
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setMaximumHeight(24)
        main_layout.addWidget(close_btn, 0)

    def create_selection_widget(self):
        """Create Column 1: Selection widget."""
        widget = QtWidgets.QGroupBox("Selection")
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(4)

        # Refresh button
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_selection)
        layout.addWidget(refresh_btn)

        # Selection count label
        self.selection_count_label = QtWidgets.QLabel("Selected: 0")
        layout.addWidget(self.selection_count_label)

        # Filter text field
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(QtWidgets.QLabel("Filter:"))
        self.selection_filter_edit = QtWidgets.QLineEdit()
        self.selection_filter_edit.setPlaceholderText("Type to filter...")
        self.selection_filter_edit.textChanged.connect(self.filter_selection_list)
        filter_layout.addWidget(self.selection_filter_edit)
        layout.addLayout(filter_layout)

        # Selection list
        self.selection_list = QtWidgets.QListWidget()
        self.selection_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        layout.addWidget(self.selection_list)

        # Selection buttons
        select_all_btn = QtWidgets.QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_lights)
        layout.addWidget(select_all_btn)

        select_none_btn = QtWidgets.QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_none_lights)
        layout.addWidget(select_none_btn)

        renderer_only_btn = QtWidgets.QPushButton("Renderer Only")
        renderer_only_btn.clicked.connect(self.select_renderer_only)
        layout.addWidget(renderer_only_btn)

        return widget

    def create_rename_widget(self):
        """Create Column 2: Rename widget."""
        widget = QtWidgets.QGroupBox("Rename Lights")
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(4)

        # Form layout for inputs
        form = QtWidgets.QFormLayout()
        form.setSpacing(4)

        # Base name
        self.base_name_edit = QtWidgets.QLineEdit()
        self.base_name_edit.setPlaceholderText("e.g., key, fill, rim")
        self.base_name_edit.textChanged.connect(self.update_rename_preview)
        form.addRow("Base Name:", self.base_name_edit)

        # Prefix
        self.prefix_edit = QtWidgets.QLineEdit()
        self.prefix_edit.setPlaceholderText("e.g., env, char")
        self.prefix_edit.textChanged.connect(self.update_rename_preview)
        form.addRow("Prefix:", self.prefix_edit)

        # Suffix
        self.suffix_edit = QtWidgets.QLineEdit()
        self.suffix_edit.setPlaceholderText("e.g., lgt, blk")
        self.suffix_edit.textChanged.connect(self.update_rename_preview)
        form.addRow("Suffix:", self.suffix_edit)

        layout.addLayout(form)

        # Numbering options
        num_group = QtWidgets.QGroupBox("Numbering")
        num_layout = QtWidgets.QHBoxLayout(num_group)

        self.add_numbers_check = QtWidgets.QCheckBox("Add Numbers")
        self.add_numbers_check.setChecked(True)
        self.add_numbers_check.toggled.connect(self.update_rename_preview)
        num_layout.addWidget(self.add_numbers_check)

        num_layout.addWidget(QtWidgets.QLabel("Start:"))
        self.start_number_spin = QtWidgets.QSpinBox()
        self.start_number_spin.setRange(0, 9999)
        self.start_number_spin.setValue(1)
        self.start_number_spin.valueChanged.connect(self.update_rename_preview)
        num_layout.addWidget(self.start_number_spin)

        num_layout.addWidget(QtWidgets.QLabel("Pad:"))
        self.number_padding_spin = QtWidgets.QSpinBox()
        self.number_padding_spin.setRange(1, 8)
        self.number_padding_spin.setValue(3)
        self.number_padding_spin.valueChanged.connect(self.update_rename_preview)
        num_layout.addWidget(self.number_padding_spin)

        layout.addWidget(num_group)

        # Preview name
        preview_layout = QtWidgets.QHBoxLayout()
        preview_layout.addWidget(QtWidgets.QLabel("Preview:"))
        self.preview_name_label = QtWidgets.QLabel("---")
        self.preview_name_label.setStyleSheet("QLabel { color: #4A90E2; font-weight: bold; }")
        preview_layout.addWidget(self.preview_name_label)
        preview_layout.addStretch()
        layout.addLayout(preview_layout)

        # Apply rename button
        apply_rename_btn = QtWidgets.QPushButton("Apply Rename")
        apply_rename_btn.setStyleSheet("QPushButton { background-color: #4A90E2; color: white; padding: 6px; }")
        apply_rename_btn.clicked.connect(self.apply_rename)
        layout.addWidget(apply_rename_btn)

        # Separator
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(separator)

        # Rename preview list
        preview_label = QtWidgets.QLabel("Rename Preview:")
        layout.addWidget(preview_label)

        self.rename_preview_list = QtWidgets.QListWidget()
        layout.addWidget(self.rename_preview_list)

        return widget

    def create_lightgroup_widget(self):
        """Create Column 3: Light Groups widget."""
        widget = QtWidgets.QGroupBox("Light Groups")
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(4)

        # Nested horizontal splitter (groups | assignments)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left: Light groups list
        groups_widget = self.create_groups_list_widget()
        splitter.addWidget(groups_widget)

        # Right: Light assignments table
        assignments_widget = self.create_assignments_widget()
        splitter.addWidget(assignments_widget)

        # Set initial sizes (35% / 65% of 700px = 245 / 455)
        splitter.setSizes([245, 455])

        layout.addWidget(splitter)
        return widget

    def create_groups_list_widget(self):
        """Create light groups list widget."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Label
        label = QtWidgets.QLabel("Light Groups:")
        layout.addWidget(label)

        # Groups list
        self.groups_list = QtWidgets.QListWidget()
        self.groups_list.itemSelectionChanged.connect(self.on_group_selected)
        layout.addWidget(self.groups_list)

        # Selected group label
        self.selected_group_label = QtWidgets.QLabel("Selected: None")
        self.selected_group_label.setStyleSheet("QLabel { color: #666; font-size: 10px; }")
        layout.addWidget(self.selected_group_label)

        # Group management buttons
        btn_layout = QtWidgets.QHBoxLayout()

        edit_btn = QtWidgets.QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_group)
        btn_layout.addWidget(edit_btn)

        delete_btn = QtWidgets.QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_group)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

        # Create new group button
        new_group_btn = QtWidgets.QPushButton("+ New Group")
        new_group_btn.clicked.connect(self.create_new_group)
        layout.addWidget(new_group_btn)

        # Add index button
        add_index_btn = QtWidgets.QPushButton("+ Add Index (1-5)")
        add_index_btn.clicked.connect(self.add_index_to_group)
        layout.addWidget(add_index_btn)

        return widget

    def create_assignments_widget(self):
        """Create light assignments table widget."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Label
        label = QtWidgets.QLabel("Light Assignments:")
        layout.addWidget(label)

        # Text filter for light names
        text_filter_layout = QtWidgets.QHBoxLayout()
        text_filter_layout.addWidget(QtWidgets.QLabel("Filter:"))
        self.assignments_filter_edit = QtWidgets.QLineEdit()
        self.assignments_filter_edit.setPlaceholderText("Type to filter lights...")
        self.assignments_filter_edit.textChanged.connect(self.filter_assignments_table)
        text_filter_layout.addWidget(self.assignments_filter_edit)
        layout.addLayout(text_filter_layout)

        # Assignments table
        self.assignments_table = QtWidgets.QTableWidget()
        self.assignments_table.setColumnCount(2)
        self.assignments_table.setHorizontalHeaderLabels(["Light Name", "Light Group"])

        # Set column widths
        header = self.assignments_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.assignments_table.setColumnWidth(0, 200)

        layout.addWidget(self.assignments_table)

        # Dropdown filter
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(QtWidgets.QLabel("Type:"))

        self.filter_combo = QtWidgets.QComboBox()
        self.filter_combo.addItems(["All", "Arnold Only", "Redshift Only", "With Groups", "No Groups"])
        self.filter_combo.currentIndexChanged.connect(self.refresh_assignments_table)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Action buttons
        btn_layout = QtWidgets.QHBoxLayout()

        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_assignments_table)
        btn_layout.addWidget(refresh_btn)

        apply_btn = QtWidgets.QPushButton("Apply Changes")
        apply_btn.setStyleSheet("QPushButton { background-color: #4A90E2; color: white; padding: 6px; }")
        apply_btn.clicked.connect(self.apply_light_group_changes)
        btn_layout.addWidget(apply_btn)

        layout.addLayout(btn_layout)

        return widget

    def create_summary_widget(self):
        """Create summary bar widget."""
        widget = QtWidgets.QWidget()
        widget.setMaximumHeight(20)
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(0)

        self.summary_label = QtWidgets.QLabel("Total: 0  |  Selected: 0  |  Groups: 0  |  Unassigned: 0")
        self.summary_label.setStyleSheet("QLabel { padding: 1px; font-size: 9px; }")
        self.summary_label.setMaximumHeight(18)
        layout.addWidget(self.summary_label)

        return widget

    # -----------------------------
    # Selection Job Management
    # -----------------------------
    def _install_selection_job(self):
        """Install Maya selection change callback."""
        self._remove_selection_job()
        if cmds:
            try:
                self._selection_job = cmds.scriptJob(
                    event=["SelectionChanged", self.refresh_selection],
                    protected=True
                )
            except Exception:
                self._selection_job = None

    def _remove_selection_job(self):
        """Remove Maya selection change callback."""
        if self._selection_job and cmds:
            try:
                if cmds.scriptJob(exists=self._selection_job):
                    cmds.scriptJob(kill=self._selection_job, force=True)
            except Exception:
                pass
        self._selection_job = None

    def closeEvent(self, event):
        """Handle window close event."""
        self._remove_selection_job()
        super(ArnoldLightRenamerUI, self).closeEvent(event)

    # -----------------------------
    # Refresh Methods
    # -----------------------------
    def refresh_all(self):
        """Refresh all UI elements."""
        self.refresh_selection()
        self.refresh_groups_list()
        self.refresh_assignments_table()
        self.update_summary()

    def refresh_selection(self):
        """
        Refresh selection list from Maya.

        Shows all lights in the scene with renderer type prefix:
        - [A] = Arnold light (aiAreaLight, aiSkyDomeLight, etc.)
        - [R] = Redshift light (RedshiftPhysicalLight, RedshiftDomeLight, etc.)
        - [L] = Standard Maya light (spotLight, pointLight, etc.)
        """
        self.selection_list.clear()

        lights = get_all_lights_in_scene()

        for light in lights:
            item = QtWidgets.QListWidgetItem(light)

            # Check if light is in Maya selection
            if cmds:
                try:
                    selected = cmds.ls(selection=True) or []
                    if light in selected:
                        item.setSelected(True)
                except Exception:
                    pass

            # Add prefix based on renderer type
            renderer = get_light_renderer_type(light)
            if renderer == 'arnold':
                item.setText(safe_format("[A] {0}", light))
            elif renderer == 'redshift':
                item.setText(safe_format("[R] {0}", light))
            else:
                item.setText(safe_format("[L] {0}", light))

            self.selection_list.addItem(item)

        # Update count
        selected_count = len(self.selection_list.selectedItems())
        self.selection_count_label.setText(safe_format("Selected: {0}", selected_count))

        # Update rename preview
        self.update_rename_preview()
        self.update_summary()

    def filter_selection_list(self):
        """Filter selection list based on text input."""
        filter_text = to_text(self.selection_filter_edit.text()).strip().lower()

        for i in range(self.selection_list.count()):
            item = self.selection_list.item(i)
            item_text = to_text(item.text()).lower()

            # Show item if filter is empty or text matches
            if not filter_text or filter_text in item_text:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def filter_assignments_table(self):
        """Filter assignments table based on text input."""
        filter_text = to_text(self.assignments_filter_edit.text()).strip().lower()

        for row in range(self.assignments_table.rowCount()):
            item = self.assignments_table.item(row, 0)
            if item:
                item_text = to_text(item.text()).lower()

                # Show row if filter is empty or text matches
                if not filter_text or filter_text in item_text:
                    self.assignments_table.setRowHidden(row, False)
                else:
                    self.assignments_table.setRowHidden(row, True)

    def refresh_groups_list(self):
        """Refresh light groups list."""
        self.groups_list.clear()

        # Get all light groups from scene (groups assigned to lights)
        scene_groups = get_all_light_groups_in_scene()

        # Merge with cache (includes manually created groups not yet assigned)
        # Use set to avoid duplicates, then sort
        all_groups = set(self._light_groups_cache + scene_groups)
        self._light_groups_cache = sorted(list(all_groups))

        for group in self._light_groups_cache:
            # Count lights in this group
            count = self.count_lights_in_group(group)
            item_text = safe_format("{0}  ({1})", group, count)
            self.groups_list.addItem(item_text)

        self.update_summary()

    def refresh_assignments_table(self):
        """
        Refresh light assignments table.

        Applies dropdown filter:
        - All: Show all lights
        - Arnold Only: Show only Arnold lights
        - Redshift Only: Show only Redshift lights
        - With Groups: Show only lights with light groups assigned
        - No Groups: Show only lights without light groups
        """
        self.assignments_table.setRowCount(0)

        lights = get_all_lights_in_scene()

        # Apply filter
        filter_type = self.filter_combo.currentText()
        filtered_lights = []

        for light in lights:
            if filter_type == "Arnold Only" and not is_arnold_light(light):
                continue
            elif filter_type == "Redshift Only" and not is_redshift_light(light):
                continue
            elif filter_type == "With Groups":
                group = get_light_group(light)
                if not group:
                    continue
            elif filter_type == "No Groups":
                group = get_light_group(light)
                if group:
                    continue

            filtered_lights.append(light)

        # Populate table
        self.assignments_table.setRowCount(len(filtered_lights))

        for row, light in enumerate(filtered_lights):
            # Column 0: Light name
            name_item = QtWidgets.QTableWidgetItem(light)
            name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.assignments_table.setItem(row, 0, name_item)

            # Column 1: Light group dropdown
            group_combo = QtWidgets.QComboBox()
            group_combo.addItem("(none)")

            # Add all available groups
            for group in self._light_groups_cache:
                group_combo.addItem(group)

            # Set current group
            current_group = get_light_group(light)
            if current_group:
                index = group_combo.findText(current_group)
                if index >= 0:
                    group_combo.setCurrentIndex(index)

            self.assignments_table.setCellWidget(row, 1, group_combo)

        self.update_summary()

    def update_summary(self):
        """
        Update summary bar with light counts.

        Shows:
        - Total: All lights in scene
        - Selected: Currently selected lights
        - Groups: Number of unique light groups
        - Unassigned: Renderer lights (Arnold/Redshift) without light groups
        """
        total_lights = len(get_all_lights_in_scene())
        selected_lights = len(self.selection_list.selectedItems())
        total_groups = len(self._light_groups_cache)

        # Count unassigned renderer lights (Arnold and Redshift)
        unassigned = 0
        for light in get_all_lights_in_scene():
            # Only count renderer lights (Arnold or Redshift)
            if is_arnold_light(light) or is_redshift_light(light):
                group = get_light_group(light)
                if not group:
                    unassigned += 1

        summary_text = safe_format(
            "Total: {0}  |  Selected: {1}  |  Groups: {2}  |  Unassigned: {3}",
            total_lights, selected_lights, total_groups, unassigned
        )
        self.summary_label.setText(summary_text)

    # -----------------------------
    # Selection Handlers
    # -----------------------------
    def select_all_lights(self):
        """Select all lights in list."""
        self.selection_list.selectAll()
        self.update_rename_preview()

    def select_none_lights(self):
        """Deselect all lights in list."""
        self.selection_list.clearSelection()
        self.update_rename_preview()

    def select_renderer_only(self):
        """
        Select only renderer lights (Arnold and Redshift).

        Excludes standard Maya lights (spotLight, pointLight, etc.)
        and selects only Arnold and Redshift lights.
        """
        self.selection_list.clearSelection()

        for i in range(self.selection_list.count()):
            item = self.selection_list.item(i)
            # Remove all prefixes to get clean light name
            light_name = item.text().replace("[A] ", "").replace("[R] ", "").replace("[L] ", "")

            # Select if Arnold or Redshift light
            if is_arnold_light(light_name) or is_redshift_light(light_name):
                item.setSelected(True)

        self.update_rename_preview()

    # -----------------------------
    # Rename Functionality
    # -----------------------------
    def update_rename_preview(self):
        """Update rename preview list."""
        self.rename_preview_list.clear()

        # Get selected lights
        selected_items = self.selection_list.selectedItems()
        if not selected_items:
            self.preview_name_label.setText("---")
            return

        # Generate preview names
        prefix = to_text(self.prefix_edit.text()).strip()
        base = to_text(self.base_name_edit.text()).strip()
        suffix = to_text(self.suffix_edit.text()).strip()

        if not base:
            self.preview_name_label.setText("(need base name)")
            return

        # Generate first name as preview
        preview_name = self.generate_new_name(prefix, base, suffix, 0)
        self.preview_name_label.setText(preview_name)

        # Generate preview for all selected lights
        for i, item in enumerate(selected_items):
            # Remove all renderer prefixes ([A], [R], [L])
            old_name = item.text().replace("[A] ", "").replace("[R] ", "").replace("[L] ", "")
            new_name = self.generate_new_name(prefix, base, suffix, i)

            preview_text = safe_format("{0}  ->  {1}", old_name, new_name)
            self.rename_preview_list.addItem(preview_text)

    def generate_new_name(self, prefix, base, suffix, index):
        """Generate new light name.

        Format: {category}_{base}_{index}_{type}
        Example: char_key_001_lgt
        """
        parts = []

        # Category (prefix)
        if prefix:
            parts.append(prefix)

        # Base name
        parts.append(base)

        # Index number (always add if numbering is enabled)
        if self.add_numbers_check.isChecked():
            start = self.start_number_spin.value()
            padding = self.number_padding_spin.value()
            number = start + index
            num_str = str(number).zfill(padding)
            parts.append(num_str)

        # Type (suffix) - always at the end
        if suffix:
            parts.append(suffix)

        return "_".join(parts)

    def apply_rename(self):
        """Apply rename to selected lights."""
        if not cmds:
            QtWidgets.QMessageBox.warning(self, "Error", "Maya commands not available!")
            return

        # Get selected lights
        selected_items = self.selection_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select lights to rename!")
            return

        # Check base name
        base = to_text(self.base_name_edit.text()).strip()
        if not base:
            QtWidgets.QMessageBox.warning(self, "No Base Name", "Please enter a base name!")
            return

        prefix = to_text(self.prefix_edit.text()).strip()
        suffix = to_text(self.suffix_edit.text()).strip()

        # Confirm
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Rename",
            safe_format("Rename {0} lights?", len(selected_items)),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply != QtWidgets.QMessageBox.Yes:
            return

        # Generate light group name from prefix and base
        # Format: {prefix}_{base} (e.g., char_key)
        light_group_name = None
        if prefix and base:
            light_group_name = safe_format("{0}_{1}", prefix, base)
        elif base:
            light_group_name = base

        # Perform rename and assign light group
        renamed_count = 0
        errors = []

        cmds.undoInfo(openChunk=True)
        try:
            for i, item in enumerate(selected_items):
                # Remove all renderer prefixes ([A], [R], [L])
                old_name = item.text().replace("[A] ", "").replace("[R] ", "").replace("[L] ", "")
                new_name = self.generate_new_name(prefix, base, suffix, i)

                try:
                    if cmds.objExists(old_name):
                        # Rename the light
                        renamed_light = cmds.rename(old_name, new_name)
                        renamed_count += 1

                        # Auto-assign light group if it's an Arnold or Redshift light
                        if light_group_name and (is_arnold_light(renamed_light) or is_redshift_light(renamed_light)):
                            set_light_group(renamed_light, light_group_name)

                            # Add to cache if not exists
                            if light_group_name not in self._light_groups_cache:
                                self._light_groups_cache.append(light_group_name)

                except Exception as e:
                    errors.append(safe_format("{0}: {1}", old_name, to_text(e)))
        finally:
            cmds.undoInfo(closeChunk=True)

        # Show result
        if errors:
            msg = safe_format("Renamed {0} lights.\n\nErrors:\n{1}", renamed_count, "\n".join(errors[:5]))
            QtWidgets.QMessageBox.warning(self, "Rename Completed (with errors)", msg)
        else:
            msg = safe_format("Renamed {0} lights!", renamed_count)
            if light_group_name:
                msg += safe_format("\n\nLight group '{0}' assigned to Arnold lights.", light_group_name)
            QtWidgets.QMessageBox.information(self, "Success", msg)

        # Refresh UI
        self.refresh_all()

    # -----------------------------
    # Light Group Management
    # -----------------------------
    def on_group_selected(self):
        """Handle group selection change."""
        selected_items = self.groups_list.selectedItems()
        if selected_items:
            group_text = selected_items[0].text()
            # Extract group name (remove count)
            group_name = group_text.split("(")[0].strip()
            self.selected_group_label.setText(safe_format("Selected: {0}", group_name))
        else:
            self.selected_group_label.setText("Selected: None")

    def count_lights_in_group(self, group_name):
        """
        Count lights assigned to a group (both Arnold and Redshift).

        Args:
            group_name (str): Name of the light group to count

        Returns:
            int: Number of lights assigned to this group
        """
        count = 0
        for light in get_all_lights_in_scene():
            # Check both Arnold and Redshift lights
            if is_arnold_light(light) or is_redshift_light(light):
                light_group = get_light_group(light)
                if light_group:
                    # Handle multiple groups (comma-separated for Arnold)
                    groups = [g.strip() for g in light_group.split(',')]
                    if group_name in groups:
                        count += 1
        return count

    def create_new_group(self):
        """Create a new light group."""
        # Show input dialog
        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Create New Light Group",
            "Enter light group name:\n(e.g., env_key, char_fill)",
            QtWidgets.QLineEdit.Normal,
            ""
        )

        if ok and text:
            group_name = to_text(text).strip()

            if not group_name:
                return

            # Check if group already exists
            if group_name in self._light_groups_cache:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Group Exists",
                    safe_format("Light group '{0}' already exists!", group_name)
                )
                return

            # Add to cache and refresh
            self._light_groups_cache.append(group_name)
            self._light_groups_cache.sort()
            self.refresh_groups_list()
            self.refresh_assignments_table()

            QtWidgets.QMessageBox.information(
                self,
                "Group Created",
                safe_format("Light group '{0}' created!\n\nAssign lights to this group in the assignments table.", group_name)
            )

    def edit_group(self):
        """Edit selected light group name."""
        selected_items = self.groups_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a light group to edit!")
            return

        # Get current group name
        group_text = selected_items[0].text()
        old_group_name = group_text.split("(")[0].strip()

        # Show input dialog
        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Edit Light Group",
            safe_format("Enter new name for '{0}':", old_group_name),
            QtWidgets.QLineEdit.Normal,
            old_group_name
        )

        if ok and text:
            new_group_name = to_text(text).strip()

            if not new_group_name or new_group_name == old_group_name:
                return

            # Rename group on all lights
            if not cmds:
                QtWidgets.QMessageBox.warning(self, "Error", "Maya commands not available!")
                return

            renamed_count = 0
            cmds.undoInfo(openChunk=True)
            try:
                for light in get_all_lights_in_scene():
                    # Process both Arnold and Redshift lights
                    if is_arnold_light(light) or is_redshift_light(light):
                        light_group = get_light_group(light)
                        if light_group:
                            # Handle multiple groups (Arnold) or single group (Redshift)
                            groups = [g.strip() for g in light_group.split(',')]
                            if old_group_name in groups:
                                # Replace old with new
                                groups = [new_group_name if g == old_group_name else g for g in groups]
                                new_value = ",".join(groups)
                                set_light_group(light, new_value)
                                renamed_count += 1
            finally:
                cmds.undoInfo(closeChunk=True)

            QtWidgets.QMessageBox.information(
                self,
                "Group Renamed",
                safe_format("Renamed light group on {0} lights!", renamed_count)
            )

            self.refresh_all()

    def delete_group(self):
        """Delete selected light group."""
        selected_items = self.groups_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a light group to delete!")
            return

        # Get group name
        group_text = selected_items[0].text()
        group_name = group_text.split("(")[0].strip()

        # Confirm
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            safe_format("Delete light group '{0}'?\n\nThis will remove the group from all lights.", group_name),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply != QtWidgets.QMessageBox.Yes:
            return

        # Remove group from all lights
        if not cmds:
            QtWidgets.QMessageBox.warning(self, "Error", "Maya commands not available!")
            return

        removed_count = 0
        cmds.undoInfo(openChunk=True)
        try:
            for light in get_all_lights_in_scene():
                # Process both Arnold and Redshift lights
                if is_arnold_light(light) or is_redshift_light(light):
                    light_group = get_light_group(light)
                    if light_group:
                        # Handle multiple groups (Arnold) or single group (Redshift)
                        groups = [g.strip() for g in light_group.split(',') if g.strip()]
                        if group_name in groups:
                            groups.remove(group_name)
                            new_value = ",".join(groups)
                            set_light_group(light, new_value)
                            removed_count += 1
        finally:
            cmds.undoInfo(closeChunk=True)

        QtWidgets.QMessageBox.information(
            self,
            "Group Deleted",
            safe_format("Removed light group from {0} lights!", removed_count)
        )

        self.refresh_all()

    def add_index_to_group(self):
        """Add index (1-5) to selected light group."""
        selected_items = self.groups_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a base light group to add index!")
            return

        # Get base group name
        group_text = selected_items[0].text()
        base_group = group_text.split("(")[0].strip()

        # Check if it already has an index
        if re.search(r'_\d+$', base_group):
            QtWidgets.QMessageBox.warning(
                self,
                "Already Indexed",
                safe_format("'{0}' already has an index!\n\nSelect the base group without index.", base_group)
            )
            return

        # Show dialog to select index
        items = ["1", "2", "3", "4", "5"]
        item, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Add Index to Light Group",
            safe_format("Select index to add to '{0}':", base_group),
            items,
            0,
            False
        )

        if ok and item:
            new_group = safe_format("{0}_{1}", base_group, item)

            # Check if already exists
            if new_group in self._light_groups_cache:
                QtWidgets.QMessageBox.information(
                    self,
                    "Already Exists",
                    safe_format("Light group '{0}' already exists!", new_group)
                )
                return

            # Add to cache
            self._light_groups_cache.append(new_group)
            self._light_groups_cache.sort()
            self.refresh_groups_list()
            self.refresh_assignments_table()

            QtWidgets.QMessageBox.information(
                self,
                "Index Added",
                safe_format("Created light group '{0}'!\n\nAssign lights to this group in the assignments table.", new_group)
            )

    def apply_light_group_changes(self):
        """
        Apply light group changes from assignments table.

        Updates light group attributes for both Arnold and Redshift lights:
        - Arnold: Sets aiAov attribute
        - Redshift: Sets rsLightGroup attribute
        """
        if not cmds:
            QtWidgets.QMessageBox.warning(self, "Error", "Maya commands not available!")
            return

        # Confirm
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Changes",
            "Apply light group assignments?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply != QtWidgets.QMessageBox.Yes:
            return

        # Apply changes
        changed_count = 0
        errors = []

        cmds.undoInfo(openChunk=True)
        try:
            for row in range(self.assignments_table.rowCount()):
                # Get light name
                name_item = self.assignments_table.item(row, 0)
                if not name_item:
                    continue

                light_name = name_item.text()

                # Get selected group from combo box
                group_combo = self.assignments_table.cellWidget(row, 1)
                if not group_combo:
                    continue

                selected_group = group_combo.currentText()

                # Skip if "(none)"
                if selected_group == "(none)":
                    selected_group = ""

                # Get current group
                current_group = get_light_group(light_name)

                # Only update if changed
                if selected_group != current_group:
                    try:
                        if set_light_group(light_name, selected_group):
                            changed_count += 1
                        else:
                            errors.append(safe_format("{0}: Not a renderer light (Arnold/Redshift)", light_name))
                    except Exception as e:
                        errors.append(safe_format("{0}: {1}", light_name, to_text(e)))
        finally:
            cmds.undoInfo(closeChunk=True)

        # Show result
        if errors:
            msg = safe_format("Updated {0} lights.\n\nErrors:\n{1}", changed_count, "\n".join(errors[:5]))
            QtWidgets.QMessageBox.warning(self, "Changes Applied (with errors)", msg)
        else:
            QtWidgets.QMessageBox.information(self, "Success", safe_format("Updated {0} lights!", changed_count))

        # Refresh UI
        self.refresh_all()


# -----------------------------
# Show UI Function
# -----------------------------
def show_ui():
    """
    Show the Arnold & Redshift Light Renamer UI.

    Opens the unified light management tool for both Arnold and Redshift renderers.
    """
    global arnold_light_renamer_window
    try:
        arnold_light_renamer_window.close()
        arnold_light_renamer_window.deleteLater()
    except Exception:
        pass

    arnold_light_renamer_window = ArnoldLightRenamerUI(parent=get_maya_main_window())
    arnold_light_renamer_window.show()


if __name__ == "__main__":
    show_ui()

