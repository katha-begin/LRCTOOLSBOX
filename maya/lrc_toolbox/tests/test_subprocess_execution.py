# -*- coding: utf-8 -*-
"""
Test Subprocess Execution

Test if mayapy.exe can actually run the render script as a subprocess.
"""

def test_subprocess_execution():
    """
    Test running mayapy.exe as a subprocess to see if it works.
    """
    print("=" * 80)
    print("SUBPROCESS EXECUTION TEST")
    print("=" * 80)
    
    import os
    import subprocess
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
    
    # Find mayapy.exe
    mayapy_path = r"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe"
    
    if not os.path.exists(mayapy_path):
        print(f"ERROR: mayapy.exe not found: {mayapy_path}")
        return
    
    print(f"mayapy.exe found: {mayapy_path}")
    
    # Build command
    command = [mayapy_path, script_path]
    
    print("\n" + "=" * 80)
    print("COMMAND TO EXECUTE")
    print("=" * 80)
    print(" ".join(command))
    
    # Execute as subprocess
    print("\n" + "=" * 80)
    print("EXECUTING SUBPROCESS")
    print("=" * 80)
    print("\nThis will run mayapy.exe as a subprocess...")
    print("Watch for output below:")
    print("=" * 80)
    
    try:
        # Run with shell=True and capture output
        import platform
        if platform.system() == 'Windows':
            # Windows-specific subprocess handling
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                startupinfo=startupinfo,
                text=True
            )
        else:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                text=True
            )
        
        print(f"\nProcess started with PID: {process.pid}")
        print("Waiting for process to complete (max 30 seconds)...")
        
        # Wait for completion with timeout
        try:
            stdout, stderr = process.communicate(timeout=30)
            return_code = process.returncode
            
            print("\n" + "=" * 80)
            print("PROCESS COMPLETED")
            print("=" * 80)
            print(f"Return code: {return_code}")
            
            if stdout:
                print("\n" + "=" * 80)
                print("STDOUT OUTPUT")
                print("=" * 80)
                print(stdout)
            
            if stderr:
                print("\n" + "=" * 80)
                print("STDERR OUTPUT")
                print("=" * 80)
                print(stderr)
            
            if return_code == 0:
                print("\n" + "=" * 80)
                print("SUCCESS! Process completed without errors.")
                print("=" * 80)
            else:
                print("\n" + "=" * 80)
                print(f"FAILED! Process exited with code {return_code}")
                print("=" * 80)
                print("\nThis is why the batch render is crashing!")
                print("Check the STDERR OUTPUT above for the error message.")
                
        except subprocess.TimeoutExpired:
            print("\n" + "=" * 80)
            print("TIMEOUT! Process is still running after 30 seconds.")
            print("=" * 80)
            print("Killing process...")
            process.kill()
            stdout, stderr = process.communicate()
            
            if stdout:
                print("\nPartial STDOUT:")
                print(stdout)
            if stderr:
                print("\nPartial STDERR:")
                print(stderr)
            
    except Exception as e:
        print("\n" + "=" * 80)
        print("SUBPROCESS EXECUTION FAILED!")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nThis is why the batch render is crashing!")


if __name__ == "__main__":
    test_subprocess_execution()

