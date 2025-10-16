"""
Shot Navigator Widget

This module provides the Shot Navigator widget for shot-based workflow navigation
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


class ShotNavigatorWidget(QtWidgets.QWidget):
    """
    Shot Navigator widget for shot-based workflow.
    
    Provides navigation through Episode → Sequence → Shot → Department hierarchy
    with real directory scanning and version file management.
    """
    
    # Signals for communication with main window
    file_selected = QtCore.Signal(str)  # Emitted when file is selected
    context_changed = QtCore.Signal(dict)  # Emitted when navigation context changes
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the Shot Navigator widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._current_context = {}
        self._project_root = settings.get_project_root()
        self._setup_ui()
        self._connect_signals()
        self._populate_initial_data()
        
        print("Shot Navigator Widget initialized")
    
    def _setup_ui(self) -> None:
        """Set up the user interface according to UI design specifications."""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create UI sections
        self._create_project_settings()
        self._create_shot_navigation()
        self._create_file_operations()
        
        # Add sections to main layout
        main_layout.addWidget(self.project_settings_group)
        main_layout.addWidget(self.shot_navigation_group)
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
    
    def _create_shot_navigation(self) -> None:
        """Create the shot navigation section."""
        self.shot_navigation_group = QtWidgets.QGroupBox("🎬 Shot Navigator")
        main_layout = QtWidgets.QVBoxLayout(self.shot_navigation_group)
        
        # Navigation controls
        controls_layout = QtWidgets.QGridLayout()
        
        # Episode
        controls_layout.addWidget(QtWidgets.QLabel("Episode:"), 0, 0)
        self.episode_combo = QtWidgets.QComboBox()
        self.episode_combo.setEditable(True)
        controls_layout.addWidget(self.episode_combo, 0, 1)
        
        # Sequence
        controls_layout.addWidget(QtWidgets.QLabel("Sequence:"), 1, 0)
        self.sequence_combo = QtWidgets.QComboBox()
        self.sequence_combo.setEditable(True)
        controls_layout.addWidget(self.sequence_combo, 1, 1)
        
        # Shot
        controls_layout.addWidget(QtWidgets.QLabel("Shot:"), 2, 0)
        self.shot_combo = QtWidgets.QComboBox()
        self.shot_combo.setEditable(True)
        controls_layout.addWidget(self.shot_combo, 2, 1)
        
        # Department (NEW)
        controls_layout.addWidget(QtWidgets.QLabel("Department:"), 3, 0)
        self.department_combo = QtWidgets.QComboBox()
        self.department_combo.setEditable(True)
        controls_layout.addWidget(self.department_combo, 3, 1)
        
        main_layout.addLayout(controls_layout)
        
        # Shot files list
        main_layout.addWidget(QtWidgets.QLabel("Version Files:"))
        self.shot_files_list = QtWidgets.QListWidget()
        self.shot_files_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        main_layout.addWidget(self.shot_files_list)
        
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
        self.file_operations_group = QtWidgets.QGroupBox("🎬 File Operations")
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
        
        # Shot navigator
        self.episode_combo.currentTextChanged.connect(self._on_episode_changed)
        self.sequence_combo.currentTextChanged.connect(self._on_sequence_changed)
        self.shot_combo.currentTextChanged.connect(self._on_shot_changed)
        self.department_combo.currentTextChanged.connect(self._on_department_changed)
        self.shot_files_list.customContextMenuRequested.connect(self._show_context_menu)
        
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
        self._scan_episodes()
    
    def _scan_episodes(self) -> None:
        """Scan for episodes in the project directory."""
        scene_path = os.path.join(self._project_root, "scene")
        if os.path.exists(scene_path):
            episodes = [d for d in os.listdir(scene_path) 
                       if os.path.isdir(os.path.join(scene_path, d)) and d.startswith("Ep")]
            episodes.sort()
            self.episode_combo.clear()
            self.episode_combo.addItems(episodes)
            if episodes:
                self._scan_sequences(episodes[0])
        else:
            # No fallback - show empty list if directory doesn't exist
            print("📁 Scene directory not found - no episodes available")
    
    def _scan_sequences(self, episode: str) -> None:
        """Scan for sequences in the selected episode."""
        episode_path = os.path.join(self._project_root, "scene", episode)
        if os.path.exists(episode_path):
            sequences = [d for d in os.listdir(episode_path) 
                        if os.path.isdir(os.path.join(episode_path, d)) and d.startswith("sq")]
            sequences.sort()
            self.sequence_combo.clear()
            self.sequence_combo.addItems(sequences)
            if sequences:
                self._scan_shots(episode, sequences[0])
        else:
            # Fallback to mock data
            self.sequence_combo.clear()
            self.sequence_combo.addItems(["sq0010", "sq0020", "sq0030"])
            self._scan_shots(episode, "sq0010")
    
    def _scan_shots(self, episode: str, sequence: str) -> None:
        """Scan for shots in the selected sequence."""
        sequence_path = os.path.join(self._project_root, "scene", episode, sequence)
        if os.path.exists(sequence_path):
            shots = [d for d in os.listdir(sequence_path) 
                    if os.path.isdir(os.path.join(sequence_path, d)) and d.startswith("SH")]
            shots.sort()
            self.shot_combo.clear()
            self.shot_combo.addItems(shots)
            if shots:
                self._scan_departments(episode, sequence, shots[0])
        else:
            # No fallback - show empty list if directory doesn't exist
            self.shot_combo.clear()
            print(f"📁 Sequence directory not found - no shots available: {sequence_path}")
    
    def _scan_departments(self, episode: str, sequence: str, shot: str) -> None:
        """Scan for departments in the selected shot."""
        shot_path = os.path.join(self._project_root, "scene", episode, sequence, shot)
        if os.path.exists(shot_path):
            departments = [d for d in os.listdir(shot_path) 
                          if os.path.isdir(os.path.join(shot_path, d))]
            departments.sort()
            self.department_combo.clear()
            self.department_combo.addItems(departments)
            if departments:
                self._refresh_files()
        else:
            # No fallback - show empty list if directory doesn't exist
            self.department_combo.clear()
            print(f"📁 Shot directory not found - no departments available: {shot_path}")
            self._refresh_files()

    def _refresh_files(self) -> None:
        """Refresh the files list based on current selection."""
        episode = self.episode_combo.currentText()
        sequence = self.sequence_combo.currentText()
        shot = self.shot_combo.currentText()
        department = self.department_combo.currentText()

        if not all([episode, sequence, shot, department]):
            self.shot_files_list.clear()
            return

        # Look for version files in the department/version directory
        version_path = os.path.join(
            self._project_root, "scene", episode, sequence, shot, department, "version"
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

        self.shot_files_list.clear()
        self.shot_files_list.addItems(files)

        # Update context
        self._update_context()

    def _update_context(self) -> None:
        """Update current navigation context and emit signal."""
        self._current_context = {
            "type": "shot",
            "episode": self.episode_combo.currentText(),
            "sequence": self.sequence_combo.currentText(),
            "shot": self.shot_combo.currentText(),
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
        self._scan_episodes()

    def _on_episode_changed(self, episode: str) -> None:
        """Handle episode selection change."""
        if episode:
            self._scan_sequences(episode)

    def _on_sequence_changed(self, sequence: str) -> None:
        """Handle sequence selection change."""
        episode = self.episode_combo.currentText()
        if episode and sequence:
            self._scan_shots(episode, sequence)

    def _on_shot_changed(self, shot: str) -> None:
        """Handle shot selection change."""
        episode = self.episode_combo.currentText()
        sequence = self.sequence_combo.currentText()
        if episode and sequence and shot:
            self._scan_departments(episode, sequence, shot)

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
            text="lighting_update"
        )

        if ok and version_name:
            QtWidgets.QMessageBox.information(
                self, "Version Saved",
                f"Mock: Version saved successfully!\n\n"
                f"Context: {context}\n"
                f"Description: {version_name}\n"
                f"File: scene_v006.ma"
            )

    def _on_export_template(self) -> None:
        """Handle export template button click."""
        context = self._get_current_context_string()
        template_name, ok = QtWidgets.QInputDialog.getText(
            self, "Export Template", "Enter template name:",
            text="shot_lighting_template"
        )

        if ok and template_name:
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
        item = self.shot_files_list.itemAt(position)
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

        menu.exec_(self.shot_files_list.mapToGlobal(position))

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
        selection = self.shot_files_list.selectedItems()
        if selection:
            return selection[0].text().split(' - ')[0][2:]  # Remove emoji and timestamp
        return None

    def _get_current_context_string(self) -> str:
        """Get current context as formatted string."""
        return f"{self.episode_combo.currentText()}/{self.sequence_combo.currentText()}/{self.shot_combo.currentText()}/{self.department_combo.currentText()}"

    def _get_file_path(self, filename: str) -> str:
        """Get full file path for a filename."""
        episode = self.episode_combo.currentText()
        sequence = self.sequence_combo.currentText()
        shot = self.shot_combo.currentText()
        department = self.department_combo.currentText()

        return os.path.join(
            self._project_root, "scene", episode, sequence, shot, department, "version", filename
        )

    def get_current_context(self) -> Dict[str, Any]:
        """Get current navigation context."""
        return self._current_context.copy()

    def set_project_root(self, root_path: str) -> None:
        """Set the project root path."""
        self._project_root = root_path
        self.project_root_edit.setText(root_path)
        self._scan_episodes()
