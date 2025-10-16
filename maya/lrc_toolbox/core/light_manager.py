"""
Light Manager

This module provides enhanced light management functionality with real Maya API
integration for scene light listing, pattern-based naming, and context-aware operations.
"""

import re
import random
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

from .models import (
    LightInfo, NavigationContext, ProjectType
)


class LightManager:
    """
    Enhanced Light Manager for handling light operations and naming.

    Provides real Maya scene light listing, pattern-based naming preview generation,
    context-aware naming pattern support, and light import/export operations.
    """

    def __init__(self):
        """Initialize Light Manager with Maya integration."""
        self._maya_available = self._check_maya_availability()
        self._light_types = ["KEY", "FILL", "RIM", "BOUNCE", "AMBIENT", "SPEC"]
        self._hierarchy_levels = ["Master", "Key", "Child"]

    def _check_maya_availability(self) -> bool:
        """Check if Maya is available."""
        try:
            import maya.cmds as cmds
            return True
        except ImportError:
            print("Warning: Maya not available - using fallback mode")
            return False
    

    
    def get_scene_lights(self) -> List[LightInfo]:
        """Get all lights in the current scene with real Maya API."""
        if self._maya_available:
            try:
                import maya.cmds as cmds

                # Get all light transforms in the scene
                lights = []
                light_types = ['directionalLight', 'pointLight', 'spotLight', 'areaLight',
                              'aiAreaLight', 'aiSkyDomeLight', 'aiMeshLight']

                for light_type in light_types:
                    light_shapes = cmds.ls(type=light_type) or []
                    for light_shape in light_shapes:
                        # Get the transform node
                        transforms = cmds.listRelatives(light_shape, parent=True, type='transform') or []
                        if transforms:
                            light_transform = transforms[0]

                            # Extract light info from Maya
                            light_info = self._extract_light_info(light_transform, light_shape)
                            if light_info:
                                lights.append(light_info)

                print(f"Found {len(lights)} lights in Maya scene")
                return lights

            except Exception as e:
                print(f"Error getting scene lights from Maya: {e}")
                return []
        else:
            print("Warning: Maya API not available - no lights can be retrieved")
            return []

    def get_selected_lights(self) -> List[LightInfo]:
        """Get currently selected lights with real Maya API."""
        if self._maya_available:
            try:
                import maya.cmds as cmds

                selected = cmds.ls(selection=True, transforms=True) or []
                selected_lights = []

                for obj in selected:
                    # Check if this transform has a light shape
                    shapes = cmds.listRelatives(obj, shapes=True, type=['directionalLight', 'pointLight',
                                                                       'spotLight', 'areaLight', 'aiAreaLight',
                                                                       'aiSkyDomeLight', 'aiMeshLight']) or []
                    if shapes:
                        light_info = self._extract_light_info(obj, shapes[0])
                        if light_info:
                            light_info.is_selected = True
                            selected_lights.append(light_info)

                return selected_lights

            except Exception as e:
                print(f"Error getting selected lights from Maya: {e}")
                return []
        else:
            # No Maya API available
            return []
    
    def get_lights_by_hierarchy(self, hierarchy_level: str) -> List[LightInfo]:
        """Get lights by hierarchy level (Master, Key, Child)."""
        all_lights = self.get_scene_lights()
        return [light for light in all_lights if light.hierarchy_level == hierarchy_level]

    def get_lights_by_type(self, light_type: str) -> List[LightInfo]:
        """Get lights by type (KEY, FILL, RIM, etc.)."""
        all_lights = self.get_scene_lights()
        return [light for light in all_lights if light.light_type == light_type]
    
    def generate_light_name(self, hierarchy_level: str, light_type: str, 
                          index: int, context: Optional[NavigationContext] = None) -> str:
        """
        Generate light name following hierarchical naming convention.
        
        Args:
            hierarchy_level: Master, Key, or Child
            light_type: KEY, FILL, RIM, etc.
            index: Light index number
            context: Navigation context for prefix generation
            
        Returns:
            Formatted light name following convention
        """
        index_str = f"{index:03d}"
        
        if hierarchy_level == "Master":
            return f"MASTER_{light_type}_{index_str}"
        
        elif hierarchy_level == "Key":
            prefix = self._get_context_prefix(context) if context else "SH0010"
            return f"{prefix}_{light_type}_{index_str}"
        
        else:  # Child
            prefix = self._get_context_prefix(context) if context else "SH0010"
            sub_type = self._get_child_sub_type(light_type)
            return f"{prefix}_{light_type}_{sub_type}_{index_str}"
    
    def rename_lights_with_pattern(self, lights: List[LightInfo],
                                 hierarchy_level: str, light_type: str,
                                 context: Optional[NavigationContext] = None) -> List[str]:
        """
        Rename lights using hierarchical naming pattern with real Maya API.

        Args:
            lights: List of lights to rename
            hierarchy_level: Target hierarchy level
            light_type: Target light type
            context: Navigation context for naming

        Returns:
            List of new light names
        """
        new_names = []

        if self._maya_available:
            try:
                import maya.cmds as cmds

                for i, light in enumerate(lights, 1):
                    new_name = self.generate_light_name(hierarchy_level, light_type, i, context)

                    # Check if light exists in Maya scene
                    if cmds.objExists(light.name):
                        # Rename the light in Maya
                        try:
                            cmds.rename(light.name, new_name)
                            print(f"Renamed '{light.name}' to '{new_name}' in Maya scene")
                        except Exception as e:
                            print(f"Warning: Could not rename '{light.name}' to '{new_name}': {e}")
                            # Use original name if rename failed
                            new_name = light.name
                    else:
                        print(f"Warning: Light '{light.name}' not found in Maya scene")

                    new_names.append(new_name)

                return new_names

            except Exception as e:
                print(f"Error renaming lights with Maya API: {e}")
                return []
        else:
            print("Warning: Maya API not available - cannot rename lights")
            return []
    
    def create_light_group(self, group_name: str, lights: List[LightInfo]) -> bool:
        """Create light group with specified lights using real Maya API."""
        if self._maya_available:
            try:
                import maya.cmds as cmds

                # Check if group already exists
                if cmds.objExists(group_name):
                    print(f"Warning: Group '{group_name}' already exists")
                    return False

                # Get light names that exist in Maya
                existing_lights = []
                for light in lights:
                    if cmds.objExists(light.name):
                        existing_lights.append(light.name)
                    else:
                        print(f"Warning: Light '{light.name}' not found in Maya scene")

                if not existing_lights:
                    print(f"Error: No valid lights found to group")
                    return False

                # Create group and add lights
                group_node = cmds.group(existing_lights, name=group_name)
                print(f"Created light group '{group_node}' with {len(existing_lights)} lights")

                for light_name in existing_lights:
                    print(f"  - Added '{light_name}' to group")

                return True

            except Exception as e:
                print(f"Error creating light group with Maya API: {e}")
                return False
        else:
            print("Warning: Maya API not available - cannot create light groups")
            return False
    
    def ungroup_lights(self, lights: List[LightInfo]) -> bool:
        """Remove lights from their current groups using real Maya API."""
        if self._maya_available:
            try:
                import maya.cmds as cmds

                ungrouped_count = 0
                for light in lights:
                    if cmds.objExists(light.name):
                        # Get parent groups
                        parents = cmds.listRelatives(light.name, parent=True, type='transform') or []

                        for parent in parents:
                            # Check if parent is a group (has no shape children)
                            shapes = cmds.listRelatives(parent, shapes=True) or []
                            if not shapes:  # It's a group
                                try:
                                    # Unparent the light from the group
                                    cmds.parent(light.name, world=True)
                                    print(f"  - Removed '{light.name}' from group '{parent}'")
                                    ungrouped_count += 1
                                    break
                                except Exception as e:
                                    print(f"Warning: Could not ungroup '{light.name}': {e}")
                    else:
                        print(f"Warning: Light '{light.name}' not found in Maya scene")

                print(f"Ungrouped {ungrouped_count} lights")
                return ungrouped_count > 0

            except Exception as e:
                print(f"Error ungrouping lights with Maya API: {e}")
                return False
        else:
            print("Warning: Maya API not available - cannot ungroup lights")
            return False
    
    def get_light_groups(self) -> Dict[str, List[LightInfo]]:
        """Get all light groups and their members using real Maya API."""
        groups = {}

        if self._maya_available:
            try:
                import maya.cmds as cmds

                # Get all lights in scene
                lights = self.get_scene_lights()

                # Group lights by their parent groups (if any)
                for light in lights:
                    if light.group_name:
                        if light.group_name not in groups:
                            groups[light.group_name] = []
                        groups[light.group_name].append(light)

                return groups

            except Exception as e:
                print(f"Error getting light groups from Maya: {e}")
                return {}
        else:
            print("Warning: Maya API not available - cannot get light groups")
            return {}
    
    def generate_group_name(self, light_type: str, context: Optional[NavigationContext] = None) -> str:
        """Generate group name following naming convention."""
        prefix = self._get_context_prefix(context) if context else "MASTER"
        return f"{prefix}_{light_type}_GROUP"
    
    def import_lights_from_template(self, template_path: str,
                                  import_mode: str = "additive") -> List[LightInfo]:
        """Import lights from template with real file operations."""
        print(f"Importing lights from template '{template_path}'")
        print(f"  - Import mode: {import_mode}")

        imported_lights = []

        try:
            # Check if template file exists
            if not os.path.exists(template_path):
                print(f"  - Template file not found: {template_path}")
                return imported_lights

            # Try Maya API import if available
            if self._maya_available:
                try:
                    import maya.cmds as cmds

                    # Import the template file
                    if import_mode == "replace":
                        # Delete existing lights first
                        existing_lights = cmds.ls(type=["directionalLight", "pointLight", "spotLight", "areaLight"])
                        if existing_lights:
                            transforms = []
                            for light in existing_lights:
                                transform = cmds.listRelatives(light, parent=True, type="transform")
                                if transform:
                                    transforms.extend(transform)
                            if transforms:
                                cmds.delete(transforms)

                    # Import lights from template
                    cmds.file(template_path, i=True, type="mayaAscii",
                             ignoreVersion=True, mergeNamespacesOnClash=False,
                             namespace=":", preserveReferences=True)

                    # Get the imported lights
                    imported_lights = self.get_scene_lights()
                    print(f"  - Successfully imported {len(imported_lights)} lights")

                except Exception as e:
                    print(f"  - Error with Maya API import: {e}")
                    print(f"  - Template file exists but could not be imported")
            else:
                print(f"  - Maya API not available, template import requires Maya")

        except Exception as e:
            print(f"  - Error importing lights: {e}")

        return imported_lights
    
    def export_lights_to_template(self, lights: List[LightInfo],
                                template_path: str) -> bool:
        """Export lights to template with real file operations."""
        print(f"Exporting {len(lights)} lights to template '{template_path}'")

        try:
            # Ensure template directory exists
            template_dir = os.path.dirname(template_path)
            if template_dir:
                os.makedirs(template_dir, exist_ok=True)

            # Try Maya API export if available
            if self._maya_available:
                try:
                    import maya.cmds as cmds

                    # Select the lights to export
                    light_transforms = []
                    for light in lights:
                        if hasattr(light, 'maya_transform_node') and light.maya_transform_node:
                            if cmds.objExists(light.maya_transform_node):
                                light_transforms.append(light.maya_transform_node)
                                print(f"  - Preparing light '{light.name}' for export")

                    if light_transforms:
                        # Select the lights
                        cmds.select(light_transforms, replace=True)

                        # Export selected lights
                        cmds.file(template_path, exportSelected=True, type="mayaAscii",
                                 force=True, preserveReferences=False)

                        print(f"  - Successfully exported {len(light_transforms)} lights to: {template_path}")
                        return True
                    else:
                        print(f"  - No valid lights found to export")
                        return False

                except Exception as e:
                    print(f"  - Error with Maya API export: {e}")
                    return False
            else:
                print(f"  - Maya API not available, light export requires Maya")
                return False

        except Exception as e:
            print(f"  - Error exporting lights: {e}")
            return False
    
    def validate_light_naming(self, light_name: str) -> Tuple[bool, str]:
        """Validate light name against naming conventions."""
        # Check for basic pattern: PREFIX_TYPE_INDEX or PREFIX_TYPE_SUBTYPE_INDEX
        pattern1 = re.compile(r'^[A-Z0-9]+_[A-Z]+_\d{3}$')  # Master/Key pattern
        pattern2 = re.compile(r'^[A-Z0-9]+_[A-Z]+_[A-Z]+_\d{3}$')  # Child pattern
        
        if pattern1.match(light_name) or pattern2.match(light_name):
            return True, "Valid naming convention"
        else:
            return False, "Invalid naming convention. Expected: PREFIX_TYPE_INDEX or PREFIX_TYPE_SUBTYPE_INDEX"
    
    def get_naming_suggestions(self, current_name: str, 
                             context: Optional[NavigationContext] = None) -> List[str]:
        """Get naming suggestions for a light."""
        suggestions = []
        
        # Extract components from current name
        parts = current_name.split('_')
        if len(parts) >= 2:
            light_type = parts[-2] if parts[-1].isdigit() else parts[-1]
            
            # Generate suggestions for different hierarchy levels
            for hierarchy in self._hierarchy_levels:
                suggestion = self.generate_light_name(hierarchy, light_type, 1, context)
                suggestions.append(suggestion)
        
        return suggestions
    
    def _get_context_prefix(self, context: NavigationContext) -> str:
        """Get prefix from navigation context."""
        if context.type == ProjectType.SHOT:
            return context.shot
        else:
            return context.asset.upper()
    
    def _get_child_sub_type(self, light_type: str) -> str:
        """Get sub-type for child lights."""
        sub_types = {
            "KEY": "RIM",
            "FILL": "BOUNCE",
            "RIM": "EDGE",
            "BOUNCE": "SOFT",
            "AMBIENT": "ENV",
            "SPEC": "HIGHLIGHT"
        }
        return sub_types.get(light_type, "SUB")
    
    def _generate_group_name(self, light_name: str) -> Optional[str]:
        """Generate group name from light name."""
        parts = light_name.split('_')
        if len(parts) >= 2:
            prefix = parts[0]
            light_type = parts[1]
            return f"{prefix}_{light_type}_GROUP"
        return None
    
    def get_light_statistics(self) -> Dict[str, Any]:
        """Get light statistics for the scene using real Maya API."""
        if self._maya_available:
            try:
                lights = self.get_scene_lights()

                hierarchy_counts = {}
                type_counts = {}

                for light in lights:
                    hierarchy_counts[light.hierarchy_level] = hierarchy_counts.get(light.hierarchy_level, 0) + 1
                    type_counts[light.light_type] = type_counts.get(light.light_type, 0) + 1

                return {
                    "total_lights": len(lights),
                    "hierarchy_breakdown": hierarchy_counts,
                    "type_breakdown": type_counts,
                    "grouped_lights": len([l for l in lights if l.group_name]),
                    "ungrouped_lights": len([l for l in lights if not l.group_name])
                }

            except Exception as e:
                print(f"Error getting light statistics from Maya: {e}")
                return {
                    "total_lights": 0,
                    "hierarchy_breakdown": {},
                    "type_breakdown": {},
                    "grouped_lights": 0,
                    "ungrouped_lights": 0
                }
        else:
            print("Warning: Maya API not available - cannot get light statistics")
            return {
                "total_lights": 0,
                "hierarchy_breakdown": {},
                "type_breakdown": {},
                "grouped_lights": 0,
                "ungrouped_lights": 0
            }

    def _extract_light_info(self, light_transform: str, light_shape: str) -> Optional[LightInfo]:
        """Extract light information from Maya light nodes."""
        if not self._maya_available:
            return None

        try:
            import maya.cmds as cmds

            # Get light name and type
            light_name = light_transform
            maya_light_type = cmds.nodeType(light_shape)

            # Map Maya light types to our categories
            type_mapping = {
                'directionalLight': 'KEY',
                'pointLight': 'FILL',
                'spotLight': 'KEY',
                'areaLight': 'KEY',
                'aiAreaLight': 'KEY',
                'aiSkyDomeLight': 'AMBIENT',
                'aiMeshLight': 'KEY'
            }

            light_type = type_mapping.get(maya_light_type, 'KEY')

            # Try to extract hierarchy from naming convention
            hierarchy_level = self._extract_hierarchy_from_name(light_name)

            # Try to extract index from naming convention
            index = self._extract_index_from_name(light_name)

            # Get transform data
            transform_data = self._get_light_transform_data(light_transform)

            # Get light attributes
            light_attributes = self._get_light_attributes(light_shape)

            return LightInfo(
                name=light_name,
                light_type=light_type,
                hierarchy_level=hierarchy_level,
                index=index,
                created_date=datetime.now(),
                is_selected=False,
                group_name=self._generate_group_name(light_name),
                transform_data=transform_data,
                light_attributes=light_attributes,
                maya_shape_node=light_shape,
                maya_transform_node=light_transform
            )

        except Exception as e:
            print(f"Warning: Could not extract light info for {light_transform}: {e}")
            return None



    def _extract_hierarchy_from_name(self, light_name: str) -> str:
        """Extract hierarchy level from light name."""
        if light_name.startswith('MASTER_'):
            return 'Master'
        elif '_' in light_name and len(light_name.split('_')) >= 3:
            return 'Key'
        elif len(light_name.split('_')) >= 4:
            return 'Child'
        else:
            return 'Key'  # Default

    def _extract_index_from_name(self, light_name: str) -> int:
        """Extract index number from light name."""
        parts = light_name.split('_')
        for part in reversed(parts):
            if part.isdigit():
                return int(part)
        return 1  # Default

    def _get_light_transform_data(self, light_transform: str) -> Dict[str, float]:
        """Get transform data from Maya light."""
        try:
            import maya.cmds as cmds

            return {
                'translateX': cmds.getAttr(f"{light_transform}.translateX"),
                'translateY': cmds.getAttr(f"{light_transform}.translateY"),
                'translateZ': cmds.getAttr(f"{light_transform}.translateZ"),
                'rotateX': cmds.getAttr(f"{light_transform}.rotateX"),
                'rotateY': cmds.getAttr(f"{light_transform}.rotateY"),
                'rotateZ': cmds.getAttr(f"{light_transform}.rotateZ"),
                'scaleX': cmds.getAttr(f"{light_transform}.scaleX"),
                'scaleY': cmds.getAttr(f"{light_transform}.scaleY"),
                'scaleZ': cmds.getAttr(f"{light_transform}.scaleZ")
            }
        except:
            return {}

    def _get_light_attributes(self, light_shape: str) -> Dict[str, Any]:
        """Get light-specific attributes from Maya light."""
        try:
            import maya.cmds as cmds

            attributes = {}

            # Common light attributes
            common_attrs = ['intensity', 'color']

            for attr in common_attrs:
                full_attr = f"{light_shape}.{attr}"
                if cmds.attributeQuery(attr, node=light_shape, exists=True):
                    try:
                        value = cmds.getAttr(full_attr)
                        attributes[attr] = value
                    except:
                        pass

            return attributes
        except:
            return {}
