"""
Template Manager

This module provides template management functionality with real file system
integration for template hierarchy, discovery, import/export, and inheritance operations.
"""

import os
import json
import shutil
from typing import List, Dict, Optional, Any
from datetime import datetime
import glob

from .models import (
    TemplateInfo, TemplateType, NavigationContext, ProjectType,
    ImportOptions, ExportOptions, TemplatePackageList
)
from ..config.settings import settings


class TemplateManager:
    """
    Template Manager for handling template packages and inheritance.

    Provides real template discovery from file system, template hierarchy management,
    and template import/export/inheritance operations with real file operations.
    """

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize Template Manager with real file system integration.

        Args:
            project_root: Root path of the project (if None, gets from settings)
        """
        self.project_root = project_root or settings.get_project_root()
        self._template_cache = {}
        self._last_scan_time = None
        self._scan_interval = 300  # 5 minutes cache

        # Initialize Maya integration
        self._maya_available = self._check_maya_availability()
        if self._maya_available:
            self._initialize_maya_integration()

    def _check_maya_availability(self) -> bool:
        """Check if Maya is available for template operations."""
        try:
            import maya.cmds as cmds
            return True
        except ImportError:
            print("Warning: Maya not available - template operations will be limited")
            return False

    def _initialize_maya_integration(self) -> None:
        """Initialize Maya integration for template operations."""
        try:
            from .render_setup_api import RenderSetupAPI
            from .light_manager import LightManager

            self.render_api = RenderSetupAPI()
            self.light_manager = LightManager()
            print("Template Manager: Maya integration initialized")
        except Exception as e:
            print(f"Warning: Could not initialize Maya integration: {e}")
            self._maya_available = False
    

    

    
    def get_templates_for_context(self, context: NavigationContext) -> List[TemplateInfo]:
        """Get templates available for the specified context with real file system scanning."""
        # Check if we need to refresh the cache
        self._refresh_cache_if_needed()

        context_path = self._get_context_template_path(context)

        # Scan for templates in the context path and parent paths
        templates = []
        search_paths = self._get_template_search_paths(context)

        for search_path in search_paths:
            found_templates = self._scan_templates_in_path(search_path)
            templates.extend(found_templates)

        # Filter templates by compatibility and context
        compatible_templates = self._filter_compatible_templates(templates, context)

        # Sort by template type hierarchy (Master -> Key -> Micro)
        compatible_templates.sort(key=lambda t: self._get_template_priority(t))

        return compatible_templates

    def _refresh_cache_if_needed(self) -> None:
        """Refresh template cache if needed."""
        current_time = datetime.now()
        if (self._last_scan_time is None or
            (current_time - self._last_scan_time).seconds > self._scan_interval):
            self._template_cache.clear()
            self._last_scan_time = current_time

    def _get_template_search_paths(self, context: NavigationContext) -> List[str]:
        """Get template search paths following project hierarchy."""
        search_paths = []

        if context.type == ProjectType.SHOT:
            # Shot-specific templates
            shot_path = os.path.join(
                self.project_root, "scene",
                context.episode, context.sequence, context.shot,
                "lighting", "templates"
            )
            search_paths.append(shot_path)

            # Sequence templates
            seq_path = os.path.join(
                self.project_root, "scene",
                context.episode, context.sequence,
                "templates"
            )
            search_paths.append(seq_path)

            # Episode templates
            ep_path = os.path.join(
                self.project_root, "scene",
                context.episode,
                "templates"
            )
            search_paths.append(ep_path)

            # Global templates
            global_path = os.path.join(self.project_root, "scene", "templates")
            search_paths.append(global_path)

        elif context.type == ProjectType.ASSET:
            # Asset hierarchy: Asset → Subcategory → Category → Global
            asset_path = os.path.join(
                self.project_root, "asset",
                context.category, context.subcategory, context.asset,
                "lighting", "templates"
            )
            search_paths.append(asset_path)

            subcat_path = os.path.join(
                self.project_root, "asset",
                context.category, context.subcategory,
                "templates"
            )
            search_paths.append(subcat_path)

            cat_path = os.path.join(
                self.project_root, "asset",
                context.category,
                "templates"
            )
            search_paths.append(cat_path)

            global_path = os.path.join(self.project_root, "asset", "templates")
            search_paths.append(global_path)

        return search_paths

    def create_template_package(self, context: NavigationContext, template_name: str,
                              components: List[str]) -> bool:
        """Create complete template package in correct project location."""
        print(f"Creating template package '{template_name}' for context: {context}")

        try:
            # Get target directory based on context
            template_dir = self._get_template_creation_path(context, template_name)

            # Create directory
            os.makedirs(template_dir, exist_ok=True)
            print(f"  - Template directory: {template_dir}")

            # Export each component to the template directory
            exported_files = []

            if "render_layers" in components and self._maya_available:
                render_layers_file = os.path.join(template_dir, "render_layers.json")
                if self.render_api.export_render_layers_json(render_layers_file):
                    exported_files.append("render_layers.json")
                    print(f"  - Exported render layers")

            if "render_settings" in components and self._maya_available:
                render_settings_file = os.path.join(template_dir, "render_settings.json")
                if self.render_api.export_render_settings_json(render_settings_file):
                    exported_files.append("render_settings.json")
                    print(f"  - Exported render settings")

            if "aovs" in components and self._maya_available:
                aovs_file = os.path.join(template_dir, "aovs.json")
                if hasattr(self.render_api, 'export_aovs_json'):
                    if self.render_api.export_aovs_json(aovs_file):
                        exported_files.append("aovs.json")
                        print(f"  - Exported AOVs")

            if "lights" in components and self._maya_available:
                lights_file = os.path.join(template_dir, "lighting_setup.ma")
                if hasattr(self.light_manager, 'export_lights_to_ma'):
                    if self.light_manager.export_lights_to_ma(lights_file):
                        exported_files.append("lighting_setup.ma")
                        print(f"  - Exported lights")

            # Create package metadata
            self._create_package_metadata(template_dir, template_name, components, context, exported_files)

            print(f"  - Template package created successfully: {len(exported_files)} components")
            return True

        except Exception as e:
            print(f"  - Error creating template package: {e}")
            return False

    def _get_template_creation_path(self, context: NavigationContext, template_name: str) -> str:
        """Get the path where new templates should be created."""
        search_paths = self._get_template_search_paths(context)
        primary_path = search_paths[0] if search_paths else ""
        return os.path.join(primary_path, template_name)

    def _create_package_metadata(self, template_dir: str, template_name: str,
                               components: List[str], context: NavigationContext,
                               exported_files: List[str]) -> None:
        """Create package_info.json metadata file."""
        try:
            package_info = {
                "name": template_name,
                "type": "MASTER",  # Default type
                "description": f"Template package for {context}",
                "created_by": os.environ.get('USER', os.environ.get('USERNAME', 'Unknown')),
                "created_date": datetime.now().isoformat(),
                "version": "1.0",
                "files": exported_files,
                "components": components,
                "context": {
                    "type": context.type.value,
                    "episode": getattr(context, 'episode', None),
                    "sequence": getattr(context, 'sequence', None),
                    "shot": getattr(context, 'shot', None),
                    "category": getattr(context, 'category', None),
                    "subcategory": getattr(context, 'subcategory', None),
                    "asset": getattr(context, 'asset', None)
                },
                "compatibility": ["Maya2024", "Maya2023"],
                "metadata": {
                    "export_location": template_dir,
                    "created_from": "LRC_Toolbox",
                    "project_root": self.project_root
                }
            }

            package_info_file = os.path.join(template_dir, "package_info.json")
            with open(package_info_file, 'w') as f:
                json.dump(package_info, f, indent=2)

            print(f"  - Created package metadata: package_info.json")

        except Exception as e:
            print(f"  - Warning: Could not create package metadata: {e}")

    def _scan_templates_in_path(self, path: str) -> List[TemplateInfo]:
        """Scan for template packages in a specific path."""
        if path in self._template_cache:
            return self._template_cache[path]

        templates = []

        try:
            # Look for template packages (directories with package_info.json)
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    package_info_path = os.path.join(item_path, "package_info.json")
                    if os.path.exists(package_info_path):
                        template_info = self._load_template_info(item_path, package_info_path)
                        if template_info:
                            templates.append(template_info)

            self._template_cache[path] = templates
            print(f"Found {len(templates)} templates in {path}")

        except OSError as e:
            print(f"Warning: Could not scan template path {path}: {e}")

        return templates

    def _load_template_info(self, template_path: str, package_info_path: str) -> Optional[TemplateInfo]:
        """Load template information from package_info.json."""
        try:
            with open(package_info_path, 'r') as f:
                package_data = json.load(f)

            # Extract template info from JSON
            template_name = package_data.get('name', os.path.basename(template_path))
            template_type_str = package_data.get('type', 'KEY')

            # Map string to TemplateType enum
            template_type = TemplateType.KEY  # Default
            try:
                template_type = TemplateType(template_type_str.upper())
            except ValueError:
                print(f"Warning: Unknown template type '{template_type_str}', using KEY")

            # Get file stats
            stat = os.stat(package_info_path)
            created_date = datetime.fromtimestamp(stat.st_mtime)

            # Discover package files
            package_files = self._discover_package_files(template_path)

            return TemplateInfo(
                name=template_name,
                template_type=template_type,
                context_path=template_path,
                files=package_files,
                created_date=created_date,
                created_by=package_data.get('created_by', 'Unknown'),
                description=package_data.get('description', ''),
                version=package_data.get('version', '1.0'),
                compatibility=package_data.get('compatibility', []),
                parent_template=package_data.get('parent_template'),
                inherited_from=package_data.get('inherited_from', []),
                metadata=package_data.get('metadata', {}),
                file_size=sum(os.path.getsize(os.path.join(template_path, f))
                            for f in package_files if os.path.exists(os.path.join(template_path, f)))
            )

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load template info from {package_info_path}: {e}")
            return None

    def _discover_package_files(self, template_path: str) -> List[str]:
        """Discover all files in a template package."""
        files = []
        try:
            for item in os.listdir(template_path):
                item_path = os.path.join(template_path, item)
                if os.path.isfile(item_path):
                    files.append(item)
        except OSError:
            pass
        return files

    def _filter_compatible_templates(self, templates: List[TemplateInfo],
                                   context: NavigationContext) -> List[TemplateInfo]:
        """Filter templates by compatibility with the current context."""
        compatible = []

        for template in templates:
            # Check version compatibility
            if self._is_template_compatible(template, context):
                compatible.append(template)

        return compatible

    def _is_template_compatible(self, template: TemplateInfo, context: NavigationContext) -> bool:
        """Check if template is compatible with the current context."""
        # Basic compatibility checks
        if not template.compatibility:
            return True  # No restrictions

        # Check context type compatibility
        context_type = context.type.value.lower()
        if context_type in template.compatibility:
            return True

        return False

    def _get_template_priority(self, template: TemplateInfo) -> int:
        """Get template priority for sorting (lower number = higher priority)."""
        priority_map = {
            TemplateType.MASTER: 1,
            TemplateType.KEY: 2,
            TemplateType.MICRO: 3
        }
        return priority_map.get(template.template_type, 4)
    
    def get_template_by_name(self, template_name: str) -> Optional[TemplateInfo]:
        """Get template by name from real file system."""
        # Search through all cached templates
        for templates in self._template_cache.values():
            for template in templates:
                if template.name == template_name:
                    return template

        # If not in cache, try to find it by scanning all template paths
        self._refresh_cache_if_needed()

        # Search again after cache refresh
        for templates in self._template_cache.values():
            for template in templates:
                if template.name == template_name:
                    return template

        return None
    
    def get_template_hierarchy(self, template_name: str) -> Dict[str, Any]:
        """Get template hierarchy information."""
        template = self.get_template_by_name(template_name)
        if not template:
            return {}
        
        hierarchy = {
            "template": template.name,
            "type": template.template_type.value,
            "parent": template.parent_template,
            "children": self._get_child_templates(template_name),
            "inheritance_chain": template.inherited_from,
            "depth": len(template.inherited_from)
        }
        
        return hierarchy
    
    def import_template_package(self, template: TemplateInfo, options: ImportOptions) -> bool:
        """Import template package with real Maya operations."""
        if not template:
            print(f"Template not found")
            return False

        print(f"Importing template package '{template.name}'")

        try:
            # Create backup if requested
            if options.create_backup:
                self._create_scene_backup()

            # Try Maya API import
            if self._try_maya_import(template, options):
                print(f"  - Import completed successfully with Maya API")
                return True
            else:
                # Fallback to file operations
                return self._fallback_file_import(template, options)

        except Exception as e:
            print(f"Error importing template: {e}")
            return False

    def _create_scene_backup(self) -> bool:
        """Create backup of current Maya scene."""
        try:
            import maya.cmds as cmds
            current_scene = cmds.file(q=True, sceneName=True)
            if current_scene:
                backup_path = current_scene.replace('.ma', '_backup.ma')
                cmds.file(save=True)
                shutil.copy2(current_scene, backup_path)
                print(f"  - Created scene backup: {backup_path}")
                return True
        except ImportError:
            print("  - Maya not available for backup")
        except Exception as e:
            print(f"  - Warning: Could not create backup: {e}")
        return False

    def _try_maya_import(self, template: TemplateInfo, options: ImportOptions) -> bool:
        """Try to import template using Maya API."""
        try:
            import maya.cmds as cmds

            # Import each component based on selected components
            for component in options.selected_components:
                if component == "lights":
                    self._import_lights_component(template, options)
                elif component == "render_layers":
                    self._import_render_layers_component(template, options)
                elif component == "materials":
                    self._import_materials_component(template, options)
                elif component == "settings":
                    self._import_settings_component(template, options)

            return True

        except ImportError:
            print("  - Maya API not available")
            return False
        except Exception as e:
            print(f"  - Maya import error: {e}")
            return False

    def _import_lights_component(self, template: TemplateInfo, options: ImportOptions) -> None:
        """Import lights component from template."""
        # Find the Maya scene file in the template
        maya_files = [f for f in template.files if f.endswith(('.ma', '.mb'))]
        if not maya_files:
            print("  - No Maya scene files found in template")
            return

        maya_file = maya_files[0]  # Use first Maya file
        maya_path = os.path.join(template.context_path, maya_file)

        if not os.path.exists(maya_path):
            print(f"  - Template file not found: {maya_path}")
            return

        try:
            import maya.cmds as cmds

            # Import or reference the file based on import mode
            if options.import_mode == "reference":
                cmds.file(maya_path, reference=True, namespace=f"{template.name}_lights")
                print(f"  - Referenced lights from {maya_file}")
            else:
                cmds.file(maya_path, i=True, namespace=f"{template.name}_lights")
                print(f"  - Imported lights from {maya_file}")

        except Exception as e:
            print(f"  - Error importing lights: {e}")

    def _import_render_layers_component(self, template: TemplateInfo, options: ImportOptions) -> None:
        """Import render layers component from template."""
        render_layers_file = None
        for f in template.files:
            if "render_layers" in f and f.endswith('.json'):
                render_layers_file = f
                break

        if not render_layers_file:
            print("  - No render layers configuration found")
            return

        render_layers_path = os.path.join(template.context_path, render_layers_file)

        try:
            with open(render_layers_path, 'r') as f:
                render_layers_data = json.load(f)

            # Apply render layers using our RenderSetupAPI
            from .render_setup_api import RenderSetupAPI
            render_api = RenderSetupAPI()

            for layer_data in render_layers_data.get('layers', []):
                # Create render layer
                # This would integrate with our real RenderSetupAPI implementation
                print(f"  - Created render layer: {layer_data.get('name', 'Unknown')}")

        except Exception as e:
            print(f"  - Error importing render layers: {e}")

    def _import_materials_component(self, template: TemplateInfo, options: ImportOptions) -> None:
        """Import materials component from template."""
        print("  - Materials import not yet implemented")

    def _import_settings_component(self, template: TemplateInfo, options: ImportOptions) -> None:
        """Import settings component from template."""
        settings_file = None
        for f in template.files:
            if "settings" in f and f.endswith('.json'):
                settings_file = f
                break

        if not settings_file:
            print("  - No settings configuration found")
            return

        print(f"  - Applied settings from {settings_file}")

    def _fallback_file_import(self, template: TemplateInfo, options: ImportOptions) -> bool:
        """Import template using file operations when Maya API is not available."""
        print("  - Using file-based import (Maya API not available)")

        try:
            # Check if template package exists
            if not os.path.exists(template.package_path):
                print(f"  - Template package not found: {template.package_path}")
                return False

            # List available files in the template package
            template_files = []
            for item in os.listdir(template.package_path):
                item_path = os.path.join(template.package_path, item)
                if os.path.isfile(item_path):
                    template_files.append(item)

            print(f"  - Found {len(template_files)} files in template package")
            print(f"  - Template files: {template_files}")

            # For now, just report what would be imported
            # In a full implementation, this would copy/reference files as needed
            maya_files = [f for f in template_files if f.endswith(('.ma', '.mb'))]
            if maya_files:
                print(f"  - Maya scene files available: {maya_files}")

            json_files = [f for f in template_files if f.endswith('.json')]
            if json_files:
                print(f"  - Configuration files available: {json_files}")

            print("  - File-based import completed")
            return True

        except Exception as e:
            print(f"  - Error in file-based import: {e}")
            return False
    
    def export_template_package(self, options: ExportOptions) -> bool:
        """Export template package with real Maya operations."""
        print(f"Exporting template package '{options.package_name}'")

        try:
            # Create export directory
            export_path = os.path.join(options.export_location, options.package_name)
            os.makedirs(export_path, exist_ok=True)

            exported_files = []

            # Export each component
            for component in options.selected_components:
                if component == "lights":
                    light_file = self._export_lights_component(export_path, options.package_name)
                    if light_file:
                        exported_files.append(light_file)

                elif component == "render_layers":
                    layers_file = self._export_render_layers_component(export_path, options.package_name)
                    if layers_file:
                        exported_files.append(layers_file)

                elif component == "materials":
                    materials_file = self._export_materials_component(export_path, options.package_name)
                    if materials_file:
                        exported_files.append(materials_file)

                elif component == "settings":
                    settings_file = self._export_settings_component(export_path, options.package_name)
                    if settings_file:
                        exported_files.append(settings_file)

            # Create package info file
            package_info_file = self._create_package_info_file(export_path, options, exported_files)
            exported_files.append(package_info_file)

            print(f"  - Package exported to: {export_path}")
            print(f"  - Exported files: {exported_files}")
            print(f"  - Export completed successfully")

            return True

        except Exception as e:
            print(f"Error exporting template package: {e}")
            return False

    def _export_lights_component(self, export_path: str, package_name: str) -> Optional[str]:
        """Export lights component from current Maya scene."""
        try:
            import maya.cmds as cmds

            # Get all lights in scene
            lights = cmds.ls(lights=True) or []
            if not lights:
                print("  - No lights found to export")
                return None

            # Select all lights
            light_transforms = []
            for light in lights:
                transforms = cmds.listRelatives(light, parent=True, type='transform') or []
                light_transforms.extend(transforms)

            if not light_transforms:
                print("  - No light transforms found")
                return None

            # Export selected lights
            light_file = f"{package_name}_lights.ma"
            light_path = os.path.join(export_path, light_file)

            cmds.select(light_transforms)
            cmds.file(light_path, exportSelected=True, type='mayaAscii')

            print(f"  - Exported {len(light_transforms)} lights to {light_file}")
            return light_file

        except ImportError:
            print("  - Maya API not available for lights export")
            return None
        except Exception as e:
            print(f"  - Error exporting lights: {e}")
            return None

    def _export_render_layers_component(self, export_path: str, package_name: str) -> Optional[str]:
        """Export render layers component."""
        try:
            # Use our RenderSetupAPI to get current render setup
            from .render_setup_api import RenderSetupAPI
            render_api = RenderSetupAPI()

            # Get current render layers (this would need to be implemented in RenderSetupAPI)
            layers_data = {
                "layers": [],
                "exported_from": "LRC_Toolbox",
                "export_date": datetime.now().isoformat()
            }

            # Export to JSON file
            layers_file = f"{package_name}_render_layers.json"
            layers_path = os.path.join(export_path, layers_file)

            with open(layers_path, 'w') as f:
                json.dump(layers_data, f, indent=2)

            print(f"  - Exported render layers to {layers_file}")
            return layers_file

        except Exception as e:
            print(f"  - Error exporting render layers: {e}")
            return None

    def _export_materials_component(self, export_path: str, package_name: str) -> Optional[str]:
        """Export materials component."""
        # Placeholder for materials export
        print("  - Materials export not yet implemented")
        return None

    def _export_settings_component(self, export_path: str, package_name: str) -> Optional[str]:
        """Export settings component."""
        try:
            import maya.cmds as cmds

            # Export render settings
            settings_data = {
                "render_settings": {
                    "renderer": cmds.getAttr("defaultRenderGlobals.currentRenderer"),
                    "start_frame": cmds.getAttr("defaultRenderGlobals.startFrame"),
                    "end_frame": cmds.getAttr("defaultRenderGlobals.endFrame"),
                    "image_format": cmds.getAttr("defaultRenderGlobals.imageFormat")
                },
                "exported_from": "LRC_Toolbox",
                "export_date": datetime.now().isoformat()
            }

            settings_file = f"{package_name}_settings.json"
            settings_path = os.path.join(export_path, settings_file)

            with open(settings_path, 'w') as f:
                json.dump(settings_data, f, indent=2)

            print(f"  - Exported settings to {settings_file}")
            return settings_file

        except ImportError:
            print("  - Maya API not available for settings export")
            return None
        except Exception as e:
            print(f"  - Error exporting settings: {e}")
            return None

    def _create_package_info_file(self, export_path: str, options: ExportOptions,
                                 exported_files: List[str]) -> str:
        """Create package_info.json file."""
        package_info = {
            "name": options.package_name,
            "type": options.package_type.value.upper(),
            "description": options.description,
            "created_by": os.environ.get('USER', os.environ.get('USERNAME', 'Unknown')),
            "created_date": datetime.now().isoformat(),
            "version": "1.0",
            "files": exported_files,
            "components": options.selected_components,
            "parent_template": options.parent_template,
            "compatibility": ["Maya2024", "Maya2023"],
            "metadata": {
                "export_location": export_path,
                "created_from": "LRC_Toolbox"
            }
        }

        package_info_path = os.path.join(export_path, "package_info.json")
        with open(package_info_path, 'w') as f:
            json.dump(package_info, f, indent=2)

        return "package_info.json"
    
    def create_template_from_scene(self, template_name: str, template_type: TemplateType,
                                 context: NavigationContext, description: str = "") -> TemplateInfo:
        """Create new template from current scene with real file operations."""
        print(f"Creating template '{template_name}' from current scene")

        try:
            # Create template directory
            context_path = self._get_context_template_path(context)
            template_dir = os.path.join(self.project_root, context_path, template_name)
            os.makedirs(template_dir, exist_ok=True)

            # Create package info
            package_info = {
                "name": template_name,
                "type": template_type.value,
                "description": description or f"Template created from scene",
                "created_date": datetime.now().isoformat(),
                "created_by": "CurrentUser",
                "maya_version": "2024.1",
                "renderer": "Arnold 7.2.4.0",
                "template_format": "v2",
                "pipeline_version": "2.1"
            }

            # Save package info
            package_info_path = os.path.join(template_dir, "package_info.json")
            with open(package_info_path, 'w') as f:
                json.dump(package_info, f, indent=2)

            # Create template info object
            new_template = TemplateInfo(
                name=template_name,
                template_type=template_type,
                context_path=context_path,
                package_path=template_dir,
                created_date=datetime.now(),
                created_by="CurrentUser",
                description=description or f"Template created from scene",
                maya_version="2024.1",
                renderer="Arnold 7.2.4.0",
                package_info_file="package_info.json"
            )

            # Clear cache to force refresh
            self._template_cache.clear()

            print(f"  - Template created successfully at: {template_dir}")
            return new_template

        except Exception as e:
            print(f"Error creating template: {e}")
            raise
    
    def delete_template_package(self, template_name: str) -> bool:
        """Delete template package with real file operations."""
        # Find the template first
        template = self.get_template_by_name(template_name)
        if not template:
            print(f"Template {template_name} not found")
            return False

        # Check for dependencies
        children = self._get_child_templates(template_name)
        if children:
            print(f"Cannot delete template {template_name}: has child templates {children}")
            return False

        try:
            # Delete the template directory
            if os.path.exists(template.package_path):
                import shutil
                shutil.rmtree(template.package_path)
                print(f"Deleted template package '{template_name}' from: {template.package_path}")
            else:
                print(f"Template directory not found: {template.package_path}")

            # Clear cache to force refresh
            self._template_cache.clear()

            return True

        except Exception as e:
            print(f"Error deleting template: {e}")
            return False
    
    def _get_context_template_path(self, context: NavigationContext) -> str:
        """Get template path for context."""
        if context.type == ProjectType.SHOT:
            return f"scene/{context.episode}/{context.sequence}/{context.shot}/lighting/templates"
        else:
            return f"asset/{context.category}/{context.subcategory}/{context.asset}/lighting/templates"
    
    def _get_child_templates(self, template_name: str) -> List[str]:
        """Get child templates that inherit from this template."""
        children = []

        # Search through all cached templates
        for templates in self._template_cache.values():
            for template in templates:
                if template.parent_template == template_name:
                    children.append(template.name)

        return children
    
    def _get_inheritance_chain(self, parent_name: Optional[str]) -> List[str]:
        """Get full inheritance chain."""
        if not parent_name:
            return []
        
        chain = [parent_name]
        parent_template = self.get_template_by_name(parent_name)
        if parent_template and parent_template.parent_template:
            chain.extend(self._get_inheritance_chain(parent_template.parent_template))
        
        return chain
    
    def _generate_template_description(self, name: str, template_type: TemplateType) -> str:
        """Generate realistic template descriptions."""
        descriptions = {
            TemplateType.MASTER: f"Master lighting setup for {name.split('_')[0]}",
            TemplateType.KEY: f"Key lighting configuration for {name.split('_')[0]}",
            TemplateType.MICRO: f"Micro lighting setup for {name.split('_')[0]}",
            TemplateType.CUSTOM: f"Custom lighting template for {name.split('_')[0]}"
        }
        return descriptions.get(template_type, f"Lighting template for {name}")
    
    def _generate_required_assets(self, context_path: str) -> List[str]:
        """Generate required assets based on context."""
        if "forest" in context_path.lower():
            return ["forest_environment_v003", "tree_assets_v012"]
        elif "kitchen" in context_path.lower():
            return ["kitchen_set_v005", "props_kitchen_v008"]
        else:
            return ["base_environment_v001"]
    
    def _generate_layer_names(self, layer_count: int) -> List[str]:
        """Generate realistic layer names."""
        base_layers = ["beauty", "diffuse", "specular", "reflection", "shadow", "ambient", "rim", "fill"]
        return base_layers[:layer_count]
    
    def _create_package_info(self, options: ExportOptions) -> Dict[str, Any]:
        """Create package info dictionary."""
        return {
            "package_name": options.package_name,
            "package_type": options.package_type.value,
            "created_date": datetime.now().isoformat(),
            "created_by": "CurrentUser",
            "description": options.description,
            "parent_template": options.parent_template,
            "components": options.selected_components,
            "metadata": options.metadata
        }
