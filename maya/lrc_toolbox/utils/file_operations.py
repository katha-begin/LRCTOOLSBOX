"""
File Operations Utilities

This module provides real file operation utilities for copy, move, delete,
and other file system operations with proper error handling.
"""

import os
import shutil
import hashlib
import stat
from typing import List, Dict, Optional, Any, Tuple, Callable
from datetime import datetime
from pathlib import Path

from ..core.models import FileInfo, VersionInfo
from .logger import logger


class FileOperations:
    """
    File Operations utility class for handling real file system operations.

    Provides real file operations (copy, move, delete) with proper error
    handling and logging for production use.
    """

    def __init__(self):
        """Initialize File Operations."""
        self._operation_history = []
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None

    def set_progress_callback(self, callback: Optional[Callable[[int, int, str], None]]) -> None:
        """Set progress callback for file operations."""
        self._progress_callback = callback

    def _report_progress(self, current: int, total: int, operation: str) -> None:
        """Report progress to callback if set."""
        if self._progress_callback:
            self._progress_callback(current, total, operation)
        logger.log_file_operation(operation, "", progress=(current, total))

    def copy_file(self, source_path: str, destination_path: str,
                  overwrite: bool = False) -> Tuple[bool, str]:
        """
        Copy file from source to destination.

        Args:
            source_path: Source file path
            destination_path: Destination file path
            overwrite: Whether to overwrite existing files

        Returns:
            Tuple of (success, message)
        """
        try:
            # Log operation start
            logger.log_file_operation("copy", source_path, destination_path)
            self._report_progress(0, 1, f"Copying {os.path.basename(source_path)}")

            # Validate source file exists
            if not os.path.exists(source_path):
                error_msg = f"Source file does not exist: {source_path}"
                logger.log_file_operation("copy", source_path, destination_path, success=False, error=error_msg)
                return False, error_msg

            if not os.path.isfile(source_path):
                error_msg = f"Source path is not a file: {source_path}"
                logger.log_file_operation("copy", source_path, destination_path, success=False, error=error_msg)
                return False, error_msg

            # Check destination file existence
            if os.path.exists(destination_path) and not overwrite:
                error_msg = f"Destination file already exists: {destination_path}"
                logger.log_file_operation("copy", source_path, destination_path, success=False, error=error_msg)
                return False, error_msg

            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(destination_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            # Perform the copy operation
            shutil.copy2(source_path, destination_path)
            self._report_progress(1, 1, f"Copied {os.path.basename(source_path)}")

            # Verify copy was successful
            if not os.path.exists(destination_path):
                error_msg = "Copy operation failed: Destination file not created"
                logger.log_file_operation("copy", source_path, destination_path, success=False, error=error_msg)
                return False, error_msg

            self._log_operation("copy", source_path, destination_path)
            logger.log_file_operation("copy", source_path, destination_path, success=True)
            return True, f"File copied successfully to {destination_path}"

        except PermissionError as e:
            return False, f"Copy operation failed: Permission denied - {str(e)}"
        except OSError as e:
            return False, f"Copy operation failed: {str(e)}"
        except Exception as e:
            return False, f"Copy operation failed: Unexpected error - {str(e)}"
    
    def move_file(self, source_path: str, destination_path: str,
                  overwrite: bool = False) -> Tuple[bool, str]:
        """
        Move file from source to destination.

        Args:
            source_path: Source file path
            destination_path: Destination file path
            overwrite: Whether to overwrite existing files

        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate source file exists
            if not os.path.exists(source_path):
                return False, f"Source file does not exist: {source_path}"

            if not os.path.isfile(source_path):
                return False, f"Source path is not a file: {source_path}"

            # Check destination file existence
            if os.path.exists(destination_path) and not overwrite:
                return False, f"Destination file already exists: {destination_path}"

            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(destination_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            # Perform the move operation
            shutil.move(source_path, destination_path)

            # Verify move was successful
            if not os.path.exists(destination_path):
                return False, "Move operation failed: Destination file not created"

            if os.path.exists(source_path):
                return False, "Move operation failed: Source file still exists"

            self._log_operation("move", source_path, destination_path)
            return True, f"File moved successfully to {destination_path}"

        except PermissionError as e:
            return False, f"Move operation failed: Permission denied - {str(e)}"
        except OSError as e:
            return False, f"Move operation failed: {str(e)}"
        except Exception as e:
            return False, f"Move operation failed: Unexpected error - {str(e)}"
    
    def delete_file(self, file_path: str, confirm: bool = True) -> Tuple[bool, str]:
        """
        Delete file at specified path.

        Args:
            file_path: Path to file to delete
            confirm: Whether confirmation is required (for UI integration)

        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                return False, f"File does not exist: {file_path}"

            if not os.path.isfile(file_path):
                return False, f"Path is not a file: {file_path}"

            # Check if file is read-only
            if not os.access(file_path, os.W_OK):
                # Try to remove read-only attribute
                try:
                    os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                except OSError:
                    return False, f"Delete operation failed: File is read-only and cannot be modified"

            # Perform the delete operation
            os.remove(file_path)

            # Verify deletion was successful
            if os.path.exists(file_path):
                return False, "Delete operation failed: File still exists"

            self._log_operation("delete", file_path, None)
            return True, f"File deleted successfully: {file_path}"

        except PermissionError as e:
            return False, f"Delete operation failed: Permission denied - {str(e)}"
        except OSError as e:
            return False, f"Delete operation failed: {str(e)}"
        except Exception as e:
            return False, f"Delete operation failed: Unexpected error - {str(e)}"
    
    def create_directory(self, directory_path: str,
                        create_parents: bool = True) -> Tuple[bool, str]:
        """
        Create directory at specified path.

        Args:
            directory_path: Path to directory to create
            create_parents: Whether to create parent directories

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if directory already exists
            if os.path.exists(directory_path):
                if os.path.isdir(directory_path):
                    return True, f"Directory already exists: {directory_path}"
                else:
                    return False, f"Path exists but is not a directory: {directory_path}"

            # Create directory
            if create_parents:
                os.makedirs(directory_path, exist_ok=True)
            else:
                os.mkdir(directory_path)

            # Verify creation was successful
            if not os.path.exists(directory_path):
                return False, "Directory creation failed: Directory not created"

            self._log_operation("mkdir", directory_path, None)
            return True, f"Directory created successfully: {directory_path}"

        except PermissionError as e:
            return False, f"Directory creation failed: Permission denied - {str(e)}"
        except OSError as e:
            return False, f"Directory creation failed: {str(e)}"
        except Exception as e:
            return False, f"Directory creation failed: Unexpected error - {str(e)}"
    
    def list_directory(self, directory_path: str,
                      include_hidden: bool = False) -> List[FileInfo]:
        """
        List contents of directory.

        Args:
            directory_path: Path to directory to list
            include_hidden: Whether to include hidden files

        Returns:
            List of FileInfo objects
        """
        try:
            # Validate directory exists
            if not os.path.exists(directory_path):
                return []

            if not os.path.isdir(directory_path):
                return []

            files = []

            # List directory contents
            for item_name in os.listdir(directory_path):
                # Skip hidden files if not requested
                if not include_hidden and item_name.startswith('.'):
                    continue

                item_path = os.path.join(directory_path, item_name)

                try:
                    # Get file stats
                    stat_info = os.stat(item_path)
                    is_directory = os.path.isdir(item_path)

                    # Get file extension
                    file_ext = os.path.splitext(item_name)[1].lower()
                    file_type = file_ext[1:] if file_ext else "unknown"
                    if is_directory:
                        file_type = "directory"

                    # Create FileInfo object
                    file_info = FileInfo(
                        name=item_name,
                        path=item_path,
                        size=stat_info.st_size if not is_directory else 0,
                        modified_date=datetime.fromtimestamp(stat_info.st_mtime),
                        file_type=file_type,
                        is_directory=is_directory,
                        metadata={
                            "permissions": oct(stat_info.st_mode)[-3:],
                            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                            "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat()
                        }
                    )

                    files.append(file_info)

                except (OSError, IOError) as e:
                    # Skip files that can't be accessed
                    print(f"Warning: Could not access {item_path}: {e}")
                    continue

            # Sort files: directories first, then by name
            files.sort(key=lambda f: (not f.is_directory, f.name.lower()))
            return files

        except (OSError, IOError) as e:
            print(f"Error listing directory {directory_path}: {e}")
            return []
    
    def get_file_info(self, file_path: str) -> Optional[FileInfo]:
        """
        Get detailed information about a file.

        Args:
            file_path: Path to file

        Returns:
            FileInfo object or None if file doesn't exist
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return None

            # Get file stats
            stat_info = os.stat(file_path)
            file_name = os.path.basename(file_path)
            is_directory = os.path.isdir(file_path)

            # Get file extension
            file_ext = os.path.splitext(file_name)[1].lower()
            file_type = file_ext[1:] if file_ext else "unknown"
            if is_directory:
                file_type = "directory"

            # Get additional metadata
            metadata = {
                "permissions": oct(stat_info.st_mode)[-3:],
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                "inode": stat_info.st_ino,
                "device": stat_info.st_dev
            }

            # Add owner information if available
            try:
                if os.name != 'nt':  # Unix/Linux/Mac
                    import pwd
                    import grp
                    metadata["owner"] = pwd.getpwuid(stat_info.st_uid).pw_name
                    metadata["group"] = grp.getgrgid(stat_info.st_gid).gr_name
                else:  # Windows
                    import getpass
                    metadata["owner"] = getpass.getuser()
            except:
                metadata["owner"] = "unknown"

            return FileInfo(
                name=file_name,
                path=file_path,
                size=stat_info.st_size if not is_directory else 0,
                modified_date=datetime.fromtimestamp(stat_info.st_mtime),
                file_type=file_type,
                is_directory=is_directory,
                metadata=metadata
            )

        except (OSError, IOError) as e:
            print(f"Error getting file info for {file_path}: {e}")
            return None
    
    def backup_file(self, file_path: str, backup_suffix: str = "_backup") -> Tuple[bool, str]:
        """
        Create backup of file.

        Args:
            file_path: Path to file to backup
            backup_suffix: Suffix to add to backup file

        Returns:
            Tuple of (success, backup_path)
        """
        try:
            # Validate source file exists
            if not os.path.exists(file_path):
                return False, f"Source file does not exist: {file_path}"

            if not os.path.isfile(file_path):
                return False, f"Source path is not a file: {file_path}"

            # Generate backup path
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            name_part, ext_part = os.path.splitext(file_name)

            # Add timestamp to make backup unique
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{name_part}{backup_suffix}_{timestamp}{ext_part}"
            backup_path = os.path.join(file_dir, backup_name)

            # Perform backup (copy)
            shutil.copy2(file_path, backup_path)

            # Verify backup was successful
            if not os.path.exists(backup_path):
                return False, "Backup failed: Backup file not created"

            self._log_operation("backup", file_path, backup_path)
            return True, backup_path

        except PermissionError as e:
            return False, f"Backup failed: Permission denied - {str(e)}"
        except OSError as e:
            return False, f"Backup failed: {str(e)}"
        except Exception as e:
            return False, f"Backup failed: Unexpected error - {str(e)}"
    
    def calculate_checksum(self, file_path: str, algorithm: str = "md5") -> str:
        """
        Calculate checksum for file.

        Args:
            file_path: Path to file
            algorithm: Checksum algorithm (md5, sha1, sha256)

        Returns:
            Checksum string
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                return f"{algorithm}_file_not_found"

            if not os.path.isfile(file_path):
                return f"{algorithm}_not_a_file"

            # Select hash algorithm
            if algorithm.lower() == "md5":
                hash_obj = hashlib.md5()
            elif algorithm.lower() == "sha1":
                hash_obj = hashlib.sha1()
            elif algorithm.lower() == "sha256":
                hash_obj = hashlib.sha256()
            else:
                return f"{algorithm}_unsupported_algorithm"

            # Calculate checksum
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files efficiently
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)

            return f"{algorithm}_{hash_obj.hexdigest()}"

        except (IOError, OSError) as e:
            return f"{algorithm}_error_{str(e).replace(' ', '_')}"
        except Exception as e:
            return f"{algorithm}_unexpected_error"
    
    def get_disk_usage(self, path: str) -> Dict[str, int]:
        """
        Get disk usage information for path.

        Args:
            path: Path to check

        Returns:
            Dictionary with total, used, and free space in bytes
        """
        try:
            # Get disk usage using shutil.disk_usage (Python 3.3+)
            if hasattr(shutil, 'disk_usage'):
                total, used, free = shutil.disk_usage(path)
                return {
                    "total": total,
                    "used": used,
                    "free": free,
                    "percent_used": (used / total) * 100 if total > 0 else 0
                }
            else:
                # Fallback for older Python versions
                if os.name == 'nt':  # Windows
                    import ctypes
                    free_bytes = ctypes.c_ulonglong(0)
                    total_bytes = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        ctypes.c_wchar_p(path),
                        ctypes.pointer(free_bytes),
                        ctypes.pointer(total_bytes),
                        None
                    )
                    total = total_bytes.value
                    free = free_bytes.value
                    used = total - free
                else:  # Unix/Linux/Mac
                    statvfs = os.statvfs(path)
                    total = statvfs.f_frsize * statvfs.f_blocks
                    free = statvfs.f_frsize * statvfs.f_available
                    used = total - free

                return {
                    "total": total,
                    "used": used,
                    "free": free,
                    "percent_used": (used / total) * 100 if total > 0 else 0
                }

        except (OSError, IOError) as e:
            print(f"Error getting disk usage for {path}: {e}")
            return {
                "total": 0,
                "used": 0,
                "free": 0,
                "percent_used": 0
            }
    
    def get_operation_history(self) -> List[Dict[str, Any]]:
        """Get history of file operations."""
        return self._operation_history.copy()
    
    def clear_operation_history(self) -> None:
        """Clear operation history."""
        self._operation_history.clear()

    def _log_operation(self, operation: str, source: str, destination: Optional[str]) -> None:
        """Log file operation to history."""
        self._operation_history.append({
            "operation": operation,
            "source": source,
            "destination": destination,
            "timestamp": datetime.now().isoformat(),
            "success": True
        })


# Convenience functions
def copy_file(source: str, destination: str, overwrite: bool = False) -> Tuple[bool, str]:
    """Convenience function for copying files."""
    file_ops = FileOperations()
    return file_ops.copy_file(source, destination, overwrite)


def move_file(source: str, destination: str, overwrite: bool = False) -> Tuple[bool, str]:
    """Convenience function for moving files."""
    file_ops = FileOperations()
    return file_ops.move_file(source, destination, overwrite)


def delete_file(file_path: str, confirm: bool = True) -> Tuple[bool, str]:
    """Convenience function for deleting files."""
    file_ops = FileOperations()
    return file_ops.delete_file(file_path, confirm)


def create_backup(file_path: str, suffix: str = "_backup") -> Tuple[bool, str]:
    """Convenience function for creating backups."""
    file_ops = FileOperations()
    return file_ops.backup_file(file_path, suffix)


def get_file_info(file_path: str) -> Optional[FileInfo]:
    """Convenience function for getting file info."""
    file_ops = FileOperations()
    return file_ops.get_file_info(file_path)
