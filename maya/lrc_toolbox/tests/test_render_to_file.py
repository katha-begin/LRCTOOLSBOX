# -*- coding: utf-8 -*-
"""
Test Render with File Output

Runs Render.exe and saves output to a log file.
"""

def test_render_to_file():
    """Run Render.exe and save output to file."""
    print("=" * 80)
    print("RENDER.EXE TEST WITH FILE OUTPUT")
    print("=" * 80)
    
    import subprocess
    import os
    import tempfile
    import maya.cmds as cmds
    
    # Get current scene
    current_scene = cmds.file(query=True, sceneName=True)
    print(f"\nCurrent scene: {current_scene}")
    
    if not current_scene:
        print("ERROR: No scene file open!")
        return
    
    # Get render layers
    import sys
    sys.path.insert(0, r'E:\dev\LRCtoolsbox\LRCtoolsbox\maya')
    from lrc_toolbox.utils.render_layers import get_all_layers
    
    layers = get_all_layers()
    if not layers:
        print("ERROR: No render layers found!")
        return
    
    layer_name = layers[0]['name']
    print(f"Using layer: {layer_name}")
    
    # Build Render.exe command
    render_exe = r"C:\Program Files\Autodesk\Maya2022\bin\Render.exe"
    
    if not os.path.exists(render_exe):
        print(f"ERROR: Render.exe not found: {render_exe}")
        return
    
    # Simple command - just render 1 frame
    command = [
        render_exe,
        "-r", "redshift",
        "-rl", layer_name,
        "-s", "1",
        "-e", "1",
        # Note: -v flag is NOT supported by Render.exe
        current_scene
    ]
    
    print("\n" + "=" * 80)
    print("COMMAND")
    print("=" * 80)
    print(" ".join(command))
    
    # Create log file
    log_file = os.path.join(tempfile.gettempdir(), "render_test.log")
    print(f"\nLog file: {log_file}")
    
    print("\n" + "=" * 80)
    print("RUNNING RENDER.EXE")
    print("=" * 80)
    print("This may take a moment...")
    print("Output will be saved to log file.")
    
    # Run with file output
    try:
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            print(f"Process started: PID {process.pid}")
            print("Waiting for process to complete...")
            
            # Wait for completion
            return_code = process.wait(timeout=120)  # 2 minute timeout
            
            print(f"\nProcess completed with return code: {return_code}")
        
        # Read and display log
        print("\n" + "=" * 80)
        print("LOG FILE CONTENT")
        print("=" * 80)
        
        with open(log_file, 'r') as log:
            content = log.read()
            print(content)
        
        print("\n" + "=" * 80)
        print("RESULT")
        print("=" * 80)
        
        if return_code == 0:
            print("✅ SUCCESS!")
        else:
            print(f"❌ FAILED with return code {return_code}")
            print("\nCheck the log above for error messages.")
            print("Look for lines containing 'Error:', 'Warning:', or 'Failed'")
        
        print(f"\nFull log saved to: {log_file}")
        
    except subprocess.TimeoutExpired:
        print("\n❌ TIMEOUT! Process took longer than 2 minutes.")
        process.kill()
        
        # Try to read partial log
        try:
            with open(log_file, 'r') as log:
                content = log.read()
                print("\nPartial log:")
                print(content)
        except:
            pass
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_render_to_file()

