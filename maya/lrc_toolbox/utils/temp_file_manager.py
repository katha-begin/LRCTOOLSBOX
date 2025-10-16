# -*- coding: utf-8 -*-
"""
Temporary File Manager

Manages temporary scene files for batch rendering with cleanup and retention policies.
Uses context-aware directory structure based on scene path.
"""

import os
import re
import glob
from datetime import datetime
from typing import List, Optional, Tuple
from pathlib import Path

from ..config.batch_render_defaults import get_batch_render_defaults
from ..core.models import NavigationContext, ProjectType


class TempFileManager:
    """
    Manages temporary files for batch rendering.

    Features:
    - Context-aware directory structure (shots/assets)
    - Creates unique temporary scene files
    - Tracks created files
    - Cleanup with retention policy
    - Age-based cleanup
    - Fallback to user Documents folder
    """

    def __init__(self):
        """Initialize temp file manager."""
        self._settings = get_batch_render_defaults()
        self._keep_latest = self._settings["file_management"]["keep_latest_files"]
        self._created_files: List[str] = []

        # Import context detector
        from ..utils.context_detector import context_detector
        self._context_detector = context_detector
    
    def generate_temp_filepath(self, scene_path: str, layer_name: str,
                              process_id: str) -> str:
        """
        Generate context-aware temporary file path.

        Path structure:
        - Shots: V:/SWA/all/scene/.tmp/Ep01/sq0010/SH0010/{dept}/MASTER_BG_A/render_SH0010_lighting_v001_timestamp_pid.ma
        - Assets: V:/SWA/all/asset/.tmp/characters/main/hero_char/{dept}/HERO_CHAR_BG_A/render_hero_char_lighting_v001_timestamp_pid.ma
        - Fallback: ~/Documents/maya_batch_tmp/MASTER_BG_A/render_unknown_timestamp_pid.ma

        Args:
            scene_path: Full path to current Maya scene
            layer_name: Render layer name
            process_id: Process ID

        Returns:
            Full path to temporary file with context-based directory structure
        """
        # Detect context from scene path
        context = self._context_detector.detect_context_from_path(scene_path)

        # Extract version from scene path
        version = self._extract_version_from_path(scene_path)

        if context:
            # Build context-based path
            temp_dir = self._build_context_temp_dir(scene_path, context, layer_name)
            filename = self._generate_context_filename(context, layer_name, version, process_id)
        else:
            # Fallback to user Documents folder
            temp_dir = self._build_fallback_temp_dir(layer_name)
            scene_name = os.path.splitext(os.path.basename(scene_path))[0] if scene_path else "unknown"
            filename = self._generate_fallback_filename(scene_name, version, process_id)

        # Ensure directory exists
        try:
            os.makedirs(temp_dir, exist_ok=True)
            print(f"[TempFile] Created temp directory: {temp_dir}")
        except Exception as e:
            print(f"[TempFile] Failed to create temp directory: {e}")
            # Ultimate fallback to current directory
            temp_dir = "."

        filepath = os.path.join(temp_dir, filename)
        print(f"[TempFile] Generated temp path: {filepath}")

        return filepath
    
    def _extract_version_from_path(self, scene_path: str) -> str:
        """
        Extract version number from scene path.

        Args:
            scene_path: Full scene path

        Returns:
            Version string (e.g., "v001") or empty string if not found
        """
        if not scene_path:
            return ""

        # Look for version pattern: _v001, _v0001, etc.
        match = re.search(r'_v(\d{3,4})', scene_path, re.IGNORECASE)
        if match:
            return f"v{match.group(1)}"

        return ""

    def _build_context_temp_dir(self, scene_path: str, context: NavigationContext,
                               layer_name: str) -> str:
        """
        Build temp directory path based on context.

        Args:
            scene_path: Full scene path
            context: Navigation context
            layer_name: Render layer name

        Returns:
            Temp directory path
        """
        # CRITICAL FIX: Clean layer name for directory path
        clean_layer = self._clean_filename(layer_name)

        # Find project root (path up to /scene/ or /asset/)
        if context.type == ProjectType.SHOT:
            # Find /scene/ in path
            match = re.search(r'(.+[/\\]scene)[/\\]', scene_path, re.IGNORECASE)
            if match:
                scene_root = match.group(1)
                return os.path.join(
                    scene_root,
                    ".tmp",
                    context.episode,
                    context.sequence,
                    context.shot,
                    context.department,
                    clean_layer  # Use cleaned name
                )
        else:  # ASSET
            # Find /asset/ in path
            match = re.search(r'(.+[/\\]asset)[/\\]', scene_path, re.IGNORECASE)
            if match:
                asset_root = match.group(1)
                return os.path.join(
                    asset_root,
                    ".tmp",
                    context.category,
                    context.subcategory,
                    context.asset,
                    context.department,
                    clean_layer  # Use cleaned name
                )

        # Fallback if pattern not found
        return self._build_fallback_temp_dir(layer_name)

    def _build_fallback_temp_dir(self, layer_name: str) -> str:
        """
        Build fallback temp directory in user Documents folder.

        Args:
            layer_name: Render layer name

        Returns:
            Fallback temp directory path
        """
        # CRITICAL FIX: Clean layer name for directory path
        clean_layer = self._clean_filename(layer_name)

        # Get user Documents folder
        if os.name == 'nt':  # Windows
            documents = os.path.join(os.path.expanduser('~'), 'Documents')
        else:  # Unix/Mac
            documents = os.path.expanduser('~/Documents')

        return os.path.join(documents, 'maya_batch_tmp', clean_layer)

    def _generate_context_filename(self, context: NavigationContext, layer_name: str,
                                   version: str, process_id: str) -> str:
        """
        Generate filename for context-based temp file.

        Format: render_{prefix}_{dept}_{version}_{timestamp}_{pid}.ma

        Args:
            context: Navigation context
            layer_name: Render layer name
            version: Version string (e.g., "v001")
            process_id: Process ID

        Returns:
            Filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if context.type == ProjectType.SHOT:
            prefix = context.shot
        else:
            prefix = context.asset

        dept = context.department

        # Build filename
        parts = ["render", prefix, dept]
        if version:
            parts.append(version)
        parts.extend([timestamp, process_id])

        return "_".join(parts) + ".ma"

    def _generate_fallback_filename(self, scene_name: str, version: str,
                                   process_id: str) -> str:
        """
        Generate filename for fallback temp file.

        Args:
            scene_name: Scene name
            version: Version string
            process_id: Process ID

        Returns:
            Filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scene_clean = self._clean_filename(scene_name)

        parts = ["render", scene_clean]
        if version:
            parts.append(version)
        parts.extend([timestamp, process_id])

        return "_".join(parts) + ".ma"

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

        # CRITICAL FIX: Remove newlines and other whitespace
        name = name.replace('\n', '_').replace('\r', '_').replace('\t', '_')
        name = ' '.join(name.split())  # Normalize whitespace

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
    
    def cleanup_temp_files(self, temp_root: Optional[str] = None,
                          keep_latest: Optional[int] = None) -> int:
        """
        Cleanup temporary files with retention policy.

        Args:
            temp_root: Root temp directory to clean (None = search common locations)
            keep_latest: Number of latest files to keep (None = use default)

        Returns:
            Number of files deleted
        """
        if keep_latest is None:
            keep_latest = self._keep_latest

        try:
            # Find all temp files
            temp_files = self._find_all_temp_files(temp_root)

            if not temp_files:
                print("[TempFile] No temp files found")
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
                    print(f"[TempFile] Deleted: {filepath}")
                except Exception as e:
                    print(f"[TempFile] Failed to delete {filepath}: {e}")

            if deleted_count > 0:
                print(f"[TempFile] Cleanup: Deleted {deleted_count} files, "
                      f"kept {len(temp_files) - deleted_count} latest")

            return deleted_count

        except Exception as e:
            print(f"[TempFile] Cleanup failed: {e}")
            return 0
    
    def cleanup_old_files(self, temp_root: Optional[str] = None,
                         max_age_hours: Optional[int] = None) -> int:
        """
        Cleanup temporary files older than specified age.

        Args:
            temp_root: Root temp directory to clean (None = search common locations)
            max_age_hours: Maximum age in hours (None = use default)

        Returns:
            Number of files deleted
        """
        if max_age_hours is None:
            max_age_hours = self._settings["file_management"]["auto_cleanup_age_hours"]

        try:
            # Find all temp files
            temp_files = self._find_all_temp_files(temp_root)

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
                        print(f"[TempFile] Deleted old file: {filepath}")

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
    
    def _find_all_temp_files(self, temp_root: Optional[str] = None) -> List[str]:
        """
        Find all temporary render files.

        Args:
            temp_root: Root directory to search (None = search common locations)

        Returns:
            List of temp file paths
        """
        temp_files = []

        if temp_root:
            # Search in specified root
            for root, dirs, files in os.walk(temp_root):
                for file in files:
                    if file.startswith("render_") and file.endswith(".ma"):
                        temp_files.append(os.path.join(root, file))
        else:
            # Search in common locations
            search_paths = []

            # 1. Check current scene path for .tmp directory
            try:
                scene_path = self._context_detector.get_current_scene_path()
                if scene_path:
                    context = self._context_detector.detect_context_from_path(scene_path)
                    if context:
                        if context.type == ProjectType.SHOT:
                            match = re.search(r'(.+[/\\]scene)[/\\]', scene_path, re.IGNORECASE)
                            if match:
                                search_paths.append(os.path.join(match.group(1), ".tmp"))
                        else:
                            match = re.search(r'(.+[/\\]asset)[/\\]', scene_path, re.IGNORECASE)
                            if match:
                                search_paths.append(os.path.join(match.group(1), ".tmp"))
            except:
                pass

            # 2. Check user Documents folder
            if os.name == 'nt':
                documents = os.path.join(os.path.expanduser('~'), 'Documents')
            else:
                documents = os.path.expanduser('~/Documents')
            search_paths.append(os.path.join(documents, 'maya_batch_tmp'))

            # Search all paths
            for search_path in search_paths:
                if os.path.exists(search_path):
                    for root, dirs, files in os.walk(search_path):
                        for file in files:
                            if file.startswith("render_") and file.endswith(".ma"):
                                temp_files.append(os.path.join(root, file))

        return temp_files

    def get_temp_files(self, temp_root: Optional[str] = None) -> List[str]:
        """
        Get list of all temporary files.

        Args:
            temp_root: Root directory to search (None = search common locations)

        Returns:
            List of temporary file paths
        """
        try:
            return self._find_all_temp_files(temp_root)
        except Exception as e:
            print(f"[TempFile] Failed to list temp files: {e}")
            return []

    def get_temp_file_count(self, temp_root: Optional[str] = None) -> int:
        """
        Get count of temporary files.

        Args:
            temp_root: Root directory to search (None = search common locations)

        Returns:
            Number of temporary files
        """
        return len(self.get_temp_files(temp_root))

    def cleanup_all(self, temp_root: Optional[str] = None) -> int:
        """
        Delete all temporary files (no retention).

        Args:
            temp_root: Root directory to clean (None = search common locations)

        Returns:
            Number of files deleted
        """
        return self.cleanup_temp_files(temp_root, keep_latest=0)

