# -*- coding: utf-8 -*-
"""
Unicode Error Fix Script for LRC Toolbox

This script fixes the UnicodeDecodeError that occurs when loading
Python files with emoji/Unicode characters on Windows machines.

Error: UnicodeDecodeError: 'charmap' codec can't decode byte 0x81

Run this in Maya Script Editor to fix the issue.
"""

from __future__ import print_function
import sys
import os
import shutil


def clear_python_cache(path):
    """
    Clear all .pyc files and __pycache__ directories.
    
    Args:
        path: Root path to clean
    """
    print("\n" + "=" * 60)
    print("CLEARING PYTHON CACHE")
    print("=" * 60)
    
    deleted_pyc = 0
    deleted_pycache = 0
    
    try:
        for root, dirs, files in os.walk(path):
            # Delete .pyc files
            for file in files:
                if file.endswith('.pyc'):
                    pyc_path = os.path.join(root, file)
                    try:
                        os.remove(pyc_path)
                        deleted_pyc += 1
                        print("Deleted: {0}".format(pyc_path))
                    except Exception as e:
                        print("Failed to delete {0}: {1}".format(pyc_path, e))
            
            # Delete __pycache__ directories
            if '__pycache__' in dirs:
                pycache_path = os.path.join(root, '__pycache__')
                try:
                    shutil.rmtree(pycache_path)
                    deleted_pycache += 1
                    print("Deleted: {0}".format(pycache_path))
                except Exception as e:
                    print("Failed to delete {0}: {1}".format(pycache_path, e))
        
        print("\n" + "=" * 60)
        print("CACHE CLEANUP SUMMARY")
        print("=" * 60)
        print("Deleted {0} .pyc files".format(deleted_pyc))
        print("Deleted {0} __pycache__ directories".format(deleted_pycache))
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print("ERROR: Cache cleanup failed: {0}".format(e))
        return False


def unload_modules(module_prefix):
    """
    Unload all modules with given prefix from sys.modules.
    
    Args:
        module_prefix: Module name prefix (e.g., 'lrc_toolbox')
    """
    print("\n" + "=" * 60)
    print("UNLOADING MODULES")
    print("=" * 60)
    
    modules_to_remove = [key for key in sys.modules.keys() if module_prefix in key]
    
    if not modules_to_remove:
        print("No modules with prefix '{0}' found in memory".format(module_prefix))
        return
    
    print("Found {0} modules to unload:".format(len(modules_to_remove)))
    for module in modules_to_remove:
        try:
            del sys.modules[module]
            print("Unloaded: {0}".format(module))
        except Exception as e:
            print("Failed to unload {0}: {1}".format(module, e))
    
    print("=" * 60)


def check_file_encoding(filepath):
    """
    Check if file has UTF-8 encoding declaration.
    
    Args:
        filepath: Path to Python file
        
    Returns:
        True if has encoding declaration, False otherwise
    """
    try:
        with open(filepath, 'rb') as f:
            first_line = f.readline()
            second_line = f.readline()
            
            # Check first two lines for encoding declaration
            for line in [first_line, second_line]:
                if b'coding' in line or b'encoding' in line:
                    if b'utf-8' in line or b'utf8' in line:
                        return True
        return False
    except Exception as e:
        print("Error checking file: {0}".format(e))
        return False


def diagnose_toolbox(toolbox_path):
    """
    Diagnose LRC Toolbox installation and identify issues.
    
    Args:
        toolbox_path: Path to lrc_toolbox directory
    """
    print("\n" + "=" * 60)
    print("LRC TOOLBOX DIAGNOSTIC")
    print("=" * 60)
    
    # Check if path exists
    print("\nPath Check:")
    print("  Path: {0}".format(toolbox_path))
    print("  Exists: {0}".format(os.path.exists(toolbox_path)))
    print("  Readable: {0}".format(os.access(toolbox_path, os.R_OK)))
    
    # Check Python version
    print("\nPython Version:")
    print("  Version: {0}".format(sys.version))
    print("  Default Encoding: {0}".format(sys.getdefaultencoding()))
    
    # Check for cached modules
    print("\nLoaded Modules:")
    lrc_modules = [key for key in sys.modules.keys() if 'lrc_toolbox' in key]
    print("  LRC modules in memory: {0}".format(len(lrc_modules)))
    if lrc_modules:
        for mod in lrc_modules[:5]:
            print("    - {0}".format(mod))
        if len(lrc_modules) > 5:
            print("    ... and {0} more".format(len(lrc_modules) - 5))
    
    # Check for .pyc files
    print("\nCache Files:")
    pyc_count = 0
    pycache_count = 0
    for root, dirs, files in os.walk(toolbox_path):
        pyc_count += sum(1 for f in files if f.endswith('.pyc'))
        pycache_count += sum(1 for d in dirs if d == '__pycache__')
    print("  .pyc files: {0}".format(pyc_count))
    print("  __pycache__ dirs: {0}".format(pycache_count))
    
    # Check main files for UTF-8 encoding
    print("\nEncoding Check:")
    main_files = [
        os.path.join(toolbox_path, 'main.py'),
        os.path.join(toolbox_path, 'ui', 'main_window.py'),
    ]
    for filepath in main_files:
        if os.path.exists(filepath):
            has_encoding = check_file_encoding(filepath)
            status = "OK" if has_encoding else "MISSING"
            print("  {0}: {1}".format(os.path.basename(filepath), status))
    
    print("=" * 60)


def fix_unicode_error(toolbox_path):
    """
    Complete fix for Unicode error.
    
    Args:
        toolbox_path: Path to lrc_toolbox directory
    """
    print("\n" + "=" * 60)
    print("UNICODE ERROR FIX")
    print("=" * 60)
    print("\nThis will:")
    print("1. Clear all Python cache files (.pyc, __pycache__)")
    print("2. Unload all lrc_toolbox modules from memory")
    print("3. Diagnose the installation")
    print("\nPath: {0}".format(toolbox_path))
    print("=" * 60)
    
    # Step 1: Clear cache
    print("\nStep 1: Clearing cache...")
    clear_python_cache(toolbox_path)
    
    # Step 2: Unload modules
    print("\nStep 2: Unloading modules...")
    unload_modules('lrc_toolbox')
    
    # Step 3: Diagnose
    print("\nStep 3: Running diagnostics...")
    diagnose_toolbox(toolbox_path)
    
    # Final instructions
    print("\n" + "=" * 60)
    print("FIX COMPLETE!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. RESTART MAYA (important!)")
    print("2. After restart, load the toolbox again")
    print("3. If error persists, check that files have UTF-8 encoding")
    print("\nTo load toolbox after restart:")
    print("  import sys")
    print("  sys.path.insert(0, r'{0}')".format(os.path.dirname(toolbox_path)))
    print("  from lrc_toolbox.main import create_dockable_ui")
    print("  ui = create_dockable_ui()")
    print("=" * 60)


# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================

def show_usage():
    """Show usage instructions."""
    print("\n" + "=" * 60)
    print("UNICODE ERROR FIX - USAGE")
    print("=" * 60)
    print("\nTo fix Unicode error, run ONE of these commands:")
    print("\n1. For T: drive installation:")
    print("   fix_unicode_error(r'T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX/maya/lrc_toolbox')")
    print("\n2. For V: drive installation:")
    print("   fix_unicode_error(r'V:/SWA/tools/git/swaLRC/maya/lrc_toolbox')")
    print("\n3. For E: drive installation:")
    print("   fix_unicode_error(r'E:/dev/LRCtoolsbox/LRCtoolsbox/maya/lrc_toolbox')")
    print("\n4. For custom path:")
    print("   fix_unicode_error(r'YOUR_PATH_HERE/maya/lrc_toolbox')")
    print("\nOr run diagnostics only:")
    print("   diagnose_toolbox(r'YOUR_PATH_HERE/maya/lrc_toolbox')")
    print("\nOr clear cache only:")
    print("   clear_python_cache(r'YOUR_PATH_HERE/maya/lrc_toolbox')")
    print("=" * 60)


# Show usage when script is loaded
show_usage()

