"""
Asset Navigator Widget

This module provides the Asset Navigator widget for asset-based workflow navigation
with department scanning and version file management.
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


class AssetNavigatorNewWidget(QtWidgets.QWidget):
    """
    Asset Navigator widget for asset-based workflow.
    
    Provides navigation through Category → Subcategory → Asset → Department hierarchy
    with real directory scanning and version file management.
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
        
        self._current_context = {}
        self._project_root = settings.get_project_root()
        self._setup_ui()
        self._connect_signals()
        self._populate_initial_data()
        
        print("Asset Navigator Widget initialized")
    
    def _setup_ui(self) -> None:
        """Set up the user interface according to UI design specifications."""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create UI sections
        self._create_project_settings()
        self._create_asset_navigation()
        self._create_file_operations()
        
        # Add sections to main layout
        main_layout.addWidget(self.project_settings_group)
        main_layout.addWidget(self.asset_navigation_group)
        main_layout.addWidget(self.file_operations_group)
        main_layout.addStretch()
    
    def _create_project_settings(self) -> None:
        """Create project settings section."""
        self.project_settings_group = QtWidgets.QGroupBox("Project Settings")
        layout = QtWidgets.QHBoxLayout(self.project_settings_group)
        
        # Project root path
        layout.addWidget(QtWidgets.QLabel("Project Root:"))
        
        self.project_root_edit = QtWidgets.QLineEdit()
        self.project_root_edit.setText(self._project_root)
        self.project_root_edit.setStyleSheet("font-family: monospace;")
        layout.addWidget(self.project_root_edit)
        
        # Browse button
        self.browse_project_btn = QtWidgets.QPushButton("Browse")
        layout.addWidget(self.browse_project_btn)
    
    def _create_asset_navigation(self) -> None:
        """Create the asset navigation section."""
        self.asset_navigation_group = QtWidgets.QGroupBox("🎨 Asset Navigator")
        main_layout = QtWidgets.QVBoxLayout(self.asset_navigation_group)
        
        # Navigation controls
        controls_layout = QtWidgets.QGridLayout()
        
        # Category
        controls_layout.addWidget(QtWidgets.QLabel("Category:"), 0, 0)
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.setEditable(True)
        controls_layout.addWidget(self.category_combo, 0, 1)
        
        # Subcategory
        controls_layout.addWidget(QtWidgets.QLabel("Subcategory:"), 1, 0)
        self.subcategory_combo = QtWidgets.QComboBox()
        self.subcategory_combo.setEditable(True)
        controls_layout.addWidget(self.subcategory_combo, 1, 1)
        
        # Asset
        controls_layout.addWidget(QtWidgets.QLabel("Asset:"), 2, 0)
        self.asset_combo = QtWidgets.QComboBox()
        self.asset_combo.setEditable(True)
        controls_layout.addWidget(self.asset_combo, 2, 1)
        
        # Department (NEW)
        controls_layout.addWidget(QtWidgets.QLabel("Department:"), 3, 0)
        self.department_combo = QtWidgets.QComboBox()
        self.department_combo.setEditable(True)
        controls_layout.addWidget(self.department_combo, 3, 1)
        
        main_layout.addLayout(controls_layout)
        
        # Asset files list
        main_layout.addWidget(QtWidgets.QLabel("Version Files:"))
        self.asset_files_list = QtWidgets.QListWidget()
        self.asset_files_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        main_layout.addWidget(self.asset_files_list)
        
        # Action buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        self.refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        self.save_version_btn = QtWidgets.QPushButton("💾 Save Version")
        self.export_template_btn = QtWidgets.QPushButton("📤 Export Template")
        
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addWidget(self.save_version_btn)
        buttons_layout.addWidget(self.export_template_btn)
        buttons_layout.addStretch()
        
        main_layout.addLayout(buttons_layout)
    
    def _create_file_operations(self) -> None:
        """Create file operations section."""
        self.file_operations_group = QtWidgets.QGroupBox("🎨 File Operations")
        layout = QtWidgets.QHBoxLayout(self.file_operations_group)
        
        self.open_btn = QtWidgets.QPushButton("📂 Open Selected")
        self.reference_btn = QtWidgets.QPushButton("🔗 Reference Selected")
        self.import_btn = QtWidgets.QPushButton("📥 Import Selected")
        
        layout.addWidget(self.open_btn)
        layout.addWidget(self.reference_btn)
        layout.addWidget(self.import_btn)
        layout.addStretch()
    
    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        # Project settings
        self.browse_project_btn.clicked.connect(self._on_browse_project)
        self.project_root_edit.textChanged.connect(self._on_project_root_changed)
        
        # Asset navigator
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        self.subcategory_combo.currentTextChanged.connect(self._on_subcategory_changed)
        self.asset_combo.currentTextChanged.connect(self._on_asset_changed)
        self.department_combo.currentTextChanged.connect(self._on_department_changed)
        self.asset_files_list.customContextMenuRequested.connect(self._show_context_menu)
        
        # Action buttons
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.save_version_btn.clicked.connect(self._on_save_version)
        self.export_template_btn.clicked.connect(self._on_export_template)
        
        # File operations
        self.open_btn.clicked.connect(self._on_open)
        self.reference_btn.clicked.connect(self._on_reference)
        self.import_btn.clicked.connect(self._on_import)
    
    def _populate_initial_data(self) -> None:
        """Populate initial data by scanning directories."""
        self._scan_categories()
    
    def _scan_categories(self) -> None:
        """Scan for asset categories in the project directory."""
        assets_path = os.path.join(self._project_root, "assets")
        if os.path.exists(assets_path):
            categories = [d for d in os.listdir(assets_path) 
                         if os.path.isdir(os.path.join(assets_path, d))]
            categories.sort()
            self.category_combo.clear()
            self.category_combo.addItems(categories)
            if categories:
                self._scan_subcategories(categories[0])
        else:
            # No fallback - show empty list if directory doesn't exist
            print("📁 Assets directory not found - no categories available")
    
    def _scan_subcategories(self, category: str) -> None:
        """Scan for subcategories in the selected category."""
        category_path = os.path.join(self._project_root, "assets", category)
        if os.path.exists(category_path):
            subcategories = [d for d in os.listdir(category_path) 
                           if os.path.isdir(os.path.join(category_path, d))]
            subcategories.sort()
            self.subcategory_combo.clear()
            self.subcategory_combo.addItems(subcategories)
            if subcategories:
                self._scan_assets(category, subcategories[0])
        else:
            # No fallback - show empty list if directory doesn't exist
            self.subcategory_combo.clear()
            print(f"📁 Category directory not found - no subcategories available: {category_path}")
    
    def _scan_assets(self, category: str, subcategory: str) -> None:
        """Scan for assets in the selected subcategory."""
        subcategory_path = os.path.join(self._project_root, "assets", category, subcategory)
        if os.path.exists(subcategory_path):
            assets = [d for d in os.listdir(subcategory_path) 
                     if os.path.isdir(os.path.join(subcategory_path, d))]
            assets.sort()
            self.asset_combo.clear()
            self.asset_combo.addItems(assets)
            if assets:
                self._scan_departments(category, subcategory, assets[0])
        else:
            # No fallback - show empty list if directory doesn't exist
            self.asset_combo.clear()
            print(f"📁 Subcategory directory not found - no assets available: {subcategory_path}")
    
    def _scan_departments(self, category: str, subcategory: str, asset: str) -> None:
        """Scan for departments in the selected asset."""
        asset_path = os.path.join(self._project_root, "assets", category, subcategory, asset)
        if os.path.exists(asset_path):
            departments = [d for d in os.listdir(asset_path) 
                          if os.path.isdir(os.path.join(asset_path, d))]
            departments.sort()
            self.department_combo.clear()
            self.department_combo.addItems(departments)
            if departments:
                self._refresh_files()
        else:
            # No fallback - show empty list if directory doesn't exist
            self.department_combo.clear()
            print(f"📁 Asset directory not found - no departments available: {asset_path}")
            self._refresh_files()

    def _refresh_files(self) -> None:
        """Refresh the files list based on current selection."""
        category = self.category_combo.currentText()
        subcategory = self.subcategory_combo.currentText()
        asset = self.asset_combo.currentText()
        department = self.department_combo.currentText()

        if not all([category, subcategory, asset, department]):
            self.asset_files_list.clear()
            return

        # Look for version files in the department/version directory
        version_path = os.path.join(
            self._project_root, "assets", category, subcategory, asset, department, "version"
        )

        files = []
        if os.path.exists(version_path):
            for file in os.listdir(version_path):
                if file.endswith(('.ma', '.mb')):
                    file_path = os.path.join(version_path, file)
                    try:
                        stat = os.stat(file_path)
                        timestamp = QtCore.QDateTime.fromSecsSinceEpoch(int(stat.st_mtime))
                        timestamp_str = timestamp.toString("yyyy-MM-dd hh:mm")

                        # Determine file type icon
                        if 'hero' in file.lower():
                            icon = '👑'
                        elif 'template' in file.lower():
                            icon = '📋'
                        else:
                            icon = '📝'

                        display_text = f"{icon} {file} - {timestamp_str}"
                        files.append(display_text)
                    except OSError:
                        files.append(f"📝 {file}")

        # Sort files (hero first, then template, then versions)
        files.sort(key=lambda x: (0 if '👑' in x else 1 if '📋' in x else 2, x))

        self.asset_files_list.clear()
        self.asset_files_list.addItems(files)

        # Update context
        self._update_context()

    def _update_context(self) -> None:
        """Update current navigation context and emit signal."""
        self._current_context = {
            "type": "asset",
            "category": self.category_combo.currentText(),
            "subcategory": self.subcategory_combo.currentText(),
            "asset": self.asset_combo.currentText(),
            "department": self.department_combo.currentText()
        }

        # Emit context change signal
        self.context_changed.emit(self._current_context)

    # Event handlers
    def _on_browse_project(self) -> None:
        """Handle browse project button click."""
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setWindowTitle("Select Project Root Directory")

        if dialog.exec_():
            selected_dirs = dialog.selectedFiles()
            if selected_dirs:
                project_root = selected_dirs[0]
                self.project_root_edit.setText(project_root)

    def _on_project_root_changed(self, text: str) -> None:
        """Handle project root path change."""
        self._project_root = text
        settings.set("project.project_root", text)
        self._scan_categories()

    def _on_category_changed(self, category: str) -> None:
        """Handle category selection change."""
        if category:
            self._scan_subcategories(category)

    def _on_subcategory_changed(self, subcategory: str) -> None:
        """Handle subcategory selection change."""
        category = self.category_combo.currentText()
        if category and subcategory:
            self._scan_assets(category, subcategory)

    def _on_asset_changed(self, asset: str) -> None:
        """Handle asset selection change."""
        category = self.category_combo.currentText()
        subcategory = self.subcategory_combo.currentText()
        if category and subcategory and asset:
            self._scan_departments(category, subcategory, asset)

    def _on_department_changed(self, department: str) -> None:
        """Handle department selection change."""
        if department:
            self._refresh_files()

    def _on_refresh(self) -> None:
        """Handle refresh button click."""
        self._refresh_files()
        QtWidgets.QMessageBox.information(self, "Refresh", "File list refreshed successfully!")

    def _on_save_version(self) -> None:
        """Handle save version button click."""
        context = self._get_current_context_string()
        version_name, ok = QtWidgets.QInputDialog.getText(
            self, "Save Version", "Enter version description:",
            text="modeling_update"
        )

        if ok and version_name:
            QtWidgets.QMessageBox.information(
                self, "Version Saved",
                f"Mock: Version saved successfully!\n\n"
                f"Context: {context}\n"
                f"Description: {version_name}\n"
                f"File: asset_v006.ma"
            )

    def _on_export_template(self) -> None:
        """Handle export template button click."""
        context = self._get_current_context_string()
        template_name, ok = QtWidgets.QInputDialog.getText(
            self, "Export Template", "Enter template name:",
            text="asset_template"
        )

        if ok and template_name:
            QtWidgets.QMessageBox.information(
                self, "Template Exported",
                f"Mock: Template exported successfully!\n\n"
                f"Template: {template_name}\n"
                f"Context: {context}\n"
                f"Package contents:\n"
                f"• Maya asset file (.ma)\n"
                f"• Textures and materials\n"
                f"• Package info (.json)"
            )

    def _on_open(self) -> None:
        """Handle open button click."""
        selected_file = self._get_selected_file()
        if selected_file:
            QtWidgets.QMessageBox.information(self, "Open File", f"Mock: Opening {selected_file}")
        else:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a file to open.")

    def _on_reference(self) -> None:
        """Handle reference button click."""
        selected_file = self._get_selected_file()
        if selected_file:
            QtWidgets.QMessageBox.information(self, "Reference File", f"Mock: Referenced {selected_file}")
        else:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a file to reference.")

    def _on_import(self) -> None:
        """Handle import button click."""
        selected_file = self._get_selected_file()
        if selected_file:
            QtWidgets.QMessageBox.information(self, "Import File", f"Mock: Imported {selected_file}")
        else:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select a file to import.")

    def _show_context_menu(self, position: QtCore.QPoint) -> None:
        """Show context menu for files list."""
        item = self.asset_files_list.itemAt(position)
        if not item:
            return

        menu = QtWidgets.QMenu(self)
        menu.addAction("📂 Open", lambda: self._context_action("open", item.text()))
        menu.addAction("🔗 Reference", lambda: self._context_action("reference", item.text()))
        menu.addAction("📥 Import", lambda: self._context_action("import", item.text()))
        menu.addSeparator()
        menu.addAction("📁 Show in Explorer", lambda: self._context_action("explorer", item.text()))
        menu.addAction("📋 Copy Path", lambda: self._context_action("copy_path", item.text()))

        if "📝" in item.text():  # Version file
            menu.addSeparator()
            menu.addAction("👑 Make Hero", lambda: self._context_action("make_hero", item.text()))

        menu.exec_(self.asset_files_list.mapToGlobal(position))

    def _context_action(self, action: str, filename: str) -> None:
        """Handle context menu actions."""
        clean_name = filename.split(' - ')[0][2:]  # Remove emoji and timestamp

        if action == "open":
            QtWidgets.QMessageBox.information(self, "Open", f"Mock: Opening {clean_name}")
        elif action == "reference":
            QtWidgets.QMessageBox.information(self, "Reference", f"Mock: Referencing {clean_name}")
        elif action == "import":
            QtWidgets.QMessageBox.information(self, "Import", f"Mock: Importing {clean_name}")
        elif action == "explorer":
            mock_path = self._get_file_path(clean_name)
            QtWidgets.QMessageBox.information(self, "Explorer", f"Mock: Opening explorer for:\n{mock_path}")
        elif action == "copy_path":
            mock_path = self._get_file_path(clean_name)
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(mock_path)
            QtWidgets.QMessageBox.information(self, "Path Copied", f"Mock: Path copied to clipboard:\n{mock_path}")
        elif action == "make_hero":
            reply = QtWidgets.QMessageBox.question(
                self, "Make Hero",
                f"Make {clean_name} the new hero file?\n"
                f"This will replace the current hero file.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                QtWidgets.QMessageBox.information(
                    self, "Hero Created",
                    f"Mock: {clean_name} is now the hero file.\n"
                    f"Previous hero backed up as hero_backup.ma"
                )
                self._refresh_files()

    # Helper methods
    def _get_selected_file(self) -> Optional[str]:
        """Get currently selected file."""
        selection = self.asset_files_list.selectedItems()
        if selection:
            return selection[0].text().split(' - ')[0][2:]  # Remove emoji and timestamp
        return None

    def _get_current_context_string(self) -> str:
        """Get current context as formatted string."""
        return f"{self.category_combo.currentText()}/{self.subcategory_combo.currentText()}/{self.asset_combo.currentText()}/{self.department_combo.currentText()}"

    def _get_file_path(self, filename: str) -> str:
        """Get full file path for a filename."""
        category = self.category_combo.currentText()
        subcategory = self.subcategory_combo.currentText()
        asset = self.asset_combo.currentText()
        department = self.department_combo.currentText()

        return os.path.join(
            self._project_root, "assets", category, subcategory, asset, department, "version", filename
        )

    def get_current_context(self) -> Dict[str, Any]:
        """Get current navigation context."""
        return self._current_context.copy()

    def set_project_root(self, root_path: str) -> None:
        """Set the project root path."""
        self._project_root = root_path
        self.project_root_edit.setText(root_path)
        self._scan_categories()
