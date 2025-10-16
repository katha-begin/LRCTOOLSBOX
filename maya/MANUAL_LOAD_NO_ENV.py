"""
LRC Toolbox - Manual Load (No Maya.env Required)

This script adds paths to Maya session and loads the toolbox.
No need to edit Maya.env or restart Maya!

Usage:
    Copy this entire file into Maya Script Editor (Python tab) and run.
"""

import sys
import os

# ============================================================================
# CONFIGURATION - Change this to your path
# ============================================================================

TOOLBOX_PATH = r"V:\SWA\tools\git\swaLRC\maya"

# ============================================================================
# MANUAL LOAD - Adds paths and loads UI
# ============================================================================

def manual_load_lrc_toolbox():
    """
    Manually load LRC Toolbox by adding paths to current Maya session.
    No Maya.env editing required!
    """
    
    print("=" * 70)
    print("LRC TOOLBOX - MANUAL LOAD (No Maya.env)")
    print("=" * 70)
    
    # Step 1: Verify path exists
    print(f"\n[1/4] Checking path: {TOOLBOX_PATH}")
    if not os.path.exists(TOOLBOX_PATH):
        print(f"    ❌ ERROR: Path not found!")
        print(f"    Please update TOOLBOX_PATH in this script")
        return None
    print(f"    ✅ Path exists")
    
    # Step 2: Add to PYTHONPATH (sys.path)
    print(f"\n[2/4] Adding to PYTHONPATH...")
    if TOOLBOX_PATH not in sys.path:
        sys.path.insert(0, TOOLBOX_PATH)
        print(f"    ✅ Added: {TOOLBOX_PATH}")
    else:
        print(f"    ✅ Already in sys.path")
    
    # Step 3: Add to MAYA_PLUG_IN_PATH (optional, for plugin loading)
    print(f"\n[3/4] Adding to MAYA_PLUG_IN_PATH...")
    try:
        import maya.cmds as cmds
        plugin_path = os.path.join(TOOLBOX_PATH, "plugins")
        
        # Get current plugin paths
        current_paths = os.environ.get('MAYA_PLUG_IN_PATH', '').split(';')
        
        if plugin_path not in current_paths:
            # Add to environment variable for this session
            if os.environ.get('MAYA_PLUG_IN_PATH'):
                os.environ['MAYA_PLUG_IN_PATH'] = f"{plugin_path};{os.environ['MAYA_PLUG_IN_PATH']}"
            else:
                os.environ['MAYA_PLUG_IN_PATH'] = plugin_path
            print(f"    ✅ Added: {plugin_path}")
        else:
            print(f"    ✅ Already in MAYA_PLUG_IN_PATH")
    except Exception as e:
        print(f"    ⚠️  Warning: Could not add to MAYA_PLUG_IN_PATH: {e}")
        print(f"    (This is optional, UI will still work)")
    
    # Step 4: Import and create UI
    print(f"\n[4/4] Loading LRC Toolbox UI...")
    try:
        from lrc_toolbox.main import create_dockable_ui
        print(f"    ✅ Import successful")
        
        ui = create_dockable_ui()
        print(f"    ✅ UI created")
        
        print("\n" + "=" * 70)
        print("✅ LRC TOOLBOX LOADED SUCCESSFULLY!")
        print("=" * 70)
        print("\nThe toolbox should now be docked on the right side of Maya.")
        print("These paths are active for this Maya session only.")
        print("To make permanent, add to Maya.env and restart Maya.")
        print("=" * 70)
        
        return ui
        
    except Exception as e:
        print(f"    ❌ ERROR: Failed to load UI")
        print(f"    Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n" + "=" * 70)
        print("❌ LOAD FAILED")
        print("=" * 70)
        return None

# ============================================================================
# RUN THE LOADER
# ============================================================================

# Execute the manual load
ui = manual_load_lrc_toolbox()

