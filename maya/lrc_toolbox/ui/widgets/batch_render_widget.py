# -*- coding: utf-8 -*-
"""
Batch Render Widget

Main UI for batch rendering with system info, render configuration,
process monitoring, and real-time logs.
"""

from typing import Optional, Dict, Any, List

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

from ...core.batch_render_api import BatchRenderAPI
from ...core.models import RenderConfig, RenderMode, RenderMethod, ProcessStatus


class BatchRenderWidget(QtWidgets.QWidget):
    """
    Batch Render widget for GPU-accelerated batch rendering.
    
    Features:
    - System information display
    - Render configuration
    - Process monitoring table
    - Real-time log viewer
    - Start/Stop controls
    """
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize Batch Render widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Initialize API
        self._api = BatchRenderAPI()
        self._api.initialize()
        
        # Connect signals
        self._connect_api_signals()
        
        # Setup UI
        self._setup_ui()
        
        # Load initial data
        self._refresh_system_info()
        self._refresh_render_layers()
        
        print("Batch Render Widget initialized")
    
    def _connect_api_signals(self) -> None:
        """Connect API signals to UI slots."""
        if hasattr(self._api, 'render_started'):
            self._api.render_started.connect(self._on_render_started)
        
        if hasattr(self._api, 'render_progress'):
            self._api.render_progress.connect(self._on_render_progress)
        
        if hasattr(self._api, 'render_completed'):
            self._api.render_completed.connect(self._on_render_completed)
        
        if hasattr(self._api, 'render_log'):
            self._api.render_log.connect(self._on_render_log)
        
        if hasattr(self._api, 'system_info_updated'):
            self._api.system_info_updated.connect(self._on_system_info_updated)
    
    def _setup_ui(self) -> None:
        """Setup user interface."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create sections
        self._create_system_info_section()
        self._create_config_section()
        self._create_process_table_section()
        self._create_log_section()
        self._create_control_section()
        
        # Add to main layout
        main_layout.addWidget(self.system_info_group)
        main_layout.addWidget(self.config_group)
        main_layout.addWidget(self.process_table_group, stretch=1)
        main_layout.addWidget(self.log_group, stretch=1)
        main_layout.addWidget(self.control_group)
    
    def _create_system_info_section(self) -> None:
        """Create system information section."""
        self.system_info_group = QtWidgets.QGroupBox("System Information")
        layout = QtWidgets.QGridLayout(self.system_info_group)
        
        # GPU info
        layout.addWidget(QtWidgets.QLabel("GPUs:"), 0, 0)
        self.gpu_info_label = QtWidgets.QLabel("Detecting...")
        layout.addWidget(self.gpu_info_label, 0, 1)
        
        # CPU info
        layout.addWidget(QtWidgets.QLabel("CPU:"), 1, 0)
        self.cpu_info_label = QtWidgets.QLabel("Detecting...")
        layout.addWidget(self.cpu_info_label, 1, 1)
        
        # Available resources
        layout.addWidget(QtWidgets.QLabel("Available:"), 2, 0)
        self.available_info_label = QtWidgets.QLabel("Detecting...")
        layout.addWidget(self.available_info_label, 2, 1)
        
        # Refresh button
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_system_info)
        layout.addWidget(self.refresh_btn, 0, 2, 3, 1)
    
    def _create_config_section(self) -> None:
        """Create render configuration section."""
        self.config_group = QtWidgets.QGroupBox("Render Configuration")
        layout = QtWidgets.QGridLayout(self.config_group)
        
        row = 0

        # Render Setup layers
        layout.addWidget(QtWidgets.QLabel("Render Setup Layer:"), row, 0)
        self.layers_combo = QtWidgets.QComboBox()
        self.layers_combo.setMinimumWidth(200)
        self.layers_combo.setToolTip("Select layer from Maya Render Setup (not legacy render layers)")
        layout.addWidget(self.layers_combo, row, 1)

        self.refresh_layers_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_layers_btn.setToolTip("Refresh layers from Render Setup")
        self.refresh_layers_btn.clicked.connect(self._refresh_render_layers)
        layout.addWidget(self.refresh_layers_btn, row, 2)
        row += 1
        
        # Frame range
        layout.addWidget(QtWidgets.QLabel("Frame Range:"), row, 0)
        self.frame_range_edit = QtWidgets.QLineEdit("1-24")
        self.frame_range_edit.setPlaceholderText("e.g., 1-24, 1,5,10, 1-100x5")
        layout.addWidget(self.frame_range_edit, row, 1, 1, 2)
        row += 1
        
        # GPU selection
        layout.addWidget(QtWidgets.QLabel("GPU:"), row, 0)
        self.gpu_combo = QtWidgets.QComboBox()
        self.gpu_combo.setToolTip(
            "Select GPU for batch rendering.\n"
            "Single GPU: Uses GPU 0 (shared with Maya)\n"
            "Multi-GPU: Uses GPU 1+ (GPU 0 reserved for Maya)"
        )
        layout.addWidget(self.gpu_combo, row, 1, 1, 2)
        row += 1
        
        # Render method with help button
        layout.addWidget(QtWidgets.QLabel("Render Method:"), row, 0)
        self.method_combo = QtWidgets.QComboBox()

        # Add methods with clear descriptions
        self.method_combo.addItem("Auto (Recommended)", RenderMethod.AUTO)
        self.method_combo.setItemData(0,
            "Automatically chooses best method with fallback.\n"
            "Tries: Custom Script → Render.exe → Basic Script\n"
            "✓ Most reliable, handles failures automatically",
            QtCore.Qt.ToolTipRole)

        self.method_combo.addItem("Custom Script (Advanced)", RenderMethod.MAYAPY_CUSTOM)
        self.method_combo.setItemData(1,
            "Uses mayapy with custom Python script.\n"
            "✓ Most flexible, allows pre/post operations\n"
            "✓ Best for complex pipelines\n"
            "⚠ Requires mayapy executable",
            QtCore.Qt.ToolTipRole)

        self.method_combo.addItem("Render.exe (Standard)", RenderMethod.RENDER_EXE)
        self.method_combo.setItemData(2,
            "Uses Maya's native Render.exe command.\n"
            "✓ Most reliable and battle-tested\n"
            "✓ Best for standard workflows\n"
            "⚠ Requires Render.exe executable",
            QtCore.Qt.ToolTipRole)

        self.method_combo.addItem("Basic Script (Fallback)", RenderMethod.MAYAPY_BASIC)
        self.method_combo.setItemData(3,
            "Uses mayapy with basic render command.\n"
            "✓ Simple and lightweight\n"
            "⚠ Limited functionality\n"
            "⚠ Last resort fallback",
            QtCore.Qt.ToolTipRole)

        self.method_combo.setToolTip("Choose render execution method (hover for details)")
        layout.addWidget(self.method_combo, row, 1)

        # Help button for method
        method_help_btn = QtWidgets.QPushButton("?")
        method_help_btn.setMaximumWidth(30)
        method_help_btn.setToolTip("Click for detailed explanation")
        method_help_btn.clicked.connect(self._show_method_help)
        layout.addWidget(method_help_btn, row, 2)
        row += 1
        
        # Renderer
        layout.addWidget(QtWidgets.QLabel("Renderer:"), row, 0)
        self.renderer_combo = QtWidgets.QComboBox()
        self.renderer_combo.addItems(["redshift", "arnold", "vray"])
        layout.addWidget(self.renderer_combo, row, 1, 1, 2)
    
    def _create_process_table_section(self) -> None:
        """Create process monitoring table."""
        self.process_table_group = QtWidgets.QGroupBox("Render Processes")
        layout = QtWidgets.QVBoxLayout(self.process_table_group)
        
        self.process_table = QtWidgets.QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels([
            "Process ID", "Layer", "Frames", "Status", "Progress", "Method"
        ])
        self.process_table.horizontalHeader().setStretchLastSection(True)
        self.process_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.process_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        
        layout.addWidget(self.process_table)
    
    def _create_log_section(self) -> None:
        """Create log viewer section."""
        self.log_group = QtWidgets.QGroupBox("Render Logs")
        layout = QtWidgets.QVBoxLayout(self.log_group)
        
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QtGui.QFont("Courier", 9))
        
        layout.addWidget(self.log_text)
        
        # Clear button
        clear_btn = QtWidgets.QPushButton("Clear Logs")
        clear_btn.clicked.connect(self.log_text.clear)
        layout.addWidget(clear_btn)
    
    def _create_control_section(self) -> None:
        """Create control buttons section."""
        self.control_group = QtWidgets.QGroupBox("Controls")
        layout = QtWidgets.QHBoxLayout(self.control_group)
        
        self.start_btn = QtWidgets.QPushButton("Start Batch Render")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self._start_render)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QtWidgets.QPushButton("Stop All")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_render)
        layout.addWidget(self.stop_btn)
    
    def _refresh_system_info(self) -> None:
        """Refresh system information display."""
        system_info = self._api.get_system_info()

        if system_info:
            # GPU info
            if system_info.gpu_count == 0:
                gpu_text = "No CUDA GPUs detected (CPU rendering only)"
            elif system_info.gpu_count == 1:
                gpu_text = f"1 GPU (shared with Maya)"
            else:
                gpu_text = f"{system_info.gpu_count} total ({system_info.available_gpus} for batch)"
            self.gpu_info_label.setText(gpu_text)

            # CPU info
            cpu_text = f"{system_info.cpu_cores} cores, {system_info.cpu_threads} threads"
            self.cpu_info_label.setText(cpu_text)

            # Available
            if system_info.gpu_count == 0:
                avail_text = f"CPU only: {system_info.available_cpu_threads} threads"
            elif system_info.gpu_count == 1:
                avail_text = f"GPU 0 (shared), {system_info.available_cpu_threads} CPU threads"
            else:
                avail_text = f"{system_info.available_gpus} GPUs, {system_info.available_cpu_threads} threads"
            self.available_info_label.setText(avail_text)

            # Update GPU combo
            self.gpu_combo.clear()

            if system_info.gpu_count == 0:
                # No GPU detected - add CPU option
                self.gpu_combo.addItem("CPU Rendering (No GPU)", 0)
            else:
                # Add available GPUs
                for gpu in system_info.gpus:
                    if gpu.is_available:
                        mem_gb = gpu.memory_total / (1024 ** 3)
                        status = " (shared)" if system_info.gpu_count == 1 else ""
                        self.gpu_combo.addItem(
                            f"GPU {gpu.device_id}: {gpu.name} ({mem_gb:.0f}GB){status}",
                            gpu.device_id
                        )
    
    def _refresh_render_layers(self) -> None:
        """Refresh render layers list from Render Setup."""
        from ...core.scene_preparation import ScenePreparation

        scene_prep = ScenePreparation()
        layers = scene_prep.get_render_layers()

        self.layers_combo.clear()
        self.layers_combo.addItems(layers)

        if layers:
            self.log_text.append(f"[UI] Found {len(layers)} layers from Render Setup")
        else:
            self.log_text.append("[UI] No Render Setup layers found. Please create layers in Render Setup first.")
    
    def _start_render(self) -> None:
        """Start batch render."""
        # Validate inputs
        layer = self.layers_combo.currentText()
        if not layer:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a render layer")
            return
        
        frame_range = self.frame_range_edit.text().strip()
        if not frame_range:
            QtWidgets.QMessageBox.warning(self, "Error", "Please enter frame range")
            return
        
        # Get GPU
        gpu_id = self.gpu_combo.currentData()
        if gpu_id is None:
            gpu_id = 1
        
        # Get method
        method = self.method_combo.currentData()
        
        # Get renderer
        renderer = self.renderer_combo.currentText()
        
        # Create config
        config = RenderConfig(
            scene_file="",  # Will be set by API
            layers=[layer],
            frame_range=frame_range,
            gpu_id=gpu_id,
            render_method=method,
            renderer=renderer
        )
        
        # Start render
        success = self._api.start_batch_render(config)
        
        if success:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.log_text.append(f"[UI] Started render: {layer} frames {frame_range}")
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Failed to start render")
    
    def _stop_render(self) -> None:
        """Stop all renders."""
        self._api.stop_all_renders()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_text.append("[UI] Stopped all renders")

    def _show_method_help(self) -> None:
        """Show detailed help dialog for render methods."""
        help_text = """
<h2>Render Method Explanation</h2>

<h3>🌟 Auto (Recommended)</h3>
<p><b>What it does:</b> Automatically selects the best method and falls back if it fails.</p>
<p><b>How it works:</b></p>
<ol>
  <li>Tries <b>Custom Script</b> first (most flexible)</li>
  <li>Falls back to <b>Render.exe</b> if custom fails (most reliable)</li>
  <li>Falls back to <b>Basic Script</b> as last resort</li>
</ol>
<p><b>When to use:</b> <span style="color: green;">Always use this unless you have specific needs!</span></p>
<p><b>Pros:</b> Handles failures automatically, most reliable</p>

<hr>

<h3>🔧 Custom Script (Advanced)</h3>
<p><b>What it does:</b> Runs mayapy with a custom Python script for maximum control.</p>
<p><b>How it works:</b> Creates a Python script that opens your scene, sets up render settings, and renders each frame individually.</p>
<p><b>When to use:</b> When you need custom pre/post render operations or complex pipeline integration.</p>
<p><b>Pros:</b> Most flexible, allows custom operations</p>
<p><b>Cons:</b> Requires mayapy, slightly slower</p>

<hr>

<h3>⚙️ Render.exe (Standard)</h3>
<p><b>What it does:</b> Uses Maya's native batch renderer (Render.exe on Windows, Render on Linux).</p>
<p><b>How it works:</b> Calls Maya's built-in batch render command directly.</p>
<p><b>When to use:</b> For standard rendering workflows without custom operations.</p>
<p><b>Pros:</b> Most reliable, battle-tested, handles edge cases</p>
<p><b>Cons:</b> Less flexible, no custom operations</p>

<hr>

<h3>📦 Basic Script (Fallback)</h3>
<p><b>What it does:</b> Simple mayapy script with basic batch render command.</p>
<p><b>How it works:</b> Opens scene and calls Maya's batchRender() command.</p>
<p><b>When to use:</b> Only as last resort when other methods fail.</p>
<p><b>Pros:</b> Simple, lightweight</p>
<p><b>Cons:</b> Limited functionality, least reliable</p>

<hr>

<h3>💡 Quick Guide</h3>
<table border="1" cellpadding="5">
  <tr>
    <th>Your Situation</th>
    <th>Recommended Method</th>
  </tr>
  <tr>
    <td>Normal rendering</td>
    <td><b>Auto</b> (let system decide)</td>
  </tr>
  <tr>
    <td>Need custom operations</td>
    <td><b>Custom Script</b></td>
  </tr>
  <tr>
    <td>Standard workflow</td>
    <td><b>Render.exe</b></td>
  </tr>
  <tr>
    <td>Troubleshooting</td>
    <td>Try each method manually</td>
  </tr>
</table>

<p><b>Note:</b> All methods use the same GPU allocation and frame range settings.</p>
        """

        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("Render Method Help")
        msg_box.setTextFormat(QtCore.Qt.RichText)
        msg_box.setText(help_text)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.setMinimumWidth(600)
        msg_box.exec_()
    
    def _on_render_started(self, process_id: str) -> None:
        """Handle render started signal."""
        self.log_text.append(f"[Render] Started: {process_id}")
        self._update_process_table()
    
    def _on_render_progress(self, process_id: str, progress: float) -> None:
        """Handle render progress signal."""
        self._update_process_table()
    
    def _on_render_completed(self, process_id: str, success: bool) -> None:
        """Handle render completed signal."""
        status = "SUCCESS" if success else "FAILED"
        self.log_text.append(f"[Render] Completed: {process_id} - {status}")
        self._update_process_table()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def _on_render_log(self, process_id: str, message: str) -> None:
        """Handle render log message."""
        self.log_text.append(f"[{process_id}] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def _on_system_info_updated(self, system_info) -> None:
        """Handle system info updated signal."""
        self._refresh_system_info()
    
    def _update_process_table(self) -> None:
        """Update process table with current processes."""
        processes = self._api.get_render_status()
        
        self.process_table.setRowCount(len(processes))
        
        for row, process in enumerate(processes):
            self.process_table.setItem(row, 0, QtWidgets.QTableWidgetItem(process.process_id))
            self.process_table.setItem(row, 1, QtWidgets.QTableWidgetItem(process.layer_name))
            self.process_table.setItem(row, 2, QtWidgets.QTableWidgetItem(process.frame_range))
            self.process_table.setItem(row, 3, QtWidgets.QTableWidgetItem(process.status.value))
            self.process_table.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{process.progress:.1f}%"))
            self.process_table.setItem(row, 5, QtWidgets.QTableWidgetItem(process.render_method.value))
    
    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        self._api.cleanup()
        super().closeEvent(event)

