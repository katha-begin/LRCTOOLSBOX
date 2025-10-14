"""
Light Importer

This module provides light-only import functionality for Maya scenes,
preserving light attributes and hierarchy while filtering out non-light objects.
"""

import os
from typing import List, Dict, Optional, Any, Tuple

from .base_importer import BaseImporter, ImportResult, ImportMode
from ..core.models import ImportOptions, LightInfo


class LightImporter(BaseImporter):
    """
    Light-only importer for Maya scenes.
    
    Imports only lights from Maya scene files, preserving light attributes
    and hierarchy while filtering out other scene objects.
    """
    
    def __init__(self):
        """Initialize light importer."""
        super().__init__()
        self._supported_extensions = ['.ma', '.mb']
        self._light_types = ['directionalLight', 'pointLight', 'spotLight', 'areaLight',
                           'aiAreaLight', 'aiSkyDomeLight', 'aiMeshLight']
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return self._supported_extensions.copy()
    
    def import_file(self, file_path: str, options: ImportOptions) -> ImportResult:
        """
        Import lights only from Maya scene file.
        
        Args:
            file_path: Path to Maya scene file
            options: Import options
            
        Returns:
            ImportResult with imported light details
        """
        # Reset cancellation flag
        self._cancel_requested = False
        
        # Validate inputs
        is_valid, error_msg = self._validate_file_path(file_path)
        if not is_valid:
            return ImportResult(False, error_msg)
        
        is_valid, error_msg = self._validate_import_options(options)
        if not is_valid:
            return ImportResult(False, error_msg)
        
        if not self.can_import_file(file_path):
            return ImportResult(False, f"Unsupported file type: {file_path}")
        
        if not self._maya_available:
            return ImportResult(False, "Maya is not available")
        
        try:
            import maya.cmds as cmds
            
            # Report progress
            if not self._report_progress(0.1, "Starting light import..."):
                return ImportResult(False, "Import cancelled by user")
            
            # Create namespace if needed
            if options.namespace:
                if not self._create_namespace_if_needed(options.namespace):
                    return ImportResult(False, f"Failed to create namespace: {options.namespace}")
            
            if not self._report_progress(0.2, "Analyzing source file..."):
                return ImportResult(False, "Import cancelled by user")
            
            # Import the entire file to a temporary namespace first
            temp_namespace = f"temp_light_import_{int(datetime.now().timestamp())}"
            
            try:
                # Import to temporary namespace
                imported_nodes = cmds.file(file_path, i=True,
                                         namespace=temp_namespace,
                                         returnNewNodes=True)
                
                if not self._report_progress(0.5, "Filtering lights..."):
                    return ImportResult(False, "Import cancelled by user")
                
                # Find all lights in the temporary namespace
                light_transforms = []
                light_shapes = []
                
                for light_type in self._light_types:
                    shapes = cmds.ls(f"{temp_namespace}:*", type=light_type) or []
                    for shape in shapes:
                        # Get the transform node
                        transforms = cmds.listRelatives(shape, parent=True, fullPath=True) or []
                        if transforms:
                            light_transforms.append(transforms[0])
                            light_shapes.append(shape)
                
                if not light_transforms:
                    # Clean up temporary namespace
                    if cmds.namespace(exists=temp_namespace):
                        cmds.namespace(removeNamespace=temp_namespace, deleteNamespaceContent=True)
                    return ImportResult(False, "No lights found in source file")
                
                if not self._report_progress(0.7, f"Processing {len(light_transforms)} lights..."):
                    return ImportResult(False, "Import cancelled by user")
                
                # Move lights to target namespace or root
                final_lights = []
                target_namespace = options.namespace or ""
                
                for light_transform in light_transforms:
                    try:
                        # Get the light name without namespace
                        light_name = light_transform.split(":")[-1]
                        
                        # Determine final name
                        if target_namespace:
                            final_name = f"{target_namespace}:{light_name}"
                        else:
                            final_name = light_name
                        
                        # Ensure unique name
                        if cmds.objExists(final_name):
                            counter = 1
                            base_name = final_name
                            while cmds.objExists(final_name):
                                if target_namespace:
                                    final_name = f"{target_namespace}:{light_name}_{counter:02d}"
                                else:
                                    final_name = f"{light_name}_{counter:02d}"
                                counter += 1
                        
                        # Parent to world and rename
                        cmds.parent(light_transform, world=True)
                        renamed_light = cmds.rename(light_transform, final_name)
                        
                        # Move to target namespace if specified
                        if target_namespace and not renamed_light.startswith(f"{target_namespace}:"):
                            try:
                                cmds.rename(renamed_light, f"{target_namespace}:{renamed_light}")
                                renamed_light = f"{target_namespace}:{renamed_light}"
                            except Exception as e:
                                print(f"Warning: Could not move light to namespace: {e}")
                        
                        final_lights.append(renamed_light)
                        
                    except Exception as e:
                        print(f"Warning: Could not process light {light_transform}: {e}")
                
                # Clean up temporary namespace
                try:
                    if cmds.namespace(exists=temp_namespace):
                        cmds.namespace(removeNamespace=temp_namespace, deleteNamespaceContent=True)
                except Exception as e:
                    print(f"Warning: Could not clean up temporary namespace: {e}")
                
                if not self._report_progress(0.9, "Finalizing light import..."):
                    pass  # Don't cancel at this point
                
                # Apply post-import options
                warnings = []
                if options.select_imported and final_lights:
                    try:
                        existing_lights = [light for light in final_lights if cmds.objExists(light)]
                        if existing_lights:
                            cmds.select(existing_lights)
                    except Exception as e:
                        warnings.append(f"Could not select imported lights: {e}")
                
                self._report_progress(1.0, "Light import completed")
                
                success_msg = f"Successfully imported {len(final_lights)} lights from {os.path.basename(file_path)}"
                return ImportResult(True, success_msg, final_lights, warnings)
                
            except Exception as e:
                # Clean up temporary namespace on error
                try:
                    if cmds.namespace(exists=temp_namespace):
                        cmds.namespace(removeNamespace=temp_namespace, deleteNamespaceContent=True)
                except:
                    pass
                
                return ImportResult(False, f"Light import failed: {str(e)}")
                
        except Exception as e:
            return ImportResult(False, f"Light import error: {str(e)}")
    
    def get_lights_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Analyze file and return information about lights without importing.
        
        Args:
            file_path: Path to Maya scene file
            
        Returns:
            List of dictionaries with light information
        """
        if not self._maya_available:
            return []
        
        try:
            import maya.cmds as cmds
            
            # Create temporary namespace for analysis
            temp_namespace = f"analyze_lights_{int(datetime.now().timestamp())}"
            
            try:
                # Import to temporary namespace
                cmds.file(file_path, i=True, namespace=temp_namespace)
                
                # Find all lights
                lights_info = []
                for light_type in self._light_types:
                    shapes = cmds.ls(f"{temp_namespace}:*", type=light_type) or []
                    for shape in shapes:
                        transforms = cmds.listRelatives(shape, parent=True, fullPath=True) or []
                        if transforms:
                            light_name = transforms[0].split(":")[-1]
                            lights_info.append({
                                'name': light_name,
                                'type': light_type,
                                'shape': shape.split(":")[-1]
                            })
                
                return lights_info
                
            finally:
                # Clean up temporary namespace
                if cmds.namespace(exists=temp_namespace):
                    cmds.namespace(removeNamespace=temp_namespace, deleteNamespaceContent=True)
                
        except Exception as e:
            print(f"Error analyzing lights in file: {e}")
            return []
