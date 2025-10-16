"""
Template Integration Demo

This script demonstrates the integrated template system with:
1. Quick template creation in Template Tools widget
2. Template package export/import in Render Setup widget
3. Project structure alignment with hierarchical navigation

Run this in Maya to test the complete template workflow.
"""

import os
import sys
from typing import Dict, Any

# Add the LRC Toolbox to Python path if needed
lrc_toolbox_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if lrc_toolbox_path not in sys.path:
    sys.path.insert(0, lrc_toolbox_path)

try:
    from PySide2 import QtWidgets, QtCore
except ImportError:
    try:
        from PySide6 import QtWidgets, QtCore
    except ImportError:
        print("Error: Neither PySide2 nor PySide6 available")
        sys.exit(1)

from maya.lrc_toolbox.ui.widgets.template_tools_widget import TemplateToolsWidget
from maya.lrc_toolbox.ui.widgets.render_setup_widget import RenderSetupWidget
from maya.lrc_toolbox.core.render_setup_api import RenderSetupAPI


class TemplateIntegrationDemo(QtWidgets.QMainWindow):
    """Demo application showing template integration."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LRC Toolbox - Template Integration Demo")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget with tabs
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Initialize widgets
        self.template_tools = TemplateToolsWidget()
        self.render_setup = RenderSetupWidget()
        
        # Add tabs
        self.tab_widget.addTab(self.template_tools, "🔧 Template Tools")
        self.tab_widget.addTab(self.render_setup, "📦 Render Setup")
        
        # Connect signals
        self._connect_signals()
        
        # Add demo controls
        self._create_demo_controls(layout)
        
        print("Template Integration Demo initialized")
    
    def _connect_signals(self):
        """Connect signals between widgets."""
        # Connect template creation signals
        self.template_tools.layer_created.connect(self._on_layer_created)
        
        # Connect package signals
        self.render_setup.package_exported.connect(self._on_package_exported)
        self.render_setup.package_imported.connect(self._on_package_imported)
    
    def _create_demo_controls(self, layout):
        """Create demo control buttons."""
        demo_group = QtWidgets.QGroupBox("🚀 Demo Controls")
        demo_layout = QtWidgets.QHBoxLayout(demo_group)
        
        # Demo scenario buttons
        self.demo_shot_btn = QtWidgets.QPushButton("Demo Shot Workflow")
        self.demo_shot_btn.setToolTip("Demonstrate shot-based template workflow")
        self.demo_shot_btn.clicked.connect(self._demo_shot_workflow)
        
        self.demo_asset_btn = QtWidgets.QPushButton("Demo Asset Workflow")
        self.demo_asset_btn.setToolTip("Demonstrate asset-based template workflow")
        self.demo_asset_btn.clicked.connect(self._demo_asset_workflow)
        
        self.demo_export_btn = QtWidgets.QPushButton("Demo Export/Import")
        self.demo_export_btn.setToolTip("Demonstrate template package export/import")
        self.demo_export_btn.clicked.connect(self._demo_export_import)
        
        demo_layout.addWidget(self.demo_shot_btn)
        demo_layout.addWidget(self.demo_asset_btn)
        demo_layout.addWidget(self.demo_export_btn)
        demo_layout.addStretch()
        
        layout.addWidget(demo_group)
    
    def _demo_shot_workflow(self):
        """Demonstrate shot-based template workflow."""
        print("\n" + "="*60)
        print("SHOT WORKFLOW DEMO")
        print("="*60)
        
        # Set shot context
        shot_context = {
            "type": "shot",
            "episode": "Ep01",
            "sequence": "sq0010",
            "shot": "SH0010"
        }
        
        # Update both widgets with context
        self.template_tools.set_context(shot_context)
        self.render_setup.set_context(shot_context)
        
        # Switch to Template Tools tab
        self.tab_widget.setCurrentIndex(0)
        
        # Show info message
        QtWidgets.QMessageBox.information(
            self, "Shot Workflow Demo",
            "🎬 Shot Workflow Demo Started!\n\n"
            "Context set to: Ep01/sq0010/SH0010\n\n"
            "Try the following:\n"
            "1. Create quick templates using the colored buttons\n"
            "2. Switch to Render Setup tab to export packages\n"
            "3. Templates will be created with SH0010 prefix\n\n"
            "Template structure follows:\n"
            "V:\\SWA\\all\\scene\\Ep01\\sq0010\\SH0010\\lighting\\templates\\"
        )
    
    def _demo_asset_workflow(self):
        """Demonstrate asset-based template workflow."""
        print("\n" + "="*60)
        print("ASSET WORKFLOW DEMO")
        print("="*60)
        
        # Set asset context
        asset_context = {
            "type": "asset",
            "category": "Sets",
            "subcategory": "interior",
            "asset": "Kitchen"
        }
        
        # Update both widgets with context
        self.template_tools.set_context(asset_context)
        self.render_setup.set_context(asset_context)
        
        # Switch to Template Tools tab
        self.tab_widget.setCurrentIndex(0)
        
        # Show info message
        QtWidgets.QMessageBox.information(
            self, "Asset Workflow Demo",
            "🏠 Asset Workflow Demo Started!\n\n"
            "Context set to: Sets/interior/Kitchen\n\n"
            "Try the following:\n"
            "1. Create quick templates using the colored buttons\n"
            "2. Switch to Render Setup tab to export packages\n"
            "3. Templates will be created with KITCHEN prefix\n\n"
            "Template structure follows:\n"
            "V:\\SWA\\all\\asset\\Sets\\interior\\Kitchen\\lighting\\templates\\"
        )
    
    def _demo_export_import(self):
        """Demonstrate template package export/import."""
        print("\n" + "="*60)
        print("EXPORT/IMPORT DEMO")
        print("="*60)
        
        # Switch to Render Setup tab
        self.tab_widget.setCurrentIndex(1)
        
        # Show info message
        QtWidgets.QMessageBox.information(
            self, "Export/Import Demo",
            "📦 Export/Import Demo Started!\n\n"
            "This demonstrates the template package system:\n\n"
            "Export Features:\n"
            "• Light rig (.ma files)\n"
            "• Render layers (.json with Maya Render Setup API)\n"
            "• Render settings (.json with renderer-specific settings)\n"
            "• AOVs configuration (.json)\n"
            "• Package metadata (.json)\n\n"
            "Import Features:\n"
            "• Selective component import\n"
            "• Render layer merge modes (additive/replace/merge)\n"
            "• Cross-renderer compatibility\n\n"
            "Try using the Export Package button in the Render Setup tab!"
        )
    
    def _on_layer_created(self, layer_name: str):
        """Handle layer creation signal."""
        print(f"✅ Layer created: {layer_name}")
        
        # Show notification
        QtWidgets.QMessageBox.information(
            self, "Layer Created",
            f"✅ Render layer created successfully!\n\n"
            f"Layer: {layer_name}\n\n"
            f"The layer includes:\n"
            f"• Hierarchical collections (geo, light)\n"
            f"• Sub-collections (matte, visibility)\n"
            f"• Proper filter configurations\n"
            f"• Maya Render Setup API integration"
        )
    
    def _on_package_exported(self, package_name: str):
        """Handle package export signal."""
        print(f"📦 Package exported: {package_name}")
    
    def _on_package_imported(self, package_name: str):
        """Handle package import signal."""
        print(f"📥 Package imported: {package_name}")


def run_demo():
    """Run the template integration demo."""
    print("Starting Template Integration Demo...")
    
    # Check if we're in Maya
    try:
        import maya.cmds as cmds
        print("✅ Running in Maya environment")
        in_maya = True
    except ImportError:
        print("⚠️  Running outside Maya (some features may not work)")
        in_maya = False
    
    # Create Qt application if needed
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    
    # Create and show demo window
    demo = TemplateIntegrationDemo()
    demo.show()
    
    # Show welcome message
    QtWidgets.QMessageBox.information(
        demo, "Welcome to LRC Toolbox Demo",
        "🎉 Welcome to the LRC Toolbox Template Integration Demo!\n\n"
        "This demo showcases:\n"
        "✅ Quick template creation with hierarchical render layers\n"
        "✅ Template package export/import system\n"
        "✅ Project structure alignment\n"
        "✅ Maya Render Setup API integration\n"
        "✅ Multi-renderer support (Redshift priority)\n\n"
        "Use the Demo Controls buttons to explore different workflows!\n\n"
        f"Maya Environment: {'✅ Available' if in_maya else '❌ Not Available'}"
    )
    
    return demo


if __name__ == "__main__":
    demo = run_demo()
    
    # If running outside Maya, start event loop
    try:
        import maya.cmds
    except ImportError:
        import sys
        sys.exit(QtWidgets.QApplication.instance().exec_())
