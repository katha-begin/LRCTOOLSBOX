"""
LRC Toolbox Main Entry Point

This module provides the main entry point for the LRC Toolbox application.
It handles Maya integration, UI creation, and application lifecycle.
"""

import sys
import os
from typing import Optional

# Add the src directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

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


def create_dockable_ui() -> Optional[RenderSetupUI]:
    """
    Create and dock the LRC Toolbox UI in Maya.
    
    Returns:
        RenderSetupUI instance or None if creation failed
    """
    if not MAYA_AVAILABLE:
        print("Maya not available - creating standalone window")
        return create_standalone_ui()
    
    # Clean up existing instances
    dock_name = "lrcToolboxDock"
    if cmds.dockControl(dock_name, exists=True):
        cmds.deleteUI(dock_name, control=True)
    
    try:
        # Create the UI
        parent = get_maya_main_window()
        ui = RenderSetupUI(parent=parent)
        
        # Create dockable control
        dock_control = cmds.dockControl(
            dock_name,
            label="LRC Toolbox v2.0",
            area="right",
            content=ui.objectName(),
            allowedArea=["right", "left"],
            sizeable=True,
            width=700,
            height=900
        )
        
        print(f"LRC Toolbox docked successfully: {dock_control}")
        return ui
        
    except Exception as e:
        print(f"Error creating dockable UI: {e}")
        print("Falling back to standalone window...")
        return create_standalone_ui()


def create_standalone_ui() -> RenderSetupUI:
    """
    Create a standalone LRC Toolbox window.
    
    Returns:
        RenderSetupUI instance
    """
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    
    parent = get_maya_main_window()
    ui = RenderSetupUI(parent=parent)
    ui.show()
    
    print("LRC Toolbox standalone window created")
    return ui


def main():
    """
    Main entry point for the LRC Toolbox application.
    """
    print("Starting LRC Toolbox v2.0...")
    
    if MAYA_AVAILABLE:
        ui = create_dockable_ui()
    else:
        ui = create_standalone_ui()
        
        # Run the application if not in Maya
        app = QtWidgets.QApplication.instance()
        if app:
            sys.exit(app.exec_())
    
    return ui


if __name__ == "__main__":
    main()
