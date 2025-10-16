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
from ..render_log_viewer import RenderLogViewer


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

        # Log viewer dialog - CRITICAL: Create immediately to capture all logs
        self._log_viewer = RenderLogViewer(self)

        # Floating process table
        self._floating_table = None

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
        self._create_control_section()  # Log button moved here

        # Add to main layout
        main_layout.addWidget(self.system_info_group)
        main_layout.addWidget(self.config_group)
        main_layout.addWidget(self.process_table_group, stretch=1)
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

        # Render Setup layers - IMPROVED: Multi-selection list
        layout.addWidget(QtWidgets.QLabel("Render Layers:"), row, 0, QtCore.Qt.AlignTop)

        # Layer list with multi-selection
        layers_container = QtWidgets.QWidget()
        layers_layout = QtWidgets.QVBoxLayout(layers_container)
        layers_layout.setContentsMargins(0, 0, 0, 0)
        layers_layout.setSpacing(4)

        self.layers_list = QtWidgets.QListWidget()
        self.layers_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.layers_list.setMaximumHeight(100)
        self.layers_list.setToolTip(
            "Select render layers (Ctrl+Click for multiple, Shift+Click for range)\n"
            "Each selected layer will be rendered as a separate job"
        )
        layers_layout.addWidget(self.layers_list)

        # Layer selection buttons
        layer_btn_layout = QtWidgets.QHBoxLayout()
        layer_btn_layout.setSpacing(4)

        self.select_all_layers_btn = QtWidgets.QPushButton("Select All")
        self.select_all_layers_btn.setToolTip("Select all layers")
        self.select_all_layers_btn.clicked.connect(self._select_all_layers)
        layer_btn_layout.addWidget(self.select_all_layers_btn)

        self.clear_layers_btn = QtWidgets.QPushButton("Clear")
        self.clear_layers_btn.setToolTip("Clear selection")
        self.clear_layers_btn.clicked.connect(self._clear_layer_selection)
        layer_btn_layout.addWidget(self.clear_layers_btn)

        self.refresh_layers_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_layers_btn.setToolTip("Refresh layers from Render Setup")
        self.refresh_layers_btn.clicked.connect(self._refresh_render_layers)
        layer_btn_layout.addWidget(self.refresh_layers_btn)

        layers_layout.addLayout(layer_btn_layout)

        layout.addWidget(layers_container, row, 1, 1, 2)
        row += 1
        
        # Frame range with help button
        layout.addWidget(QtWidgets.QLabel("Frame Range:"), row, 0)
        self.frame_range_edit = QtWidgets.QLineEdit("1-24")
        self.frame_range_edit.setPlaceholderText("e.g., 1-24, 1,5,10, 1-100x5")
        self.frame_range_edit.setToolTip(
            "Frame Range Syntax:\n\n"
            "Simple ranges:\n"
            "  1-24        → Frames 1 to 24\n"
            "  10-20       → Frames 10 to 20\n\n"
            "Specific frames:\n"
            "  1,5,10      → Only frames 1, 5, and 10\n"
            "  1,10,20,30  → Only these frames\n\n"
            "Steps (every Nth frame):\n"
            "  1-24x2      → Every 2nd frame (1,3,5,...,23,24)\n"
            "  1-100x5     → Every 5th frame (1,6,11,...,96,100)\n"
            "  ⚠ First and last frames always included!\n\n"
            "Combined:\n"
            "  1-10,20-30  → Frames 1-10 and 20-30\n"
            "  1,10-20,50  → Frame 1, frames 10-20, and frame 50\n"
            "  1-10x2,50   → Every 2nd frame from 1-10, plus frame 50"
        )
        layout.addWidget(self.frame_range_edit, row, 1)

        # Help button for frame range
        frame_help_btn = QtWidgets.QPushButton("?")
        frame_help_btn.setMaximumWidth(30)
        frame_help_btn.setToolTip("Click for frame range syntax examples")
        frame_help_btn.clicked.connect(self._show_frame_range_help)
        layout.addWidget(frame_help_btn, row, 2)
        row += 1
        
        # GPU selection - IMPROVED: Concurrent job support
        layout.addWidget(QtWidgets.QLabel("GPU Assignment:"), row, 0)

        gpu_container = QtWidgets.QWidget()
        gpu_layout = QtWidgets.QHBoxLayout(gpu_container)
        gpu_layout.setContentsMargins(0, 0, 0, 0)
        gpu_layout.setSpacing(8)

        self.gpu_mode_combo = QtWidgets.QComboBox()
        self.gpu_mode_combo.addItem("Auto (FIFO Queue)", "auto")
        self.gpu_mode_combo.addItem("Manual Assignment", "manual")
        self.gpu_mode_combo.setToolTip(
            "Auto: Jobs queued and assigned to available GPUs automatically\n"
            "Manual: Specify GPU for each job"
        )
        self.gpu_mode_combo.currentIndexChanged.connect(self._on_gpu_mode_changed)
        gpu_layout.addWidget(self.gpu_mode_combo, 1)

        self.gpu_combo = QtWidgets.QComboBox()
        self.gpu_combo.setToolTip("Select GPU for manual assignment")
        self.gpu_combo.setEnabled(False)  # Disabled by default (Auto mode)
        gpu_layout.addWidget(self.gpu_combo, 1)

        self.concurrent_jobs_spin = QtWidgets.QSpinBox()
        self.concurrent_jobs_spin.setMinimum(1)
        self.concurrent_jobs_spin.setMaximum(8)
        self.concurrent_jobs_spin.setValue(1)
        self.concurrent_jobs_spin.setPrefix("Max Jobs: ")
        self.concurrent_jobs_spin.setToolTip(
            "Maximum concurrent render jobs\n"
            "Set based on available GPUs and memory"
        )
        gpu_layout.addWidget(self.concurrent_jobs_spin)

        layout.addWidget(gpu_container, row, 1, 1, 2)
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
        
        # Renderer with GPU/CPU mode
        layout.addWidget(QtWidgets.QLabel("Renderer:"), row, 0)

        renderer_container = QtWidgets.QWidget()
        renderer_layout = QtWidgets.QHBoxLayout(renderer_container)
        renderer_layout.setContentsMargins(0, 0, 0, 0)
        renderer_layout.setSpacing(8)

        self.renderer_combo = QtWidgets.QComboBox()
        self.renderer_combo.addItems(["redshift", "arnold", "vray"])
        self.renderer_combo.currentIndexChanged.connect(self._on_renderer_changed)
        renderer_layout.addWidget(self.renderer_combo, 2)

        # GPU/CPU mode for renderer
        self.render_mode_combo = QtWidgets.QComboBox()
        self.render_mode_combo.addItem("GPU", "gpu")
        self.render_mode_combo.addItem("CPU", "cpu")
        self.render_mode_combo.setToolTip(
            "GPU: Use GPU acceleration (faster, requires CUDA)\n"
            "CPU: Use CPU rendering (slower, more compatible)"
        )
        renderer_layout.addWidget(self.render_mode_combo, 1)

        layout.addWidget(renderer_container, row, 1, 1, 2)
        row += 1
    
    def _create_process_table_section(self) -> None:
        """Create process monitoring table - IMPROVED: Compact with float button."""
        self.process_table_group = QtWidgets.QGroupBox("Render Processes")
        layout = QtWidgets.QVBoxLayout(self.process_table_group)
        layout.setSpacing(4)

        # Header with float button
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(8)

        status_label = QtWidgets.QLabel("Active Jobs: 0")
        status_label.setStyleSheet("font-weight: bold;")
        self.process_status_label = status_label
        header_layout.addWidget(status_label)

        header_layout.addStretch()

        float_btn = QtWidgets.QPushButton("Float Window")
        float_btn.setToolTip("Open process table in floating window")
        float_btn.clicked.connect(self._float_process_table)
        header_layout.addWidget(float_btn)

        layout.addLayout(header_layout)

        # Process table - IMPROVED: Taller to match widget
        self.process_table = QtWidgets.QTableWidget()
        self.process_table.setColumnCount(7)
        self.process_table.setHorizontalHeaderLabels([
            "Layer", "Frames", "GPU", "Status", "Progress", "Time", "Actions"
        ])
        self.process_table.horizontalHeader().setStretchLastSection(False)
        self.process_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.process_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.process_table.setMinimumHeight(200)  # Taller minimum height
        # No maximum height - let it expand with widget
        self.process_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.process_table.customContextMenuRequested.connect(self._show_process_context_menu)

        # Set column widths
        self.process_table.setColumnWidth(0, 120)  # Layer
        self.process_table.setColumnWidth(1, 80)   # Frames
        self.process_table.setColumnWidth(2, 50)   # GPU
        self.process_table.setColumnWidth(3, 80)   # Status
        self.process_table.setColumnWidth(4, 100)  # Progress
        self.process_table.setColumnWidth(5, 80)   # Time
        self.process_table.horizontalHeader().setStretchLastSection(True)  # Actions

        layout.addWidget(self.process_table)
    
    def _create_control_section(self) -> None:
        """Create control buttons section - IMPROVED: Log button moved here."""
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

        # Log viewer button - MOVED from separate section
        self.open_logs_btn = QtWidgets.QPushButton("Open Log Viewer")
        self.open_logs_btn.setMinimumHeight(40)  # Match other buttons
        self.open_logs_btn.clicked.connect(self._open_log_viewer)
        layout.addWidget(self.open_logs_btn)
    
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
        """Refresh render layers list from Render Setup - IMPROVED: Multi-select list."""
        from ...core.scene_preparation import ScenePreparation

        scene_prep = ScenePreparation()
        layers = scene_prep.get_render_layers()

        self.layers_list.clear()
        self.layers_list.addItems(layers)

        if layers:
            print(f"[UI] Found {len(layers)} layers from Render Setup")
        else:
            print("[UI] No Render Setup layers found. Please create layers in Render Setup first.")

    def _select_all_layers(self) -> None:
        """Select all layers in the list."""
        self.layers_list.selectAll()

    def _clear_layer_selection(self) -> None:
        """Clear layer selection."""
        self.layers_list.clearSelection()

    def _on_gpu_mode_changed(self, index: int) -> None:
        """Handle GPU mode change."""
        mode = self.gpu_mode_combo.currentData()

        if mode == "manual":
            self.gpu_combo.setEnabled(True)
            self.concurrent_jobs_spin.setEnabled(False)
        else:  # auto
            self.gpu_combo.setEnabled(False)
            self.concurrent_jobs_spin.setEnabled(True)

    def _on_renderer_changed(self, index: int) -> None:
        """Handle renderer change - update render mode options."""
        renderer = self.renderer_combo.currentText()

        # Arnold supports both GPU and CPU well
        # Redshift is GPU-only (but has CPU fallback)
        # V-Ray supports both

        if renderer == "redshift":
            # Redshift is primarily GPU
            self.render_mode_combo.setCurrentIndex(0)  # Default to GPU
        elif renderer == "arnold":
            # Arnold CPU is very common
            self.render_mode_combo.setCurrentIndex(1)  # Default to CPU
        else:  # vray
            self.render_mode_combo.setCurrentIndex(0)  # Default to GPU
    
    def _start_render(self) -> None:
        """Start batch render - IMPROVED: Multiple layers support."""
        # Validate inputs - Get selected layers
        selected_items = self.layers_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select at least one render layer")
            return

        # CRITICAL FIX: Clean layer names (remove newlines, extra whitespace)
        layers = []
        for item in selected_items:
            layer_name = item.text().strip()
            # Remove newlines and normalize whitespace
            layer_name = ' '.join(layer_name.split())
            if layer_name:
                layers.append(layer_name)

        if not layers:
            QtWidgets.QMessageBox.warning(self, "Error", "No valid layers selected")
            return

        frame_range = self.frame_range_edit.text().strip()
        if not frame_range:
            QtWidgets.QMessageBox.warning(self, "Error", "Please enter frame range")
            return

        # CRITICAL: Verify renderable camera before starting render
        try:
            import maya.cmds as cmds

            # Get renderable cameras
            renderable_cameras = []
            all_cameras = cmds.ls(type='camera')
            for cam in all_cameras:
                if cmds.getAttr(f"{cam}.renderable"):
                    transform = cmds.listRelatives(cam, parent=True, type='transform')
                    if transform:
                        renderable_cameras.append(transform[0])

            # Check camera count
            if len(renderable_cameras) == 0:
                QtWidgets.QMessageBox.critical(
                    self,
                    "No Renderable Camera",
                    "No camera is set as renderable!\n\n"
                    "Please set a camera as renderable:\n"
                    "1. Select your render camera\n"
                    "2. Open Attribute Editor\n"
                    "3. Go to camera shape tab\n"
                    "4. Check 'Renderable' checkbox"
                )
                return

            elif len(renderable_cameras) > 1:
                cam_list = "\n".join([f"  • {cam}" for cam in renderable_cameras])
                result = QtWidgets.QMessageBox.warning(
                    self,
                    "Multiple Renderable Cameras",
                    f"Multiple cameras are set as renderable:\n\n{cam_list}\n\n"
                    f"Render.exe will use the FIRST one (unpredictable).\n\n"
                    f"Do you want to continue anyway?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                if result == QtWidgets.QMessageBox.No:
                    return

            else:
                # Exactly one renderable camera - perfect!
                print(f"[UI] Renderable camera: {renderable_cameras[0]}")

        except Exception as e:
            print(f"[UI] Warning: Could not verify renderable camera: {e}")

        # Get GPU mode and settings
        gpu_mode = self.gpu_mode_combo.currentData()
        max_concurrent = self.concurrent_jobs_spin.value()

        # Get method, renderer, and render mode
        method = self.method_combo.currentData()
        renderer = self.renderer_combo.currentText()
        render_mode = self.render_mode_combo.currentData()  # "gpu" or "cpu"
        use_gpu = (render_mode == "gpu")

        # CRITICAL: Set max concurrent jobs in API
        self._api.set_max_concurrent_jobs(max_concurrent)

        print(f"[UI] Render settings: {renderer} ({render_mode.upper()}), Max concurrent: {max_concurrent}")

        # Confirm multiple layers
        if len(layers) > 1:
            result = QtWidgets.QMessageBox.question(
                self,
                "Multiple Layers",
                f"Start {len(layers)} render jobs?\n\n"
                f"Layers: {', '.join(layers)}\n"
                f"Frames: {frame_range}\n"
                f"GPU Mode: {gpu_mode.upper()}\n"
                f"Max Concurrent: {max_concurrent if gpu_mode == 'auto' else 'N/A'}\n\n"
                f"Jobs will be queued and start automatically as slots become available.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes
            )
            if result == QtWidgets.QMessageBox.No:
                return

        # Get current scene file for output path calculation
        try:
            import maya.cmds as cmds
            current_scene = cmds.file(query=True, sceneName=True)
            if not current_scene:
                QtWidgets.QMessageBox.warning(self, "Error", "No scene file open. Please save your scene first.")
                return
        except Exception as e:
            print(f"[UI] Error getting current scene: {e}")
            QtWidgets.QMessageBox.warning(self, "Error", f"Could not get current scene file: {e}")
            return

        # Start render for each layer (will queue if needed)
        success_count = 0
        for layer_index, layer in enumerate(layers):
            # Get GPU for this job
            if gpu_mode == "manual":
                gpu_id = self.gpu_combo.currentData()
                if gpu_id is None:
                    gpu_id = 1
            else:
                # Auto mode - Use round-robin GPU assignment
                # Get available GPUs from system info
                system_info = self._api.get_system_info()
                if system_info and system_info.gpus:
                    gpu_count = len(system_info.gpus)
                    # Round-robin: distribute jobs across all GPUs
                    gpu_id = (layer_index % gpu_count) + 1  # 1-based indexing
                    print(f"[UI] Auto-assigning layer '{layer}' to GPU {gpu_id} (of {gpu_count} GPUs)")
                else:
                    gpu_id = 1  # Fallback if no GPU info

            # Create config with CURRENT scene file (critical for correct output path)
            config = RenderConfig(
                scene_file=current_scene,  # CRITICAL: Use current scene for version extraction
                layers=[layer],
                frame_range=frame_range,
                gpu_id=gpu_id,
                render_method=method,
                renderer=renderer,
                use_gpu=use_gpu  # Pass GPU/CPU mode
            )

            # Start render
            success = self._api.start_batch_render(config)
            if success:
                success_count += 1
                print(f"[UI] Started render: {layer} frames {frame_range}")

        if success_count > 0:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            print(f"[UI] Started {success_count}/{len(layers)} render jobs")
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Failed to start any renders")
    
    def _stop_render(self) -> None:
        """Stop all renders."""
        self._api.stop_all_renders()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        print("[UI] Stopped all renders")

    def _open_log_viewer(self) -> None:
        """Open the log viewer dialog."""
        # Log viewer is already created in __init__, just show it
        self._log_viewer.show()
        self._log_viewer.raise_()
        self._log_viewer.activateWindow()

    def _float_process_table(self) -> None:
        """Open process table in floating window - IMPLEMENTED!"""
        if not self._floating_table:
            from ..floating_process_table import FloatingProcessTable
            self._floating_table = FloatingProcessTable(self._api, self)

        self._floating_table.show()
        self._floating_table.raise_()
        self._floating_table.activateWindow()

    def _show_process_context_menu(self, position) -> None:
        """Show context menu for process table."""
        # Get selected row
        row = self.process_table.rowAt(position.y())
        if row < 0:
            return

        # Get process ID from row
        process_id_item = self.process_table.item(row, 0)
        if not process_id_item:
            return

        process_id = process_id_item.data(QtCore.Qt.UserRole)
        if not process_id:
            return

        # Create context menu
        menu = QtWidgets.QMenu(self)

        # Re-render action
        rerender_action = menu.addAction("Re-render...")
        rerender_action.triggered.connect(lambda: self._rerender_job(process_id))

        # Stop action
        stop_action = menu.addAction("Stop Job")
        stop_action.triggered.connect(lambda: self._stop_job(process_id))

        menu.addSeparator()

        # View logs action
        logs_action = menu.addAction("View Logs")
        logs_action.triggered.connect(lambda: self._view_job_logs(process_id))

        # Show menu
        menu.exec_(self.process_table.viewport().mapToGlobal(position))

    def _rerender_job(self, process_id: str) -> None:
        """Re-render a job with custom settings."""
        # Get process info
        processes = self._api.get_render_status()
        process = None
        for p in processes:
            if p.process_id == process_id:
                process = p
                break

        if not process:
            QtWidgets.QMessageBox.warning(self, "Error", "Process not found")
            return

        # Show re-render dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Re-render: {process.layer_name}")
        dialog.setMinimumWidth(400)

        layout = QtWidgets.QFormLayout(dialog)

        # Layer (read-only)
        layer_edit = QtWidgets.QLineEdit(process.layer_name)
        layer_edit.setReadOnly(True)
        layout.addRow("Layer:", layer_edit)

        # Frame range (editable)
        frame_edit = QtWidgets.QLineEdit(process.frame_range)
        frame_edit.setPlaceholderText("e.g., 1-24, 1,5,10")
        layout.addRow("Frame Range:", frame_edit)

        # GPU
        gpu_combo = QtWidgets.QComboBox()
        # Copy GPU list from main widget
        for i in range(self.gpu_combo.count()):
            gpu_combo.addItem(self.gpu_combo.itemText(i), self.gpu_combo.itemData(i))
        layout.addRow("GPU:", gpu_combo)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        # Show dialog
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Start new render with updated settings
            new_frame_range = frame_edit.text().strip()
            new_gpu_id = gpu_combo.currentData()

            if not new_frame_range:
                QtWidgets.QMessageBox.warning(self, "Error", "Please enter frame range")
                return

            # Create new config
            config = RenderConfig(
                scene_file="",
                layers=[process.layer_name],
                frame_range=new_frame_range,
                gpu_id=new_gpu_id if new_gpu_id is not None else 1,
                render_method=process.render_method,
                renderer="redshift"  # TODO: Get from process
            )

            # Start render
            success = self._api.start_batch_render(config)
            if success:
                print(f"[UI] Re-rendering: {process.layer_name} frames {new_frame_range}")
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to start re-render")

    def _stop_job(self, process_id: str) -> None:
        """Stop a specific job."""
        # TODO: Implement stop single job in API
        QtWidgets.QMessageBox.information(
            self,
            "Coming Soon",
            "Stop single job will be implemented in next update.\n\n"
            "For now, use 'Stop All' button to stop all renders."
        )

    def _view_job_logs(self, process_id: str) -> None:
        """View logs for a specific job."""
        # Open log viewer
        self._log_viewer.show()
        self._log_viewer.raise_()
        self._log_viewer.activateWindow()

        # Select the specific process in the dropdown
        for i in range(self._log_viewer.process_combo.count()):
            if self._log_viewer.process_combo.itemData(i) == process_id:
                self._log_viewer.process_combo.setCurrentIndex(i)
                break

    def _show_frame_range_help(self) -> None:
        """Show detailed help dialog for frame range syntax."""
        help_text = """
<h2>Frame Range Syntax Guide</h2>

<h3>📋 Simple Ranges</h3>
<table border="1" cellpadding="5">
  <tr>
    <th>Input</th>
    <th>Result</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><b>1-24</b></td>
    <td>1, 2, 3, ..., 24</td>
    <td>All frames from 1 to 24</td>
  </tr>
  <tr>
    <td><b>10-20</b></td>
    <td>10, 11, 12, ..., 20</td>
    <td>All frames from 10 to 20</td>
  </tr>
  <tr>
    <td><b>100-150</b></td>
    <td>100, 101, 102, ..., 150</td>
    <td>All frames from 100 to 150</td>
  </tr>
</table>

<h3>🎯 Specific Frames</h3>
<table border="1" cellpadding="5">
  <tr>
    <th>Input</th>
    <th>Result</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><b>1,5,10</b></td>
    <td>1, 5, 10</td>
    <td>Only these 3 frames</td>
  </tr>
  <tr>
    <td><b>1,10,20,30</b></td>
    <td>1, 10, 20, 30</td>
    <td>Only these 4 frames</td>
  </tr>
  <tr>
    <td><b>5,15,25,35,45</b></td>
    <td>5, 15, 25, 35, 45</td>
    <td>Every 10th frame manually</td>
  </tr>
</table>

<h3>⚡ Steps (Every Nth Frame)</h3>
<table border="1" cellpadding="5">
  <tr>
    <th>Input</th>
    <th>Result</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><b>1-24x2</b></td>
    <td>1, 3, 5, 7, ..., 23, <span style="color: red;">24</span></td>
    <td>Every 2nd frame</td>
  </tr>
  <tr>
    <td><b>1-100x5</b></td>
    <td>1, 6, 11, 16, ..., 96, <span style="color: red;">100</span></td>
    <td>Every 5th frame</td>
  </tr>
  <tr>
    <td><b>1-10x3</b></td>
    <td>1, 4, 7, <span style="color: red;">10</span></td>
    <td>Every 3rd frame</td>
  </tr>
</table>

<p><b>⚠️ Important:</b> <span style="color: red;">First and last frames are ALWAYS included</span> when using steps!</p>

<h3>🔀 Combined Syntax</h3>
<table border="1" cellpadding="5">
  <tr>
    <th>Input</th>
    <th>Result</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><b>1-10,20-30</b></td>
    <td>1-10, 20-30</td>
    <td>Two separate ranges</td>
  </tr>
  <tr>
    <td><b>1,10-20,50</b></td>
    <td>1, 10-20, 50</td>
    <td>Mix of single frames and range</td>
  </tr>
  <tr>
    <td><b>1-10x2,50-60</b></td>
    <td>1,3,5,7,9,10, 50-60</td>
    <td>Steps + range</td>
  </tr>
  <tr>
    <td><b>1,5,10-20,50,60-70x2</b></td>
    <td>Complex mix</td>
    <td>All syntax combined</td>
  </tr>
</table>

<h3>💡 Common Use Cases</h3>
<table border="1" cellpadding="5">
  <tr>
    <th>Scenario</th>
    <th>Frame Range</th>
  </tr>
  <tr>
    <td>Full animation (120 frames)</td>
    <td><b>1-120</b></td>
  </tr>
  <tr>
    <td>Preview render (every other frame)</td>
    <td><b>1-120x2</b></td>
  </tr>
  <tr>
    <td>Fast preview (every 5th frame)</td>
    <td><b>1-120x5</b></td>
  </tr>
  <tr>
    <td>Test render (first, middle, last)</td>
    <td><b>1,60,120</b></td>
  </tr>
  <tr>
    <td>Multiple shots</td>
    <td><b>1-24,50-74,100-124</b></td>
  </tr>
  <tr>
    <td>Key frames only</td>
    <td><b>1,12,24,36,48,60</b></td>
  </tr>
</table>

<h3>✅ Valid Examples</h3>
<ul>
  <li><b>1-24</b> - Simple range</li>
  <li><b>1-100x10</b> - Every 10th frame</li>
  <li><b>1,5,10,15,20</b> - Specific frames</li>
  <li><b>1-10,20-30,40-50</b> - Multiple ranges</li>
  <li><b>1-50x5,100-150</b> - Steps + range</li>
</ul>

<h3>❌ Invalid Examples</h3>
<ul>
  <li><b>24-1</b> - Start must be less than end</li>
  <li><b>1-24x0</b> - Step must be greater than 0</li>
  <li><b>abc</b> - Must be numbers</li>
  <li><b>1..24</b> - Use single dash, not double</li>
</ul>

<p><b>Tip:</b> Hover over the frame range field to see quick syntax reminder!</p>
        """

        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("Frame Range Syntax Help")
        msg_box.setTextFormat(QtCore.Qt.RichText)
        msg_box.setText(help_text)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.setMinimumWidth(700)
        msg_box.exec_()

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
        print(f"[Render] Started: {process_id}")

        # Add process to log viewer
        if self._log_viewer:
            processes = self._api.get_render_status()
            for process in processes:
                if process.process_id == process_id:
                    display_name = f"{process.layer_name} - {process.frame_range}"
                    self._log_viewer.add_process(process_id, display_name)
                    break

        self._update_process_table()

    def _on_render_progress(self, process_id: str, progress: float) -> None:
        """Handle render progress signal."""
        self._update_process_table()

    def _on_render_completed(self, process_id: str, success: bool) -> None:
        """Handle render completed signal."""
        status = "SUCCESS" if success else "FAILED"
        print(f"[Render] Completed: {process_id} - {status}")

        # Get output path from process (parsed from render logs)
        output_path = None
        processes = self._api.get_render_status()
        for process in processes:
            if process.process_id == process_id:
                # Use the output path parsed from "Saved file" messages
                if hasattr(process, 'output_path') and process.output_path:
                    output_path = process.output_path
                break

        # Add completion message to log viewer
        if self._log_viewer:
            self._log_viewer.add_completion_message(process_id, success, output_path)

        # Show output path in console
        if success and output_path:
            print(f"[Render] Output: {output_path}")

        self._update_process_table()

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _on_render_log(self, process_id: str, message: str) -> None:
        """Handle render log message."""
        # Send to log viewer instead of script editor
        if self._log_viewer:
            self._log_viewer.add_log(process_id, message)
    
    def _on_system_info_updated(self, system_info) -> None:
        """Handle system info updated signal."""
        self._refresh_system_info()
    
    def _update_process_table(self) -> None:
        """Update process table with current processes - IMPROVED: New columns."""
        processes = self._api.get_render_status()

        self.process_table.setRowCount(len(processes))

        # Update status label
        active_count = sum(1 for p in processes if p.status in [ProcessStatus.RENDERING, ProcessStatus.INITIALIZING, ProcessStatus.WAITING])
        self.process_status_label.setText(f"Active Jobs: {active_count} / Total: {len(processes)}")

        for row, process in enumerate(processes):
            # Column 0: Layer
            layer_item = QtWidgets.QTableWidgetItem(process.layer_name)
            layer_item.setData(QtCore.Qt.UserRole, process.process_id)  # Store process ID
            self.process_table.setItem(row, 0, layer_item)

            # Column 1: Frames
            self.process_table.setItem(row, 1, QtWidgets.QTableWidgetItem(process.frame_range))

            # Column 2: GPU
            gpu_text = f"GPU {process.gpu_id if hasattr(process, 'gpu_id') else 'N/A'}"
            self.process_table.setItem(row, 2, QtWidgets.QTableWidgetItem(gpu_text))

            # Column 3: Status
            status_item = QtWidgets.QTableWidgetItem(process.status.value.upper())
            # Color code status
            if process.status == ProcessStatus.COMPLETED:
                status_item.setForeground(QtGui.QColor(0, 150, 0))  # Green
            elif process.status == ProcessStatus.FAILED:
                status_item.setForeground(QtGui.QColor(200, 0, 0))  # Red
            elif process.status == ProcessStatus.RENDERING:
                status_item.setForeground(QtGui.QColor(0, 100, 200))  # Blue
            self.process_table.setItem(row, 3, status_item)

            # Column 4: Progress
            progress_text = f"{process.progress:.1f}%"
            if process.current_frame > 0 and process.total_frames > 0:
                progress_text += f" ({process.current_frame}/{process.total_frames})"
            self.process_table.setItem(row, 4, QtWidgets.QTableWidgetItem(progress_text))

            # Column 5: Time
            if process.start_time:
                from datetime import datetime
                elapsed = datetime.now() - process.start_time
                minutes = int(elapsed.total_seconds() / 60)
                seconds = int(elapsed.total_seconds() % 60)
                time_text = f"{minutes}m {seconds}s"
            else:
                time_text = "N/A"
            self.process_table.setItem(row, 5, QtWidgets.QTableWidgetItem(time_text))

            # Column 6: Actions (buttons)
            actions_widget = QtWidgets.QWidget()
            actions_layout = QtWidgets.QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)

            # Re-render button only (logs accessible via right-click or main button)
            rerender_btn = QtWidgets.QPushButton("⟳")
            rerender_btn.setToolTip("Re-render with custom settings")
            rerender_btn.setMaximumWidth(30)
            rerender_btn.clicked.connect(lambda checked, pid=process.process_id: self._rerender_job(pid))
            actions_layout.addWidget(rerender_btn)

            self.process_table.setCellWidget(row, 6, actions_widget)
    
    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        self._api.cleanup()
        super().closeEvent(event)

