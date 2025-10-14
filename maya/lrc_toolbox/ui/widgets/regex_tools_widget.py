"""
Regex Tools Widget

This module provides the Regex Tools widget for DAG path to regex conversion
according to UI design specifications.
"""

import re
from typing import Optional, List, Dict, Any

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtWidgets import *
    from PySide2.QtCore import *
    from PySide2.QtGui import *
except ImportError:
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        from PySide6.QtWidgets import *
        from PySide6.QtCore import *
        from PySide6.QtGui import *
    except ImportError:
        print("Warning: Neither PySide2 nor PySide6 available")
        QtWidgets = None


class RegexToolsWidget(QtWidgets.QWidget):
    """
    Regex Tools widget for DAG path to regex conversion.
    
    Provides DAG path conversion tools and quick utilities
    according to the UI design specifications.
    """
    
    # Signals for communication with main window
    regex_generated = QtCore.Signal(str)  # Emitted when regex is generated
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the Regex Tools widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._setup_ui()
        self._connect_signals()
        self._populate_example_data()
        
        print("Regex Tools Widget initialized")
    
    def _setup_ui(self) -> None:
        """Set up the user interface according to UI design specifications."""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create UI sections
        self._create_dag_converter()
        self._create_quick_tools()
        
        # Add sections to main layout
        main_layout.addWidget(self.dag_converter_group)
        main_layout.addWidget(self.quick_tools_group)
        main_layout.addStretch()
    
    def _create_dag_converter(self) -> None:
        """Create DAG path converter section."""
        self.dag_converter_group = QtWidgets.QGroupBox("🔧 DAG Path to Regex Converter")
        layout = QtWidgets.QVBoxLayout(self.dag_converter_group)
        
        # Input section
        layout.addWidget(QtWidgets.QLabel("DAG Paths (one per line):"))
        self.dag_input_text = QtWidgets.QTextEdit()
        self.dag_input_text.setMaximumHeight(100)
        self.dag_input_text.setPlaceholderText(
            "|forest_environment_trees_*\n"
            "|character_*\n"
            "|props_hero_*"
        )
        layout.addWidget(self.dag_input_text)
        
        # Options
        options_layout = QtWidgets.QHBoxLayout()
        self.escape_special_check = QtWidgets.QCheckBox("☑ Escape Special Characters")
        self.escape_special_check.setChecked(True)
        self.convert_wildcards_check = QtWidgets.QCheckBox("☑ Convert Wildcards")
        self.convert_wildcards_check.setChecked(True)
        
        options_layout.addWidget(self.escape_special_check)
        options_layout.addWidget(self.convert_wildcards_check)
        options_layout.addStretch()
        
        layout.addLayout(options_layout)
        
        # Convert button
        convert_layout = QtWidgets.QHBoxLayout()
        self.convert_btn = QtWidgets.QPushButton("Convert to Regex")
        convert_layout.addWidget(self.convert_btn)
        convert_layout.addStretch()
        
        layout.addLayout(convert_layout)
        
        # Output section
        layout.addWidget(QtWidgets.QLabel("Generated Regex:"))
        self.regex_output_text = QtWidgets.QTextEdit()
        self.regex_output_text.setMaximumHeight(80)
        self.regex_output_text.setReadOnly(True)
        self.regex_output_text.setStyleSheet(
            "font-family: monospace; background-color: #f8f8f8;"
        )
        layout.addWidget(self.regex_output_text)
        
        # Copy button
        copy_layout = QtWidgets.QHBoxLayout()
        self.copy_regex_btn = QtWidgets.QPushButton("📋 Copy Regex")
        copy_layout.addWidget(self.copy_regex_btn)
        copy_layout.addStretch()
        
        layout.addLayout(copy_layout)
    
    def _create_quick_tools(self) -> None:
        """Create quick tools section."""
        self.quick_tools_group = QtWidgets.QGroupBox("⚡ Quick Tools")
        layout = QtWidgets.QHBoxLayout(self.quick_tools_group)
        
        self.selected_to_regex_btn = QtWidgets.QPushButton("Selected Objects to Regex")
        layout.addWidget(self.selected_to_regex_btn)
        layout.addStretch()
    
    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        # DAG converter
        self.convert_btn.clicked.connect(self._on_convert_to_regex)
        self.copy_regex_btn.clicked.connect(self._on_copy_regex)
        
        # Quick tools
        self.selected_to_regex_btn.clicked.connect(self._on_selected_to_regex)
    
    def _populate_example_data(self) -> None:
        """Populate example data in the input field."""
        example_paths = [
            "|forest_environment_trees_*",
            "|character_*", 
            "|props_hero_*"
        ]
        self.dag_input_text.setPlainText("\n".join(example_paths))
    
    def _convert_dag_paths_to_regex(self, dag_paths: List[str]) -> str:
        """
        Convert DAG paths to regex pattern.
        
        Args:
            dag_paths: List of DAG paths to convert
            
        Returns:
            Generated regex pattern
        """
        if not dag_paths:
            return ""
        
        patterns = []
        
        for path in dag_paths:
            path = path.strip()
            if not path:
                continue
            
            # Remove leading pipe if present
            if path.startswith('|'):
                path = path[1:]
            
            # Escape special regex characters if option is enabled
            if self.escape_special_check.isChecked():
                # Escape special characters except * and ?
                path = re.escape(path)
                # Unescape * and ? for wildcard conversion
                path = path.replace(r'\*', '*').replace(r'\?', '?')
            
            # Convert wildcards if option is enabled
            if self.convert_wildcards_check.isChecked():
                # Convert * to .* and ? to .
                path = path.replace('*', '.*').replace('?', '.')
            
            # Add pipe prefix back
            path = '|' + path
            patterns.append(path)
        
        # Combine patterns with alternation
        if len(patterns) == 1:
            return f"({patterns[0]})"
        else:
            combined = "|".join(patterns)
            return f"({combined})"
    
    # Event handlers
    def _on_convert_to_regex(self) -> None:
        """Handle convert to regex button click."""
        input_text = self.dag_input_text.toPlainText().strip()
        
        if not input_text:
            QtWidgets.QMessageBox.warning(
                self, "No Input",
                "Please enter DAG paths to convert."
            )
            return
        
        # Split input into lines
        dag_paths = [line.strip() for line in input_text.split('\n') if line.strip()]
        
        if not dag_paths:
            QtWidgets.QMessageBox.warning(
                self, "No Valid Paths",
                "Please enter valid DAG paths."
            )
            return
        
        # Convert to regex
        regex_pattern = self._convert_dag_paths_to_regex(dag_paths)
        
        # Display result
        self.regex_output_text.setPlainText(regex_pattern)
        
        # Show success message
        QtWidgets.QMessageBox.information(
            self, "Conversion Complete",
            f"Successfully converted {len(dag_paths)} DAG paths to regex!\n\n"
            f"Generated pattern:\n{regex_pattern}"
        )
        
        # Emit signal
        self.regex_generated.emit(regex_pattern)
    
    def _on_copy_regex(self) -> None:
        """Handle copy regex button click."""
        regex_text = self.regex_output_text.toPlainText().strip()
        
        if not regex_text:
            QtWidgets.QMessageBox.warning(
                self, "No Regex",
                "Please generate a regex pattern first."
            )
            return
        
        # Copy to clipboard
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(regex_text)
        
        QtWidgets.QMessageBox.information(
            self, "Copied",
            f"Regex pattern copied to clipboard!\n\n{regex_text}"
        )
    
    def _on_selected_to_regex(self) -> None:
        """Handle selected objects to regex button click."""
        # Mock selected objects - in real implementation, get from Maya selection
        mock_selected = [
            "|forest_environment_trees_oak_01",
            "|forest_environment_trees_pine_02", 
            "|character_hero_main",
            "|character_sidekick_01",
            "|props_hero_sword",
            "|props_hero_shield"
        ]
        
        if not mock_selected:
            QtWidgets.QMessageBox.warning(
                self, "No Selection",
                "Please select objects in the Maya scene."
            )
            return
        
        # Show selection info
        selection_text = "\n".join(mock_selected)
        reply = QtWidgets.QMessageBox.question(
            self, "Convert Selection",
            f"Convert {len(mock_selected)} selected objects to regex?\n\n"
            f"Selected objects:\n{selection_text}",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            # Set input text
            self.dag_input_text.setPlainText("\n".join(mock_selected))
            
            # Auto-convert
            self._on_convert_to_regex()
    
    # Public methods
    def set_dag_paths(self, paths: List[str]) -> None:
        """Set DAG paths in the input field."""
        self.dag_input_text.setPlainText("\n".join(paths))
    
    def get_generated_regex(self) -> str:
        """Get the generated regex pattern."""
        return self.regex_output_text.toPlainText().strip()
    
    def clear_input(self) -> None:
        """Clear the input field."""
        self.dag_input_text.clear()
    
    def clear_output(self) -> None:
        """Clear the output field."""
        self.regex_output_text.clear()
    
    def set_conversion_options(self, escape_special: bool, convert_wildcards: bool) -> None:
        """Set conversion options."""
        self.escape_special_check.setChecked(escape_special)
        self.convert_wildcards_check.setChecked(convert_wildcards)
