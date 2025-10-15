# -*- coding: utf-8 -*-
"""
Minimal mayapy Test

Creates a minimal test script to see if mayapy can even start.
"""

def test_mayapy_minimal():
    """Create and test minimal mayapy script."""
    print("=" * 80)
    print("MINIMAL MAYAPY TEST")
    print("=" * 80)
    
    import os
    import subprocess
    import tempfile
    
    # Create minimal test script
    test_script = """
import sys
print("Python version:", sys.version)
print("Python executable:", sys.executable)

try:
    print("Importing maya.standalone...")
    import maya.standalone
    print("SUCCESS: maya.standalone imported")
    
    print("Initializing maya.standalone...")
    maya.standalone.initialize(name='python')
    print("SUCCESS: maya.standalone initialized")
    
    print("Importing maya.cmds...")
    import maya.cmds as cmds
    print("SUCCESS: maya.cmds imported")
    
    print("Checking batch mode...")
    is_batch = cmds.about(batch=True)
    print(f"Batch mode: {is_batch}")
    
    print("Uninitializing maya.standalone...")
    maya.standalone.uninitialize()
    print("SUCCESS: maya.standalone uninitialized")
    
    print("ALL TESTS PASSED!")
    sys.exit(0)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    
    # Save to temp file
    temp_dir = tempfile.gettempdir()
    script_path = os.path.join(temp_dir, "test_mayapy_minimal.py")
    
    print(f"\nCreating test script: {script_path}")
    with open(script_path, 'w') as f:
        f.write(test_script)
    
    print("Test script created")
    
    # Find mayapy
    mayapy_path = r"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe"
    
    if not os.path.exists(mayapy_path):
        print(f"ERROR: mayapy not found: {mayapy_path}")
        return
    
    print(f"\nMayapy path: {mayapy_path}")
    
    # Build command
    command = [mayapy_path, script_path]
    
    print("\n" + "=" * 80)
    print("RUNNING MINIMAL TEST")
    print("=" * 80)
    print("Command:", " ".join(command))
    print("\nThis will test if mayapy can start at all...")
    print("If this crashes, the problem is with Maya installation or environment.")
    print("=" * 80)
    
    # Run with output
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("\n" + "=" * 80)
        print("OUTPUT")
        print("=" * 80)
        if result.stdout:
            print(result.stdout)
        else:
            print("(no stdout)")
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        print("\n" + "=" * 80)
        print("RESULT")
        print("=" * 80)
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ SUCCESS! mayapy is working correctly.")
            print("\nThe problem is likely in the render script itself.")
        else:
            print("❌ FAILED! mayapy cannot start properly.")
            print("\nPossible causes:")
            print("1. Maya installation is corrupted")
            print("2. Missing DLLs or dependencies")
            print("3. Conflicting Python environment")
            print("4. Insufficient permissions")
        
    except subprocess.TimeoutExpired:
        print("\n❌ TIMEOUT! mayapy hung and didn't respond.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_mayapy_minimal()

