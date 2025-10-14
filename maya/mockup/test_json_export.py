#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for JSON export functionality in save_and_setting.py

This script demonstrates how to use the JSON export functions to export
shot data for external use.

Usage in Maya Script Editor:
    exec(open(r'E:\dev\LRCtoolsbox\LRCtoolsbox\maya\mockup\test_json_export.py').read())
"""

from __future__ import print_function
import os
import sys

# Add the mockup directory to Python path if not already there
mockup_dir = os.path.dirname(__file__)
if mockup_dir not in sys.path:
    sys.path.insert(0, mockup_dir)

try:
    import maya.cmds as cmds
    from save_and_setting import (
        export_shot_data_to_json,
        _extract_shot_data_from_node,
        _get_json_export_path,
        _list_shot_nodes
    )
    
    def test_json_export():
        """Test the JSON export functionality."""
        print("=" * 60)
        print("Testing JSON Export Functionality")
        print("=" * 60)
        
        # 1. List available shot nodes
        print("\n1. Checking for shot nodes...")
        shot_nodes = _list_shot_nodes()
        if not shot_nodes:
            print("   No shot nodes found in current scene.")
            print("   Creating a test shot node...")
            
            # Create a test shot node
            shot_node = cmds.shot(
                shotName="Ep01_sq0010_SH0045",
                startTime=1001,
                endTime=1120,
                sequenceStartTime=1001,
                sequenceEndTime=1120
            )
            print("   Created test shot node: {}".format(shot_node))
        else:
            shot_node = shot_nodes[0]
            print("   Found shot node: {}".format(shot_node))
        
        # 2. Test data extraction
        print("\n2. Testing data extraction...")
        try:
            shot_data = _extract_shot_data_from_node(shot_node, "SWA")
            print("   ✓ Successfully extracted shot data")
            print("   Episode: {}".format(shot_data["shot_info"]["episode"]))
            print("   Sequence: {}".format(shot_data["shot_info"]["sequence"]))
            print("   Shot: {}".format(shot_data["shot_info"]["shot"]))
            print("   Frames: {}-{}".format(
                shot_data["shot_info"]["start_frame"],
                shot_data["shot_info"]["end_frame"]
            ))
        except Exception as e:
            print("   ✗ Failed to extract shot data: {}".format(e))
            return False
        
        # 3. Test JSON path generation
        print("\n3. Testing JSON path generation...")
        json_path = _get_json_export_path(
            "V:/",
            "SWA", 
            shot_data["shot_info"]["episode"],
            shot_data["shot_info"]["sequence"],
            shot_data["shot_info"]["shot"]
        )
        print("   JSON export path: {}".format(json_path))
        
        # 4. Test full export
        print("\n4. Testing full JSON export...")
        try:
            success, file_path, data = export_shot_data_to_json(shot_node, "V:/", "SWA")
            if success:
                print("   ✓ Export successful!")
                print("   File: {}".format(file_path))
                print("   Data keys: {}".format(list(data.keys())))
                
                # Check if file exists
                if os.path.exists(file_path):
                    print("   ✓ JSON file created successfully")
                    file_size = os.path.getsize(file_path)
                    print("   File size: {} bytes".format(file_size))
                else:
                    print("   ✗ JSON file not found at expected location")
            else:
                print("   ✗ Export failed: {}".format(data.get("error", "Unknown error")))
                return False
        except Exception as e:
            print("   ✗ Export exception: {}".format(e))
            return False
        
        # 5. Test duplicate export (should skip)
        print("\n5. Testing duplicate export detection...")
        try:
            success2, file_path2, data2 = export_shot_data_to_json(shot_node, "V:/", "SWA")
            if success2:
                print("   ✓ Second export completed (should have been skipped if data unchanged)")
            else:
                print("   ✗ Second export failed: {}".format(data2.get("error", "Unknown error")))
        except Exception as e:
            print("   ✗ Second export exception: {}".format(e))
        
        print("\n" + "=" * 60)
        print("JSON Export Test Completed Successfully!")
        print("=" * 60)
        print("\nSample JSON structure:")
        print("- metadata: Export info, Maya version, scene file")
        print("- shot_info: Episode, sequence, shot, frames, version")
        print("- render_settings: Renderer, animation settings, image prefix")
        print("- timeline_settings: Playback and animation ranges")
        print("- shot_attributes: Additional shot node attributes")
        print("\nJSON file location pattern:")
        print("{project_root}\\{project}\\all\\scene\\{ep}\\{seq}\\{shot}\\.{ep}_{seq}_{shot}.json")
        
        return True
    
    def cleanup_test():
        """Clean up test shot nodes."""
        print("\nCleaning up test shot nodes...")
        shot_nodes = _list_shot_nodes()
        for node in shot_nodes:
            if "test" in node.lower() or cmds.getAttr(node + ".shotName", asString=True).startswith("Ep01_sq0010_SH0045"):
                try:
                    cmds.delete(node)
                    print("   Deleted test shot node: {}".format(node))
                except Exception:
                    pass
    
    # Run the test
    if __name__ == "__main__":
        test_json_export()
        
        # Ask user if they want to clean up
        result = cmds.confirmDialog(
            title="Test Complete",
            message="JSON export test completed. Clean up test shot nodes?",
            button=["Yes", "No"],
            defaultButton="Yes",
            cancelButton="No",
            dismissString="No"
        )
        
        if result == "Yes":
            cleanup_test()

except ImportError as e:
    print("Error: Could not import required modules: {}".format(e))
    print("Make sure you're running this in Maya and save_and_setting.py is available.")
except Exception as e:
    print("Unexpected error: {}".format(e))
