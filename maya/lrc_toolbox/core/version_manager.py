"""
Version Manager

This module provides version management functionality with real file system operations
for version creation, hero file management, and file listing.
"""

import os
import re
import shutil
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import hashlib

from .models import VersionInfo, FileInfo, NavigationContext


class VersionManager:
    """
    Version Manager for handling file versioning and hero file management.

    Provides real file system operations for version creation, hero file management,
    and file listing with version information.
    """

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize Version Manager.

        Args:
            project_root: Root path of the project
        """
        self.project_root = project_root or r"V:\SWA\all"
        self._version_pattern = re.compile(r'_v(\d{3,4})(?:\.|$)')
    
    def get_versions_for_file(self, base_file_path: str) -> List[VersionInfo]:
        """Get all versions for a base file by scanning the file system."""
        # Extract base name without version
        base_name = self._get_base_name(base_file_path)
        file_dir = os.path.dirname(base_file_path)
        file_ext = os.path.splitext(base_file_path)[1]

        # Check if directory exists
        if not os.path.exists(file_dir):
            return []

        # Scan directory for version files
        versions = []
        version_pattern = re.compile(rf'{re.escape(base_name)}_v(\d{{3,4}}){re.escape(file_ext)}$')

        try:
            for filename in os.listdir(file_dir):
                match = version_pattern.match(filename)
                if match:
                    version_number = int(match.group(1))
                    version_path = os.path.join(file_dir, filename)

                    # Get file stats
                    try:
                        stat = os.stat(version_path)
                        file_size = stat.st_size
                        created_date = datetime.fromtimestamp(stat.st_mtime)

                        # Check if this is a hero file (symlink or file with _hero suffix)
                        hero_path = os.path.join(file_dir, f"{base_name}_hero{file_ext}")
                        is_hero = os.path.exists(hero_path) and os.path.samefile(version_path, hero_path)

                        # Extract metadata from file if possible
                        metadata = self._extract_file_metadata(version_path)

                        versions.append(VersionInfo(
                            version_number=version_number,
                            file_path=version_path,
                            file_name=filename,
                            file_size=file_size,
                            created_date=created_date,
                            created_by=self._get_file_owner(version_path),
                            is_hero=is_hero,
                            is_published=False,  # TODO: Implement published status detection
                            comment=f"Version {version_number}",
                            checksum=self._calculate_checksum(version_path),
                            metadata=metadata
                        ))
                    except (OSError, IOError) as e:
                        print(f"Warning: Could not read file stats for {version_path}: {e}")
                        continue
        except OSError as e:
            print(f"Warning: Could not scan directory {file_dir}: {e}")
            return []

        # Sort versions by version number
        versions.sort(key=lambda v: v.version_number)
        return versions
    
    def get_latest_version(self, base_file_path: str) -> Optional[VersionInfo]:
        """Get the latest version of a file."""
        versions = self.get_versions_for_file(base_file_path)
        if not versions:
            return None
        
        return max(versions, key=lambda v: v.version_number)
    
    def get_hero_version(self, base_file_path: str) -> Optional[VersionInfo]:
        """Get the hero version of a file."""
        versions = self.get_versions_for_file(base_file_path)
        hero_versions = [v for v in versions if v.is_hero]
        
        if hero_versions:
            return hero_versions[0]
        
        # If no hero version, return latest
        return self.get_latest_version(base_file_path)
    
    def create_new_version(self, base_file_path: str, comment: str = "") -> VersionInfo:
        """Create a new version of a file with real file operations."""
        # Get current Maya scene file path if no base path provided
        if not base_file_path or not os.path.exists(base_file_path):
            try:
                import maya.cmds as cmds
                current_scene = cmds.file(q=True, sceneName=True)
                if current_scene:
                    base_file_path = current_scene
                else:
                    raise ValueError("No current scene file to version")
            except ImportError:
                raise ValueError("Maya not available and no valid file path provided")

        latest_version = self.get_latest_version(base_file_path)
        new_version_number = (latest_version.version_number + 1) if latest_version else 1

        base_name = self._get_base_name(base_file_path)
        file_dir = os.path.dirname(base_file_path)
        file_ext = os.path.splitext(base_file_path)[1]

        # Ensure version directory exists
        os.makedirs(file_dir, exist_ok=True)

        new_version_file = f"{base_name}_v{new_version_number:03d}{file_ext}"
        new_version_path = os.path.join(file_dir, new_version_file)

        try:
            # Save current Maya scene as new version
            import maya.cmds as cmds
            cmds.file(rename=new_version_path)
            cmds.file(save=True, type='mayaAscii' if file_ext == '.ma' else 'mayaBinary')

            # Get file stats
            stat = os.stat(new_version_path)
            file_size = stat.st_size
            created_date = datetime.fromtimestamp(stat.st_mtime)

            new_version = VersionInfo(
                version_number=new_version_number,
                file_path=new_version_path,
                file_name=new_version_file,
                file_size=file_size,
                created_date=created_date,
                created_by=self._get_current_user(),
                is_hero=False,  # Will be set to hero separately
                is_published=False,
                comment=comment or f"Version {new_version_number} created",
                checksum=self._calculate_checksum(new_version_path),
                metadata=self._extract_file_metadata(new_version_path)
            )

            print(f"Created new version: {new_version_file}")
            return new_version

        except ImportError:
            # Fallback: copy existing file if Maya not available
            if os.path.exists(base_file_path):
                shutil.copy2(base_file_path, new_version_path)
                stat = os.stat(new_version_path)

                new_version = VersionInfo(
                    version_number=new_version_number,
                    file_path=new_version_path,
                    file_name=new_version_file,
                    file_size=stat.st_size,
                    created_date=datetime.fromtimestamp(stat.st_mtime),
                    created_by=self._get_current_user(),
                    is_hero=False,
                    is_published=False,
                    comment=comment or f"Version {new_version_number} created",
                    checksum=self._calculate_checksum(new_version_path),
                    metadata={}
                )

                print(f"Created new version (file copy): {new_version_file}")
                return new_version
            else:
                raise FileNotFoundError(f"Source file not found: {base_file_path}")
    
    def set_hero_version(self, version_info: VersionInfo) -> bool:
        """Set a specific version as hero with real file operations."""
        try:
            base_name = self._get_base_name(version_info.file_path)
            file_dir = os.path.dirname(version_info.file_path)
            file_ext = os.path.splitext(version_info.file_path)[1]

            hero_path = os.path.join(file_dir, f"{base_name}_hero{file_ext}")

            # Remove existing hero file/link
            if os.path.exists(hero_path):
                if os.path.islink(hero_path):
                    os.unlink(hero_path)
                else:
                    os.remove(hero_path)

            # Create new hero link (Windows symlink or copy fallback)
            try:
                if os.name == 'nt':  # Windows
                    # Try to create symlink (requires admin rights or developer mode)
                    os.symlink(version_info.file_path, hero_path)
                else:  # Unix/Linux/Mac
                    os.symlink(version_info.file_path, hero_path)
                print(f"Created hero symlink: {os.path.basename(hero_path)} -> {version_info.file_name}")
            except OSError:
                # Fallback to hard copy if symlink fails
                shutil.copy2(version_info.file_path, hero_path)
                print(f"Created hero copy: {os.path.basename(hero_path)} (copied from {version_info.file_name})")

            return True

        except (OSError, IOError) as e:
            print(f"Error setting hero version: {e}")
            return False
    
    def publish_version(self, version_info: VersionInfo) -> bool:
        """Publish a specific version by creating a published marker file."""
        try:
            # Create a .published marker file alongside the version
            published_marker = f"{version_info.file_path}.published"

            with open(published_marker, 'w') as f:
                f.write(f"Published: {datetime.now().isoformat()}\n")
                f.write(f"Version: {version_info.version_number}\n")
                f.write(f"File: {version_info.file_name}\n")

            print(f"Published version {version_info.file_name}")
            return True

        except (OSError, IOError) as e:
            print(f"Error publishing version {version_info.file_name}: {e}")
            return False

    def delete_version(self, version_info: VersionInfo) -> bool:
        """Delete a specific version file."""
        try:
            # Prevent deletion of hero version
            if version_info.is_hero:
                print(f"Warning: Cannot delete hero version {version_info.file_name}")
                return False

            # Check if file exists
            if not os.path.exists(version_info.file_path):
                print(f"Warning: Version file does not exist: {version_info.file_path}")
                return False

            # Delete the version file
            os.remove(version_info.file_path)

            # Also delete published marker if it exists
            published_marker = f"{version_info.file_path}.published"
            if os.path.exists(published_marker):
                os.remove(published_marker)

            print(f"Deleted version {version_info.file_name}")
            return True

        except (OSError, IOError) as e:
            print(f"Error deleting version {version_info.file_name}: {e}")
            return False
    
    def get_version_history(self, base_file_path: str) -> List[Dict[str, Any]]:
        """Get version history with change information."""
        versions = self.get_versions_for_file(base_file_path)
        
        history = []
        for version in versions:
            history.append({
                "version": version.version_number,
                "date": version.created_date.isoformat(),
                "user": version.created_by,
                "comment": version.comment,
                "is_hero": version.is_hero,
                "is_published": version.is_published,
                "file_size": version.file_size,
                "changes": self._get_version_changes(version)
            })
        
        return history
    
    def backup_current_version(self, file_path: str) -> bool:
        """Create backup of current version."""
        try:
            if not os.path.exists(file_path):
                print(f"Warning: File does not exist: {file_path}")
                return False

            # Generate backup path with timestamp
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            name_part, ext_part = os.path.splitext(file_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{name_part}_backup_{timestamp}{ext_part}"
            backup_path = os.path.join(file_dir, backup_name)

            # Create backup
            shutil.copy2(file_path, backup_path)
            print(f"Created backup at {backup_path}")
            return True

        except (OSError, IOError) as e:
            print(f"Error creating backup: {e}")
            return False

    def restore_version(self, version_info: VersionInfo, target_path: str) -> bool:
        """Restore a specific version to target path."""
        try:
            if not os.path.exists(version_info.file_path):
                print(f"Warning: Version file does not exist: {version_info.file_path}")
                return False

            # Create target directory if needed
            target_dir = os.path.dirname(target_path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)

            # Copy version file to target
            shutil.copy2(version_info.file_path, target_path)
            print(f"Restored {version_info.file_name} to {target_path}")
            return True

        except (OSError, IOError) as e:
            print(f"Error restoring version: {e}")
            return False
    
    def get_version_comparison(self, version1: VersionInfo, version2: VersionInfo) -> Dict[str, Any]:
        """Get comparison between two versions (mock implementation)."""
        return {
            "version1": version1.version_number,
            "version2": version2.version_number,
            "size_diff": version2.file_size - version1.file_size,
            "time_diff": (version2.created_date - version1.created_date).days,
            "changes": [
                "Added 3 new lights",
                "Modified render layer settings",
                "Updated material assignments",
                "Fixed light naming conventions"
            ],
            "compatibility": "Compatible"
        }
    
    def _get_base_name(self, file_path: str) -> str:
        """Extract base name without version suffix."""
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Remove version suffix if present
        match = self._version_pattern.search(file_name)
        if match:
            return file_name[:match.start()]
        
        return file_name
    
    def _generate_version_comment(self, version_number: int, is_published: bool) -> str:
        """Generate realistic version comments."""
        comments = [
            "Initial lighting setup",
            "Added key lights and shadows",
            "Refined light positioning",
            "Updated render layer assignments",
            "Fixed light naming issues",
            "Optimized render settings",
            "Added atmospheric effects",
            "Final lighting adjustments"
        ]
        
        base_comment = comments[min(version_number - 1, len(comments) - 1)]
        
        if is_published:
            return f"{base_comment} - PUBLISHED"
        
        return base_comment
    
    def _get_version_changes(self, version: VersionInfo) -> List[str]:
        """Get version changes from comment or file analysis."""
        changes = []

        # Parse comment for change information
        if version.comment:
            # Split comment by common delimiters
            comment_parts = version.comment.replace(',', '\n').replace(';', '\n').split('\n')
            changes = [part.strip() for part in comment_parts if part.strip()]

        # If no changes found in comment, provide generic info
        if not changes:
            changes = [f"Version {version.version_number} created"]
            if version.is_published:
                changes.append("Published version")

        return changes

    def _extract_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from Maya file."""
        metadata = {}
        try:
            if file_path.endswith(('.ma', '.mb')):
                # Try to extract basic Maya metadata without loading the file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read first few lines for Maya header info
                    for i, line in enumerate(f):
                        if i > 20:  # Only check first 20 lines
                            break
                        if 'Maya' in line and 'version' in line:
                            metadata['maya_version'] = line.strip()
                        elif 'currentUnit' in line:
                            metadata['scene_units'] = line.strip()
                        elif 'Arnold' in line:
                            metadata['renderer'] = 'Arnold'

            # Add file system metadata
            stat = os.stat(file_path)
            metadata.update({
                'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created_from': 'LRC Toolbox'
            })

        except (IOError, OSError) as e:
            print(f"Warning: Could not extract metadata from {file_path}: {e}")

        return metadata

    def _get_file_owner(self, file_path: str) -> str:
        """Get file owner/creator."""
        try:
            if os.name == 'nt':  # Windows
                # Windows doesn't have pwd module, use alternative approach
                import getpass
                return getpass.getuser()
            else:  # Unix/Linux/Mac
                import pwd
                stat = os.stat(file_path)
                return pwd.getpwuid(stat.st_uid).pw_name
        except:
            # Fallback to environment user
            return os.environ.get('USER', os.environ.get('USERNAME', 'Unknown'))

    def _get_current_user(self) -> str:
        """Get current system user."""
        return os.environ.get('USER', os.environ.get('USERNAME', 'Unknown'))

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return f"md5_{hash_md5.hexdigest()[:8]}"
        except (IOError, OSError):
            return f"md5_unknown_{int(datetime.now().timestamp())}"
