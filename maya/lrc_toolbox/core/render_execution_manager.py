# -*- coding: utf-8 -*-
"""
Render Execution Manager

Three-level fallback system for batch rendering:
Priority 1: Maya Render.exe (most stable and reliable)
Priority 2: mayapy with custom script (flexible but can crash)
Priority 3: mayapy with basic render (fallback)
"""

import os
import platform
from typing import Optional, Dict, Any, List
from pathlib import Path

from .models import RenderMethod, RenderConfig
from .system_detector import SystemDetector


class RenderExecutionManager:
    """
    Manages render execution with automatic fallback system.

    Three-level priority system:
    1. RENDER_EXE: Maya Render.exe (most stable and reliable)
    2. MAYAPY_CUSTOM: mayapy + custom script (flexible but can crash)
    3. MAYAPY_BASIC: mayapy + basic render (fallback)
    """
    
    def __init__(self):
        """Initialize render execution manager."""
        self._system_detector = SystemDetector()
        self._mayapy_path: Optional[str] = None
        self._render_exe_path: Optional[str] = None
        self._system = platform.system()

        # Automatically detect executables on initialization
        self.detect_executables()
    
    def detect_executables(self) -> Dict[str, Optional[str]]:
        """
        Detect available Maya executables.
        
        Returns:
            Dictionary with executable paths
        """
        self._mayapy_path = self._system_detector.find_mayapy_executable()
        self._render_exe_path = self._system_detector.find_render_executable()
        
        return {
            "mayapy": self._mayapy_path,
            "render_exe": self._render_exe_path
        }
    
    def get_available_methods(self) -> List[RenderMethod]:
        """
        Get list of available render methods.
        
        Returns:
            List of available RenderMethod enums
        """
        if not self._mayapy_path and not self._render_exe_path:
            self.detect_executables()
        
        methods = []
        
        if self._mayapy_path:
            methods.append(RenderMethod.MAYAPY_CUSTOM)
            methods.append(RenderMethod.MAYAPY_BASIC)
        
        if self._render_exe_path:
            methods.append(RenderMethod.RENDER_EXE)
        
        return methods
    
    def select_render_method(self, preferred: RenderMethod = RenderMethod.AUTO) -> RenderMethod:
        """
        Select render method with fallback.
        
        Args:
            preferred: Preferred render method
            
        Returns:
            Selected RenderMethod (with fallback if preferred not available)
        """
        available = self.get_available_methods()
        
        if not available:
            raise RuntimeError("No render methods available - Maya executables not found")
        
        # AUTO mode: use priority order
        if preferred == RenderMethod.AUTO:
            # Priority 1: RENDER_EXE (most stable, native Maya batch renderer)
            if RenderMethod.RENDER_EXE in available:
                print("[RenderExec] Selected: RENDER_EXE (Priority 1 - Most Stable)")
                return RenderMethod.RENDER_EXE

            # Priority 2: MAYAPY_CUSTOM (flexible but can crash)
            if RenderMethod.MAYAPY_CUSTOM in available:
                print("[RenderExec] Selected: MAYAPY_CUSTOM (Priority 2)")
                return RenderMethod.MAYAPY_CUSTOM

            # Priority 3: MAYAPY_BASIC (fallback)
            if RenderMethod.MAYAPY_BASIC in available:
                print("[RenderExec] Selected: MAYAPY_BASIC (Priority 3)")
                return RenderMethod.MAYAPY_BASIC
        
        # Specific method requested
        if preferred in available:
            print(f"[RenderExec] Selected: {preferred.value} (requested)")
            return preferred
        
        # Fallback to first available
        fallback = available[0]
        print(f"[RenderExec] Fallback: {fallback.value} (preferred not available)")
        return fallback
    
    def build_render_command(self, config: RenderConfig, method: RenderMethod,
                            temp_scene_file: str) -> List[str]:
        """
        Build render command for specified method.
        
        Args:
            config: Render configuration
            method: Render method to use
            temp_scene_file: Path to temporary scene file
            
        Returns:
            Command as list of strings
        """
        if method == RenderMethod.MAYAPY_CUSTOM:
            return self._build_mayapy_custom_command(config, temp_scene_file)
        
        elif method == RenderMethod.RENDER_EXE:
            return self._build_render_exe_command(config, temp_scene_file)
        
        elif method == RenderMethod.MAYAPY_BASIC:
            return self._build_mayapy_basic_command(config, temp_scene_file)
        
        else:
            raise ValueError(f"Unknown render method: {method}")
    
    def _build_mayapy_custom_command(self, config: RenderConfig, 
                                    scene_file: str) -> List[str]:
        """
        Build mayapy custom script command (Priority 1).
        
        Most flexible - allows custom pre/post render operations.
        """
        if not self._mayapy_path:
            raise RuntimeError("mayapy not available")
        
        # Create custom render script path
        script_path = self._create_custom_render_script(config, scene_file)
        
        command = [self._mayapy_path, script_path]
        
        return command
    
    def _build_render_exe_command(self, config: RenderConfig,
                                  scene_file: str) -> List[str]:
        """
        Build Render.exe command (Priority 2).

        Most reliable - uses Maya's native batch renderer.
        Includes all critical flags to prevent crashes.
        """
        if not self._render_exe_path:
            raise RuntimeError("Render.exe not available")

        command = [self._render_exe_path]

        # Renderer
        command.extend(["-r", config.renderer])

        # Render layer
        if config.layers:
            command.extend(["-rl", config.layers[0]])

        # Frame range
        from ..utils.frame_parser import get_first_last_frames
        try:
            first, last = get_first_last_frames(config.frame_range)
            command.extend(["-s", str(first)])
            command.extend(["-e", str(last)])
            command.extend(["-b", "1"])  # Frame step
        except:
            pass

        # Project directory (extract from scene path)
        # Simplified - just use scene directory's parent
        try:
            scene_dir = os.path.dirname(scene_file)
            project_root = os.path.dirname(scene_dir)
            command.extend(["-proj", project_root])
            print(f"[RenderExec] Project directory: {project_root}")
        except Exception as e:
            print(f"[RenderExec] Could not set project directory: {e}")

        # Output directory - simplified to avoid crashes
        # Just use images folder next to scene folder
        try:
            if config.layers:
                layer_name = config.layers[0]
                scene_dir = os.path.dirname(scene_file)
                images_dir = os.path.join(os.path.dirname(scene_dir), "images", layer_name)

                # Create output directory if it doesn't exist
                os.makedirs(images_dir, exist_ok=True)
                command.extend(["-rd", images_dir])
                print(f"[RenderExec] Output directory: {images_dir}")
        except Exception as e:
            print(f"[RenderExec] Could not set output directory: {e}")

        # Image name prefix
        if config.layers:
            layer_name = config.layers[0]
            scene_name = os.path.splitext(os.path.basename(scene_file))[0]
            image_prefix = f"{scene_name}_{layer_name}"
            command.extend(["-im", image_prefix])

        # Verbosity (maximum for debugging)
        command.extend(["-v", "5"])

        # Scene file (must be last)
        command.append(scene_file)

        return command
    
    def _build_mayapy_basic_command(self, config: RenderConfig,
                                   scene_file: str) -> List[str]:
        """
        Build mayapy basic render command (Priority 3).
        
        Fallback - simple render without custom operations.
        """
        if not self._mayapy_path:
            raise RuntimeError("mayapy not available")
        
        # Create basic render script
        script_path = self._create_basic_render_script(config, scene_file)
        
        command = [self._mayapy_path, script_path]
        
        return command
    
    def build_environment(self, config: RenderConfig) -> Dict[str, str]:
        """
        Build environment variables for render process.
        
        Args:
            config: Render configuration
            
        Returns:
            Dictionary of environment variables
        """
        env = os.environ.copy()
        
        # Set GPU
        env["CUDA_VISIBLE_DEVICES"] = str(config.gpu_id)
        
        # Set CPU threads (if supported by renderer)
        env["OMP_NUM_THREADS"] = str(config.cpu_threads)
        
        return env
    
    def _create_custom_render_script(self, config: RenderConfig,
                                    scene_file: str) -> str:
        """
        Create custom mayapy render script (Priority 1).

        Returns:
            Path to created script file
        """
        from ..utils.frame_parser import parse_frame_range

        # Parse frames
        frames = parse_frame_range(config.frame_range)
        layer_name = config.layers[0] if config.layers else "defaultRenderLayer"

        # Create script content with proper error handling
        script_content = f'''# -*- coding: utf-8 -*-
"""Custom Batch Render Script - Priority 1 with Error Handling"""

import sys
import traceback

def main():
    """Main render function with proper error handling."""
    try:
        # Initialize Maya standalone with name argument
        print("[Render] Initializing Maya standalone...")
        import maya.standalone
        maya.standalone.initialize(name='python')

        import maya.cmds as cmds

        # Verify batch mode
        is_batch = cmds.about(batch=True)
        print(f"[Render] Batch mode: {{is_batch}}")

        # Load required plugins
        print("[Render] Loading plugins...")
        plugins = ['{config.renderer}']
        for plugin in plugins:
            try:
                if not cmds.pluginInfo(plugin, query=True, loaded=True):
                    cmds.loadPlugin(plugin, quiet=True)
                    print(f"[Render] Loaded plugin: {{plugin}}")
            except Exception as e:
                print(f"[Render] Warning: Could not load plugin {{plugin}}: {{e}}")

        # Open scene with error handling
        print("[Render] Opening scene: {scene_file}")
        try:
            cmds.file("{scene_file}", open=True, force=True, ignoreVersion=True)
            print("[Render] Scene opened successfully")
        except Exception as e:
            print(f"[Render] ERROR: Failed to open scene: {{e}}")
            return 1

        # Set render layer
        print("[Render] Setting render layer: {layer_name}")
        try:
            cmds.editRenderLayerGlobals(currentRenderLayer="{layer_name}")
        except Exception as e:
            print(f"[Render] ERROR: Failed to set render layer: {{e}}")
            return 1

        # Set renderer
        print("[Render] Setting renderer: {config.renderer}")
        try:
            cmds.setAttr("defaultRenderGlobals.currentRenderer", "{config.renderer}", type="string")
        except Exception as e:
            print(f"[Render] ERROR: Failed to set renderer: {{e}}")
            return 1

        # Render frames
        frames = {frames}
        total_frames = len(frames)
        print(f"[Render] Rendering {{total_frames}} frames: {{frames}}")

        for i, frame in enumerate(frames, 1):
            try:
                print(f"[Render] Rendering frame {{frame}} ({{i}}/{{total_frames}})")
                cmds.currentTime(frame)

                # Custom pre-render operations can be added here

                # Render
                cmds.render()

                # Custom post-render operations can be added here

                print(f"[Render] Frame {{frame}} completed")

            except Exception as e:
                print(f"[Render] ERROR: Failed to render frame {{frame}}: {{e}}")
                traceback.print_exc()
                return 1

        print("[Render] Render complete!")
        return 0

    except Exception as e:
        print(f"[Render] FATAL ERROR: {{e}}")
        traceback.print_exc()
        return 1

    finally:
        # Always uninitialize Maya
        try:
            print("[Render] Uninitializing Maya...")
            maya.standalone.uninitialize()
        except:
            pass

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
'''

        # Save script to temp file
        script_path = scene_file.replace('.ma', '_render_custom.py')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        return script_path

    def _create_basic_render_script(self, config: RenderConfig,
                                   scene_file: str) -> str:
        """
        Create basic mayapy render script (Priority 3).

        Returns:
            Path to created script file
        """
        from ..utils.frame_parser import get_first_last_frames

        # Get frame range
        try:
            first, last = get_first_last_frames(config.frame_range)
        except:
            first, last = 1, 1

        layer_name = config.layers[0] if config.layers else "defaultRenderLayer"

        # Create basic script with error handling
        script_content = f'''# -*- coding: utf-8 -*-
"""Basic Batch Render Script - Priority 3 Fallback with Error Handling"""

import sys
import traceback

def main():
    """Main render function with proper error handling."""
    try:
        # Initialize Maya standalone
        print("[Render] Initializing Maya standalone...")
        import maya.standalone
        maya.standalone.initialize(name='python')

        import maya.cmds as cmds

        # Verify batch mode
        is_batch = cmds.about(batch=True)
        print(f"[Render] Batch mode: {{is_batch}}")

        # Load required plugins
        print("[Render] Loading plugins...")
        plugins = ['{config.renderer}']
        for plugin in plugins:
            try:
                if not cmds.pluginInfo(plugin, query=True, loaded=True):
                    cmds.loadPlugin(plugin, quiet=True)
                    print(f"[Render] Loaded plugin: {{plugin}}")
            except Exception as e:
                print(f"[Render] Warning: Could not load plugin {{plugin}}: {{e}}")

        # Open scene
        print("[Render] Opening scene: {scene_file}")
        try:
            cmds.file("{scene_file}", open=True, force=True, ignoreVersion=True)
            print("[Render] Scene opened successfully")
        except Exception as e:
            print(f"[Render] ERROR: Failed to open scene: {{e}}")
            return 1

        # Set render layer
        print("[Render] Setting render layer: {layer_name}")
        try:
            cmds.editRenderLayerGlobals(currentRenderLayer="{layer_name}")
        except Exception as e:
            print(f"[Render] ERROR: Failed to set render layer: {{e}}")
            return 1

        # Set renderer
        print("[Render] Setting renderer: {config.renderer}")
        try:
            cmds.setAttr("defaultRenderGlobals.currentRenderer", "{config.renderer}", type="string")
        except Exception as e:
            print(f"[Render] ERROR: Failed to set renderer: {{e}}")
            return 1

        # Set frame range
        print("[Render] Frame range: {first}-{last}")
        try:
            cmds.setAttr("defaultRenderGlobals.startFrame", {first})
            cmds.setAttr("defaultRenderGlobals.endFrame", {last})
        except Exception as e:
            print(f"[Render] ERROR: Failed to set frame range: {{e}}")
            return 1

        # Batch render
        print("[Render] Starting batch render...")
        try:
            cmds.batchRender()
            print("[Render] Render complete!")
            return 0
        except Exception as e:
            print(f"[Render] ERROR: Batch render failed: {{e}}")
            traceback.print_exc()
            return 1

    except Exception as e:
        print(f"[Render] FATAL ERROR: {{e}}")
        traceback.print_exc()
        return 1

    finally:
        # Always uninitialize Maya
        try:
            print("[Render] Uninitializing Maya...")
            maya.standalone.uninitialize()
        except:
            pass

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
'''

        # Save script
        script_path = scene_file.replace('.ma', '_render_basic.py')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        return script_path

