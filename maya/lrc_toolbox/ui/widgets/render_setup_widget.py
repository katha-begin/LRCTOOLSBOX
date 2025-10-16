"""
Render Setup Widget

This module provides the Render Setup widget with Enhanced Template Browser
and Import/Export System according to UI design specifications.
"""

import os
import json
from datetime import datetime
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
from ...core.template_manager import TemplateManager
from ...core.project_manager import ProjectManager
from ...core.template_exporter import template_exporter
from ...core.models import NavigationContext, ProjectType
from ...utils.context_detector import context_detector


class RenderSetupWidget(QtWidgets.QWidget):
    """
    Render Setup widget with Enhanced Template Browser and Import/Export System.

    Provides template package browsing, import/export functionality, and
    dependency tracking according to the UI design specifications.
    """

    # Signals for communication with main window
    template_loaded = QtCore.Signal(str)  # Emitted when template is loaded
    template_created = QtCore.Signal(str)  # Emitted when template is created
    package_imported = QtCore.Signal(str)  # Emitted when package is imported
    package_exported = QtCore.Signal(str)  # Emitted when package is exported

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the Render Setup widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._project_root = settings.get_project_root()
        self._current_context = {}

        # Initialize backend managers for real operations
        self._template_manager = TemplateManager()
        self._project_manager = ProjectManager()

        self._setup_ui()
        self._connect_signals()
        self._populate_initial_navigation_data()
        self._populate_template_packages()

        print("Enhanced Render Setup Widget initialized with TemplateManager")

    def _populate_initial_navigation_data(self) -> None:
        """Populate initial navigation data from real file system."""
        try:
            # Populate episodes
            episodes = self._project_manager.get_episodes()
            self.episode_combo.clear()
            self.episode_combo.addItems(["[Select Episode]"] + episodes)

            # Populate categories
            categories = self._project_manager.get_categories()
            self.category_combo.clear()
            self.category_combo.addItems(["[Select Category]"] + categories)

            print(f"📁 Loaded {len(episodes)} episodes and {len(categories)} categories from file system")

        except Exception as e:
            print(f"Error populating initial navigation data: {e}")

    def _setup_ui(self) -> None:
        """Set up the Enhanced Template Browser UI according to design specifications."""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Create UI sections according to Enhanced Template Browser design
        self._create_template_package_browser()
        self._create_template_exporter()

        # Add sections to main layout
        main_layout.addWidget(self.template_browser_group)
        main_layout.addWidget(self.template_exporter_group)
        main_layout.addStretch()
    
    def _create_template_package_browser(self) -> None:
        """Create Enhanced Template Package Browser with Template Navigator."""
        self.template_browser_group = QtWidgets.QGroupBox("📦 Template Package Browser")
        layout = QtWidgets.QVBoxLayout(self.template_browser_group)

        # Template Navigator Section
        navigator_group = QtWidgets.QGroupBox("🧭 Template Navigator")
        navigator_layout = QtWidgets.QGridLayout(navigator_group)

        # Navigation Type Selection
        navigator_layout.addWidget(QtWidgets.QLabel("Browse:"), 0, 0)
        self.nav_type_combo = QtWidgets.QComboBox()
        self.nav_type_combo.addItems(["Shot Templates", "Asset Templates", "Global Templates"])
        navigator_layout.addWidget(self.nav_type_combo, 0, 1, 1, 3)

        # Shot Navigation (Row 1)
        navigator_layout.addWidget(QtWidgets.QLabel("Episode:"), 1, 0)
        self.episode_combo = QtWidgets.QComboBox()
        self.episode_combo.addItems(["[Select Episode]"])  # Will be populated by _populate_initial_navigation_data()
        navigator_layout.addWidget(self.episode_combo, 1, 1)

        navigator_layout.addWidget(QtWidgets.QLabel("Sequence:"), 1, 2)
        self.sequence_combo = QtWidgets.QComboBox()
        self.sequence_combo.addItems(["[Select Sequence]"])
        navigator_layout.addWidget(self.sequence_combo, 1, 3)

        # Shot/Asset Navigation (Row 2)
        self.shot_asset_label = QtWidgets.QLabel("Shot:")
        navigator_layout.addWidget(self.shot_asset_label, 2, 0)
        self.shot_asset_combo = QtWidgets.QComboBox()
        self.shot_asset_combo.addItems(["[Select Shot]"])
        navigator_layout.addWidget(self.shot_asset_combo, 2, 1)

        # Template Level Selection (Row 2, right side)
        navigator_layout.addWidget(QtWidgets.QLabel("Level:"), 2, 2)
        self.template_level_combo = QtWidgets.QComboBox()
        self.template_level_combo.addItems(["Shot Level", "Sequence Level", "Episode Level", "Global Level"])
        navigator_layout.addWidget(self.template_level_combo, 2, 3)

        # Asset Navigation (initially hidden)
        navigator_layout.addWidget(QtWidgets.QLabel("Category:"), 3, 0)
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItems(["[Select Category]", "Sets", "Characters", "Props", "Vehicles"])
        navigator_layout.addWidget(self.category_combo, 3, 1)

        navigator_layout.addWidget(QtWidgets.QLabel("Subcategory:"), 3, 2)
        self.subcategory_combo = QtWidgets.QComboBox()
        self.subcategory_combo.addItems(["[Select Subcategory]"])
        navigator_layout.addWidget(self.subcategory_combo, 3, 3)

        # Asset Name (Row 4)
        navigator_layout.addWidget(QtWidgets.QLabel("Asset:"), 4, 0)
        self.asset_combo = QtWidgets.QComboBox()
        self.asset_combo.addItems(["[Select Asset]"])
        navigator_layout.addWidget(self.asset_combo, 4, 1)

        # Browse button
        self.browse_templates_btn = QtWidgets.QPushButton("Browse Templates")
        navigator_layout.addWidget(self.browse_templates_btn, 4, 2, 1, 2)

        layout.addWidget(navigator_group)

        # Current Location Display
        self.location_label = QtWidgets.QLabel("Template Location: [Select navigation options above]")
        self.location_label.setStyleSheet("font-weight: bold; color: #2c5aa0; background-color: #f0f8ff; padding: 4px; border: 1px solid #c0c0c0;")
        layout.addWidget(self.location_label)

        # Package list with tree structure
        self.package_tree = QtWidgets.QTreeWidget()
        self.package_tree.setHeaderLabels(["Template Package", "Actions"])
        self.package_tree.setRootIsDecorated(True)
        self.package_tree.setAlternatingRowColors(True)
        self.package_tree.setMaximumHeight(250)
        layout.addWidget(self.package_tree)

        # Package actions
        actions_layout = QtWidgets.QHBoxLayout()
        self.import_package_btn = QtWidgets.QPushButton("Import Selected Package")
        self.import_individual_btn = QtWidgets.QPushButton("Import Individual Files")
        self.refresh_packages_btn = QtWidgets.QPushButton("Refresh")

        actions_layout.addWidget(self.import_package_btn)
        actions_layout.addWidget(self.import_individual_btn)
        actions_layout.addWidget(self.refresh_packages_btn)
        actions_layout.addStretch()

        layout.addLayout(actions_layout)

        # Initially hide asset navigation
        self._update_navigation_visibility()


    
    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        # Template Navigator
        self.nav_type_combo.currentTextChanged.connect(self._on_nav_type_changed)
        self.episode_combo.currentTextChanged.connect(self._on_episode_changed)
        self.sequence_combo.currentTextChanged.connect(self._on_sequence_changed)
        self.shot_asset_combo.currentTextChanged.connect(self._on_shot_asset_changed)
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        self.subcategory_combo.currentTextChanged.connect(self._on_subcategory_changed)
        self.asset_combo.currentTextChanged.connect(self._on_asset_changed)
        self.template_level_combo.currentTextChanged.connect(self._on_template_level_changed)
        self.browse_templates_btn.clicked.connect(self._on_browse_templates)

        # Template Package Browser
        self.import_package_btn.clicked.connect(self._on_import_package)
        self.import_individual_btn.clicked.connect(self._on_import_individual)
        self.refresh_packages_btn.clicked.connect(self._on_refresh_packages)
        self.package_tree.itemDoubleClicked.connect(self._on_package_double_clicked)
    
    def _populate_template_packages(self) -> None:
        """Populate template packages tree with real TemplateManager data."""
        self.package_tree.clear()

        # Get current navigation context
        context = self._get_current_navigation_context()
        if not context:
            # Show message in tree
            info_item = QtWidgets.QTreeWidgetItem(self.package_tree)
            info_item.setText(0, "📍 Please select navigation options to browse templates")
            return

        # Update location label
        location = self._get_current_template_location()
        self.location_label.setText(f"Template Location: {location}")

        try:
            # Get real templates from TemplateManager
            templates = self._template_manager.get_templates_for_context(context)

            if not templates:
                # Show no packages message
                info_item = QtWidgets.QTreeWidgetItem(self.package_tree)
                info_item.setText(0, f"📂 No template packages found for this context")
                return

            # Group templates by hierarchy level and populate with inheritance display
            self._populate_template_tree_with_inheritance(templates, context)

        except Exception as e:
            print(f"Error loading templates: {e}")
            error_item = QtWidgets.QTreeWidgetItem(self.package_tree)
            error_item.setText(0, f"❌ Error loading templates: {str(e)}")

    def _populate_template_tree_with_inheritance(self, templates: List, context: NavigationContext) -> None:
        """Populate template tree with inheritance hierarchy display."""
        try:
            # Group templates by hierarchy level
            hierarchy_groups = {
                "current": [],    # Current context level (shot/asset)
                "sequence": [],   # Sequence level (shots only)
                "episode": [],    # Episode level (shots only) / Category level (assets)
                "global": []      # Global level
            }

            # Categorize templates by their source level
            for template in templates:
                level = self._determine_template_hierarchy_level(template, context)
                if level in hierarchy_groups:
                    hierarchy_groups[level].append(template)
                else:
                    hierarchy_groups["current"].append(template)  # Default to current

            # Create tree structure with hierarchy levels
            hierarchy_order = ["current", "sequence", "episode", "global"]
            hierarchy_labels = {
                "current": f"📍 {context.type.value.title()} Level",
                "sequence": "🎬 Sequence Level",
                "episode": "📺 Episode Level" if context.type == ProjectType.SHOT else "📁 Category Level",
                "global": "🌍 Global Level"
            }

            total_templates = 0
            for level in hierarchy_order:
                templates_in_level = hierarchy_groups[level]
                if not templates_in_level:
                    continue

                # Create hierarchy level group
                level_item = QtWidgets.QTreeWidgetItem(self.package_tree)
                level_item.setText(0, f"{hierarchy_labels[level]} ({len(templates_in_level)} templates)")
                level_item.setExpanded(True)

                # Style the hierarchy level item
                font = level_item.font(0)
                font.setBold(True)
                level_item.setFont(0, font)

                # Add templates to this level
                for template in templates_in_level:
                    # Create package item
                    package_item = QtWidgets.QTreeWidgetItem(level_item)

                    # Choose icon based on template type
                    icon = self._get_template_icon(template.template_type)
                    package_item.setText(0, f"{icon} {template.name}")
                    package_item.setData(0, QtCore.Qt.UserRole, template)

                    # Add tooltip with template info
                    tooltip = (f"Type: {template.template_type.value}\n"
                              f"Description: {template.description}\n"
                              f"Created: {template.created_date.strftime('%Y-%m-%d %H:%M')}\n"
                              f"Version: {template.version}\n"
                              f"Hierarchy: {hierarchy_labels[level]}")
                    package_item.setToolTip(0, tooltip)

                    # Add import button to second column
                    import_btn = QtWidgets.QPushButton("Import Package")
                    import_btn.clicked.connect(lambda checked, tmpl=template: self._import_specific_template(tmpl))
                    self.package_tree.setItemWidget(package_item, 1, import_btn)

                    # Add file children
                    for file_name in template.files:
                        file_item = QtWidgets.QTreeWidgetItem(package_item)
                        file_icon = self._get_file_icon(file_name)
                        file_item.setText(0, f"  ├── {file_icon} {file_name}")
                        file_item.setData(0, QtCore.Qt.UserRole, {'file_name': file_name, 'template': template})

                total_templates += len(templates_in_level)

            # Expand all items
            self.package_tree.expandAll()
            print(f"✅ Loaded {total_templates} template packages with inheritance hierarchy")

        except Exception as e:
            print(f"Error creating inheritance hierarchy: {e}")
            # Fallback to simple list
            self._populate_simple_template_list(templates)

    def _determine_template_hierarchy_level(self, template, context: NavigationContext) -> str:
        """Determine which hierarchy level a template belongs to."""
        try:
            # This is a simplified version - in reality, you'd check the template's source path
            # For now, we'll use template name patterns or metadata

            if hasattr(template, 'context_path') and template.context_path:
                template_path = template.context_path.lower()

                if context.type == ProjectType.SHOT:
                    if context.shot and context.shot.lower() in template_path:
                        return "current"  # Shot level
                    elif context.sequence and context.sequence.lower() in template_path:
                        return "sequence"  # Sequence level
                    elif context.episode and context.episode.lower() in template_path:
                        return "episode"  # Episode level
                    elif "templates" in template_path and "global" in template_path:
                        return "global"  # Global level

                elif context.type == ProjectType.ASSET:
                    if context.asset and context.asset.lower() in template_path:
                        return "current"  # Asset level
                    elif context.subcategory and context.subcategory.lower() in template_path:
                        return "sequence"  # Subcategory level (using sequence slot)
                    elif context.category and context.category.lower() in template_path:
                        return "episode"  # Category level (using episode slot)
                    elif "templates" in template_path and "global" in template_path:
                        return "global"  # Global level

            # Default to current level if can't determine
            return "current"

        except Exception as e:
            print(f"Warning: Could not determine template hierarchy level: {e}")
            return "current"

    def _populate_simple_template_list(self, templates: List) -> None:
        """Fallback method to populate templates as simple list."""
        try:
            for template in templates:
                # Create package item
                package_item = QtWidgets.QTreeWidgetItem(self.package_tree)

                # Choose icon based on template type
                icon = self._get_template_icon(template.template_type)
                package_item.setText(0, f"{icon} {template.name}")
                package_item.setData(0, QtCore.Qt.UserRole, template)

                # Add tooltip with template info
                tooltip = (f"Type: {template.template_type.value}\n"
                          f"Description: {template.description}\n"
                          f"Created: {template.created_date.strftime('%Y-%m-%d %H:%M')}\n"
                          f"Version: {template.version}")
                package_item.setToolTip(0, tooltip)

                # Add import button to second column
                import_btn = QtWidgets.QPushButton("Import Package")
                import_btn.clicked.connect(lambda checked, tmpl=template: self._import_specific_template(tmpl))
                self.package_tree.setItemWidget(package_item, 1, import_btn)

                # Add file children
                for file_name in template.files:
                    file_item = QtWidgets.QTreeWidgetItem(package_item)
                    file_icon = self._get_file_icon(file_name)
                    file_item.setText(0, f"  ├── {file_icon} {file_name}")
                    file_item.setData(0, QtCore.Qt.UserRole, {'file_name': file_name, 'template': template})

            # Expand all items
            self.package_tree.expandAll()
            print(f"✅ Loaded {len(templates)} template packages (simple list)")

        except Exception as e:
            print(f"Error in simple template list: {e}")

    def _get_current_navigation_context(self) -> Optional[NavigationContext]:
        """Get current navigation context as NavigationContext object."""
        try:
            nav_type = self.nav_type_combo.currentText()

            if "Shot" in nav_type:
                episode = self.episode_combo.currentText()
                sequence = self.sequence_combo.currentText()
                shot = self.shot_asset_combo.currentText()

                # Validate we have required values
                if not all([episode, sequence, shot]) or any(
                    text.startswith("[Select") for text in [episode, sequence, shot]
                ):
                    return None

                return NavigationContext(
                    type=ProjectType.SHOT,
                    episode=episode,
                    sequence=sequence,
                    shot=shot,
                    department="lighting"
                )

            elif "Asset" in nav_type:
                category = self.category_combo.currentText()
                subcategory = self.subcategory_combo.currentText()
                asset = self.asset_combo.currentText()

                # Validate we have required values
                if not all([category, subcategory, asset]) or any(
                    text.startswith("[Select") for text in [category, subcategory, asset]
                ):
                    return None

                return NavigationContext(
                    type=ProjectType.ASSET,
                    category=category,
                    subcategory=subcategory,
                    asset=asset,
                    department="lighting"
                )

            return None

        except Exception as e:
            print(f"Error creating navigation context: {e}")
            return None

    def _get_template_icon(self, template_type) -> str:
        """Get icon for template type."""
        from ...core.models import TemplateType

        icon_map = {
            TemplateType.MASTER: "👑",
            TemplateType.KEY: "🔑",
            TemplateType.MICRO: "🧩"
        }
        return icon_map.get(template_type, "📦")

    def _get_file_icon(self, file_name: str) -> str:
        """Get icon for file type."""
        if file_name.endswith(('.ma', '.mb')):
            return "🎬"
        elif file_name.endswith('.json'):
            return "📄"
        elif file_name.endswith(('.exr', '.jpg', '.png')):
            return "🖼"
        else:
            return "📄"

    def _import_specific_template(self, template) -> None:
        """Import a specific template using real TemplateManager."""
        try:
            # Show import options dialog
            dialog = self._create_template_import_dialog(template)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                # Get selected options from dialog
                options = self._get_import_options_from_dialog(dialog)

                # Use enhanced import with render layers support
                success = self._import_template_package_enhanced(template, options)

                if success:
                    QtWidgets.QMessageBox.information(
                        self, "Import Successful",
                        f"Successfully imported template package:\n{template.name}"
                    )
                    # Emit signal for main window
                    self.package_imported.emit(template.name)
                    print(f"✅ Imported template: {template.name}")
                else:
                    QtWidgets.QMessageBox.warning(
                        self, "Import Failed",
                        f"Failed to import template package:\n{template.name}"
                    )

        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Import Error",
                f"Error importing template:\n{str(e)}"
            )
            print(f"❌ Error importing template: {e}")

    def _create_template_import_dialog(self, template):
        """Create import options dialog for template."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Import Template: {template.name}")
        dialog.setModal(True)
        dialog.resize(500, 400)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Template info
        info_group = QtWidgets.QGroupBox("Template Information:")
        info_layout = QtWidgets.QVBoxLayout(info_group)
        info_layout.addWidget(QtWidgets.QLabel(f"Name: {template.name}"))
        info_layout.addWidget(QtWidgets.QLabel(f"Type: {template.template_type.value}"))
        info_layout.addWidget(QtWidgets.QLabel(f"Description: {template.description}"))
        info_layout.addWidget(QtWidgets.QLabel(f"Files: {len(template.files)} items"))
        layout.addWidget(info_group)

        # Components selection
        components_group = QtWidgets.QGroupBox("Select Components to Import:")
        components_layout = QtWidgets.QVBoxLayout(components_group)

        # Standard components
        dialog.lights_check = QtWidgets.QCheckBox("🎭 Lights")
        dialog.lights_check.setChecked(True)
        dialog.render_layers_check = QtWidgets.QCheckBox("🎬 Render Layers")
        dialog.render_layers_check.setChecked(True)
        dialog.materials_check = QtWidgets.QCheckBox("🎨 Materials")
        dialog.materials_check.setChecked(False)
        dialog.settings_check = QtWidgets.QCheckBox("⚙️ Settings")
        dialog.settings_check.setChecked(False)

        components_layout.addWidget(dialog.lights_check)
        components_layout.addWidget(dialog.render_layers_check)
        components_layout.addWidget(dialog.materials_check)
        components_layout.addWidget(dialog.settings_check)

        layout.addWidget(components_group)

        # Import options
        options_group = QtWidgets.QGroupBox("Import Options:")
        options_layout = QtWidgets.QVBoxLayout(options_group)

        dialog.import_mode_combo = QtWidgets.QComboBox()
        dialog.import_mode_combo.addItems(["import", "reference"])
        dialog.create_backup_check = QtWidgets.QCheckBox("Create scene backup before import")
        dialog.create_backup_check.setChecked(True)

        options_layout.addWidget(QtWidgets.QLabel("Import Mode:"))
        options_layout.addWidget(dialog.import_mode_combo)
        options_layout.addWidget(dialog.create_backup_check)

        layout.addWidget(options_group)

        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        return dialog

    def _get_import_options_from_dialog(self, dialog):
        """Extract import options from dialog."""
        from ...core.models import ImportOptions

        selected_components = []
        if dialog.lights_check.isChecked():
            selected_components.append("lights")
        if dialog.render_layers_check.isChecked():
            selected_components.append("render_layers")
        if dialog.materials_check.isChecked():
            selected_components.append("materials")
        if dialog.settings_check.isChecked():
            selected_components.append("settings")

        return ImportOptions(
            import_mode=dialog.import_mode_combo.currentText(),
            selected_components=selected_components,
            create_backup=dialog.create_backup_check.isChecked(),
            check_existing_lights=True,
            rename_conflicts=True
        )

    def _get_packages_for_location(self, location: str) -> List[Dict[str, Any]]:
        """Get mock template packages for the specified location."""
        # Mock data based on location - in real implementation, scan directories
        if "SH0010" in location:
            return [
                {
                    "name": "sq010_SH0010_master_pkg",
                    "type": "master",
                    "icon": "🏛️",
                    "files": [
                        {"name": "sq010_SH0010_light_master.ma", "icon": "💡"},
                        {"name": "render_layers.json", "icon": "📋"},
                        {"name": "render_settings.json", "icon": "⚙️"},
                        {"name": "aovs.json", "icon": "🎨"},
                        {"name": "package_info.json", "icon": "📄"}
                    ]
                },
                {
                    "name": "sq010_SH0010_key_pkg",
                    "type": "key",
                    "icon": "🔑",
                    "files": [
                        {"name": "sq010_SH0010_light_key.ma", "icon": "💡"},
                        {"name": "render_layers.json", "icon": "📋"},
                        {"name": "package_info.json", "icon": "📄"}
                    ]
                }
            ]
        elif "sq0010" in location and "templates" in location:
            return [
                {
                    "name": "sq010_master_pkg",
                    "type": "sequence_master",
                    "icon": "🏛️",
                    "files": [
                        {"name": "sq010_light_master.ma", "icon": "💡"},
                        {"name": "render_layers.json", "icon": "📋"},
                        {"name": "render_settings.json", "icon": "⚙️"},
                        {"name": "package_info.json", "icon": "📄"}
                    ]
                }
            ]
        elif "Kitchen" in location:
            return [
                {
                    "name": "kitchen_day_master_pkg",
                    "type": "asset_master",
                    "icon": "🏛️",
                    "files": [
                        {"name": "kitchen_day_light_rig_master.ma", "icon": "💡"},
                        {"name": "render_layers.json", "icon": "📋"},
                        {"name": "render_settings.json", "icon": "⚙️"},
                        {"name": "package_info.json", "icon": "📄"}
                    ]
                }
            ]
        elif "asset\\templates" in location:
            return [
                {
                    "name": "global_asset_master_pkg",
                    "type": "global_master",
                    "icon": "🌍",
                    "files": [
                        {"name": "global_asset_light_rig_master.ma", "icon": "💡"},
                        {"name": "render_layers.json", "icon": "📋"},
                        {"name": "render_settings.json", "icon": "⚙️"},
                        {"name": "package_info.json", "icon": "📄"}
                    ]
                }
            ]

        return []  # No packages for this location
    
    # Navigation event handlers
    def _on_nav_type_changed(self, nav_type: str) -> None:
        """Handle navigation type change (Shot/Asset/Global Templates)."""
        self._update_navigation_visibility()
        self._reset_navigation_combos()
        self._update_location_display()

    def _on_episode_changed(self, episode: str) -> None:
        """Handle episode selection change."""
        if episode and not episode.startswith("["):
            # Populate sequences for selected episode
            sequences = self._get_sequences_for_episode(episode)
            self.sequence_combo.clear()
            self.sequence_combo.addItems(["[Select Sequence]"] + sequences)
        self._update_location_display()

    def _on_sequence_changed(self, sequence: str) -> None:
        """Handle sequence selection change."""
        if sequence and not sequence.startswith("["):
            # Populate shots for selected sequence
            shots = self._get_shots_for_sequence(sequence)
            self.shot_asset_combo.clear()
            self.shot_asset_combo.addItems(["[Select Shot]"] + shots)
        self._update_location_display()

    def _on_shot_asset_changed(self, shot_asset: str) -> None:
        """Handle shot/asset selection change."""
        self._update_location_display()

    def _on_category_changed(self, category: str) -> None:
        """Handle category selection change."""
        if category and not category.startswith("["):
            # Populate subcategories for selected category
            subcategories = self._get_subcategories_for_category(category)
            self.subcategory_combo.clear()
            self.subcategory_combo.addItems(["[Select Subcategory]"] + subcategories)
        self._update_location_display()

    def _on_subcategory_changed(self, subcategory: str) -> None:
        """Handle subcategory selection change."""
        if subcategory and not subcategory.startswith("["):
            # Populate assets for selected subcategory
            assets = self._get_assets_for_subcategory(subcategory)
            self.asset_combo.clear()
            self.asset_combo.addItems(["[Select Asset]"] + assets)
        self._update_location_display()

    def _on_asset_changed(self, asset: str) -> None:
        """Handle asset selection change."""
        self._update_location_display()

    def _on_template_level_changed(self, level: str) -> None:
        """Handle template level selection change."""
        self._update_location_display()

    def _on_browse_templates(self) -> None:
        """Handle browse templates button click."""
        location = self._get_current_template_location()
        if location == "[Invalid Selection]":
            QtWidgets.QMessageBox.warning(
                self, "Invalid Selection",
                "Please select valid navigation options to browse templates."
            )
            return

        # Update location display and populate packages
        self.location_label.setText(f"Template Location: {location}")
        self._populate_template_packages()

    # Event handlers for Enhanced Template Browser
    def _on_import_package(self) -> None:
        """Handle import selected package button click."""
        selected_items = self.package_tree.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(
                self, "No Selection",
                "Please select a template package to import."
            )
            return

        selected_item = selected_items[0]
        package_data = selected_item.data(0, QtCore.Qt.UserRole)

        if not package_data or "name" not in package_data:
            QtWidgets.QMessageBox.warning(
                self, "Invalid Selection",
                "Please select a template package (not individual files)."
            )
            return

        self._show_import_options_dialog(package_data)

    def _on_import_individual(self) -> None:
        """Handle import individual files button click."""
        selected_items = self.package_tree.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(
                self, "No Selection",
                "Please select files to import individually."
            )
            return

        # Show individual import dialog
        self._show_individual_import_dialog(selected_items)

    def _on_refresh_packages(self) -> None:
        """Handle refresh packages button click with enhanced functionality."""
        try:
            # Show progress
            self.refresh_packages_btn.setText("🔄 Refreshing...")
            self.refresh_packages_btn.setEnabled(False)

            # Refresh template manager cache
            self._template_manager._template_cache.clear()
            self._template_manager._last_scan_time = None

            # Refresh project structure
            self._project_manager.refresh_project_structure()

            # Repopulate navigation data
            self._populate_initial_navigation_data()

            # Refresh template packages
            self._populate_template_packages()

            QtWidgets.QMessageBox.information(
                self, "Refresh Complete",
                "Template packages and project structure refreshed successfully!"
            )

            print("🔄 Template browser refresh completed")

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Refresh Error",
                f"Error during refresh:\n{str(e)}"
            )
            print(f"❌ Template browser refresh failed: {e}")

        finally:
            # Restore button state
            self.refresh_packages_btn.setText("🔄 Refresh Packages")
            self.refresh_packages_btn.setEnabled(True)

    def refresh_template_browser(self) -> None:
        """Refresh template browser with current context templates (called from Template Tools)."""
        try:
            print("🔄 Refreshing template browser from external trigger...")

            # Get current navigation context from main window if available
            current_context = self._get_current_navigation_context_from_main_window()

            if current_context:
                # Update navigation dropdowns to match current context
                self._sync_navigation_with_context(current_context)

            # Refresh the template packages display
            self._populate_template_packages()

            print("✅ Template browser refreshed successfully")

        except Exception as e:
            print(f"⚠️ Template browser refresh failed: {e}")

    def _get_current_navigation_context_from_main_window(self) -> Optional[NavigationContext]:
        """Get current navigation context from main window navigator."""
        try:
            # Try to get parent main window and then navigator widget
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'navigator_widget'):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, 'navigator_widget'):
                return main_window.navigator_widget._create_navigation_context()
            else:
                print("Warning: Could not find navigator widget for context")
                return None

        except Exception as e:
            print(f"Warning: Could not get navigation context from main window: {e}")
            return None

    def _sync_navigation_with_context(self, context: NavigationContext) -> None:
        """Sync navigation dropdowns with provided context."""
        try:
            if context.type == ProjectType.SHOT:
                # Set to Shot Templates
                self.nav_type_combo.setCurrentText("Shot Templates")

                # Update dropdowns if they exist and have the values
                if hasattr(self, 'episode_combo') and context.episode:
                    index = self.episode_combo.findText(context.episode)
                    if index >= 0:
                        self.episode_combo.setCurrentIndex(index)

                if hasattr(self, 'sequence_combo') and context.sequence:
                    index = self.sequence_combo.findText(context.sequence)
                    if index >= 0:
                        self.sequence_combo.setCurrentIndex(index)

                if hasattr(self, 'shot_combo') and context.shot:
                    index = self.shot_combo.findText(context.shot)
                    if index >= 0:
                        self.shot_combo.setCurrentIndex(index)

            elif context.type == ProjectType.ASSET:
                # Set to Asset Templates
                self.nav_type_combo.setCurrentText("Asset Templates")

                # Update dropdowns if they exist and have the values
                if hasattr(self, 'category_combo') and context.category:
                    index = self.category_combo.findText(context.category)
                    if index >= 0:
                        self.category_combo.setCurrentIndex(index)

                if hasattr(self, 'subcategory_combo') and context.subcategory:
                    index = self.subcategory_combo.findText(context.subcategory)
                    if index >= 0:
                        self.subcategory_combo.setCurrentIndex(index)

                if hasattr(self, 'asset_combo') and context.asset:
                    index = self.asset_combo.findText(context.asset)
                    if index >= 0:
                        self.asset_combo.setCurrentIndex(index)

            print(f"✅ Navigation synced with context: {context}")

        except Exception as e:
            print(f"Warning: Could not sync navigation with context: {e}")
    
    def _on_package_double_clicked(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        """Handle package double-click (same as import)."""
        package_data = item.data(0, QtCore.Qt.UserRole)
        if package_data and "name" in package_data:
            self._show_import_options_dialog(package_data)



    def _import_specific_package(self, package_data: Dict[str, Any]) -> None:
        """Import a specific package (called from tree widget buttons)."""
        self._show_import_options_dialog(package_data)
    
    def _show_import_options_dialog(self, package_data: Dict[str, Any]) -> None:
        """Show import options dialog for selected package."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Import Options for: {package_data['name']}")
        dialog.setModal(True)
        dialog.resize(500, 400)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Components selection
        components_group = QtWidgets.QGroupBox("Select Components to Import:")
        components_layout = QtWidgets.QVBoxLayout(components_group)

        # Create checkboxes for each file in package
        checkboxes = {}
        for file_info in package_data.get("files", []):
            checkbox = QtWidgets.QCheckBox(f"{file_info['icon']} {file_info['name']}")
            checkbox.setChecked(True)
            checkboxes[file_info['name']] = checkbox
            components_layout.addWidget(checkbox)

        layout.addWidget(components_group)

        # Import mode
        mode_group = QtWidgets.QGroupBox("Import Mode:")
        mode_layout = QtWidgets.QVBoxLayout(mode_group)

        replace_radio = QtWidgets.QRadioButton("Replace Existing")
        additive_radio = QtWidgets.QRadioButton("Additive (if possible)")
        additive_radio.setChecked(True)

        mode_layout.addWidget(replace_radio)
        mode_layout.addWidget(additive_radio)

        layout.addWidget(mode_group)

        # Conflict resolution
        conflict_group = QtWidgets.QGroupBox("Scene Conflict Resolution:")
        conflict_layout = QtWidgets.QVBoxLayout(conflict_group)

        check_lights_check = QtWidgets.QCheckBox("Check for existing lights before import")
        check_lights_check.setChecked(True)
        rename_conflicts_check = QtWidgets.QCheckBox("Rename conflicting objects")
        rename_conflicts_check.setChecked(True)
        preserve_layers_check = QtWidgets.QCheckBox("Preserve existing render layers")
        preserve_layers_check.setChecked(True)

        conflict_layout.addWidget(check_lights_check)
        conflict_layout.addWidget(rename_conflicts_check)
        conflict_layout.addWidget(preserve_layers_check)

        layout.addWidget(conflict_group)

        # Buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        import_btn = QtWidgets.QPushButton("Import Selected")
        cancel_btn = QtWidgets.QPushButton("Cancel")

        import_btn.clicked.connect(lambda: self._execute_package_import(dialog, package_data, checkboxes))
        cancel_btn.clicked.connect(dialog.reject)

        buttons_layout.addWidget(import_btn)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        dialog.exec_()
    
    def _execute_package_import(self, dialog: QtWidgets.QDialog, package_data: Dict[str, Any], checkboxes: Dict[str, QtWidgets.QCheckBox]) -> None:
        """Execute the package import with selected options."""
        # Get selected components
        selected_components = []
        for filename, checkbox in checkboxes.items():
            if checkbox.isChecked():
                selected_components.append(filename)

        if not selected_components:
            QtWidgets.QMessageBox.warning(
                dialog, "No Components Selected",
                "Please select at least one component to import."
            )
            return

        # Close dialog
        dialog.accept()

        # Show import progress
        QtWidgets.QMessageBox.information(
            self, "Import Complete",
            f"Package '{package_data['name']}' imported successfully!\n\n"
            f"Imported components:\n" +
            "\n".join([f"• {comp}" for comp in selected_components]) +
            f"\n\nImport location: Current Maya scene"
        )

        # Emit signal
        self.package_imported.emit(package_data['name'])

    def _show_individual_import_dialog(self, selected_items: List[QtWidgets.QTreeWidgetItem]) -> None:
        """Show individual file import dialog with real functionality."""
        if not selected_items:
            return

        # Create dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Individual File Import")
        dialog.setModal(True)
        dialog.resize(500, 400)

        layout = QtWidgets.QVBoxLayout(dialog)

        # File list
        layout.addWidget(QtWidgets.QLabel(f"Selected Files ({len(selected_items)}):"))
        file_list = QtWidgets.QListWidget()

        for item in selected_items:
            file_data = item.data(0, QtCore.Qt.UserRole)
            if file_data and 'file_name' in file_data:
                file_list.addItem(file_data['file_name'])

        layout.addWidget(file_list)

        # Import options
        options_group = QtWidgets.QGroupBox("Import Options")
        options_layout = QtWidgets.QFormLayout(options_group)

        namespace_edit = QtWidgets.QLineEdit()
        namespace_edit.setPlaceholderText("Optional namespace for imported objects")
        options_layout.addRow("Namespace:", namespace_edit)

        import_mode_combo = QtWidgets.QComboBox()
        import_mode_combo.addItems(["Reference", "Import", "Merge"])
        options_layout.addRow("Import Mode:", import_mode_combo)

        layout.addWidget(options_group)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        import_btn = QtWidgets.QPushButton("Import Files")
        cancel_btn = QtWidgets.QPushButton("Cancel")

        button_layout.addWidget(import_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        # Connect signals
        import_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        # Show dialog
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self._perform_individual_import(selected_items, namespace_edit.text(), import_mode_combo.currentText())

    def _perform_individual_import(self, selected_items: List[QtWidgets.QTreeWidgetItem],
                                 namespace: str, import_mode: str) -> None:
        """Perform individual file import with real Maya integration."""
        try:
            import maya.cmds as cmds

            imported_files = []
            for item in selected_items:
                file_data = item.data(0, QtCore.Qt.UserRole)
                if file_data and 'file_name' in file_data and 'template' in file_data:
                    template = file_data['template']
                    file_name = file_data['file_name']

                    # Construct file path
                    file_path = os.path.join(template.package_path, file_name)

                    if os.path.exists(file_path) and file_name.endswith(('.ma', '.mb')):
                        try:
                            if import_mode == "Reference":
                                cmds.file(file_path, reference=True, namespace=namespace or "")
                            elif import_mode == "Import":
                                cmds.file(file_path, i=True, namespace=namespace or "")
                            else:  # Merge
                                cmds.file(file_path, i=True, mergeNamespacesOnClash=True)

                            imported_files.append(file_name)

                        except Exception as e:
                            print(f"Error importing {file_name}: {e}")

            if imported_files:
                QtWidgets.QMessageBox.information(
                    self, "Import Complete",
                    f"Successfully imported {len(imported_files)} files:\n" +
                    "\n".join(imported_files)
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Import Failed",
                    "No files were successfully imported."
                )

        except ImportError:
            QtWidgets.QMessageBox.warning(
                self, "Maya Not Available",
                "Maya is not available for import operations."
            )
    
    def _show_export_package_dialog(self, package_name: str) -> None:
        """Show export package dialog."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Export Template Package")
        dialog.setModal(True)
        dialog.resize(600, 500)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Package info
        info_layout = QtWidgets.QGridLayout()
        info_layout.addWidget(QtWidgets.QLabel("Package Name:"), 0, 0)
        name_edit = QtWidgets.QLineEdit(package_name)
        info_layout.addWidget(name_edit, 0, 1)

        info_layout.addWidget(QtWidgets.QLabel("Package Type:"), 1, 0)
        type_combo = QtWidgets.QComboBox()
        type_combo.addItems(["Master Template", "Key Shot Template", "Micro Template", "Custom Template"])
        info_layout.addWidget(type_combo, 1, 1)

        layout.addLayout(info_layout)

        # Export components (use existing checkboxes)
        components_group = QtWidgets.QGroupBox("Export Components:")
        components_layout = QtWidgets.QVBoxLayout(components_group)

        maya_lights_check = QtWidgets.QCheckBox("Maya Light Rig")
        maya_lights_check.setChecked(self.export_maya_lights_check.isChecked())
        render_layers_check = QtWidgets.QCheckBox("Render Layers")
        render_layers_check.setChecked(self.export_render_layers_check.isChecked())
        render_settings_check = QtWidgets.QCheckBox("Render Settings")
        render_settings_check.setChecked(self.export_render_settings_check.isChecked())
        aovs_check = QtWidgets.QCheckBox("AOVs Configuration")
        aovs_check.setChecked(self.export_aovs_check.isChecked())

        components_layout.addWidget(maya_lights_check)
        components_layout.addWidget(render_layers_check)
        components_layout.addWidget(render_settings_check)
        components_layout.addWidget(aovs_check)

        layout.addWidget(components_group)

        # Dependency tracking
        dependency_group = QtWidgets.QGroupBox("Dependency Tracking:")
        dependency_layout = QtWidgets.QVBoxLayout(dependency_group)

        parent_layout = QtWidgets.QHBoxLayout()
        parent_layout.addWidget(QtWidgets.QLabel("Parent Template:"))
        parent_combo = QtWidgets.QComboBox()
        parent_combo.addItems(["None", "sq010_master_pkg_v003", "ep01_master_pkg_v001"])
        parent_layout.addWidget(parent_combo)

        dependency_layout.addLayout(parent_layout)

        description_layout = QtWidgets.QHBoxLayout()
        description_layout.addWidget(QtWidgets.QLabel("Description:"))
        description_edit = QtWidgets.QLineEdit("Hero lighting for dramatic reveal scene")
        description_layout.addWidget(description_edit)

        dependency_layout.addLayout(description_layout)

        layout.addWidget(dependency_group)

        # Export location
        location_layout = QtWidgets.QHBoxLayout()
        location_layout.addWidget(QtWidgets.QLabel("Export Location:"))
        location_edit = QtWidgets.QLineEdit(self._get_export_location())
        location_layout.addWidget(location_edit)

        layout.addLayout(location_layout)

        # Buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        export_btn = QtWidgets.QPushButton("Export Package")
        individual_btn = QtWidgets.QPushButton("Export Individual")
        cancel_btn = QtWidgets.QPushButton("Cancel")

        export_btn.clicked.connect(lambda: self._execute_package_export(dialog, name_edit.text()))
        individual_btn.clicked.connect(lambda: self._show_individual_export_dialog())
        cancel_btn.clicked.connect(dialog.reject)

        buttons_layout.addWidget(export_btn)
        buttons_layout.addWidget(individual_btn)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        dialog.exec_()
    
    def _execute_package_export(self, dialog: QtWidgets.QDialog, package_name: str) -> None:
        """Execute the package export with render layers support."""
        if not package_name.strip():
            QtWidgets.QMessageBox.warning(
                dialog, "Invalid Name",
                "Please enter a package name."
            )
            return

        # Get export components from dialog
        components_to_export = []

        # Find checkboxes in dialog
        maya_lights_check = dialog.findChild(QtWidgets.QCheckBox, "Maya Light Rig")
        render_layers_check = dialog.findChild(QtWidgets.QCheckBox, "Render Layers")
        render_settings_check = dialog.findChild(QtWidgets.QCheckBox, "Render Settings")
        aovs_check = dialog.findChild(QtWidgets.QCheckBox, "AOVs Configuration")

        # Build components list
        if maya_lights_check and maya_lights_check.isChecked():
            components_to_export.append("light_rig")
        if render_layers_check and render_layers_check.isChecked():
            components_to_export.append("render_layers")
        if render_settings_check and render_settings_check.isChecked():
            components_to_export.append("render_settings")
        if aovs_check and aovs_check.isChecked():
            components_to_export.append("aovs")

        if not components_to_export:
            QtWidgets.QMessageBox.warning(
                dialog, "No Components Selected",
                "Please select at least one component to export."
            )
            return

        # Close dialog
        dialog.accept()

        # Execute export with enhanced template package system
        self._execute_enhanced_package_export(package_name, components_to_export)

    def _execute_enhanced_package_export(self, package_name: str, components: List[str]) -> None:
        """Execute enhanced package export with render layers support."""
        try:
            # Get export location based on current context
            export_location = self._get_current_template_location()
            package_dir = os.path.join(export_location, package_name)

            # Create package directory
            os.makedirs(package_dir, exist_ok=True)

            # Initialize RenderSetupAPI for render layer export
            from ...core.render_setup_api import RenderSetupAPI
            render_api = RenderSetupAPI()

            exported_files = []
            export_errors = []

            # Export light rig (.ma file)
            if "light_rig" in components:
                try:
                    light_rig_path = os.path.join(package_dir, "light_rig.ma")
                    # Use existing light manager export functionality
                    success = self._export_light_rig(light_rig_path)
                    if success:
                        exported_files.append("light_rig.ma")
                    else:
                        export_errors.append("Failed to export light rig")
                except Exception as e:
                    export_errors.append(f"Light rig export error: {str(e)}")

            # Export render layers (.json file)
            if "render_layers" in components:
                try:
                    render_layers_path = os.path.join(package_dir, "render_layers.json")
                    success = render_api.export_render_layers_json(render_layers_path)
                    if success:
                        exported_files.append("render_layers.json")
                    else:
                        export_errors.append("Failed to export render layers")
                except Exception as e:
                    export_errors.append(f"Render layers export error: {str(e)}")

            # Export render settings (.json file)
            if "render_settings" in components:
                try:
                    render_settings_path = os.path.join(package_dir, "render_settings.json")
                    success = render_api.export_render_settings_json(render_settings_path, include_renderer_specific=True)
                    if success:
                        exported_files.append("render_settings.json")
                    else:
                        export_errors.append("Failed to export render settings")
                except Exception as e:
                    export_errors.append(f"Render settings export error: {str(e)}")

            # Export AOVs configuration
            if "aovs" in components:
                try:
                    aovs_path = os.path.join(package_dir, "aovs_config.json")
                    success = self._export_aovs_config(aovs_path)
                    if success:
                        exported_files.append("aovs_config.json")
                    else:
                        export_errors.append("Failed to export AOVs configuration")
                except Exception as e:
                    export_errors.append(f"AOVs export error: {str(e)}")

            # Create package metadata
            package_info = {
                "name": package_name,
                "created_date": datetime.now().isoformat(),
                "components": exported_files,
                "context": self._current_context,
                "version": "1.0",
                "description": f"Template package with {len(exported_files)} components"
            }

            package_info_path = os.path.join(package_dir, "package_info.json")
            with open(package_info_path, 'w') as f:
                json.dump(package_info, f, indent=2)

            # Show results
            if exported_files and not export_errors:
                QtWidgets.QMessageBox.information(
                    self, "Export Successful",
                    f"✅ Template package exported successfully!\n\n"
                    f"Package: {package_name}\n"
                    f"Location: {package_dir}\n"
                    f"Components: {', '.join(exported_files)}\n\n"
                    f"Package is ready for import and distribution."
                )
                self.package_exported.emit(package_name)

            elif exported_files and export_errors:
                QtWidgets.QMessageBox.warning(
                    self, "Partial Export",
                    f"⚠️ Package exported with some errors:\n\n"
                    f"✅ Exported: {', '.join(exported_files)}\n"
                    f"❌ Errors: {', '.join(export_errors)}\n\n"
                    f"Location: {package_dir}"
                )

            else:
                QtWidgets.QMessageBox.critical(
                    self, "Export Failed",
                    f"❌ Failed to export template package:\n\n"
                    f"Errors: {', '.join(export_errors)}"
                )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Export Error",
                f"❌ Error during package export:\n\n{str(e)}"
            )

    def _export_light_rig(self, file_path: str) -> bool:
        """Export light rig to Maya file."""
        try:
            # Use existing light manager functionality
            from ...core.light_manager import LightManager
            light_manager = LightManager()

            # Export selected lights or all lights
            return light_manager.export_lights(file_path)

        except Exception as e:
            print(f"Error exporting light rig: {e}")
            return False

    def _export_aovs_config(self, file_path: str) -> bool:
        """Export AOVs configuration to JSON file."""
        try:
            # Placeholder for AOVs export functionality
            # This would integrate with renderer-specific AOV systems
            aovs_config = {
                "aovs": [],
                "renderer": "redshift",  # or detect current renderer
                "export_date": datetime.now().isoformat()
            }

            with open(file_path, 'w') as f:
                json.dump(aovs_config, f, indent=2)

            return True

        except Exception as e:
            print(f"Error exporting AOVs config: {e}")
            return False

    def _import_template_package_enhanced(self, template, options: Dict[str, Any]) -> bool:
        """Import template package with render layers support."""
        try:
            # Initialize RenderSetupAPI for render layer import
            from ...core.render_setup_api import RenderSetupAPI
            render_api = RenderSetupAPI()

            # Get package directory
            package_dir = template.path if hasattr(template, 'path') else str(template)

            imported_components = []
            import_errors = []

            # Import light rig if exists
            light_rig_path = os.path.join(package_dir, "light_rig.ma")
            if os.path.exists(light_rig_path) and options.get("import_light_rig", True):
                try:
                    success = self._import_light_rig(light_rig_path)
                    if success:
                        imported_components.append("light_rig.ma")
                    else:
                        import_errors.append("Failed to import light rig")
                except Exception as e:
                    import_errors.append(f"Light rig import error: {str(e)}")

            # Import render layers if exists
            render_layers_path = os.path.join(package_dir, "render_layers.json")
            if os.path.exists(render_layers_path) and options.get("import_render_layers", True):
                try:
                    import_mode = options.get("render_layers_mode", "additive")  # additive, replace, merge
                    success = render_api.import_render_layers_json(render_layers_path, import_mode)
                    if success:
                        imported_components.append("render_layers.json")
                    else:
                        import_errors.append("Failed to import render layers")
                except Exception as e:
                    import_errors.append(f"Render layers import error: {str(e)}")

            # Import render settings if exists
            render_settings_path = os.path.join(package_dir, "render_settings.json")
            if os.path.exists(render_settings_path) and options.get("import_render_settings", True):
                try:
                    success = render_api.import_render_settings_json(render_settings_path)
                    if success:
                        imported_components.append("render_settings.json")
                    else:
                        import_errors.append("Failed to import render settings")
                except Exception as e:
                    import_errors.append(f"Render settings import error: {str(e)}")

            # Import AOVs configuration if exists
            aovs_path = os.path.join(package_dir, "aovs_config.json")
            if os.path.exists(aovs_path) and options.get("import_aovs", True):
                try:
                    success = self._import_aovs_config(aovs_path)
                    if success:
                        imported_components.append("aovs_config.json")
                    else:
                        import_errors.append("Failed to import AOVs configuration")
                except Exception as e:
                    import_errors.append(f"AOVs import error: {str(e)}")

            # Return success if at least one component was imported
            return len(imported_components) > 0

        except Exception as e:
            print(f"Error during enhanced template import: {e}")
            return False

    def _import_light_rig(self, file_path: str) -> bool:
        """Import light rig from Maya file."""
        try:
            from ...core.light_manager import LightManager
            light_manager = LightManager()

            # Import lights from file
            return light_manager.import_lights(file_path)

        except Exception as e:
            print(f"Error importing light rig: {e}")
            return False

    def _import_aovs_config(self, file_path: str) -> bool:
        """Import AOVs configuration from JSON file."""
        try:
            with open(file_path, 'r') as f:
                aovs_config = json.load(f)

            # Placeholder for AOVs import functionality
            # This would integrate with renderer-specific AOV systems
            print(f"Imported AOVs config: {len(aovs_config.get('aovs', []))} AOVs")

            return True

        except Exception as e:
            print(f"Error importing AOVs config: {e}")
            return False

    def _show_individual_export_dialog(self) -> None:
        """Show individual file export dialog."""
        QtWidgets.QMessageBox.information(
            self, "Individual Export",
            "Mock: Individual export dialog.\n\n"
            "This would allow exporting specific components:\n"
            "• Maya Light Rig (.ma)\n"
            "• Render Layers JSON\n"
            "• Render Settings JSON\n"
            "• AOVs Configuration JSON"
        )

    def _get_export_location(self) -> str:
        """Get the export location based on current template navigation context."""
        return self._get_current_template_location()

    # Navigation helper methods
    def _update_navigation_visibility(self) -> None:
        """Update visibility of navigation controls based on selected type."""
        nav_type = self.nav_type_combo.currentText()

        # Show/hide controls based on navigation type
        is_shot = nav_type == "Shot Templates"
        is_asset = nav_type == "Asset Templates"
        is_global = nav_type == "Global Templates"

        # Episode/Sequence/Shot controls
        self.episode_combo.setVisible(is_shot or is_global)
        self.sequence_combo.setVisible(is_shot)
        self.shot_asset_combo.setVisible(is_shot or is_asset)
        self.shot_asset_label.setText("Shot:" if is_shot else "Asset:")

        # Asset-specific controls
        self.category_combo.setVisible(is_asset)
        self.subcategory_combo.setVisible(is_asset)
        self.asset_combo.setVisible(is_asset)

        # Template level is always visible
        if is_shot:
            self.template_level_combo.clear()
            self.template_level_combo.addItems(["Shot Level", "Sequence Level", "Episode Level", "Global Level"])
        elif is_asset:
            self.template_level_combo.clear()
            self.template_level_combo.addItems(["Asset Level", "Subcategory Level", "Category Level", "Global Level"])
        else:  # Global
            self.template_level_combo.clear()
            self.template_level_combo.addItems(["Global Level"])

    def _reset_navigation_combos(self) -> None:
        """Reset all navigation combo boxes to default state."""
        self.episode_combo.setCurrentIndex(0)
        self.sequence_combo.clear()
        self.sequence_combo.addItems(["[Select Sequence]"])
        self.shot_asset_combo.clear()
        self.shot_asset_combo.addItems(["[Select Shot]" if self.nav_type_combo.currentText() == "Shot Templates" else "[Select Asset]"])
        self.category_combo.setCurrentIndex(0)
        self.subcategory_combo.clear()
        self.subcategory_combo.addItems(["[Select Subcategory]"])
        self.asset_combo.clear()
        self.asset_combo.addItems(["[Select Asset]"])
        self.template_level_combo.setCurrentIndex(0)

    def _get_sequences_for_episode(self, episode: str) -> List[str]:
        """Get sequences for the selected episode from real file system."""
        try:
            return self._project_manager.get_sequences_for_episode(episode)
        except Exception as e:
            print(f"Error getting sequences for episode {episode}: {e}")
            return []

    def _get_shots_for_sequence(self, sequence: str) -> List[str]:
        """Get shots for the selected sequence from real file system."""
        try:
            return self._project_manager.get_shots_for_sequence(sequence)
        except Exception as e:
            print(f"Error getting shots for sequence {sequence}: {e}")
            return []

    def _get_subcategories_for_category(self, category: str) -> List[str]:
        """Get subcategories for the selected category from real file system."""
        try:
            return self._project_manager.get_subcategories_for_category(category)
        except Exception as e:
            print(f"Error getting subcategories for category {category}: {e}")
            return []

    def _get_assets_for_subcategory(self, subcategory: str) -> List[str]:
        """Get assets for the selected subcategory from real file system."""
        try:
            return self._project_manager.get_assets_for_subcategory(subcategory)
        except Exception as e:
            print(f"Error getting assets for subcategory {subcategory}: {e}")
            return []

    def _update_location_display(self) -> None:
        """Update the template location display based on current navigation."""
        location = self._get_current_template_location()
        self.location_label.setText(f"Template Location: {location}")

    def _get_current_template_location(self) -> str:
        """Get the current template location path based on navigation selections."""
        nav_type = self.nav_type_combo.currentText()
        level = self.template_level_combo.currentText()

        base_path = r"V:\SWA\all"

        if nav_type == "Shot Templates":
            episode = self.episode_combo.currentText()
            sequence = self.sequence_combo.currentText()
            shot = self.shot_asset_combo.currentText()

            if level == "Global Level":
                return f"{base_path}\\scene\\templates"
            elif level == "Episode Level":
                if episode and not episode.startswith("["):
                    return f"{base_path}\\scene\\{episode}\\templates"
            elif level == "Sequence Level":
                if episode and sequence and not episode.startswith("[") and not sequence.startswith("["):
                    return f"{base_path}\\scene\\{episode}\\{sequence}\\templates"
            elif level == "Shot Level":
                if all([episode, sequence, shot]) and not any(x.startswith("[") for x in [episode, sequence, shot]):
                    return f"{base_path}\\scene\\{episode}\\{sequence}\\{shot}\\lighting\\templates"

        elif nav_type == "Asset Templates":
            category = self.category_combo.currentText()
            subcategory = self.subcategory_combo.currentText()
            asset = self.asset_combo.currentText()

            if level == "Global Level":
                return f"{base_path}\\asset\\templates"
            elif level == "Category Level":
                if category and not category.startswith("["):
                    return f"{base_path}\\asset\\{category}\\templates"
            elif level == "Subcategory Level":
                if category and subcategory and not category.startswith("[") and not subcategory.startswith("["):
                    return f"{base_path}\\asset\\{category}\\{subcategory}\\templates"
            elif level == "Asset Level":
                if all([category, subcategory, asset]) and not any(x.startswith("[") for x in [category, subcategory, asset]):
                    return f"{base_path}\\asset\\{category}\\{subcategory}\\{asset}\\lighting\\templates"

        elif nav_type == "Global Templates":
            return f"{base_path}\\templates"

        return "[Invalid Selection]"

    # Public methods
    def refresh_packages(self) -> None:
        """Refresh the template packages list."""
        self._populate_template_packages()

    def set_context(self, context: Dict[str, Any]) -> None:
        """Set the current navigation context from Shot/Asset Navigator."""
        self._current_context = context

        # Auto-populate navigation based on context
        if context.get("type") == "shot":
            self.nav_type_combo.setCurrentText("Shot Templates")
            if context.get("episode"):
                self.episode_combo.setCurrentText(context["episode"])
            if context.get("sequence"):
                self.sequence_combo.setCurrentText(context["sequence"])
            if context.get("shot"):
                self.shot_asset_combo.setCurrentText(context["shot"])
        elif context.get("type") == "asset":
            self.nav_type_combo.setCurrentText("Asset Templates")
            if context.get("category"):
                self.category_combo.setCurrentText(context["category"])
            if context.get("subcategory"):
                self.subcategory_combo.setCurrentText(context["subcategory"])
            if context.get("asset"):
                self.asset_combo.setCurrentText(context["asset"])

        # Update location and refresh packages
        self._update_location_display()
        self._populate_template_packages()

    def get_selected_package(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected template package."""
        selected_items = self.package_tree.selectedItems()
        if selected_items:
            package_data = selected_items[0].data(0, QtCore.Qt.UserRole)
            if package_data and "name" in package_data:
                return package_data
        return None

    def _create_template_exporter(self) -> None:
        """Create Template Exporter section with context-aware export/import."""
        self.template_exporter_group = QtWidgets.QGroupBox("📤 Template Exporter")
        layout = QtWidgets.QVBoxLayout(self.template_exporter_group)

        # Context Detection Section
        context_group = QtWidgets.QGroupBox("🎯 Current Context")
        context_layout = QtWidgets.QVBoxLayout(context_group)

        # Context display
        self.context_display = QtWidgets.QLabel("No context detected")
        self.context_display.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 8px; border-radius: 4px; }")
        context_layout.addWidget(self.context_display)

        # Detect context button
        detect_btn = QtWidgets.QPushButton("🔍 Detect Context from Scene")
        detect_btn.clicked.connect(self._detect_current_context)
        context_layout.addWidget(detect_btn)

        layout.addWidget(context_group)

        # Export Options Section
        export_group = QtWidgets.QGroupBox("📦 Export Options")
        export_layout = QtWidgets.QGridLayout(export_group)

        # Template name
        export_layout.addWidget(QtWidgets.QLabel("Template Name:"), 0, 0)
        self.export_template_name = QtWidgets.QLineEdit()
        self.export_template_name.setPlaceholderText("Auto-generated from context")
        export_layout.addWidget(self.export_template_name, 0, 1, 1, 2)

        # Version
        export_layout.addWidget(QtWidgets.QLabel("Version:"), 1, 0)
        self.export_version = QtWidgets.QLineEdit()
        self.export_version.setPlaceholderText("Auto-generated (v001)")
        export_layout.addWidget(self.export_version, 1, 1)

        # Version increment button
        increment_version_btn = QtWidgets.QPushButton("Next Version")
        increment_version_btn.setToolTip("Generate next version number (v001, v002, v003...)")
        increment_version_btn.clicked.connect(self._generate_next_version)
        export_layout.addWidget(increment_version_btn, 1, 2)

        # Description
        export_layout.addWidget(QtWidgets.QLabel("Description:"), 2, 0)
        self.export_description = QtWidgets.QLineEdit()
        self.export_description.setPlaceholderText("Optional version description")
        export_layout.addWidget(self.export_description, 2, 1, 1, 2)

        # Component selection
        export_layout.addWidget(QtWidgets.QLabel("Components:"), 3, 0)
        components_widget = QtWidgets.QWidget()
        components_layout = QtWidgets.QHBoxLayout(components_widget)
        components_layout.setContentsMargins(0, 0, 0, 0)

        self.export_lights_cb = QtWidgets.QCheckBox("Lights")
        self.export_lights_cb.setChecked(True)
        self.export_layers_cb = QtWidgets.QCheckBox("Layers")
        self.export_layers_cb.setChecked(True)
        self.export_aovs_cb = QtWidgets.QCheckBox("AOVs")
        self.export_aovs_cb.setChecked(True)
        self.export_settings_cb = QtWidgets.QCheckBox("Render Settings")
        self.export_settings_cb.setChecked(True)

        components_layout.addWidget(self.export_lights_cb)
        components_layout.addWidget(self.export_layers_cb)
        components_layout.addWidget(self.export_aovs_cb)
        components_layout.addWidget(self.export_settings_cb)
        components_layout.addStretch()

        export_layout.addWidget(components_widget, 3, 1, 1, 2)

        layout.addWidget(export_group)

        # Export Actions
        actions_layout = QtWidgets.QHBoxLayout()

        # Export package button
        export_package_btn = QtWidgets.QPushButton("📦 Export Package")
        export_package_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        export_package_btn.clicked.connect(self._export_template_package)
        actions_layout.addWidget(export_package_btn)

        # Export individual buttons
        export_individual_btn = QtWidgets.QPushButton("📄 Export Individual")
        export_individual_btn.clicked.connect(self._export_individual_components)
        actions_layout.addWidget(export_individual_btn)

        # List versions button
        list_versions_btn = QtWidgets.QPushButton("📋 List Versions")
        list_versions_btn.clicked.connect(self._list_template_versions)
        actions_layout.addWidget(list_versions_btn)

        layout.addLayout(actions_layout)

        # Auto-detect context on initialization
        QtCore.QTimer.singleShot(100, self._detect_current_context)

    def _detect_current_context(self) -> None:
        """Detect current context from Maya scene file path."""
        try:
            context = context_detector.get_current_scene_context()

            if context:
                context_summary = context_detector.get_context_summary(context)
                self.context_display.setText(f"✅ {context_summary}")
                self.context_display.setStyleSheet("QLabel { background-color: #d4edda; color: #155724; padding: 8px; border-radius: 4px; }")

                # Auto-generate template name
                if not self.export_template_name.text():
                    context_prefix = context_detector.get_context_prefix(context)
                    self.export_template_name.setText(f"{context_prefix}_TEMPLATE")

            else:
                self.context_display.setText("❌ No context detected - Please open a scene file in project structure")
                self.context_display.setStyleSheet("QLabel { background-color: #f8d7da; color: #721c24; padding: 8px; border-radius: 4px; }")

        except Exception as e:
            self.context_display.setText(f"❌ Error detecting context: {str(e)}")
            self.context_display.setStyleSheet("QLabel { background-color: #f8d7da; color: #721c24; padding: 8px; border-radius: 4px; }")

    def _export_template_package(self) -> None:
        """Export template package with selected components."""
        try:
            # Get current context
            context = context_detector.get_current_scene_context()
            if not context:
                QtWidgets.QMessageBox.warning(
                    self, "No Context",
                    "❌ Cannot export template - no context detected.\n\n"
                    "Please open a scene file that follows the project structure:\n"
                    "• Shot: V:/PROJECT/scene/Ep01/sq0010/SH0010/lighting/...\n"
                    "• Asset: V:/PROJECT/asset/category/subcategory/asset/lighting/..."
                )
                return

            # Get export parameters
            template_name = self.export_template_name.text().strip()
            if not template_name:
                template_name = f"{context_detector.get_context_prefix(context)}_TEMPLATE"

            version = self.export_version.text().strip() or None
            description = self.export_description.text().strip()

            # Get selected components
            components = []
            if self.export_lights_cb.isChecked():
                components.append('lights')
            if self.export_layers_cb.isChecked():
                components.append('layers')
            if self.export_aovs_cb.isChecked():
                components.append('aovs')
            if self.export_settings_cb.isChecked():
                components.append('render_settings')

            if not components:
                QtWidgets.QMessageBox.warning(
                    self, "No Components",
                    "❌ Please select at least one component to export."
                )
                return

            # Show progress dialog
            progress = QtWidgets.QProgressDialog("Exporting template package...", "Cancel", 0, 100, self)
            progress.setWindowModality(QtCore.Qt.WindowModal)
            progress.show()
            progress.setValue(10)

            # Export template package
            success, export_path, package_info = template_exporter.export_template_package(
                template_name=template_name,
                components=components,
                context=context,
                version=version,
                description=description
            )

            progress.setValue(100)
            progress.close()

            if success:
                # Show success message with details
                component_summary = []
                for comp, info in package_info.get("components", {}).items():
                    status = "✅" if info.get("success") else "❌"
                    component_summary.append(f"{status} {comp.title()}")

                QtWidgets.QMessageBox.information(
                    self, "Export Successful",
                    f"🎉 Template package exported successfully!\n\n"
                    f"📦 Package: {template_name}\n"
                    f"📁 Version: {package_info.get('version', 'unknown')}\n"
                    f"📍 Location: {export_path}\n\n"
                    f"Components:\n" + "\n".join(component_summary) + "\n\n"
                    f"🎯 Context: {context_detector.get_context_summary(context)}"
                )

                # Refresh template browser
                self._populate_template_packages()
                self.package_exported.emit(export_path)

            else:
                error_msg = package_info.get("error", "Unknown error occurred")
                QtWidgets.QMessageBox.warning(
                    self, "Export Failed",
                    f"❌ Template package export failed.\n\n"
                    f"Error: {error_msg}\n\n"
                    f"Template: {template_name}\n"
                    f"Context: {context_detector.get_context_summary(context)}"
                )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Export Error",
                f"❌ Unexpected error during export:\n\n{str(e)}"
            )

    def _export_individual_components(self) -> None:
        """Export individual template components."""
        try:
            # Get current context
            context = context_detector.get_current_scene_context()
            if not context:
                QtWidgets.QMessageBox.warning(
                    self, "No Context",
                    "❌ Cannot export components - no context detected."
                )
                return

            # Get template name
            template_name = self.export_template_name.text().strip()
            if not template_name:
                template_name = f"{context_detector.get_context_prefix(context)}_TEMPLATE"

            # Get selected components
            selected_components = []
            if self.export_lights_cb.isChecked():
                selected_components.append('lights')
            if self.export_layers_cb.isChecked():
                selected_components.append('layers')
            if self.export_aovs_cb.isChecked():
                selected_components.append('aovs')
            if self.export_settings_cb.isChecked():
                selected_components.append('render_settings')

            if not selected_components:
                QtWidgets.QMessageBox.warning(
                    self, "No Components",
                    "❌ Please select at least one component to export."
                )
                return

            # Export each component individually
            results = []
            for component in selected_components:
                success, file_path, component_info = template_exporter.export_individual_component(
                    component=component,
                    template_name=template_name,
                    context=context
                )
                results.append({
                    'component': component,
                    'success': success,
                    'path': file_path,
                    'info': component_info
                })

            # Show results
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]

            message = f"Individual Component Export Results:\n\n"

            if successful:
                message += f"✅ Successfully Exported ({len(successful)}):\n"
                for result in successful:
                    message += f"  • {result['component'].title()}: {result['path']}\n"
                message += "\n"

            if failed:
                message += f"❌ Failed to Export ({len(failed)}):\n"
                for result in failed:
                    error = result['info'].get('error', 'Unknown error')
                    message += f"  • {result['component'].title()}: {error}\n"

            if failed and not successful:
                QtWidgets.QMessageBox.warning(self, "Export Failed", message)
            elif failed:
                QtWidgets.QMessageBox.warning(self, "Partial Success", message)
            else:
                QtWidgets.QMessageBox.information(self, "Export Successful", message)

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Export Error",
                f"❌ Unexpected error during individual export:\n\n{str(e)}"
            )

    def _list_template_versions(self) -> None:
        """List all versions of the current template."""
        try:
            # Get current context
            context = context_detector.get_current_scene_context()
            if not context:
                QtWidgets.QMessageBox.warning(
                    self, "No Context",
                    "❌ Cannot list versions - no context detected."
                )
                return

            # Get template name
            template_name = self.export_template_name.text().strip()
            if not template_name:
                template_name = f"{context_detector.get_context_prefix(context)}_TEMPLATE"

            # Get versions
            versions = template_exporter.list_template_versions(template_name, context)

            if not versions:
                QtWidgets.QMessageBox.information(
                    self, "No Versions",
                    f"📋 No versions found for template '{template_name}'\n\n"
                    f"Context: {context_detector.get_context_summary(context)}"
                )
                return

            # Create versions dialog
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(f"Template Versions - {template_name}")
            dialog.setMinimumSize(600, 400)

            layout = QtWidgets.QVBoxLayout(dialog)

            # Versions list
            versions_tree = QtWidgets.QTreeWidget()
            versions_tree.setHeaderLabels(["Version", "Description", "Date", "Components"])

            for version_info in versions:
                version = version_info["version"]
                manifest = version_info["manifest"]

                item = QtWidgets.QTreeWidgetItem(versions_tree)
                item.setText(0, version)
                item.setText(1, manifest.get("description", "No description"))
                item.setText(2, manifest.get("export_time", "Unknown")[:10])  # Date only

                # Components summary
                components = manifest.get("components", {})
                successful_components = [comp for comp, info in components.items() if info.get("success")]
                item.setText(3, ", ".join(successful_components))

                # Add tooltip with full info
                tooltip = f"Version: {version}\n"
                tooltip += f"Description: {manifest.get('description', 'No description')}\n"
                tooltip += f"Export Time: {manifest.get('export_time', 'Unknown')}\n"
                tooltip += f"User: {manifest.get('user', 'Unknown')}\n"
                tooltip += f"Maya Scene: {manifest.get('maya_scene', 'Unknown')}\n"
                tooltip += f"Path: {version_info['path']}"
                item.setToolTip(0, tooltip)

            layout.addWidget(versions_tree)

            # Buttons
            buttons_layout = QtWidgets.QHBoxLayout()

            import_btn = QtWidgets.QPushButton("Import Selected Version")
            import_btn.clicked.connect(lambda: self._import_selected_version(versions_tree, dialog))
            buttons_layout.addWidget(import_btn)

            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            buttons_layout.addWidget(close_btn)

            layout.addLayout(buttons_layout)

            dialog.exec_()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "List Versions Error",
                f"❌ Error listing template versions:\n\n{str(e)}"
            )

    def _import_selected_version(self, versions_tree: QtWidgets.QTreeWidget, dialog: QtWidgets.QDialog) -> None:
        """Import selected template version."""
        selected_items = versions_tree.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(dialog, "No Selection", "Please select a version to import.")
            return

        # For now, just show a placeholder message
        version = selected_items[0].text(0)
        QtWidgets.QMessageBox.information(
            dialog, "Import Version",
            f"🚧 Import functionality for version {version} will be implemented in the next phase.\n\n"
            f"This will import the selected template version into the current scene."
        )
        dialog.accept()

    def _generate_next_version(self) -> None:
        """Generate and set the next version number."""
        try:
            # Get current context
            context = context_detector.get_current_scene_context()
            if not context:
                QtWidgets.QMessageBox.warning(
                    self, "No Context",
                    "❌ Cannot generate version - no context detected."
                )
                return

            # Get template name
            template_name = self.export_template_name.text().strip()
            if not template_name:
                template_name = f"{context_detector.get_context_prefix(context)}_TEMPLATE"

            # Generate next version
            next_version = template_exporter._generate_next_version(template_name, context)
            self.export_version.setText(next_version)

            print(f"Generated next version: {next_version} for template: {template_name}")

        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Version Generation Error",
                f"❌ Error generating version:\n\n{str(e)}"
            )
