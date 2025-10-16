"""
Template Tools Widget

This module provides the Template Tools widget with Automated Render Layer
creation and Light Manager functionality according to UI design specifications.
"""

import os
from typing import Optional, List, Dict, Any

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtWidgets import *
    from PySide2.QtCore import *
    from PySide2.QtGui import *
except ImportError:
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        from PySide6.QtWidgets import *
        from PySide6.QtCore import *
        from PySide6.QtGui import *
    except ImportError:
        print("Warning: Neither PySide2 nor PySide6 available")
        QtWidgets = None

from ...config.settings import settings
from ...core.render_setup_api import RenderSetupAPI
from ...core.light_manager import LightManager
from ...core.template_manager import TemplateManager
from ...core.models import (
    RenderLayerElement,
    RenderLayerVariance,
    NavigationContext,
    ProjectType,
)



class TemplateToolsWidget(QtWidgets.QWidget):
    """
    Template Tools widget for automated render layer creation and light management.

    Provides render layer creation tools following naming conventions and
    light management tools with hierarchical naming and grouping.
    """

    # Signals for communication with main window
    layer_created = QtCore.Signal(str)      # Emitted when render layer is created
    lights_renamed = QtCore.Signal(list)    # Emitted when lights are renamed
    light_group_created = QtCore.Signal(str)  # Emitted when light group is created

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the Template Tools widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Core APIs with real Maya integration
        self.render_api = RenderSetupAPI()
        self.light_manager = LightManager()
        self.template_manager = TemplateManager()

        self._current_context = {}
        self._setup_ui()
        self._connect_signals()
        self._populate_initial_data()

        print("Template Tools Widget initialized")



    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Create sections
        self._create_render_layer_widget()
        self._create_light_manager_widget()

        # Add sections to main layout
        main_layout.addWidget(self.render_layer_group)
        main_layout.addWidget(self.light_manager_group)
        main_layout.addStretch()

    def _create_render_layer_widget(self) -> None:
        """Create Automated Render Layer Widget section."""
        self.render_layer_group = QtWidgets.QGroupBox("🎬 Automated Render Layer Creation")
        layout = QtWidgets.QVBoxLayout(self.render_layer_group)

        # Layer naming controls
        naming_layout = QtWidgets.QGridLayout()

        # Prefix selection
        naming_layout.addWidget(QtWidgets.QLabel("Prefix:"), 0, 0)
        self.prefix_combo = QtWidgets.QComboBox()
        self.prefix_combo.setEditable(True)
        self.prefix_combo.addItems(["MASTER", "SH0010", "SH0020", "KITCHEN", "FOREST", "HERO"])
        naming_layout.addWidget(self.prefix_combo, 0, 1)

        # Element selection
        naming_layout.addWidget(QtWidgets.QLabel("Element:"), 0, 2)
        self.element_combo = QtWidgets.QComboBox()
        self.element_combo.addItems(["BG", "CHAR", "ATMOS", "FX"])
        naming_layout.addWidget(self.element_combo, 0, 3)

        # Variance selection
        naming_layout.addWidget(QtWidgets.QLabel("Variance:"), 1, 0)
        self.variance_combo = QtWidgets.QComboBox()
        self.variance_combo.addItems(["A", "B", "C"])
        naming_layout.addWidget(self.variance_combo, 1, 1)

        # Preview
        naming_layout.addWidget(QtWidgets.QLabel("Preview:"), 1, 2)
        self.layer_preview_label = QtWidgets.QLabel("MASTER_BG_A")
        self.layer_preview_label.setStyleSheet("font-weight: bold; color: #2c5aa0; background-color: #f0f8ff; padding: 4px; border: 1px solid #c0c0c0;")
        naming_layout.addWidget(self.layer_preview_label, 1, 3)

        layout.addLayout(naming_layout)

        # Examples section
        examples_group = QtWidgets.QGroupBox("📋 Standard Examples")
        examples_layout = QtWidgets.QVBoxLayout(examples_group)

        # Shot-Specific Examples
        shot_examples = QtWidgets.QLabel(
            "Shot-Specific Examples:\n"
            "• SH0010_BG_A, SH0010_CHAR_B, SH0010_ATMOS, SH0010_FX_A\n"
            "• SH0020_BG_A, SH0020_CHAR_A, SH0020_ATMOS"
        )
        shot_examples.setStyleSheet("color: #666666; font-size: 10px;")
        examples_layout.addWidget(shot_examples)

        # Asset-Specific Examples
        asset_examples = QtWidgets.QLabel(
            "Asset-Specific Examples:\n"
            "• KITCHEN_BG_A, KITCHEN_CHAR_A, KITCHEN_ATMOS\n"
            "• FOREST_BG_A, FOREST_CHAR_B, FOREST_ATMOS, FOREST_FX_A"
        )
        asset_examples.setStyleSheet("color: #666666; font-size: 10px;")
        examples_layout.addWidget(asset_examples)

        layout.addWidget(examples_group)

        # Action buttons
        layer_actions_layout = QtWidgets.QHBoxLayout()
        self.create_layer_btn = QtWidgets.QPushButton("Create Render Layer")
        self.create_layer_btn.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white;")
        self.preview_layer_btn = QtWidgets.QPushButton("Preview Only")

        layer_actions_layout.addWidget(self.create_layer_btn)
        layer_actions_layout.addWidget(self.preview_layer_btn)
        layer_actions_layout.addStretch()

        layout.addLayout(layer_actions_layout)

        # Quick Template Creation Section
        quick_template_group = QtWidgets.QGroupBox("⚡ Quick Template Creation")
        quick_layout = QtWidgets.QVBoxLayout(quick_template_group)

        # Context input for quick templates
        context_layout = QtWidgets.QHBoxLayout()
        context_layout.addWidget(QtWidgets.QLabel("Context:"))
        self.quick_context_edit = QtWidgets.QLineEdit()
        self.quick_context_edit.setText("MASTER")
        self.quick_context_edit.setPlaceholderText("e.g., MASTER, SH0010, KITCHEN")
        context_layout.addWidget(self.quick_context_edit)

        context_layout.addWidget(QtWidgets.QLabel("Variance:"))
        self.quick_variance_combo = QtWidgets.QComboBox()
        self.quick_variance_combo.addItems(["A", "B", "C"])
        context_layout.addWidget(self.quick_variance_combo)

        quick_layout.addLayout(context_layout)

        # Individual template buttons
        individual_layout = QtWidgets.QHBoxLayout()

        self.create_bg_btn = QtWidgets.QPushButton("BG Template")
        self.create_bg_btn.setToolTip("Create Background template with geo/light collections")
        self.create_bg_btn.setStyleSheet("background-color: #8BC34A; color: white; font-weight: bold;")

        self.create_char_btn = QtWidgets.QPushButton("CHAR Template")
        self.create_char_btn.setToolTip("Create Character template with geo/light collections")
        self.create_char_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")

        self.create_atmos_btn = QtWidgets.QPushButton("ATMOS Template")
        self.create_atmos_btn.setToolTip("Create Atmospheric template with geo/light collections")
        self.create_atmos_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")

        self.create_fx_btn = QtWidgets.QPushButton("FX Template")
        self.create_fx_btn.setToolTip("Create Effects template with geo/light collections")
        self.create_fx_btn.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold;")

        individual_layout.addWidget(self.create_bg_btn)
        individual_layout.addWidget(self.create_char_btn)
        individual_layout.addWidget(self.create_atmos_btn)
        individual_layout.addWidget(self.create_fx_btn)

        quick_layout.addLayout(individual_layout)

        # Batch creation button
        batch_layout = QtWidgets.QHBoxLayout()
        self.create_all_templates_btn = QtWidgets.QPushButton("🚀 Create All Standard Templates")
        self.create_all_templates_btn.setToolTip("Create all standard templates (BG, CHAR, ATMOS, FX) at once")
        self.create_all_templates_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")

        self.clear_layers_btn = QtWidgets.QPushButton("🧹 Clear All Layers")
        self.clear_layers_btn.setToolTip("Clear all render layers (except default)")
        self.clear_layers_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")

        batch_layout.addWidget(self.create_all_templates_btn)
        batch_layout.addWidget(self.clear_layers_btn)

        quick_layout.addLayout(batch_layout)

        # Template structure info
        structure_info = QtWidgets.QLabel(
            "📋 Template Structure:\n"
            "• Layer: {context}_{element}_{variance} (filter: transforms, pattern: '*_Grp')\n"
            "  ├── Collection: {context}_{element}_{variance}_geo (filter: transforms, pattern: '*')\n"
            "  │   ├── Sub: {context}_{element}_{variance}_matte (filter: shapes, blank pattern)\n"
            "  │   └── Sub: {context}_{element}_{variance}_visibility (filter: shapes, blank pattern)\n"
            "  └── Collection: {context}_{element}_{variance}_light (filter: transforms, pattern: '*')"
        )
        structure_info.setStyleSheet("color: #666666; font-size: 9px; background-color: #f9f9f9; padding: 8px; border: 1px solid #ddd;")
        structure_info.setWordWrap(True)
        quick_layout.addWidget(structure_info)

        layout.addWidget(quick_template_group)

    def _create_light_manager_widget(self) -> None:
        """Create Light Manager Widget section."""
        self.light_manager_group = QtWidgets.QGroupBox("💡 Light Manager")
        layout = QtWidgets.QVBoxLayout(self.light_manager_group)

        # Light Rename Tool
        rename_group = QtWidgets.QGroupBox("🏷️ Light Rename Tool")
        rename_layout = QtWidgets.QGridLayout(rename_group)

        # Hierarchy level
        rename_layout.addWidget(QtWidgets.QLabel("Hierarchy:"), 0, 0)
        self.hierarchy_combo = QtWidgets.QComboBox()
        self.hierarchy_combo.addItems(["Master", "Key", "Child"])
        rename_layout.addWidget(self.hierarchy_combo, 0, 1)

        # Light type
        rename_layout.addWidget(QtWidgets.QLabel("Type:"), 0, 2)
        self.light_type_combo = QtWidgets.QComboBox()
        self.light_type_combo.setEditable(True)
        self.light_type_combo.addItems(["KEY", "FILL", "RIM", "BOUNCE", "KICK"])
        rename_layout.addWidget(self.light_type_combo, 0, 3)

        # Index
        rename_layout.addWidget(QtWidgets.QLabel("Index:"), 1, 0)
        self.light_index_spin = QtWidgets.QSpinBox()
        self.light_index_spin.setRange(1, 999)
        self.light_index_spin.setValue(1)
        self.light_index_spin.setPrefix("00")
        rename_layout.addWidget(self.light_index_spin, 1, 1)

        # Preview
        rename_layout.addWidget(QtWidgets.QLabel("Preview:"), 1, 2)
        self.light_preview_label = QtWidgets.QLabel("MASTER_KEY_001")
        self.light_preview_label.setStyleSheet("font-weight: bold; color: #2c5aa0; background-color: #f0f8ff; padding: 4px; border: 1px solid #c0c0c0;")
        rename_layout.addWidget(self.light_preview_label, 1, 3)

        layout.addWidget(rename_group)

        # Light Grouping Tools
        grouping_group = QtWidgets.QGroupBox("👥 Light Grouping Tools")
        grouping_layout = QtWidgets.QHBoxLayout(grouping_group)

        self.group_selected_btn = QtWidgets.QPushButton("Group Selected Lights")
        self.create_group_btn = QtWidgets.QPushButton("Create Light Group")
        self.ungroup_btn = QtWidgets.QPushButton("Ungroup Selected")

        grouping_layout.addWidget(self.group_selected_btn)
        grouping_layout.addWidget(self.create_group_btn)
        grouping_layout.addWidget(self.ungroup_btn)
        grouping_layout.addStretch()

        layout.addWidget(grouping_group)

        # Light actions
        light_actions_layout = QtWidgets.QHBoxLayout()
        self.rename_lights_btn = QtWidgets.QPushButton("Rename Selected Lights")
        self.rename_lights_btn.setStyleSheet("font-weight: bold; background-color: #2196F3; color: white;")
        self.refresh_lights_btn = QtWidgets.QPushButton("Refresh Scene Lights")

        light_actions_layout.addWidget(self.rename_lights_btn)
        light_actions_layout.addWidget(self.refresh_lights_btn)
        light_actions_layout.addStretch()

        layout.addLayout(light_actions_layout)

    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        # Render Layer controls
        self.prefix_combo.currentTextChanged.connect(self._update_layer_preview)
        self.element_combo.currentTextChanged.connect(self._update_layer_preview)
        self.variance_combo.currentTextChanged.connect(self._update_layer_preview)
        self.create_layer_btn.clicked.connect(self._on_create_layer)
        self.preview_layer_btn.clicked.connect(self._on_preview_layer)

        # Light Manager controls
        self.hierarchy_combo.currentTextChanged.connect(self._update_light_preview)
        self.light_type_combo.currentTextChanged.connect(self._update_light_preview)
        self.light_index_spin.valueChanged.connect(self._update_light_preview)
        self.rename_lights_btn.clicked.connect(self._on_rename_lights)
        self.refresh_lights_btn.clicked.connect(self._on_refresh_lights)

        # Light Grouping controls
        self.group_selected_btn.clicked.connect(self._on_group_selected)
        self.create_group_btn.clicked.connect(self._on_create_group)
        self.ungroup_btn.clicked.connect(self._on_ungroup_selected)

        # Quick Template controls
        self.quick_context_edit.textChanged.connect(self._update_quick_template_preview)
        self.quick_variance_combo.currentTextChanged.connect(self._update_quick_template_preview)

        # Individual template buttons
        self.create_bg_btn.clicked.connect(self._on_create_bg_template)
        self.create_char_btn.clicked.connect(self._on_create_char_template)
        self.create_atmos_btn.clicked.connect(self._on_create_atmos_template)
        self.create_fx_btn.clicked.connect(self._on_create_fx_template)

        # Batch template controls
        self.create_all_templates_btn.clicked.connect(self._on_create_all_templates)
        self.clear_layers_btn.clicked.connect(self._on_clear_layers)

    def _populate_initial_data(self) -> None:
        """Populate initial data and update previews."""
        self._update_layer_preview()
        self._update_light_preview()

    # Event handlers
    def _update_layer_preview(self) -> None:
        """Update render layer name preview."""
        prefix = self.prefix_combo.currentText()
        element = self.element_combo.currentText()
        variance = self.variance_combo.currentText()

        # ATMOS omits variance according to naming convention
        if element == "ATMOS":
            layer_name = f"{prefix}_{element}"
        else:
            layer_name = f"{prefix}_{element}_{variance}"

        self.layer_preview_label.setText(layer_name)

    def _update_light_preview(self) -> None:
        """Update light name preview."""
        hierarchy = self.hierarchy_combo.currentText()
        light_type = self.light_type_combo.currentText()
        index = self.light_index_spin.value()

        # Format index with zero padding
        index_str = f"{index:03d}"

        if hierarchy == "Master":
            light_name = f"MASTER_{light_type}_{index_str}"
        elif hierarchy == "Key":
            # Use current context prefix if available
            prefix = self._get_current_prefix()
            light_name = f"{prefix}_{light_type}_{index_str}"
        else:  # Child
            prefix = self._get_current_prefix()
            # For child lights, add a sub-type (simplified version)
            sub_type = "RIM" if light_type == "KEY" else "BOUNCE"
            light_name = f"{prefix}_{light_type}_{sub_type}_{index_str}"

        self.light_preview_label.setText(light_name)

    def _get_current_prefix(self) -> str:
        """Get current prefix based on context or default."""
        # Use render layer prefix or default to SH0010
        current_prefix = self.prefix_combo.currentText()
        return current_prefix if current_prefix else "SH0010"

    def _on_create_layer(self) -> None:
        """Handle create render layer button click."""
        layer_name = self.layer_preview_label.text()

        # Validate naming via API
        ok, message = self.render_api.validate_layer_naming(layer_name)
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Invalid Layer Name", message)
            return

        # Map UI to enums
        element_text = self.element_combo.currentText()
        variance_text = self.variance_combo.currentText()
        element = RenderLayerElement[element_text]
        variance = None if element_text == "ATMOS" else RenderLayerVariance[variance_text]
        prefix = self.prefix_combo.currentText()

        # Create layer via API (mock-backed today)
        layer_info = self.render_api.create_render_layer(layer_name, prefix, element, variance)

        QtWidgets.QMessageBox.information(
            self, "Layer Created",
            f"Render layer '{layer_info.full_name}' created successfully."
        )

        # Emit signal
        self.layer_created.emit(layer_info.full_name)

    def _on_preview_layer(self) -> None:
        """Handle preview layer button click."""
        layer_name = self.layer_preview_label.text()
        QtWidgets.QMessageBox.information(
            self, "Layer Preview",
            f"Layer Name Preview: {layer_name}\n\n"
            f"Naming Convention Applied:\n"
            f"• Prefix: {self.prefix_combo.currentText()}\n"
            f"• Element: {self.element_combo.currentText()}\n"
            f"• Variance: {self.variance_combo.currentText() if self.element_combo.currentText() != 'ATMOS' else 'N/A (ATMOS omits variance)'}"
        )

    def _on_rename_lights(self) -> None:
        """Handle rename lights button click using LightManager API (mock-backed)."""
        hierarchy = self.hierarchy_combo.currentText()
        light_type = self.light_type_combo.currentText()
        context = self._build_navigation_context_from_prefix()

        # Prefer selected lights if available; otherwise take first few scene lights (mock)
        lights = []
        if hasattr(self.light_manager, "get_selected_lights"):
            try:
                lights = self.light_manager.get_selected_lights()  # type: ignore[attr-defined]
            except Exception:
                lights = []
        if not lights:
            try:
                lights = self.light_manager.get_scene_lights()[:3]
            except Exception:
                lights = []

        if not lights:
            QtWidgets.QMessageBox.information(
                self, "Rename Lights",
                "No lights found to rename (mock scene is empty)."
            )
            return

        new_names = self.light_manager.rename_lights_with_pattern(lights, hierarchy, light_type, context)

        QtWidgets.QMessageBox.information(
            self, "Lights Renamed",
            f"Successfully renamed {len(new_names)} lights!\n\n" +
            "\n".join([f"• {name}" for name in new_names])
        )

        # Emit signal
        self.lights_renamed.emit(new_names)

    def _on_refresh_lights(self) -> None:
        """Handle refresh lights button click (mock-backed)."""
        try:
            count = len(self.light_manager.get_scene_lights())
        except Exception:
            count = 0
        QtWidgets.QMessageBox.information(
            self, "Refresh Lights",
            f"Scene lights scanned. Found {count} lights (mock)."
        )

    def _on_group_selected(self) -> None:
        """Handle group selected lights button click using LightManager (mock-backed)."""
        group_name = self._generate_group_name()
        # Use selected lights if available, else first few scene lights (mock)
        lights = []
        if hasattr(self.light_manager, "get_selected_lights"):
            try:
                lights = self.light_manager.get_selected_lights()  # type: ignore[attr-defined]
            except Exception:
                lights = []
        if not lights:
            try:
                lights = self.light_manager.get_scene_lights()[:3]
            except Exception:
                lights = []

        self.light_manager.create_light_group(group_name, lights)

        QtWidgets.QMessageBox.information(
            self, "Group Lights",
            f"Grouped {len(lights)} lights into '{group_name}' (mock)."
        )

        # Emit signal
        self.light_group_created.emit(group_name)

    def _on_create_group(self) -> None:
        """Handle create light group button click using LightManager (mock-backed)."""
        group_name = self._generate_group_name()
        context = self._build_navigation_context_from_prefix()

        # Create an empty group
        self.light_manager.create_light_group(group_name, [], context)

        QtWidgets.QMessageBox.information(
            self, "Create Light Group",
            f"Light group '{group_name}' created (empty, mock)."
        )

        # Emit signal
        self.light_group_created.emit(group_name)

    def _on_ungroup_selected(self) -> None:
        """Handle ungroup selected button click using LightManager (mock-backed)."""
        # Use selected or sample lights
        lights = []
        if hasattr(self.light_manager, "get_selected_lights"):
            try:
                lights = self.light_manager.get_selected_lights()  # type: ignore[attr-defined]
            except Exception:
                lights = []
        if not lights:
            try:
                lights = self.light_manager.get_scene_lights()[:3]
            except Exception:
                lights = []

        self.light_manager.ungroup_lights(lights)

        QtWidgets.QMessageBox.information(
            self, "Ungroup Lights",
            f"Ungrouped {len(lights)} lights (mock)."
        )

    def _generate_group_name(self) -> str:
        """Generate group name based on current light settings (via LightManager)."""
        light_type = self.light_type_combo.currentText()
        context = self._build_navigation_context_from_prefix()
        try:
            return self.light_manager.generate_group_name(light_type, context)
        except Exception:
            prefix = self._get_current_prefix()
            return f"{prefix}_{light_type}_GROUP"

    def _build_navigation_context_from_prefix(self) -> NavigationContext:
        """Build a minimal NavigationContext from the current prefix for naming APIs."""
        prefix = self._get_current_prefix()
        if prefix.upper().startswith("SH"):
            return NavigationContext(type=ProjectType.SHOT, shot=prefix, department="lighting")
        return NavigationContext(type=ProjectType.ASSET, asset=prefix.upper(), department="lighting")

    # Public methods
    def set_context(self, context: Dict[str, Any]) -> None:
        """Set current context from Navigator widget."""
        self._current_context = context

        # Update prefix combo based on context
        if context.get("type") == "shot":
            shot = context.get("shot", "")
            if shot:
                self.prefix_combo.setCurrentText(shot)
        elif context.get("type") == "asset":
            asset = context.get("asset", "")
            if asset:
                self.prefix_combo.setCurrentText(asset.upper())

        # Update quick template context
        if context.get("type") == "shot":
            shot = context.get("shot", "")
            if shot:
                self.quick_context_edit.setText(shot)
        elif context.get("type") == "asset":
            asset = context.get("asset", "")
            if asset:
                self.quick_context_edit.setText(asset.upper())

        # Update previews
        self._update_layer_preview()
        self._update_light_preview()
        self._update_quick_template_preview()

    def get_current_layer_name(self) -> str:
        """Get the current render layer name preview."""
        return self.layer_preview_label.text()

    def get_current_light_name(self) -> str:
        """Get the current light name preview."""
        return self.light_preview_label.text()

    # Quick Template Methods
    def _update_quick_template_preview(self) -> None:
        """Update quick template preview tooltips."""
        context = self.quick_context_edit.text().strip() or "MASTER"
        variance = self.quick_variance_combo.currentText()

        # Update button tooltips with preview names
        self.create_bg_btn.setToolTip(f"Create: {context}_BG_{variance}")
        self.create_char_btn.setToolTip(f"Create: {context}_CHAR_{variance}")
        self.create_atmos_btn.setToolTip(f"Create: {context}_ATMOS_{variance}")
        self.create_fx_btn.setToolTip(f"Create: {context}_FX_{variance}")

        # Update batch button tooltip
        templates = [f"{context}_BG_{variance}", f"{context}_CHAR_{variance}",
                    f"{context}_ATMOS_{variance}", f"{context}_FX_{variance}"]
        self.create_all_templates_btn.setToolTip(f"Create all: {', '.join(templates)}")

    def _on_create_bg_template(self) -> None:
        """Handle BG template creation."""
        context = self.quick_context_edit.text().strip() or "MASTER"
        variance = self.quick_variance_combo.currentText()

        success = self.render_api.create_bg_template(context, variance)

        if success:
            layer_name = f"{context}_BG_{variance}"
            QtWidgets.QMessageBox.information(
                self, "Template Created",
                f"✅ BG Template created successfully!\n\n"
                f"Layer: {layer_name}\n"
                f"Collections: geo, light\n"
                f"Sub-collections: matte, visibility"
            )
            self.layer_created.emit(layer_name)
        else:
            QtWidgets.QMessageBox.warning(
                self, "Creation Failed",
                f"❌ Failed to create BG template.\n\n"
                f"The layer may already exist or Maya Render Setup is not available."
            )

    def _on_create_char_template(self) -> None:
        """Handle CHAR template creation."""
        context = self.quick_context_edit.text().strip() or "MASTER"
        variance = self.quick_variance_combo.currentText()

        success = self.render_api.create_char_template(context, variance)

        if success:
            layer_name = f"{context}_CHAR_{variance}"
            QtWidgets.QMessageBox.information(
                self, "Template Created",
                f"✅ CHAR Template created successfully!\n\n"
                f"Layer: {layer_name}\n"
                f"Collections: geo, light\n"
                f"Sub-collections: matte, visibility"
            )
            self.layer_created.emit(layer_name)
        else:
            QtWidgets.QMessageBox.warning(
                self, "Creation Failed",
                f"❌ Failed to create CHAR template.\n\n"
                f"The layer may already exist or Maya Render Setup is not available."
            )

    def _on_create_atmos_template(self) -> None:
        """Handle ATMOS template creation."""
        context = self.quick_context_edit.text().strip() or "MASTER"
        variance = self.quick_variance_combo.currentText()

        success = self.render_api.create_atmos_template(context, variance)

        if success:
            layer_name = f"{context}_ATMOS_{variance}"
            QtWidgets.QMessageBox.information(
                self, "Template Created",
                f"✅ ATMOS Template created successfully!\n\n"
                f"Layer: {layer_name}\n"
                f"Collections: geo, light\n"
                f"Sub-collections: matte, visibility"
            )
            self.layer_created.emit(layer_name)
        else:
            QtWidgets.QMessageBox.warning(
                self, "Creation Failed",
                f"❌ Failed to create ATMOS template.\n\n"
                f"The layer may already exist or Maya Render Setup is not available."
            )

    def _on_create_fx_template(self) -> None:
        """Handle FX template creation."""
        context = self.quick_context_edit.text().strip() or "MASTER"
        variance = self.quick_variance_combo.currentText()

        success = self.render_api.create_fx_template(context, variance)

        if success:
            layer_name = f"{context}_FX_{variance}"
            QtWidgets.QMessageBox.information(
                self, "Template Created",
                f"✅ FX Template created successfully!\n\n"
                f"Layer: {layer_name}\n"
                f"Collections: geo, light\n"
                f"Sub-collections: matte, visibility"
            )
            self.layer_created.emit(layer_name)
        else:
            QtWidgets.QMessageBox.warning(
                self, "Creation Failed",
                f"❌ Failed to create FX template.\n\n"
                f"The layer may already exist or Maya Render Setup is not available."
            )

    def _on_create_all_templates(self) -> None:
        """Handle batch creation of all standard templates."""
        context = self.quick_context_edit.text().strip() or "MASTER"
        variance = self.quick_variance_combo.currentText()

        # Confirm batch creation
        reply = QtWidgets.QMessageBox.question(
            self, "Create All Templates",
            f"Create all standard templates for context '{context}_{variance}'?\n\n"
            f"This will create:\n"
            f"• {context}_BG_{variance}\n"
            f"• {context}_CHAR_{variance}\n"
            f"• {context}_ATMOS_{variance}\n"
            f"• {context}_FX_{variance}\n\n"
            f"Each with geo/light collections and matte/visibility sub-collections.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes
        )

        if reply != QtWidgets.QMessageBox.Yes:
            return

        # Create all templates
        results = self.render_api.create_all_standard_templates(context, variance)

        # Show results
        successful = [k for k, v in results.items() if v]
        failed = [k for k, v in results.items() if not v]

        message = f"Batch Template Creation Results:\n\n"

        if successful:
            message += f"✅ Successfully Created ({len(successful)}):\n"
            for template_type in successful:
                layer_name = f"{context}_{template_type}_{variance}"
                message += f"  • {layer_name}\n"
                self.layer_created.emit(layer_name)
            message += "\n"

        if failed:
            message += f"❌ Failed to Create ({len(failed)}):\n"
            for template_type in failed:
                layer_name = f"{context}_{template_type}_{variance}"
                message += f"  • {layer_name}\n"
            message += "\n"

        if not results:
            message += "❌ No templates were created.\nMaya Render Setup may not be available."

        # Show appropriate message box
        if failed and not successful:
            QtWidgets.QMessageBox.warning(self, "Batch Creation Failed", message)
        elif failed:
            QtWidgets.QMessageBox.warning(self, "Partial Success", message)
        else:
            QtWidgets.QMessageBox.information(self, "Batch Creation Successful", message)

    def _on_clear_layers(self) -> None:
        """Handle clearing all render layers."""
        # Confirm clear operation
        reply = QtWidgets.QMessageBox.question(
            self, "Clear All Layers",
            "⚠️ Clear all render layers?\n\n"
            "This will delete all render layers except the default layer.\n"
            "This action cannot be undone.\n\n"
            "This will also prevent numeric suffixes when recreating layers.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply != QtWidgets.QMessageBox.Yes:
            return

        try:
            from ...utils import render_layers

            if not render_layers.is_available():
                QtWidgets.QMessageBox.warning(
                    self, "Clear Failed",
                    "❌ Maya Render Setup not available.\n\n"
                    "Cannot clear render layers."
                )
                return

            # Get current layers before clearing
            current_layers = render_layers.list_layers()

            if not current_layers:
                QtWidgets.QMessageBox.information(
                    self, "No Layers to Clear",
                    "ℹ️ No render layers to clear.\n\n"
                    "Only the default render layer exists."
                )
                return

            # Clear layers using improved function
            render_layers.clear_layers(keep_default=True)

            # Verify layers were cleared
            remaining_layers = render_layers.list_layers()
            cleared_count = len(current_layers) - len(remaining_layers)

            QtWidgets.QMessageBox.information(
                self, "Layers Cleared",
                f"✅ Successfully cleared {cleared_count} render layers.\n\n"
                f"Cleared layers:\n" + "\n".join(f"• {layer}" for layer in current_layers) +
                f"\n\nRemaining layers: {remaining_layers if remaining_layers else ['defaultRenderLayer']}"
            )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Clear Failed",
                f"❌ Error clearing render layers:\n\n{str(e)}"
            )
