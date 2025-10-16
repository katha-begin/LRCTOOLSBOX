"""
Scene Importer

This module provides Maya scene file import functionality with reference/import modes
and namespace handling.
"""

import os
from typing import List, Dict, Optional, Any, Tuple

from .base_importer import BaseImporter, ImportResult, ImportMode
from ..core.models import ImportOptions


class SceneImporter(BaseImporter):
    """
    Maya scene file importer with reference/import modes and namespace handling.
    
    Supports importing .ma and .mb files with various import modes and options.
    """
    
    def __init__(self):
        """Initialize scene importer."""
        super().__init__()
        self._supported_extensions = ['.ma', '.mb']
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return self._supported_extensions.copy()
    
    def import_file(self, file_path: str, options: ImportOptions) -> ImportResult:
        """
        Import Maya scene file with specified options.
        
        Args:
            file_path: Path to Maya scene file
            options: Import options
            
        Returns:
            ImportResult with operation details
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
        
        # Check file extension
        if not self.can_import_file(file_path):
            return ImportResult(False, f"Unsupported file type: {file_path}")
        
        if not self._maya_available:
            return ImportResult(False, "Maya is not available")
        
        try:
            import maya.cmds as cmds
            
            # Report progress
            if not self._report_progress(0.1, "Starting scene import..."):
                return ImportResult(False, "Import cancelled by user")
            
            # Create namespace if needed
            if options.namespace:
                if not self._create_namespace_if_needed(options.namespace):
                    return ImportResult(False, f"Failed to create namespace: {options.namespace}")
            
            if not self._report_progress(0.2, "Preparing import..."):
                return ImportResult(False, "Import cancelled by user")
            
            # Store initial scene state for cleanup if needed
            initial_objects = set(cmds.ls(dag=True, long=True) or [])
            
            imported_objects = []
            warnings = []
            
            try:
                if options.import_mode == ImportMode.REFERENCE:
                    # Reference the file
                    if not self._report_progress(0.5, "Creating reference..."):
                        return ImportResult(False, "Import cancelled by user")
                    
                    ref_node = cmds.file(file_path, reference=True, 
                                       namespace=options.namespace or "",
                                       returnNewNodes=True)
                    
                    if ref_node:
                        imported_objects.extend(ref_node)
                        print(f"Referenced file: {file_path}")
                        if options.namespace:
                            print(f"  - Namespace: {options.namespace}")
                
                elif options.import_mode == ImportMode.IMPORT:
                    # Import the file
                    if not self._report_progress(0.5, "Importing scene..."):
                        return ImportResult(False, "Import cancelled by user")
                    
                    imported_nodes = cmds.file(file_path, i=True,
                                             namespace=options.namespace or "",
                                             returnNewNodes=True,
                                             preserveReferences=options.preserve_references)
                    
                    if imported_nodes:
                        imported_objects.extend(imported_nodes)
                        print(f"Imported file: {file_path}")
                        if options.namespace:
                            print(f"  - Namespace: {options.namespace}")
                
                elif options.import_mode == ImportMode.MERGE:
                    # Merge the file (no namespace)
                    if options.namespace:
                        warnings.append("Namespace ignored for merge mode")
                    
                    if not self._report_progress(0.5, "Merging scene..."):
                        return ImportResult(False, "Import cancelled by user")
                    
                    # Get objects before merge
                    pre_merge_objects = set(cmds.ls(dag=True, long=True) or [])
                    
                    cmds.file(file_path, i=True, mergeNamespacesOnClash=True)
                    
                    # Get objects after merge
                    post_merge_objects = set(cmds.ls(dag=True, long=True) or [])
                    new_objects = post_merge_objects - pre_merge_objects
                    imported_objects.extend(list(new_objects))
                    
                    print(f"Merged file: {file_path}")
                
                else:
                    return ImportResult(False, f"Unsupported import mode: {options.import_mode}")
                
                if not self._report_progress(0.9, "Finalizing import..."):
                    # Don't cancel at this point, import is mostly done
                    pass
                
                # Apply post-import options
                if options.select_imported and imported_objects:
                    try:
                        # Filter objects that still exist
                        existing_objects = [obj for obj in imported_objects if cmds.objExists(obj)]
                        if existing_objects:
                            cmds.select(existing_objects)
                    except Exception as e:
                        warnings.append(f"Could not select imported objects: {e}")
                
                self._report_progress(1.0, "Import completed")
                
                success_msg = f"Successfully imported {len(imported_objects)} objects from {os.path.basename(file_path)}"
                return ImportResult(True, success_msg, imported_objects, warnings)
                
            except Exception as e:
                # Clean up on error
                current_objects = set(cmds.ls(dag=True, long=True) or [])
                new_objects = current_objects - initial_objects
                if new_objects:
                    self._cleanup_on_error(list(new_objects))
                
                return ImportResult(False, f"Import failed: {str(e)}")
                
        except Exception as e:
            return ImportResult(False, f"Import error: {str(e)}")
    
    def import_with_progress(self, file_path: str, options: ImportOptions,
                           progress_callback=None) -> ImportResult:
        """
        Import file with progress reporting.
        
        Args:
            file_path: Path to file to import
            options: Import options
            progress_callback: Progress callback function
            
        Returns:
            ImportResult with operation details
        """
        if progress_callback:
            self.set_progress_callback(progress_callback)
        
        return self.import_file(file_path, options)
    
    def batch_import(self, file_paths: List[str], options: ImportOptions) -> List[ImportResult]:
        """
        Import multiple files with the same options.
        
        Args:
            file_paths: List of file paths to import
            options: Import options to apply to all files
            
        Returns:
            List of ImportResult objects
        """
        results = []
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            if self._cancel_requested:
                break
            
            # Update progress for batch operation
            batch_progress = i / total_files
            self._report_progress(batch_progress, f"Importing file {i+1} of {total_files}")
            
            result = self.import_file(file_path, options)
            results.append(result)
            
            if not result.success:
                print(f"Failed to import {file_path}: {result.message}")
        
        return results
