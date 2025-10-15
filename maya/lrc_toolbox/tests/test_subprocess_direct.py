# -*- coding: utf-8 -*-
"""
Test Subprocess Directly

Run the render command directly to see what happens.
"""

def test_subprocess_direct():
    """Test running the render command directly."""
    print("=" * 80)
    print("DIRECT SUBPROCESS TEST")
    print("=" * 80)
    
    import subprocess
    import os
    import maya.cmds as cmds
    
    # Get current scene
    current_scene = cmds.file(query=True, sceneName=True)
    print(f"\nCurrent scene: {current_scene}")
    
    if not current_scene:
        print("ERROR: No scene file open!")
        return
    
    # Find the render script
    script_path = current_scene.replace('.ma', '_render_custom.py')
    
    if not os.path.exists(script_path):
        print(f"ERROR: Script not found: {script_path}")
        print("Run the debug test first to create the script.")
        return
    
    print(f"Script found: {script_path}")
    
    # Build command
    mayapy_path = r"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe"
    
    if not os.path.exists(mayapy_path):
        print(f"ERROR: mayapy not found: {mayapy_path}")
        return
    
    command = [mayapy_path, script_path]
    
    print("\n" + "=" * 80)
    print("COMMAND")
    print("=" * 80)
    print(" ".join(command))
    
    print("\n" + "=" * 80)
    print("RUNNING COMMAND (this may take a moment)...")
    print("=" * 80)
    
    # Run with output capture
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        print("\n" + "=" * 80)
        print("STDOUT OUTPUT")
        print("=" * 80)
        print(result.stdout)
        
        print("\n" + "=" * 80)
        print("STDERR OUTPUT")
        print("=" * 80)
        print(result.stderr)
        
        print("\n" + "=" * 80)
        print("RETURN CODE")
        print("=" * 80)
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ SUCCESS!")
        else:
            print("❌ FAILED!")
            print("\nThis is why the batch render is crashing!")
        
    except subprocess.TimeoutExpired:
        print("\n" + "=" * 80)
        print("TIMEOUT!")
        print("=" * 80)
        print("The command took longer than 30 seconds.")
        print("This might mean it's actually working but taking a long time.")
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("ERROR!")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_subprocess_direct()

