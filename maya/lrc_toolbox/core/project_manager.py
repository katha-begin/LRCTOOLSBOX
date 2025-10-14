"""
Project Manager

This module provides project management functionality with real directory
scanning for episodes, sequences, shots, and asset hierarchies.
"""

import os
import glob
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from .models import (
    ProjectInfo, ProjectType, NavigationContext, FileInfo, VersionInfo
)
from ..utils.logger import logger
from ..utils.error_handler import error_handler_decorator, ErrorCategory, handle_file_error


class ProjectManager:
    """
    Project Manager for handling project structure and navigation.

    Provides real directory scanning for episodes, sequences, shots, and asset hierarchies.
    """

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize Project Manager.

        Args:
            project_root: Root path of the project
        """
        self.project_root = project_root or r"V:\SWA\all"
        self._episodes = {}
        self._sequences = {}
        self._shots = {}
        self._categories = {}
        self._subcategories = {}
        self._assets = {}
        self._departments = {}

        self._initialize_project_data()
    
    def _initialize_project_data(self) -> None:
        """Initialize project data from real directory structure."""
        logger.log_directory_access(self.project_root, "check")

        # Check if project root exists
        if os.path.exists(self.project_root):
            self._scan_real_directories()
        else:
            # Try Maya workspace as fallback
            maya_workspace = self._get_maya_workspace()
            if maya_workspace and os.path.exists(maya_workspace):
                logger.log_maya_fallback(self.project_root, maya_workspace, "project root not found")
                self.project_root = maya_workspace
                self._scan_real_directories()
            else:
                logger.log_directory_access(self.project_root, "check", success=False,
                                          error="Project root and Maya workspace not accessible")
                # Initialize empty data structures
                self._initialize_empty_data()

    def _get_maya_workspace(self) -> Optional[str]:
        """Get Maya workspace directory as fallback."""
        try:
            import maya.cmds as cmds
            workspace = cmds.workspace(query=True, rootDirectory=True)
            logger.log_ui_operation("ProjectManager", "maya_workspace_query", workspace)
            return workspace
        except ImportError:
            logger.log_error("ProjectManager", Exception("Maya not available"), "workspace query")
            return None
        except Exception as e:
            logger.log_error("ProjectManager", e, "maya workspace query")
            return None

    def _initialize_empty_data(self) -> None:
        """Initialize empty data structures when no directories are accessible."""
        self._episodes = {}
        self._sequences = {}
        self._shots = {}
        self._categories = {}
        self._subcategories = {}
        self._assets = {}
        self._departments = {}
        logger.log_directory_access(self.project_root, "initialize", success=True,
                                  error="Using empty data structures")

    def _scan_real_directories(self) -> None:
        """Scan real directory structure for episodes, sequences, and shots."""
        start_time = time.time()
        logger.log_directory_access(self.project_root, "scan_start")

        # Scan for episodes in scene directory (V:\SWA\all\scene\Ep01)
        scene_dir = os.path.join(self.project_root, "scene")

        try:
            if os.path.exists(scene_dir):
                episode_pattern = os.path.join(scene_dir, "[Ee]p*")
                episode_dirs = glob.glob(episode_pattern)
                logger.log_directory_access(scene_dir, "episode_scan", success=True,
                                          item_count=len(episode_dirs))
            else:
                episode_dirs = []
                logger.log_directory_access(scene_dir, "episode_scan", success=False,
                                          error="Scene directory not found")
        except Exception as e:
            episode_dirs = []
            logger.log_error("ProjectManager", e, f"scanning episodes in {scene_dir}")

        self._episodes = {}
        self._sequences = {}
        self._shots = {}

        for episode_path in episode_dirs:
            try:
                if os.path.isdir(episode_path):
                    episode_name = os.path.basename(episode_path)
                    self._episodes[episode_name] = {
                        "name": episode_name,
                        "description": f"Episode from {episode_path}"
                    }

                    # Scan for sequences in this episode
                    seq_pattern = os.path.join(episode_path, "sq*")
                    seq_dirs = glob.glob(seq_pattern)
                    sequences = []

                    for seq_path in seq_dirs:
                        try:
                            if os.path.isdir(seq_path):
                                seq_name = os.path.basename(seq_path)
                                sequences.append(seq_name)

                                # Scan for shots in this sequence
                                shot_pattern = os.path.join(seq_path, "[Ss][Hh]*")
                                shot_dirs = glob.glob(shot_pattern)
                                shots = []

                                for shot_path in shot_dirs:
                                    try:
                                        if os.path.isdir(shot_path):
                                            shot_name = os.path.basename(shot_path)
                                            shots.append(shot_name)
                                    except Exception as e:
                                        logger.log_error("ProjectManager", e, f"scanning shot {shot_path}")

                                if shots:
                                    self._shots[seq_name] = sorted(shots)
                                    logger.log_directory_access(seq_path, "shot_scan", success=True,
                                                              item_count=len(shots))
                        except Exception as e:
                            logger.log_error("ProjectManager", e, f"scanning sequence {seq_path}")

                    if sequences:
                        self._sequences[episode_name] = sorted(sequences)
                        logger.log_directory_access(episode_path, "sequence_scan", success=True,
                                                  item_count=len(sequences))
            except Exception as e:
                logger.log_error("ProjectManager", e, f"scanning episode {episode_path}")

        # Scan for assets (look for 'asset' or 'assets' directory)
        asset_base_dirs = [
            os.path.join(self.project_root, "asset"),
            os.path.join(self.project_root, "assets"),
            os.path.join(self.project_root, "Asset"),
            os.path.join(self.project_root, "Assets")
        ]

        self._categories = {}
        self._subcategories = {}
        self._assets = {}

        for asset_base in asset_base_dirs:
            try:
                if os.path.exists(asset_base) and os.path.isdir(asset_base):
                    logger.log_directory_access(asset_base, "asset_base_scan")

                    # Scan for categories
                    category_paths = glob.glob(os.path.join(asset_base, "*"))
                    for category_path in category_paths:
                        try:
                            if os.path.isdir(category_path):
                                category_name = os.path.basename(category_path)
                                self._categories[category_name] = {
                                    "name": category_name,
                                    "description": f"Category from {category_path}"
                                }

                                # Scan for subcategories
                                subcategories = []
                                subcat_paths = glob.glob(os.path.join(category_path, "*"))
                                for subcat_path in subcat_paths:
                                    try:
                                        if os.path.isdir(subcat_path):
                                            subcat_name = os.path.basename(subcat_path)
                                            subcategories.append(subcat_name)

                                            # Scan for assets in this subcategory
                                            assets = []
                                            asset_paths = glob.glob(os.path.join(subcat_path, "*"))
                                            for asset_path in asset_paths:
                                                try:
                                                    if os.path.isdir(asset_path):
                                                        asset_name = os.path.basename(asset_path)
                                                        assets.append(asset_name)
                                                except Exception as e:
                                                    logger.log_error("ProjectManager", e, f"scanning asset {asset_path}")

                                            if assets:
                                                self._assets[subcat_name] = sorted(assets)
                                                logger.log_directory_access(subcat_path, "asset_scan", success=True,
                                                                          item_count=len(assets))
                                    except Exception as e:
                                        logger.log_error("ProjectManager", e, f"scanning subcategory {subcat_path}")

                                if subcategories:
                                    self._subcategories[category_name] = sorted(subcategories)
                                    logger.log_directory_access(category_path, "subcategory_scan", success=True,
                                                              item_count=len(subcategories))
                        except Exception as e:
                            logger.log_error("ProjectManager", e, f"scanning category {category_path}")

                    logger.log_directory_access(asset_base, "asset_base_complete", success=True,
                                              item_count=len(self._categories))
                    break  # Use first found asset directory
            except Exception as e:
                logger.log_error("ProjectManager", e, f"scanning asset base {asset_base}")

        # Scan for departments by looking at actual shot/asset directory structures
        self._scan_departments()

        # Log scan completion with performance metrics
        scan_duration = time.time() - start_time
        logger.log_network_performance(self.project_root, "directory_scan", scan_duration)

        total_episodes = len(self._episodes)
        total_sequences = sum(len(seqs) for seqs in self._sequences.values())
        total_shots = sum(len(shots) for shots in self._shots.values())
        total_categories = len(self._categories)
        total_subcategories = sum(len(subcats) for subcats in self._subcategories.values())
        total_assets = sum(len(assets) for assets in self._assets.values())
        total_departments = len(self._departments)

        logger.log_directory_access(self.project_root, "scan_complete", success=True,
                                  error=f"Episodes: {total_episodes}, Sequences: {total_sequences}, Shots: {total_shots}, "
                                        f"Categories: {total_categories}, Subcategories: {total_subcategories}, "
                                        f"Assets: {total_assets}, Departments: {total_departments}")

        # Note: No fallback mock data - empty structures are acceptable

    def _scan_departments(self) -> None:
        """Scan for departments in shot and asset directories."""
        shot_departments = set()
        asset_departments = set()

        # Scan shot departments (V:\SWA\all\scene\Ep01\sq0040\SH0210\[department])
        scene_dir = os.path.join(self.project_root, "scene")
        for episode_name in self._episodes:
            if episode_name in self._sequences:
                for seq_name in self._sequences[episode_name]:
                    if seq_name in self._shots:
                        for shot_name in self._shots[seq_name]:
                            shot_path = os.path.join(scene_dir, episode_name, seq_name, shot_name)
                            if os.path.exists(shot_path):
                                for dept in os.listdir(shot_path):
                                    dept_path = os.path.join(shot_path, dept)
                                    if os.path.isdir(dept_path) and not dept.startswith('.'):
                                        shot_departments.add(dept)

        # Scan asset departments (V:\SWA\all\assets\Sets\interior\Kitchen\[department])
        asset_base_dirs = [
            os.path.join(self.project_root, "asset"),
            os.path.join(self.project_root, "assets"),
        ]

        for asset_base in asset_base_dirs:
            if os.path.exists(asset_base):
                for category_name in self._categories:
                    if category_name in self._subcategories:
                        for subcat_name in self._subcategories[category_name]:
                            if subcat_name in self._assets:
                                for asset_name in self._assets[subcat_name]:
                                    asset_path = os.path.join(asset_base, category_name, subcat_name, asset_name)
                                    if os.path.exists(asset_path):
                                        for dept in os.listdir(asset_path):
                                            dept_path = os.path.join(asset_path, dept)
                                            if os.path.isdir(dept_path) and not dept.startswith('.'):
                                                asset_departments.add(dept)

        # Store departments
        self._departments = {
            "shot": sorted(list(shot_departments)),
            "asset": sorted(list(asset_departments))
        }

        print(f"INFO: Found {len(shot_departments)} shot departments: {sorted(shot_departments)}")
        print(f"INFO: Found {len(asset_departments)} asset departments: {sorted(asset_departments)}")


    
    def get_project_info(self) -> ProjectInfo:
        """Get current project information."""
        return ProjectInfo(
            name="SWA Project",
            root_path=self.project_root,
            type=ProjectType.SHOT,  # Default
            created_date=datetime.now() - timedelta(days=30),
            last_modified=datetime.now(),
            description="Sample project for LRC Toolbox development",
            metadata={"version": "1.0", "pipeline": "Maya 2024"}
        )

    def refresh_project_structure(self) -> None:
        """Refresh project structure by rescanning directories."""
        logger.log_ui_operation("ProjectManager", "refresh_structure", self.project_root)

        # Clear existing data
        self._episodes.clear()
        self._sequences.clear()
        self._shots.clear()
        self._categories.clear()
        self._subcategories.clear()
        self._assets.clear()
        self._departments.clear()

        # Reinitialize with real data
        self._initialize_project_data()

    def set_project_root(self, new_root: str) -> None:
        """Set new project root and refresh structure."""
        if new_root != self.project_root:
            old_root = self.project_root
            self.project_root = new_root
            logger.log_project_root_change(old_root, new_root, "user")
            self.refresh_project_structure()

    def get_episodes(self) -> List[str]:
        """Get list of available episodes."""
        episodes = list(self._episodes.keys())
        logger.log_ui_operation("ProjectManager", "get_episodes", f"Returning episodes: {episodes}")
        return episodes
    
    def get_sequences_for_episode(self, episode: str) -> List[str]:
        """Get sequences for the specified episode."""
        return self._sequences.get(episode, [])
    
    def get_shots_for_sequence(self, sequence: str) -> List[str]:
        """Get shots for the specified sequence."""
        return self._shots.get(sequence, [])
    
    def get_categories(self) -> List[str]:
        """Get list of available asset categories."""
        categories = list(self._categories.keys())
        logger.log_ui_operation("ProjectManager", "get_categories", f"Returning categories: {categories}")
        return categories
    
    def get_subcategories_for_category(self, category: str) -> List[str]:
        """Get subcategories for the specified category."""
        return self._subcategories.get(category, [])
    
    def get_assets_for_subcategory(self, subcategory: str) -> List[str]:
        """Get assets for the specified subcategory."""
        return self._assets.get(subcategory, [])
    
    def get_departments_for_context(self, context_type: str) -> List[str]:
        """Get departments for the specified context type."""
        return self._departments.get(context_type, [])

    def get_departments_for_shot(self, episode: str, sequence: str, shot: str) -> List[str]:
        """Get actual departments that exist for a specific shot."""
        shot_path = os.path.join(self.project_root, "scene", episode, sequence, shot)
        if not os.path.exists(shot_path):
            return []

        departments = []
        try:
            for item in os.listdir(shot_path):
                item_path = os.path.join(shot_path, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    departments.append(item)
            return sorted(departments)
        except OSError:
            return []

    def get_departments_for_asset(self, category: str, subcategory: str, asset: str) -> List[str]:
        """Get actual departments that exist for a specific asset."""
        asset_base_dirs = [
            os.path.join(self.project_root, "asset"),
            os.path.join(self.project_root, "assets"),
        ]

        for asset_base in asset_base_dirs:
            asset_path = os.path.join(asset_base, category, subcategory, asset)
            if os.path.exists(asset_path):
                departments = []
                try:
                    for item in os.listdir(asset_path):
                        item_path = os.path.join(asset_path, item)
                        if os.path.isdir(item_path) and not item.startswith('.'):
                            # Exclude 'hero' directory as it's not a department
                            if item.lower() != 'hero':
                                departments.append(item)
                    return sorted(departments)
                except OSError:
                    break
        return []
    
    def get_context_path(self, context: NavigationContext) -> str:
        """Get the full file system path for the given context."""
        base_path = self.project_root
        
        if context.type == ProjectType.SHOT:
            if context.is_valid_shot_context:
                return os.path.join(
                    base_path, "scene", 
                    context.episode, context.sequence, context.shot, context.department
                )
        else:
            if context.is_valid_asset_context:
                return os.path.join(
                    base_path, "asset",
                    context.category, context.subcategory, context.asset, context.department
                )
        
        return "[Invalid Context]"
    
    def get_files_for_context(self, context: NavigationContext) -> List[FileInfo]:
        """Get files for the specified context with real file system scanning."""
        context_path = self.get_context_path(context)
        if context_path == "[Invalid Context]":
            logger.log_directory_access("Invalid Context", "file_scan", success=False,
                                       error="Invalid navigation context")
            return []

        # Check if directory exists
        if not os.path.exists(context_path):
            logger.log_directory_access(context_path, "file_scan", success=False,
                                       error="Directory does not exist")
            return []

        files = []
        start_time = time.time()

        try:
            # Scan directory for files
            items = os.listdir(context_path)
            logger.log_directory_access(context_path, "file_scan_start", success=True,
                                       item_count=len(items))

            for item in items:
                item_path = os.path.join(context_path, item)

                try:
                    stat = os.stat(item_path)
                    is_directory = os.path.isdir(item_path)

                    # Get file extension
                    file_type = ""
                    if not is_directory:
                        _, ext = os.path.splitext(item)
                        file_type = ext[1:] if ext else ""

                    # Create FileInfo object
                    file_info = FileInfo(
                        name=item,
                        path=item_path,
                        size=stat.st_size if not is_directory else 0,
                        modified_date=datetime.fromtimestamp(stat.st_mtime),
                        file_type=file_type,
                        is_directory=is_directory,
                        metadata=self._extract_file_metadata(item_path)
                    )

                    files.append(file_info)

                except (OSError, IOError) as e:
                    logger.log_error("ProjectManager", e, f"reading file stats for {item_path}")
                    continue

            # Sort files: directories first, then by name
            files.sort(key=lambda f: (not f.is_directory, f.name.lower()))

            # Log performance
            scan_duration = time.time() - start_time
            logger.log_network_performance(context_path, "file_scan", scan_duration)
            logger.log_directory_access(context_path, "file_scan_complete", success=True,
                                       item_count=len(files))
            return files

        except OSError as e:
            logger.log_error("ProjectManager", e, f"scanning directory {context_path}")
            return []

    def _extract_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract basic metadata from file."""
        metadata = {}

        try:
            stat = os.stat(file_path)

            # Basic file metadata
            metadata.update({
                "size_mb": round(stat.st_size / (1024 * 1024), 2) if stat.st_size > 1024*1024 else 0,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat()
            })

            # Try to detect file type specific metadata
            if file_path.endswith(('.ma', '.mb')):
                metadata["app"] = "Maya"
                metadata["type"] = "scene"
            elif file_path.endswith('.json'):
                metadata["type"] = "data"
            elif file_path.endswith(('.exr', '.jpg', '.png', '.tif')):
                metadata["type"] = "image"
            elif os.path.isdir(file_path):
                metadata["type"] = "directory"

        except (OSError, IOError):
            pass

        return metadata
    
    def validate_context(self, context: NavigationContext) -> bool:
        """Validate if the navigation context is valid."""
        if context.type == ProjectType.SHOT:
            return (context.episode in self._episodes and
                    context.sequence in self.get_sequences_for_episode(context.episode) and
                    context.shot in self.get_shots_for_sequence(context.sequence) and
                    context.department in self.get_departments_for_context("shot"))
        else:
            return (context.category in self._categories and
                    context.subcategory in self.get_subcategories_for_category(context.category) and
                    context.asset in self.get_assets_for_subcategory(context.subcategory) and
                    context.department in self.get_departments_for_context("asset"))
    
    def create_directory_structure(self, context: NavigationContext) -> bool:
        """Create directory structure for the given context with real file operations."""
        context_path = self.get_context_path(context)
        if context_path == "[Invalid Context]":
            logger.log_directory_access("Invalid Context", "create", success=False,
                                       error="Invalid navigation context")
            return False

        try:
            # Create directory structure
            os.makedirs(context_path, exist_ok=True)
            logger.log_directory_access(context_path, "create", success=True)

            # Verify creation
            if os.path.exists(context_path):
                logger.log_file_operation("create_directory", context_path, success=True)
                return True
            else:
                logger.log_file_operation("create_directory", context_path, success=False,
                                        error="Directory creation verification failed")
                return False

        except OSError as e:
            logger.log_error("ProjectManager", e, f"creating directory structure at {context_path}")
            return False
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """Get project statistics."""
        return {
            "total_episodes": len(self._episodes),
            "total_sequences": sum(len(seqs) for seqs in self._sequences.values()),
            "total_shots": sum(len(shots) for shots in self._shots.values()),
            "total_categories": len(self._categories),
            "total_assets": sum(len(assets) for assets in self._assets.values()),
            "last_updated": datetime.now().isoformat()
        }
