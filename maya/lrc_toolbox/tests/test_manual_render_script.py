# -*- coding: utf-8 -*-
"""
Test Manual Render Script Execution

This will show you the EXACT error that's causing the crash.
Run this in Maya Script Editor to see the full error output.
"""

def test_manual_render_script():
    """
    Manually execute the render script to see full error output.
    """
    print("=" * 80)
    print("MANUAL RENDER SCRIPT TEST")
    print("=" * 80)
    
    import os
    import maya.cmds as cmds
    
    # Get current scene
    current_scene = cmds.file(query=True, sceneName=True)
    print(f"\nCurrent scene: {current_scene}")
    
    if not current_scene:
        print("ERROR: No scene file open!")
        return
    
    # Find the render script that was created
    script_path = current_scene.replace('.ma', '_render_custom.py')
    
    print(f"\nLooking for script: {script_path}")
    
    if not os.path.exists(script_path):
        print(f"ERROR: Script not found!")
        print(f"Please run the debug test first to create the script:")
        print(f"  from lrc_toolbox.tests.test_render_command_debug import test_render_command_debug")
        print(f"  test_render_command_debug()")
        return
    
    print(f"Script found!")
    
    # Read and display the script
    print("\n" + "=" * 80)
    print("SCRIPT CONTENT")
    print("=" * 80)
    with open(script_path, 'r') as f:
        script_content = f.read()
        lines = script_content.split('\n')
        for i, line in enumerate(lines[:50], 1):  # Show first 50 lines
            print(f"{i:3d}: {line}")
        if len(lines) > 50:
            print(f"... ({len(lines) - 50} more lines)")
    
    # Now execute the script and capture output
    print("\n" + "=" * 80)
    print("EXECUTING SCRIPT")
    print("=" * 80)
    print("\nThis will show the EXACT error that's causing the crash...")
    print("=" * 80)
    
    # Execute the script using exec
    try:
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # Execute in a namespace to capture output
        namespace = {}
        exec(script_content, namespace)
        
        print("\n" + "=" * 80)
        print("SCRIPT EXECUTED SUCCESSFULLY!")
        print("=" * 80)
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("SCRIPT EXECUTION FAILED!")
        print("=" * 80)
        print(f"\nError: {e}")
        print("\nFull traceback:")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 80)
        print("THIS IS THE ERROR CAUSING THE CRASH!")
        print("=" * 80)


if __name__ == "__main__":
    test_manual_render_script()

