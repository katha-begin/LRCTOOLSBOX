"""
LRC Toolbox Loader Script

This script loads the LRC Toolbox plugin from any path.
Works regardless of repository name or directory structure.

Usage in Maya Script Editor (Python tab):
    execfile(r"V:\SWA\tools\git\swaLRC\maya\load_lrc_toolbox.py")

Or copy-paste this entire file into Maya Script Editor and run.
"""

import sys
import os
import maya.cmds as cmds


def load_lrc_toolbox(toolbox_path=None):
    """
    Load LRC Toolbox from specified path.
    
    Args:
        toolbox_path: Path to the maya directory containing lrc_toolbox package.
                     If None, uses the directory where this script is located.
    
    Returns:
        UI widget instance or None if failed
    """
    print("=" * 70)
    print("LRC TOOLBOX LOADER")
    print("=" * 70)
    
    # Step 1: Determine toolbox path
    if toolbox_path is None:
        # Auto-detect from script location
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            toolbox_path = script_dir
            print(f"[1/5] Auto-detected path: {toolbox_path}")
        except NameError:
            # __file__ not available (running in Script Editor)
            print("[1/5] ERROR: Cannot auto-detect path when running in Script Editor")
            print("      Please specify toolbox_path parameter")
            return None
    else:
        print(f"[1/5] Using specified path: {toolbox_path}")
    
    # Step 2: Verify path exists
    if not os.path.exists(toolbox_path):
        print(f"[2/5] ERROR: Path does not exist: {toolbox_path}")
        return None
    print(f"[2/5] Path verified: {toolbox_path}")
    
    # Step 3: Verify lrc_toolbox package exists
    lrc_toolbox_dir = os.path.join(toolbox_path, "lrc_toolbox")
    if not os.path.exists(lrc_toolbox_dir):
        print(f"[3/5] ERROR: lrc_toolbox package not found at: {lrc_toolbox_dir}")
        print("      Expected structure: <path>/maya/lrc_toolbox/")
        return None
    
    main_py = os.path.join(lrc_toolbox_dir, "main.py")
    if not os.path.exists(main_py):
        print(f"[3/5] ERROR: main.py not found at: {main_py}")
        return None
    print(f"[3/5] Package verified: {lrc_toolbox_dir}")
    
    # Step 4: Add to Python path
    if toolbox_path not in sys.path:
        sys.path.insert(0, toolbox_path)
        print(f"[4/5] Added to sys.path: {toolbox_path}")
    else:
        print(f"[4/5] Already in sys.path: {toolbox_path}")
    
    # Step 5: Import and create UI
    try:
        print("[5/5] Importing lrc_toolbox.main...")
        from lrc_toolbox.main import create_dockable_ui
        
        print("[5/5] Creating UI...")
        ui = create_dockable_ui()
        
        print("=" * 70)
        print("✅ LRC TOOLBOX LOADED SUCCESSFULLY!")
        print("=" * 70)
        return ui
        
    except ImportError as e:
        print(f"[5/5] ERROR: Failed to import lrc_toolbox: {e}")
        print("\nPython paths:")
        for p in sys.path:
            if "swaLRC" in p or "LRCtoolsbox" in p or "maya" in p:
                print(f"  - {p}")
        return None
    except Exception as e:
        print(f"[5/5] ERROR: Failed to create UI: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_lrc_toolbox_from_path(path):
    """
    Convenience function to load from specific path.
    
    Args:
        path: Full path to maya directory
    
    Returns:
        UI widget instance or None if failed
    
    Example:
        load_lrc_toolbox_from_path(r"V:\SWA\tools\git\swaLRC\maya")
    """
    return load_lrc_toolbox(toolbox_path=path)


# ============================================================================
# QUICK LOAD FUNCTIONS FOR COMMON PATHS
# ============================================================================

def load_from_production():
    """Load from production path: V:\SWA\tools\git\swaLRC\maya"""
    return load_lrc_toolbox_from_path(r"V:\SWA\tools\git\swaLRC\maya")


def load_from_dev():
    """Load from development path: E:\dev\LRCtoolsbox\LRCtoolsbox\maya"""
    return load_lrc_toolbox_from_path(r"E:\dev\LRCtoolsbox\LRCtoolsbox\maya")


# ============================================================================
# AUTO-LOAD WHEN SCRIPT IS EXECUTED
# ============================================================================

if __name__ == "__main__":
    # When script is executed directly, try to load from production path
    print("\n🚀 Auto-loading from production path...")
    ui = load_from_production()
    
    if ui is None:
        print("\n⚠️  Production path failed, trying development path...")
        ui = load_from_dev()
    
    if ui is None:
        print("\n" + "=" * 70)
        print("❌ FAILED TO LOAD LRC TOOLBOX")
        print("=" * 70)
        print("\nManual load instructions:")
        print("1. Find the correct path to your maya directory")
        print("2. Run this command in Maya Script Editor (Python tab):")
        print("")
        print("   import sys")
        print("   sys.path.insert(0, r'<YOUR_PATH>\\maya')")
        print("   from lrc_toolbox.main import create_dockable_ui")
        print("   ui = create_dockable_ui()")
        print("")
        print("Replace <YOUR_PATH> with your actual path")
        print("=" * 70)

