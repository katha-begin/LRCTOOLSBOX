"""
Scene Exporter

This module provides Maya scene export functionality with version management
integration and hero file creation.
"""

import os
from typing import List, Dict, Optional, Any

from .base_exporter import BaseExporter, ExportResult, ExportFormat
from ..core.models import ExportOptions


class SceneExporter(BaseExporter):
    """
    Maya scene exporter with version management integration.
    
    Exports Maya scenes with proper version management and hero file creation.
    """
    
    def __init__(self):
        """Initialize scene exporter."""
        super().__init__()
        self._supported_formats = [ExportFormat.MAYA_ASCII, ExportFormat.MAYA_BINARY]
    
    def get_supported_formats(self) -> List[ExportFormat]:
        """Get supported export formats."""
        return self._supported_formats.copy()
    
    def export_to_file(self, file_path: str, objects: List[str], 
                      options: ExportOptions) -> ExportResult:
        """
        Export scene or selected objects to Maya file.
        
        Args:
            file_path: Path to export file
            objects: List of objects to export (empty for full scene)
            options: Export options
            
        Returns:
            ExportResult with operation details
        """
        # Reset cancellation flag
        self._cancel_requested = False
        
        # Validate inputs
        is_valid, error_msg = self._validate_export_path(file_path)
        if not is_valid:
            return ExportResult(False, error_msg)
        
        is_valid, error_msg = self._validate_export_options(options)
        if not is_valid:
            return ExportResult(False, error_msg)
        
        if not self.can_export_format(file_path):
            return ExportResult(False, f"Unsupported export format: {file_path}")
        
        if not self._maya_available:
            return ExportResult(False, "Maya is not available")
        
        try:
            import maya.cmds as cmds
            
            # Report progress
            if not self._report_progress(0.1, "Starting scene export..."):
                return ExportResult(False, "Export cancelled by user")
            
            # Validate objects if specified
            existing_objects = []
            missing_objects = []
            warnings = []
            
            if objects:
                existing_objects, missing_objects = self._validate_objects_exist(objects)
                if missing_objects:
                    warnings.append(f"Missing objects: {', '.join(missing_objects)}")
                if not existing_objects:
                    return ExportResult(False, "No valid objects to export")
            
            if not self._report_progress(0.2, "Preparing export..."):
                return ExportResult(False, "Export cancelled by user")
            
            # Create backup if file exists
            backup_path = None
            if options.create_backup:
                backup_path = self._backup_existing_file(file_path)
            
            try:
                # Determine export type
                export_format = self._get_file_format_from_extension(file_path)
                file_type = 'mayaAscii' if export_format == ExportFormat.MAYA_ASCII else 'mayaBinary'
                
                if objects and existing_objects:
                    # Export selected objects
                    if not self._report_progress(0.5, f"Exporting {len(existing_objects)} objects..."):
                        return ExportResult(False, "Export cancelled by user")
                    
                    # Select objects for export
                    cmds.select(existing_objects)
                    
                    # Export selection
                    cmds.file(file_path, 
                             exportSelected=True,
                             type=file_type,
                             preserveReferences=options.preserve_references,
                             force=True)
                    
                    print(f"Exported {len(existing_objects)} objects to {file_path}")
                    
                else:
                    # Export entire scene
                    if not self._report_progress(0.5, "Exporting scene..."):
                        return ExportResult(False, "Export cancelled by user")
                    
                    if options.export_mode == "save_as":
                        # Save scene as new file
                        cmds.file(rename=file_path)
                        cmds.file(save=True, type=file_type)
                    else:
                        # Export all
                        cmds.file(file_path,
                                 exportAll=True,
                                 type=file_type,
                                 preserveReferences=options.preserve_references,
                                 force=True)
                    
                    print(f"Exported scene to {file_path}")
                
                if not self._report_progress(0.8, "Finalizing export..."):
                    pass  # Don't cancel at this point
                
                # Add metadata if requested
                if options.include_metadata:
                    self._add_export_metadata(file_path, objects or [], options)
                
                # Create hero file if requested
                hero_path = None
                if options.create_hero:
                    hero_path = self._create_hero_file(file_path)
                    if hero_path:
                        print(f"Created hero file: {hero_path}")
                
                self._report_progress(1.0, "Export completed")
                
                exported_objects = existing_objects if objects else ["<entire_scene>"]
                success_msg = f"Successfully exported to {os.path.basename(file_path)}"
                
                result = ExportResult(True, success_msg, file_path, exported_objects, warnings)
                if hero_path:
                    result.metadata = {"hero_file": hero_path}
                
                return result
                
            except Exception as e:
                # Clean up on error
                self._cleanup_on_error(file_path, backup_path)
                return ExportResult(False, f"Export failed: {str(e)}")
                
        except Exception as e:
            return ExportResult(False, f"Export error: {str(e)}")
    
    def export_current_scene(self, file_path: str, options: ExportOptions) -> ExportResult:
        """
        Export current scene to file.
        
        Args:
            file_path: Path to export file
            options: Export options
            
        Returns:
            ExportResult with operation details
        """
        return self.export_to_file(file_path, [], options)
    
    def export_selection(self, file_path: str, options: ExportOptions) -> ExportResult:
        """
        Export currently selected objects to file.
        
        Args:
            file_path: Path to export file
            options: Export options
            
        Returns:
            ExportResult with operation details
        """
        if not self._maya_available:
            return ExportResult(False, "Maya is not available")
        
        try:
            import maya.cmds as cmds
            selected = cmds.ls(selection=True) or []
            
            if not selected:
                return ExportResult(False, "No objects selected for export")
            
            return self.export_to_file(file_path, selected, options)
            
        except Exception as e:
            return ExportResult(False, f"Error getting selection: {str(e)}")
    
    def _create_hero_file(self, source_path: str) -> Optional[str]:
        """
        Create hero file from exported file.
        
        Args:
            source_path: Path to source file
            
        Returns:
            Hero file path if created successfully
        """
        try:
            # Generate hero file path
            dir_path = os.path.dirname(source_path)
            file_name = os.path.basename(source_path)
            name_part, ext_part = os.path.splitext(file_name)
            
            # Remove version suffix if present
            import re
            version_pattern = re.compile(r'_v\d{3,4}$')
            base_name = version_pattern.sub('', name_part)
            
            hero_name = f"{base_name}_hero{ext_part}"
            hero_path = os.path.join(dir_path, hero_name)
            
            # Create hero file (symlink or copy)
            if os.path.exists(hero_path):
                if os.path.islink(hero_path):
                    os.unlink(hero_path)
                else:
                    os.remove(hero_path)
            
            try:
                # Try to create symlink
                os.symlink(source_path, hero_path)
            except OSError:
                # Fallback to copy
                import shutil
                shutil.copy2(source_path, hero_path)
            
            return hero_path
            
        except Exception as e:
            print(f"Warning: Could not create hero file: {e}")
            return None
    
    def _add_export_metadata(self, file_path: str, objects: List[str], 
                           options: ExportOptions) -> None:
        """
        Add export metadata to file.
        
        Args:
            file_path: Path to exported file
            objects: List of exported objects
            options: Export options used
        """
        try:
            metadata = {
                "export_time": datetime.now().isoformat(),
                "exported_objects_count": len(objects),
                "export_options": {
                    "preserve_references": options.preserve_references,
                    "create_backup": options.create_backup,
                    "create_hero": options.create_hero
                },
                "exporter": "LRC Toolbox Scene Exporter"
            }
            
            # Write metadata to companion file
            metadata_path = f"{file_path}.metadata.json"
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
        except Exception as e:
            print(f"Warning: Could not write export metadata: {e}")
