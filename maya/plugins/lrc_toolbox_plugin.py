"""
LRC Toolbox v2.0 Maya Plugin

This plugin provides easy loading and management of the LRC Toolbox v2.0
Enhanced Template Management System directly from Maya's Plugin Manager.

Installation:
1. Add the parent directory to MAYA_PLUG_IN_PATH in Maya.env
2. Load the plugin from Maya's Plugin Manager
3. The LRC Toolbox will be available in the Maya menu and as a dockable window

Usage:
- Menu: LRC Toolbox > Open Toolbox
- Command: lrc_toolbox_open()
- Dockable: The toolbox will dock to the right side of Maya by default
"""

import sys
import os
from typing import Optional

import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel

# Plugin information
PLUGIN_NAME = "LRC Toolbox v2.0"
PLUGIN_VERSION = "2.0.0"
PLUGIN_AUTHOR = "LRC Team"
PLUGIN_DESCRIPTION = "Enhanced Template Management & Context-Aware Workflows"

# Global reference to keep UI alive
_lrc_toolbox_ui = None


def maya_useNewAPI():
    """Tell Maya to use the new API."""
    pass


class LRCToolboxCommand(om.MPxCommand):
    """Maya command for opening the LRC Toolbox."""

    COMMAND_NAME = "lrcToolboxOpen"

    def __init__(self):
        super().__init__()

    @staticmethod
    def creator():
        """Create command instance."""
        return LRCToolboxCommand()

    def doIt(self, args):
        """Execute the command."""
        try:
            # Import and create the toolbox
            toolbox_ui = open_lrc_toolbox()
            if toolbox_ui:
                om.MGlobal.displayInfo("✅ LRC Toolbox v2.0 opened successfully")
            else:
                om.MGlobal.displayError("❌ Failed to open LRC Toolbox v2.0")
        except Exception as e:
            om.MGlobal.displayError(f"❌ Error opening LRC Toolbox: {str(e)}")


class LRCSaveSettingsCommand(om.MPxCommand):
    """Maya command for opening the Save & Settings tool."""

    COMMAND_NAME = "lrcOpenSaveSettings"

    def __init__(self):
        super().__init__()

    @staticmethod
    def creator():
        """Create command instance."""
        return LRCSaveSettingsCommand()

    def doIt(self, args):
        """Execute the command."""
        try:
            result = lrc_open_save_settings_tool()
            if result:
                om.MGlobal.displayInfo("✅ Save & Settings tool opened successfully")
            else:
                om.MGlobal.displayError("❌ Failed to open Save & Settings tool")
        except Exception as e:
            om.MGlobal.displayError(f"❌ Error opening Save & Settings tool: {str(e)}")


class LRCShotBuildCommand(om.MPxCommand):
    """Maya command for opening the Shot Build tool."""

    COMMAND_NAME = "lrcOpenShotBuild"

    def __init__(self):
        super().__init__()

    @staticmethod
    def creator():
        return LRCShotBuildCommand()

    def doIt(self, args):
        """Execute the command."""
        try:
            result = lrc_open_shot_build_tool()
            if result:
                om.MGlobal.displayInfo("✅ Shot Build tool opened successfully")
            else:
                om.MGlobal.displayError("❌ Failed to open Shot Build tool")
        except Exception as e:
            om.MGlobal.displayError(f"❌ Error opening Shot Build tool: {str(e)}")


def open_lrc_toolbox():
    """
    Open the LRC Toolbox UI.
    
    Returns:
        UI widget instance or None if creation failed
    """
    global _lrc_toolbox_ui
    
    try:
        # Add the parent directory to Python path (go up from plugins/ to maya/)
        # Handle case where __file__ might not be defined in Maya's execution context
        try:
            plugin_dir = os.path.dirname(__file__)
            parent_dir = os.path.dirname(plugin_dir)  # Go up one level to maya/
        except NameError:
            # Fallback: search for lrc_toolbox in sys.path
            parent_dir = None
            for path in sys.path:
                if path.endswith('maya') and os.path.exists(os.path.join(path, 'lrc_toolbox')):
                    parent_dir = path
                    break

            if parent_dir is None:
                # Try to find relative to this plugin's location using Maya's plugin info
                try:
                    loaded_plugins = cmds.pluginInfo(query=True, listPlugins=True) or []
                    for plugin in loaded_plugins:
                        if 'lrc_toolbox_plugin' in plugin:
                            plugin_path = cmds.pluginInfo(plugin, query=True, path=True)
                            if plugin_path:
                                plugin_dir = os.path.dirname(plugin_path)
                                maya_dir = os.path.dirname(plugin_dir)
                                if os.path.exists(os.path.join(maya_dir, 'lrc_toolbox')):
                                    parent_dir = maya_dir
                                    break
                except:
                    pass

        if parent_dir and parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            print(f"✅ Added to Python path: {parent_dir}")
        
        # Import the main module
        from lrc_toolbox.main import create_dockable_ui
        
        # Create or show existing UI
        if _lrc_toolbox_ui is None:
            print("🚀 Creating new LRC Toolbox v2.0 instance...")
            _lrc_toolbox_ui = create_dockable_ui()
        else:
            print("🔄 Showing existing LRC Toolbox v2.0 instance...")
            # Try to show existing docked window
            dock_name = "lrcToolboxDock"
            if cmds.dockControl(dock_name, exists=True):
                cmds.dockControl(dock_name, edit=True, visible=True)
            else:
                # Recreate if dock was deleted
                _lrc_toolbox_ui = create_dockable_ui()
        
        return _lrc_toolbox_ui
        
    except ImportError as e:
        # Provide detailed diagnostics
        current_paths = [path for path in sys.path if 'swaLRC' in path or 'LRCtoolsbox' in path or 'maya' in path]

        # Try to determine the correct path dynamically
        suggested_path = parent_dir if 'parent_dir' in locals() and parent_dir else '<PLUGIN_DIRECTORY>/maya'

        error_msg = (
            f"❌ Failed to import LRC Toolbox modules: {str(e)}\n\n"
            f"Diagnostics:\n"
            f"• Parent directory: {parent_dir if 'parent_dir' in locals() else 'Not found'}\n"
            f"• Current Python paths: {current_paths}\n"
            f"• Expected structure: lrc_toolbox/main.py\n\n"
            f"Solution:\n"
            f"1. Add to Maya.env (replace with your actual path):\n"
            f"   PYTHONPATH={suggested_path};$PYTHONPATH\n"
            f"2. Restart Maya\n"
            f"3. Reload plugin\n\n"
            f"Or run manually in Script Editor (Python tab):\n"
            f"import sys\n"
            f"sys.path.insert(0, r'{suggested_path}')\n"
            f"from lrc_toolbox.main import create_dockable_ui\n"
            f"ui = create_dockable_ui()"
        )
        om.MGlobal.displayError(error_msg)
        print(error_msg)  # Also print to console
        return None
    except Exception as e:
        import traceback
        error_msg = f"❌ Unexpected error opening LRC Toolbox: {str(e)}\n{traceback.format_exc()}"
        om.MGlobal.displayError(error_msg)
        print(error_msg)  # Also print to console
        return None


def create_menu():
    """Create the LRC Toolbox menu in Maya."""
    try:
        # Check if menu already exists
        if cmds.menu("lrcToolboxMenu", exists=True):
            cmds.deleteUI("lrcToolboxMenu", menu=True)
        
        # Create main menu
        main_menu = cmds.menu(
            "lrcToolboxMenu",
            label="LRC Toolbox",
            parent="MayaWindow",
            tearOff=True
        )
        
        # Add menu items
        cmds.menuItem(
            label="Open Toolbox",
            command="import maya.cmds as cmds; cmds.lrcToolboxOpen()",
            annotation="Open the LRC Toolbox v2.0 Enhanced Template Management System",
            parent=main_menu
        )

        cmds.menuItem(
            label="Save & Settings Tool",
            command="import maya.cmds as cmds; cmds.lrcOpenSaveSettings()",
            annotation="Open Save & Settings tool for shot setup and scene management",
            parent=main_menu
        )

        cmds.menuItem(
            label="Shot Build Tool",
            command="import maya.cmds as cmds; cmds.lrcOpenShotBuild()",
            annotation="Open Shot Build tool for pipeline asset building and management",
            parent=main_menu
        )

        cmds.menuItem(divider=True, parent=main_menu)
        
        cmds.menuItem(
            label="About",
            command=lambda *args: show_about_dialog(),
            annotation="About LRC Toolbox v2.0",
            parent=main_menu
        )
        
        print("✅ LRC Toolbox menu created successfully")
        
    except Exception as e:
        om.MGlobal.displayError(f"❌ Failed to create LRC Toolbox menu: {str(e)}")


def remove_menu():
    """Remove the LRC Toolbox menu from Maya."""
    try:
        if cmds.menu("lrcToolboxMenu", exists=True):
            cmds.deleteUI("lrcToolboxMenu", menu=True)
            print("✅ LRC Toolbox menu removed successfully")
    except Exception as e:
        om.MGlobal.displayError(f"❌ Failed to remove LRC Toolbox menu: {str(e)}")


def show_about_dialog():
    """Show about dialog for the LRC Toolbox."""
    about_text = (
        f"{PLUGIN_NAME}\n"
        f"Version: {PLUGIN_VERSION}\n"
        f"Author: {PLUGIN_AUTHOR}\n\n"
        f"{PLUGIN_DESCRIPTION}\n\n"
        f"Features:\n"
        f"• Enhanced Template Management\n"
        f"• Context-Aware Navigation\n"
        f"• Maya Light Rig Integration\n"
        f"• Render Layer Management\n"
        f"• Pattern-Based Naming\n"
        f"• Regex Tools\n\n"
        f"Usage:\n"
        f"• Menu: LRC Toolbox > Open Toolbox\n"
        f"• Command: lrcToolboxOpen()\n"
        f"• Dockable interface with 5 specialized tabs"
    )
    
    cmds.confirmDialog(
        title=f"About {PLUGIN_NAME}",
        message=about_text,
        button=["OK"],
        defaultButton="OK",
        icon="information"
    )


def initializePlugin(plugin):
    """Initialize the plugin."""
    try:
        # Get plugin function set
        plugin_fn = om.MFnPlugin(plugin, PLUGIN_AUTHOR, PLUGIN_VERSION, "Any")
        
        # Register commands
        plugin_fn.registerCommand(
            LRCToolboxCommand.COMMAND_NAME,
            LRCToolboxCommand.creator
        )

        plugin_fn.registerCommand(
            LRCSaveSettingsCommand.COMMAND_NAME,
            LRCSaveSettingsCommand.creator
        )

        plugin_fn.registerCommand(
            LRCShotBuildCommand.COMMAND_NAME,
            LRCShotBuildCommand.creator
        )
        
        # Create menu (delayed to ensure Maya UI is ready)
        cmds.evalDeferred(create_menu)
        
        print(f"✅ {PLUGIN_NAME} v{PLUGIN_VERSION} loaded successfully")
        print(f"📋 Access via: LRC Toolbox menu or lrcToolboxOpen() command")
        
    except Exception as e:
        om.MGlobal.displayError(f"❌ Failed to initialize {PLUGIN_NAME}: {str(e)}")
        raise


def uninitializePlugin(plugin):
    """Uninitialize the plugin."""
    global _lrc_toolbox_ui
    
    try:
        # Get plugin function set
        plugin_fn = om.MFnPlugin(plugin)
        
        # Clean up UI
        if _lrc_toolbox_ui is not None:
            dock_name = "lrcToolboxDock"
            if cmds.dockControl(dock_name, exists=True):
                cmds.deleteUI(dock_name, control=True)
            _lrc_toolbox_ui = None
        
        # Remove menu
        remove_menu()
        
        # Deregister commands
        plugin_fn.deregisterCommand(LRCToolboxCommand.COMMAND_NAME)
        plugin_fn.deregisterCommand(LRCSaveSettingsCommand.COMMAND_NAME)
        plugin_fn.deregisterCommand(LRCShotBuildCommand.COMMAND_NAME)
        
        print(f"✅ {PLUGIN_NAME} v{PLUGIN_VERSION} unloaded successfully")
        
    except Exception as e:
        om.MGlobal.displayError(f"❌ Failed to uninitialize {PLUGIN_NAME}: {str(e)}")
        raise


# Convenience functions for direct use
def lrc_toolbox_open():
    """Convenience function to open LRC Toolbox (can be called directly)."""
    return open_lrc_toolbox()


def lrc_open_save_settings_tool():
    """Open the Save & Settings tool from mockup directory (same location as plugin)."""
    try:
        # Method 1: Try to get plugin location from Maya's plugin info
        script_path = None
        try:
            # Get list of loaded plugins and their paths
            loaded_plugins = cmds.pluginInfo(query=True, listPlugins=True) or []
            for plugin in loaded_plugins:
                if 'lrc_toolbox_plugin' in plugin:
                    # Get the full path of this plugin
                    plugin_path = cmds.pluginInfo(plugin, query=True, path=True)
                    if plugin_path:
                        plugin_dir = os.path.dirname(plugin_path)
                        maya_dir = os.path.dirname(plugin_dir)  # Go up to maya/
                        script_path = os.path.join(maya_dir, "mockup", "save_and_setting.py")
                        break
        except:
            pass

        # Method 2: Try using inspect module to get current file location
        if not script_path:
            try:
                import inspect
                current_frame = inspect.currentframe()
                if current_frame:
                    plugin_file = inspect.getfile(current_frame)
                    plugin_dir = os.path.dirname(plugin_file)
                    maya_dir = os.path.dirname(plugin_dir)
                    script_path = os.path.join(maya_dir, "mockup", "save_and_setting.py")
            except:
                pass

        # Method 3: Search Maya's sys.path for likely locations
        if not script_path:
            import sys
            for path in sys.path:
                # Look for paths that might contain our plugin
                if 'plugins' in path.lower() or 'maya' in path.lower():
                    # Try going up from plugins to maya, then to mockup
                    if 'plugins' in path.lower():
                        maya_dir = os.path.dirname(path)
                    else:
                        maya_dir = path

                    test_path = os.path.join(maya_dir, "mockup", "save_and_setting.py")
                    if os.path.exists(test_path):
                        script_path = test_path
                        break

        # Verify the script exists
        if not script_path or not os.path.exists(script_path):
            error_msg = "❌ Save & Settings script not found. Please ensure save_and_setting.py is in maya/mockup/ folder relative to the plugin."
            om.MGlobal.displayError(error_msg)
            print(error_msg)
            print("Searched locations:")
            if script_path:
                print(f"  - {script_path}")
            return None

        # Execute the script using Maya's evalDeferred for proper context
        print(f"🚀 Opening Save & Settings tool from: {script_path}")

        # Use Maya's evalDeferred to ensure proper execution context with UTF-8 encoding
        exec_command = f'exec(open(r"{script_path}", encoding="utf-8").read())'
        cmds.evalDeferred(exec_command)

        om.MGlobal.displayInfo("✅ Save & Settings tool opened")
        return True

    except Exception as e:
        error_msg = f"❌ Failed to open Save & Settings tool: {str(e)}"
        om.MGlobal.displayError(error_msg)
        print(error_msg)
        return None


def lrc_open_shot_build_tool():
    """Open the Shot Build tool from mockup directory."""
    try:
        # Method 1: Try to get plugin location from Maya's plugin info
        script_path = None
        try:
            # Get list of loaded plugins and their paths
            loaded_plugins = cmds.pluginInfo(query=True, listPlugins=True) or []

            for plugin in loaded_plugins:
                if "lrc_toolbox_plugin" in plugin.lower():
                    plugin_path = cmds.pluginInfo(plugin, query=True, path=True)
                    if plugin_path:
                        # Navigate to the mockup directory
                        plugin_dir = os.path.dirname(plugin_path)
                        mockup_dir = os.path.join(plugin_dir, "..", "mockup")
                        script_path = os.path.join(mockup_dir, "igl_shot_build.py")
                        script_path = os.path.normpath(script_path)
                        break
        except Exception:
            pass

        # Method 2: Try relative to this plugin file
        if not script_path or not os.path.exists(script_path):
            try:
                current_file = os.path.abspath(__file__)
                plugin_dir = os.path.dirname(current_file)
                mockup_dir = os.path.join(plugin_dir, "..", "mockup")
                script_path = os.path.join(mockup_dir, "igl_shot_build.py")
                script_path = os.path.normpath(script_path)
            except Exception:
                pass

        # Method 3: Try common Maya script paths
        if not script_path or not os.path.exists(script_path):
            try:
                maya_app_dir = os.environ.get('MAYA_APP_DIR', '')
                if maya_app_dir:
                    script_path = os.path.join(maya_app_dir, "scripts", "lrc_toolbox", "maya", "mockup", "igl_shot_build.py")
                    script_path = os.path.normpath(script_path)
            except Exception:
                pass

        # Verify the script exists
        if not script_path or not os.path.exists(script_path):
            error_msg = "❌ Shot Build tool script not found. Searched locations:"
            print(error_msg)
            if script_path:
                print(f"  - {script_path}")
            return None

        # Execute the script using Maya's evalDeferred for proper context
        print(f"🚀 Opening Shot Build tool from: {script_path}")

        # Use Maya's evalDeferred to ensure proper execution context with UTF-8 encoding
        exec_command = f'exec(open(r"{script_path}", encoding="utf-8").read())'
        cmds.evalDeferred(exec_command)

        om.MGlobal.displayInfo("✅ Shot Build tool opened")
        return True

    except Exception as e:
        error_msg = f"❌ Failed to open Shot Build tool: {str(e)}"
        om.MGlobal.displayError(error_msg)
        print(error_msg)
        return None


if __name__ == "__main__":
    # For testing outside of Maya
    print(f"{PLUGIN_NAME} v{PLUGIN_VERSION}")
    print(f"This is a Maya plugin file. Load it through Maya's Plugin Manager.")
