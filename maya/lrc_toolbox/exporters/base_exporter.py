"""
Base Exporter

This module provides the base exporter interface and common functionality
for all export operations in the LRC Toolbox.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple, Callable
from datetime import datetime
from enum import Enum

from ..core.models import ExportOptions, ProgressCallback


class ExportFormat(Enum):
    """Export format enumeration."""
    MAYA_ASCII = "ma"
    MAYA_BINARY = "mb"
    JSON = "json"
    XML = "xml"


class ExportResult:
    """Result of an export operation."""
    
    def __init__(self, success: bool, message: str, exported_file: str = None,
                 exported_objects: List[str] = None, warnings: List[str] = None, 
                 errors: List[str] = None):
        self.success = success
        self.message = message
        self.exported_file = exported_file
        self.exported_objects = exported_objects or []
        self.warnings = warnings or []
        self.errors = errors or []
        self.export_time = datetime.now()


class BaseExporter(ABC):
    """
    Base class for all exporters in the LRC Toolbox.
    
    Provides common functionality and interface for exporting various content
    from Maya scenes with proper error handling and progress reporting.
    """
    
    def __init__(self):
        """Initialize base exporter."""
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
        """Set progress callback for reporting export progress."""
        self._progress_callback = callback
    
    def cancel_export(self) -> None:
        """Request cancellation of current export operation."""
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
    
    def _validate_export_path(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate that the export path is writable.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path:
            return False, "Export path is empty"
        
        # Check directory exists and is writable
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except OSError as e:
                return False, f"Cannot create directory: {e}"
        
        if directory and not os.access(directory, os.W_OK):
            return False, f"Directory is not writable: {directory}"
        
        # Check if file exists and is writable
        if os.path.exists(file_path) and not os.access(file_path, os.W_OK):
            return False, f"File is not writable: {file_path}"
        
        return True, ""
    
    def _validate_export_options(self, options: ExportOptions) -> Tuple[bool, str]:
        """
        Validate export options.
        
        Args:
            options: Export options to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not options:
            return False, "Export options are required"
        
        return True, ""
    
    def _validate_objects_exist(self, objects: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate that objects exist in Maya scene.
        
        Args:
            objects: List of object names to validate
            
        Returns:
            Tuple of (existing_objects, missing_objects)
        """
        if not self._maya_available:
            return objects, []  # Can't validate without Maya
        
        try:
            import maya.cmds as cmds
            
            existing = []
            missing = []
            
            for obj in objects:
                if cmds.objExists(obj):
                    existing.append(obj)
                else:
                    missing.append(obj)
            
            return existing, missing
            
        except Exception as e:
            print(f"Error validating objects: {e}")
            return [], objects
    
    def _backup_existing_file(self, file_path: str) -> Optional[str]:
        """
        Create backup of existing file if it exists.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Backup file path if created, None otherwise
        """
        if not os.path.exists(file_path):
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.backup_{timestamp}"
            
            import shutil
            shutil.copy2(file_path, backup_path)
            
            print(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
            return None
    
    def _cleanup_on_error(self, file_path: str, backup_path: Optional[str] = None) -> None:
        """
        Clean up files on export error.
        
        Args:
            file_path: Export file path to clean up
            backup_path: Backup file path to restore if available
        """
        try:
            # Remove partial export file
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up partial export: {file_path}")
            
            # Restore backup if available
            if backup_path and os.path.exists(backup_path):
                import shutil
                shutil.move(backup_path, file_path)
                print(f"Restored backup: {file_path}")
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def _get_file_format_from_extension(self, file_path: str) -> Optional[ExportFormat]:
        """
        Determine export format from file extension.
        
        Args:
            file_path: File path to analyze
            
        Returns:
            ExportFormat or None if not recognized
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        format_map = {
            '.ma': ExportFormat.MAYA_ASCII,
            '.mb': ExportFormat.MAYA_BINARY,
            '.json': ExportFormat.JSON,
            '.xml': ExportFormat.XML
        }
        
        return format_map.get(ext)
    
    @abstractmethod
    def export_to_file(self, file_path: str, objects: List[str], 
                      options: ExportOptions) -> ExportResult:
        """
        Export objects to file with specified options.
        
        Args:
            file_path: Path to export file
            objects: List of objects to export
            options: Export options
            
        Returns:
            ExportResult with operation details
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[ExportFormat]:
        """
        Get list of supported export formats.
        
        Returns:
            List of supported ExportFormat values
        """
        pass
    
    def can_export_format(self, file_path: str) -> bool:
        """
        Check if this exporter can handle the specified file format.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if this exporter can handle the format
        """
        format_type = self._get_file_format_from_extension(file_path)
        return format_type in self.get_supported_formats() if format_type else False
