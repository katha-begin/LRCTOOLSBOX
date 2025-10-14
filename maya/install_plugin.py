"""
LRC Toolbox v2.0 Plugin Installation Script

This script helps install the LRC Toolbox v2.0 as a Maya plugin.
It copies the necessary files to Maya's plugins directory and provides
instructions for loading the plugin.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Optional, List

try:
    import maya.cmds as cmds
    import maya.mel as mel
    MAYA_AVAILABLE = True
    print("✅ Maya environment detected")
except ImportError:
    MAYA_AVAILABLE = False
    print("ℹ️  Running outside Maya - installation only")


def get_maya_plugins_directory() -> Optional[Path]:
    """
    Get the Maya plugins directory for the current user.
    
    Returns:
        Path to Maya plugins directory or None if not found
    """
    if MAYA_AVAILABLE:
        # Get from Maya preferences
        try:
            plugins_paths = cmds.pluginInfo(query=True, listPluginsPath=True)
            if plugins_paths:
                # Use the first user plugins directory
                for path in plugins_paths:
                    if "plug-ins" in path and os.access(path, os.W_OK):
                        return Path(path)
        except:
            pass
    
    # Fallback to standard Maya directories
    maya_versions = ["2024", "2023", "2022", "2021", "2020"]
    
    if sys.platform == "win32":
        # Windows
        documents = Path.home() / "Documents"
        for version in maya_versions:
            plugins_dir = documents / f"maya/{version}/plug-ins"
            if plugins_dir.exists():
                return plugins_dir
        
        # Create for latest version if none exist
        latest_plugins_dir = documents / f"maya/{maya_versions[0]}/plug-ins"
        latest_plugins_dir.mkdir(parents=True, exist_ok=True)
        return latest_plugins_dir
        
    elif sys.platform == "darwin":
        # macOS
        maya_dir = Path.home() / "Library/Preferences/Autodesk/maya"
        for version in maya_versions:
            plugins_dir = maya_dir / f"{version}/plug-ins"
            if plugins_dir.exists():
                return plugins_dir
        
        # Create for latest version if none exist
        latest_plugins_dir = maya_dir / f"{maya_versions[0]}/plug-ins"
        latest_plugins_dir.mkdir(parents=True, exist_ok=True)
        return latest_plugins_dir
        
    else:
        # Linux
        maya_dir = Path.home() / "maya"
        for version in maya_versions:
            plugins_dir = maya_dir / f"{version}/plug-ins"
            if plugins_dir.exists():
                return plugins_dir
        
        # Create for latest version if none exist
        latest_plugins_dir = maya_dir / f"{maya_versions[0]}/plug-ins"
        latest_plugins_dir.mkdir(parents=True, exist_ok=True)
        return latest_plugins_dir
    
    return None


def copy_plugin_files(source_dir: Path, target_dir: Path) -> bool:
    """
    Copy LRC Toolbox files to Maya plugins directory.
    
    Args:
        source_dir: Source directory containing LRC Toolbox
        target_dir: Target Maya plugins directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create target directory structure
        lrc_target = target_dir / "lrc_toolbox"
        lrc_target.mkdir(exist_ok=True)
        
        # Copy main plugin file
        plugin_file = source_dir / "lrc_toolbox_plugin.py"
        if plugin_file.exists():
            shutil.copy2(plugin_file, target_dir / "lrc_toolbox_plugin.py")
            print(f"✅ Copied plugin file: {plugin_file.name}")
        else:
            print(f"❌ Plugin file not found: {plugin_file}")
            return False
        
        # Copy LRC Toolbox package
        lrc_source = source_dir / "lrc_toolbox"
        if lrc_source.exists():
            # Remove existing installation
            if lrc_target.exists():
                shutil.rmtree(lrc_target)
            
            # Copy entire package
            shutil.copytree(lrc_source, lrc_target)
            print(f"✅ Copied LRC Toolbox package to: {lrc_target}")
        else:
            print(f"❌ LRC Toolbox package not found: {lrc_source}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error copying files: {e}")
        return False


def install_plugin() -> bool:
    """
    Install the LRC Toolbox plugin.
    
    Returns:
        True if installation successful, False otherwise
    """
    print("🚀 Installing LRC Toolbox v2.0 Plugin...")
    
    # Get source directory (where this script is located)
    source_dir = Path(__file__).parent
    print(f"📁 Source directory: {source_dir}")
    
    # Get Maya plugins directory
    plugins_dir = get_maya_plugins_directory()
    if not plugins_dir:
        print("❌ Could not find Maya plugins directory")
        return False
    
    print(f"📁 Target directory: {plugins_dir}")
    
    # Copy files
    if not copy_plugin_files(source_dir, plugins_dir):
        return False
    
    print("✅ LRC Toolbox v2.0 plugin installed successfully!")
    print("\n📋 Next Steps:")
    print("1. Open Maya")
    print("2. Go to Windows > Settings/Preferences > Plug-in Manager")
    print("3. Find 'lrc_toolbox_plugin.py' in the list")
    print("4. Check 'Loaded' to load the plugin")
    print("5. Check 'Auto load' to load automatically on Maya startup")
    print("6. Access via: LRC Toolbox menu or lrcToolboxOpen() command")
    
    return True


def uninstall_plugin() -> bool:
    """
    Uninstall the LRC Toolbox plugin.
    
    Returns:
        True if uninstallation successful, False otherwise
    """
    print("🗑️  Uninstalling LRC Toolbox v2.0 Plugin...")
    
    # Get Maya plugins directory
    plugins_dir = get_maya_plugins_directory()
    if not plugins_dir:
        print("❌ Could not find Maya plugins directory")
        return False
    
    try:
        # Remove plugin file
        plugin_file = plugins_dir / "lrc_toolbox_plugin.py"
        if plugin_file.exists():
            plugin_file.unlink()
            print(f"✅ Removed plugin file: {plugin_file}")
        
        # Remove LRC Toolbox package
        lrc_dir = plugins_dir / "lrc_toolbox"
        if lrc_dir.exists():
            shutil.rmtree(lrc_dir)
            print(f"✅ Removed LRC Toolbox package: {lrc_dir}")
        
        print("✅ LRC Toolbox v2.0 plugin uninstalled successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during uninstallation: {e}")
        return False


def main():
    """Main installation function."""
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        success = uninstall_plugin()
    else:
        success = install_plugin()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
