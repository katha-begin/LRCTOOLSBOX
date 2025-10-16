"""
Regex Tools Utilities

This module provides regex conversion and pattern matching utilities
with mock implementations for DAG path to regex conversion.
"""

import re
from typing import List, Dict, Optional, Any, Tuple, Pattern
import random


class RegexTools:
    """
    Regex Tools utility class for pattern conversion and matching.
    
    Provides mock regex conversion functionality and pattern matching
    utilities for DAG paths and naming patterns.
    """
    
    def __init__(self):
        """Initialize Regex Tools."""
        self._conversion_history = []
        self._common_patterns = {
            "dag_path": r"\|[^|]+",
            "light_name": r"[A-Z0-9]+_[A-Z]+_\d{3}",
            "version_number": r"_v\d{3,4}",
            "file_extension": r"\.[a-zA-Z0-9]+$",
            "maya_node": r"[a-zA-Z_][a-zA-Z0-9_]*",
            "frame_number": r"\d{4,6}",
            "sequence_pattern": r"[a-z]{2}\d{4}",
            "shot_pattern": r"SH\d{4}"
        }
    
    def dag_path_to_regex(self, dag_path: str, 
                         wildcards: bool = True,
                         escape_special: bool = True) -> str:
        """
        Convert Maya DAG path to regex pattern.
        
        Args:
            dag_path: Maya DAG path (e.g., |group1|light1)
            wildcards: Whether to include wildcard patterns
            escape_special: Whether to escape special regex characters
            
        Returns:
            Regex pattern string
        """
        print(f"Mock: Converting DAG path to regex: {dag_path}")
        
        # Mock conversion logic
        if escape_special:
            # Escape special regex characters
            escaped_path = re.escape(dag_path)
        else:
            escaped_path = dag_path
        
        if wildcards:
            # Replace parts with wildcard patterns
            pattern = escaped_path.replace(r"\|", r"\|[^|]*")
            pattern = pattern.replace("Shape", r"Shape\d*")
            pattern = pattern.replace("light", r"light\d*")
        else:
            pattern = escaped_path
        
        # Log conversion
        self._conversion_history.append({
            "input": dag_path,
            "output": pattern,
            "wildcards": wildcards,
            "escaped": escape_special,
            "timestamp": "mock_timestamp"
        })
        
        print(f"  Result: {pattern}")
        return pattern
    
    def regex_to_dag_paths(self, regex_pattern: str, 
                          search_scope: List[str]) -> List[str]:
        """
        Find DAG paths matching regex pattern.
        
        Args:
            regex_pattern: Regex pattern to match
            search_scope: List of DAG paths to search in
            
        Returns:
            List of matching DAG paths
        """
        print(f"Mock: Finding DAG paths matching: {regex_pattern}")
        print(f"  Search scope: {len(search_scope)} paths")
        
        # Mock matching logic
        try:
            compiled_pattern = re.compile(regex_pattern)
            matches = []
            
            for dag_path in search_scope:
                if compiled_pattern.search(dag_path):
                    matches.append(dag_path)
            
            # Add some mock matches if none found
            if not matches and search_scope:
                mock_matches = random.sample(search_scope, min(3, len(search_scope)))
                matches.extend(mock_matches)
                print(f"  Mock: Added {len(mock_matches)} sample matches")
            
            print(f"  Found {len(matches)} matches")
            return matches
            
        except re.error as e:
            print(f"  Regex error: {e}")
            return []
    
    def validate_regex_pattern(self, pattern: str) -> Tuple[bool, str]:
        """
        Validate regex pattern syntax.
        
        Args:
            pattern: Regex pattern to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        print(f"Mock: Validating regex pattern: {pattern}")
        
        try:
            re.compile(pattern)
            return True, "Valid regex pattern"
        except re.error as e:
            return False, f"Invalid regex pattern: {str(e)}"
    
    def generate_pattern_from_examples(self, examples: List[str],
                                     generalize: bool = True) -> str:
        """
        Generate regex pattern from example strings.
        
        Args:
            examples: List of example strings
            generalize: Whether to generalize the pattern
            
        Returns:
            Generated regex pattern
        """
        print(f"Mock: Generating pattern from {len(examples)} examples")
        
        if not examples:
            return ""
        
        # Mock pattern generation logic
        if len(examples) == 1:
            # Single example - escape and return
            pattern = re.escape(examples[0])
        else:
            # Multiple examples - find common patterns
            first_example = examples[0]
            
            if generalize:
                # Replace numbers with \d+ pattern
                pattern = re.sub(r'\d+', r'\\d+', re.escape(first_example))
                # Replace common variations
                pattern = pattern.replace(r'\_001', r'\_\\d{3}')
                pattern = pattern.replace(r'\_v001', r'\_v\\d{3}')
            else:
                pattern = re.escape(first_example)
        
        print(f"  Generated pattern: {pattern}")
        return pattern
    
    def test_pattern_against_strings(self, pattern: str, 
                                   test_strings: List[str]) -> Dict[str, List[str]]:
        """
        Test regex pattern against list of strings.
        
        Args:
            pattern: Regex pattern to test
            test_strings: List of strings to test against
            
        Returns:
            Dictionary with 'matches' and 'non_matches' lists
        """
        print(f"Mock: Testing pattern against {len(test_strings)} strings")
        
        try:
            compiled_pattern = re.compile(pattern)
            matches = []
            non_matches = []
            
            for test_string in test_strings:
                if compiled_pattern.search(test_string):
                    matches.append(test_string)
                else:
                    non_matches.append(test_string)
            
            print(f"  Matches: {len(matches)}")
            print(f"  Non-matches: {len(non_matches)}")
            
            return {
                "matches": matches,
                "non_matches": non_matches,
                "pattern": pattern,
                "total_tested": len(test_strings)
            }
            
        except re.error as e:
            print(f"  Pattern error: {e}")
            return {
                "matches": [],
                "non_matches": test_strings,
                "pattern": pattern,
                "error": str(e)
            }
    
    def get_common_patterns(self) -> Dict[str, str]:
        """Get dictionary of common regex patterns."""
        return self._common_patterns.copy()
    
    def extract_pattern_groups(self, pattern: str, text: str) -> List[Dict[str, Any]]:
        """
        Extract groups from regex pattern matches.
        
        Args:
            pattern: Regex pattern with groups
            text: Text to search in
            
        Returns:
            List of match dictionaries with group information
        """
        print(f"Mock: Extracting groups from pattern: {pattern}")
        
        try:
            compiled_pattern = re.compile(pattern)
            matches = []
            
            for match in compiled_pattern.finditer(text):
                match_info = {
                    "full_match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "groups": match.groups(),
                    "groupdict": match.groupdict()
                }
                matches.append(match_info)
            
            print(f"  Found {len(matches)} matches with groups")
            return matches
            
        except re.error as e:
            print(f"  Pattern error: {e}")
            return []
    
    def replace_with_pattern(self, text: str, pattern: str, 
                           replacement: str, count: int = 0) -> Tuple[str, int]:
        """
        Replace text using regex pattern.
        
        Args:
            text: Text to perform replacement on
            pattern: Regex pattern to match
            replacement: Replacement string
            count: Maximum number of replacements (0 = all)
            
        Returns:
            Tuple of (modified_text, replacement_count)
        """
        print(f"Mock: Replacing pattern in text")
        print(f"  Pattern: {pattern}")
        print(f"  Replacement: {replacement}")
        
        try:
            if count == 0:
                modified_text, replacement_count = re.subn(pattern, replacement, text)
            else:
                modified_text, replacement_count = re.subn(pattern, replacement, text, count=count)
            
            print(f"  Made {replacement_count} replacements")
            return modified_text, replacement_count
            
        except re.error as e:
            print(f"  Pattern error: {e}")
            return text, 0
    
    def split_with_pattern(self, text: str, pattern: str, 
                          maxsplit: int = 0) -> List[str]:
        """
        Split text using regex pattern.
        
        Args:
            text: Text to split
            pattern: Regex pattern to split on
            maxsplit: Maximum number of splits (0 = no limit)
            
        Returns:
            List of split strings
        """
        print(f"Mock: Splitting text with pattern: {pattern}")
        
        try:
            if maxsplit == 0:
                result = re.split(pattern, text)
            else:
                result = re.split(pattern, text, maxsplit=maxsplit)
            
            print(f"  Split into {len(result)} parts")
            return result
            
        except re.error as e:
            print(f"  Pattern error: {e}")
            return [text]
    
    def get_conversion_history(self) -> List[Dict[str, Any]]:
        """Get history of DAG path conversions."""
        return self._conversion_history.copy()
    
    def clear_conversion_history(self) -> None:
        """Clear conversion history."""
        self._conversion_history.clear()
        print("Mock: Conversion history cleared")
    
    def generate_maya_selection_pattern(self, node_types: List[str],
                                      name_patterns: List[str]) -> str:
        """
        Generate regex pattern for Maya node selection.
        
        Args:
            node_types: List of Maya node types to match
            name_patterns: List of name patterns to match
            
        Returns:
            Combined regex pattern
        """
        print(f"Mock: Generating Maya selection pattern")
        print(f"  Node types: {node_types}")
        print(f"  Name patterns: {name_patterns}")
        
        # Mock pattern generation
        type_pattern = "|".join(node_types) if node_types else ".*"
        name_pattern = "|".join(name_patterns) if name_patterns else ".*"
        
        combined_pattern = f"({type_pattern}).*({name_pattern})"
        
        print(f"  Generated pattern: {combined_pattern}")
        return combined_pattern


# Convenience functions
def dag_to_regex(dag_path: str, wildcards: bool = True) -> str:
    """Convenience function for DAG path to regex conversion."""
    regex_tools = RegexTools()
    return regex_tools.dag_path_to_regex(dag_path, wildcards)


def validate_regex(pattern: str) -> Tuple[bool, str]:
    """Convenience function for regex validation."""
    regex_tools = RegexTools()
    return regex_tools.validate_regex_pattern(pattern)


def test_regex(pattern: str, test_strings: List[str]) -> Dict[str, List[str]]:
    """Convenience function for regex testing."""
    regex_tools = RegexTools()
    return regex_tools.test_pattern_against_strings(pattern, test_strings)


def get_common_patterns() -> Dict[str, str]:
    """Convenience function to get common regex patterns."""
    regex_tools = RegexTools()
    return regex_tools.get_common_patterns()
