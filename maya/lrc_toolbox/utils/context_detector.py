"""
Context Detector

This module provides context detection functionality from Maya scene file paths
and current session information to automatically determine shot/asset context.
"""

import os
import re
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from ..core.models import NavigationContext, ProjectType
from ..config.settings import settings


class ContextDetector:
    """
    Context detector for automatically determining shot/asset context from Maya scene paths.
    
    Provides intelligent context detection from current Maya scene file paths,
    following standard project structure conventions.
    """

    def __init__(self):
        """Initialize context detector."""
        self._maya_available = self._check_maya_availability()
        self._project_root = settings.get_project_root()
        
        # Path patterns for context detection
        self._shot_patterns = [
            # V:/SWA/all/scene/Ep01/sq0010/SH0010/lighting/version/filename.ma
            r'scene[/\\](?P<episode>Ep\d+)[/\\](?P<sequence>sq\d+)[/\\](?P<shot>SH\d+)[/\\](?P<department>\w+)',
            # Alternative patterns
            r'scene[/\\](?P<episode>[^/\\]+)[/\\](?P<sequence>[^/\\]+)[/\\](?P<shot>[^/\\]+)[/\\](?P<department>\w+)',
        ]
        
        self._asset_patterns = [
            # V:/SWA/all/asset/characters/main/hero_char/lighting/version/filename.ma
            r'asset[/\\](?P<category>\w+)[/\\](?P<subcategory>\w+)[/\\](?P<asset>[^/\\]+)[/\\](?P<department>\w+)',
            # Alternative patterns
            r'assets[/\\](?P<category>\w+)[/\\](?P<subcategory>\w+)[/\\](?P<asset>[^/\\]+)[/\\](?P<department>\w+)',
        ]

    def _check_maya_availability(self) -> bool:
        """Check if Maya is available."""
        try:
            import maya.cmds as cmds
            return True
        except ImportError:
            return False

    def get_current_scene_context(self) -> Optional[NavigationContext]:
        """
        Get navigation context from current Maya scene file path.
        
        Returns:
            NavigationContext if detected, None otherwise
        """
        scene_path = self.get_current_scene_path()
        if not scene_path:
            return None
            
        return self.detect_context_from_path(scene_path)

    def get_current_scene_path(self) -> Optional[str]:
        """
        Get current Maya scene file path.
        
        Returns:
            Current scene path or None if not available
        """
        if not self._maya_available:
            print("Maya not available - cannot get scene path")
            return None
            
        try:
            import maya.cmds as cmds
            scene_path = cmds.file(query=True, sceneName=True)
            
            if scene_path:
                print(f"Current scene path: {scene_path}")
                return scene_path
            else:
                print("No scene file currently open")
                return None
                
        except Exception as e:
            print(f"Error getting scene path: {e}")
            return None

    def detect_context_from_path(self, file_path: str) -> Optional[NavigationContext]:
        """
        Detect navigation context from file path.
        
        Args:
            file_path: File path to analyze
            
        Returns:
            NavigationContext if detected, None otherwise
        """
        if not file_path:
            return None
            
        # Normalize path separators
        normalized_path = file_path.replace('\\', '/')
        print(f"Analyzing path: {normalized_path}")
        
        # Try shot patterns first
        shot_context = self._detect_shot_context(normalized_path)
        if shot_context:
            return shot_context
            
        # Try asset patterns
        asset_context = self._detect_asset_context(normalized_path)
        if asset_context:
            return asset_context
            
        print("No context pattern matched")
        return None

    def _detect_shot_context(self, file_path: str) -> Optional[NavigationContext]:
        """Detect shot context from file path."""
        for pattern in self._shot_patterns:
            match = re.search(pattern, file_path, re.IGNORECASE)
            if match:
                groups = match.groupdict()
                print(f"Shot context detected: {groups}")
                
                return NavigationContext(
                    type=ProjectType.SHOT,
                    episode=groups.get('episode', ''),
                    sequence=groups.get('sequence', ''),
                    shot=groups.get('shot', ''),
                    department=groups.get('department', 'lighting')
                )
        return None

    def _detect_asset_context(self, file_path: str) -> Optional[NavigationContext]:
        """Detect asset context from file path."""
        for pattern in self._asset_patterns:
            match = re.search(pattern, file_path, re.IGNORECASE)
            if match:
                groups = match.groupdict()
                print(f"Asset context detected: {groups}")
                
                return NavigationContext(
                    type=ProjectType.ASSET,
                    category=groups.get('category', ''),
                    subcategory=groups.get('subcategory', ''),
                    asset=groups.get('asset', ''),
                    department=groups.get('department', 'lighting')
                )
        return None

    def get_template_export_path(self, context: NavigationContext, template_name: str) -> str:
        """
        Get template export path based on context.
        
        Args:
            context: Navigation context
            template_name: Template name
            
        Returns:
            Template export path
        """
        if context.type == ProjectType.SHOT:
            return os.path.join(
                self._project_root, "scene",
                context.episode, context.sequence, context.shot,
                context.department, "templates", template_name
            )
        else:
            return os.path.join(
                self._project_root, "asset",
                context.category, context.subcategory, context.asset,
                context.department, "templates", template_name
            )

    def get_context_prefix(self, context: NavigationContext) -> str:
        """
        Get context prefix for template naming.
        
        Args:
            context: Navigation context
            
        Returns:
            Context prefix string
        """
        if context.type == ProjectType.SHOT:
            return context.shot
        else:
            return context.asset

    def validate_context(self, context: NavigationContext) -> Tuple[bool, str]:
        """
        Validate navigation context.
        
        Args:
            context: Navigation context to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not context:
            return False, "No context provided"
            
        if context.type == ProjectType.SHOT:
            if not all([context.episode, context.sequence, context.shot]):
                return False, "Shot context missing required fields (episode, sequence, shot)"
        else:
            if not all([context.category, context.subcategory, context.asset]):
                return False, "Asset context missing required fields (category, subcategory, asset)"
                
        return True, "Context is valid"

    def get_context_summary(self, context: NavigationContext) -> str:
        """
        Get human-readable context summary.
        
        Args:
            context: Navigation context
            
        Returns:
            Context summary string
        """
        if not context:
            return "No context"
            
        if context.type == ProjectType.SHOT:
            return f"Shot: {context.episode}/{context.sequence}/{context.shot}/{context.department}"
        else:
            return f"Asset: {context.category}/{context.subcategory}/{context.asset}/{context.department}"


# Global instance
context_detector = ContextDetector()
