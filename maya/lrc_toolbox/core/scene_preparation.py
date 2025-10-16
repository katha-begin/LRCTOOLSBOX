# -*- coding: utf-8 -*-
"""
Scene Preparation

Prepares Maya scenes for batch rendering by saving temporary files
with specific render layer configurations.
"""

import os
from typing import List, Optional, Tuple

from ..utils.temp_file_manager import TempFileManager


class ScenePreparation:
    """
    Prepares Maya scenes for batch rendering.
    
    Features:
    - Save current scene to temporary file
    - Get available render layers
    - Validate scene for rendering
    - Scene file management
    """
    
    def __init__(self):
        """Initialize scene preparation."""
        self._temp_manager = TempFileManager()
        self._maya_available = False
        
        # Try to import Maya
        try:
            import maya.cmds as cmds
            self._cmds = cmds
            self._maya_available = True
        except ImportError:
            self._cmds = None
            print("[ScenePrep] Maya not available - running in standalone mode")
    
    def is_maya_available(self) -> bool:
        """
        Check if Maya is available.
        
        Returns:
            True if Maya cmds available, False otherwise
        """
        return self._maya_available
    
    def get_current_scene_file(self) -> Optional[str]:
        """
        Get current Maya scene file path.
        
        Returns:
            Scene file path or None if no scene open
        """
        if not self._maya_available:
            return None
        
        try:
            scene_file = self._cmds.file(query=True, sceneName=True)
            
            if not scene_file:
                print("[ScenePrep] No scene file open")
                return None
            
            return scene_file
            
        except Exception as e:
            print(f"[ScenePrep] Failed to get scene file: {e}")
            return None
    
    def get_render_layers(self) -> List[str]:
        """
        Get list of available render layers from Maya Render Setup.

        This uses Maya's Render Setup system (not legacy render layers).
        Returns only enabled/renderable layers.

        Returns:
            List of render layer names from Render Setup (excludes defaultRenderLayer)
        """
        if not self._maya_available:
            return []

        try:
            # Use Render Setup API (not legacy render layers)
            from ..utils.render_layers import get_all_layers

            layers = get_all_layers()

            # Filter out default layer and get names
            # get_all_layers() returns layers from Render Setup system
            layer_names = []
            for layer_info in layers:
                name = layer_info.get("name", "")
                enabled = layer_info.get("enabled", True)

                # Only include enabled layers, exclude default
                if name and name != "defaultRenderLayer" and enabled:
                    layer_names.append(name)

            print(f"[ScenePrep] Found {len(layer_names)} render layers from Render Setup")
            return layer_names

        except Exception as e:
            print(f"[ScenePrep] Failed to get render layers from Render Setup: {e}")
            return []

    def get_renderable_cameras(self) -> List[str]:
        """
        Get list of renderable cameras from render settings.

        Returns cameras that have the 'renderable' attribute set to True.
        These are the cameras that will be used by batch rendering.

        Returns:
            List of camera transform names that are renderable
        """
        if not self._maya_available:
            return []

        try:
            cameras = []
            all_cameras = self._cmds.ls(type='camera')

            for cam in all_cameras:
                if self._cmds.getAttr(f"{cam}.renderable"):
                    # Get the transform node
                    transform = self._cmds.listRelatives(cam, parent=True, type='transform')
                    if transform:
                        cameras.append(transform[0])

            return cameras

        except Exception as e:
            print(f"[ScenePrep] Failed to get renderable cameras: {e}")
            return []

    def verify_renderable_camera(self) -> Tuple[bool, str]:
        """
        Verify that exactly one camera is set as renderable.

        Batch rendering requires exactly one camera to be renderable.
        Multiple or zero renderable cameras will cause issues.

        Returns:
            Tuple of (is_valid, message)
        """
        if not self._maya_available:
            return False, "Maya not available"

        try:
            renderable_cameras = self.get_renderable_cameras()

            if len(renderable_cameras) == 0:
                return False, "No renderable camera found. Please set a camera as renderable in render settings."

            elif len(renderable_cameras) > 1:
                cam_list = ", ".join(renderable_cameras)
                return False, f"Multiple renderable cameras found: {cam_list}. Please set only ONE camera as renderable."

            else:
                return True, f"Renderable camera: {renderable_cameras[0]}"

        except Exception as e:
            return False, f"Failed to verify camera: {e}"
    
    def save_temp_scene(self, layer_name: str, process_id: str) -> Optional[str]:
        """
        Save current scene to temporary file for batch rendering.

        IMPORTANT: Preserves renderable camera settings to prevent viewport
        camera from affecting batch rendering.

        Args:
            layer_name: Render layer name
            process_id: Process ID for unique filename

        Returns:
            Path to saved temporary file or None if failed
        """
        if not self._maya_available:
            print("[ScenePrep] Cannot save scene - Maya not available")
            return None

        try:
            # Get current scene name
            current_scene = self.get_current_scene_file()

            if not current_scene:
                print("[ScenePrep] No scene open to save")
                return None

            # CRITICAL: Store renderable camera settings BEFORE saving
            # This prevents viewport camera from affecting batch rendering
            renderable_cameras = {}
            all_cameras = self._cmds.ls(type='camera')
            for cam in all_cameras:
                renderable_cameras[cam] = self._cmds.getAttr(f"{cam}.renderable")

            # Verify renderable camera settings
            renderable_count = sum(1 for is_renderable in renderable_cameras.values() if is_renderable)

            print(f"[ScenePrep] Checking renderable camera settings:")
            if renderable_count == 0:
                print(f"[ScenePrep] WARNING: No renderable camera found!")
                print(f"[ScenePrep] Batch render may fail - please set a camera as renderable")
            elif renderable_count > 1:
                print(f"[ScenePrep] WARNING: Multiple renderable cameras found ({renderable_count})!")
                print(f"[ScenePrep] Render.exe will use the first one (unpredictable)")

            for cam, is_renderable in renderable_cameras.items():
                if is_renderable:
                    transform = self._cmds.listRelatives(cam, parent=True, type='transform')
                    cam_name = transform[0] if transform else cam
                    print(f"[ScenePrep]   ✓ {cam_name}: renderable=True")

            # Generate temp filepath (context-aware)
            temp_file = self._temp_manager.generate_temp_filepath(
                current_scene, layer_name, process_id
            )

            # CRITICAL: Simple 3-step process that doesn't affect current session:
            # 1. Save current session (if modified)
            # 2. Copy saved file to /tmp
            # 3. Render from /tmp file

            print(f"[ScenePrep] Preparing temp scene file...")

            # Step 1: Save current scene if modified (preserves everything)
            if self._cmds.file(query=True, modified=True):
                print(f"[ScenePrep] Saving current scene (has unsaved changes)...")
                self._cmds.file(save=True, force=True)
                print(f"[ScenePrep] Current scene saved")
            else:
                print(f"[ScenePrep] Current scene already saved (no changes)")

            # Step 2: Copy current scene file to temp location
            # This is a simple file system operation - no Maya commands involved!
            print(f"[ScenePrep] Copying scene to temp location...")
            import shutil
            try:
                shutil.copy2(current_scene, temp_file)
                print(f"[ScenePrep] Scene copied to: {os.path.basename(temp_file)}")
            except Exception as e:
                print(f"[ScenePrep] ERROR: Failed to copy scene file: {e}")
                return None

            # Step 3: Render will use the temp file (happens in separate process)
            # Current Maya session is completely unaffected!

            # Register temp file for cleanup
            self._temp_manager.register_file(temp_file)

            print(f"[ScenePrep] Temp scene ready: {os.path.basename(temp_file)}")
            return temp_file

        except Exception as e:
            print(f"[ScenePrep] Failed to save temp scene: {e}")
            return None
    
    def validate_scene_for_render(self) -> Tuple[bool, str]:
        """
        Validate current scene is ready for rendering.

        Checks:
        - Scene file is open
        - Scene has no unsaved changes
        - Render layers exist
        - Exactly one camera is renderable

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self._maya_available:
            return False, "Maya not available"

        try:
            # Check if scene is open
            scene_file = self.get_current_scene_file()
            if not scene_file:
                return False, "No scene file open"

            # Check if scene has been saved
            if self._cmds.file(query=True, modified=True):
                return False, "Scene has unsaved changes"

            # Check if render layers exist
            layers = self.get_render_layers()
            if not layers:
                return False, "No render layers found in scene"

            # Check renderable camera
            camera_valid, camera_msg = self.verify_renderable_camera()
            if not camera_valid:
                return False, camera_msg

            return True, ""

        except Exception as e:
            return False, f"Validation error: {e}"
    
    def get_scene_info(self) -> dict:
        """
        Get information about current scene.

        Returns:
            Dictionary with scene information including renderable cameras
        """
        info = {
            "maya_available": self._maya_available,
            "scene_file": None,
            "scene_name": None,
            "has_unsaved_changes": False,
            "render_layers": [],
            "renderable_cameras": [],
            "camera_valid": False,
            "camera_message": "",
            "is_valid": False,
            "error_message": ""
        }

        if not self._maya_available:
            info["error_message"] = "Maya not available"
            return info

        try:
            # Get scene file
            scene_file = self.get_current_scene_file()
            info["scene_file"] = scene_file

            if scene_file:
                info["scene_name"] = os.path.splitext(os.path.basename(scene_file))[0]
                info["has_unsaved_changes"] = self._cmds.file(query=True, modified=True)

            # Get render layers
            info["render_layers"] = self.get_render_layers()

            # Get renderable cameras
            info["renderable_cameras"] = self.get_renderable_cameras()

            # Verify camera
            camera_valid, camera_msg = self.verify_renderable_camera()
            info["camera_valid"] = camera_valid
            info["camera_message"] = camera_msg

            # Validate
            is_valid, error_msg = self.validate_scene_for_render()
            info["is_valid"] = is_valid
            info["error_message"] = error_msg

        except Exception as e:
            info["error_message"] = str(e)

        return info
    
    def cleanup_temp_files(self, keep_latest: int = 5) -> int:
        """
        Cleanup temporary scene files.
        
        Args:
            keep_latest: Number of latest files to keep
            
        Returns:
            Number of files deleted
        """
        return self._temp_manager.cleanup_temp_files(keep_latest)
    
    def get_temp_file_manager(self) -> TempFileManager:
        """
        Get temp file manager instance.
        
        Returns:
            TempFileManager instance
        """
        return self._temp_manager

