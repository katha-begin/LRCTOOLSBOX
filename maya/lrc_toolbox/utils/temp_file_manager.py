# -*- coding: utf-8 -*-
"""
Temporary File Manager

Manages temporary scene files for batch rendering with cleanup and retention policies.
"""

import os
import glob
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from ..config.batch_render_defaults import get_batch_render_defaults


class TempFileManager:
    """
    Manages temporary files for batch rendering.
    
    Features:
    - Creates unique temporary scene files
    - Tracks created files
    - Cleanup with retention policy
    - Age-based cleanup
    """
    
    def __init__(self):
        """Initialize temp file manager."""
        self._settings = get_batch_render_defaults()
        self._temp_dir = self._settings["file_management"]["temp_directory"]
        self._keep_latest = self._settings["file_management"]["keep_latest_files"]
        self._created_files: List[str] = []
        
        # Ensure temp directory exists
        self._ensure_temp_directory()
    
    def _ensure_temp_directory(self) -> None:
        """Ensure temporary directory exists."""
        try:
            os.makedirs(self._temp_dir, exist_ok=True)
        except Exception as e:
            print(f"[TempFile] Failed to create temp directory: {e}")
    
    def generate_temp_filename(self, scene_name: str, layer_name: str, 
                              process_id: str) -> str:
        """
        Generate unique temporary filename.
        
        Format: render_{sceneName}_{timestamp}_{layerName}_{processId}.ma
        
        Args:
            scene_name: Original scene name (without extension)
            layer_name: Render layer name
            process_id: Process ID
            
        Returns:
            Full path to temporary file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean names for filename
        scene_clean = self._clean_filename(scene_name)
        layer_clean = self._clean_filename(layer_name)
        
        filename = f"render_{scene_clean}_{timestamp}_{layer_clean}_{process_id}.ma"
        filepath = os.path.join(self._temp_dir, filename)
        
        return filepath
    
    def _clean_filename(self, name: str) -> str:
        """
        Clean string for use in filename.
        
        Args:
            name: String to clean
            
        Returns:
            Cleaned string safe for filename
        """
        # Remove file extension if present
        name = os.path.splitext(name)[0]
        
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Remove spaces
        name = name.replace(' ', '_')
        
        return name
    
    def register_file(self, filepath: str) -> None:
        """
        Register created temporary file for tracking.
        
        Args:
            filepath: Path to temporary file
        """
        if filepath not in self._created_files:
            self._created_files.append(filepath)
    
    def cleanup_temp_files(self, keep_latest: Optional[int] = None) -> int:
        """
        Cleanup temporary files with retention policy.
        
        Args:
            keep_latest: Number of latest files to keep (None = use default)
            
        Returns:
            Number of files deleted
        """
        if keep_latest is None:
            keep_latest = self._keep_latest
        
        try:
            # Get all temp files
            pattern = os.path.join(self._temp_dir, "render_*.ma")
            temp_files = glob.glob(pattern)
            
            if not temp_files:
                return 0
            
            # Sort by modification time (newest first)
            temp_files.sort(key=os.path.getmtime, reverse=True)
            
            # Keep latest N files, delete the rest
            files_to_delete = temp_files[keep_latest:]
            
            deleted_count = 0
            for filepath in files_to_delete:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    print(f"[TempFile] Deleted: {os.path.basename(filepath)}")
                except Exception as e:
                    print(f"[TempFile] Failed to delete {filepath}: {e}")
            
            if deleted_count > 0:
                print(f"[TempFile] Cleanup: Deleted {deleted_count} files, "
                      f"kept {len(temp_files) - deleted_count} latest")
            
            return deleted_count
            
        except Exception as e:
            print(f"[TempFile] Cleanup failed: {e}")
            return 0
    
    def cleanup_old_files(self, max_age_hours: Optional[int] = None) -> int:
        """
        Cleanup temporary files older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours (None = use default)
            
        Returns:
            Number of files deleted
        """
        if max_age_hours is None:
            max_age_hours = self._settings["file_management"]["auto_cleanup_age_hours"]
        
        try:
            pattern = os.path.join(self._temp_dir, "render_*.ma")
            temp_files = glob.glob(pattern)
            
            if not temp_files:
                return 0
            
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            deleted_count = 0
            for filepath in temp_files:
                try:
                    file_age = current_time - os.path.getmtime(filepath)
                    
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        deleted_count += 1
                        print(f"[TempFile] Deleted old file: {os.path.basename(filepath)}")
                        
                except Exception as e:
                    print(f"[TempFile] Failed to delete {filepath}: {e}")
            
            if deleted_count > 0:
                print(f"[TempFile] Cleanup: Deleted {deleted_count} files older than "
                      f"{max_age_hours} hours")
            
            return deleted_count
            
        except Exception as e:
            print(f"[TempFile] Age-based cleanup failed: {e}")
            return 0
    
    def delete_file(self, filepath: str) -> bool:
        """
        Delete specific temporary file.
        
        Args:
            filepath: Path to file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                
                if filepath in self._created_files:
                    self._created_files.remove(filepath)
                
                print(f"[TempFile] Deleted: {os.path.basename(filepath)}")
                return True
            
            return False
            
        except Exception as e:
            print(f"[TempFile] Failed to delete {filepath}: {e}")
            return False
    
    def get_temp_files(self) -> List[str]:
        """
        Get list of all temporary files.
        
        Returns:
            List of temporary file paths
        """
        try:
            pattern = os.path.join(self._temp_dir, "render_*.ma")
            return glob.glob(pattern)
        except Exception as e:
            print(f"[TempFile] Failed to list temp files: {e}")
            return []
    
    def get_temp_file_count(self) -> int:
        """
        Get count of temporary files.
        
        Returns:
            Number of temporary files
        """
        return len(self.get_temp_files())
    
    def cleanup_all(self) -> int:
        """
        Delete all temporary files (no retention).
        
        Returns:
            Number of files deleted
        """
        return self.cleanup_temp_files(keep_latest=0)

