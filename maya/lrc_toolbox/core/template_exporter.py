"""
Template Exporter

This module provides comprehensive template export functionality with versioning,
package creation, and individual component export capabilities.
"""

import os
import json
import shutil
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

from .models import NavigationContext, ExportOptions
from .render_setup_api import RenderSetupAPI
from ..config.settings import settings
from ..utils.context_detector import context_detector


class TemplateExporter:
    """
    Template exporter with versioning and package management.
    
    Provides comprehensive template export functionality including:
    - Package export (lights, layers, AOVs, render settings)
    - Individual component export
    - Version management with semantic versioning
    - Context-aware export paths
    """

    def __init__(self):
        """Initialize template exporter."""
        self._render_api = RenderSetupAPI()
        self._project_root = settings.get_project_root()

    def export_template_package(self, 
                               template_name: str,
                               components: List[str] = None,
                               context: NavigationContext = None,
                               version: str = None,
                               description: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        """
        Export complete template package with versioning.
        
        Args:
            template_name: Name of template
            components: List of components to export ['lights', 'layers', 'aovs', 'render_settings']
            context: Navigation context (auto-detected if None)
            version: Version string (auto-generated if None)
            description: Version description
            
        Returns:
            Tuple of (success, export_path, package_info)
        """
        # Auto-detect context if not provided
        if not context:
            context = context_detector.get_current_scene_context()
            if not context:
                return False, "", {"error": "Could not detect context from current scene"}

        # Validate context
        is_valid, error_msg = context_detector.validate_context(context)
        if not is_valid:
            return False, "", {"error": f"Invalid context: {error_msg}"}

        # Default components
        if not components:
            components = ['lights', 'layers', 'aovs', 'render_settings']

        # Generate version if not provided
        if not version:
            version = self._generate_next_version(template_name, context)

        # Create export directory
        export_path = self._get_versioned_export_path(template_name, context, version)
        os.makedirs(export_path, exist_ok=True)

        # Export components
        package_info = {
            "template_name": template_name,
            "version": version,
            "description": description,
            "context": {
                "type": context.type.value,
                "summary": context_detector.get_context_summary(context)
            },
            "components": {},
            "export_time": datetime.now().isoformat(),
            "maya_scene": context_detector.get_current_scene_path(),
            "user": os.getenv("USERNAME", "unknown")
        }

        success_count = 0
        total_components = len(components)

        for component in components:
            component_success, component_path, component_info = self._export_component(
                component, export_path, template_name, context
            )
            
            package_info["components"][component] = {
                "success": component_success,
                "path": component_path,
                "info": component_info
            }
            
            if component_success:
                success_count += 1

        # Save package manifest
        manifest_path = os.path.join(export_path, "package_manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump(package_info, f, indent=2)

        # Overall success if at least one component exported
        overall_success = success_count > 0
        
        return overall_success, export_path, package_info

    def export_individual_component(self,
                                   component: str,
                                   template_name: str,
                                   context: NavigationContext = None,
                                   export_path: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Export individual template component.
        
        Args:
            component: Component type ('lights', 'layers', 'aovs', 'render_settings')
            template_name: Template name
            context: Navigation context (auto-detected if None)
            export_path: Custom export path (auto-generated if None)
            
        Returns:
            Tuple of (success, file_path, component_info)
        """
        # Auto-detect context if not provided
        if not context:
            context = context_detector.get_current_scene_context()
            if not context:
                return False, "", {"error": "Could not detect context from current scene"}

        # Generate export path if not provided
        if not export_path:
            export_path = self._get_component_export_path(template_name, context, component)
            os.makedirs(os.path.dirname(export_path), exist_ok=True)

        return self._export_component(component, os.path.dirname(export_path), template_name, context)

    def _export_component(self, 
                         component: str, 
                         export_dir: str, 
                         template_name: str,
                         context: NavigationContext) -> Tuple[bool, str, Dict[str, Any]]:
        """Export individual component."""
        component_info = {
            "component": component,
            "export_time": datetime.now().isoformat(),
            "template_name": template_name
        }

        try:
            if component == 'layers':
                return self._export_render_layers(export_dir, template_name, component_info)
            elif component == 'lights':
                return self._export_lights(export_dir, template_name, component_info)
            elif component == 'aovs':
                return self._export_aovs(export_dir, template_name, component_info)
            elif component == 'render_settings':
                return self._export_render_settings(export_dir, template_name, component_info)
            else:
                component_info["error"] = f"Unknown component: {component}"
                return False, "", component_info

        except Exception as e:
            component_info["error"] = str(e)
            return False, "", component_info

    def _export_render_layers(self, export_dir: str, template_name: str, info: Dict) -> Tuple[bool, str, Dict]:
        """Export render layers using Maya API."""
        file_path = os.path.join(export_dir, f"{template_name}_layers.json")
        
        # Use render setup API for export
        success = self._render_api.export_render_setup(file_path)
        
        info.update({
            "method": "maya_render_setup_api",
            "file_path": file_path,
            "success": success
        })
        
        return success, file_path, info

    def _export_lights(self, export_dir: str, template_name: str, info: Dict) -> Tuple[bool, str, Dict]:
        """Export lights as Maya scene file (.ma)."""
        file_path = os.path.join(export_dir, f"{template_name}_lights.ma")

        try:
            # Export lights as Maya scene file
            success = self._export_lights_to_maya(file_path)

            if success:
                # Get light count for info
                lights_data = self._render_api.get_scene_lights()
                light_count = len(lights_data.get("lights", []))

                info.update({
                    "method": "maya_scene_export",
                    "file_path": file_path,
                    "light_count": light_count,
                    "file_type": "maya_ascii"
                })

                return True, file_path, info
            else:
                info.update({
                    "method": "maya_scene_export",
                    "file_path": file_path,
                    "error": "Failed to export lights to Maya file"
                })
                return False, file_path, info

        except Exception as e:
            info.update({
                "method": "maya_scene_export",
                "file_path": file_path,
                "error": str(e)
            })
            return False, file_path, info

    def _export_aovs(self, export_dir: str, template_name: str, info: Dict) -> Tuple[bool, str, Dict]:
        """Export AOVs configuration."""
        file_path = os.path.join(export_dir, f"{template_name}_aovs.json")
        
        # Export AOVs using render API
        aovs_data = self._render_api.get_render_aovs()
        
        with open(file_path, 'w') as f:
            json.dump(aovs_data, f, indent=2)
        
        info.update({
            "method": "render_aovs_export",
            "file_path": file_path,
            "aov_count": len(aovs_data.get("aovs", []))
        })
        
        return True, file_path, info

    def _export_render_settings(self, export_dir: str, template_name: str, info: Dict) -> Tuple[bool, str, Dict]:
        """Export render settings."""
        file_path = os.path.join(export_dir, f"{template_name}_render_settings.json")
        
        # Export render settings using render API
        settings_data = self._render_api.get_render_settings()
        
        with open(file_path, 'w') as f:
            json.dump(settings_data, f, indent=2)
        
        info.update({
            "method": "render_settings_export",
            "file_path": file_path,
            "renderer": settings_data.get("renderer", "unknown")
        })
        
        return True, file_path, info

    def _export_lights_to_maya(self, file_path: str) -> bool:
        """
        Export lights to Maya scene file.

        Args:
            file_path: Path to Maya file (.ma)

        Returns:
            Success status
        """
        try:
            # Check if Maya is available
            if not hasattr(self._render_api, '_maya_available') or not self._render_api._maya_available:
                print("  - Maya not available for light export")
                return False

            import maya.cmds as cmds

            # Get all lights in the scene
            lights_data = self._render_api.get_scene_lights()
            light_names = [light.get("name") for light in lights_data.get("lights", []) if light.get("name")]

            if not light_names:
                print("  - No lights found to export")
                return False

            print(f"  - Exporting {len(light_names)} lights to Maya file")

            # Ensure export directory exists
            export_dir = os.path.dirname(file_path)
            if export_dir:
                os.makedirs(export_dir, exist_ok=True)

            # Export selected lights to Maya file
            # First select all lights
            cmds.select(clear=True)
            existing_lights = []

            for light_name in light_names:
                if cmds.objExists(light_name):
                    existing_lights.append(light_name)

            if not existing_lights:
                print("  - No valid lights found in scene")
                return False

            # Select all existing lights
            cmds.select(existing_lights, replace=True)

            # Export selected lights as Maya ASCII
            cmds.file(file_path,
                     exportSelected=True,
                     type="mayaAscii",
                     force=True)

            print(f"  - Successfully exported {len(existing_lights)} lights to {file_path}")
            return True

        except Exception as e:
            print(f"  - Error exporting lights to Maya file: {e}")
            return False

    def _generate_next_version(self, template_name: str, context: NavigationContext) -> str:
        """Generate next version number for template."""
        base_path = context_detector.get_template_export_path(context, template_name)

        if not os.path.exists(base_path):
            return "v001"

        # Find existing versions
        versions = []
        for item in os.listdir(base_path):
            if item.startswith("v") and os.path.isdir(os.path.join(base_path, item)):
                try:
                    # Parse version (v001 -> 1, v010 -> 10, etc.)
                    version_num = int(item[1:])
                    versions.append(version_num)
                except ValueError:
                    continue

        if not versions:
            return "v001"

        # Get highest version and increment
        latest = max(versions)
        next_version = latest + 1

        return f"v{next_version:03d}"

    def _get_versioned_export_path(self, template_name: str, context: NavigationContext, version: str) -> str:
        """Get versioned export path."""
        base_path = context_detector.get_template_export_path(context, template_name)
        return os.path.join(base_path, version)

    def _get_component_export_path(self, template_name: str, context: NavigationContext, component: str) -> str:
        """Get component export path."""
        base_path = context_detector.get_template_export_path(context, template_name)
        return os.path.join(base_path, "individual", f"{template_name}_{component}.json")

    def list_template_versions(self, template_name: str, context: NavigationContext) -> List[Dict[str, Any]]:
        """List all versions of a template."""
        base_path = context_detector.get_template_export_path(context, template_name)
        
        if not os.path.exists(base_path):
            return []
        
        versions = []
        for item in os.listdir(base_path):
            version_path = os.path.join(base_path, item)
            if os.path.isdir(version_path) and item.startswith("v"):
                manifest_path = os.path.join(version_path, "package_manifest.json")
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                        versions.append({
                            "version": item,
                            "path": version_path,
                            "manifest": manifest
                        })
                    except Exception as e:
                        print(f"Error reading manifest for {item}: {e}")
        
        # Sort by version
        versions.sort(key=lambda x: x["version"], reverse=True)
        return versions


# Global instance
template_exporter = TemplateExporter()
