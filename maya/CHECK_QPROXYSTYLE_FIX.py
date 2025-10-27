#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QProxyStyle Error Diagnostic Script

This script checks if the QProxyStyle fix is present in your installation.

Run this in Maya Script Editor to diagnose the issue.
"""

from __future__ import print_function
import os
import sys


def check_qproxystyle_fix(toolbox_path):
    """
    Check if main_window.py has the QProxyStyle fix.
    
    Args:
        toolbox_path: Path to lrc_toolbox directory
    """
    print("\n" + "=" * 60)
    print("QPROXYSTYLE FIX DIAGNOSTIC")
    print("=" * 60)
    
    main_window_path = os.path.join(toolbox_path, "ui", "main_window.py")
    
    print("\nChecking file: {0}".format(main_window_path))
    print("File exists: {0}".format(os.path.exists(main_window_path)))
    
    if not os.path.exists(main_window_path):
        print("\n❌ ERROR: main_window.py not found!")
        print("   Path: {0}".format(main_window_path))
        return False
    
    try:
        with open(main_window_path, 'r') as f:
            content = f.read()
        
        # Check for the problematic line
        has_active_icon = "self.setWindowIcon(self.style().standardIcon" in content
        has_commented_icon = "# self.setWindowIcon(self.style().standardIcon" in content
        has_fix_comment = "Removed self.style().standardIcon() call to fix QProxyStyle error" in content
        
        print("\n" + "=" * 60)
        print("DIAGNOSTIC RESULTS")
        print("=" * 60)
        
        print("\n1. Active setWindowIcon call:")
        if has_active_icon and not has_commented_icon:
            print("   ❌ FOUND - This is the problem!")
            print("   The line 'self.setWindowIcon(self.style().standardIcon(...))' is ACTIVE")
            print("   This causes: Internal C++ object (PySide2.QtWidgets.QProxyStyle) already deleted")
        else:
            print("   ✅ NOT FOUND - Good!")
        
        print("\n2. Commented setWindowIcon call:")
        if has_commented_icon:
            print("   ✅ FOUND - Fix is present!")
            print("   The problematic line is commented out")
        else:
            print("   ❌ NOT FOUND - Fix is missing!")
        
        print("\n3. Fix documentation comment:")
        if has_fix_comment:
            print("   ✅ FOUND - Fix is documented!")
        else:
            print("   ⚠️  NOT FOUND - Fix comment missing")
        
        print("\n" + "=" * 60)
        print("CONCLUSION")
        print("=" * 60)
        
        if has_commented_icon and has_fix_comment and not (has_active_icon and not has_commented_icon):
            print("\n✅ FIX IS PRESENT!")
            print("   The QProxyStyle fix is correctly applied.")
            print("   If you're still getting the error, try:")
            print("   1. Clear Python cache (.pyc files)")
            print("   2. Restart Maya")
            print("   3. Make sure you're loading from the correct path")
            return True
        else:
            print("\n❌ FIX IS MISSING!")
            print("   The QProxyStyle fix is NOT applied.")
            print("   You need to:")
            print("   1. Pull latest code from master branch")
            print("   2. Make sure you're on master branch, not deploy/igloo-production")
            print("   3. Clear Python cache")
            print("   4. Restart Maya")
            return False
        
    except Exception as e:
        print("\n❌ ERROR reading file: {0}".format(e))
        return False


def check_loaded_module():
    """Check which version of main_window is loaded in memory."""
    print("\n" + "=" * 60)
    print("LOADED MODULE CHECK")
    print("=" * 60)
    
    if 'lrc_toolbox.ui.main_window' in sys.modules:
        module = sys.modules['lrc_toolbox.ui.main_window']
        module_file = getattr(module, '__file__', 'Unknown')
        print("\n✅ Module is loaded in memory")
        print("   Module file: {0}".format(module_file))
        
        # Check if the loaded module has the fix
        if hasattr(module, 'RenderSetupUI'):
            print("\n   Checking loaded RenderSetupUI class...")
            # We can't easily check the source of loaded code, but we can check the file
            if module_file and module_file != 'Unknown':
                print("   Loading from: {0}".format(module_file))
                return module_file
        else:
            print("\n   ⚠️  RenderSetupUI class not found in module")
    else:
        print("\n⚠️  Module not loaded in memory yet")
        print("   This is normal if you haven't opened the toolbox yet")
    
    return None


def show_fix_instructions(toolbox_path):
    """Show instructions to fix the issue."""
    print("\n" + "=" * 60)
    print("HOW TO FIX")
    print("=" * 60)
    
    print("\nOption 1: Pull Latest Code (Recommended)")
    print("-" * 60)
    print("1. Open command prompt/terminal")
    print("2. Navigate to your repository:")
    print("   cd {0}".format(os.path.dirname(os.path.dirname(toolbox_path))))
    print("3. Make sure you're on master branch:")
    print("   git checkout master")
    print("4. Pull latest code:")
    print("   git pull origin master")
    print("5. Restart Maya")
    
    print("\nOption 2: Clear Cache and Reload")
    print("-" * 60)
    print("1. Run this in Maya Script Editor:")
    print("   import sys, os, shutil")
    print("   toolbox_path = r'{0}'".format(toolbox_path))
    print("   for root, dirs, files in os.walk(toolbox_path):")
    print("       for file in files:")
    print("           if file.endswith('.pyc'):")
    print("               os.remove(os.path.join(root, file))")
    print("       if '__pycache__' in dirs:")
    print("           shutil.rmtree(os.path.join(root, '__pycache__'))")
    print("   # Unload module")
    print("   if 'lrc_toolbox.ui.main_window' in sys.modules:")
    print("       del sys.modules['lrc_toolbox.ui.main_window']")
    print("   print('Cache cleared!')")
    print("2. Restart Maya")
    
    print("\nOption 3: Check Your Path")
    print("-" * 60)
    print("Make sure you're loading from the correct location:")
    print("- E: drive (development): E:/dev/LRCtoolsbox/LRCtoolsbox/maya/lrc_toolbox")
    print("- V: drive (production): V:/SWA/tools/git/swaLRC/maya/lrc_toolbox")
    print("- T: drive (Igloo): T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX/maya/lrc_toolbox")
    print("\nIf T: drive has old code, you need to update it!")


def full_diagnostic(toolbox_path):
    """Run full diagnostic."""
    print("\n" + "=" * 80)
    print(" " * 20 + "QPROXYSTYLE ERROR FULL DIAGNOSTIC")
    print("=" * 80)
    print("\nToolbox Path: {0}".format(toolbox_path))
    print("=" * 80)
    
    # Check file
    has_fix = check_qproxystyle_fix(toolbox_path)
    
    # Check loaded module
    loaded_from = check_loaded_module()
    
    # Show fix instructions if needed
    if not has_fix:
        show_fix_instructions(toolbox_path)
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
    
    return has_fix


# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================

def show_usage():
    """Show usage instructions."""
    print("\n" + "=" * 60)
    print("QPROXYSTYLE ERROR DIAGNOSTIC - USAGE")
    print("=" * 60)
    print("\nTo diagnose QProxyStyle error, run ONE of these commands:")
    print("\n1. For T: drive installation:")
    print("   full_diagnostic(r'T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX/maya/lrc_toolbox')")
    print("\n2. For V: drive installation:")
    print("   full_diagnostic(r'V:/SWA/tools/git/swaLRC/maya/lrc_toolbox')")
    print("\n3. For E: drive installation:")
    print("   full_diagnostic(r'E:/dev/LRCtoolsbox/LRCtoolsbox/maya/lrc_toolbox')")
    print("\n4. For custom path:")
    print("   full_diagnostic(r'YOUR_PATH_HERE/maya/lrc_toolbox')")
    print("\nOr check file only:")
    print("   check_qproxystyle_fix(r'YOUR_PATH_HERE/maya/lrc_toolbox')")
    print("\nOr check loaded module only:")
    print("   check_loaded_module()")
    print("=" * 60)


# Show usage when script is loaded
show_usage()

