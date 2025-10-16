"""
LRC TOOLBOX - QUICK LOAD SCRIPT

Copy-paste this entire file into Maya Script Editor (Python tab) and run.
Works from any repository name or path.
"""

# ============================================================================
# CONFIGURATION - CHANGE THIS TO YOUR PATH
# ============================================================================

TOOLBOX_PATH = r"V:\SWA\tools\git\swaLRC\maya"

# ============================================================================
# LOAD SCRIPT - DO NOT MODIFY BELOW THIS LINE
# ============================================================================

import sys
import os

def quick_load():
    """Quick load LRC Toolbox"""
    
    # Verify path exists
    if not os.path.exists(TOOLBOX_PATH):
        print(f"ERROR: Path not found: {TOOLBOX_PATH}")
        print("Please update TOOLBOX_PATH in this script")
        return None
    
    # Verify lrc_toolbox package exists
    lrc_path = os.path.join(TOOLBOX_PATH, "lrc_toolbox")
    if not os.path.exists(lrc_path):
        print(f"ERROR: lrc_toolbox package not found at: {lrc_path}")
        return None
    
    # Add to Python path
    if TOOLBOX_PATH not in sys.path:
        sys.path.insert(0, TOOLBOX_PATH)
        print(f"Added to path: {TOOLBOX_PATH}")
    
    # Import and create UI
    try:
        from lrc_toolbox.main import create_dockable_ui
        ui = create_dockable_ui()
        print("✅ LRC Toolbox loaded successfully!")
        return ui
    except Exception as e:
        print(f"ERROR: Failed to load: {e}")
        import traceback
        traceback.print_exc()
        return None

# Run
ui = quick_load()

