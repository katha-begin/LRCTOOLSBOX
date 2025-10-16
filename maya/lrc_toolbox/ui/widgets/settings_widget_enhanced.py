"""
Enhanced Settings Widget

Comprehensive user preferences and workflow customization interface
with tabbed organization and real-time preview.
"""

import os
from typing import Optional, Dict, Any, List

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
from ...config.session_manager import session_manager


class EnhancedSettingsWidget(QtWidgets.QWidget):
    """
    Comprehensive Settings widget for configuration management.

    Features:
    - Tabbed interface for organized preferences
    - Real-time preview and validation
    - Import/Export configuration
    - Reset to defaults functionality
    - User workflow customization
    """

    # Signals for communication with main window
    settings_saved = QtCore.Signal(dict)  # Emitted when settings are saved
    settings_reset = QtCore.Signal()  # Emitted when settings are reset
    preferences_changed = QtCore.Signal(str, object)  # Emitted when individual preference changes

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the Enhanced Settings widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Track changes for validation
        self._unsaved_changes = False
        self._original_settings = {}

        self._setup_ui()
        self._connect_signals()
        self._load_settings()

        print("Enhanced Settings Widget initialized")

    def _setup_ui(self) -> None:
        """Set up the comprehensive user interface."""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Create header with title and status
        self._create_header()
        main_layout.addWidget(self.header_widget)

        # Create tabbed interface
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabPosition(QtWidgets.QTabWidget.North)
        main_layout.addWidget(self.tab_widget)

        # Create preference tabs
        self._create_general_tab()
        self._create_workflow_tab()
        self._create_naming_tab()
        self._create_ui_tab()
        self._create_maya_tab()
        self._create_advanced_tab()

        # Create footer with actions
        self._create_footer()
        main_layout.addWidget(self.footer_widget)

    def _create_header(self) -> None:
        """Create header with title and status indicator."""
        self.header_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(self.header_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title_label = QtWidgets.QLabel("User Preferences & Workflow Customization")
        title_font = QtGui.QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        layout.addStretch()

        # Status indicator
        self.status_label = QtWidgets.QLabel("All settings saved")
        self.status_label.setStyleSheet("color: green; font-style: italic;")
        layout.addWidget(self.status_label)

    def _create_general_tab(self) -> None:
        """Create general preferences tab."""
        tab_widget = QtWidgets.QWidget()
        self.tab_widget.addTab(tab_widget, "General")

        layout = QtWidgets.QVBoxLayout(tab_widget)
        layout.setSpacing(8)

        # Project Settings Group
        project_group = QtWidgets.QGroupBox("Project Settings")
        project_layout = QtWidgets.QGridLayout(project_group)

        project_layout.addWidget(QtWidgets.QLabel("Default Project Root:"), 0, 0)
        self.project_root_edit = QtWidgets.QLineEdit()
        self.project_root_edit.setText(settings.get_project_root())
        project_layout.addWidget(self.project_root_edit, 0, 1)

        self.browse_project_btn = QtWidgets.QPushButton("Browse...")
        project_layout.addWidget(self.browse_project_btn, 0, 2)

        # Recent Projects Management
        project_layout.addWidget(QtWidgets.QLabel("Max Recent Projects:"), 1, 0)
        self.max_recent_spin = QtWidgets.QSpinBox()
        self.max_recent_spin.setRange(1, 20)
        self.max_recent_spin.setValue(settings.get("persistence.project_memory.max_recent_projects", 5))
        project_layout.addWidget(self.max_recent_spin, 1, 1)

        self.clear_recent_btn = QtWidgets.QPushButton("Clear Recent Projects")
        project_layout.addWidget(self.clear_recent_btn, 1, 2)

        layout.addWidget(project_group)

        # Session Management Group
        session_group = QtWidgets.QGroupBox("Session Management")
        session_layout = QtWidgets.QGridLayout(session_group)

        session_layout.addWidget(QtWidgets.QLabel("Auto-save Interval (seconds):"), 0, 0)
        self.autosave_spin = QtWidgets.QSpinBox()
        self.autosave_spin.setRange(10, 300)
        self.autosave_spin.setValue(settings.get("session.auto_save_interval", 30))
        session_layout.addWidget(self.autosave_spin, 0, 1)

        session_layout.addWidget(QtWidgets.QLabel("Session Backup Count:"), 1, 0)
        self.backup_count_spin = QtWidgets.QSpinBox()
        self.backup_count_spin.setRange(1, 10)
        self.backup_count_spin.setValue(settings.get("session.session_backup_count", 3))
        session_layout.addWidget(self.backup_count_spin, 1, 1)

        self.restore_crash_check = QtWidgets.QCheckBox("Enable Crash Recovery")
        self.restore_crash_check.setChecked(settings.get("session.restore_on_crash", True))
        session_layout.addWidget(self.restore_crash_check, 2, 0, 1, 2)

        layout.addWidget(session_group)

        layout.addStretch()

    def _create_workflow_tab(self) -> None:
        """Create workflow customization tab."""
        tab_widget = QtWidgets.QWidget()
        self.tab_widget.addTab(tab_widget, "Workflow")

        layout = QtWidgets.QVBoxLayout(tab_widget)
        layout.setSpacing(8)

        # Navigation Preferences
        nav_group = QtWidgets.QGroupBox("Navigation Preferences")
        nav_layout = QtWidgets.QGridLayout(nav_group)

        self.remember_context_check = QtWidgets.QCheckBox("Remember Last Navigation Context")
        self.remember_context_check.setChecked(
            settings.get("persistence.navigation_context.remember_last_context", True)
        )
        nav_layout.addWidget(self.remember_context_check, 0, 0, 1, 2)

        self.auto_restore_check = QtWidgets.QCheckBox("Auto-restore Context on Startup")
        self.auto_restore_check.setChecked(
            settings.get("persistence.navigation_context.auto_restore_on_startup", True)
        )
        nav_layout.addWidget(self.auto_restore_check, 1, 0, 1, 2)

        nav_layout.addWidget(QtWidgets.QLabel("Context History Limit:"), 2, 0)
        self.context_history_spin = QtWidgets.QSpinBox()
        self.context_history_spin.setRange(5, 50)
        self.context_history_spin.setValue(
            settings.get("persistence.navigation_context.context_history_limit", 10)
        )
        nav_layout.addWidget(self.context_history_spin, 2, 1)

        layout.addWidget(nav_group)

        # File Operations
        file_group = QtWidgets.QGroupBox("File Operation Preferences")
        file_layout = QtWidgets.QGridLayout(file_group)

        self.remember_dirs_check = QtWidgets.QCheckBox("Remember Last Directories")
        self.remember_dirs_check.setChecked(
            settings.get("persistence.file_operations.remember_last_directories", True)
        )
        file_layout.addWidget(self.remember_dirs_check, 0, 0, 1, 2)

        # Default file operation behaviors
        file_layout.addWidget(QtWidgets.QLabel("Default Import Behavior:"), 1, 0)
        self.import_behavior_combo = QtWidgets.QComboBox()
        self.import_behavior_combo.addItems(["Ask", "Reference", "Import", "Open"])
        file_layout.addWidget(self.import_behavior_combo, 1, 1)

        file_layout.addWidget(QtWidgets.QLabel("Default Export Format:"), 2, 0)
        self.export_format_combo = QtWidgets.QComboBox()
        self.export_format_combo.addItems(["Maya Binary", "Maya ASCII", "JSON Template"])
        file_layout.addWidget(self.export_format_combo, 2, 1)

        layout.addWidget(file_group)

        layout.addStretch()

    def _create_naming_tab(self) -> None:
        """Create naming convention customization tab."""
        tab_widget = QtWidgets.QWidget()
        self.tab_widget.addTab(tab_widget, "Naming")

        layout = QtWidgets.QVBoxLayout(tab_widget)
        layout.setSpacing(8)

        # General Naming Rules
        general_group = QtWidgets.QGroupBox("General Naming Rules")
        general_layout = QtWidgets.QGridLayout(general_group)

        general_layout.addWidget(QtWidgets.QLabel("Separator:"), 0, 0)
        self.separator_edit = QtWidgets.QLineEdit()
        self.separator_edit.setMaximumWidth(60)
        self.separator_edit.setText(settings.get("naming.separator", "_"))
        general_layout.addWidget(self.separator_edit, 0, 1)

        general_layout.addWidget(QtWidgets.QLabel("Index Padding:"), 1, 0)
        self.index_padding_spin = QtWidgets.QSpinBox()
        self.index_padding_spin.setRange(1, 6)
        self.index_padding_spin.setValue(settings.get("naming.index_padding", 3))
        general_layout.addWidget(self.index_padding_spin, 1, 1)

        general_layout.addWidget(QtWidgets.QLabel("Case Style:"), 2, 0)
        self.case_combo = QtWidgets.QComboBox()
        self.case_combo.addItems(["lower", "upper", "title", "camel"])
        self.case_combo.setCurrentText(settings.get("naming.case_style", "lower"))
        general_layout.addWidget(self.case_combo, 2, 1)

        layout.addWidget(general_group)

        # Light Naming Patterns
        light_group = QtWidgets.QGroupBox("Light Naming Patterns")
        light_layout = QtWidgets.QGridLayout(light_group)

        light_layout.addWidget(QtWidgets.QLabel("Pattern:"), 0, 0)
        self.light_pattern_edit = QtWidgets.QLineEdit()
        self.light_pattern_edit.setText(
            settings.get("naming.light_naming.pattern", "{sequence}_{shot}_{type}_{purpose}_{index:03d}")
        )
        light_layout.addWidget(self.light_pattern_edit, 0, 1)

        # Light Types
        light_layout.addWidget(QtWidgets.QLabel("Light Types:"), 1, 0)
        self.light_types_edit = QtWidgets.QLineEdit()
        light_types = settings.get("naming.light_naming.types", ["LGT", "AREA", "SPOT", "DIR", "POINT", "VOL"])
        self.light_types_edit.setText(", ".join(light_types))
        light_layout.addWidget(self.light_types_edit, 1, 1)

        # Light Purposes
        light_layout.addWidget(QtWidgets.QLabel("Light Purposes:"), 2, 0)
        self.light_purposes_edit = QtWidgets.QLineEdit()
        purposes = settings.get("naming.light_naming.purposes", ["key", "fill", "rim", "bounce", "practical", "fx"])
        self.light_purposes_edit.setText(", ".join(purposes))
        light_layout.addWidget(self.light_purposes_edit, 2, 1)

        layout.addWidget(light_group)

        # Preview Section
        preview_group = QtWidgets.QGroupBox("Preview")
        preview_layout = QtWidgets.QVBoxLayout(preview_group)

        self.naming_preview_label = QtWidgets.QLabel("Preview will appear here...")
        self.naming_preview_label.setStyleSheet("background: #f0f0f0; padding: 8px; border: 1px solid #ccc;")
        preview_layout.addWidget(self.naming_preview_label)

        layout.addWidget(preview_group)
        layout.addStretch()

    def _create_ui_tab(self) -> None:
        """Create UI customization tab."""
        tab_widget = QtWidgets.QWidget()
        self.tab_widget.addTab(tab_widget, "Interface")

        layout = QtWidgets.QVBoxLayout(tab_widget)
        layout.setSpacing(8)

        # Window Preferences
        window_group = QtWidgets.QGroupBox("Window Preferences")
        window_layout = QtWidgets.QGridLayout(window_group)

        self.restore_window_check = QtWidgets.QCheckBox("Restore Window State on Startup")
        self.restore_window_check.setChecked(settings.get("ui.window.restore_state", True))
        window_layout.addWidget(self.restore_window_check, 0, 0, 1, 2)

        window_layout.addWidget(QtWidgets.QLabel("Default Docking Area:"), 1, 0)
        self.docking_combo = QtWidgets.QComboBox()
        self.docking_combo.addItems(["right", "left", "top", "bottom"])
        self.docking_combo.setCurrentText(settings.get("ui.window.docking_area", "right"))
        window_layout.addWidget(self.docking_combo, 1, 1)

        layout.addWidget(window_group)

        # Widget State Persistence
        widget_group = QtWidgets.QGroupBox("Widget State Persistence")
        widget_layout = QtWidgets.QGridLayout(widget_group)

        self.save_filters_check = QtWidgets.QCheckBox("Save Filter States")
        self.save_filters_check.setChecked(settings.get("persistence.widget_states.save_filter_states", True))
        widget_layout.addWidget(self.save_filters_check, 0, 0)

        self.save_columns_check = QtWidgets.QCheckBox("Save Column Widths")
        self.save_columns_check.setChecked(settings.get("persistence.widget_states.save_column_widths", True))
        widget_layout.addWidget(self.save_columns_check, 0, 1)

        self.save_sort_check = QtWidgets.QCheckBox("Save Sort Orders")
        self.save_sort_check.setChecked(settings.get("persistence.widget_states.save_sort_orders", True))
        widget_layout.addWidget(self.save_sort_check, 1, 0)

        self.restore_expanded_check = QtWidgets.QCheckBox("Restore Expanded Items")
        self.restore_expanded_check.setChecked(settings.get("persistence.widget_states.restore_expanded_items", True))
        widget_layout.addWidget(self.restore_expanded_check, 1, 1)

        layout.addWidget(widget_group)

        # Refresh Settings
        refresh_group = QtWidgets.QGroupBox("Refresh Settings")
        refresh_layout = QtWidgets.QGridLayout(refresh_group)

        refresh_layout.addWidget(QtWidgets.QLabel("Auto-refresh Interval (ms):"), 0, 0)
        self.refresh_interval_spin = QtWidgets.QSpinBox()
        self.refresh_interval_spin.setRange(1000, 30000)
        self.refresh_interval_spin.setValue(settings.get("ui.refresh_interval", 5000))
        refresh_layout.addWidget(self.refresh_interval_spin, 0, 1)

        layout.addWidget(refresh_group)
        layout.addStretch()

    def _create_maya_tab(self) -> None:
        """Create Maya integration tab."""
        tab_widget = QtWidgets.QWidget()
        self.tab_widget.addTab(tab_widget, "Maya")

        layout = QtWidgets.QVBoxLayout(tab_widget)
        layout.setSpacing(8)

        # Render Setup Settings
        render_group = QtWidgets.QGroupBox("Render Setup Integration")
        render_layout = QtWidgets.QGridLayout(render_group)

        render_layout.addWidget(QtWidgets.QLabel("Default Layer Name:"), 0, 0)
        self.default_layer_edit = QtWidgets.QLineEdit()
        self.default_layer_edit.setText(
            settings.get("maya.render_setup.default_layer_name", "defaultRenderLayer")
        )
        render_layout.addWidget(self.default_layer_edit, 0, 1)

        render_layout.addWidget(QtWidgets.QLabel("Collection Prefix:"), 1, 0)
        self.collection_prefix_edit = QtWidgets.QLineEdit()
        self.collection_prefix_edit.setText(
            settings.get("maya.render_setup.collection_prefix", "collection_")
        )
        render_layout.addWidget(self.collection_prefix_edit, 1, 1)

        render_layout.addWidget(QtWidgets.QLabel("Override Prefix:"), 2, 0)
        self.override_prefix_edit = QtWidgets.QLineEdit()
        self.override_prefix_edit.setText(
            settings.get("maya.render_setup.override_prefix", "override_")
        )
        render_layout.addWidget(self.override_prefix_edit, 2, 1)

        layout.addWidget(render_group)

        # Light Management Settings
        light_mgmt_group = QtWidgets.QGroupBox("Light Management")
        light_mgmt_layout = QtWidgets.QGridLayout(light_mgmt_group)

        light_mgmt_layout.addWidget(QtWidgets.QLabel("Default Light Types:"), 0, 0)
        self.light_types_list = QtWidgets.QListWidget()
        self.light_types_list.setMaximumHeight(100)
        light_types = settings.get("maya.light_management.light_types", [])
        self.light_types_list.addItems(light_types)
        light_mgmt_layout.addWidget(self.light_types_list, 0, 1)

        light_mgmt_layout.addWidget(QtWidgets.QLabel("Default Attributes:"), 1, 0)
        self.light_attrs_list = QtWidgets.QListWidget()
        self.light_attrs_list.setMaximumHeight(100)
        light_attrs = settings.get("maya.light_management.default_attributes", [])
        self.light_attrs_list.addItems(light_attrs)
        light_mgmt_layout.addWidget(self.light_attrs_list, 1, 1)

        layout.addWidget(light_mgmt_group)
        layout.addStretch()

    def _create_advanced_tab(self) -> None:
        """Create advanced settings tab."""
        tab_widget = QtWidgets.QWidget()
        self.tab_widget.addTab(tab_widget, "Advanced")

        layout = QtWidgets.QVBoxLayout(tab_widget)
        layout.setSpacing(8)

        # Template Management
        template_group = QtWidgets.QGroupBox("Template Management")
        template_layout = QtWidgets.QGridLayout(template_group)

        template_layout.addWidget(QtWidgets.QLabel("Template Directory:"), 0, 0)
        self.template_dir_edit = QtWidgets.QLineEdit()
        self.template_dir_edit.setText(settings.get("templates.template_directory", "templates"))
        template_layout.addWidget(self.template_dir_edit, 0, 1)

        self.browse_template_btn = QtWidgets.QPushButton("Browse...")
        template_layout.addWidget(self.browse_template_btn, 0, 2)

        self.auto_discovery_check = QtWidgets.QCheckBox("Enable Auto-discovery")
        self.auto_discovery_check.setChecked(settings.get("templates.auto_discovery", True))
        template_layout.addWidget(self.auto_discovery_check, 1, 0, 1, 3)

        layout.addWidget(template_group)

        # Debug and Logging
        debug_group = QtWidgets.QGroupBox("Debug and Logging")
        debug_layout = QtWidgets.QGridLayout(debug_group)

        self.enable_logging_check = QtWidgets.QCheckBox("Enable Debug Logging")
        debug_layout.addWidget(self.enable_logging_check, 0, 0)

        self.verbose_mode_check = QtWidgets.QCheckBox("Verbose Mode")
        debug_layout.addWidget(self.verbose_mode_check, 0, 1)

        debug_layout.addWidget(QtWidgets.QLabel("Log Level:"), 1, 0)
        self.log_level_combo = QtWidgets.QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")
        debug_layout.addWidget(self.log_level_combo, 1, 1)

        layout.addWidget(debug_group)

        # Import/Export Configuration
        config_group = QtWidgets.QGroupBox("Configuration Management")
        config_layout = QtWidgets.QHBoxLayout(config_group)

        self.export_config_btn = QtWidgets.QPushButton("Export Configuration...")
        config_layout.addWidget(self.export_config_btn)

        self.import_config_btn = QtWidgets.QPushButton("Import Configuration...")
        config_layout.addWidget(self.import_config_btn)

        config_layout.addStretch()

        layout.addWidget(config_group)
        layout.addStretch()

    def _create_footer(self) -> None:
        """Create footer with action buttons."""
        self.footer_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(self.footer_widget)
        layout.setContentsMargins(0, 8, 0, 0)

        # Reset to defaults
        self.reset_defaults_btn = QtWidgets.QPushButton("Reset to Defaults")
        self.reset_defaults_btn.setStyleSheet("QPushButton { color: red; }")
        layout.addWidget(self.reset_defaults_btn)

        layout.addStretch()

        # Apply and Save buttons
        self.apply_btn = QtWidgets.QPushButton("Apply")
        self.apply_btn.setEnabled(False)
        layout.addWidget(self.apply_btn)

        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.setDefault(True)
        layout.addWidget(self.save_btn)

    def _connect_signals(self) -> None:
        """Connect UI signals to handlers."""
        # File browser buttons
        self.browse_project_btn.clicked.connect(self._browse_project_root)
        if hasattr(self, 'browse_template_btn'):
            self.browse_template_btn.clicked.connect(self._browse_template_directory)

        # Action buttons
        self.save_btn.clicked.connect(self._save_settings)
        self.apply_btn.clicked.connect(self._apply_settings)
        self.reset_defaults_btn.clicked.connect(self._reset_to_defaults)

        # Clear buttons
        self.clear_recent_btn.clicked.connect(self._clear_recent_projects)

        # Import/Export buttons
        if hasattr(self, 'export_config_btn'):
            self.export_config_btn.clicked.connect(self._export_configuration)
        if hasattr(self, 'import_config_btn'):
            self.import_config_btn.clicked.connect(self._import_configuration)

        # Change tracking for all inputs
        self._connect_change_tracking()

        print("Enhanced Settings signals connected")

    def _connect_change_tracking(self) -> None:
        """Connect change tracking to all input widgets."""
        # Track changes on various widget types
        for widget in self.findChildren(QtWidgets.QLineEdit):
            widget.textChanged.connect(self._on_setting_changed)

        for widget in self.findChildren(QtWidgets.QSpinBox):
            widget.valueChanged.connect(self._on_setting_changed)

        for widget in self.findChildren(QtWidgets.QComboBox):
            widget.currentTextChanged.connect(self._on_setting_changed)

        for widget in self.findChildren(QtWidgets.QCheckBox):
            widget.toggled.connect(self._on_setting_changed)

    def _on_setting_changed(self) -> None:
        """Handle setting change."""
        self._unsaved_changes = True
        self.apply_btn.setEnabled(True)
        self.status_label.setText("Unsaved changes")
        self.status_label.setStyleSheet("color: orange; font-style: italic;")

        # Update naming preview if on naming tab
        if self.tab_widget.currentIndex() == 2:  # Naming tab
            self._update_naming_preview()

    def _update_naming_preview(self) -> None:
        """Update naming convention preview."""
        try:
            separator = self.separator_edit.text()
            pattern = self.light_pattern_edit.text()

            # Create preview with sample data
            preview_text = pattern.format(
                sequence="sq0010",
                shot="SH0020",
                type="LGT",
                purpose="key",
                index=1
            )

            self.naming_preview_label.setText(f"Example: {preview_text}")

        except Exception as e:
            self.naming_preview_label.setText(f"Preview error: {str(e)}")

    def _load_settings(self) -> None:
        """Load current settings into the UI."""
        try:
            # Store original settings for comparison
            self._original_settings = {
                "project_root": settings.get_project_root(),
                "persistence": settings.get_persistence_settings(),
                "session": settings.get_session_settings(),
                "naming": settings.get_naming_settings(),
                "ui": settings.get_ui_settings(),
                "maya": settings.get("maya", {}),
                "templates": settings.get_template_settings()
            }

            # Reset change tracking
            self._unsaved_changes = False
            self.apply_btn.setEnabled(False)
            self.status_label.setText("All settings saved")
            self.status_label.setStyleSheet("color: green; font-style: italic;")

            # Update naming preview
            self._update_naming_preview()

            print("Settings loaded successfully")

        except Exception as e:
            print(f"Error loading settings: {e}")

    def _save_settings(self) -> None:
        """Save all settings."""
        try:
            self._apply_settings()
            settings.save_settings()

            self._unsaved_changes = False
            self.apply_btn.setEnabled(False)
            self.status_label.setText("All settings saved")
            self.status_label.setStyleSheet("color: green; font-style: italic;")

            # Emit signal
            self.settings_saved.emit(self._get_current_settings())

            print("Settings saved successfully")

        except Exception as e:
            print(f"Error saving settings: {e}")
            QtWidgets.QMessageBox.critical(self, "Save Error", f"Failed to save settings:\n{str(e)}")

    def _apply_settings(self) -> None:
        """Apply settings without saving to disk."""
        try:
            # General settings
            settings.set("project.project_root", self.project_root_edit.text())
            settings.set("persistence.project_memory.max_recent_projects", self.max_recent_spin.value())
            settings.set("session.auto_save_interval", self.autosave_spin.value())
            settings.set("session.session_backup_count", self.backup_count_spin.value())
            settings.set("session.restore_on_crash", self.restore_crash_check.isChecked())

            # Workflow settings
            settings.set("persistence.navigation_context.remember_last_context",
                        self.remember_context_check.isChecked())
            settings.set("persistence.navigation_context.auto_restore_on_startup",
                        self.auto_restore_check.isChecked())
            settings.set("persistence.navigation_context.context_history_limit",
                        self.context_history_spin.value())

            # Naming settings
            settings.set("naming.separator", self.separator_edit.text())
            settings.set("naming.index_padding", self.index_padding_spin.value())
            settings.set("naming.case_style", self.case_combo.currentText())
            settings.set("naming.light_naming.pattern", self.light_pattern_edit.text())

            # Parse comma-separated lists
            light_types = [t.strip() for t in self.light_types_edit.text().split(",") if t.strip()]
            settings.set("naming.light_naming.types", light_types)

            purposes = [p.strip() for p in self.light_purposes_edit.text().split(",") if p.strip()]
            settings.set("naming.light_naming.purposes", purposes)

            # UI settings
            settings.set("ui.window.restore_state", self.restore_window_check.isChecked())
            settings.set("ui.window.docking_area", self.docking_combo.currentText())
            settings.set("ui.refresh_interval", self.refresh_interval_spin.value())

            # Widget state persistence
            settings.set("persistence.widget_states.save_filter_states", self.save_filters_check.isChecked())
            settings.set("persistence.widget_states.save_column_widths", self.save_columns_check.isChecked())
            settings.set("persistence.widget_states.save_sort_orders", self.save_sort_check.isChecked())
            settings.set("persistence.widget_states.restore_expanded_items", self.restore_expanded_check.isChecked())

            # Maya settings
            settings.set("maya.render_setup.default_layer_name", self.default_layer_edit.text())
            settings.set("maya.render_setup.collection_prefix", self.collection_prefix_edit.text())
            settings.set("maya.render_setup.override_prefix", self.override_prefix_edit.text())

            # Template settings
            if hasattr(self, 'template_dir_edit'):
                settings.set("templates.template_directory", self.template_dir_edit.text())
            if hasattr(self, 'auto_discovery_check'):
                settings.set("templates.auto_discovery", self.auto_discovery_check.isChecked())

            print("Settings applied successfully")

        except Exception as e:
            print(f"Error applying settings: {e}")
            raise

    def _get_current_settings(self) -> Dict[str, Any]:
        """Get current settings as dictionary."""
        return {
            "project_root": self.project_root_edit.text(),
            "max_recent_projects": self.max_recent_spin.value(),
            "auto_save_interval": self.autosave_spin.value(),
            "naming_separator": self.separator_edit.text(),
            "light_pattern": self.light_pattern_edit.text(),
            "ui_refresh_interval": self.refresh_interval_spin.value()
        }

    def _browse_project_root(self) -> None:
        """Browse for project root directory."""
        current_root = self.project_root_edit.text()
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Project Root Directory", current_root
        )
        if directory:
            self.project_root_edit.setText(directory)

    def _browse_template_directory(self) -> None:
        """Browse for template directory."""
        if hasattr(self, 'template_dir_edit'):
            current_dir = self.template_dir_edit.text()
            directory = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select Template Directory", current_dir
            )
            if directory:
                self.template_dir_edit.setText(directory)

    def _clear_recent_projects(self) -> None:
        """Clear recent projects list."""
        reply = QtWidgets.QMessageBox.question(
            self, "Clear Recent Projects",
            "Are you sure you want to clear all recent projects?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            settings.clear_recent_projects()
            QtWidgets.QMessageBox.information(self, "Cleared", "Recent projects cleared successfully.")

    def _reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        reply = QtWidgets.QMessageBox.question(
            self, "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?\n"
            "This action cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            # Reset settings to defaults
            from ...config.defaults import DEFAULT_SETTINGS
            settings._settings = DEFAULT_SETTINGS.copy()
            settings.save_settings()

            # Reload UI
            self._load_settings()

            # Emit signal
            self.settings_reset.emit()

            QtWidgets.QMessageBox.information(self, "Reset Complete", "Settings reset to defaults.")

    def _export_configuration(self) -> None:
        """Export current configuration to file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Configuration",
            "lrc_toolbox_config.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                import json
                config_data = {
                    "version": settings.get("version", "2.0.0"),
                    "exported_at": settings._get_current_timestamp(),
                    "settings": settings._settings
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)

                QtWidgets.QMessageBox.information(
                    self, "Export Complete",
                    f"Configuration exported successfully to:\n{file_path}"
                )

            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Export Error",
                    f"Failed to export configuration:\n{str(e)}"
                )

    def _import_configuration(self) -> None:
        """Import configuration from file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Configuration",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                imported_settings = config_data.get("settings", {})

                reply = QtWidgets.QMessageBox.question(
                    self, "Import Configuration",
                    f"Import configuration from:\n{file_path}\n\n"
                    "This will overwrite current settings. Continue?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )

                if reply == QtWidgets.QMessageBox.Yes:
                    settings._settings.update(imported_settings)
                    settings.save_settings()
                    self._load_settings()

                    QtWidgets.QMessageBox.information(
                        self, "Import Complete",
                        "Configuration imported successfully."
                    )

            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Import Error",
                    f"Failed to import configuration:\n{str(e)}"
                )

    def refresh(self) -> None:
        """Refresh the settings widget."""
        self._load_settings()

    def set_navigation_context(self, context) -> None:
        """Set navigation context (for consistency with other widgets)."""
        # Settings widget doesn't need context, but method provided for interface consistency
        pass

    def get_state(self) -> Dict[str, Any]:
        """Get current widget state."""
        return {
            "current_tab": self.tab_widget.currentIndex(),
            "unsaved_changes": self._unsaved_changes
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        """Set widget state."""
        if "current_tab" in state:
            self.tab_widget.setCurrentIndex(state["current_tab"])