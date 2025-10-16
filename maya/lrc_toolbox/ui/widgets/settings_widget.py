"""
Settings Widget

This module provides the Settings widget for configuration management
according to UI design specifications.
"""

from typing import Optional, Dict, Any

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


class SettingsWidget(QtWidgets.QWidget):
    """
    Settings widget for configuration management.
    
    Provides naming convention rules and other configuration options
    according to the UI design specifications.
    """
    
    # Signals for communication with main window
    settings_saved = QtCore.Signal(dict)  # Emitted when settings are saved
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the Settings widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._setup_ui()
        self._connect_signals()
        self._load_settings()
        
        print("Settings Widget initialized")
    
    def _setup_ui(self) -> None:
        """Set up the user interface according to UI design specifications."""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create UI sections
        self._create_naming_convention()
        self._create_project_settings()
        self._create_ui_settings()
        self._create_save_section()
        
        # Add sections to main layout
        main_layout.addWidget(self.naming_convention_group)
        main_layout.addWidget(self.project_settings_group)
        main_layout.addWidget(self.ui_settings_group)
        main_layout.addWidget(self.save_section_group)
        main_layout.addStretch()
    
    def _create_naming_convention(self) -> None:
        """Create naming convention rules section."""
        self.naming_convention_group = QtWidgets.QGroupBox("⚙️ Naming Convention Rules")
        layout = QtWidgets.QGridLayout(self.naming_convention_group)
        
        # Separator
        layout.addWidget(QtWidgets.QLabel("Separator:"), 0, 0)
        self.separator_edit = QtWidgets.QLineEdit()
        self.separator_edit.setMaximumWidth(50)
        self.separator_edit.setText("_")
        layout.addWidget(self.separator_edit, 0, 1)
        
        # Index padding
        layout.addWidget(QtWidgets.QLabel("Index Padding:"), 1, 0)
        self.index_padding_spin = QtWidgets.QSpinBox()
        self.index_padding_spin.setRange(1, 5)
        self.index_padding_spin.setValue(3)
        self.index_padding_spin.setMaximumWidth(80)
        layout.addWidget(self.index_padding_spin, 1, 1)
        
        # Case
        layout.addWidget(QtWidgets.QLabel("Case:"), 2, 0)
        self.case_combo = QtWidgets.QComboBox()
        self.case_combo.addItems(["lower", "upper", "title", "camel"])
        self.case_combo.setCurrentText("lower")
        layout.addWidget(self.case_combo, 2, 1)
        
        # Add stretch to push everything to the left
        layout.setColumnStretch(2, 1)
    
    def _create_project_settings(self) -> None:
        """Create project settings section."""
        self.project_settings_group = QtWidgets.QGroupBox("📁 Project Settings")
        layout = QtWidgets.QGridLayout(self.project_settings_group)
        
        # Default project root
        layout.addWidget(QtWidgets.QLabel("Default Project Root:"), 0, 0)
        self.project_root_edit = QtWidgets.QLineEdit()
        self.project_root_edit.setText(settings.get_project_root())
        layout.addWidget(self.project_root_edit, 0, 1)
        
        self.browse_project_btn = QtWidgets.QPushButton("Browse")
        layout.addWidget(self.browse_project_btn, 0, 2)
        
        # Auto-save interval
        layout.addWidget(QtWidgets.QLabel("Auto-save Interval (min):"), 1, 0)
        self.autosave_spin = QtWidgets.QSpinBox()
        self.autosave_spin.setRange(1, 60)
        self.autosave_spin.setValue(5)
        self.autosave_spin.setMaximumWidth(80)
        layout.addWidget(self.autosave_spin, 1, 1)
        
        # Backup versions to keep
        layout.addWidget(QtWidgets.QLabel("Backup Versions:"), 2, 0)
        self.backup_versions_spin = QtWidgets.QSpinBox()
        self.backup_versions_spin.setRange(1, 20)
        self.backup_versions_spin.setValue(5)
        self.backup_versions_spin.setMaximumWidth(80)
        layout.addWidget(self.backup_versions_spin, 2, 1)
        
        # Add stretch
        layout.setColumnStretch(3, 1)
    
    def _create_ui_settings(self) -> None:
        """Create UI settings section."""
        self.ui_settings_group = QtWidgets.QGroupBox("🎨 UI Settings")
        layout = QtWidgets.QGridLayout(self.ui_settings_group)
        
        # Theme
        layout.addWidget(QtWidgets.QLabel("Theme:"), 0, 0)
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(["Default", "Dark", "Light", "Maya"])
        self.theme_combo.setCurrentText("Default")
        layout.addWidget(self.theme_combo, 0, 1)
        
        # Font size
        layout.addWidget(QtWidgets.QLabel("Font Size:"), 1, 0)
        self.font_size_spin = QtWidgets.QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(9)
        self.font_size_spin.setMaximumWidth(80)
        layout.addWidget(self.font_size_spin, 1, 1)
        
        # Show tooltips
        self.show_tooltips_check = QtWidgets.QCheckBox("Show Tooltips")
        self.show_tooltips_check.setChecked(True)
        layout.addWidget(self.show_tooltips_check, 2, 0, 1, 2)
        
        # Show status bar
        self.show_status_bar_check = QtWidgets.QCheckBox("Show Status Bar")
        self.show_status_bar_check.setChecked(True)
        layout.addWidget(self.show_status_bar_check, 3, 0, 1, 2)
        
        # Add stretch
        layout.setColumnStretch(2, 1)
    
    def _create_save_section(self) -> None:
        """Create save section."""
        self.save_section_group = QtWidgets.QGroupBox()
        self.save_section_group.setStyleSheet("QGroupBox { border: none; }")
        layout = QtWidgets.QHBoxLayout(self.save_section_group)
        
        self.save_settings_btn = QtWidgets.QPushButton("💾 Save Settings")
        self.save_settings_btn.setStyleSheet(
            "QPushButton { font-weight: bold; padding: 8px 16px; }"
        )
        self.reset_settings_btn = QtWidgets.QPushButton("🔄 Reset to Defaults")
        
        layout.addWidget(self.save_settings_btn)
        layout.addWidget(self.reset_settings_btn)
        layout.addStretch()
    
    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        # Project settings
        self.browse_project_btn.clicked.connect(self._on_browse_project)
        
        # Save section
        self.save_settings_btn.clicked.connect(self._on_save_settings)
        self.reset_settings_btn.clicked.connect(self._on_reset_settings)
    
    def _load_settings(self) -> None:
        """Load settings from configuration."""
        # Naming convention
        self.separator_edit.setText(settings.get("naming.separator", "_"))
        self.index_padding_spin.setValue(settings.get("naming.index_padding", 3))
        self.case_combo.setCurrentText(settings.get("naming.case", "lower"))
        
        # Project settings
        self.project_root_edit.setText(settings.get_project_root())
        self.autosave_spin.setValue(settings.get("project.autosave_interval", 5))
        self.backup_versions_spin.setValue(settings.get("project.backup_versions", 5))
        
        # UI settings
        self.theme_combo.setCurrentText(settings.get("ui.theme", "Default"))
        self.font_size_spin.setValue(settings.get("ui.font_size", 9))
        self.show_tooltips_check.setChecked(settings.get("ui.show_tooltips", True))
        self.show_status_bar_check.setChecked(settings.get("ui.show_status_bar", True))
    
    # Event handlers
    def _on_browse_project(self) -> None:
        """Handle browse project button click."""
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setWindowTitle("Select Default Project Root Directory")
        
        if dialog.exec_():
            selected_dirs = dialog.selectedFiles()
            if selected_dirs:
                project_root = selected_dirs[0]
                self.project_root_edit.setText(project_root)
    
    def _on_save_settings(self) -> None:
        """Handle save settings button click."""
        # Collect all settings
        new_settings = {
            # Naming convention
            "naming.separator": self.separator_edit.text(),
            "naming.index_padding": self.index_padding_spin.value(),
            "naming.case": self.case_combo.currentText(),
            
            # Project settings
            "project.project_root": self.project_root_edit.text(),
            "project.autosave_interval": self.autosave_spin.value(),
            "project.backup_versions": self.backup_versions_spin.value(),
            
            # UI settings
            "ui.theme": self.theme_combo.currentText(),
            "ui.font_size": self.font_size_spin.value(),
            "ui.show_tooltips": self.show_tooltips_check.isChecked(),
            "ui.show_status_bar": self.show_status_bar_check.isChecked()
        }
        
        # Validate settings
        if not new_settings["naming.separator"]:
            QtWidgets.QMessageBox.warning(
                self, "Invalid Settings",
                "Separator cannot be empty."
            )
            return
        
        if not new_settings["project.project_root"]:
            QtWidgets.QMessageBox.warning(
                self, "Invalid Settings",
                "Project root cannot be empty."
            )
            return
        
        # Save settings
        for key, value in new_settings.items():
            settings.set(key, value)

        # Persist to disk
        settings.save_settings()

        # Show success message
        QtWidgets.QMessageBox.information(
            self, "Settings Saved",
            "Settings saved successfully!\n\n"
            "Some changes may require restarting the toolbox to take effect."
        )

        # Emit signal
        self.settings_saved.emit(new_settings)

    def _on_reset_settings(self) -> None:
        """Handle reset settings button click."""
        reply = QtWidgets.QMessageBox.question(
            self, "Reset Settings",
            "Reset all settings to default values?\n\n"
            "This action cannot be undone!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            # Reset to defaults
            self.separator_edit.setText("_")
            self.index_padding_spin.setValue(3)
            self.case_combo.setCurrentText("lower")
            
            self.project_root_edit.setText("V:/SWA/all")
            self.autosave_spin.setValue(5)
            self.backup_versions_spin.setValue(5)
            
            self.theme_combo.setCurrentText("Default")
            self.font_size_spin.setValue(9)
            self.show_tooltips_check.setChecked(True)
            self.show_status_bar_check.setChecked(True)
            
            QtWidgets.QMessageBox.information(
                self, "Settings Reset",
                "Settings reset to default values!\n\n"
                "Click 'Save Settings' to apply the changes."
            )
    
    # Public methods
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current settings values."""
        return {
            "naming.separator": self.separator_edit.text(),
            "naming.index_padding": self.index_padding_spin.value(),
            "naming.case": self.case_combo.currentText(),
            "project.project_root": self.project_root_edit.text(),
            "project.autosave_interval": self.autosave_spin.value(),
            "project.backup_versions": self.backup_versions_spin.value(),
            "ui.theme": self.theme_combo.currentText(),
            "ui.font_size": self.font_size_spin.value(),
            "ui.show_tooltips": self.show_tooltips_check.isChecked(),
            "ui.show_status_bar": self.show_status_bar_check.isChecked()
        }
    
    def apply_theme(self, theme_name: str) -> None:
        """Apply a theme to the widget."""
        # Mock theme application - in real implementation, apply actual styling
        if theme_name == "Dark":
            self.setStyleSheet("QWidget { background-color: #2b2b2b; color: #ffffff; }")
        elif theme_name == "Light":
            self.setStyleSheet("QWidget { background-color: #ffffff; color: #000000; }")
        else:
            self.setStyleSheet("")  # Default theme
