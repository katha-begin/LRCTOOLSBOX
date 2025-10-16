"""
Naming Conventions Utilities

This module provides naming convention validation and generation utilities
with mock implementations for render layer naming and light naming patterns.
"""

import re
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum

from ..core.models import (
    RenderLayerElement, RenderLayerVariance, NavigationContext, ProjectType
)


class NamingPattern(Enum):
    """Naming pattern types."""
    RENDER_LAYER = "render_layer"
    LIGHT_MASTER = "light_master"
    LIGHT_KEY = "light_key"
    LIGHT_CHILD = "light_child"
    TEMPLATE_PACKAGE = "template_package"
    FILE_VERSION = "file_version"


class NamingConventions:
    """
    Naming Conventions utility class for validation and generation.
    
    Provides mock naming convention validation including render layer naming
    ({context}_{element}_{variance}) and light naming patterns.
    """
    
    def __init__(self):
        """Initialize Naming Conventions."""
        self._patterns = {
            NamingPattern.RENDER_LAYER: {
                "with_variance": r"^[A-Z0-9]+_(?:BG|CHAR|FX)_[ABC]$",
                "without_variance": r"^[A-Z0-9]+_ATMOS$"
            },
            NamingPattern.LIGHT_MASTER: r"^MASTER_[A-Z]+_\d{3}$",
            NamingPattern.LIGHT_KEY: r"^[A-Z0-9]+_[A-Z]+_\d{3}$",
            NamingPattern.LIGHT_CHILD: r"^[A-Z0-9]+_[A-Z]+_[A-Z]+_\d{3}$",
            NamingPattern.TEMPLATE_PACKAGE: r"^[a-z0-9_]+_pkg$",
            NamingPattern.FILE_VERSION: r"^.+_v\d{3,4}\.[a-zA-Z0-9]+$"
        }
        
        self._valid_elements = [e.value for e in RenderLayerElement]
        self._valid_variances = [v.value for v in RenderLayerVariance]
        self._valid_light_types = ["KEY", "FILL", "RIM", "BOUNCE", "AMBIENT", "SPEC"]
    
    def validate_render_layer_name(self, layer_name: str) -> Tuple[bool, str, Dict[str, str]]:
        """
        Validate render layer name against naming convention.
        
        Args:
            layer_name: Layer name to validate
            
        Returns:
            Tuple of (is_valid, message, parsed_components)
        """
        print(f"Mock: Validating render layer name: {layer_name}")
        
        # Parse components
        parts = layer_name.split('_')
        
        if len(parts) < 2:
            return False, "Layer name must have at least PREFIX_ELEMENT", {}
        
        prefix = parts[0]
        element = parts[1]
        variance = parts[2] if len(parts) > 2 else None
        
        components = {
            "prefix": prefix,
            "element": element,
            "variance": variance
        }
        
        # Validate element
        if element not in self._valid_elements:
            return False, f"Invalid element '{element}'. Valid: {self._valid_elements}", components
        
        # Check variance rules
        if element == "ATMOS":
            if variance is not None:
                return False, "ATMOS element should not have variance", components
        else:
            if variance is None:
                return False, f"Element '{element}' requires variance (A, B, or C)", components
            if variance not in self._valid_variances:
                return False, f"Invalid variance '{variance}'. Valid: {self._valid_variances}", components
        
        return True, "Valid render layer naming convention", components
    
    def generate_render_layer_name(self, prefix: str, element: RenderLayerElement,
                                 variance: Optional[RenderLayerVariance] = None) -> str:
        """
        Generate render layer name following naming convention.
        
        Args:
            prefix: Context prefix (MASTER, SH0010, etc.)
            element: Render layer element
            variance: Render layer variance (omitted for ATMOS)
            
        Returns:
            Generated layer name
        """
        if element == RenderLayerElement.ATMOS:
            return f"{prefix}_{element.value}"
        else:
            variance_str = variance.value if variance else "A"
            return f"{prefix}_{element.value}_{variance_str}"
    
    def validate_light_name(self, light_name: str) -> Tuple[bool, str, Dict[str, str]]:
        """
        Validate light name against hierarchical naming convention.
        
        Args:
            light_name: Light name to validate
            
        Returns:
            Tuple of (is_valid, message, parsed_components)
        """
        print(f"Mock: Validating light name: {light_name}")
        
        parts = light_name.split('_')
        components = {}
        
        if len(parts) < 3:
            return False, "Light name must have at least PREFIX_TYPE_INDEX", {}
        
        # Check for Master pattern: MASTER_TYPE_INDEX
        if parts[0] == "MASTER" and len(parts) == 3:
            pattern = self._patterns[NamingPattern.LIGHT_MASTER]
            if re.match(pattern, light_name):
                components = {
                    "hierarchy": "Master",
                    "prefix": "MASTER",
                    "type": parts[1],
                    "index": parts[2]
                }
                return True, "Valid Master light naming", components
        
        # Check for Key pattern: PREFIX_TYPE_INDEX
        elif len(parts) == 3:
            pattern = self._patterns[NamingPattern.LIGHT_KEY]
            if re.match(pattern, light_name):
                components = {
                    "hierarchy": "Key",
                    "prefix": parts[0],
                    "type": parts[1],
                    "index": parts[2]
                }
                return True, "Valid Key light naming", components
        
        # Check for Child pattern: PREFIX_TYPE_SUBTYPE_INDEX
        elif len(parts) == 4:
            pattern = self._patterns[NamingPattern.LIGHT_CHILD]
            if re.match(pattern, light_name):
                components = {
                    "hierarchy": "Child",
                    "prefix": parts[0],
                    "type": parts[1],
                    "subtype": parts[2],
                    "index": parts[3]
                }
                return True, "Valid Child light naming", components
        
        return False, "Invalid light naming convention", components
    
    def generate_light_name(self, hierarchy: str, light_type: str, index: int,
                          context: Optional[NavigationContext] = None,
                          subtype: Optional[str] = None) -> str:
        """
        Generate light name following hierarchical naming convention.
        
        Args:
            hierarchy: Master, Key, or Child
            light_type: KEY, FILL, RIM, etc.
            index: Light index number
            context: Navigation context for prefix
            subtype: Sub-type for child lights
            
        Returns:
            Generated light name
        """
        index_str = f"{index:03d}"
        
        if hierarchy == "Master":
            return f"MASTER_{light_type}_{index_str}"
        
        elif hierarchy == "Key":
            prefix = self._get_context_prefix(context) if context else "SH0010"
            return f"{prefix}_{light_type}_{index_str}"
        
        else:  # Child
            prefix = self._get_context_prefix(context) if context else "SH0010"
            sub = subtype or self._get_default_subtype(light_type)
            return f"{prefix}_{light_type}_{sub}_{index_str}"
    
    def validate_template_package_name(self, package_name: str) -> Tuple[bool, str]:
        """
        Validate template package name.
        
        Args:
            package_name: Package name to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        print(f"Mock: Validating template package name: {package_name}")
        
        pattern = self._patterns[NamingPattern.TEMPLATE_PACKAGE]
        
        if re.match(pattern, package_name):
            return True, "Valid template package naming"
        else:
            return False, "Package name must be lowercase with underscores and end with '_pkg'"
    
    def validate_file_version_name(self, file_name: str) -> Tuple[bool, str, Dict[str, str]]:
        """
        Validate file version name.
        
        Args:
            file_name: File name to validate
            
        Returns:
            Tuple of (is_valid, message, parsed_components)
        """
        print(f"Mock: Validating file version name: {file_name}")
        
        pattern = self._patterns[NamingPattern.FILE_VERSION]
        
        if re.match(pattern, file_name):
            # Extract version number
            version_match = re.search(r'_v(\d{3,4})', file_name)
            base_name = re.sub(r'_v\d{3,4}', '', file_name)
            
            components = {
                "base_name": base_name,
                "version": version_match.group(1) if version_match else "000",
                "extension": file_name.split('.')[-1] if '.' in file_name else ""
            }
            
            return True, "Valid file version naming", components
        else:
            return False, "File name must include version pattern '_vXXX'", {}
    
    def suggest_names(self, pattern_type: NamingPattern, 
                     context: Optional[NavigationContext] = None,
                     **kwargs) -> List[str]:
        """
        Suggest names based on pattern type and context.
        
        Args:
            pattern_type: Type of naming pattern
            context: Navigation context
            **kwargs: Additional parameters for name generation
            
        Returns:
            List of suggested names
        """
        suggestions = []
        
        if pattern_type == NamingPattern.RENDER_LAYER:
            prefix = self._get_context_prefix(context) if context else "MASTER"
            for element in RenderLayerElement:
                if element == RenderLayerElement.ATMOS:
                    suggestions.append(f"{prefix}_{element.value}")
                else:
                    for variance in RenderLayerVariance:
                        suggestions.append(f"{prefix}_{element.value}_{variance.value}")
        
        elif pattern_type == NamingPattern.LIGHT_MASTER:
            for light_type in self._valid_light_types:
                suggestions.append(f"MASTER_{light_type}_001")
        
        elif pattern_type == NamingPattern.LIGHT_KEY:
            prefix = self._get_context_prefix(context) if context else "SH0010"
            for light_type in self._valid_light_types:
                suggestions.append(f"{prefix}_{light_type}_001")
        
        elif pattern_type == NamingPattern.TEMPLATE_PACKAGE:
            if context:
                if context.type == ProjectType.SHOT:
                    suggestions.extend([
                        f"{context.sequence}_{context.shot}_master_pkg",
                        f"{context.sequence}_{context.shot}_key_pkg",
                        f"{context.sequence}_{context.shot}_micro_pkg"
                    ])
                else:
                    asset_name = context.asset.lower()
                    suggestions.extend([
                        f"{asset_name}_master_pkg",
                        f"{asset_name}_day_pkg",
                        f"{asset_name}_night_pkg"
                    ])
        
        return suggestions[:10]  # Limit to 10 suggestions
    
    def get_naming_rules(self, pattern_type: NamingPattern) -> Dict[str, Any]:
        """
        Get naming rules for a specific pattern type.
        
        Args:
            pattern_type: Type of naming pattern
            
        Returns:
            Dictionary with naming rules and examples
        """
        rules = {
            NamingPattern.RENDER_LAYER: {
                "pattern": "{context}_{element}_{variance}",
                "rules": [
                    "Context: MASTER, SH0010, KITCHEN, etc.",
                    "Element: BG, CHAR, ATMOS, FX",
                    "Variance: A, B, C (omitted for ATMOS)",
                    "Example: MASTER_BG_A, SH0010_CHAR_B, MASTER_ATMOS"
                ]
            },
            NamingPattern.LIGHT_MASTER: {
                "pattern": "MASTER_{type}_{index}",
                "rules": [
                    "Always starts with MASTER",
                    "Type: KEY, FILL, RIM, BOUNCE, AMBIENT, SPEC",
                    "Index: 3-digit zero-padded number",
                    "Example: MASTER_KEY_001, MASTER_FILL_002"
                ]
            },
            NamingPattern.LIGHT_KEY: {
                "pattern": "{prefix}_{type}_{index}",
                "rules": [
                    "Prefix: Context-based (SH0010, KITCHEN, etc.)",
                    "Type: KEY, FILL, RIM, BOUNCE, AMBIENT, SPEC",
                    "Index: 3-digit zero-padded number",
                    "Example: SH0010_KEY_001, KITCHEN_FILL_002"
                ]
            },
            NamingPattern.LIGHT_CHILD: {
                "pattern": "{prefix}_{type}_{subtype}_{index}",
                "rules": [
                    "Prefix: Context-based (SH0010, KITCHEN, etc.)",
                    "Type: KEY, FILL, RIM, BOUNCE, AMBIENT, SPEC",
                    "Subtype: RIM, BOUNCE, EDGE, SOFT, etc.",
                    "Index: 3-digit zero-padded number",
                    "Example: SH0010_KEY_RIM_001, KITCHEN_FILL_BOUNCE_002"
                ]
            }
        }
        
        return rules.get(pattern_type, {"pattern": "Unknown", "rules": []})
    
    def _get_context_prefix(self, context: NavigationContext) -> str:
        """Get prefix from navigation context."""
        if context.type == ProjectType.SHOT:
            return context.shot
        else:
            return context.asset.upper()
    
    def _get_default_subtype(self, light_type: str) -> str:
        """Get default subtype for child lights."""
        subtypes = {
            "KEY": "RIM",
            "FILL": "BOUNCE",
            "RIM": "EDGE",
            "BOUNCE": "SOFT",
            "AMBIENT": "ENV",
            "SPEC": "HIGHLIGHT"
        }
        return subtypes.get(light_type, "SUB")


# Convenience functions
def validate_render_layer(layer_name: str) -> Tuple[bool, str]:
    """Convenience function for validating render layer names."""
    naming = NamingConventions()
    is_valid, message, _ = naming.validate_render_layer_name(layer_name)
    return is_valid, message


def validate_light_name(light_name: str) -> Tuple[bool, str]:
    """Convenience function for validating light names."""
    naming = NamingConventions()
    is_valid, message, _ = naming.validate_light_name(light_name)
    return is_valid, message


def generate_layer_name(prefix: str, element: str, variance: Optional[str] = None) -> str:
    """Convenience function for generating render layer names."""
    naming = NamingConventions()
    element_enum = RenderLayerElement(element)
    variance_enum = RenderLayerVariance(variance) if variance else None
    return naming.generate_render_layer_name(prefix, element_enum, variance_enum)
