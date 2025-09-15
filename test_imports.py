#!/usr/bin/env python3
"""
Test script to verify import paths work correctly after directory reorganization.
"""

import sys
import os

# Add maya directory to Python path
maya_dir = os.path.join(os.path.dirname(__file__), "maya")
if maya_dir not in sys.path:
    sys.path.insert(0, maya_dir)

def test_imports():
    """Test that all imports work correctly."""
    try:
        # Test main package import
        import lrc_toolbox
        print(f"✅ lrc_toolbox imported successfully from: {lrc_toolbox.__file__}")

        # Test submodule imports (empty but should work)
        import lrc_toolbox.core
        import lrc_toolbox.utils
        import lrc_toolbox.ui
        import lrc_toolbox.config
        print("✅ Submodules imported successfully")

        # Test config imports (these actually exist)
        from lrc_toolbox.config import Settings, DEFAULT_SETTINGS
        print("✅ Config modules imported successfully")

        # Test main entry point (this exists)
        from lrc_toolbox.main import create_dockable_ui, create_standalone_ui
        print("✅ Main entry point imported successfully")

        print("\n🎉 All imports successful! Directory structure is working correctly.")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing LRC Toolbox imports after directory reorganization...")
    print(f"Maya directory: {maya_dir}")
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
    print()
    
    success = test_imports()
    sys.exit(0 if success else 1)
