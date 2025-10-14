"""
Maya Helpers Utilities

This module provides Maya-specific helper functions with real Maya API integration
for scene operations, node management, and Maya API interactions.
"""

from typing import List, Dict, Optional, Any, Tuple


class MayaHelpers:
    """
    Maya Helpers utility class for Maya-specific operations.

    Provides real Maya API functions for scene operations,
    node management, and API interactions with graceful fallback when Maya is unavailable.
    """

    def __init__(self):
        """Initialize Maya Helpers with Maya API availability check."""
        self._maya_available = self._check_maya_availability()

    def _check_maya_availability(self) -> bool:
        """Check if Maya is available."""
        try:
            import maya.cmds as cmds
            return True
        except ImportError:
            print("Warning: Maya not available - MayaHelpers will use fallback mode")
            return False
    

    
    def get_scene_lights(self, light_types: Optional[List[str]] = None) -> List[str]:
        """
        Get all lights in the scene using real Maya API.

        Args:
            light_types: Optional list of light types to filter by

        Returns:
            List of light transform node names
        """
        if not self._maya_available:
            print("Maya not available - cannot get scene lights")
            return []

        try:
            import maya.cmds as cmds

            # Default light types if none specified
            if not light_types:
                light_types = [
                    'directionalLight', 'pointLight', 'spotLight', 'areaLight',
                    'aiAreaLight', 'aiSkyDomeLight', 'aiMeshLight', 'volumeLight'
                ]

            lights = []
            for light_type in light_types:
                # Get light shape nodes
                light_shapes = cmds.ls(type=light_type) or []

                for light_shape in light_shapes:
                    # Get the transform node (parent of shape)
                    transforms = cmds.listRelatives(light_shape, parent=True, type='transform') or []
                    if transforms:
                        light_transform = transforms[0]
                        if light_transform not in lights:
                            lights.append(light_transform)

            print(f"Found {len(lights)} lights in Maya scene")
            return lights

        except Exception as e:
            print(f"Error getting scene lights: {e}")
            return []
    
    def get_selected_objects(self) -> List[str]:
        """Get currently selected objects using real Maya API."""
        if not self._maya_available:
            print("Maya not available - cannot get selected objects")
            return []

        try:
            import maya.cmds as cmds
            selected = cmds.ls(selection=True) or []
            print(f"Found {len(selected)} selected objects in Maya")
            return selected

        except Exception as e:
            print(f"Error getting selected objects: {e}")
            return []

    def select_objects(self, object_names: List[str], add: bool = False) -> bool:
        """
        Select objects in Maya using real Maya API.

        Args:
            object_names: List of object names to select
            add: Whether to add to current selection

        Returns:
            Success status
        """
        if not self._maya_available:
            print("Maya not available - cannot select objects")
            return False

        try:
            import maya.cmds as cmds

            # Filter existing objects
            existing_objects = []
            for obj_name in object_names:
                if cmds.objExists(obj_name):
                    existing_objects.append(obj_name)
                else:
                    print(f"Warning: Object '{obj_name}' not found in Maya scene")

            if not existing_objects:
                print("No valid objects to select")
                return False

            # Select objects
            if add:
                cmds.select(existing_objects, add=True)
            else:
                cmds.select(existing_objects, replace=True)

            print(f"Selected {len(existing_objects)} objects in Maya")
            return True

        except Exception as e:
            print(f"Error selecting objects: {e}")
            return False

    def clear_selection(self) -> bool:
        """Clear current selection using real Maya API."""
        if not self._maya_available:
            print("Maya not available - cannot clear selection")
            return False

        try:
            import maya.cmds as cmds
            cmds.select(clear=True)
            print("Cleared Maya selection")
            return True

        except Exception as e:
            print(f"Error clearing selection: {e}")
            return False
    
    def create_group(self, group_name: str, objects: List[str]) -> bool:
        """
        Create group and parent objects to it using real Maya API.

        Args:
            group_name: Name of group to create
            objects: List of objects to group

        Returns:
            Success status
        """
        if not self._maya_available:
            print("Maya not available - cannot create group")
            return False

        try:
            import maya.cmds as cmds

            # Filter existing objects
            existing_objects = []
            for obj_name in objects:
                if cmds.objExists(obj_name):
                    existing_objects.append(obj_name)
                else:
                    print(f"Warning: Object '{obj_name}' not found in Maya scene")

            if not existing_objects:
                # Create empty group
                group = cmds.group(empty=True, name=group_name)
                print(f"Created empty group '{group}'")
                return True

            # Create group with objects
            group = cmds.group(existing_objects, name=group_name)
            print(f"Created group '{group}' with {len(existing_objects)} objects")
            return True

        except Exception as e:
            print(f"Error creating group: {e}")
            return False
    
    def ungroup_objects(self, group_name: str) -> bool:
        """
        Ungroup objects from group using real Maya API.

        Args:
            group_name: Name of group to ungroup

        Returns:
            Success status
        """
        if not self._maya_available:
            print("Maya not available - cannot ungroup objects")
            return False

        try:
            import maya.cmds as cmds

            if not cmds.objExists(group_name):
                print(f"Group '{group_name}' not found in Maya scene")
                return False

            # Get children of the group
            children = cmds.listRelatives(group_name, children=True, type='transform') or []

            if children:
                # Ungroup by parenting children to world
                for child in children:
                    cmds.parent(child, world=True)
                print(f"Ungrouped {len(children)} objects from '{group_name}'")

            # Delete the empty group
            cmds.delete(group_name)
            print(f"Deleted group '{group_name}'")
            return True

        except Exception as e:
            print(f"Error ungrouping objects: {e}")
            return False

    def rename_object(self, old_name: str, new_name: str) -> bool:
        """
        Rename object in Maya using real Maya API.

        Args:
            old_name: Current object name
            new_name: New object name

        Returns:
            Success status
        """
        if not self._maya_available:
            print("Maya not available - cannot rename object")
            return False

        try:
            import maya.cmds as cmds

            if not cmds.objExists(old_name):
                print(f"Object '{old_name}' not found in Maya scene")
                return False

            if cmds.objExists(new_name):
                print(f"Object '{new_name}' already exists in Maya scene")
                return False

            # Rename the object
            result = cmds.rename(old_name, new_name)
            print(f"Renamed '{old_name}' to '{result}' in Maya")
            return True

        except Exception as e:
            print(f"Error renaming object: {e}")
            return False
    
    def get_object_attributes(self, object_name: str,
                            attributes: List[str]) -> Dict[str, Any]:
        """
        Get object attributes using real Maya API.

        Args:
            object_name: Name of object
            attributes: List of attribute names to get

        Returns:
            Dictionary of attribute values
        """
        if not self._maya_available:
            print("Maya not available - cannot get object attributes")
            return {}

        try:
            import maya.cmds as cmds

            if not cmds.objExists(object_name):
                print(f"Object '{object_name}' not found in Maya scene")
                return {}

            result = {}
            for attr in attributes:
                attr_name = f"{object_name}.{attr}"
                if cmds.objExists(attr_name):
                    try:
                        value = cmds.getAttr(attr_name)
                        result[attr] = value
                        print(f"  {attr}: {value}")
                    except Exception as e:
                        print(f"  Warning: Could not get attribute '{attr}': {e}")
                else:
                    print(f"  Warning: Attribute '{attr}' not found on '{object_name}'")

            return result

        except Exception as e:
            print(f"Error getting object attributes: {e}")
            return {}

    def set_object_attributes(self, object_name: str,
                            attributes: Dict[str, Any]) -> bool:
        """
        Set object attributes using real Maya API.

        Args:
            object_name: Name of object
            attributes: Dictionary of attribute name/value pairs

        Returns:
            Success status
        """
        if not self._maya_available:
            print("Maya not available - cannot set object attributes")
            return False

        try:
            import maya.cmds as cmds

            if not cmds.objExists(object_name):
                print(f"Object '{object_name}' not found in Maya scene")
                return False

            success_count = 0
            for attr, value in attributes.items():
                attr_name = f"{object_name}.{attr}"
                if cmds.objExists(attr_name):
                    try:
                        cmds.setAttr(attr_name, value)
                        print(f"  Set {attr}: {value}")
                        success_count += 1
                    except Exception as e:
                        print(f"  Warning: Could not set attribute '{attr}': {e}")
                else:
                    print(f"  Warning: Attribute '{attr}' not found on '{object_name}'")

            return success_count > 0

        except Exception as e:
            print(f"Error setting object attributes: {e}")
            return False
    
    def get_dag_path(self, object_name: str) -> str:
        """
        Get full DAG path for object using real Maya API.

        Args:
            object_name: Name of object

        Returns:
            Full DAG path
        """
        if not self._maya_available:
            return f"|{object_name}"  # Fallback when Maya not available

        try:
            import maya.cmds as cmds

            if not cmds.objExists(object_name):
                return f"|{object_name}"  # Fallback for non-existent objects

            # Get full path
            full_paths = cmds.ls(object_name, long=True)
            if full_paths:
                return full_paths[0]
            else:
                return f"|{object_name}"  # Fallback

        except Exception as e:
            print(f"Error getting DAG path for '{object_name}': {e}")
            return f"|{object_name}"  # Fallback

    def list_relatives(self, object_name: str,
                      children: bool = True,
                      all_descendants: bool = False) -> List[str]:
        """
        List relatives of object using real Maya API.

        Args:
            object_name: Name of object
            children: Whether to list children
            all_descendants: Whether to list all descendants

        Returns:
            List of relative object names
        """
        if not self._maya_available:
            print("Maya not available - cannot list relatives")
            return []

        try:
            import maya.cmds as cmds

            if not cmds.objExists(object_name):
                print(f"Object '{object_name}' not found in Maya scene")
                return []

            relatives = []

            if children:
                if all_descendants:
                    # Get all descendants
                    descendants = cmds.listRelatives(object_name, allDescendents=True, type='transform') or []
                    relatives.extend(descendants)
                else:
                    # Get direct children only
                    direct_children = cmds.listRelatives(object_name, children=True, type='transform') or []
                    relatives.extend(direct_children)

            print(f"Found {len(relatives)} relatives for '{object_name}'")
            return relatives

        except Exception as e:
            print(f"Error listing relatives for '{object_name}': {e}")
            return []
    
    def get_scene_statistics(self) -> Dict[str, Any]:
        """Get scene statistics using real Maya API."""
        if not self._maya_available:
            return {
                "total_nodes": 0,
                "selected_nodes": 0,
                "node_types": {},
                "lights": 0,
                "geometry": 0,
                "groups": 0
            }

        try:
            import maya.cmds as cmds

            # Get all nodes
            all_nodes = cmds.ls() or []
            selected_nodes = cmds.ls(selection=True) or []

            # Count node types
            node_types = {}
            for node in all_nodes:
                node_type = cmds.nodeType(node)
                node_types[node_type] = node_types.get(node_type, 0) + 1

            # Count specific types
            light_types = ['directionalLight', 'pointLight', 'spotLight', 'areaLight',
                          'aiAreaLight', 'aiSkyDomeLight', 'aiMeshLight', 'volumeLight']
            lights = 0
            for light_type in light_types:
                lights += len(cmds.ls(type=light_type) or [])

            geometry = len(cmds.ls(type='mesh') or [])
            groups = len(cmds.ls(type='transform') or [])

            return {
                "total_nodes": len(all_nodes),
                "selected_nodes": len(selected_nodes),
                "node_types": node_types,
                "lights": lights,
                "geometry": geometry,
                "groups": groups
            }

        except Exception as e:
            print(f"Error getting scene statistics: {e}")
            return {
                "total_nodes": 0,
                "selected_nodes": 0,
                "node_types": {},
                "lights": 0,
                "geometry": 0,
                "groups": 0
            }
    
    def save_scene(self, file_path: str, file_type: str = "mayaAscii") -> bool:
        """
        Save Maya scene using real Maya API.

        Args:
            file_path: Path to save file
            file_type: File type (mayaAscii, mayaBinary)

        Returns:
            Success status
        """
        if not self._maya_available:
            print("Maya not available - cannot save scene")
            return False

        try:
            import maya.cmds as cmds
            import os

            # Ensure directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            # Save the scene
            cmds.file(rename=file_path)
            cmds.file(save=True, type=file_type)

            print(f"Scene saved successfully to '{file_path}'")
            print(f"  File type: {file_type}")
            return True

        except Exception as e:
            print(f"Error saving scene: {e}")
            return False

    def open_scene(self, file_path: str, force: bool = False) -> bool:
        """
        Open Maya scene using real Maya API.

        Args:
            file_path: Path to scene file
            force: Whether to force open without saving current scene

        Returns:
            Success status
        """
        if not self._maya_available:
            print("Maya not available - cannot open scene")
            return False

        try:
            import maya.cmds as cmds
            import os

            if not os.path.exists(file_path):
                print(f"Scene file not found: '{file_path}'")
                return False

            # Open the scene
            cmds.file(file_path, open=True, force=force)

            print(f"Scene opened successfully: '{file_path}'")
            print(f"  Force open: {force}")
            return True

        except Exception as e:
            print(f"Error opening scene: {e}")
            return False
    



# Convenience functions
def get_selected() -> List[str]:
    """Convenience function to get selected objects."""
    maya_helpers = MayaHelpers()
    return maya_helpers.get_selected_objects()


def select_lights(light_types: Optional[List[str]] = None) -> List[str]:
    """Convenience function to select all lights."""
    maya_helpers = MayaHelpers()
    lights = maya_helpers.get_scene_lights(light_types)
    maya_helpers.select_objects(lights)
    return lights


def rename_selected(name_pattern: str) -> List[str]:
    """Convenience function to rename selected objects."""
    maya_helpers = MayaHelpers()
    selected = maya_helpers.get_selected_objects()
    renamed = []
    
    for i, obj in enumerate(selected, 1):
        new_name = name_pattern.replace("#", f"{i:03d}")
        if maya_helpers.rename_object(obj, new_name):
            renamed.append(new_name)
    
    return renamed
