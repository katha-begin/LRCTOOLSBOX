"""
Base Importer

This module provides the base importer interface and common functionality
for all import operations in the LRC Toolbox.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple, Callable
from datetime import datetime
from enum import Enum

from ..core.models import ImportOptions, ProgressCallback


class ImportMode(Enum):
    """Import mode enumeration."""
    REFERENCE = "reference"
    IMPORT = "import"
    MERGE = "merge"


class ImportResult:
    """Result of an import operation."""
    
    def __init__(self, success: bool, message: str, imported_objects: List[str] = None,
                 warnings: List[str] = None, errors: List[str] = None):
        self.success = success
        self.message = message
        self.imported_objects = imported_objects or []
        self.warnings = warnings or []
        self.errors = errors or []
        self.import_time = datetime.now()


class BaseImporter(ABC):
    """
    Base class for all importers in the LRC Toolbox.
    
    Provides common functionality and interface for importing various file types
    into Maya scenes with proper error handling and progress reporting.
    """
    
    def __init__(self):
        """Initialize base importer."""
        self._maya_available = self._check_maya_availability()
        self._progress_callback: Optional[ProgressCallback] = None
        self._cancel_requested = False
    
    def _check_maya_availability(self) -> bool:
        """Check if Maya is available."""
        try:
            import maya.cmds as cmds
            return True
        except ImportError:
            return False
    
    def set_progress_callback(self, callback: ProgressCallback) -> None:
        """Set progress callback for reporting import progress."""
        self._progress_callback = callback
    
    def cancel_import(self) -> None:
        """Request cancellation of current import operation."""
        self._cancel_requested = True
    
    def _report_progress(self, progress: float, message: str = "") -> bool:
        """
        Report progress and check for cancellation.
        
        Args:
            progress: Progress value between 0.0 and 1.0
            message: Progress message
            
        Returns:
            True if should continue, False if cancelled
        """
        if self._cancel_requested:
            return False
        
        if self._progress_callback:
            self._progress_callback(progress, message)
        
        return True
    
    def _validate_file_path(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate that the file path exists and is accessible.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path:
            return False, "File path is empty"
        
        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"
        
        if not os.path.isfile(file_path):
            return False, f"Path is not a file: {file_path}"
        
        if not os.access(file_path, os.R_OK):
            return False, f"File is not readable: {file_path}"
        
        return True, ""
    
    def _validate_import_options(self, options: ImportOptions) -> Tuple[bool, str]:
        """
        Validate import options.
        
        Args:
            options: Import options to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not options:
            return False, "Import options are required"
        
        # Validate namespace
        if options.namespace and not self._is_valid_namespace(options.namespace):
            return False, f"Invalid namespace: {options.namespace}"
        
        return True, ""
    
    def _is_valid_namespace(self, namespace: str) -> bool:
        """Check if namespace is valid for Maya."""
        if not namespace:
            return True  # Empty namespace is valid
        
        # Maya namespace rules: alphanumeric and underscore, no spaces
        import re
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', namespace))
    
    def _create_namespace_if_needed(self, namespace: str) -> bool:
        """
        Create namespace in Maya if it doesn't exist.
        
        Args:
            namespace: Namespace to create
            
        Returns:
            True if successful or already exists
        """
        if not self._maya_available or not namespace:
            return True
        
        try:
            import maya.cmds as cmds
            
            if not cmds.namespace(exists=namespace):
                cmds.namespace(add=namespace)
                print(f"Created namespace: {namespace}")
            
            return True
            
        except Exception as e:
            print(f"Error creating namespace '{namespace}': {e}")
            return False
    
    def _cleanup_on_error(self, imported_objects: List[str]) -> None:
        """
        Clean up imported objects on error.
        
        Args:
            imported_objects: List of objects to clean up
        """
        if not self._maya_available or not imported_objects:
            return
        
        try:
            import maya.cmds as cmds
            
            for obj in imported_objects:
                if cmds.objExists(obj):
                    try:
                        cmds.delete(obj)
                    except Exception as e:
                        print(f"Warning: Could not clean up object '{obj}': {e}")
            
            print(f"Cleaned up {len(imported_objects)} objects after error")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    @abstractmethod
    def import_file(self, file_path: str, options: ImportOptions) -> ImportResult:
        """
        Import file with specified options.
        
        Args:
            file_path: Path to file to import
            options: Import options
            
        Returns:
            ImportResult with operation details
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.
        
        Returns:
            List of supported extensions (e.g., ['.ma', '.mb'])
        """
        pass
    
    def can_import_file(self, file_path: str) -> bool:
        """
        Check if this importer can handle the specified file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if this importer can handle the file
        """
        if not file_path:
            return False
        
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in self.get_supported_extensions()
