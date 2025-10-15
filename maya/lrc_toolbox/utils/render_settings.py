# -*- coding: utf-8 -*-
"""
Render Settings Utilities

Functions for reading and parsing Maya render settings.
"""

import os
import re
from typing import Optional, Tuple


def get_render_output_path(scene_file: str, layer_name: str) -> Optional[str]:
    """
    Get the render output path from scene file's render settings.
    
    Parses the filename prefix from render settings and constructs
    the absolute output directory path.
    
    Args:
        scene_file: Path to Maya scene file
        layer_name: Render layer name
    
    Returns:
        Absolute output directory path, or None if not found
    
    Example:
        Input: W:/SWA/all/scene/Ep01/sq0040/SH0200/lighting/publish/v005/<RenderLayer>/<RenderLayer>/<RenderLayer>.####.ext
        Output: W:/SWA/all/scene/Ep01/sq0040/SH0200/lighting/publish/v005/MASTER_CHAR_A/MASTER_CHAR_A
    """
    try:
        import maya.cmds as cmds
        
        # Get current scene to restore later
        current_scene = cmds.file(query=True, sceneName=True)
        
        # Open the scene file (quietly)
        cmds.file(scene_file, open=True, force=True, ignoreVersion=True)
        
        # Get filename prefix from render settings
        # This is the path template with <RenderLayer> tokens
        filename_prefix = cmds.getAttr("defaultRenderGlobals.imageFilePrefix")
        
        # Restore original scene
        if current_scene:
            cmds.file(current_scene, open=True, force=True, ignoreVersion=True)
        
        if not filename_prefix:
            print("[RenderSettings] No filename prefix found in render settings")
            return None
        
        print(f"[RenderSettings] Filename prefix: {filename_prefix}")
        
        # Replace <RenderLayer> tokens with actual layer name
        output_path = filename_prefix.replace("<RenderLayer>", layer_name)
        
        # Remove filename part (everything after last /)
        if "/" in output_path or "\\" in output_path:
            output_path = os.path.dirname(output_path)
        
        # Make absolute path
        if not os.path.isabs(output_path):
            # Relative to scene file directory
            scene_dir = os.path.dirname(scene_file)
            output_path = os.path.join(scene_dir, output_path)
        
        # Normalize path
        output_path = os.path.normpath(output_path)
        
        print(f"[RenderSettings] Output path: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"[RenderSettings] Error getting output path: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_filename_prefix_from_file(scene_file: str) -> Optional[str]:
    """
    Parse filename prefix directly from scene file without opening it.
    
    This is faster but less reliable than opening the scene.
    
    Args:
        scene_file: Path to Maya scene file (.ma or .mb)
    
    Returns:
        Filename prefix string, or None if not found
    """
    try:
        # Only works with .ma (ASCII) files
        if not scene_file.endswith('.ma'):
            return None
        
        with open(scene_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Look for imageFilePrefix attribute
                if 'imageFilePrefix' in line:
                    # Extract value from: setAttr ".imageFilePrefix" -type "string" "path/to/output";
                    match = re.search(r'imageFilePrefix.*?"([^"]+)"', line)
                    if match:
                        return match.group(1)
        
        return None
        
    except Exception as e:
        print(f"[RenderSettings] Error parsing file: {e}")
        return None


def construct_output_path_from_scene(scene_file: str, layer_name: str) -> str:
    """
    Construct output path based on scene file location and layer name.
    
    Follows the pattern:
    {scene_dir}/publish/{version}/<RenderLayer>/<RenderLayer>
    
    Args:
        scene_file: Path to scene file
        layer_name: Render layer name
    
    Returns:
        Constructed output path
    
    Example:
        Input: W:/SWA/all/scene/Ep01/sq0040/SH0200/lighting/version/file_v005.ma
        Output: W:/SWA/all/scene/Ep01/sq0040/SH0200/lighting/publish/v005/MASTER_CHAR_A/MASTER_CHAR_A
    """
    scene_dir = os.path.dirname(scene_file)
    scene_name = os.path.basename(scene_file)
    
    # Extract version from filename (e.g., v005)
    version_match = re.search(r'_v(\d{3,4})', scene_name)
    version = f"v{version_match.group(1)}" if version_match else "v001"
    
    # Replace 'version' with 'publish' in path
    if '/version/' in scene_dir or '\\version\\' in scene_dir:
        publish_dir = scene_dir.replace('/version/', '/publish/').replace('\\version\\', '\\publish\\')
    else:
        # Fallback: use scene_dir/publish
        publish_dir = os.path.join(scene_dir, 'publish')
    
    # Construct full output path
    output_path = os.path.join(publish_dir, version, layer_name, layer_name)
    output_path = os.path.normpath(output_path)
    
    return output_path


def get_output_directory(scene_file: str, layer_name: str) -> str:
    """
    Get the output directory for renders.
    
    Tries multiple methods in order:
    1. Read from render settings (most accurate)
    2. Parse from scene file directly (fast)
    3. Construct from scene path (fallback)
    
    Args:
        scene_file: Path to scene file
        layer_name: Render layer name
    
    Returns:
        Output directory path
    """
    # Method 1: Read from render settings (requires opening scene)
    output_path = get_render_output_path(scene_file, layer_name)
    if output_path:
        return output_path
    
    # Method 2: Parse from file (fast but only works with .ma)
    filename_prefix = parse_filename_prefix_from_file(scene_file)
    if filename_prefix:
        output_path = filename_prefix.replace("<RenderLayer>", layer_name)
        if "/" in output_path or "\\" in output_path:
            output_path = os.path.dirname(output_path)
        if not os.path.isabs(output_path):
            scene_dir = os.path.dirname(scene_file)
            output_path = os.path.join(scene_dir, output_path)
        return os.path.normpath(output_path)
    
    # Method 3: Construct from scene path (fallback)
    return construct_output_path_from_scene(scene_file, layer_name)

