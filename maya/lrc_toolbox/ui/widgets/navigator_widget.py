"""
Navigator Widget

This module provides the combined Navigator widget that merges Shot Navigator
and Asset Navigator functionality with a type dropdown selection.
"""

import os
import subprocess
import platform
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
from ...core import ProjectManager, VersionManager, TemplateManager
from ...core.models import NavigationContext, ProjectType
from ...utils.logger import logger
from ...utils.file_operations import FileOperations


class FileOperationWorker(QtCore.QThread):
    """Worker thread for file operations to prevent UI freezing."""

    progress_updated = QtCore.Signal(int, int, str)  # current, total, operation
    operation_completed = QtCore.Signal(bool, str)  # success, message

    def __init__(self, operation: str, source: str, dest: str = None):
        super().__init__()
        self.operation = operation
        self.source = source
        self.dest = dest
        self.file_ops = FileOperations()

    def run(self):
        """Execute the file operation in thread."""
        try:
            # Set up progress callback
            self.file_ops.set_progress_callback(self._progress_callback)

            if self.operation == "copy":
                success, message = self.file_ops.copy_file(self.source, self.dest)
            elif self.operation == "move":
                success, message = self.file_ops.move_file(self.source, self.dest)
            elif self.operation == "delete":
                success, message = self.file_ops.delete_file(self.source)
            else:
                success, message = False, f"Unknown operation: {self.operation}"

            self.operation_completed.emit(success, message)

        except Exception as e:
            logger.log_error("FileOperationWorker", e, f"{self.operation} operation")
            self.operation_completed.emit(False, str(e))

    def _progress_callback(self, current: int, total: int, operation: str):
        """Progress callback for file operations."""
        self.progress_updated.emit(current, total, operation)


class NavigatorWidget(QtWidgets.QWidget):
    """
    Combined Navigator widget for both Shot and Asset navigation.
    
    Provides unified navigation interface with type selection dropdown
    that dynamically changes the available navigation controls.
    """
    
    # Signals for communication with main window
    context_changed = QtCore.Signal(dict)  # Emitted when navigation context changes
    file_selected = QtCore.Signal(str)     # Emitted when file is selected
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the Navigator widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize backend services
        self.project_manager = ProjectManager()
        self.version_manager = VersionManager()
        self.template_manager = TemplateManager()
        self.file_operations = FileOperations()

        self._project_root = settings.get_project_root()
        self._current_context = {}
        self._worker_thread = None

        self._setup_ui()
        self._connect_signals()
        self._populate_initial_data()

        # Connect file operations progress callback
        self.file_operations.set_progress_callback(self._show_progress)

        logger.log_ui_operation("NavigatorWidget", "initialized", self._project_root)

    def _set_combo_status(self, combo: QtWidgets.QComboBox, status: str) -> None:
        """Set combo box enabled state without color styling."""
        try:
            if status == "loading":
                combo.setEnabled(False)
            elif status in ["selected", "error", "default"]:
                combo.setEnabled(True)
            # No color styling - keep Maya default appearance
        except Exception as e:
            logger.log_error("NavigatorWidget", e, f"setting combo status to {status}")
            combo.setEnabled(True)

    def _update_breadcrumb(self) -> None:
        """Update breadcrumb navigation display."""
        try:
            breadcrumb_parts = []

            if self.type_combo.currentText() == "Shot":
                if "episode" in self._current_context:
                    breadcrumb_parts.append(f"📺 {self._current_context['episode']}")
                if "sequence" in self._current_context:
                    breadcrumb_parts.append(f"🎬 {self._current_context['sequence']}")
                if "shot" in self._current_context:
                    breadcrumb_parts.append(f"🎯 {self._current_context['shot']}")
            else:  # Asset
                if "category" in self._current_context:
                    breadcrumb_parts.append(f"📁 {self._current_context['category']}")
                if "subcategory" in self._current_context:
                    breadcrumb_parts.append(f"📂 {self._current_context['subcategory']}")
                if "asset" in self._current_context:
                    breadcrumb_parts.append(f"🎨 {self._current_context['asset']}")

            if "department" in self._current_context:
                breadcrumb_parts.append(f"🏢 {self._current_context['department']}")

            breadcrumb_text = " → ".join(breadcrumb_parts) if breadcrumb_parts else "[No selection]"

            # Update path label with breadcrumb
            if hasattr(self, 'path_label'):
                self.path_label.setText(f"Path: {breadcrumb_text}")

        except Exception as e:
            print(f"Warning: Could not update breadcrumb: {e}")

    def _get_scan_path(self, base_path: str, directory_type: str) -> str:
        """Get the actual path to scan based on directory type selection."""
        if directory_type == "Hero Directory":
            # For assets, hero directory is at asset level
            if "asset" in base_path.lower():
                # Check if base_path already ends with a department (has 6 path parts)
                # V:\SWA\all\asset\Character\Main\Ajay\model (7 parts - includes department)
                # V:\SWA\all\asset\Character\Main\Ajay (6 parts - asset level)
                path_parts = base_path.split(os.sep)
                if len(path_parts) > 6:  # Includes department
                    # Go up one level from department to asset level, then into hero
                    asset_path = os.path.dirname(base_path)
                    hero_path = os.path.join(asset_path, "hero")
                else:  # Already at asset level
                    # Directly go into hero
                    hero_path = os.path.join(base_path, "hero")

                if os.path.exists(hero_path):
                    return hero_path
            return base_path
        else:  # Version Directory
            # For assets, version directory is inside the department
            # base_path = V:\SWA\all\asset\Props\object\ClosetToysG\model
            # version_path = V:\SWA\all\asset\Props\object\ClosetToysG\model\version
            version_path = os.path.join(base_path, "version")
            if os.path.exists(version_path):
                logger.log_directory_access(version_path, "scan_path", success=True)
                return version_path

            versions_path = os.path.join(base_path, "versions")
            if os.path.exists(versions_path):
                logger.log_directory_access(versions_path, "scan_path", success=True)
                return versions_path
            logger.log_directory_access(base_path, "scan_path_fallback", success=True,
                                      error="No version/versions directory found, using base path")
            return base_path

    def _scan_directory(self, path: str, file_filter: str, directory_type: str) -> List[Dict[str, Any]]:
        """Scan directory and return file information."""
        files = []

        try:
            # Get file extensions based on filter
            extensions = self._get_filter_extensions(file_filter)

            # List directory contents first
            dir_contents = os.listdir(path)
            logger.log_directory_access(path, "scan_directory", success=True, item_count=len(dir_contents))
            logger.log_ui_operation("NavigatorWidget", "scan_directory_contents", f"Contents: {dir_contents}")

            # Scan directory
            for item in dir_contents:
                item_path = os.path.join(path, item)

                # Skip directories unless we're looking for specific structure
                if os.path.isdir(item_path):
                    continue

                # Check file extension
                _, ext = os.path.splitext(item)
                if extensions and ext.lower() not in extensions:
                    continue

                # Get file info
                try:
                    stat_info = os.stat(item_path)
                    file_size = self._format_file_size(stat_info.st_size)
                    modified_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")

                    # Extract version info if present
                    version = self._extract_version_from_filename(item)

                    file_info = {
                        'name': item,
                        'path': item_path,
                        'extension': ext.lower(),
                        'size': file_size,
                        'modified': modified_time,
                        'version': version,
                        'is_hero': directory_type == "Hero Directory" and not version
                    }

                    files.append(file_info)

                except OSError as e:
                    print(f"Warning: Could not get info for {item}: {e}")
                    continue

            # Sort files by name
            files.sort(key=lambda x: x['name'].lower())

        except OSError as e:
            print(f"Error scanning directory {path}: {e}")

        return files

    def _get_filter_extensions(self, file_filter: str) -> List[str]:
        """Get file extensions for the selected filter."""
        filter_map = {
            "All Files": [],  # Empty list means all files
            "Maya Files (.ma, .mb)": ['.ma', '.mb'],
            "Lighting Files": ['.ma', '.mb', '.json', '.xml'],
            "Render Files": ['.exr', '.jpg', '.png', '.tif', '.tiff']
        }
        return filter_map.get(file_filter, [])

    def _get_file_icon(self, extension: str) -> str:
        """Get appropriate icon for file type."""
        icon_map = {
            '.ma': '🎬',
            '.mb': '🎬',
            '.json': '📋',
            '.xml': '📋',
            '.exr': '🖼️',
            '.jpg': '🖼️',
            '.jpeg': '🖼️',
            '.png': '🖼️',
            '.tif': '🖼️',
            '.tiff': '🖼️',
            '.py': '🐍',
            '.mel': '📜'
        }
        return icon_map.get(extension.lower(), '📄')

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def _extract_version_from_filename(self, filename: str) -> Optional[str]:
        """Extract version number from filename."""
        import re
        # Look for patterns like v001, v002, etc.
        match = re.search(r'v(\d{3,4})', filename, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create navigation sections
        self._create_project_settings()
        self._create_type_selection()
        self._create_navigation_controls()
        self._create_file_browser()
        self._create_context_templates()
        self._create_action_buttons()

        # Add sections to main layout
        main_layout.addWidget(self.project_settings_group)
        main_layout.addWidget(self.type_group)
        main_layout.addWidget(self.navigation_group)
        main_layout.addWidget(self.file_browser_group)
        main_layout.addWidget(self.context_templates_group)
        main_layout.addWidget(self.actions_group)
        main_layout.addStretch()

        # Add progress bar at footer (initially hidden)
        self._create_progress_bar()
        main_layout.addWidget(self.progress_bar)

    def _create_progress_bar(self) -> None:
        """Create progress bar for file operations."""
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)  # Initially hidden
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Ready")

    def _show_progress(self, current: int, total: int, operation: str) -> None:
        """Show and update progress bar."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{operation}: {current}/{total}")

    def _hide_progress(self) -> None:
        """Hide progress bar."""
        self.progress_bar.setVisible(False)
        self.progress_bar.setFormat("Ready")

    def _show_error_notification(self, title: str, message: str) -> None:
        """Show error notification to user."""
        QtWidgets.QMessageBox.critical(self, title, message)
        logger.log_ui_operation("NavigatorWidget", "error_notification", f"{title}: {message}")

    def _show_warning_notification(self, title: str, message: str) -> None:
        """Show warning notification to user."""
        QtWidgets.QMessageBox.warning(self, title, message)
        logger.log_ui_operation("NavigatorWidget", "warning_notification", f"{title}: {message}")

    def _show_info_notification(self, title: str, message: str) -> None:
        """Show info notification to user."""
        QtWidgets.QMessageBox.information(self, title, message)
        logger.log_ui_operation("NavigatorWidget", "info_notification", f"{title}: {message}")

    def _handle_worker_completion(self, success: bool, message: str) -> None:
        """Handle completion of worker thread operations."""
        self._hide_progress()

        if success:
            self._show_info_notification("Operation Complete", message)
            # Refresh file list to show changes
            self._populate_file_list()
        else:
            self._show_error_notification("Operation Failed", message)

        # Clean up worker thread
        if self._worker_thread:
            self._worker_thread.deleteLater()
            self._worker_thread = None

    def _start_file_operation(self, operation: str, source: str, dest: str = None) -> None:
        """Start a file operation in a worker thread."""
        if self._worker_thread and self._worker_thread.isRunning():
            self._show_warning_notification("Operation in Progress",
                                           "Please wait for the current operation to complete.")
            return

        # Create and start worker thread
        self._worker_thread = FileOperationWorker(operation, source, dest)
        self._worker_thread.progress_updated.connect(self._show_progress)
        self._worker_thread.operation_completed.connect(self._handle_worker_completion)
        self._worker_thread.start()

        logger.log_ui_operation("NavigatorWidget", f"start_{operation}", f"{source} -> {dest or 'N/A'}")

    def _create_project_settings(self) -> None:
        """Create project settings section."""
        self.project_settings_group = QtWidgets.QGroupBox("⚙️ Project Settings")
        layout = QtWidgets.QHBoxLayout(self.project_settings_group)

        # Project root path
        layout.addWidget(QtWidgets.QLabel("Project Root:"))
        self.project_root_edit = QtWidgets.QLineEdit()
        self.project_root_edit.setText(self._project_root or "")
        self.project_root_edit.setPlaceholderText("Select project root directory...")
        layout.addWidget(self.project_root_edit)

        # Browse button
        self.browse_project_btn = QtWidgets.QPushButton("Browse...")
        layout.addWidget(self.browse_project_btn)

        # Validation status
        self.validation_label = QtWidgets.QLabel("✅ Valid")
        self.validation_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.validation_label)

    def _create_type_selection(self) -> None:
        """Create navigation type selection section."""
        self.type_group = QtWidgets.QGroupBox("🧭 Navigation Type")
        layout = QtWidgets.QHBoxLayout(self.type_group)
        
        layout.addWidget(QtWidgets.QLabel("Browse:"))
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["Shot Navigation", "Asset Navigation"])
        layout.addWidget(self.type_combo)
        layout.addStretch()
    
    def _create_navigation_controls(self) -> None:
        """Create dynamic navigation controls section."""
        self.navigation_group = QtWidgets.QGroupBox("📍 Navigation Controls")
        self.navigation_layout = QtWidgets.QGridLayout(self.navigation_group)
        
        # Shot Navigation Controls
        self.navigation_layout.addWidget(QtWidgets.QLabel("Episode:"), 0, 0)
        self.episode_combo = QtWidgets.QComboBox()
        #self.episode_combo.addItems(["[Select Episode]"])  # Will be populated by _populate_initial_data()
        self.navigation_layout.addWidget(self.episode_combo, 0, 1)
        
        self.navigation_layout.addWidget(QtWidgets.QLabel("Sequence:"), 0, 2)
        self.sequence_combo = QtWidgets.QComboBox()
        self.sequence_combo.addItems(["[Select Sequence]"])
        self.navigation_layout.addWidget(self.sequence_combo, 0, 3)
        
        self.navigation_layout.addWidget(QtWidgets.QLabel("Shot:"), 1, 0)
        self.shot_combo = QtWidgets.QComboBox()
        self.shot_combo.addItems(["[Select Shot]"])
        self.navigation_layout.addWidget(self.shot_combo, 1, 1)

        # Department for shot navigation (same row as shot)
        self.navigation_layout.addWidget(QtWidgets.QLabel("Department:"), 1, 2)
        self.shot_department_combo = QtWidgets.QComboBox()
        self.shot_department_combo.addItems(["[Select Department]"])
        self.navigation_layout.addWidget(self.shot_department_combo, 1, 3)
        
        # Asset Navigation Controls (initially hidden)
        self.navigation_layout.addWidget(QtWidgets.QLabel("Category:"), 2, 0)
        self.category_combo = QtWidgets.QComboBox()
        #self.category_combo.addItems(["[Select Category]"])  # Will be populated by _populate_initial_data()
        self.navigation_layout.addWidget(self.category_combo, 2, 1)
        
        self.navigation_layout.addWidget(QtWidgets.QLabel("Subcategory:"), 2, 2)
        self.subcategory_combo = QtWidgets.QComboBox()
        self.subcategory_combo.addItems(["[Select Subcategory]"])
        self.navigation_layout.addWidget(self.subcategory_combo, 2, 3)
        
        self.navigation_layout.addWidget(QtWidgets.QLabel("Asset:"), 3, 0)
        self.asset_combo = QtWidgets.QComboBox()
        self.asset_combo.addItems(["[Select Asset]"])
        self.navigation_layout.addWidget(self.asset_combo, 3, 1)

        # Department (next to asset for asset navigation, shared with shot navigation)
        self.navigation_layout.addWidget(QtWidgets.QLabel("Department:"), 3, 2)
        self.department_combo = QtWidgets.QComboBox()
        self.department_combo.addItems(["[Select Department]"])
        self.navigation_layout.addWidget(self.department_combo, 3, 3)
        
        # Update visibility based on initial type
        self._update_navigation_visibility()

    def _get_active_department_combo(self) -> QtWidgets.QComboBox:
        """Get the active department combo based on navigation type."""
        is_shot = self.type_combo.currentText() == "Shot Navigation"
        return self.shot_department_combo if is_shot else self.department_combo
    
    def _create_file_browser(self) -> None:
        """Create enhanced file browser section with version/hero directory selection."""
        self.file_browser_group = QtWidgets.QGroupBox("📁 Files")
        layout = QtWidgets.QVBoxLayout(self.file_browser_group)

        # File browser controls
        controls_layout = QtWidgets.QHBoxLayout()

        # Directory type selection dropdown
        controls_layout.addWidget(QtWidgets.QLabel("Directory:"))
        self.directory_type_combo = QtWidgets.QComboBox()
        self.directory_type_combo.addItems(["Hero Directory", "Version Directory"])
        self.directory_type_combo.setToolTip("Choose between hero files or versioned files")
        controls_layout.addWidget(self.directory_type_combo)

        # File type filter
        controls_layout.addWidget(QtWidgets.QLabel("Filter:"))
        self.file_filter_combo = QtWidgets.QComboBox()
        self.file_filter_combo.addItems(["All Files", "Maya Files (.ma, .mb)", "Lighting Files", "Render Files"])
        self.file_filter_combo.setToolTip("Filter files by type")
        controls_layout.addWidget(self.file_filter_combo)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Current path display
        self.path_label = QtWidgets.QLabel("Path: [Select navigation options above]")
        self.path_label.setStyleSheet("font-weight: bold; color: #666666; background-color: #f0f0f0; padding: 4px;")
        layout.addWidget(self.path_label)

        # File list with enhanced display
        self.file_list = QtWidgets.QListWidget()
        self.file_list.setMaximumHeight(200)
        self.file_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setSortingEnabled(True)
        layout.addWidget(self.file_list)

        # File details display
        self.file_details_label = QtWidgets.QLabel("Select a file to view details")
        self.file_details_label.setStyleSheet("color: #666666; font-style: italic; padding: 4px;")
        self.file_details_label.setWordWrap(True)
        layout.addWidget(self.file_details_label)

    def _create_context_templates(self) -> None:
        """Create context templates section."""
        self.context_templates_group = QtWidgets.QGroupBox("📋 Context Templates")
        layout = QtWidgets.QVBoxLayout(self.context_templates_group)

        # Current context display
        context_layout = QtWidgets.QHBoxLayout()
        context_layout.addWidget(QtWidgets.QLabel("Context:"))
        self.context_display = QtWidgets.QLabel("[No context selected]")
        self.context_display.setStyleSheet("font-weight: bold; color: #0066cc;")
        context_layout.addWidget(self.context_display)
        context_layout.addStretch()
        layout.addLayout(context_layout)

        # Template list
        self.template_list = QtWidgets.QListWidget()
        self.template_list.setMaximumHeight(150)
        layout.addWidget(self.template_list)

        # Template metadata display
        self.template_metadata = QtWidgets.QLabel("Select a template to view metadata")
        self.template_metadata.setStyleSheet("color: #666666; font-style: italic;")
        self.template_metadata.setWordWrap(True)
        layout.addWidget(self.template_metadata)

    def _create_action_buttons(self) -> None:
        """Create enhanced action buttons section."""
        self.actions_group = QtWidgets.QGroupBox("⚡ Actions")
        layout = QtWidgets.QHBoxLayout(self.actions_group)

        # File operations
        self.open_file_btn = QtWidgets.QPushButton("📂 Open File")
        self.open_file_btn.setToolTip("Open selected file in Maya")

        self.reference_file_btn = QtWidgets.QPushButton("🔗 Reference File")
        self.reference_file_btn.setToolTip("Create Maya reference from selected file")

        # Navigation operations
        self.refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("Refresh file list and project structure")

        self.browse_folder_btn = QtWidgets.QPushButton("📁 Browse Folder")
        self.browse_folder_btn.setToolTip("Open current folder in file explorer")

        # Add buttons to layout
        layout.addWidget(self.open_file_btn)
        layout.addWidget(self.reference_file_btn)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.browse_folder_btn)
        layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        # Project settings
        self.project_root_edit.textChanged.connect(self._on_project_root_changed)
        self.browse_project_btn.clicked.connect(self._on_browse_project_root)

        # Type selection
        self.type_combo.currentTextChanged.connect(self._on_type_changed)

        # Navigation controls
        self.episode_combo.currentTextChanged.connect(self._on_episode_changed)
        self.sequence_combo.currentTextChanged.connect(self._on_sequence_changed)
        self.shot_combo.currentTextChanged.connect(self._on_shot_changed)
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        self.subcategory_combo.currentTextChanged.connect(self._on_subcategory_changed)
        self.asset_combo.currentTextChanged.connect(self._on_asset_changed)
        self.department_combo.currentTextChanged.connect(self._on_department_changed)
        self.shot_department_combo.currentTextChanged.connect(self._on_department_changed)

        # File browser
        self.file_list.itemDoubleClicked.connect(self._on_file_double_clicked)
        self.file_list.itemSelectionChanged.connect(self._on_file_selection_changed)
        self.file_list.customContextMenuRequested.connect(self._show_context_menu)
        self.directory_type_combo.currentTextChanged.connect(self._on_directory_type_changed)
        self.file_filter_combo.currentTextChanged.connect(self._on_file_filter_changed)

        # Context templates
        self.template_list.itemSelectionChanged.connect(self._on_template_selection_changed)

        # Action buttons
        self.open_file_btn.clicked.connect(self._on_open_file)
        self.reference_file_btn.clicked.connect(self._on_reference_file)
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.browse_folder_btn.clicked.connect(self._on_browse_folder)

    def _populate_initial_data(self) -> None:
        """Populate initial data for navigation controls."""
        # Validate project path
        self._validate_project_path()

        # Set initial type
        self.type_combo.setCurrentText("Shot Navigation")
        self._update_navigation_visibility()

        # Populate episodes from project manager
        episodes = self.project_manager.get_episodes()
        logger.log_ui_operation("NavigatorWidget", "populate_episodes", f"Found episodes: {episodes}")
        self.episode_combo.addItems(["[Select Episode]"] + episodes)

        # Populate categories from project manager
        categories = self.project_manager.get_categories()
        logger.log_ui_operation("NavigatorWidget", "populate_categories", f"Found categories: {categories}")
        self.category_combo.addItems(["[Select Category]"] + categories)

    # Event handlers
    def _on_project_root_changed(self, path: str) -> None:
        """Handle project root path change."""
        self._project_root = path
        self._validate_project_path()

    def _on_browse_project_root(self) -> None:
        """Handle browse project root button click."""
        current_path = self.project_root_edit.text() or self._project_root or ""
        dialog = QtWidgets.QFileDialog()
        selected_path = dialog.getExistingDirectory(
            self, "Select Project Root Directory", current_path
        )

        if selected_path:
            self.project_root_edit.setText(selected_path)
            self._project_root = selected_path
            self._validate_project_path()
            # Save to settings
            settings.set_project_root(selected_path)
            # Update project manager with new root and refresh structure
            self.project_manager.set_project_root(selected_path)
            # Refresh the navigation data
            self._refresh_navigation_data()

    def _refresh_navigation_data(self) -> None:
        """Refresh navigation data from project manager."""
        # Clear existing data
        self.episode_combo.clear()
        self.sequence_combo.clear()
        self.shot_combo.clear()
        self.category_combo.clear()
        self.subcategory_combo.clear()
        self.asset_combo.clear()
        self.department_combo.clear()

        # Repopulate with fresh data
        episodes = self.project_manager.get_episodes()
        logger.log_ui_operation("NavigatorWidget", "refresh_episodes", f"Refreshed episodes: {episodes}")
        self.episode_combo.addItems(["[Select Episode]"] + episodes)

        categories = self.project_manager.get_categories()
        logger.log_ui_operation("NavigatorWidget", "refresh_categories", f"Refreshed categories: {categories}")
        self.category_combo.addItems(["[Select Category]"] + categories)

        logger.log_ui_operation("NavigatorWidget", "refresh_complete", f"{len(episodes)} episodes, {len(categories)} categories")

    def _validate_project_path(self) -> None:
        """Validate the current project path with Maya workspace fallback."""
        if not self._project_root:
            # Try Maya workspace as fallback
            maya_workspace = self._get_maya_workspace()
            if maya_workspace:
                self._project_root = maya_workspace
                self.project_root_edit.setText(maya_workspace)
                settings.set_project_root(maya_workspace)
                self.project_manager.set_project_root(maya_workspace)
                logger.log_maya_fallback("No project root", maya_workspace, "using Maya workspace")
                self.validation_label.setText("✅ Maya Workspace")
                self.validation_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.validation_label.setText("❌ No path set")
                self.validation_label.setStyleSheet("color: red; font-weight: bold;")
                self._show_error_notification("Project Root Required",
                                            "Please set a project root directory or open Maya with a valid workspace.")
            return

        if os.path.exists(self._project_root):
            self.validation_label.setText("✅ Valid")
            self.validation_label.setStyleSheet("color: green; font-weight: bold;")
            logger.log_directory_access(self._project_root, "validate", success=True)
        else:
            # Try Maya workspace as fallback
            maya_workspace = self._get_maya_workspace()
            if maya_workspace and os.path.exists(maya_workspace):
                old_root = self._project_root
                self._project_root = maya_workspace
                self.project_root_edit.setText(maya_workspace)
                settings.set_project_root(maya_workspace)
                self.project_manager.set_project_root(maya_workspace)
                logger.log_maya_fallback(old_root, maya_workspace, "project root not accessible")
                self.validation_label.setText("✅ Maya Workspace")
                self.validation_label.setStyleSheet("color: orange; font-weight: bold;")
                self._show_warning_notification("Project Root Changed",
                                              f"Project root not accessible. Using Maya workspace:\n{maya_workspace}")
            else:
                self.validation_label.setText("❌ Path not found")
                self.validation_label.setStyleSheet("color: red; font-weight: bold;")
                logger.log_directory_access(self._project_root, "validate", success=False,
                                          error="Path not found and no Maya workspace available")
                self._show_error_notification("Project Root Error",
                                            f"Project root not accessible:\n{self._project_root}\n\nPlease select a valid directory.")

    def _get_maya_workspace(self) -> Optional[str]:
        """Get Maya workspace directory."""
        try:
            import maya.cmds as cmds
            workspace = cmds.workspace(query=True, rootDirectory=True)
            return workspace
        except ImportError:
            logger.log_error("NavigatorWidget", Exception("Maya not available"), "workspace query")
            return None
        except Exception as e:
            logger.log_error("NavigatorWidget", e, "Maya workspace query")
            return None

    def _on_type_changed(self, nav_type: str) -> None:
        """Handle navigation type change."""
        self._update_navigation_visibility()
        self._reset_navigation_controls()
        self._update_context()

    def _on_episode_changed(self, episode: str) -> None:
        """Handle episode selection change with enhanced cascading."""
        if episode and not episode.startswith("["):
            # Update visual indicator
            self._set_combo_status(self.episode_combo, "selected")

            # Show loading state for sequence combo
            self._set_combo_status(self.sequence_combo, "loading")

            # Populate sequences
            try:
                sequences = self.project_manager.get_sequences_for_episode(episode)
                self.sequence_combo.clear()
                self.sequence_combo.addItems(["[Select Sequence]"] + sequences)
                self._set_combo_status(self.sequence_combo, "default")

                # Reset dependent combos
                self.shot_combo.clear()
                self.shot_combo.addItems(["[Select Shot]"])
                self._set_combo_status(self.shot_combo, "default")

            except Exception as e:
                print(f"Error loading sequences: {e}")
                self._set_combo_status(self.sequence_combo, "error")

        else:
            # Reset all dependent combos
            self._set_combo_status(self.episode_combo, "default")
            self.sequence_combo.clear()
            self.sequence_combo.addItems(["[Select Sequence]"])
            self._set_combo_status(self.sequence_combo, "default")
            self.shot_combo.clear()
            self.shot_combo.addItems(["[Select Shot]"])
            self._set_combo_status(self.shot_combo, "default")

        self._update_context()
        self._update_breadcrumb()

    def _on_sequence_changed(self, sequence: str) -> None:
        """Handle sequence selection change with enhanced cascading."""
        if sequence and not sequence.startswith("["):
            # Update visual indicator
            self._set_combo_status(self.sequence_combo, "selected")

            # Show loading state for shot combo
            self._set_combo_status(self.shot_combo, "loading")

            # Populate shots
            try:
                shots = self.project_manager.get_shots_for_sequence(sequence)
                self.shot_combo.clear()
                self.shot_combo.addItems(["[Select Shot]"] + shots)
                self._set_combo_status(self.shot_combo, "default")

            except Exception as e:
                print(f"Error loading shots: {e}")
                self._set_combo_status(self.shot_combo, "error")

        else:
            # Reset shot combo
            self._set_combo_status(self.sequence_combo, "default")
            self.shot_combo.clear()
            self.shot_combo.addItems(["[Select Shot]"])
            self._set_combo_status(self.shot_combo, "default")

        self._update_context()
        self._update_breadcrumb()

    def _on_shot_changed(self, shot: str) -> None:
        """Handle shot selection change with enhanced cascading."""
        if shot and not shot.startswith("["):
            # Update visual indicator
            self._set_combo_status(self.shot_combo, "selected")

            # Show loading state for department combo
            self._set_combo_status(self.department_combo, "loading")

            # Populate departments for the specific shot
            try:
                episode = self.episode_combo.currentText()
                sequence = self.sequence_combo.currentText()
                if episode and not episode.startswith("[") and sequence and not sequence.startswith("["):
                    departments = self.project_manager.get_departments_for_shot(episode, sequence, shot)
                else:
                    departments = []

                dept_combo = self._get_active_department_combo()
                dept_combo.clear()
                dept_combo.addItems(["[Select Department]"] + departments)
                self._set_combo_status(dept_combo, "default")

                logger.log_ui_operation("NavigatorWidget", "populate_departments",
                                      f"Found {len(departments)} departments for {episode}/{sequence}/{shot}")

            except Exception as e:
                logger.log_error("NavigatorWidget", e, f"loading departments for shot {shot}")
                self._set_combo_status(self.department_combo, "error")

        else:
            # Reset department combo
            self._set_combo_status(self.shot_combo, "default")
            self.department_combo.clear()
            self.department_combo.addItems(["[Select Department]"])
            self._set_combo_status(self.department_combo, "default")

        self._update_context()
        self._update_breadcrumb()

    def _on_category_changed(self, category: str) -> None:
        """Handle category selection change."""
        if category and not category.startswith("["):
            subcategories = self.project_manager.get_subcategories_for_category(category)
            self.subcategory_combo.clear()
            self.subcategory_combo.addItems(["[Select Subcategory]"] + subcategories)
        self._update_context()

    def _on_subcategory_changed(self, subcategory: str) -> None:
        """Handle subcategory selection change."""
        if subcategory and not subcategory.startswith("["):
            assets = self.project_manager.get_assets_for_subcategory(subcategory)
            self.asset_combo.clear()
            self.asset_combo.addItems(["[Select Asset]"] + assets)
        self._update_context()

    def _on_asset_changed(self, asset: str) -> None:
        """Handle asset selection change."""
        if asset and not asset.startswith("["):
            # Get departments for the specific asset
            category = self.category_combo.currentText()
            subcategory = self.subcategory_combo.currentText()
            if category and not category.startswith("[") and subcategory and not subcategory.startswith("["):
                departments = self.project_manager.get_departments_for_asset(category, subcategory, asset)
            else:
                departments = []

            dept_combo = self._get_active_department_combo()
            dept_combo.clear()
            dept_combo.addItems(["[Select Department]"] + departments)


            logger.log_ui_operation("NavigatorWidget", "populate_asset_departments",
                                  f"Found {len(departments)} departments for {category}/{subcategory}/{asset}")

        # For Hero Directory, we can populate files even without department selection
        directory_type = self.directory_type_combo.currentText()
        if directory_type == "Hero Directory":
            self._populate_file_list()

        self._update_context()

    def _on_department_changed(self, department: str) -> None:
        """Handle department selection change."""
        self._update_context()
        self._populate_file_list()
        self._populate_context_templates()

    def _on_template_selection_changed(self) -> None:
        """Handle template selection change."""
        selected_items = self.template_list.selectedItems()
        if selected_items:
            template_item = selected_items[0]
            template_info = template_item.data(QtCore.Qt.UserRole)
            if template_info:
                metadata_text = f"Type: {template_info.type.value}\nSource: {template_info.source_path}\nCreator: {template_info.creator}"
                self.template_metadata.setText(metadata_text)
        else:
            self.template_metadata.setText("Select a template to view metadata")

    def _on_file_double_clicked(self, item: QtWidgets.QListWidgetItem) -> None:
        """Handle file double-click."""
        file_data = item.data(QtCore.Qt.UserRole)
        if file_data:
            # Extract file path from the data (could be dict or string)
            if isinstance(file_data, dict):
                file_path = file_data.get('path')
            else:
                file_path = file_data

            if file_path:
                self.file_selected.emit(file_path)

    def _on_open_file(self) -> None:
        """Handle open file button click."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.information(
                self, "No Selection",
                "Please select a file to open."
            )
            return

        file_data = selected_items[0].data(QtCore.Qt.UserRole)
        if not file_data:
            return

        # Extract file path from the data (could be dict or string)
        if isinstance(file_data, dict):
            file_path = file_data.get('path')
        else:
            file_path = file_data

        if not file_path:
            QtWidgets.QMessageBox.warning(
                self, "Invalid Selection",
                "Selected item does not contain a valid file path."
            )
            return



        # Check if file exists
        if not os.path.exists(file_path):
            QtWidgets.QMessageBox.warning(
                self, "File Not Found",
                f"File does not exist:\n{file_path}"
            )
            return

        # Try to open with Maya first, then fallback to system default
        try:
            # Check if Maya is available
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

            # Open the file in Maya
            cmds.file(file_path, open=True, force=True)
            QtWidgets.QMessageBox.information(
                self, "Success",
                f"Opened in Maya:\n{os.path.basename(file_path)}"
            )
            print(f"✅ Opened file in Maya: {file_path}")

        except ImportError:
            # Maya not available, try system default
            try:
                import subprocess
                import platform

                normalized_path = os.path.normpath(file_path)
                system = platform.system()

                if system == "Windows":
                    subprocess.run(['start', '', normalized_path], shell=True, check=True)
                elif system == "Darwin":  # macOS
                    subprocess.run(['open', normalized_path], check=True)
                else:  # Linux and others
                    subprocess.run(['xdg-open', normalized_path], check=True)

                print(f"✅ Opened file with system default: {file_path}")

            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Open Error",
                    f"Failed to open file:\n{str(e)}"
                )
                print(f"❌ Error opening file: {e}")

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Maya Error",
                f"Failed to open file in Maya:\n{str(e)}"
            )
            print(f"❌ Error opening file in Maya: {e}")

        # Also emit the signal for other components
        self.file_selected.emit(file_path)

    def _on_directory_type_changed(self, directory_type: str) -> None:
        """Handle directory type selection change."""
        self._populate_file_list()


    def _on_file_filter_changed(self, file_filter: str) -> None:
        """Handle file filter selection change."""
        self._populate_file_list()


    def _on_file_selection_changed(self) -> None:
        """Handle file selection change to show details."""
        selected_items = self.file_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            file_info = item.data(QtCore.Qt.UserRole)
            if file_info and isinstance(file_info, dict):
                details = f"📄 {file_info['name']}\n"
                details += f"📁 Path: {file_info['path']}\n"
                details += f"📏 Size: {file_info.get('size', 'Unknown')}\n"
                details += f"📅 Modified: {file_info.get('modified', 'Unknown')}\n"
                if file_info.get('version'):
                    details += f"🔢 Version: v{file_info['version']}\n"
                if file_info.get('is_hero'):
                    details += "⭐ Hero File\n"
                self.file_details_label.setText(details)
            else:
                self.file_details_label.setText("File information not available")
        else:
            self.file_details_label.setText("Select a file to view details")

    def _on_reference_file(self) -> None:
        """Handle reference file button click."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.information(self, "Reference File", "Please select a file to reference.")
            return

        file_info = selected_items[0].data(QtCore.Qt.UserRole)
        if not file_info or not isinstance(file_info, dict):
            QtWidgets.QMessageBox.warning(self, "Reference File", "Invalid file selection.")
            return

        file_path = file_info['path']

        # Check if Maya is available
        try:
            import maya.cmds as cmds

            # Create reference
            try:
                # Generate namespace from file name
                file_name = os.path.splitext(file_info['name'])[0]
                namespace = file_name.replace(' ', '_').replace('-', '_')

                # Create the reference
                ref_node = cmds.file(file_path, reference=True, namespace=namespace)

                QtWidgets.QMessageBox.information(
                    self, "Reference Created",
                    f"Successfully created reference:\n"
                    f"File: {file_info['name']}\n"
                    f"Namespace: {namespace}\n"
                    f"Reference Node: {ref_node}"
                )

                print(f"✅ Created Maya reference: {file_path} -> {namespace}")

            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Reference Error",
                    f"Failed to create reference:\n{str(e)}"
                )
                print(f"❌ Reference creation failed: {e}")

        except ImportError:
            QtWidgets.QMessageBox.warning(
                self, "Maya Not Available",
                "Maya is not available. Cannot create reference."
            )

    def _on_refresh(self) -> None:
        """Handle refresh button click with enhanced functionality."""
        try:
            # Show progress
            self.refresh_btn.setText("🔄 Refreshing...")
            self.refresh_btn.setEnabled(False)

            # Refresh project structure from directories
            self.project_manager.refresh_project_structure()

            # Refresh navigation data in UI
            self._refresh_navigation_data()

            # Refresh file list
            self._populate_file_list()

            # Refresh context templates
            self._populate_context_templates()

            # Show completion message
            QtWidgets.QMessageBox.information(
                self, "Refresh Complete",
                "Project structure and file listings have been refreshed."
            )

            print("🔄 Navigator refresh completed successfully")

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Refresh Error",
                f"Error during refresh:\n{str(e)}"
            )
            print(f"❌ Refresh failed: {e}")

        finally:
            # Restore button state
            self.refresh_btn.setText("🔄 Refresh")
            self.refresh_btn.setEnabled(True)

    def _on_browse_folder(self) -> None:
        """Handle browse folder button click with real file explorer integration."""
        current_path = self._get_current_path()
        if current_path == "[Invalid Selection]":
            QtWidgets.QMessageBox.information(
                self, "Browse Folder",
                "Please select a valid navigation context first."
            )
            return

        # Get the actual scan path based on directory type
        directory_type = self.directory_type_combo.currentText()
        scan_path = self._get_scan_path(current_path, directory_type)

        if not os.path.exists(scan_path):
            QtWidgets.QMessageBox.warning(
                self, "Browse Folder",
                f"Directory does not exist:\n{scan_path}"
            )
            return

        try:
            # Open folder in system file explorer
            import subprocess
            import platform

            # Normalize path for the operating system
            normalized_path = os.path.normpath(scan_path)

            system = platform.system()
            if system == "Windows":
                subprocess.run(['explorer', normalized_path], check=True)
            elif system == "Darwin":  # macOS
                subprocess.run(['open', normalized_path], check=True)
            else:  # Linux and others
                subprocess.run(['xdg-open', normalized_path], check=True)

            logger.log_ui_operation("NavigatorWidget", "browse_folder", scan_path)

        except subprocess.CalledProcessError as e:
            QtWidgets.QMessageBox.critical(
                self, "Browse Error",
                f"Failed to open folder in explorer:\n{str(e)}"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Browse Error",
                f"Unexpected error opening folder:\n{str(e)}"
            )

    def _show_context_menu(self, position: QtCore.QPoint) -> None:
        """Show context menu for file list."""
        item = self.file_list.itemAt(position)
        if not item:
            return

        menu = QtWidgets.QMenu(self)

        # File operations
        open_action = menu.addAction("📂 Open File")
        open_action.triggered.connect(lambda: self._on_open_file())

        reference_action = menu.addAction("🔗 Reference File")
        reference_action.triggered.connect(lambda: self._on_reference_file())

        menu.addSeparator()

        # File info
        properties_action = menu.addAction("📋 Properties")
        properties_action.triggered.connect(lambda: self._show_file_properties(item))

        menu.exec_(self.file_list.mapToGlobal(position))

    # Helper methods
    def _update_navigation_visibility(self) -> None:
        """Update visibility of navigation controls based on type."""
        is_shot = self.type_combo.currentText() == "Shot Navigation"

        # Show/hide shot-specific controls (row 0: Episode/Sequence, row 1: Shot/Department)
        # Row 0: Episode, Sequence
        for col in range(4):
            item = self.navigation_layout.itemAtPosition(0, col)
            if item and item.widget():
                item.widget().setVisible(is_shot)

        # Row 1: Shot controls and shot department (only visible in shot mode)
        for col in range(4):
            item = self.navigation_layout.itemAtPosition(1, col)
            if item and item.widget():
                item.widget().setVisible(is_shot)

        # Show/hide asset-specific controls (rows 2-3)
        for row in range(2, 4):
            for col in range(4):
                item = self.navigation_layout.itemAtPosition(row, col)
                if item and item.widget():
                    item.widget().setVisible(not is_shot)  # Asset-only controls

    def _reset_navigation_controls(self) -> None:
        """Reset all navigation controls to default state."""
        self.episode_combo.setCurrentIndex(0)
        self.sequence_combo.clear()
        self.sequence_combo.addItems(["[Select Sequence]"])
        self.shot_combo.clear()
        self.shot_combo.addItems(["[Select Shot]"])
        self.category_combo.setCurrentIndex(0)
        self.subcategory_combo.clear()
        self.subcategory_combo.addItems(["[Select Subcategory]"])
        self.asset_combo.clear()
        self.asset_combo.addItems(["[Select Asset]"])
        # Reset both department combos
        self.department_combo.clear()
        self.department_combo.addItems(["[Select Department]"])
        self.shot_department_combo.clear()
        self.shot_department_combo.addItems(["[Select Department]"])

    def _update_context(self) -> None:
        """Update current context and emit context changed signal."""
        is_shot = self.type_combo.currentText() == "Shot Navigation"

        if is_shot:
            context = {
                "type": "shot",
                "episode": self.episode_combo.currentText() if not self.episode_combo.currentText().startswith("[") else "",
                "sequence": self.sequence_combo.currentText() if not self.sequence_combo.currentText().startswith("[") else "",
                "shot": self.shot_combo.currentText() if not self.shot_combo.currentText().startswith("[") else "",
                "department": self.department_combo.currentText() if not self.department_combo.currentText().startswith("[") else ""
            }
        else:
            context = {
                "type": "asset",
                "category": self.category_combo.currentText() if not self.category_combo.currentText().startswith("[") else "",
                "subcategory": self.subcategory_combo.currentText() if not self.subcategory_combo.currentText().startswith("[") else "",
                "asset": self.asset_combo.currentText() if not self.asset_combo.currentText().startswith("[") else "",
                "department": self._get_active_department_combo().currentText() if not self._get_active_department_combo().currentText().startswith("[") else ""
            }

        self._current_context = context
        self.context_changed.emit(context)

        # Update path display
        current_path = self._get_current_path()
        self.path_label.setText(f"Path: {current_path}")

    def _get_current_path(self) -> str:
        """Get current path based on navigation selections."""
        is_shot = self.type_combo.currentText() == "Shot Navigation"
        base_path = self._project_root or r"V:\SWA\all"
        directory_type = self.directory_type_combo.currentText()

        if is_shot:
            episode = self.episode_combo.currentText()
            sequence = self.sequence_combo.currentText()
            shot = self.shot_combo.currentText()
            department = self._get_active_department_combo().currentText()

            if all([episode, sequence, shot, department]) and not any(x.startswith("[") for x in [episode, sequence, shot, department]):
                return f"{base_path}\\scene\\{episode}\\{sequence}\\{shot}\\{department}"
        else:
            category = self.category_combo.currentText()
            subcategory = self.subcategory_combo.currentText()
            asset = self.asset_combo.currentText()
            department = self._get_active_department_combo().currentText()

            # For Hero Directory, we don't need department selection
            if directory_type == "Hero Directory":
                if all([category, subcategory, asset]) and not any(x.startswith("[") for x in [category, subcategory, asset]):
                    return f"{base_path}\\asset\\{category}\\{subcategory}\\{asset}"
            else:
                # For Version Directory, we need department selection
                if all([category, subcategory, asset, department]) and not any(x.startswith("[") for x in [category, subcategory, asset, department]):
                    return f"{base_path}\\asset\\{category}\\{subcategory}\\{asset}\\{department}"

        return "[Invalid Selection]"

    def _populate_file_list(self) -> None:
        """Populate file list with real file system integration."""
        self.file_list.clear()
        self.file_details_label.setText("Select a file to view details")

        current_path = self._get_current_path()
        if current_path == "[Invalid Selection]":
            logger.log_ui_operation("NavigatorWidget", "populate_files", "Invalid selection - no context")
            return

        # Check if path exists
        if not os.path.exists(current_path):
            logger.log_directory_access(current_path, "populate_files", success=False, error="Directory not found")
            item = QtWidgets.QListWidgetItem("📂 Directory not found")
            item.setForeground(QtGui.QColor("#999999"))
            self.file_list.addItem(item)
            return

        logger.log_directory_access(current_path, "populate_files", success=True)

        try:
            # Determine directory to scan based on selection
            directory_type = self.directory_type_combo.currentText()
            scan_path = self._get_scan_path(current_path, directory_type)

            logger.log_ui_operation("NavigatorWidget", "file_scan", f"Scanning: {scan_path} (type: {directory_type})")

            if not os.path.exists(scan_path):
                logger.log_directory_access(scan_path, "file_scan", success=False, error=f"{directory_type} not found")
                item = QtWidgets.QListWidgetItem(f"📂 {directory_type} not found")
                item.setForeground(QtGui.QColor("#999999"))
                self.file_list.addItem(item)
                return

            # Get file filter
            file_filter = self.file_filter_combo.currentText()

            # Scan directory for files
            files = self._scan_directory(scan_path, file_filter, directory_type)

            logger.log_ui_operation("NavigatorWidget", "file_scan_result", f"Found {len(files)} files in {scan_path}")

            if not files:
                item = QtWidgets.QListWidgetItem("📂 No files found")
                item.setForeground(QtGui.QColor("#999999"))
                self.file_list.addItem(item)
                return

            # Populate file list
            for file_info in files:
                item = QtWidgets.QListWidgetItem()

                # Set icon based on file type
                icon = self._get_file_icon(file_info['extension'])

                # Format display text
                display_text = f"{icon} {file_info['name']}"
                if file_info.get('size'):
                    display_text += f" ({file_info['size']})"
                if file_info.get('version'):
                    display_text += f" [v{file_info['version']}]"

                item.setText(display_text)
                item.setData(QtCore.Qt.UserRole, file_info)
                item.setToolTip(f"Path: {file_info['path']}\nModified: {file_info.get('modified', 'Unknown')}")

                self.file_list.addItem(item)



        except Exception as e:
            print(f"Error populating file list: {e}")
            item = QtWidgets.QListWidgetItem(f"❌ Error loading files: {str(e)}")
            item.setForeground(QtGui.QColor("#cc0000"))
            self.file_list.addItem(item)

    def _create_navigation_context(self) -> Optional[NavigationContext]:
        """Create navigation context from current selections."""
        is_shot = self.type_combo.currentText() == "Shot Navigation"

        if is_shot:
            episode = self.episode_combo.currentText()
            sequence = self.sequence_combo.currentText()
            shot = self.shot_combo.currentText()
            department = self.department_combo.currentText()

            if all([episode, sequence, shot, department]) and not any(x.startswith("[") for x in [episode, sequence, shot, department]):
                return NavigationContext(
                    type=ProjectType.SHOT,
                    episode=episode,
                    sequence=sequence,
                    shot=shot,
                    department=department
                )
        else:
            category = self.category_combo.currentText()
            subcategory = self.subcategory_combo.currentText()
            asset = self.asset_combo.currentText()
            department = self.department_combo.currentText()

            if all([category, subcategory, asset, department]) and not any(x.startswith("[") for x in [category, subcategory, asset, department]):
                return NavigationContext(
                    type=ProjectType.ASSET,
                    category=category,
                    subcategory=subcategory,
                    asset=asset,
                    department=department
                )

        return None

    def _populate_context_templates(self) -> None:
        """Populate context templates based on current navigation context."""
        self.template_list.clear()

        # Create navigation context
        context = self._create_navigation_context()
        if not context:
            self.context_display.setText("[No context selected]")
            return

        # Update context display
        if context.type == ProjectType.SHOT:
            context_text = f"{context.episode}/{context.sequence}/{context.shot} ({context.department})"
        else:
            context_text = f"{context.category}/{context.subcategory}/{context.asset} ({context.department})"
        self.context_display.setText(context_text)

        # Get templates from TemplateManager
        templates = self.template_manager.get_templates_for_context(context)

        for template_info in templates:
            item = QtWidgets.QListWidgetItem()
            item.setText(f"📋 {template_info.name} ({template_info.type.value})")
            item.setData(QtCore.Qt.UserRole, template_info)
            self.template_list.addItem(item)



    # Public methods
    def get_current_context(self) -> Dict[str, Any]:
        """Get the current navigation context."""
        return self._current_context.copy()

    def refresh_files(self) -> None:
        """Refresh the file list."""
        self._populate_file_list()

    def _show_file_properties(self, item) -> None:
        """Show file properties dialog with real file information."""
        file_info = item.data(QtCore.Qt.UserRole)
        if not file_info or not isinstance(file_info, dict):
            QtWidgets.QMessageBox.warning(self, "Properties", "No file information available.")
            return

        file_path = file_info.get('path', 'Unknown')
        file_name = file_info.get('name', 'Unknown')
        file_size = file_info.get('size', 'Unknown')
        modified_time = file_info.get('modified', 'Unknown')
        version = file_info.get('version', 'N/A')

        properties_text = f"""File Properties:

Name: {file_name}
Path: {file_path}
Size: {file_size}
Modified: {modified_time}
Version: {version}"""

        QtWidgets.QMessageBox.information(
            self, "File Properties",
            properties_text
        )



    def _reset_navigation_controls(self) -> None:
        """Reset all navigation controls to default state."""
        self.episode_combo.setCurrentIndex(0)
        self.sequence_combo.clear()
        self.sequence_combo.addItems(["[Select Sequence]"])
        self.shot_combo.clear()
        self.shot_combo.addItems(["[Select Shot]"])
        self.category_combo.setCurrentIndex(0)
        self.subcategory_combo.clear()
        self.subcategory_combo.addItems(["[Select Subcategory]"])
        self.asset_combo.clear()
        self.asset_combo.addItems(["[Select Asset]"])
        self.department_combo.clear()
        self.department_combo.addItems(["[Select Department]"])


