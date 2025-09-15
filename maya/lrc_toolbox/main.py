"""
LRC Toolbox Main Entry Point

This module provides the main entry point for the LRC Toolbox application.
It handles Maya integration, UI creation, and application lifecycle.
"""

import sys
import os
from typing import Optional

# Add the maya directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
maya_dir = os.path.dirname(current_dir)
if maya_dir not in sys.path:
    sys.path.insert(0, maya_dir)

try:
    # Maya imports
    import maya.cmds as cmds
    import maya.OpenMayaUI as omui
    from PySide2 import QtWidgets, QtCore
    from shiboken2 import wrapInstance
    MAYA_AVAILABLE = True
except ImportError:
    # Fallback for development/testing without Maya
    try:
        from PySide2 import QtWidgets, QtCore
    except ImportError:
        from PySide6 import QtWidgets, QtCore
    MAYA_AVAILABLE = False

from lrc_toolbox.ui.main_window import RenderSetupUI


def get_maya_main_window() -> Optional[QtWidgets.QWidget]:
    """
    Get Maya's main window as a Qt widget.
    
    Returns:
        Maya main window widget or None if not available
    """
    if not MAYA_AVAILABLE:
        return None
        
    try:
        main_window_ptr = omui.MQtUtil.mainWindow()
        if main_window_ptr:
            return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    except Exception as e:
        print(f"Warning: Could not get Maya main window: {e}")
    
    return None


def create_dockable_ui() -> Optional[QtWidgets.QWidget]:
    """
    Create and dock the LRC Toolbox UI in Maya.

    Returns:
        UI widget instance or None if creation failed

    Note: This is a placeholder implementation until RenderSetupUI is created.
    """
    if not MAYA_AVAILABLE:
        print("Maya not available - creating standalone window")
        return create_standalone_ui()

    print("🚧 Placeholder: create_dockable_ui() - RenderSetupUI not implemented yet")
    print("This will create a dockable Maya UI when the UI components are implemented")

    # TODO: Implement when RenderSetupUI is available
    # Clean up existing instances
    # dock_name = "lrcToolboxDock"
    # if cmds.dockControl(dock_name, exists=True):
    #     cmds.deleteUI(dock_name, control=True)

    return None


def create_standalone_ui() -> Optional[QtWidgets.QWidget]:
    """
    Create a standalone LRC Toolbox window.

    Returns:
        UI widget instance or None if creation failed

    Note: This is a placeholder implementation until RenderSetupUI is created.
    """
    print("🚧 Placeholder: create_standalone_ui() - RenderSetupUI not implemented yet")
    print("This will create a standalone UI window when the UI components are implemented")

    # TODO: Implement when RenderSetupUI is available
    # app = QtWidgets.QApplication.instance()
    # if app is None:
    #     app = QtWidgets.QApplication(sys.argv)

    # parent = get_maya_main_window()
    # ui = RenderSetupUI(parent=parent)
    # ui.show()

    return None


def main():
    """
    Main entry point for the LRC Toolbox application.

    Note: This is a placeholder implementation until UI components are created.
    """
    print("🚀 Starting LRC Toolbox v2.0...")
    print("📁 Project structure initialized and ready for development")

    if MAYA_AVAILABLE:
        print("🎯 Maya environment detected")
        ui = create_dockable_ui()
    else:
        print("🖥️  Standalone mode")
        ui = create_standalone_ui()

        # Run the application if not in Maya (when UI is implemented)
        # app = QtWidgets.QApplication.instance()
        # if app:
        #     sys.exit(app.exec_())

    print("✅ LRC Toolbox initialization complete")
    print("📋 Ready for UI-first development phase")
    return ui


if __name__ == "__main__":
    main()
