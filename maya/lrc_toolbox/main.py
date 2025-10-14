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
    """
    if not MAYA_AVAILABLE:
        print("Maya not available - creating standalone window")
        return create_standalone_ui()

    try:
        # Clean up existing instances
        dock_name = "lrcToolboxDock"
        if cmds.dockControl(dock_name, exists=True):
            cmds.deleteUI(dock_name, control=True)

        # Create the UI with Maya main window as parent
        parent = get_maya_main_window()
        ui = RenderSetupUI(parent=parent)

        # Create dockable window
        dock_control = cmds.dockControl(
            dock_name,
            label="LRC Toolbox v2.0",
            area="right",
            content=ui.objectName(),
            allowedArea=["right", "left"],
            sizeable=True,
            width=500
        )

        print("SUCCESS: Dockable UI created successfully")
        return ui

    except Exception as e:
        print(f"ERROR: Error creating dockable UI: {e}")
        return None


def create_standalone_ui() -> Optional[QtWidgets.QWidget]:
    """
    Create a standalone LRC Toolbox window.

    Returns:
        UI widget instance or None if creation failed
    """
    try:
        # Ensure QApplication exists
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)

        # Create the UI (no parent for standalone)
        ui = RenderSetupUI(parent=None)
        ui.show()

        print("SUCCESS: Standalone UI created successfully")
        return ui

    except Exception as e:
        print(f"ERROR: Error creating standalone UI: {e}")
        return None


def main():
    """
    Main entry point for the LRC Toolbox application.
    """
    print("STARTING: LRC Toolbox v2.0...")
    print("INFO: Enhanced Template Management System")

    if MAYA_AVAILABLE:
        print("INFO: Maya environment detected - creating dockable UI")
        ui = create_dockable_ui()
    else:
        print("INFO: Standalone mode - creating standalone window")
        ui = create_standalone_ui()

        # Run the application if not in Maya
        if ui is not None:
            app = QtWidgets.QApplication.instance()
            if app:
                print("INFO: Starting application event loop...")
                sys.exit(app.exec_())

    if ui is not None:
        print("SUCCESS: LRC Toolbox v2.0 initialized successfully")
        print("INFO: Tab-based interface ready for use")
    else:
        print("ERROR: Failed to initialize LRC Toolbox")

    return ui


if __name__ == "__main__":
    main()
