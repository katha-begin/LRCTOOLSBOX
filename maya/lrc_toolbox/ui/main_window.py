"""
Main Window for LRC Toolbox

This module contains the main UI window that serves as the primary interface
for the LRC Toolbox application with enhanced template management.
"""

import sys
import os
from typing import Optional, Dict, Any

# Ensure UTF-8 encoding for emoji and Unicode support
if sys.version_info >= (3, 7):
    # Python 3.7+ has UTF-8 mode
    if not os.environ.get('PYTHONUTF8'):
        os.environ['PYTHONUTF8'] = '1'
else:
    # For older Python versions, set encoding explicitly
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            pass  # Use system default

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtWidgets import *
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    QAction = QtWidgets.QAction
    QShortcut = QtWidgets.QShortcut
except ImportError:
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        from PySide6.QtWidgets import *
        from PySide6.QtCore import *
        from PySide6.QtGui import *
        # In PySide6, QAction and QShortcut are in QtGui, not QtWidgets
        QAction = QtGui.QAction
        QShortcut = QtGui.QShortcut
    except ImportError:
        print("Warning: Neither PySide2 nor PySide6 available")
        QtWidgets = None

from ..config.settings import settings
from .widgets.navigator_widget import NavigatorWidget
from .widgets.template_tools_widget import TemplateToolsWidget
from .widgets.render_setup_widget import RenderSetupWidget
from .widgets.light_manager_widget import LightManagerWidget
from .widgets.regex_tools_widget import RegexToolsWidget
from .widgets.settings_widget_enhanced import EnhancedSettingsWidget as SettingsWidget
from .widgets.batch_render_widget import BatchRenderWidget
from ..core.models import NavigationContext, ProjectType
from ..utils.error_handler import error_handler, ErrorCategory, error_handler_decorator


class RenderSetupUI(QtWidgets.QMainWindow):
    """
    Main window for the LRC Toolbox application.

    Enhanced template management system with tab-based interface supporting:
    - Asset/Shot Navigator with context-aware navigation
    - Render Setup management with template packages
    - Light Manager with pattern-based naming
    - Regex Tools for DAG path conversion
    - Settings for configuration management
    """

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the main window.

        Args:
            parent: Parent widget (Maya main window when docked)
        """
        super().__init__(parent)

        # Set object name for Maya docking
        self.setObjectName("LRCToolboxMainWindow")

        # Initialize UI components
        self._setup_window()
        self._create_widgets()
        self._create_layouts()
        self._connect_signals()
        self._restore_window_state()

        # Add docking menu actions
        self._create_docking_menu()

        print("SUCCESS: RenderSetupUI initialized with tab-based interface")

    def _setup_unicode_font(self) -> None:
        """Setup font for proper Unicode and emoji rendering."""
        try:
            # Get current font
            current_font = self.font()

            # Set font properties for better Unicode support
            font = QtGui.QFont(current_font)

            # Try to use system fonts that support emoji
            preferred_fonts = [
                "Segoe UI Emoji",  # Windows
                "Apple Color Emoji",  # macOS
                "Noto Color Emoji",  # Linux
                "Segoe UI",  # Windows fallback
                "Arial Unicode MS",  # Cross-platform
                current_font.family()  # Current font as final fallback
            ]

            for font_name in preferred_fonts:
                font.setFamily(font_name)
                font_info = QtGui.QFontInfo(font)
                if font_info.family() == font_name:
                    break

            # Ensure proper rendering
            font.setStyleHint(QtGui.QFont.SansSerif)
            font.setStyleStrategy(QtGui.QFont.PreferAntialias)

            # Apply font to application
            self.setFont(font)

            print(f"Unicode font setup: {font.family()}")

        except Exception as e:
            print(f"Warning: Could not setup Unicode font: {e}")

    def _setup_docking_features(self) -> None:
        """Setup enhanced docking features for Maya integration."""
        try:
            # Enable proper resizing in all directions
            self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

            # Set size constraints for better docking behavior
            self.setMinimumSize(400, 600)
            self.setMaximumSize(16777215, 16777215)  # Qt maximum

            # Enable corner widget docking
            self.setCorner(QtCore.Qt.TopLeftCorner, QtCore.Qt.LeftDockWidgetArea)
            self.setCorner(QtCore.Qt.TopRightCorner, QtCore.Qt.RightDockWidgetArea)
            self.setCorner(QtCore.Qt.BottomLeftCorner, QtCore.Qt.LeftDockWidgetArea)
            self.setCorner(QtCore.Qt.BottomRightCorner, QtCore.Qt.RightDockWidgetArea)

            # Set window properties for better Maya integration
            self.setWindowFlags(
                QtCore.Qt.Window |
                QtCore.Qt.WindowMinimizeButtonHint |
                QtCore.Qt.WindowMaximizeButtonHint |
                QtCore.Qt.WindowCloseButtonHint
            )

            # Store docking state
            self._is_docked = False
            self._dock_area = None
            self._floating_geometry = None

            print("Enhanced docking features configured")

        except Exception as e:
            print(f"Warning: Could not setup docking features: {e}")

    def _create_docking_menu(self) -> None:
        """Create docking menu actions."""
        try:
            # Find or create Window menu
            window_menu = None
            for action in self.menuBar().actions():
                if action.text() == "&Window":
                    window_menu = action.menu()
                    break

            if not window_menu:
                window_menu = self.menuBar().addMenu("&Window")

            # Add separator if menu has items
            if window_menu.actions():
                window_menu.addSeparator()

            # Undock action
            undock_action = QtWidgets.QAction("&Undock Window", self)
            undock_action.setShortcut("Ctrl+Shift+U")
            undock_action.setStatusTip("Undock window to float independently")
            undock_action.triggered.connect(self._undock_window)
            window_menu.addAction(undock_action)

            # Redock action
            redock_action = QtWidgets.QAction("&Redock Window", self)
            redock_action.setShortcut("Ctrl+Shift+D")
            redock_action.setStatusTip("Redock floating window back to Maya")
            redock_action.triggered.connect(self._redock_window)
            window_menu.addAction(redock_action)

            print("Docking menu actions created")

        except Exception as e:
            print(f"Warning: Could not create docking menu: {e}")

    def _undock_window(self) -> None:
        """Undock window to float independently."""
        try:
            if not self._is_docked:
                QtWidgets.QMessageBox.information(self, "Undock Window",
                                                "Window is already floating.")
                return

            # Store current docked state
            self._floating_geometry = self.geometry()

            # Set window flags for floating
            self.setWindowFlags(
                QtCore.Qt.Window |
                QtCore.Qt.WindowMinimizeButtonHint |
                QtCore.Qt.WindowMaximizeButtonHint |
                QtCore.Qt.WindowCloseButtonHint
            )

            # Show as floating window
            self.show()
            self._is_docked = False

            self.status_bar.showMessage("🔓 Window undocked - now floating independently")
            print("Window undocked successfully")

        except Exception as e:
            print(f"Error undocking window: {e}")
            QtWidgets.QMessageBox.warning(self, "Undock Error",
                                        f"Could not undock window: {str(e)}")

    def _redock_window(self) -> None:
        """Redock floating window back to Maya."""
        try:
            if self._is_docked:
                QtWidgets.QMessageBox.information(self, "Redock Window",
                                                "Window is already docked.")
                return

            # Check if Maya is available for docking
            maya_available = False
            try:
                import maya.cmds as cmds
                maya_available = True
            except ImportError:
                pass

            if not maya_available:
                QtWidgets.QMessageBox.warning(self, "Redock Error",
                                            "Maya is not available for docking.")
                return

            # Restore docked window flags
            self.setWindowFlags(QtCore.Qt.Window)

            # Restore geometry if available
            if self._floating_geometry:
                self.setGeometry(self._floating_geometry)

            self.show()
            self._is_docked = True

            self.status_bar.showMessage("🔒 Window redocked to Maya interface")
            print("Window redocked successfully")

        except Exception as e:
            print(f"Error redocking window: {e}")
            QtWidgets.QMessageBox.warning(self, "Redock Error",
                                        f"Could not redock window: {str(e)}")

    def _setup_window(self) -> None:
        """Configure the main window properties according to UI design specifications."""
        self.setWindowTitle("Render Setup Manager v2.0")

        # Get window settings from configuration
        ui_settings = settings.get_ui_settings()
        window_settings = ui_settings.get("window", {})

        # Set window size (UI design specifies 700x900 minimum)
        width = window_settings.get("width", 700)
        height = window_settings.get("height", 900)
        self.resize(width, height)

        # Set minimum size as per UI design specifications (but allow resizing)
        self.setMinimumSize(400, 600)  # Reduced minimum for better flexibility

        # Set size policy for proper resizing
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # Set window icon (placeholder - will be enhanced later)
        self.setWindowIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))

        # Ensure proper font rendering for Unicode/emoji
        self._setup_unicode_font()

        # Configure for Maya docking (right/left areas as specified)
        self.setDockNestingEnabled(True)

        # Maya-specific docking properties
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setWindowFlags(QtCore.Qt.Window)

        # Enhanced docking capabilities
        self._setup_docking_features()

        # Create menu bar and keyboard shortcuts
        self._create_menu_bar()
        self._create_keyboard_shortcuts()
    
    def _create_widgets(self) -> None:
        """Create all UI widgets according to tab-based design."""
        # Create central widget (use Maya's default colors)
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        # Create main tab widget with enhanced styling and increased header height
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabPosition(QtWidgets.QTabWidget.North)

        # Apply Maya-consistent tab styling - reduced height, bigger font
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                padding: 6px 12px;
                margin: 0px;
                min-width: 80px;
                min-height: 25px;
                text-align: center;
                font-size: 12px;
                font-weight: normal;
            }
            QTabBar::tab:selected {
                font-weight: bold;
            }
        """)

        # Create tab content widgets (placeholders for now)
        self._create_tab_placeholders()

        # Create status bar
        self._create_status_bar()

    def _create_menu_bar(self) -> None:
        """Create menu bar with file, tools, and help menus."""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        # Refresh action
        refresh_action = QAction("&Refresh All", self)
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("Refresh all widgets and reload data")
        refresh_action.triggered.connect(self.refresh_all_widgets)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        # Settings action
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.setStatusTip("Open settings dialog")
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        # Close action
        close_action = QAction("&Close", self)
        close_action.setShortcut("Ctrl+W")
        close_action.setStatusTip("Close the application")
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")

        # Switch to Asset Navigator
        nav_action = QAction("&Asset Navigator", self)
        nav_action.setShortcut("Ctrl+1")
        nav_action.setStatusTip("Switch to Asset Navigator tab")
        nav_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        tools_menu.addAction(nav_action)

        # Switch to Template Tools
        template_action = QAction("&Template Tools", self)
        template_action.setShortcut("Ctrl+2")
        template_action.setStatusTip("Switch to Template Tools tab")
        template_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        tools_menu.addAction(template_action)

        # Switch to Light Manager
        light_action = QAction("&Light Manager", self)
        light_action.setShortcut("Ctrl+3")
        light_action.setStatusTip("Switch to Light Manager tab")
        light_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        tools_menu.addAction(light_action)

        # Switch to Render Setup
        render_action = QAction("&Render Setup", self)
        render_action.setShortcut("Ctrl+4")
        render_action.setStatusTip("Switch to Render Setup tab")
        render_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        tools_menu.addAction(render_action)

        # Switch to Regex Tools
        regex_action = QAction("Re&gex Tools", self)
        regex_action.setShortcut("Ctrl+5")
        regex_action.setStatusTip("Switch to Regex Tools tab")
        regex_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))
        tools_menu.addAction(regex_action)

        tools_menu.addSeparator()

        # Export Current Context
        export_context_action = QAction("Export &Context...", self)
        export_context_action.setShortcut("Ctrl+E")
        export_context_action.setStatusTip("Export current navigation context")
        export_context_action.triggered.connect(self._export_context)
        tools_menu.addAction(export_context_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = QAction("&About LRC Toolbox", self)
        about_action.setStatusTip("About LRC Toolbox")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_keyboard_shortcuts(self) -> None:
        """Create additional keyboard shortcuts."""
        # Tab switching shortcuts
        for i in range(6):  # 0-5 for our 6 tabs
            shortcut = QShortcut(f"Alt+{i+1}", self)
            shortcut.activated.connect(lambda idx=i: self.tab_widget.setCurrentIndex(idx))

        # Context refresh shortcut
        refresh_shortcut = QShortcut("Ctrl+R", self)
        refresh_shortcut.activated.connect(self.refresh_all_widgets)

        # Quick context switch (for development)
        if self.is_maya_available():
            # Maya-specific shortcuts can be added here
            pass

        print("INFO: Keyboard shortcuts created")

    def _create_tab_placeholders(self) -> None:
        """Create tabs with updated UI design specifications and cross-widget communication."""
        # Current navigation context shared across widgets
        self._current_context = None

        # Tab 1: Project Navigator (📁) - Shot/Asset Navigation and File Browser
        self.navigator_widget = NavigatorWidget()
        self.navigator_widget.context_changed.connect(self._on_context_changed)
        self.navigator_widget.file_selected.connect(self._on_file_selected)
        self.tab_widget.addTab(self.navigator_widget, "📁\nProject\nNavigator")

        # Tab 2: Template Tools (🔧) - Render Layer + Light Management
        self.template_tools_widget = TemplateToolsWidget()
        self.template_tools_widget.layer_created.connect(self._on_layer_created)
        self.template_tools_widget.lights_renamed.connect(self._on_lights_renamed)
        self.tab_widget.addTab(self.template_tools_widget, "🔧\nTemplate\nTools")

        # Tab 3: Light Manager (💡) - Advanced Light Management
        self.light_manager_widget = LightManagerWidget()
        self.light_manager_widget.lights_renamed.connect(self._on_lights_renamed)
        self.light_manager_widget.lights_exported.connect(self._on_lights_exported)
        self.tab_widget.addTab(self.light_manager_widget, "💡\nLight\nManager")

        # Tab 4: Render Setup (📋) - Template Browser + Import
        self.render_setup_widget = RenderSetupWidget()
        self.render_setup_widget.template_loaded.connect(self._on_template_loaded)
        self.render_setup_widget.package_imported.connect(self._on_package_imported)
        self.tab_widget.addTab(self.render_setup_widget, "📋\nRender\nSetup")

        # Tab 5: Regex Tools (🔧) - DAG Path Conversion
        self.regex_tools_widget = RegexToolsWidget()
        self.regex_tools_widget.regex_generated.connect(self._on_regex_generated)
        self.tab_widget.addTab(self.regex_tools_widget, "🔧\nRegex\nTools")

        # Tab 6: Batch Render (🎬) - GPU Batch Rendering
        self.batch_render_widget = BatchRenderWidget()
        self.tab_widget.addTab(self.batch_render_widget, "🎬\nBatch\nRender")

        # Tab 7: Settings (⚙️) - Configuration Management
        self.settings_widget = SettingsWidget()
        self.settings_widget.settings_saved.connect(self._on_settings_saved)
        self.tab_widget.addTab(self.settings_widget, "⚙️\nSettings")

    def _create_status_bar(self) -> None:
        """Create status bar for application feedback."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("✅ Ready - LRC Toolbox v2.0 with Enhanced Template Management")

    def _create_layouts(self) -> None:
        """Create and set up the main layout with tab widget."""
        # Create main layout for central widget
        main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
    

    
    def _connect_signals(self) -> None:
        """Connect widget signals to their handlers."""
        # Tab widget signals
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        print("INFO: Tab-based signal connections established")
    
    # Event handlers (placeholder implementations)
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change event."""
        tab_names = [
            "Navigator",
            "Template Tools",
            "Render Setup",
            "Regex Tools",
            "Settings"
        ]

        if 0 <= index < len(tab_names):
            tab_name = tab_names[index]
            self.status_bar.showMessage(f"📋 Switched to {tab_name} tab")
            print(f"🔄 Tab changed to: {tab_name} (index: {index})")
        else:
            print(f"⚠️ Unknown tab index: {index}")

    def _on_context_changed(self, context: dict) -> None:
        """Handle context change from Asset Navigator and propagate to other widgets."""
        context_str = ""
        context_type = context.get("type", "unknown")

        # Create NavigationContext from dict
        nav_context = None
        if context_type == "shot":
            # Shot navigator context
            episode = context.get("episode", "")
            sequence = context.get("sequence", "")
            shot = context.get("shot", "")
            department = context.get("department", "")
            if all([episode, sequence, shot, department]):
                context_str = f"🎬 {episode}/{sequence}/{shot}/{department}"
                nav_context = NavigationContext(
                    type=ProjectType.SHOT,
                    episode=episode,
                    sequence=sequence,
                    shot=shot,
                    department=department
                )
        elif context_type == "asset":
            # Asset navigator context
            category = context.get("category", "")
            subcategory = context.get("subcategory", "")
            asset = context.get("asset", "")
            department = context.get("department", "")
            if all([category, subcategory, asset, department]):
                context_str = f"🎨 {category}/{subcategory}/{asset}/{department}"
                nav_context = NavigationContext(
                    type=ProjectType.ASSET,
                    category=category,
                    subcategory=subcategory,
                    asset=asset,
                    department=department
                )

        if context_str and nav_context:
            # Store current context
            self._current_context = nav_context

            # Update status bar
            self.status_bar.showMessage(f"📍 Context: {context_str}")
            print(f"🔄 Navigation context changed: {context_str}")

            # Save navigation context to settings
            self._save_navigation_context(nav_context)

            # Propagate context to other widgets
            self._propagate_context_to_widgets(nav_context)

    def _propagate_context_to_widgets(self, context: NavigationContext) -> None:
        """Propagate navigation context to all relevant widgets."""
        try:
            # Update Template Tools widget with new context
            if hasattr(self.template_tools_widget, 'set_navigation_context'):
                self.template_tools_widget.set_navigation_context(context)

            # Update Light Manager with context for naming prefixes
            if hasattr(self.light_manager_widget, 'set_navigation_context'):
                self.light_manager_widget.set_navigation_context(context)

            # Update Render Setup widget with context for template filtering
            if hasattr(self.render_setup_widget, 'set_navigation_context'):
                self.render_setup_widget.set_navigation_context(context)

            # Update Regex Tools widget with context for pattern generation
            if hasattr(self.regex_tools_widget, 'set_navigation_context'):
                self.regex_tools_widget.set_navigation_context(context)

            print(f"🔗 Context propagated to all widgets: {context.get_display_name()}")

        except Exception as e:
            print(f"⚠️ Error propagating context: {e}")
            self.status_bar.showMessage(f"⚠️ Context update error: {str(e)}")

    def _on_template_loaded(self, template_name: str) -> None:
        """Handle template loaded signal from Render Setup widget."""
        self.status_bar.showMessage(f"📋 Template loaded: {template_name}")
        print(f"✅ Template loaded: {template_name}")

    def _on_layer_created(self, layer_name: str) -> None:
        """Handle render layer created signal from Template Tools widget."""
        self.status_bar.showMessage(f"🔧 Render layer created: {layer_name}")
        print(f"✅ Render layer created: {layer_name}")

    def _on_lights_renamed(self, light_names: list) -> None:
        """Handle lights renamed signal from Template Tools widget."""
        count = len(light_names)
        self.status_bar.showMessage(f"🔧 {count} lights renamed successfully")
        print(f"✅ Lights renamed: {light_names}")

    def _on_package_imported(self, package_name: str) -> None:
        """Handle template package imported signal from Render Setup widget."""
        self.status_bar.showMessage(f"📋 Package imported: {package_name}")
        print(f"✅ Package imported: {package_name}")

    def _on_regex_generated(self, regex_pattern: str) -> None:
        """Handle regex generated signal from Regex Tools widget."""
        self.status_bar.showMessage(f"🔧 Regex pattern generated")
        print(f"✅ Regex generated: {regex_pattern}")

    def _on_settings_saved(self, settings_dict: dict) -> None:
        """Handle settings saved signal from Settings widget."""
        self.status_bar.showMessage(f"⚙️ Settings saved successfully")
        print(f"✅ Settings saved: {len(settings_dict)} settings updated")

    def _on_file_selected(self, file_path: str) -> None:
        """Handle file selected signal from Asset Navigator."""
        import os
        file_name = os.path.basename(file_path)
        self.status_bar.showMessage(f"📁 Selected file: {file_name}")
        print(f"📁 File selected: {file_path}")

    def _on_lights_exported(self, export_path: str) -> None:
        """Handle lights exported signal from Light Manager."""
        import os
        export_name = os.path.basename(export_path)
        self.status_bar.showMessage(f"💡 Lights exported to: {export_name}")
        print(f"✅ Lights exported: {export_path}")

        # Notify other widgets about light export if needed
        if hasattr(self.template_tools_widget, 'on_lights_exported'):
            self.template_tools_widget.on_lights_exported(export_path)

    def get_maya_dock_name(self) -> str:
        """Get the Maya dock control name for this window."""
        return f"{self.objectName()}Dock"

    def is_maya_available(self) -> bool:
        """Check if Maya is available for docking."""
        try:
            import maya.cmds as cmds
            return True
        except ImportError:
            return False

    def get_current_context(self) -> Optional[NavigationContext]:
        """Get the current navigation context."""
        return self._current_context

    def refresh_all_widgets(self) -> None:
        """Refresh all widgets with current context."""
        if self._current_context:
            self._propagate_context_to_widgets(self._current_context)

        # Refresh individual widgets
        try:
            if hasattr(self.navigator_widget, 'refresh'):
                self.navigator_widget.refresh()

            if hasattr(self.template_tools_widget, 'refresh'):
                self.template_tools_widget.refresh()

            if hasattr(self.light_manager_widget, 'refresh'):
                self.light_manager_widget.refresh()

            if hasattr(self.render_setup_widget, 'refresh'):
                self.render_setup_widget.refresh()

            if hasattr(self.regex_tools_widget, 'refresh'):
                self.regex_tools_widget.refresh()

            if hasattr(self.settings_widget, 'refresh'):
                self.settings_widget.refresh()

            self.status_bar.showMessage("🔄 All widgets refreshed")
            print("✅ All widgets refreshed successfully")

        except Exception as e:
            print(f"⚠️ Error refreshing widgets: {e}")
            self.status_bar.showMessage(f"⚠️ Refresh error: {str(e)}")

    def set_context(self, context: NavigationContext) -> None:
        """Set navigation context from external source."""
        self._current_context = context
        self._propagate_context_to_widgets(context)

        # Update status bar
        context_str = ""
        if context.type == ProjectType.SHOT:
            context_str = f"🎬 {context.episode}/{context.sequence}/{context.shot}/{context.department}"
        else:
            context_str = f"🎨 {context.category}/{context.subcategory}/{context.asset}/{context.department}"

        self.status_bar.showMessage(f"📍 Context: {context_str}")
        print(f"🔄 Context set externally: {context_str}")

    def _open_settings(self) -> None:
        """Open settings tab."""
        # Switch to settings tab (index 5)
        self.tab_widget.setCurrentIndex(5)
        self.status_bar.showMessage("⚙️ Settings opened")

    def _export_context(self) -> None:
        """Export current navigation context to file."""
        if not self._current_context:
            QtWidgets.QMessageBox.information(
                self, "Export Context",
                "No navigation context available to export."
            )
            return

        # Open file dialog
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Navigation Context",
            f"context_{self._current_context.get_display_name().replace('/', '_')}.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                import json
                context_data = {
                    "type": self._current_context.type.value,
                    "episode": self._current_context.episode,
                    "sequence": self._current_context.sequence,
                    "shot": self._current_context.shot,
                    "category": self._current_context.category,
                    "subcategory": self._current_context.subcategory,
                    "asset": self._current_context.asset,
                    "department": self._current_context.department,
                    "exported_at": QtCore.QDateTime.currentDateTime().toString(),
                    "display_name": self._current_context.get_display_name()
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(context_data, f, indent=2, ensure_ascii=False)

                self.status_bar.showMessage(f"📁 Context exported to: {file_path}")
                print(f"✅ Context exported: {file_path}")

            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Export Error",
                    f"Failed to export context:\n{str(e)}"
                )
                print(f"❌ Export error: {e}")

    def _show_about(self) -> None:
        """Show about dialog."""
        about_text = """
<h3>LRC Toolbox v2.0</h3>
<p>Maya lighting and render setup management tool with enhanced template management.</p>

<p><b>Features:</b></p>
<ul>
<li>Asset/Shot Navigation with context-aware workflows</li>
<li>Template Management with inheritance system</li>
<li>Light Manager with pattern-based naming</li>
<li>Render Setup integration</li>
<li>Regex Tools for DAG path conversion</li>
<li>Cross-widget communication</li>
</ul>

<p><b>Keyboard Shortcuts:</b></p>
<ul>
<li>F5 / Ctrl+R: Refresh all widgets</li>
<li>Ctrl+1-5: Switch between tabs</li>
<li>Alt+1-6: Alternative tab switching</li>
<li>Ctrl+E: Export current context</li>
<li>Ctrl+W: Close window</li>
</ul>

<p>Developed for Maya 2024+ with PySide2/PySide6 support.</p>
        """

        QtWidgets.QMessageBox.about(self, "About LRC Toolbox", about_text)

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Save current window settings
        try:
            current_settings = settings.get("ui.window", {})
            current_settings.update({
                "width": self.width(),
                "height": self.height(),
                "tab_index": self.tab_widget.currentIndex()
            })
            settings.set("ui.window", current_settings)
            settings.save_settings()
            print("✅ Window settings saved on close")
        except Exception as e:
            print(f"⚠️ Error saving window settings: {e}")

        # Call parent close event
        super().closeEvent(event)

    def _restore_window_state(self) -> None:
        """Restore window state from settings."""
        try:
            window_settings = settings.get("ui.window", {})

            # Restore last active tab
            last_tab = window_settings.get("tab_index", 0)
            if 0 <= last_tab < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(last_tab)
                print(f"🔄 Restored last active tab: {last_tab}")

            # Restore navigation context if enabled
            if settings.get("persistence.navigation_context.auto_restore_on_startup", True):
                self._restore_navigation_context()

            # Add current project to recent projects
            current_project_root = settings.get_project_root()
            if current_project_root:
                settings.add_recent_project(current_project_root, "Current Project")

        except Exception as e:
            print(f"⚠️ Error restoring window state: {e}")

    @error_handler_decorator(category=ErrorCategory.NAVIGATION, attempt_recovery=True)
    def _restore_navigation_context(self) -> None:
        """Restore last navigation context from settings."""
        last_context_data = settings.get_last_navigation_context()
        if last_context_data:
            # Convert dict back to NavigationContext
            nav_context = NavigationContext(
                type=ProjectType(last_context_data.get("type", "shot")),
                episode=last_context_data.get("episode", ""),
                sequence=last_context_data.get("sequence", ""),
                shot=last_context_data.get("shot", ""),
                category=last_context_data.get("category", ""),
                subcategory=last_context_data.get("subcategory", ""),
                asset=last_context_data.get("asset", ""),
                department=last_context_data.get("department", "")
            )

            # Set context without saving (to avoid loops)
            self._current_context = nav_context
            self._propagate_context_to_widgets(nav_context)

            # Update status bar
            context_str = nav_context.get_display_name()
            self.status_bar.showMessage(f"Restored context: {context_str}")
            print(f"Navigation context restored: {context_str}")

    @error_handler_decorator(category=ErrorCategory.SETTINGS, attempt_recovery=True)
    def _save_navigation_context(self, context: NavigationContext) -> None:
        """Save navigation context to settings."""
        context_data = {
            "type": context.type.value,
            "episode": context.episode,
            "sequence": context.sequence,
            "shot": context.shot,
            "category": context.category,
            "subcategory": context.subcategory,
            "asset": context.asset,
            "department": context.department,
            "display_name": context.get_display_name(),
            "timestamp": settings._get_current_timestamp()
        }

        settings.save_navigation_context(context_data)

    def get_communication_hub_info(self) -> Dict[str, Any]:
        """Get information about the communication hub state."""
        return {
            "current_context": self._current_context.to_dict() if self._current_context else None,
            "active_tab": self.tab_widget.currentIndex(),
            "tab_count": self.tab_widget.count(),
            "widget_states": {
                "navigator": hasattr(self.navigator_widget, 'get_state'),
                "template_tools": hasattr(self.template_tools_widget, 'get_state'),
                "light_manager": hasattr(self.light_manager_widget, 'get_state'),
                "render_setup": hasattr(self.render_setup_widget, 'get_state'),
                "regex_tools": hasattr(self.regex_tools_widget, 'get_state'),
                "settings": hasattr(self.settings_widget, 'get_state')
            },
            "is_maya_docked": self.is_maya_available(),
            "window_size": {
                "width": self.width(),
                "height": self.height()
            }
        }
