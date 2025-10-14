"""
Render Setup API

This module provides render setup management functionality with real Maya API
integration for render layer creation, template operations, and render setup import/export.
"""

import json
import os
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

from .models import (
    RenderLayerInfo, RenderLayerElement, RenderLayerVariance,
    NavigationContext, TemplateInfo, ImportOptions, ExportOptions
)


class RenderSetupAPI:
    """
    Render Setup API for handling Maya render setup operations.

    Provides real Maya Render Setup integration for render layer creation and management,
    template creation and application, and render setup import/export functionality.
    """

    def __init__(self):
        """Initialize Render Setup API with Maya integration."""
        self._maya_available = self._check_maya_availability()
        self._render_setup = None
        self._initialize_render_setup()

    def _check_maya_availability(self) -> bool:
        """Check if Maya and Render Setup are available."""
        try:
            import maya.cmds as cmds
            import maya.app.renderSetup.model.renderSetup as renderSetup
            return True
        except ImportError:
            print("Warning: Maya Render Setup not available - using fallback mode")
            return False

    def _initialize_render_setup(self) -> None:
        """Initialize Maya Render Setup system."""
        if not self._maya_available:
            return

        try:
            import maya.app.renderSetup.model.renderSetup as renderSetup
            self._render_setup = renderSetup.instance()
            print("Maya Render Setup initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize Render Setup: {e}")
            self._maya_available = False
    

    
    def get_render_layers(self) -> List[RenderLayerInfo]:
        """Get all render layers in the scene."""
        layers = []

        if self._maya_available and self._render_setup:
            try:
                # Get layers from Maya Render Setup
                maya_layers = self._render_setup.getRenderLayers()

                for maya_layer in maya_layers:
                    # Skip default render layer
                    if maya_layer.name() == "defaultRenderLayer":
                        continue

                    # Parse layer name to extract prefix, element, and variance
                    layer_name = maya_layer.name()
                    prefix, element, variance = self._parse_layer_name(layer_name)

                    # Get collections
                    collections = []
                    for collection in maya_layer.getCollections():
                        collections.append(collection.name())

                    # Create layer info
                    layer_info = RenderLayerInfo(
                        name=layer_name,
                        prefix=prefix,
                        element=element,
                        variance=variance,
                        created_date=datetime.now(),
                        is_active=maya_layer.isVisible(),
                        collections=collections,
                        overrides=self._extract_layer_overrides(maya_layer),
                        metadata={
                            "maya_layer_name": maya_layer.name(),
                            "render_engine": "Arnold"
                        }
                    )
                    layers.append(layer_info)

            except Exception as e:
                print(f"Error getting render layers from Maya: {e}")
        else:
            print("Maya Render Setup not available - no layers to retrieve")

        return layers

    def _parse_layer_name(self, layer_name: str) -> Tuple[str, RenderLayerElement, Optional[RenderLayerVariance]]:
        """Parse layer name to extract prefix, element, and variance."""
        parts = layer_name.split('_')

        if len(parts) < 2:
            return "UNKNOWN", RenderLayerElement.BG, None

        prefix = parts[0]
        element_str = parts[1]
        variance = None

        # Map element string to enum
        try:
            element = RenderLayerElement(element_str)
        except ValueError:
            element = RenderLayerElement.BG

        # Extract variance if present
        if len(parts) >= 3 and element != RenderLayerElement.ATMOS:
            try:
                variance = RenderLayerVariance(parts[2])
            except ValueError:
                pass

        return prefix, element, variance

    def get_active_render_layer(self) -> Optional[RenderLayerInfo]:
        """Get the currently active render layer."""
        if self._maya_available and self._render_setup:
            try:
                # Get current render layer from Maya
                import maya.cmds as cmds
                current_layer = cmds.editRenderLayerGlobals(query=True, currentRenderLayer=True)

                # Find the corresponding layer info
                all_layers = self.get_render_layers()
                for layer in all_layers:
                    if layer.name == current_layer:
                        return layer

            except Exception as e:
                print(f"Error getting active render layer: {e}")

        return None
    
    def create_render_layer(self, name: str, prefix: str, element: RenderLayerElement,
                          variance: Optional[RenderLayerVariance] = None) -> RenderLayerInfo:
        """
        Create a new render layer following naming convention with real Maya API.

        Args:
            name: Layer name (will be generated if not provided)
            prefix: Context prefix (MASTER, SH0010, etc.)
            element: Render layer element (BG, CHAR, ATMOS, FX)
            variance: Render layer variance (A, B, C) - omitted for ATMOS

        Returns:
            Created RenderLayerInfo object
        """
        # Generate name if not provided
        if not name:
            if element == RenderLayerElement.ATMOS:
                name = f"{prefix}_{element.value}"
            else:
                variance_str = variance.value if variance else "A"
                name = f"{prefix}_{element.value}_{variance_str}"

        if self._maya_available and self._render_setup:
            try:
                # Real Maya Render Setup API implementation
                import maya.app.renderSetup.model.renderLayer as renderLayer
                import maya.app.renderSetup.model.collection as collection

                # Create render layer
                layer = self._render_setup.createRenderLayer(name)
                layer.setVisible(True)

                # Create default collection for the layer
                collection_name = f"{name}_collection"
                coll = layer.createCollection(collection_name)

                # Set up basic overrides
                self._apply_default_overrides(layer)

                print(f"Created render layer '{name}' with Maya Render Setup API")

                # Create layer info object
                layer_info = RenderLayerInfo(
                    name=name,
                    prefix=prefix,
                    element=element,
                    variance=variance,
                    created_date=datetime.now(),
                    is_active=True,
                    collections=[collection_name],
                    overrides=self._extract_layer_overrides(layer),
                    metadata={
                        "created_by": "LRC_Toolbox",
                        "render_engine": "Arnold",
                        "creation_method": "maya_api",
                        "maya_layer_name": layer.name()
                    }
                )

                return layer_info

            except Exception as e:
                print(f"Error creating render layer with Maya API: {e}")
                return None
        else:
            print("Maya Render Setup not available - cannot create render layer")
            return None


    
    def delete_render_layer(self, layer_name: str) -> bool:
        """Delete a render layer."""
        if layer_name == "defaultRenderLayer":
            print("Cannot delete default render layer")
            return False

        if self._maya_available and self._render_setup:
            try:
                # Find and delete the layer using Maya API
                maya_layers = self._render_setup.getRenderLayers()
                for layer in maya_layers:
                    if layer.name() == layer_name:
                        self._render_setup.detachRenderLayer(layer)
                        print(f"Deleted render layer '{layer_name}'")
                        return True

                print(f"Render layer '{layer_name}' not found")
                return False

            except Exception as e:
                print(f"Error deleting render layer: {e}")
                return False
        else:
            print("Maya Render Setup not available - cannot delete render layer")
            return False
    
    def set_active_render_layer(self, layer_name: str) -> bool:
        """Set the active render layer."""
        if self._maya_available and self._render_setup:
            try:
                import maya.cmds as cmds

                # Check if layer exists
                if not cmds.objExists(layer_name):
                    print(f"Render layer '{layer_name}' not found")
                    return False

                # Set the active render layer
                cmds.editRenderLayerGlobals(currentRenderLayer=layer_name)
                print(f"Set '{layer_name}' as active render layer")
                return True

            except Exception as e:
                print(f"Error setting active render layer: {e}")
                return False
        else:
            print("Maya Render Setup not available - cannot set active render layer")
            return False
    
    def create_collection(self, layer_name: str, collection_name: str,
                        objects: List[str]) -> bool:
        """Create a collection in the specified render layer."""
        if self._maya_available and self._render_setup:
            try:
                # Find the render layer
                maya_layers = self._render_setup.getRenderLayers()
                target_layer = None
                for layer in maya_layers:
                    if layer.name() == layer_name:
                        target_layer = layer
                        break

                if not target_layer:
                    print(f"Render layer '{layer_name}' not found")
                    return False

                # Create collection
                collection = target_layer.createCollection(collection_name)

                # Add objects to collection
                if objects:
                    # Create selector pattern from objects
                    pattern = "|".join(objects)
                    collection.getSelector().setPattern(pattern)

                print(f"Created collection '{collection_name}' in layer '{layer_name}'")
                print(f"  - Added {len(objects)} objects to collection")
                return True

            except Exception as e:
                print(f"Error creating collection: {e}")
                return False
        else:
            print("Maya Render Setup not available - cannot create collection")
            return False
    
    def create_override(self, layer_name: str, collection_name: str,
                       attribute: str, value: Any) -> bool:
        """Create an override for a collection attribute."""
        if self._maya_available and self._render_setup:
            try:
                # Find the render layer
                maya_layers = self._render_setup.getRenderLayers()
                target_layer = None
                for layer in maya_layers:
                    if layer.name() == layer_name:
                        target_layer = layer
                        break

                if not target_layer:
                    print(f"Render layer '{layer_name}' not found")
                    return False

                # Find the collection
                target_collection = None
                for collection in target_layer.getCollections():
                    if collection.name() == collection_name:
                        target_collection = collection
                        break

                if not target_collection:
                    print(f"Collection '{collection_name}' not found in layer '{layer_name}'")
                    return False

                # Create override
                override = target_collection.createAbsOverride(
                    attrName=attribute,
                    attrValue=value
                )

                print(f"Created override in layer '{layer_name}'")
                print(f"  - Collection: {collection_name}")
                print(f"  - Attribute: {attribute}")
                print(f"  - Value: {value}")
                return True

            except Exception as e:
                print(f"Error creating override: {e}")
                return False
        else:
            print("Maya Render Setup not available - cannot create override")
            return False
    
    def import_render_setup_template(self, template_path: str,
                                   options: ImportOptions) -> bool:
        """Import render setup from template."""
        print(f"Importing render setup template from '{template_path}'")
        print(f"  - Import mode: {options.import_mode}")

        try:
            # Check if template file exists
            if not os.path.exists(template_path):
                print(f"  - Template file not found: {template_path}")
                return False

            # Load template data
            with open(template_path, 'r') as f:
                template_data = json.load(f)

            if "layers" not in template_data:
                print("  - Invalid template format: no layers found")
                return False

            if self._maya_available and self._render_setup:
                # Clear existing layers if replace mode
                if options.import_mode == "replace":
                    print("  - Clearing existing render setup")
                    existing_layers = self._render_setup.getRenderLayers()
                    for layer in existing_layers:
                        if layer.name() != "defaultRenderLayer":
                            self._render_setup.detachRenderLayer(layer)

                # Import template layers
                for layer_data in template_data["layers"]:
                    layer_name = layer_data["name"]
                    prefix = layer_data.get("prefix", "TEMPLATE")
                    element_str = layer_data.get("element", "BG")

                    try:
                        element = RenderLayerElement(element_str)
                    except ValueError:
                        element = RenderLayerElement.BG

                    variance = None
                    if layer_data.get("variance"):
                        try:
                            variance = RenderLayerVariance(layer_data["variance"])
                        except ValueError:
                            pass

                    # Create the layer
                    created_layer = self.create_render_layer(layer_name, prefix, element, variance)
                    if created_layer:
                        print(f"  - Imported layer: {layer_name}")

                print("  - Import completed successfully")
                return True
            else:
                print("  - Maya Render Setup not available")
                return False

        except Exception as e:
            print(f"  - Error importing template: {e}")
            return False
    
    def export_render_layers_json(self, file_path: str, selected_layers: Optional[List[str]] = None) -> bool:
        """
        Export render layers using Maya's native Render Setup export methods.

        Args:
            file_path: Path to export file
            selected_layers: List of layer names to export (None = all layers)

        Returns:
            Success status
        """
        print(f"Exporting render layers to '{file_path}' using Maya native methods")

        try:
            if not self._maya_available or not self._render_setup:
                print("  - Maya Render Setup not available")
                return False

            # Ensure export directory exists
            export_dir = os.path.dirname(file_path)
            if export_dir:
                os.makedirs(export_dir, exist_ok=True)

            # Try Maya's native export methods first
            if self._try_native_render_setup_export(file_path, selected_layers):
                print("  - Export completed using Maya native methods")
                return True
            else:
                print("  - Native export not available, using fallback JSON export")
                return self._fallback_json_export(file_path, selected_layers)

        except Exception as e:
            print(f"  - Error exporting render layers: {e}")
            return False

    def _try_native_render_setup_export(self, file_path: str, selected_layers: List[str] = None) -> bool:
        """Try to use Maya's native render setup export methods."""
        try:
            # Check if renderSetup has native export methods
            if hasattr(self._render_setup, 'exportToFile'):
                print("  - Using renderSetup.exportToFile()")
                self._render_setup.exportToFile(file_path)
                return True

            elif hasattr(self._render_setup, 'export'):
                print("  - Using renderSetup.export()")
                self._render_setup.export(file_path)
                return True

            # Check for Maya file command render setup support
            import maya.cmds as cmds
            if self._try_maya_file_export(file_path, selected_layers):
                return True

            return False

        except Exception as e:
            print(f"  - Native export failed: {e}")
            return False

    def _try_maya_file_export(self, file_path: str, selected_layers: List[str] = None) -> bool:
        """Try Maya file command for render setup export."""
        try:
            import maya.cmds as cmds

            # Try different file types that might support render setup
            file_types = ['renderSetup', 'json', 'mayaAscii']

            for file_type in file_types:
                try:
                    # Try exporting render setup with this file type
                    cmds.file(file_path, exportSelected=True, type=file_type, force=True)
                    print(f"  - Maya file export successful with type: {file_type}")
                    return True
                except:
                    continue

            return False

        except Exception as e:
            print(f"  - Maya file export failed: {e}")
            return False

    def _fallback_json_export(self, file_path: str, selected_layers: List[str] = None) -> bool:
        """Fallback to manual JSON export if native methods not available."""
        try:
            # Create export data structure
            export_data = {
                "render_setup_version": "1.0",
                "maya_version": self._get_maya_version(),
                "exported_date": datetime.now().isoformat(),
                "exported_by": "LRC_Toolbox",
                "export_method": "fallback_json",
                "render_layers": []
            }

            # Get all render layers from Maya Render Setup
            maya_layers = self._render_setup.getRenderLayers()

            for maya_layer in maya_layers:
                layer_name = maya_layer.name()

                # Skip default render layer
                if layer_name == "defaultRenderLayer":
                    continue

                # Filter by selected layers if specified
                if selected_layers and layer_name not in selected_layers:
                    continue

                # Export layer data using Render Setup API
                layer_data = self._export_render_layer_data(maya_layer)
                if layer_data:
                    export_data["render_layers"].append(layer_data)
                    print(f"  - Exported layer: {layer_name}")

            # Write JSON file
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            print(f"  - Fallback export: {len(export_data['render_layers'])} render layers")
            return True

        except Exception as e:
            print(f"  - Fallback export failed: {e}")
            return False

    def export_render_settings_json(self, file_path: str, include_renderer_specific: bool = True) -> bool:
        """
        Export render settings to JSON using Maya Render Setup API and render globals.

        Args:
            file_path: Path to export JSON file
            include_renderer_specific: Whether to include renderer-specific settings

        Returns:
            Success status
        """
        print(f"Exporting render settings to '{file_path}'")

        try:
            if not self._maya_available:
                print("  - Maya not available")
                return False

            import maya.cmds as cmds

            # Ensure export directory exists
            export_dir = os.path.dirname(file_path)
            if export_dir:
                os.makedirs(export_dir, exist_ok=True)

            # Get current renderer
            current_renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")

            # Create export data structure
            export_data = {
                "render_settings_version": "1.0",
                "maya_version": self._get_maya_version(),
                "exported_date": datetime.now().isoformat(),
                "exported_by": "LRC_Toolbox",
                "current_renderer": current_renderer,
                "render_globals": self._export_render_globals(),
                "renderer_settings": {}
            }

            # Export renderer-specific settings
            if include_renderer_specific:
                if current_renderer == "redshift":
                    export_data["renderer_settings"] = self._export_redshift_settings()
                elif current_renderer == "arnold":
                    export_data["renderer_settings"] = self._export_arnold_settings()
                elif current_renderer == "mayaSoftware":
                    export_data["renderer_settings"] = self._export_maya_software_settings()
                elif current_renderer == "mayaHardware2":
                    export_data["renderer_settings"] = self._export_maya_hardware_settings()
                else:
                    print(f"  - Renderer '{current_renderer}' settings export not implemented")

            # Write JSON file
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            print(f"  - Exported render settings for {current_renderer}")
            print(f"  - Export completed successfully")
            return True

        except Exception as e:
            print(f"  - Error exporting render settings: {e}")
            return False

    # ========================================
    # RESTORED MISSING METHODS FOR TEMPLATE EXPORT
    # ========================================

    def get_scene_lights(self) -> Dict[str, Any]:
        """
        Get scene lights data for template export.

        Returns:
            Dictionary containing lights data with structure matching v004 exports
        """
        print("Getting scene lights for template export")

        try:
            if not self._maya_available:
                print("  - Maya not available")
                return {"lights": []}

            import maya.cmds as cmds

            lights_data = {
                "lights_version": "1.0",
                "exported_date": datetime.now().isoformat(),
                "exported_by": "LRC_Toolbox",
                "lights": []
            }

            # Get all light types
            light_types = [
                'directionalLight', 'pointLight', 'spotLight', 'areaLight',
                'aiAreaLight', 'aiSkyDomeLight', 'aiMeshLight', 'volumeLight',
                'RedshiftPhysicalLight', 'RedshiftDomeLight', 'RedshiftIESLight'
            ]

            for light_type in light_types:
                # Get light shape nodes
                light_shapes = cmds.ls(type=light_type) or []

                for light_shape in light_shapes:
                    # Get the transform node (parent of shape)
                    transforms = cmds.listRelatives(light_shape, parent=True, type='transform') or []
                    if transforms:
                        light_transform = transforms[0]

                        # Extract light data
                        light_info = {
                            "name": light_transform,
                            "shape": light_shape,
                            "type": light_type,
                            "transform": light_transform,
                            "enabled": cmds.getAttr(f"{light_shape}.visibility") if cmds.objExists(f"{light_shape}.visibility") else True
                        }

                        # Get transform attributes
                        if cmds.objExists(light_transform):
                            try:
                                light_info["transform_data"] = {
                                    "translate": cmds.getAttr(f"{light_transform}.translate")[0],
                                    "rotate": cmds.getAttr(f"{light_transform}.rotate")[0],
                                    "scale": cmds.getAttr(f"{light_transform}.scale")[0]
                                }
                            except:
                                pass

                        # Get light-specific attributes
                        try:
                            attrs = cmds.listAttr(light_shape, keyable=True, scalar=True) or []
                            light_attrs = {}
                            for attr in attrs[:20]:  # Limit to avoid too much data
                                try:
                                    attr_name = f"{light_shape}.{attr}"
                                    if cmds.objExists(attr_name):
                                        value = cmds.getAttr(attr_name)
                                        light_attrs[attr] = value
                                except:
                                    continue
                            light_info["attributes"] = light_attrs
                        except:
                            light_info["attributes"] = {}

                        lights_data["lights"].append(light_info)

            print(f"  - Found {len(lights_data['lights'])} lights in scene")
            return lights_data

        except Exception as e:
            print(f"  - Error getting scene lights: {e}")
            return {"lights": []}

    def get_render_aovs(self) -> Dict[str, Any]:
        """
        Get render AOVs data for template export.

        Returns:
            Dictionary containing AOVs configuration data
        """
        print("Getting render AOVs for template export")

        try:
            if not self._maya_available:
                print("  - Maya not available")
                return {"aovs": []}

            import maya.cmds as cmds

            aovs_data = {
                "aovs_version": "1.0",
                "exported_date": datetime.now().isoformat(),
                "exported_by": "LRC_Toolbox",
                "aovs": []
            }

            # Get current renderer to determine AOV method
            current_renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")

            if current_renderer == "arnold":
                # Get Arnold AOVs
                aovs_data["aovs"] = self._get_arnold_aovs()
            elif current_renderer == "redshift":
                # Get Redshift AOVs
                aovs_data["aovs"] = self._get_redshift_aovs()
            else:
                print(f"  - AOV export not implemented for renderer: {current_renderer}")

            print(f"  - Found {len(aovs_data['aovs'])} AOVs for {current_renderer}")
            return aovs_data

        except Exception as e:
            print(f"  - Error getting render AOVs: {e}")
            return {"aovs": []}

    def get_render_settings(self) -> Dict[str, Any]:
        """
        Get render settings data for template export.

        Returns:
            Dictionary containing render settings (wrapper around export_render_settings_json)
        """
        print("Getting render settings for template export")

        try:
            if not self._maya_available:
                print("  - Maya not available")
                return {"render_settings": {}}

            import maya.cmds as cmds

            # Get current renderer
            current_renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")

            # Create render settings data structure (similar to export_render_settings_json)
            settings_data = {
                "render_settings_version": "1.0",
                "maya_version": self._get_maya_version(),
                "exported_date": datetime.now().isoformat(),
                "exported_by": "LRC_Toolbox",
                "current_renderer": current_renderer,
                "render_globals": self._export_render_globals(),
                "renderer_settings": {}
            }

            # Export renderer-specific settings
            if current_renderer == "redshift":
                settings_data["renderer_settings"] = self._export_redshift_settings()
            elif current_renderer == "arnold":
                settings_data["renderer_settings"] = self._export_arnold_settings()
            elif current_renderer == "mayaSoftware":
                settings_data["renderer_settings"] = self._export_maya_software_settings()
            elif current_renderer == "mayaHardware2":
                settings_data["renderer_settings"] = self._export_maya_hardware_settings()

            print(f"  - Exported render settings for {current_renderer}")
            return settings_data

        except Exception as e:
            print(f"  - Error getting render settings: {e}")
            return {"render_settings": {}}

    def export_render_setup(self, file_path: str) -> bool:
        """
        Export render setup (wrapper around export_render_layers_json).

        Args:
            file_path: Path to export file

        Returns:
            Success status
        """
        print(f"Exporting render setup to '{file_path}'")

        # Use the existing render layers export method
        return self.export_render_layers_json(file_path)

    def _get_arnold_aovs(self) -> List[Dict[str, Any]]:
        """Get Arnold AOVs configuration."""
        try:
            import maya.cmds as cmds

            aovs = []

            # Get all Arnold AOV nodes
            aov_nodes = cmds.ls(type='aiAOV') or []

            for aov_node in aov_nodes:
                try:
                    aov_info = {
                        "name": aov_node,
                        "type": "aiAOV",
                        "enabled": cmds.getAttr(f"{aov_node}.enabled") if cmds.objExists(f"{aov_node}.enabled") else True
                    }

                    # Get AOV-specific attributes
                    if cmds.objExists(f"{aov_node}.name"):
                        aov_info["aov_name"] = cmds.getAttr(f"{aov_node}.name")

                    if cmds.objExists(f"{aov_node}.type"):
                        aov_info["aov_type"] = cmds.getAttr(f"{aov_node}.type")

                    aovs.append(aov_info)

                except Exception as e:
                    print(f"    - Warning: Could not get AOV info for {aov_node}: {e}")
                    continue

            return aovs

        except Exception as e:
            print(f"  - Error getting Arnold AOVs: {e}")
            return []

    def _get_redshift_aovs(self) -> List[Dict[str, Any]]:
        """Get Redshift AOVs configuration."""
        try:
            import maya.cmds as cmds

            aovs = []

            # Get Redshift AOV nodes
            aov_nodes = cmds.ls(type='RedshiftAOV') or []

            for aov_node in aov_nodes:
                try:
                    aov_info = {
                        "name": aov_node,
                        "type": "RedshiftAOV",
                        "enabled": cmds.getAttr(f"{aov_node}.enabled") if cmds.objExists(f"{aov_node}.enabled") else True
                    }

                    # Get AOV-specific attributes
                    if cmds.objExists(f"{aov_node}.aovType"):
                        aov_info["aov_type"] = cmds.getAttr(f"{aov_node}.aovType")

                    if cmds.objExists(f"{aov_node}.aovSuffix"):
                        aov_info["aov_suffix"] = cmds.getAttr(f"{aov_node}.aovSuffix")

                    aovs.append(aov_info)

                except Exception as e:
                    print(f"    - Warning: Could not get AOV info for {aov_node}: {e}")
                    continue

            return aovs

        except Exception as e:
            print(f"  - Error getting Redshift AOVs: {e}")
            return []
    
    def export_render_setup_template(self, template_path: str,
                                   selected_layers: List[str]) -> bool:
        """
        Export render setup to template (legacy method - use export_render_layers_json instead).

        Args:
            template_path: Path to template file
            selected_layers: List of layer names to export

        Returns:
            Success status
        """
        print("Warning: export_render_setup_template is deprecated, use export_render_layers_json")
        return self.export_render_layers_json(template_path, selected_layers)

    def apply_render_settings_template(self, template_path: str) -> bool:
        """Apply render settings from template."""
        print(f"Applying render settings from '{template_path}'")

        try:
            # Check if template file exists
            if not os.path.exists(template_path):
                print(f"  - Template file not found: {template_path}")
                return False

            # Load render settings template
            with open(template_path, 'r') as f:
                settings_data = json.load(f)

            if "render_settings" not in settings_data:
                print("  - Invalid template format: no render_settings found")
                return False

            if self._maya_available:
                try:
                    import maya.cmds as cmds

                    settings = settings_data["render_settings"]

                    # Apply renderer settings
                    if "renderer" in settings:
                        cmds.setAttr("defaultRenderGlobals.currentRenderer", settings["renderer"], type="string")
                        print(f"  - Applied renderer: {settings['renderer']}")

                    # Apply image format settings
                    if "image_format" in settings:
                        format_map = {"exr": 51, "png": 32, "jpg": 8, "tiff": 3}
                        if settings["image_format"] in format_map:
                            cmds.setAttr("defaultRenderGlobals.imageFormat", format_map[settings["image_format"]])
                            print(f"  - Applied image format: {settings['image_format']}")

                    # Apply resolution settings
                    if "resolution" in settings and len(settings["resolution"]) == 2:
                        cmds.setAttr("defaultResolution.width", settings["resolution"][0])
                        cmds.setAttr("defaultResolution.height", settings["resolution"][1])
                        print(f"  - Applied resolution: {settings['resolution']}")

                    print("  - Render settings applied successfully")
                    return True

                except Exception as e:
                    print(f"  - Error applying render settings: {e}")
                    return False
            else:
                print("  - Maya not available - cannot apply render settings")
                return False

        except Exception as e:
            print(f"  - Error loading render settings template: {e}")
            return False
    
    def get_render_layer_statistics(self) -> Dict[str, Any]:
        """Get render layer statistics."""
        layers = self.get_render_layers()

        element_counts = {}
        prefix_counts = {}
        total_collections = 0
        total_overrides = 0

        for layer in layers:
            element_counts[layer.element.value] = element_counts.get(layer.element.value, 0) + 1
            prefix_counts[layer.prefix] = prefix_counts.get(layer.prefix, 0) + 1
            total_collections += len(layer.collections)
            total_overrides += len(layer.overrides)

        return {
            "total_layers": len(layers),
            "active_layers": len([l for l in layers if l.is_active]),
            "element_breakdown": element_counts,
            "prefix_breakdown": prefix_counts,
            "total_collections": total_collections,
            "total_overrides": total_overrides
        }
    
    def validate_layer_naming(self, layer_name: str) -> Tuple[bool, str]:
        """Validate render layer name against naming convention."""
        # Check for pattern: PREFIX_ELEMENT or PREFIX_ELEMENT_VARIANCE
        parts = layer_name.split('_')
        
        if len(parts) < 2:
            return False, "Layer name must have at least PREFIX_ELEMENT"
        
        prefix = parts[0]
        element = parts[1]
        
        # Validate element
        valid_elements = [e.value for e in RenderLayerElement]
        if element not in valid_elements:
            return False, f"Invalid element '{element}'. Valid elements: {valid_elements}"
        
        # Check variance for non-ATMOS elements
        if element != "ATMOS":
            if len(parts) != 3:
                return False, f"Element '{element}' requires variance (A, B, or C)"
            
            variance = parts[2]
            valid_variances = [v.value for v in RenderLayerVariance]
            if variance not in valid_variances:
                return False, f"Invalid variance '{variance}'. Valid variances: {valid_variances}"
        else:
            if len(parts) != 2:
                return False, "ATMOS element should not have variance"
        
        return True, "Valid layer naming convention"
    
    def _generate_default_overrides(self) -> Dict[str, Any]:
        """Generate default render layer overrides."""
        return {
            "visibility": True,
            "primary_visibility": True,
            "cast_shadows": True,
            "receive_shadows": True,
            "motion_blur": True,
            "subdivision_surface": True,
            "displacement": True
        }

    def _apply_default_overrides(self, layer) -> None:
        """Apply default overrides to a Maya render layer."""
        if not self._maya_available:
            return

        try:
            import maya.app.renderSetup.model.override as override
            import maya.cmds as cmds

            # Get the default collection for this layer
            collections = layer.getCollections()
            if not collections:
                return

            default_collection = collections[0]

            # Create common visibility overrides
            visibility_attrs = [
                'visibility',
                'primaryVisibility',
                'castsShadows',
                'receiveShadows',
                'motionBlur',
                'visibleInReflections',
                'visibleInRefractions'
            ]

            for attr in visibility_attrs:
                try:
                    abs_override = default_collection.createAbsOverride(
                        attrName=attr,
                        attrValue=True
                    )
                    print(f"Applied override: {attr} = True")
                except Exception as e:
                    print(f"Warning: Could not create override for {attr}: {e}")

        except Exception as e:
            print(f"Warning: Could not apply default overrides: {e}")

    def _extract_layer_overrides(self, layer) -> Dict[str, Any]:
        """Extract overrides from a Maya render layer."""
        overrides = {}

        if not self._maya_available:
            return self._generate_default_overrides()

        try:
            collections = layer.getCollections()
            for collection in collections:
                collection_overrides = collection.getOverrides()
                for override_obj in collection_overrides:
                    attr_name = override_obj.getAttributeName()
                    attr_value = override_obj.getAttributeValue()
                    overrides[attr_name] = attr_value

        except Exception as e:
            print(f"Warning: Could not extract layer overrides: {e}")
            return self._generate_default_overrides()

        return overrides if overrides else self._generate_default_overrides()

    def _export_render_layer_data(self, maya_layer) -> Optional[Dict[str, Any]]:
        """
        Export complete render layer data using Maya Render Setup API.

        Args:
            maya_layer: Maya render layer object

        Returns:
            Layer data dictionary or None if export fails
        """
        try:
            layer_data = {
                "name": maya_layer.name(),
                "enabled": maya_layer.isEnabled(),
                "renderable": maya_layer.isRenderable(),
                "visible": maya_layer.isVisible(),
                "collections": [],
                "global_overrides": [],
                "metadata": {
                    "layer_type": str(type(maya_layer).__name__),
                    "has_adjustments": maya_layer.hasAdjustments(),
                    "num_collections": len(maya_layer.getCollections())
                }
            }

            # Export collections
            for collection in maya_layer.getCollections():
                collection_data = self._export_collection_data(collection)
                if collection_data:
                    layer_data["collections"].append(collection_data)

            # Export global layer overrides (if any)
            try:
                global_overrides = maya_layer.getOverrides()
                for override_obj in global_overrides:
                    override_data = self._export_override_data(override_obj)
                    if override_data:
                        layer_data["global_overrides"].append(override_data)
            except:
                pass  # Some layers may not have global overrides

            return layer_data

        except Exception as e:
            print(f"Warning: Could not export layer data for {maya_layer.name()}: {e}")
            return None

    def _export_collection_data(self, collection) -> Optional[Dict[str, Any]]:
        """
        Export collection data using Maya Render Setup API.

        Args:
            collection: Maya collection object

        Returns:
            Collection data dictionary or None if export fails
        """
        try:
            collection_data = {
                "name": collection.name(),
                "enabled": collection.isEnabled(),
                "selector": {
                    "pattern": collection.getSelector().pattern(),
                    "filter_type": collection.getSelector().filterType(),
                    "static_selection": collection.getSelector().staticSelection()
                },
                "overrides": [],
                "metadata": {
                    "collection_type": str(type(collection).__name__),
                    "num_overrides": len(collection.getOverrides())
                }
            }

            # Export overrides for this collection
            for override_obj in collection.getOverrides():
                override_data = self._export_override_data(override_obj)
                if override_data:
                    collection_data["overrides"].append(override_data)

            return collection_data

        except Exception as e:
            print(f"Warning: Could not export collection data for {collection.name()}: {e}")
            return None

    def _export_override_data(self, override_obj) -> Optional[Dict[str, Any]]:
        """
        Export override data using Maya Render Setup API.

        Args:
            override_obj: Maya override object

        Returns:
            Override data dictionary or None if export fails
        """
        try:
            override_data = {
                "name": override_obj.name(),
                "enabled": override_obj.isEnabled(),
                "attribute_name": override_obj.getAttributeName(),
                "override_type": str(type(override_obj).__name__),
                "metadata": {}
            }

            # Get override value based on type
            try:
                if hasattr(override_obj, 'getAttributeValue'):
                    override_data["attribute_value"] = override_obj.getAttributeValue()
                elif hasattr(override_obj, 'attrValue'):
                    override_data["attribute_value"] = override_obj.attrValue()
                else:
                    override_data["attribute_value"] = None
            except:
                override_data["attribute_value"] = None

            # Add type-specific data
            if "AbsOverride" in override_data["override_type"]:
                override_data["metadata"]["override_method"] = "absolute"
            elif "RelOverride" in override_data["override_type"]:
                override_data["metadata"]["override_method"] = "relative"
            elif "UniqueOverride" in override_data["override_type"]:
                override_data["metadata"]["override_method"] = "unique"

            return override_data

        except Exception as e:
            print(f"Warning: Could not export override data: {e}")
            return None

    def _get_maya_version(self) -> str:
        """Get Maya version string."""
        try:
            import maya.cmds as cmds
            return cmds.about(version=True)
        except:
            return "Unknown"

    def _export_render_globals(self) -> Dict[str, Any]:
        """
        Export Maya render globals settings.

        Returns:
            Dictionary containing render globals settings
        """
        try:
            import maya.cmds as cmds

            render_globals = {
                # Frame settings
                "start_frame": cmds.getAttr("defaultRenderGlobals.startFrame"),
                "end_frame": cmds.getAttr("defaultRenderGlobals.endFrame"),
                "frame_step": cmds.getAttr("defaultRenderGlobals.byFrameStep"),
                "frame_padding": cmds.getAttr("defaultRenderGlobals.extensionPadding"),

                # Image settings
                "image_format": cmds.getAttr("defaultRenderGlobals.imageFormat"),
                "image_file_prefix": cmds.getAttr("defaultRenderGlobals.imageFilePrefix") or "",
                "animation": cmds.getAttr("defaultRenderGlobals.animation"),
                "put_frame_before_ext": cmds.getAttr("defaultRenderGlobals.putFrameBeforeExt"),
                "period_in_ext": cmds.getAttr("defaultRenderGlobals.periodInExt"),

                # Resolution settings
                "width": cmds.getAttr("defaultResolution.width"),
                "height": cmds.getAttr("defaultResolution.height"),
                "device_aspect_ratio": cmds.getAttr("defaultResolution.deviceAspectRatio"),
                "pixel_aspect": cmds.getAttr("defaultResolution.pixelAspect"),

                # Renderable cameras
                "renderable_cameras": self._get_renderable_cameras(),

                # Quality settings
                "enable_default_light": cmds.getAttr("defaultRenderGlobals.enableDefaultLight"),
                "shadow_linking": cmds.getAttr("defaultRenderGlobals.shadowLinking"),
                "light_linking": cmds.getAttr("defaultRenderGlobals.lightLinking")
            }

            return render_globals

        except Exception as e:
            print(f"Warning: Could not export render globals: {e}")
            return {}

    def _get_renderable_cameras(self) -> List[str]:
        """Get list of renderable cameras."""
        try:
            import maya.cmds as cmds

            cameras = []
            all_cameras = cmds.ls(type='camera')

            for camera in all_cameras:
                if cmds.getAttr(f"{camera}.renderable"):
                    # Get the transform node
                    transform = cmds.listRelatives(camera, parent=True, type='transform')
                    if transform:
                        cameras.append(transform[0])

            return cameras

        except Exception as e:
            print(f"Warning: Could not get renderable cameras: {e}")
            return []

    def _export_redshift_settings(self) -> Dict[str, Any]:
        """
        Export Redshift renderer-specific settings.

        Returns:
            Dictionary containing Redshift settings
        """
        try:
            import maya.cmds as cmds

            redshift_settings = {}

            # Get all Redshift option attributes
            redshift_nodes = cmds.ls(type='RedshiftOptions')
            if redshift_nodes:
                redshift_node = redshift_nodes[0]

                # Get all attributes from the Redshift options node
                attrs = cmds.listAttr(redshift_node, keyable=True, scalar=True)
                if attrs:
                    for attr in attrs:
                        try:
                            attr_name = f"{redshift_node}.{attr}"
                            if cmds.objExists(attr_name):
                                value = cmds.getAttr(attr_name)
                                redshift_settings[attr] = value
                        except:
                            continue

                # Add specific important Redshift settings
                important_attrs = [
                    'primaryGIEngine', 'secondaryGIEngine', 'numGIBounces',
                    'bruteForceGINumRays', 'photonGINumPhotons', 'irradianceCacheNumRays',
                    'unifiedSampling', 'unifiedMinSamples', 'unifiedMaxSamples',
                    'bucketOrder', 'bucketSize', 'enableOptiXRTOnSupportedGPUs'
                ]

                for attr in important_attrs:
                    try:
                        attr_name = f"{redshift_node}.{attr}"
                        if cmds.objExists(attr_name):
                            redshift_settings[attr] = cmds.getAttr(attr_name)
                    except:
                        continue

            return redshift_settings

        except Exception as e:
            print(f"Warning: Could not export Redshift settings: {e}")
            return {}

    def _export_arnold_settings(self) -> Dict[str, Any]:
        """
        Export Arnold renderer-specific settings.

        Returns:
            Dictionary containing Arnold settings
        """
        try:
            import maya.cmds as cmds

            arnold_settings = {}

            # Get Arnold render options
            arnold_nodes = cmds.ls(type='aiOptions')
            if arnold_nodes:
                arnold_node = arnold_nodes[0]

                # Important Arnold settings
                important_attrs = [
                    'AASamples', 'GIDiffuseSamples', 'GIGlossySamples', 'GIRefractionSamples',
                    'GIDiffuseDepth', 'GIGlossyDepth', 'GIRefractionDepth',
                    'GITotalDepth', 'GITransmissionDepth',
                    'bucketScanning', 'bucketSize', 'threads', 'threadPriority',
                    'textureMaxMemoryMB', 'textureMaxOpenFiles', 'textureAutotile',
                    'lowLightThreshold', 'enableProgressiveRender'
                ]

                for attr in important_attrs:
                    try:
                        attr_name = f"{arnold_node}.{attr}"
                        if cmds.objExists(attr_name):
                            arnold_settings[attr] = cmds.getAttr(attr_name)
                    except:
                        continue

            return arnold_settings

        except Exception as e:
            print(f"Warning: Could not export Arnold settings: {e}")
            return {}

    def _export_maya_software_settings(self) -> Dict[str, Any]:
        """
        Export Maya Software renderer settings.

        Returns:
            Dictionary containing Maya Software settings
        """
        try:
            import maya.cmds as cmds

            maya_settings = {
                # Anti-aliasing
                "edge_anti_aliasing": cmds.getAttr("defaultRenderQuality.edgeAntiAliasing"),
                "shading_samples": cmds.getAttr("defaultRenderQuality.shadingSamples"),
                "max_shading_samples": cmds.getAttr("defaultRenderQuality.maxShadingSamples"),
                "red_threshold": cmds.getAttr("defaultRenderQuality.redThreshold"),
                "green_threshold": cmds.getAttr("defaultRenderQuality.greenThreshold"),
                "blue_threshold": cmds.getAttr("defaultRenderQuality.blueThreshold"),

                # Raytracing
                "raytracing": cmds.getAttr("defaultRenderGlobals.enableRaytracing"),
                "reflections": cmds.getAttr("defaultRenderGlobals.reflections"),
                "refractions": cmds.getAttr("defaultRenderGlobals.refractions"),
                "shadows": cmds.getAttr("defaultRenderGlobals.shadows"),
                "max_trace_depth": cmds.getAttr("defaultRenderGlobals.maxTraceDepth"),

                # Motion blur
                "motion_blur": cmds.getAttr("defaultRenderGlobals.motionBlur"),
                "motion_blur_by_frame": cmds.getAttr("defaultRenderGlobals.motionBlurByFrame"),
                "shutter_angle": cmds.getAttr("defaultRenderGlobals.shutterAngle")
            }

            return maya_settings

        except Exception as e:
            print(f"Warning: Could not export Maya Software settings: {e}")
            return {}

    def _export_maya_hardware_settings(self) -> Dict[str, Any]:
        """
        Export Maya Hardware renderer settings.

        Returns:
            Dictionary containing Maya Hardware settings
        """
        try:
            import maya.cmds as cmds

            hardware_settings = {
                # Hardware render globals
                "enable_geometry_mask": cmds.getAttr("hardwareRenderGlobals.enableGeometryMask"),
                "geometry_mask": cmds.getAttr("hardwareRenderGlobals.geometryMask"),
                "enable_stroke_render": cmds.getAttr("hardwareRenderGlobals.enableStrokeRender"),
                "line_smoothing": cmds.getAttr("hardwareRenderGlobals.lineSmoothing"),
                "full_image_resolution": cmds.getAttr("hardwareRenderGlobals.fullImageResolution"),
                "acceleration": cmds.getAttr("hardwareRenderGlobals.acceleration"),
                "transparent_shadows": cmds.getAttr("hardwareRenderGlobals.transparentShadows")
            }

            return hardware_settings

        except Exception as e:
            print(f"Warning: Could not export Maya Hardware settings: {e}")
            return {}

    def import_render_layers_json(self, file_path: str, import_mode: str = "additive") -> bool:
        """
        Import render layers using Maya's native Render Setup import methods.

        Args:
            file_path: Path to file to import
            import_mode: Import mode ("additive", "replace", "merge")

        Returns:
            Success status
        """
        print(f"Importing render layers from '{file_path}' using Maya native methods")
        print(f"  - Import mode: {import_mode}")

        try:
            if not self._maya_available or not self._render_setup:
                print("  - Maya Render Setup not available")
                return False

            if not os.path.exists(file_path):
                print(f"  - File not found: {file_path}")
                return False

            # Try Maya's native import methods first
            if self._try_native_render_setup_import(file_path, import_mode):
                print("  - Import completed using Maya native methods")
                return True
            else:
                print("  - Native import not available, using fallback JSON import")
                return self._fallback_json_import(file_path, import_mode)

        except Exception as e:
            print(f"  - Error importing render layers: {e}")
            return False

    def _try_native_render_setup_import(self, file_path: str, import_mode: str) -> bool:
        """Try to use Maya's native render setup import methods."""
        try:
            # Handle import mode for native methods
            if import_mode == "replace":
                # Clear existing layers first
                existing_layers = self._render_setup.getRenderLayers()
                for layer in existing_layers:
                    if layer.name() != "defaultRenderLayer":
                        self._render_setup.detachRenderLayer(layer)
                        print(f"  - Removed existing layer: {layer.name()}")

            # Check if renderSetup has native import methods
            if hasattr(self._render_setup, 'importFromFile'):
                print("  - Using renderSetup.importFromFile()")
                self._render_setup.importFromFile(file_path)
                return True

            elif hasattr(self._render_setup, 'importData'):
                print("  - Using renderSetup.importData()")
                self._render_setup.importData(file_path)
                return True

            # Check for Maya file command render setup support
            import maya.cmds as cmds
            if self._try_maya_file_import(file_path, import_mode):
                return True

            return False

        except Exception as e:
            print(f"  - Native import failed: {e}")
            return False

    def _try_maya_file_import(self, file_path: str, import_mode: str) -> bool:
        """Try Maya file command for render setup import."""
        try:
            import maya.cmds as cmds

            # Try importing with different methods
            import_methods = [
                {'i': True},  # Import
                {'reference': True},  # Reference
                {'open': True}  # Open (for replace mode)
            ]

            for method in import_methods:
                try:
                    if 'open' in method and import_mode != "replace":
                        continue  # Only use open for replace mode

                    cmds.file(file_path, **method, force=True)
                    print(f"  - Maya file import successful with method: {list(method.keys())[0]}")
                    return True
                except:
                    continue

            return False

        except Exception as e:
            print(f"  - Maya file import failed: {e}")
            return False

    def _fallback_json_import(self, file_path: str, import_mode: str) -> bool:
        """Fallback to manual JSON import if native methods not available."""
        try:
            # Load JSON data
            with open(file_path, 'r') as f:
                import_data = json.load(f)

            if "render_layers" not in import_data:
                print("  - Invalid file format: no render_layers found")
                return False

            # Handle import mode
            if import_mode == "replace":
                # Delete existing layers (except default)
                existing_layers = self._render_setup.getRenderLayers()
                for layer in existing_layers:
                    if layer.name() != "defaultRenderLayer":
                        self._render_setup.detachRenderLayer(layer)
                        print(f"  - Removed existing layer: {layer.name()}")

            # Import each layer
            imported_count = 0
            for layer_data in import_data["render_layers"]:
                if self._import_render_layer_data(layer_data, import_mode):
                    imported_count += 1

            print(f"  - Fallback import: {imported_count} render layers")
            return imported_count > 0

        except Exception as e:
            print(f"  - Fallback import failed: {e}")
            return False

    def _import_render_layer_data(self, layer_data: Dict[str, Any], import_mode: str) -> bool:
        """
        Import individual render layer data using Maya Render Setup API.

        Args:
            layer_data: Layer data dictionary
            import_mode: Import mode

        Returns:
            Success status
        """
        try:
            layer_name = layer_data["name"]

            # Check if layer already exists
            existing_layer = None
            for layer in self._render_setup.getRenderLayers():
                if layer.name() == layer_name:
                    existing_layer = layer
                    break

            if existing_layer and import_mode == "additive":
                print(f"  - Skipping existing layer: {layer_name}")
                return False
            elif existing_layer and import_mode == "merge":
                # Use existing layer
                render_layer = existing_layer
                print(f"  - Merging into existing layer: {layer_name}")
            else:
                # Create new layer
                render_layer = self._render_setup.createRenderLayer(layer_name)
                print(f"  - Created new layer: {layer_name}")

            # Set layer properties
            render_layer.setEnabled(layer_data.get("enabled", True))
            render_layer.setRenderable(layer_data.get("renderable", True))
            render_layer.setVisible(layer_data.get("visible", True))

            # Import collections
            for collection_data in layer_data.get("collections", []):
                self._import_collection_data(render_layer, collection_data, import_mode)

            # Import global overrides
            for override_data in layer_data.get("global_overrides", []):
                self._import_override_data(render_layer, override_data)

            return True

        except Exception as e:
            print(f"Warning: Could not import layer {layer_data.get('name', 'Unknown')}: {e}")
            return False

    def _import_collection_data(self, render_layer, collection_data: Dict[str, Any], import_mode: str) -> bool:
        """
        Import collection data into render layer.

        Args:
            render_layer: Maya render layer object
            collection_data: Collection data dictionary
            import_mode: Import mode

        Returns:
            Success status
        """
        try:
            collection_name = collection_data["name"]

            # Check if collection already exists
            existing_collection = None
            for collection in render_layer.getCollections():
                if collection.name() == collection_name:
                    existing_collection = collection
                    break

            if existing_collection and import_mode == "merge":
                collection = existing_collection
                print(f"    - Merging into existing collection: {collection_name}")
            else:
                # Create new collection
                collection = render_layer.createCollection(collection_name)
                print(f"    - Created collection: {collection_name}")

            # Set collection properties
            collection.setEnabled(collection_data.get("enabled", True))

            # Set selector properties
            selector_data = collection_data.get("selector", {})
            selector = collection.getSelector()

            if "pattern" in selector_data:
                selector.setPattern(selector_data["pattern"])
            if "filter_type" in selector_data:
                selector.setFilterType(selector_data["filter_type"])
            if "static_selection" in selector_data:
                selector.setStaticSelection(selector_data["static_selection"])

            # Import overrides for this collection
            for override_data in collection_data.get("overrides", []):
                self._import_override_data(collection, override_data)

            return True

        except Exception as e:
            print(f"Warning: Could not import collection {collection_data.get('name', 'Unknown')}: {e}")
            return False

    def _import_override_data(self, parent_object, override_data: Dict[str, Any]) -> bool:
        """
        Import override data into collection or layer.

        Args:
            parent_object: Maya collection or layer object
            override_data: Override data dictionary

        Returns:
            Success status
        """
        try:
            override_name = override_data["name"]
            attribute_name = override_data["attribute_name"]
            attribute_value = override_data.get("attribute_value")
            override_type = override_data.get("override_type", "AbsOverride")

            # Create override based on type
            if "AbsOverride" in override_type:
                override_obj = parent_object.createAbsOverride(
                    attrName=attribute_name,
                    attrValue=attribute_value
                )
            elif "RelOverride" in override_type:
                override_obj = parent_object.createRelOverride(
                    attrName=attribute_name,
                    attrValue=attribute_value
                )
            elif "UniqueOverride" in override_type:
                override_obj = parent_object.createUniqueOverride(
                    attrName=attribute_name,
                    attrValue=attribute_value
                )
            else:
                # Default to absolute override
                override_obj = parent_object.createAbsOverride(
                    attrName=attribute_name,
                    attrValue=attribute_value
                )

            # Set override properties
            if override_obj:
                override_obj.setEnabled(override_data.get("enabled", True))
                print(f"      - Created override: {override_name} ({attribute_name})")
                return True

            return False

        except Exception as e:
            print(f"Warning: Could not import override {override_data.get('name', 'Unknown')}: {e}")
            return False

    def import_render_settings_json(self, file_path: str, apply_renderer_settings: bool = True) -> bool:
        """
        Import render settings from JSON.

        Args:
            file_path: Path to JSON file to import
            apply_renderer_settings: Whether to apply renderer-specific settings

        Returns:
            Success status
        """
        print(f"Importing render settings from '{file_path}'")

        try:
            if not self._maya_available:
                print("  - Maya not available")
                return False

            if not os.path.exists(file_path):
                print(f"  - File not found: {file_path}")
                return False

            # Load JSON data
            with open(file_path, 'r') as f:
                settings_data = json.load(f)

            if "render_globals" not in settings_data:
                print("  - Invalid file format: no render_globals found")
                return False

            import maya.cmds as cmds

            # Apply render globals
            render_globals = settings_data["render_globals"]
            self._apply_render_globals(render_globals)

            # Apply renderer-specific settings
            if apply_renderer_settings and "renderer_settings" in settings_data:
                current_renderer = settings_data.get("current_renderer")
                if current_renderer:
                    # Set the renderer first
                    cmds.setAttr("defaultRenderGlobals.currentRenderer", current_renderer, type="string")
                    print(f"  - Set renderer to: {current_renderer}")

                    # Apply renderer-specific settings
                    renderer_settings = settings_data["renderer_settings"]
                    if current_renderer == "redshift":
                        self._apply_redshift_settings(renderer_settings)
                    elif current_renderer == "arnold":
                        self._apply_arnold_settings(renderer_settings)
                    elif current_renderer == "mayaSoftware":
                        self._apply_maya_software_settings(renderer_settings)
                    elif current_renderer == "mayaHardware2":
                        self._apply_maya_hardware_settings(renderer_settings)

            print("  - Render settings imported successfully")
            return True

        except Exception as e:
            print(f"  - Error importing render settings: {e}")
            return False

    def _apply_render_globals(self, render_globals: Dict[str, Any]) -> None:
        """Apply render globals settings."""
        try:
            import maya.cmds as cmds

            # Frame settings
            if "start_frame" in render_globals:
                cmds.setAttr("defaultRenderGlobals.startFrame", render_globals["start_frame"])
            if "end_frame" in render_globals:
                cmds.setAttr("defaultRenderGlobals.endFrame", render_globals["end_frame"])
            if "frame_step" in render_globals:
                cmds.setAttr("defaultRenderGlobals.byFrameStep", render_globals["frame_step"])
            if "frame_padding" in render_globals:
                cmds.setAttr("defaultRenderGlobals.extensionPadding", render_globals["frame_padding"])

            # Image settings
            if "image_format" in render_globals:
                cmds.setAttr("defaultRenderGlobals.imageFormat", render_globals["image_format"])
            if "image_file_prefix" in render_globals:
                cmds.setAttr("defaultRenderGlobals.imageFilePrefix", render_globals["image_file_prefix"], type="string")
            if "animation" in render_globals:
                cmds.setAttr("defaultRenderGlobals.animation", render_globals["animation"])

            # Resolution settings
            if "width" in render_globals:
                cmds.setAttr("defaultResolution.width", render_globals["width"])
            if "height" in render_globals:
                cmds.setAttr("defaultResolution.height", render_globals["height"])
            if "device_aspect_ratio" in render_globals:
                cmds.setAttr("defaultResolution.deviceAspectRatio", render_globals["device_aspect_ratio"])
            if "pixel_aspect" in render_globals:
                cmds.setAttr("defaultResolution.pixelAspect", render_globals["pixel_aspect"])

            # Quality settings
            if "enable_default_light" in render_globals:
                cmds.setAttr("defaultRenderGlobals.enableDefaultLight", render_globals["enable_default_light"])
            if "shadow_linking" in render_globals:
                cmds.setAttr("defaultRenderGlobals.shadowLinking", render_globals["shadow_linking"])
            if "light_linking" in render_globals:
                cmds.setAttr("defaultRenderGlobals.lightLinking", render_globals["light_linking"])

            print("  - Applied render globals")

        except Exception as e:
            print(f"Warning: Could not apply render globals: {e}")

    def _apply_redshift_settings(self, redshift_settings: Dict[str, Any]) -> None:
        """Apply Redshift renderer settings."""
        try:
            import maya.cmds as cmds

            redshift_nodes = cmds.ls(type='RedshiftOptions')
            if not redshift_nodes:
                print("  - No Redshift options node found")
                return

            redshift_node = redshift_nodes[0]

            for attr, value in redshift_settings.items():
                try:
                    attr_name = f"{redshift_node}.{attr}"
                    if cmds.objExists(attr_name):
                        cmds.setAttr(attr_name, value)
                except:
                    continue

            print("  - Applied Redshift settings")

        except Exception as e:
            print(f"Warning: Could not apply Redshift settings: {e}")

    def _apply_arnold_settings(self, arnold_settings: Dict[str, Any]) -> None:
        """Apply Arnold renderer settings."""
        try:
            import maya.cmds as cmds

            arnold_nodes = cmds.ls(type='aiOptions')
            if not arnold_nodes:
                print("  - No Arnold options node found")
                return

            arnold_node = arnold_nodes[0]

            for attr, value in arnold_settings.items():
                try:
                    attr_name = f"{arnold_node}.{attr}"
                    if cmds.objExists(attr_name):
                        cmds.setAttr(attr_name, value)
                except:
                    continue

            print("  - Applied Arnold settings")

        except Exception as e:
            print(f"Warning: Could not apply Arnold settings: {e}")

    def _apply_maya_software_settings(self, maya_settings: Dict[str, Any]) -> None:
        """Apply Maya Software renderer settings."""
        try:
            import maya.cmds as cmds

            # Apply render quality settings
            quality_attrs = [
                ("edge_anti_aliasing", "defaultRenderQuality.edgeAntiAliasing"),
                ("shading_samples", "defaultRenderQuality.shadingSamples"),
                ("max_shading_samples", "defaultRenderQuality.maxShadingSamples"),
                ("red_threshold", "defaultRenderQuality.redThreshold"),
                ("green_threshold", "defaultRenderQuality.greenThreshold"),
                ("blue_threshold", "defaultRenderQuality.blueThreshold")
            ]

            for setting_key, maya_attr in quality_attrs:
                if setting_key in maya_settings:
                    cmds.setAttr(maya_attr, maya_settings[setting_key])

            # Apply render globals
            globals_attrs = [
                ("raytracing", "defaultRenderGlobals.enableRaytracing"),
                ("reflections", "defaultRenderGlobals.reflections"),
                ("refractions", "defaultRenderGlobals.refractions"),
                ("shadows", "defaultRenderGlobals.shadows"),
                ("max_trace_depth", "defaultRenderGlobals.maxTraceDepth"),
                ("motion_blur", "defaultRenderGlobals.motionBlur"),
                ("motion_blur_by_frame", "defaultRenderGlobals.motionBlurByFrame"),
                ("shutter_angle", "defaultRenderGlobals.shutterAngle")
            ]

            for setting_key, maya_attr in globals_attrs:
                if setting_key in maya_settings:
                    cmds.setAttr(maya_attr, maya_settings[setting_key])

            print("  - Applied Maya Software settings")

        except Exception as e:
            print(f"Warning: Could not apply Maya Software settings: {e}")

    def _apply_maya_hardware_settings(self, hardware_settings: Dict[str, Any]) -> None:
        """Apply Maya Hardware renderer settings."""
        try:
            import maya.cmds as cmds

            hardware_attrs = [
                ("enable_geometry_mask", "hardwareRenderGlobals.enableGeometryMask"),
                ("geometry_mask", "hardwareRenderGlobals.geometryMask"),
                ("enable_stroke_render", "hardwareRenderGlobals.enableStrokeRender"),
                ("line_smoothing", "hardwareRenderGlobals.lineSmoothing"),
                ("full_image_resolution", "hardwareRenderGlobals.fullImageResolution"),
                ("acceleration", "hardwareRenderGlobals.acceleration"),
                ("transparent_shadows", "hardwareRenderGlobals.transparentShadows")
            ]

            for setting_key, maya_attr in hardware_attrs:
                if setting_key in hardware_settings:
                    cmds.setAttr(maya_attr, hardware_settings[setting_key])

            print("  - Applied Maya Hardware settings")

        except Exception as e:
            print(f"Warning: Could not apply Maya Hardware settings: {e}")

    # Quick Template Creation Methods
    def create_quick_template(self, template_type: str, context: str, variance: str = "A") -> bool:
        """
        Create quick template using standard configurations.

        Args:
            template_type: Template type (BG, CHAR, ATMOS, FX)
            context: Context prefix (e.g., MASTER, SH0010)
            variance: Variance suffix (default: A)

        Returns:
            Success status
        """
        try:
            from ..utils import render_layers

            if not render_layers.is_available():
                print("Maya Render Setup not available")
                return False

            # Create template configuration
            template = render_layers.create_standard_template_config(template_type, context, variance)

            # Create the template layer
            success = render_layers.create_template_layer(template)

            if success:
                print(f"Created {template_type} template: {template.name}")
                print(f"  - Layer pattern: {template.pattern}")
                print(f"  - Collections: {len(template.collections)}")
                for collection in template.collections:
                    print(f"    - {collection.name} ({collection.filter_type}): '{collection.pattern}'")
                    if collection.sub_collections:
                        for sub_coll in collection.sub_collections:
                            print(f"      - {sub_coll.name} ({sub_coll.filter_type}): '{sub_coll.pattern}'")
            else:
                print(f"Failed to create {template_type} template")

            return success

        except Exception as e:
            print(f"Error creating quick template: {e}")
            return False

    def create_bg_template(self, context: str, variance: str = "A") -> bool:
        """Create background template layer."""
        return self.create_quick_template("BG", context, variance)

    def create_char_template(self, context: str, variance: str = "A") -> bool:
        """Create character template layer."""
        return self.create_quick_template("CHAR", context, variance)

    def create_atmos_template(self, context: str, variance: str = "A") -> bool:
        """Create atmospheric template layer."""
        return self.create_quick_template("ATMOS", context, variance)

    def create_fx_template(self, context: str, variance: str = "A") -> bool:
        """Create effects template layer."""
        return self.create_quick_template("FX", context, variance)

    def create_all_standard_templates(self, context: str, variance: str = "A") -> Dict[str, bool]:
        """
        Create all standard template layers.

        Args:
            context: Context prefix (e.g., MASTER, SH0010)
            variance: Variance suffix (default: A)

        Returns:
            Dictionary mapping template type to success status
        """
        try:
            from ..utils import render_layers

            if not render_layers.is_available():
                print("Maya Render Setup not available")
                return {}

            results = render_layers.create_all_standard_templates(context, variance)

            # Report results
            successful = [k for k, v in results.items() if v]
            failed = [k for k, v in results.items() if not v]

            print(f"Template creation results for context '{context}_{variance}':")
            if successful:
                print(f"  ✅ Created: {', '.join(successful)}")
            if failed:
                print(f"  ❌ Failed: {', '.join(failed)}")

            return results

        except Exception as e:
            print(f"Error creating standard templates: {e}")
            return {}

    def get_available_template_types(self) -> List[str]:
        """Get list of available template types."""
        try:
            from ..utils import render_layers
            return list(render_layers.STANDARD_TEMPLATES.keys())
        except Exception:
            return ["BG", "CHAR", "ATMOS", "FX"]

    def get_template_info(self, template_type: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a template type.

        Args:
            template_type: Template type to query

        Returns:
            Template information dictionary or None
        """
        try:
            from ..utils import render_layers

            if template_type in render_layers.STANDARD_TEMPLATES:
                return render_layers.STANDARD_TEMPLATES[template_type].copy()

            return None

        except Exception:
            return None
