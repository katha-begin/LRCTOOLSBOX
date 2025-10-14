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
    
    def save_temp_scene(self, layer_name: str, process_id: str) -> Optional[str]:
        """
        Save current scene to temporary file for batch rendering.
        
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
            
            scene_name = os.path.splitext(os.path.basename(current_scene))[0]
            
            # Generate temp filename
            temp_file = self._temp_manager.generate_temp_filename(
                scene_name, layer_name, process_id
            )
            
            # Save scene as Maya ASCII
            self._cmds.file(rename=temp_file)
            self._cmds.file(save=True, type='mayaAscii')
            
            # Restore original scene name
            self._cmds.file(rename=current_scene)
            
            # Register temp file
            self._temp_manager.register_file(temp_file)
            
            print(f"[ScenePrep] Saved temp scene: {os.path.basename(temp_file)}")
            return temp_file
            
        except Exception as e:
            print(f"[ScenePrep] Failed to save temp scene: {e}")
            return None
    
    def validate_scene_for_render(self) -> Tuple[bool, str]:
        """
        Validate current scene is ready for rendering.
        
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
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def get_scene_info(self) -> dict:
        """
        Get information about current scene.
        
        Returns:
            Dictionary with scene information
        """
        info = {
            "maya_available": self._maya_available,
            "scene_file": None,
            "scene_name": None,
            "has_unsaved_changes": False,
            "render_layers": [],
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

