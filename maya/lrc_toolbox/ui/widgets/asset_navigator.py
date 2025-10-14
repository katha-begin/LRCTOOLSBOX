"""
Asset Navigator Widget

This module provides the Asset/Shot Navigator widget with enhanced template management
and context-aware navigation functionality.
"""

import os
import glob
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
from ...core.project_manager import ProjectManager
from ...core.models import NavigationContext, ProjectType


class AssetNavigatorWidget(QtWidgets.QWidget):
    """
    Asset/Shot Navigator widget with enhanced template management.
    
    Provides context-aware navigation through project hierarchy with:
    - Project settings configuration
    - Shot navigator (Episode → Sequence → Shot)
    - Asset navigator (Category → Subcategory → Asset)
    - File lists with context menus
    - Template integration
    """
    
    # Signals for communication with main window
    file_selected = QtCore.Signal(str)  # Emitted when file is selected
    context_changed = QtCore.Signal(dict)  # Emitted when navigation context changes
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the Asset Navigator widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize ProjectManager for real file operations
        self._project_manager = ProjectManager()
        self._current_context = {}

        # Make widget resizable
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setMinimumSize(400, 450)
        self.resize(500, 650)

        self._setup_ui()
        self._connect_signals()
        self._populate_initial_data()

        print("SUCCESS: AssetNavigatorWidget initialized with real ProjectManager")
    
    def _setup_ui(self) -> None:
        """Set up the user interface according to UI design specifications."""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create UI sections
        self._create_project_settings()
        self._create_navigation_section()
        self._create_action_buttons()

        # Add sections to main layout
        main_layout.addWidget(self.project_settings_group)
        main_layout.addWidget(self.navigation_group)
        main_layout.addWidget(self.action_buttons_group)
        main_layout.addStretch()
    
    def _create_project_settings(self) -> None:
        """Create project settings section."""
        self.project_settings_group = QtWidgets.QGroupBox("Project Settings")
        layout = QtWidgets.QHBoxLayout(self.project_settings_group)
        
        # Project root path
        layout.addWidget(QtWidgets.QLabel("Project Root:"))
        
        self.project_root_edit = QtWidgets.QLineEdit()
        self.project_root_edit.setText(settings.get_project_root())
        self.project_root_edit.setStyleSheet("font-family: monospace;")
        layout.addWidget(self.project_root_edit)
        
        # Browse button
        self.browse_project_btn = QtWidgets.QPushButton("Browse")
        layout.addWidget(self.browse_project_btn)
    
    def _create_navigation_section(self) -> None:
        """Create unified navigation section with mode selector and department dropdown."""
        self.navigation_group = QtWidgets.QGroupBox("Navigation")
        main_nav_layout = QtWidgets.QVBoxLayout(self.navigation_group)

        # Mode selector (Shot vs Asset workflow)
        self._create_mode_selector()
        main_nav_layout.addWidget(self.mode_selector_group)

        # Unified navigation controls
        self._create_navigation_controls()
        main_nav_layout.addWidget(self.navigation_controls_group)

        # Department selector
        self._create_department_selector()
        main_nav_layout.addWidget(self.department_group)

        # File list
        self._create_file_list()
        main_nav_layout.addWidget(self.file_list_group)
    
    def _create_mode_selector(self) -> None:
        """Create mode selector (Shot vs Asset workflow)."""
        self.mode_selector_group = QtWidgets.QGroupBox("Workflow Mode")
        layout = QtWidgets.QHBoxLayout(self.mode_selector_group)

        # Mode radio buttons
        self.shot_mode_radio = QtWidgets.QRadioButton("Shot Workflow")
        self.asset_mode_radio = QtWidgets.QRadioButton("Asset Workflow")
        self.shot_mode_radio.setChecked(True)  # Default to shot mode

        layout.addWidget(self.shot_mode_radio)
        layout.addWidget(self.asset_mode_radio)
        layout.addStretch()

    def _create_navigation_controls(self) -> None:
        """Create unified navigation controls that change based on mode."""
        self.navigation_controls_group = QtWidgets.QGroupBox("Navigation Path")
        self.controls_layout = QtWidgets.QGridLayout(self.navigation_controls_group)

        # Initialize all combo boxes (will be shown/hidden based on mode)
        # Shot workflow controls
        self.episode_combo = QtWidgets.QComboBox()
        self.episode_combo.setEditable(True)
        self.sequence_combo = QtWidgets.QComboBox()
        self.sequence_combo.setEditable(True)
        self.shot_combo = QtWidgets.QComboBox()
        self.shot_combo.setEditable(True)

        # Asset workflow controls
        self.asset_category_combo = QtWidgets.QComboBox()
        self.asset_category_combo.setEditable(True)
        self.asset_subcategory_combo = QtWidgets.QComboBox()
        self.asset_subcategory_combo.setEditable(True)
        self.asset_combo = QtWidgets.QComboBox()
        self.asset_combo.setEditable(True)

        # Labels
        self.episode_label = QtWidgets.QLabel("Episode:")
        self.sequence_label = QtWidgets.QLabel("Sequence:")
        self.shot_label = QtWidgets.QLabel("Shot:")
        self.category_label = QtWidgets.QLabel("Category:")
        self.subcategory_label = QtWidgets.QLabel("Subcategory:")
        self.asset_label = QtWidgets.QLabel("Asset:")

        # Start with shot mode layout
        self._setup_shot_mode_layout()

    def _create_department_selector(self) -> None:
        """Create department selector dropdown."""
        self.department_group = QtWidgets.QGroupBox("Department")
        layout = QtWidgets.QHBoxLayout(self.department_group)

        layout.addWidget(QtWidgets.QLabel("Department:"))
        self.department_combo = QtWidgets.QComboBox()
        self.department_combo.setEditable(True)
        layout.addWidget(self.department_combo)
        layout.addStretch()

    def _create_file_list(self) -> None:
        """Create unified file list for version files."""
        self.file_list_group = QtWidgets.QGroupBox("Version Files")
        layout = QtWidgets.QVBoxLayout(self.file_list_group)

        # Path display
        self.current_path_label = QtWidgets.QLabel("Path: Not selected")
        self.current_path_label.setStyleSheet("font-family: monospace; color: #666;")
        layout.addWidget(self.current_path_label)

        # File list
        self.files_list = QtWidgets.QListWidget()
        self.files_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        layout.addWidget(self.files_list)

    def _setup_shot_mode_layout(self) -> None:
        """Setup layout for shot workflow mode."""
        # Clear existing layout
        for i in reversed(range(self.controls_layout.count())):
            self.controls_layout.itemAt(i).widget().setParent(None)

        # Add shot workflow controls
        self.controls_layout.addWidget(self.episode_label, 0, 0)
        self.controls_layout.addWidget(self.episode_combo, 0, 1)
        self.controls_layout.addWidget(self.sequence_label, 1, 0)
        self.controls_layout.addWidget(self.sequence_combo, 1, 1)
        self.controls_layout.addWidget(self.shot_label, 2, 0)
        self.controls_layout.addWidget(self.shot_combo, 2, 1)

    def _setup_asset_mode_layout(self) -> None:
        """Setup layout for asset workflow mode."""
        # Clear existing layout
        for i in reversed(range(self.controls_layout.count())):
            self.controls_layout.itemAt(i).widget().setParent(None)

        # Add asset workflow controls
        self.controls_layout.addWidget(self.category_label, 0, 0)
        self.controls_layout.addWidget(self.asset_category_combo, 0, 1)
        self.controls_layout.addWidget(self.subcategory_label, 1, 0)
        self.controls_layout.addWidget(self.asset_subcategory_combo, 1, 1)
        self.controls_layout.addWidget(self.asset_label, 2, 0)
        self.controls_layout.addWidget(self.asset_combo, 2, 1)
    
    def _create_action_buttons(self) -> None:
        """Create action buttons section."""
        self.action_buttons_group = QtWidgets.QGroupBox("Actions")
        layout = QtWidgets.QHBoxLayout(self.action_buttons_group)
        
        # File operations
        self.refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        self.reference_btn = QtWidgets.QPushButton("🔗 Reference")

        # Add buttons to layout
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.reference_btn)
        layout.addStretch()
    
    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        # Project settings
        self.browse_project_btn.clicked.connect(self._on_browse_project)
        self.project_root_edit.textChanged.connect(self._on_project_root_changed)

        # Mode selector
        self.shot_mode_radio.toggled.connect(self._on_mode_changed)
        self.asset_mode_radio.toggled.connect(self._on_mode_changed)

        # Navigation controls (both shot and asset)
        self.episode_combo.currentTextChanged.connect(self._on_episode_changed)
        self.sequence_combo.currentTextChanged.connect(self._on_sequence_changed)
        self.shot_combo.currentTextChanged.connect(self._on_shot_changed)
        self.asset_category_combo.currentTextChanged.connect(self._on_asset_category_changed)
        self.asset_subcategory_combo.currentTextChanged.connect(self._on_asset_subcategory_changed)
        self.asset_combo.currentTextChanged.connect(self._on_asset_changed)

        # Department selector
        self.department_combo.currentTextChanged.connect(self._on_department_changed)

        # Unified file list
        self.files_list.customContextMenuRequested.connect(self._show_file_context_menu)

        # Action buttons
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.reference_btn.clicked.connect(self._on_reference)
    
    def _populate_initial_data(self) -> None:
        """Populate initial data from real ProjectManager based on current mode."""
        if self.shot_mode_radio.isChecked():
            # Shot workflow mode - populate episode data
            self._populate_episodes()
            if self.episode_combo.count() > 1:
                self.episode_combo.setCurrentIndex(1)  # Skip "[Select...]" item
        else:
            # Asset workflow mode - populate category data
            self._populate_asset_categories()
            if self.asset_category_combo.count() > 1:
                self.asset_category_combo.setCurrentIndex(1)  # Skip "[Select...]" item

        # Initialize departments
        self._populate_departments()

    def _populate_episodes(self) -> None:
        """Populate episodes from real project structure."""
        self.episode_combo.clear()
        self.episode_combo.addItem("[Select Episode]")

        try:
            episodes = self._project_manager.get_episodes()  # This returns a list
            if episodes:
                for episode in sorted(episodes):  # episodes is already a list, not dict
                    self.episode_combo.addItem(episode)
                print(f"SUCCESS: Loaded {len(episodes)} episodes: {episodes}")
            else:
                print("WARNING: No episodes found in project structure")
        except Exception as e:
            print(f"ERROR: Error loading episodes: {e}")
            # No fallback - show empty list if real data fails

    def _populate_sequences(self, episode: str) -> None:
        """Populate sequences for selected episode."""
        self.sequence_combo.clear()
        self.sequence_combo.addItem("[Select Sequence]")

        if not episode or episode.startswith("[Select"):
            return

        try:
            sequences = self._project_manager.get_sequences_for_episode(episode)
            if sequences:
                for sequence in sorted(sequences):
                    self.sequence_combo.addItem(sequence)
                print(f"SUCCESS: Loaded {len(sequences)} sequences for {episode}: {sequences}")
            else:
                print(f"WARNING: No sequences found for episode {episode}")
        except Exception as e:
            print(f"ERROR: Error loading sequences for {episode}: {e}")

    def _populate_shots(self, sequence: str) -> None:
        """Populate shots for selected sequence."""
        self.shot_combo.clear()
        self.shot_combo.addItem("[Select Shot]")

        if not sequence or sequence.startswith("[Select"):
            return

        try:
            shots = self._project_manager.get_shots_for_sequence(sequence)
            if shots:
                for shot in sorted(shots):
                    self.shot_combo.addItem(shot)
                print(f"✅ Loaded {len(shots)} shots for {sequence}")
            else:
                print(f"📁 No shots found for sequence {sequence}")
        except Exception as e:
            print(f"❌ Error loading shots for {sequence}: {e}")

    def _populate_asset_categories(self) -> None:
        """Populate asset categories from real project structure."""
        self.asset_category_combo.clear()
        self.asset_category_combo.addItem("[Select Category]")

        try:
            categories = self._project_manager.get_categories()  # Fixed method name
            if categories:
                for category in sorted(categories):  # categories is a list, not dict
                    self.asset_category_combo.addItem(category)
                print(f"✅ Loaded {len(categories)} asset categories")
            else:
                print("📁 No asset categories found in project structure")
        except Exception as e:
            print(f"❌ Error loading asset categories: {e}")
            # No fallback - show empty list if real data fails

    def _populate_asset_subcategories(self, category: str) -> None:
        """Populate asset subcategories for selected category."""
        self.asset_subcategory_combo.clear()
        self.asset_subcategory_combo.addItem("[Select Subcategory]")

        if not category or category.startswith("[Select"):
            return

        try:
            subcategories = self._project_manager.get_subcategories_for_category(category)
            if subcategories:
                for subcategory in sorted(subcategories):
                    self.asset_subcategory_combo.addItem(subcategory)
                print(f"✅ Loaded {len(subcategories)} subcategories for {category}")
            else:
                print(f"📁 No subcategories found for category {category}")
        except Exception as e:
            print(f"❌ Error loading subcategories for {category}: {e}")

    def _populate_assets(self, subcategory: str) -> None:
        """Populate assets for selected subcategory."""
        self.asset_combo.clear()
        self.asset_combo.addItem("[Select Asset]")

        if not subcategory or subcategory.startswith("[Select"):
            return

        try:
            assets = self._project_manager.get_assets_for_subcategory(subcategory)
            if assets:
                for asset in sorted(assets):
                    self.asset_combo.addItem(asset)
                print(f"✅ Loaded {len(assets)} assets for {subcategory}")
            else:
                print(f"📁 No assets found for subcategory {subcategory}")
        except Exception as e:
            print(f"❌ Error loading assets for {subcategory}: {e}")

    # Event handlers (placeholder implementations)
    def _on_browse_project(self) -> None:
        """Handle browse project button click."""
        print("🚧 Placeholder: Browse project root")

        # Mock: Show file dialog
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setWindowTitle("Select Project Root Directory")

        if dialog.exec_():
            selected_dirs = dialog.selectedFiles()
            if selected_dirs:
                project_root = selected_dirs[0]
                self.project_root_edit.setText(project_root)
                print(f"🚧 Mock: Project root set to {project_root}")

    def _on_project_root_changed(self, text: str) -> None:
        """Handle project root path change with real hierarchy refresh."""
        print(f"🔄 Project root changed to: {text}")

        # Update settings
        settings.set("project.project_root", text)

        # Update ProjectManager with new root
        self._project_manager.project_root = text
        self._project_manager._mock_data_initialized = False

        # Refresh all hierarchy data
        self._populate_initial_data()

        print("SUCCESS: Project hierarchy refreshed for new root")

    def _on_episode_changed(self, episode: str) -> None:
        """Handle episode selection change with real data population."""
        print(f"INFO: Episode changed to: {episode}")

        # Populate sequences for selected episode
        self._populate_sequences(episode)

        # Clear downstream selections
        self.shot_combo.clear()
        self.shot_combo.addItem("[Select Shot]")

        # Refresh files and context
        self._refresh_shot_files()
        self._update_context()

    def _on_sequence_changed(self, sequence: str) -> None:
        """Handle sequence selection change with real data population."""
        print(f"🔄 Sequence changed to: {sequence}")

        # Populate shots for selected sequence
        self._populate_shots(sequence)

        # Refresh files and context
        self._refresh_shot_files()
        self._update_context()

    def _on_shot_changed(self, shot: str) -> None:
        """Handle shot selection change."""
        print(f"INFO: Shot changed to: {shot}")
        self._populate_departments()
        self._update_context()

    def _on_asset_category_changed(self, category: str) -> None:
        """Handle asset category selection change with real data population."""
        print(f"🔄 Asset category changed to: {category}")

        # Populate subcategories for selected category
        self._populate_asset_subcategories(category)

        # Clear downstream selections
        self.asset_combo.clear()
        self.asset_combo.addItem("[Select Asset]")

        # Refresh files and context
        self._refresh_asset_files()
        self._update_context()

    def _on_asset_subcategory_changed(self, subcategory: str) -> None:
        """Handle asset subcategory selection change with real data population."""
        print(f"🔄 Asset subcategory changed to: {subcategory}")

        # Populate assets for selected subcategory
        self._populate_assets(subcategory)

        # Refresh files and context
        self._refresh_asset_files()
        self._update_context()

    def _on_asset_changed(self, asset: str) -> None:
        """Handle asset selection change."""
        print(f"INFO: Asset changed to: {asset}")
        self._populate_departments()
        self._update_context()

    def _on_mode_changed(self) -> None:
        """Handle workflow mode change between Shot and Asset."""
        if self.shot_mode_radio.isChecked():
            print("INFO: Switched to Shot workflow mode")
            self._setup_shot_mode_layout()
            self._populate_initial_data()  # Reload data for shot mode
        else:
            print("INFO: Switched to Asset workflow mode")
            self._setup_asset_mode_layout()
            self._populate_initial_data()  # Reload data for asset mode

    def _on_department_changed(self, department: str) -> None:
        """Handle department selection change."""
        print(f"INFO: Department changed to: {department}")
        self._refresh_version_files()
        self._update_current_path()
        self._update_context()

    def _populate_departments(self) -> None:
        """Populate department dropdown based on current specific context."""
        self.department_combo.clear()
        self.department_combo.addItem("[Select Department]")

        try:
            departments = []
            if self.shot_mode_radio.isChecked():
                # Get departments for specific shot
                episode = self.episode_combo.currentText()
                sequence = self.sequence_combo.currentText()
                shot = self.shot_combo.currentText()

                if not any(x.startswith("[Select") for x in [episode, sequence, shot]):
                    departments = self._project_manager.get_departments_for_shot(episode, sequence, shot)
            else:
                # Get departments for specific asset
                category = self.asset_category_combo.currentText()
                subcategory = self.asset_subcategory_combo.currentText()
                asset = self.asset_combo.currentText()

                if not any(x.startswith("[Select") for x in [category, subcategory, asset]):
                    departments = self._project_manager.get_departments_for_asset(category, subcategory, asset)

            for dept in departments:
                self.department_combo.addItem(dept)

            print(f"SUCCESS: Loaded {len(departments)} departments for current context: {departments}")
        except Exception as e:
            print(f"ERROR: Error loading departments: {e}")

    def _refresh_version_files(self) -> None:
        """Refresh version files list from the version directory."""
        print("INFO: Refreshing version files from version directory")

        # Clear current list
        self.files_list.clear()

        # Get current path
        current_path = self._get_current_version_path()
        if not current_path or not os.path.exists(current_path):
            print(f"WARNING: Version directory not found: {current_path}")
            return

        try:
            # List files in version directory
            version_files = []
            for file_path in glob.glob(os.path.join(current_path, "*")):
                if os.path.isfile(file_path):
                    file_info = {
                        'name': os.path.basename(file_path),
                        'path': file_path,
                        'modified': os.path.getmtime(file_path)
                    }
                    version_files.append(file_info)

            # Sort by modification time (newest first)
            version_files.sort(key=lambda x: x['modified'], reverse=True)

            # Add to list widget
            for file_info in version_files:
                item = QtWidgets.QListWidgetItem(file_info['name'])
                item.setData(QtCore.Qt.UserRole, file_info['path'])

                # Set file type icon based on name
                if 'hero' in file_info['name'].lower():
                    item.setText(f"👑 {file_info['name']}")
                elif 'template' in file_info['name'].lower():
                    item.setText(f"📋 {file_info['name']}")
                else:
                    item.setText(f"📝 {file_info['name']}")

                self.files_list.addItem(item)

            print(f"SUCCESS: Loaded {len(version_files)} version files")

        except Exception as e:
            print(f"ERROR: Error loading version files: {e}")

    def _get_current_version_path(self) -> str:
        """Get the current version directory path based on selection."""
        base_path = self.project_root_edit.text() or self._project_manager.project_root
        department = self.department_combo.currentText()

        if department.startswith("[Select"):
            return ""

        if self.shot_mode_radio.isChecked():
            # Shot path: V:\SWA\all\scene\Ep01\sq0040\SH0210\light\version
            episode = self.episode_combo.currentText()
            sequence = self.sequence_combo.currentText()
            shot = self.shot_combo.currentText()

            if any(x.startswith("[Select") for x in [episode, sequence, shot]):
                return ""

            version_path = os.path.join(base_path, "scene", episode, sequence, shot, department, "version")
        else:
            # Asset path: V:\SWA\all\assets\category\subcategory\asset\department\version
            category = self.asset_category_combo.currentText()
            subcategory = self.asset_subcategory_combo.currentText()
            asset = self.asset_combo.currentText()

            if any(x.startswith("[Select") for x in [category, subcategory, asset]):
                return ""

            version_path = os.path.join(base_path, "assets", category, subcategory, asset, department, "version")

        return version_path

    def _update_current_path(self) -> None:
        """Update the current path display."""
        path = self._get_current_version_path()
        if path:
            self.current_path_label.setText(f"Path: {path}")
        else:
            self.current_path_label.setText("Path: Not selected")

    def _refresh_shot_files(self) -> None:
        """Refresh shot files list with real ProjectManager data."""
        print("🔄 Refreshing shot files from ProjectManager")

        # Clear current list
        self.shot_files_list.clear()

        # Get current navigation context
        context = self._get_current_navigation_context()
        if not context or context.type != ProjectType.SHOT:
            print("Invalid shot context")
            return

        # Get real files from ProjectManager
        try:
            files = self._project_manager.get_files_for_context(context)

            if not files:
                self.shot_files_list.addItem("📁 No files found in this location")
                return

            # Convert FileInfo objects to display strings
            file_items = []
            for file_info in files:
                # Format file display string
                if file_info.is_directory:
                    icon = "📁"
                    display_name = f"{file_info.name}/"
                else:
                    # Choose icon based on file type
                    if file_info.file_type == "ma" or file_info.file_type == "mb":
                        if "hero" in file_info.name.lower():
                            icon = "👑"
                        elif "template" in file_info.name.lower():
                            icon = "📋"
                        elif "lighting" in file_info.name.lower():
                            icon = "💡"
                        else:
                            icon = "📝"
                    elif file_info.file_type in ["exr", "jpg", "png", "tif"]:
                        icon = "🖼"
                    elif file_info.file_type == "json":
                        icon = "📄"
                    else:
                        icon = "📄"

                    # Format with date
                    date_str = file_info.modified_date.strftime("%Y-%m-%d %H:%M")
                    display_name = f"{file_info.name} - {date_str}"

                file_items.append(f"{icon} {display_name}")

            self.shot_files_list.addItems(file_items)
            print(f"✅ Loaded {len(files)} items for shot context")

        except Exception as e:
            print(f"Error refreshing shot files: {e}")
            self.shot_files_list.addItem("❌ Error loading files")

    def _refresh_asset_files(self) -> None:
        """Refresh asset files list with real ProjectManager data."""
        print("🔄 Refreshing asset files from ProjectManager")

        # Clear current list
        self.asset_files_list.clear()

        # Get current navigation context
        context = self._get_current_navigation_context()
        if not context or context.type != ProjectType.ASSET:
            print("Invalid asset context")
            return

        # Get real files from ProjectManager
        try:
            files = self._project_manager.get_files_for_context(context)

            if not files:
                self.asset_files_list.addItem("📁 No files found in this location")
                return

            # Convert FileInfo objects to display strings
            file_items = []
            for file_info in files:
                # Format file display string
                if file_info.is_directory:
                    icon = "📁"
                    display_name = f"{file_info.name}/"
                else:
                    # Choose icon based on file type
                    if file_info.file_type == "ma" or file_info.file_type == "mb":
                        if "hero" in file_info.name.lower():
                            icon = "👑"
                        elif "template" in file_info.name.lower():
                            icon = "📋"
                        elif "lighting" in file_info.name.lower():
                            icon = "💡"
                        else:
                            icon = "📝"
                    elif file_info.file_type in ["exr", "jpg", "png", "tif"]:
                        icon = "🖼"
                    elif file_info.file_type == "json":
                        icon = "📄"
                    else:
                        icon = "📄"

                    # Format with date
                    date_str = file_info.modified_date.strftime("%Y-%m-%d %H:%M")
                    display_name = f"{file_info.name} - {date_str}"

                file_items.append(f"{icon} {display_name}")

            self.asset_files_list.addItems(file_items)
            print(f"✅ Loaded {len(files)} items for asset context")

        except Exception as e:
            print(f"Error refreshing asset files: {e}")
            self.asset_files_list.addItem("❌ Error loading files")

    def _update_context(self) -> None:
        """Update current navigation context and emit signal."""
        self._current_context = {
            "episode": self.episode_combo.currentText(),
            "sequence": self.sequence_combo.currentText(),
            "shot": self.shot_combo.currentText(),
            "asset_category": self.asset_category_combo.currentText(),
            "asset_subcategory": self.asset_subcategory_combo.currentText(),
            "asset": self.asset_combo.currentText()
        }

        # Emit context change signal
        self.context_changed.emit(self._current_context)
        print(f"🔄 Context updated: {self._current_context}")

    def _get_current_navigation_context(self) -> Optional[NavigationContext]:
        """Get current navigation context as NavigationContext object."""
        try:
            # Determine if we're in shot or asset mode based on current tab
            current_tab = self.navigation_tabs.currentIndex()

            if current_tab == 0:  # Shot tab
                episode = self.episode_combo.currentText()
                sequence = self.sequence_combo.currentText()
                shot = self.shot_combo.currentText()

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
                    department="lighting"  # Default department
                )

            else:  # Asset tab
                category = self.asset_category_combo.currentText()
                subcategory = self.asset_subcategory_combo.currentText()
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
                    department="lighting"  # Default department
                )

        except Exception as e:
            print(f"Error creating navigation context: {e}")
            return None

    def _get_file_path_from_display(self, display_text: str) -> Optional[str]:
        """Extract actual file path from display text."""
        try:
            # Get current context
            context = self._get_current_navigation_context()
            if not context:
                return None

            # Extract filename from display text (remove emoji and timestamp)
            clean_name = display_text.split(' - ')[0][2:].strip()  # Remove emoji and timestamp
            if clean_name.endswith('/'):
                clean_name = clean_name[:-1]  # Remove trailing slash for directories

            # Get the context path from ProjectManager
            context_path = self._project_manager.get_context_path(context)
            if context_path == "[Invalid Context]":
                return None

            # Combine to get full path
            file_path = os.path.join(context_path, clean_name)
            return file_path

        except Exception as e:
            print(f"Error extracting file path: {e}")
            return None

    def _show_shot_context_menu(self, position: QtCore.QPoint) -> None:
        """Show context menu for shot files list."""
        item = self.shot_files_list.itemAt(position)
        if not item:
            return

        print(f"🚧 Placeholder: Shot context menu for {item.text()}")

        menu = QtWidgets.QMenu(self)
        menu.addAction("📂 Open", lambda: self._context_open(item.text()))
        menu.addAction("🔗 Reference", lambda: self._context_reference(item.text()))
        menu.addAction("📥 Import", lambda: self._context_import(item.text()))
        menu.addSeparator()
        menu.addAction("📁 Show in Explorer", lambda: self._context_show_explorer(item.text()))
        menu.addAction("📋 Copy Path", lambda: self._context_copy_path(item.text()))

        if "📝" in item.text():  # Version file
            menu.addSeparator()
            menu.addAction("👑 Make Hero", lambda: self._context_make_hero(item.text()))

        menu.exec_(self.shot_files_list.mapToGlobal(position))

    def _show_asset_context_menu(self, position: QtCore.QPoint) -> None:
        """Show context menu for asset files list."""
        item = self.asset_files_list.itemAt(position)
        if not item:
            return

        print(f"🚧 Placeholder: Asset context menu for {item.text()}")

        menu = QtWidgets.QMenu(self)
        menu.addAction("📂 Open", lambda: self._context_open(item.text()))
        menu.addAction("🔗 Reference", lambda: self._context_reference(item.text()))
        menu.addAction("📥 Import", lambda: self._context_import(item.text()))
        menu.addSeparator()
        menu.addAction("📁 Show in Explorer", lambda: self._context_show_explorer(item.text()))
        menu.addAction("📋 Copy Path", lambda: self._context_copy_path(item.text()))

        if "📝" in item.text():  # Version file
            menu.addSeparator()
            menu.addAction("👑 Make Hero", lambda: self._context_make_hero(item.text()))

        menu.exec_(self.asset_files_list.mapToGlobal(position))

    def _show_file_context_menu(self, position: QtCore.QPoint) -> None:
        """Show context menu for the unified file list."""
        item = self.files_list.itemAt(position)
        if not item:
            return

        file_path = item.data(QtCore.Qt.UserRole)
        if not file_path:
            return

        print(f"INFO: File context menu for {item.text()}")

        menu = QtWidgets.QMenu(self)
        menu.addAction("📂 Open", lambda: self._context_open_file(file_path))
        menu.addAction("🔗 Reference", lambda: self._context_reference_file(file_path))
        menu.addAction("📥 Import", lambda: self._context_import_file(file_path))
        menu.addSeparator()
        menu.addAction("📁 Show in Explorer", lambda: self._context_show_explorer_file(file_path))
        menu.addAction("📋 Copy Path", lambda: self._context_copy_path_file(file_path))

        if "📝" in item.text():  # Version file
            menu.addSeparator()
            menu.addAction("👑 Make Hero", lambda: self._context_make_hero_file(file_path))

        menu.exec_(self.files_list.mapToGlobal(position))

    # Action button handlers
    def _on_refresh(self) -> None:
        """Handle refresh button click."""
        print("🚧 Placeholder: Refresh all file lists")
        self._refresh_shot_files()
        self._refresh_asset_files()
        QtWidgets.QMessageBox.information(self, "Refresh", "Mock: File lists refreshed successfully!")

    def _on_open(self) -> None:
        """Handle open button click."""
        selected_file = self._get_selected_file()
        if selected_file:
            print(f"🚧 Placeholder: Opening {selected_file}")
            QtWidgets.QMessageBox.information(self, "Open File", f"Mock: Opening {selected_file}")
        else:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a file to open.")

    def _on_reference(self) -> None:
        """Handle reference button click."""
        selected_file = self._get_selected_file()
        if selected_file:
            print(f"🚧 Placeholder: Referencing {selected_file}")
            QtWidgets.QMessageBox.information(self, "Reference File", f"Mock: Referenced {selected_file}")
        else:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a file to reference.")

    def _on_import(self) -> None:
        """Handle import button click."""
        selected_file = self._get_selected_file()
        if selected_file:
            print(f"🚧 Placeholder: Importing {selected_file}")
            QtWidgets.QMessageBox.information(self, "Import File", f"Mock: Imported {selected_file}")
        else:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a file to import.")

    def _on_save_version(self) -> None:
        """Handle save version button click."""
        print("🚧 Placeholder: Save version dialog")

        # Mock version save dialog
        version_name, ok = QtWidgets.QInputDialog.getText(
            self, "Save Version", "Enter version description:",
            text="lighting_update"
        )

        if ok and version_name:
            context = self._get_current_context_string()
            QtWidgets.QMessageBox.information(
                self, "Version Saved",
                f"Mock: Version saved successfully!\n\n"
                f"Context: {context}\n"
                f"Description: {version_name}\n"
                f"File: scene_v006.ma"
            )

    def _on_export_template(self) -> None:
        """Handle export template button click."""
        print("🚧 Placeholder: Export template dialog")

        # Mock template export dialog
        template_name, ok = QtWidgets.QInputDialog.getText(
            self, "Export Template", "Enter template name:",
            text="master_lighting_template"
        )

        if ok and template_name:
            context = self._get_current_context_string()
            QtWidgets.QMessageBox.information(
                self, "Template Exported",
                f"Mock: Template exported successfully!\n\n"
                f"Template: {template_name}\n"
                f"Context: {context}\n"
                f"Package contents:\n"
                f"• Maya light rig (.ma)\n"
                f"• Render layers (.json)\n"
                f"• Package info (.json)"
            )

    # Context menu handlers
    def _context_open(self, filename: str) -> None:
        """Handle context menu open action with real Maya operations."""
        file_path = self._get_file_path_from_display(filename)
        if not file_path:
            QtWidgets.QMessageBox.warning(self, "Error", "Could not determine file path")
            return

        # Check if file exists
        if not os.path.exists(file_path):
            QtWidgets.QMessageBox.warning(self, "Error", f"File not found:\n{file_path}")
            return

        # Check if it's a directory
        if os.path.isdir(file_path):
            QtWidgets.QMessageBox.information(self, "Directory", "Cannot open directory as Maya file")
            return

        try:
            # Try Maya API first
            import maya.cmds as cmds

            # Check if scene has unsaved changes
            if cmds.file(q=True, modified=True):
                reply = QtWidgets.QMessageBox.question(
                    self, "Unsaved Changes",
                    "Current scene has unsaved changes. Save before opening new file?",
                    QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
                )

                if reply == QtWidgets.QMessageBox.Save:
                    cmds.file(save=True)
                elif reply == QtWidgets.QMessageBox.Cancel:
                    return

            # Open the file
            cmds.file(file_path, open=True, force=True)
            QtWidgets.QMessageBox.information(self, "Success", f"Opened:\n{os.path.basename(file_path)}")
            print(f"✅ Opened file: {file_path}")

        except ImportError:
            QtWidgets.QMessageBox.warning(self, "Maya Not Available",
                                        "Maya API not available. Cannot open Maya files.")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to open file:\n{str(e)}")
            print(f"❌ Error opening file: {e}")

    def _context_reference(self, filename: str) -> None:
        """Handle context menu reference action with real Maya operations."""
        file_path = self._get_file_path_from_display(filename)
        if not file_path:
            QtWidgets.QMessageBox.warning(self, "Error", "Could not determine file path")
            return

        # Check if file exists
        if not os.path.exists(file_path):
            QtWidgets.QMessageBox.warning(self, "Error", f"File not found:\n{file_path}")
            return

        # Check if it's a Maya file
        if not file_path.endswith(('.ma', '.mb')):
            QtWidgets.QMessageBox.warning(self, "Error", "Can only reference Maya scene files (.ma/.mb)")
            return

        try:
            import maya.cmds as cmds

            # Create namespace from filename
            namespace = os.path.splitext(os.path.basename(file_path))[0]
            namespace = namespace.replace('.', '_').replace('-', '_')  # Clean namespace

            # Reference the file
            cmds.file(file_path, reference=True, namespace=namespace)
            QtWidgets.QMessageBox.information(self, "Success",
                                            f"Referenced:\n{os.path.basename(file_path)}\nNamespace: {namespace}")
            print(f"✅ Referenced file: {file_path} with namespace: {namespace}")

        except ImportError:
            QtWidgets.QMessageBox.warning(self, "Maya Not Available",
                                        "Maya API not available. Cannot reference Maya files.")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to reference file:\n{str(e)}")
            print(f"❌ Error referencing file: {e}")

    def _context_import(self, filename: str) -> None:
        """Handle context menu import action with real Maya operations."""
        file_path = self._get_file_path_from_display(filename)
        if not file_path:
            QtWidgets.QMessageBox.warning(self, "Error", "Could not determine file path")
            return

        # Check if file exists
        if not os.path.exists(file_path):
            QtWidgets.QMessageBox.warning(self, "Error", f"File not found:\n{file_path}")
            return

        # Check if it's a Maya file
        if not file_path.endswith(('.ma', '.mb')):
            QtWidgets.QMessageBox.warning(self, "Error", "Can only import Maya scene files (.ma/.mb)")
            return

        try:
            import maya.cmds as cmds

            # Create namespace from filename
            namespace = os.path.splitext(os.path.basename(file_path))[0]
            namespace = namespace.replace('.', '_').replace('-', '_')  # Clean namespace

            # Import the file
            cmds.file(file_path, i=True, namespace=namespace)
            QtWidgets.QMessageBox.information(self, "Success",
                                            f"Imported:\n{os.path.basename(file_path)}\nNamespace: {namespace}")
            print(f"✅ Imported file: {file_path} with namespace: {namespace}")

        except ImportError:
            QtWidgets.QMessageBox.warning(self, "Maya Not Available",
                                        "Maya API not available. Cannot import Maya files.")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to import file:\n{str(e)}")
            print(f"❌ Error importing file: {e}")

    def _context_show_explorer(self, filename: str) -> None:
        """Handle context menu show in explorer action."""
        file_path = self._get_file_path_from_display(filename)
        if not file_path:
            QtWidgets.QMessageBox.warning(self, "Error", "Could not determine file path")
            return

        try:
            import subprocess
            import platform

            # Get the directory containing the file
            if os.path.isfile(file_path):
                directory = os.path.dirname(file_path)
            else:
                directory = file_path

            # Open file explorer based on platform
            if platform.system() == "Windows":
                if os.path.isfile(file_path):
                    # Select the file in explorer
                    subprocess.run(['explorer', '/select,', file_path])
                else:
                    # Open the directory
                    subprocess.run(['explorer', directory])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(['open', '-R', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', directory])

            print(f"✅ Opened explorer for: {file_path}")

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to open explorer:\n{str(e)}")
            print(f"❌ Error opening explorer: {e}")

    def _context_copy_path(self, filename: str) -> None:
        """Handle context menu copy path action."""
        file_path = self._get_file_path_from_display(filename)
        if not file_path:
            QtWidgets.QMessageBox.warning(self, "Error", "Could not determine file path")
            return

        try:
            # Copy to clipboard
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(file_path)

            QtWidgets.QMessageBox.information(self, "Path Copied",
                                            f"Path copied to clipboard:\n{file_path}")
            print(f"✅ Copied path to clipboard: {file_path}")

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to copy path:\n{str(e)}")
            print(f"❌ Error copying path: {e}")

    def _context_make_hero(self, filename: str) -> None:
        """Handle context menu make hero action with real version management."""
        file_path = self._get_file_path_from_display(filename)
        if not file_path:
            QtWidgets.QMessageBox.warning(self, "Error", "Could not determine file path")
            return

        # Check if file exists
        if not os.path.exists(file_path):
            QtWidgets.QMessageBox.warning(self, "Error", f"File not found:\n{file_path}")
            return

        # Check if it's a version file
        if not any(pattern in os.path.basename(file_path) for pattern in ['_v', '_V']):
            QtWidgets.QMessageBox.warning(self, "Error", "File does not appear to be a version file")
            return

        clean_name = os.path.basename(file_path)
        reply = QtWidgets.QMessageBox.question(
            self, "Make Hero",
            f"Make {clean_name} the new hero file?\n"
            f"This will replace the current hero file.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            try:
                # Use our VersionManager to set hero file
                from ...core.version_manager import VersionManager
                from ...core.models import VersionInfo

                version_manager = VersionManager()

                # Create a basic VersionInfo object
                stat = os.stat(file_path)
                version_info = VersionInfo(
                    version_number=1,  # Would need to extract from filename
                    file_path=file_path,
                    file_name=clean_name,
                    file_size=stat.st_size,
                    created_date=datetime.fromtimestamp(stat.st_mtime),
                    created_by="Unknown",
                    is_hero=False,
                    is_published=False,
                    comment="Made hero from Asset Navigator",
                    checksum="",
                    metadata={}
                )

                # Set as hero version
                success = version_manager.set_hero_version(version_info)

                if success:
                    QtWidgets.QMessageBox.information(self, "Success",
                                                    f"Successfully made {clean_name} the hero file!")
                    # Refresh the file list to show updated status
                    self._refresh_current_files()
                    print(f"✅ Made hero file: {file_path}")
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", "Failed to set hero file")

            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to make hero file:\n{str(e)}")
                print(f"❌ Error making hero file: {e}")

    def _refresh_current_files(self) -> None:
        """Refresh the currently active file list."""
        current_tab = self.navigation_tabs.currentIndex()
        if current_tab == 0:  # Shot tab
            self._refresh_shot_files()
        else:  # Asset tab
            self._refresh_asset_files()

    def refresh_hierarchy(self) -> None:
        """Public method to refresh the entire navigation hierarchy."""
        print("🔄 Refreshing navigation hierarchy...")

        # Clear current selections
        current_episode = self.episode_combo.currentText()
        current_sequence = self.sequence_combo.currentText()
        current_shot = self.shot_combo.currentText()
        current_category = self.asset_category_combo.currentText()
        current_subcategory = self.asset_subcategory_combo.currentText()
        current_asset = self.asset_combo.currentText()

        # Refresh hierarchy data
        self._populate_initial_data()

        # Try to restore previous selections if they still exist
        if current_episode and current_episode != "[Select Episode]":
            episode_index = self.episode_combo.findText(current_episode)
            if episode_index >= 0:
                self.episode_combo.setCurrentIndex(episode_index)
                self._on_episode_changed(current_episode)

                if current_sequence and current_sequence != "[Select Sequence]":
                    sequence_index = self.sequence_combo.findText(current_sequence)
                    if sequence_index >= 0:
                        self.sequence_combo.setCurrentIndex(sequence_index)
                        self._on_sequence_changed(current_sequence)

                        if current_shot and current_shot != "[Select Shot]":
                            shot_index = self.shot_combo.findText(current_shot)
                            if shot_index >= 0:
                                self.shot_combo.setCurrentIndex(shot_index)

        if current_category and current_category != "[Select Category]":
            category_index = self.asset_category_combo.findText(current_category)
            if category_index >= 0:
                self.asset_category_combo.setCurrentIndex(category_index)
                self._on_asset_category_changed(current_category)

                if current_subcategory and current_subcategory != "[Select Subcategory]":
                    subcategory_index = self.asset_subcategory_combo.findText(current_subcategory)
                    if subcategory_index >= 0:
                        self.asset_subcategory_combo.setCurrentIndex(subcategory_index)
                        self._on_asset_subcategory_changed(current_subcategory)

                        if current_asset and current_asset != "[Select Asset]":
                            asset_index = self.asset_combo.findText(current_asset)
                            if asset_index >= 0:
                                self.asset_combo.setCurrentIndex(asset_index)

        print("SUCCESS: Navigation hierarchy refresh complete")

    # New unified context menu handlers for file operations
    def _context_open_file(self, file_path: str) -> None:
        """Open file in Maya."""
        try:
            print(f"INFO: Opening file: {file_path}")
            # Maya file operation would go here
            if os.path.exists(file_path):
                print(f"SUCCESS: Would open file: {file_path}")
            else:
                print(f"ERROR: File not found: {file_path}")
        except Exception as e:
            print(f"ERROR: Error opening file: {e}")

    def _context_reference_file(self, file_path: str) -> None:
        """Reference file in Maya."""
        try:
            print(f"INFO: Referencing file: {file_path}")
            # Maya reference operation would go here
            if os.path.exists(file_path):
                print(f"SUCCESS: Would reference file: {file_path}")
            else:
                print(f"ERROR: File not found: {file_path}")
        except Exception as e:
            print(f"ERROR: Error referencing file: {e}")

    def _context_import_file(self, file_path: str) -> None:
        """Import file in Maya."""
        try:
            print(f"INFO: Importing file: {file_path}")
            # Maya import operation would go here
            if os.path.exists(file_path):
                print(f"SUCCESS: Would import file: {file_path}")
            else:
                print(f"ERROR: File not found: {file_path}")
        except Exception as e:
            print(f"ERROR: Error importing file: {e}")

    def _context_show_explorer_file(self, file_path: str) -> None:
        """Show file in Windows Explorer."""
        try:
            import subprocess
            subprocess.run(['explorer', '/select,', file_path])
            print(f"SUCCESS: Opened explorer for: {file_path}")
        except Exception as e:
            print(f"ERROR: Error opening explorer: {e}")

    def _context_copy_path_file(self, file_path: str) -> None:
        """Copy file path to clipboard."""
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(file_path)
            print(f"SUCCESS: Copied path to clipboard: {file_path}")
        except Exception as e:
            print(f"ERROR: Error copying path: {e}")

    def _context_make_hero_file(self, file_path: str) -> None:
        """Make this file the hero file."""
        try:
            reply = QtWidgets.QMessageBox.question(
                self, "Make Hero",
                f"Make {os.path.basename(file_path)} the new hero file?\n"
                f"This will replace the current hero file.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )

            if reply == QtWidgets.QMessageBox.Yes:
                print(f"SUCCESS: Would make hero file: {file_path}")
                # Hero file operation would go here
        except Exception as e:
            print(f"ERROR: Error making hero file: {e}")

    # Helper methods
    def _get_selected_file(self) -> Optional[str]:
        """Get currently selected file from unified file list."""
        selection = self.files_list.selectedItems()
        if selection:
            return selection[0].text().split(' - ')[0][2:]  # Remove emoji and timestamp
        return None

    def _get_current_context_string(self) -> str:
        """Get current context as formatted string."""
        if self.shot_combo.currentText():
            return f"{self.episode_combo.currentText()}/{self.sequence_combo.currentText()}/{self.shot_combo.currentText()}"
        elif self.asset_combo.currentText():
            return f"{self.asset_category_combo.currentText()}/{self.asset_subcategory_combo.currentText()}/{self.asset_combo.currentText()}"
        else:
            return "No context selected"

    def get_current_context(self) -> Dict[str, Any]:
        """Get current navigation context."""
        return self._current_context.copy()
