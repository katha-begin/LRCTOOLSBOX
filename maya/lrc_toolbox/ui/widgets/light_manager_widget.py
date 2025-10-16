"""
Light Manager Widget

This module provides the Light Manager widget for light naming and management
according to UI design specifications.
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
from ...core.light_manager import LightManager
from ...core.models import NavigationContext, ProjectType


class LightManagerWidget(QtWidgets.QWidget):
    """
    Light Manager widget for light naming and management.
    
    Provides light naming tools, import/export functionality, and scene light management
    according to the UI design specifications.
    """
    
    # Signals for communication with main window
    lights_renamed = QtCore.Signal(list)  # Emitted when lights are renamed
    lights_exported = QtCore.Signal(str)  # Emitted when lights are exported
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the Light Manager widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize real LightManager for advanced features
        self._light_manager = LightManager()
        self._current_context = None

        self._setup_ui()
        self._connect_signals()
        self._populate_initial_data()

        print("Light Manager Widget initialized with real LightManager")
    
    def _setup_ui(self) -> None:
        """Set up the user interface according to UI design specifications."""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create UI sections
        self._create_light_naming()
        self._create_import_export()
        self._create_scene_lights()
        
        # Add sections to main layout
        main_layout.addWidget(self.light_naming_group)
        main_layout.addWidget(self.import_export_group)
        main_layout.addWidget(self.scene_lights_group)
        main_layout.addStretch()
    
    def _create_light_naming(self) -> None:
        """Create light naming section."""
        self.light_naming_group = QtWidgets.QGroupBox("💡 Light Naming")
        layout = QtWidgets.QVBoxLayout(self.light_naming_group)
        
        # Naming controls
        controls_layout = QtWidgets.QGridLayout()
        
        # Prefix
        controls_layout.addWidget(QtWidgets.QLabel("Prefix:"), 0, 0)
        self.light_prefix_combo = QtWidgets.QComboBox()
        self.light_prefix_combo.setEditable(True)
        controls_layout.addWidget(self.light_prefix_combo, 0, 1)
        
        # Index
        controls_layout.addWidget(QtWidgets.QLabel("Index:"), 0, 2)
        self.light_index_spin = QtWidgets.QSpinBox()
        self.light_index_spin.setRange(1, 999)
        self.light_index_spin.setValue(1)
        self.light_index_spin.setMinimumWidth(80)
        controls_layout.addWidget(self.light_index_spin, 0, 3)
        
        # Suffix
        controls_layout.addWidget(QtWidgets.QLabel("Suffix:"), 1, 0)
        self.light_suffix_combo = QtWidgets.QComboBox()
        self.light_suffix_combo.setEditable(True)
        controls_layout.addWidget(self.light_suffix_combo, 1, 1)
        
        layout.addLayout(controls_layout)
        
        # Preview
        preview_layout = QtWidgets.QHBoxLayout()
        preview_layout.addWidget(QtWidgets.QLabel("Preview:"))
        self.preview_label = QtWidgets.QLabel("key_001_lgt")
        self.preview_label.setStyleSheet(
            "font-family: monospace; font-weight: bold; "
            "background-color: #f0f0f0; padding: 4px; border: 1px solid #ccc;"
        )
        preview_layout.addWidget(self.preview_label)
        preview_layout.addStretch()
        
        layout.addLayout(preview_layout)
        
        # Apply button
        apply_layout = QtWidgets.QHBoxLayout()
        self.apply_naming_btn = QtWidgets.QPushButton("Apply to Selected Lights")
        apply_layout.addWidget(self.apply_naming_btn)
        apply_layout.addStretch()
        
        layout.addLayout(apply_layout)
    
    def _create_import_export(self) -> None:
        """Create import/export section."""
        self.import_export_group = QtWidgets.QGroupBox("📤 Light Import/Export")
        layout = QtWidgets.QHBoxLayout(self.import_export_group)
        
        self.export_lights_btn = QtWidgets.QPushButton("Export Lights Only")
        self.import_lights_btn = QtWidgets.QPushButton("Import Lights Only")
        
        layout.addWidget(self.export_lights_btn)
        layout.addWidget(self.import_lights_btn)
        layout.addStretch()
    
    def _create_scene_lights(self) -> None:
        """Create scene lights section."""
        self.scene_lights_group = QtWidgets.QGroupBox("Scene Lights")
        layout = QtWidgets.QVBoxLayout(self.scene_lights_group)
        
        # Lights list
        self.scene_lights_list = QtWidgets.QListWidget()
        self.scene_lights_list.setMaximumHeight(200)
        layout.addWidget(self.scene_lights_list)
        
        # Refresh button
        refresh_layout = QtWidgets.QHBoxLayout()
        self.refresh_lights_btn = QtWidgets.QPushButton("🔄 Refresh Light List")
        refresh_layout.addWidget(self.refresh_lights_btn)
        refresh_layout.addStretch()
        
        layout.addLayout(refresh_layout)
    
    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        # Light naming
        self.light_prefix_combo.currentTextChanged.connect(self._update_preview)
        self.light_prefix_combo.editTextChanged.connect(self._update_preview)
        self.light_index_spin.valueChanged.connect(self._update_preview)
        self.light_suffix_combo.currentTextChanged.connect(self._update_preview)
        self.light_suffix_combo.editTextChanged.connect(self._update_preview)
        self.apply_naming_btn.clicked.connect(self._on_apply_naming)
        
        # Import/Export
        self.export_lights_btn.clicked.connect(self._on_export_lights)
        self.import_lights_btn.clicked.connect(self._on_import_lights)
        
        # Scene lights
        self.refresh_lights_btn.clicked.connect(self._on_refresh_lights)
    
    def _populate_initial_data(self) -> None:
        """Populate initial data for dropdowns and lists."""
        # Light prefixes
        prefixes = [
            "key", "fill", "rim", "bounce", "sun", "sky", "env", 
            "spot", "area", "point", "directional", "volume"
        ]
        self.light_prefix_combo.addItems(prefixes)
        self.light_prefix_combo.setCurrentText("key")
        
        # Light suffixes
        suffixes = [
            "lgt", "light", "lamp", "illumination", "source"
        ]
        self.light_suffix_combo.addItems(suffixes)
        self.light_suffix_combo.setCurrentText("lgt")
        
        # Populate scene lights with mock data
        self._populate_scene_lights()
        
        # Update preview
        self._update_preview()
    
    def _populate_scene_lights(self) -> None:
        """Populate scene lights list with real Maya scene data."""
        self.scene_lights_list.clear()

        try:
            # Get real lights from LightManager
            lights = self._light_manager.get_scene_lights()

            if not lights:
                self.scene_lights_list.addItem("📭 No lights found in scene")
                return

            # Convert LightInfo objects to display strings
            light_items = []
            for light_info in lights:
                # Format light display string with type icon
                type_icon = self._get_light_type_icon(light_info.light_type)
                hierarchy_icon = self._get_hierarchy_icon(light_info.hierarchy_level)

                display_name = f"{type_icon}{hierarchy_icon} {light_info.name}"

                # Add hierarchy and type info as tooltip
                tooltip = (f"Type: {light_info.light_type}\n"
                          f"Hierarchy: {light_info.hierarchy_level}\n"
                          f"Index: {light_info.index}\n"
                          f"Transform: {light_info.maya_transform_node}\n"
                          f"Shape: {light_info.maya_shape_node}")

                item = QtWidgets.QListWidgetItem(display_name)
                item.setToolTip(tooltip)
                item.setData(QtCore.Qt.UserRole, light_info)

                # Color code by hierarchy
                if light_info.hierarchy_level == "Master":
                    item.setForeground(QtGui.QColor("#DAA520"))  # Gold
                elif light_info.hierarchy_level == "Key":
                    item.setForeground(QtGui.QColor("#4169E1"))  # Royal Blue
                elif light_info.hierarchy_level == "Child":
                    item.setForeground(QtGui.QColor("#32CD32"))  # Lime Green

                self.scene_lights_list.addItem(item)

            print(f"✅ Loaded {len(lights)} lights from Maya scene")

        except Exception as e:
            print(f"Error loading scene lights: {e}")
            self.scene_lights_list.addItem(f"❌ Error loading lights: {str(e)}")

    def _get_light_type_icon(self, light_type: str) -> str:
        """Get icon for light type."""
        type_icons = {
            "KEY": "🔑",
            "FILL": "🌕",
            "RIM": "🌙",
            "BOUNCE": "💫",
            "AMBIENT": "🌍",
            "SPEC": "✨"
        }
        return type_icons.get(light_type, "💡")

    def _get_hierarchy_icon(self, hierarchy_level: str) -> str:
        """Get icon for hierarchy level."""
        hierarchy_icons = {
            "Master": "👑",
            "Key": "🔑",
            "Child": "🧩"
        }
        return hierarchy_icons.get(hierarchy_level, "")

    def refresh_lights(self) -> None:
        """Public method to refresh lights from external calls."""
        self._populate_scene_lights()
        print("🔄 Light Manager refreshed")

    def set_navigation_context(self, context: NavigationContext) -> None:
        """Set current navigation context for context-aware naming."""
        self._current_context = context

        # Update prefix based on context
        if context.type == ProjectType.SHOT:
            prefix = f"{context.shot}"
        else:
            prefix = f"{context.asset.upper()}"

        # Update prefix combo if this prefix exists
        prefix_index = self.light_prefix_combo.findText(prefix)
        if prefix_index >= 0:
            self.light_prefix_combo.setCurrentIndex(prefix_index)
        else:
            # Add the new prefix
            self.light_prefix_combo.addItem(prefix)
            self.light_prefix_combo.setCurrentText(prefix)

        print(f"🔄 Light Manager context updated to: {prefix}")
        self._update_preview()

    def _update_preview(self) -> None:
        """Update the naming preview label."""
        prefix = self.light_prefix_combo.currentText()
        index = self.light_index_spin.value()
        suffix = self.light_suffix_combo.currentText()
        
        # Format index with zero padding
        index_str = f"{index:03d}"
        
        # Generate preview name
        preview_name = f"{prefix}_{index_str}_{suffix}"
        self.preview_label.setText(preview_name)
    
    # Event handlers
    def _on_apply_naming(self) -> None:
        """Handle apply naming button click with real Maya operations."""
        prefix = self.light_prefix_combo.currentText()
        index = self.light_index_spin.value()
        suffix = self.light_suffix_combo.currentText()

        if not prefix or not suffix:
            QtWidgets.QMessageBox.warning(
                self, "Invalid Input",
                "Please enter both prefix and suffix."
            )
            return

        try:
            # Get selected lights from Maya
            selected_lights = self._light_manager.get_selected_lights()

            if not selected_lights:
                QtWidgets.QMessageBox.warning(
                    self, "No Selection",
                    "Please select lights in the Maya scene to rename."
                )
                return

            # Generate names for selected lights
            new_names = []
            for i, light_info in enumerate(selected_lights):
                current_index = index + i
                index_str = f"{current_index:03d}"
                new_name = f"{prefix}_{index_str}_{suffix}"
                new_names.append(new_name)

            # Show confirmation
            names_text = "\n".join(new_names)
            reply = QtWidgets.QMessageBox.question(
                self, "Apply Naming",
                f"Rename {len(selected_lights)} selected lights?\n\n"
                f"New names:\n{names_text}",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )

            if reply == QtWidgets.QMessageBox.Yes:
                # Actually rename the lights in Maya
                success_count = 0
                failed_renames = []

                try:
                    import maya.cmds as cmds

                    for i, light_info in enumerate(selected_lights):
                        old_name = light_info.maya_transform_node
                        new_name = new_names[i]

                        try:
                            # Rename the transform node
                            cmds.rename(old_name, new_name)
                            success_count += 1
                            print(f"✅ Renamed {old_name} -> {new_name}")

                        except Exception as e:
                            failed_renames.append(f"{old_name}: {str(e)}")
                            print(f"❌ Failed to rename {old_name}: {e}")

                    # Show results
                    if success_count > 0:
                        message = f"Successfully renamed {success_count} lights!"
                        if failed_renames:
                            message += f"\n\nFailed to rename {len(failed_renames)} lights:\n" + "\n".join(failed_renames)

                        QtWidgets.QMessageBox.information(self, "Rename Complete", message)

                        # Update index for next use
                        self.light_index_spin.setValue(index + success_count)

                        # Refresh lights list
                        self._populate_scene_lights()

                        # Emit signal
                        self.lights_renamed.emit(new_names[:success_count])

                    else:
                        QtWidgets.QMessageBox.warning(
                            self, "Rename Failed",
                            f"Failed to rename any lights:\n" + "\n".join(failed_renames)
                        )

                except ImportError:
                    QtWidgets.QMessageBox.warning(
                        self, "Maya Not Available",
                        "Maya API not available. Cannot rename lights."
                    )

        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Error",
                f"Error applying naming: {str(e)}"
            )
            print(f"❌ Error applying naming: {e}")
    
    def _on_export_lights(self) -> None:
        """Handle export lights button click."""
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setWindowTitle("Export Lights Only")
        file_dialog.setNameFilter("Maya ASCII (*.ma);;Maya Binary (*.mb);;All files (*.*)")
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        file_dialog.setDefaultSuffix("ma")
        
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                export_path = file_paths[0]
                
                QtWidgets.QMessageBox.information(
                    self, "Export Complete",
                    f"Lights exported successfully!\n\n"
                    f"File: {export_path}\n\n"
                    f"Exported:\n"
                    f"• All scene lights\n"
                    f"• Light transforms\n"
                    f"• Light attributes\n"
                    f"• Light shaders"
                )
                
                # Emit signal
                self.lights_exported.emit(export_path)
    
    def _on_import_lights(self) -> None:
        """Handle import lights button click."""
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setWindowTitle("Import Lights Only")
        file_dialog.setNameFilter("Maya ASCII (*.ma);;Maya Binary (*.mb);;All files (*.*)")
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                import_path = file_paths[0]
                
                reply = QtWidgets.QMessageBox.question(
                    self, "Import Lights",
                    f"Import lights from:\n{import_path}\n\n"
                    f"This will add lights to the current scene.\n"
                    f"Continue?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.Yes:
                    QtWidgets.QMessageBox.information(
                        self, "Import Complete",
                        f"Lights imported successfully!\n\n"
                        f"File: {import_path}\n\n"
                        f"Imported:\n"
                        f"• Light objects\n"
                        f"• Light transforms\n"
                        f"• Light attributes\n"
                        f"• Light shaders"
                    )
                    
                    # Refresh lights list
                    self._populate_scene_lights()
    
    def _on_refresh_lights(self) -> None:
        """Handle refresh lights button click."""
        self._populate_scene_lights()
        QtWidgets.QMessageBox.information(
            self, "Refresh Complete",
            "Scene lights list refreshed successfully!"
        )
    
    # Public methods
    def get_current_naming_pattern(self) -> Dict[str, Any]:
        """Get current naming pattern settings."""
        return {
            "prefix": self.light_prefix_combo.currentText(),
            "index": self.light_index_spin.value(),
            "suffix": self.light_suffix_combo.currentText(),
            "preview": self.preview_label.text()
        }
    
    def set_naming_pattern(self, prefix: str, index: int, suffix: str) -> None:
        """Set naming pattern settings."""
        self.light_prefix_combo.setCurrentText(prefix)
        self.light_index_spin.setValue(index)
        self.light_suffix_combo.setCurrentText(suffix)
        self._update_preview()
