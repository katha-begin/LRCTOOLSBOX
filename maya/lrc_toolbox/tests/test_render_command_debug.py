# -*- coding: utf-8 -*-
"""
Debug Render Command Generation

Run this to see what command is being generated and if there are any errors.
"""

def test_render_command_debug():
    """Test render command generation with debug output."""
    print("=" * 80)
    print("RENDER COMMAND DEBUG TEST")
    print("=" * 80)
    
    try:
        from lrc_toolbox.core.render_execution_manager import RenderExecutionManager
        from lrc_toolbox.core.models import RenderConfig, RenderMethod
        import maya.cmds as cmds
        
        # Get current scene
        current_scene = cmds.file(query=True, sceneName=True)
        print(f"\nCurrent scene: {current_scene}")
        
        if not current_scene:
            print("ERROR: No scene file open!")
            print("Please open a scene file first.")
            return
        
        # Create test config
        config = RenderConfig(
            frame_range="1-10",
            layers=["MASTER_BG_A"],
            gpu_id=0,
            cpu_threads=4,
            renderer="redshift",
            method=RenderMethod.AUTO
        )
        
        print("\nTest Config:")
        print(f"  Frame Range: {config.frame_range}")
        print(f"  Layers: {config.layers}")
        print(f"  Renderer: {config.renderer}")
        print(f"  Method: {config.method}")
        
        # Initialize execution manager
        print("\n" + "=" * 80)
        print("INITIALIZING EXECUTION MANAGER")
        print("=" * 80)
        
        exec_manager = RenderExecutionManager()
        
        print(f"\nMayapy path: {exec_manager._mayapy_path}")
        print(f"Render.exe path: {exec_manager._render_exe_path}")
        
        # Test command generation for each method
        print("\n" + "=" * 80)
        print("TESTING RENDER.EXE COMMAND")
        print("=" * 80)
        
        try:
            render_exe_cmd = exec_manager._build_render_exe_command(config, current_scene)
            print("\nRender.exe Command:")
            print(" ".join(render_exe_cmd))
            print("\nCommand Parts:")
            for i, part in enumerate(render_exe_cmd):
                print(f"  [{i}] {part}")
        except Exception as e:
            print(f"\nERROR building Render.exe command: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("TESTING MAYAPY CUSTOM COMMAND")
        print("=" * 80)
        
        try:
            mayapy_custom_cmd = exec_manager._build_mayapy_custom_command(config, current_scene)
            print("\nMayapy Custom Command:")
            print(" ".join(mayapy_custom_cmd))
            print("\nCommand Parts:")
            for i, part in enumerate(mayapy_custom_cmd):
                print(f"  [{i}] {part}")
            
            # Check if script file was created
            script_path = mayapy_custom_cmd[1]
            import os
            if os.path.exists(script_path):
                print(f"\nScript file created: {script_path}")
                print("\nScript content (first 20 lines):")
                with open(script_path, 'r') as f:
                    lines = f.readlines()[:20]
                    for i, line in enumerate(lines, 1):
                        print(f"  {i:3d}: {line.rstrip()}")
            else:
                print(f"\nWARNING: Script file not found: {script_path}")
                
        except Exception as e:
            print(f"\nERROR building mayapy custom command: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("TESTING MAYAPY BASIC COMMAND")
        print("=" * 80)
        
        try:
            mayapy_basic_cmd = exec_manager._build_mayapy_basic_command(config, current_scene)
            print("\nMayapy Basic Command:")
            print(" ".join(mayapy_basic_cmd))
            print("\nCommand Parts:")
            for i, part in enumerate(mayapy_basic_cmd):
                print(f"  [{i}] {part}")
                
            # Check if script file was created
            script_path = mayapy_basic_cmd[1]
            import os
            if os.path.exists(script_path):
                print(f"\nScript file created: {script_path}")
                print("\nScript content (first 20 lines):")
                with open(script_path, 'r') as f:
                    lines = f.readlines()[:20]
                    for i, line in enumerate(lines, 1):
                        print(f"  {i:3d}: {line.rstrip()}")
            else:
                print(f"\nWARNING: Script file not found: {script_path}")
                
        except Exception as e:
            print(f"\nERROR building mayapy basic command: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("TESTING ENVIRONMENT VARIABLES")
        print("=" * 80)
        
        try:
            env_vars = exec_manager.build_environment(config)
            print("\nEnvironment Variables:")
            for key, value in env_vars.items():
                print(f"  {key} = {value}")
        except Exception as e:
            print(f"\nERROR building environment: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        
        print("\nIf you see errors above, that's what's causing the immediate crash!")
        print("Copy the error message and we can fix it.")
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_render_command_debug()

