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
        
        # Render layers
        layout.addWidget(QtWidgets.QLabel("Render Layers:"), row, 0)
        self.layers_combo = QtWidgets.QComboBox()
        self.layers_combo.setMinimumWidth(200)
        layout.addWidget(self.layers_combo, row, 1)
        
        self.refresh_layers_btn = QtWidgets.QPushButton("Refresh")
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
        layout.addWidget(self.gpu_combo, row, 1, 1, 2)
        row += 1
        
        # Render method
        layout.addWidget(QtWidgets.QLabel("Method:"), row, 0)
        self.method_combo = QtWidgets.QComboBox()
        self.method_combo.addItem("Auto (with fallback)", RenderMethod.AUTO)
        self.method_combo.addItem("mayapy Custom (Priority 1)", RenderMethod.MAYAPY_CUSTOM)
        self.method_combo.addItem("Render.exe (Priority 2)", RenderMethod.RENDER_EXE)
        self.method_combo.addItem("mayapy Basic (Priority 3)", RenderMethod.MAYAPY_BASIC)
        layout.addWidget(self.method_combo, row, 1, 1, 2)
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
            gpu_text = f"{system_info.gpu_count} total"
            self.gpu_info_label.setText(gpu_text)
            
            # CPU info
            cpu_text = f"{system_info.cpu_cores} cores, {system_info.cpu_threads} threads"
            self.cpu_info_label.setText(cpu_text)
            
            # Available
            avail_text = f"{system_info.available_gpus} GPUs, {system_info.available_cpu_threads} threads"
            self.available_info_label.setText(avail_text)
            
            # Update GPU combo
            self.gpu_combo.clear()
            for gpu in system_info.gpus:
                if gpu.is_available:
                    self.gpu_combo.addItem(
                        f"GPU {gpu.device_id}: {gpu.name}",
                        gpu.device_id
                    )
    
    def _refresh_render_layers(self) -> None:
        """Refresh render layers list."""
        from ...core.scene_preparation import ScenePreparation
        
        scene_prep = ScenePreparation()
        layers = scene_prep.get_render_layers()
        
        self.layers_combo.clear()
        self.layers_combo.addItems(layers)
        
        if layers:
            self.log_text.append(f"[UI] Found {len(layers)} render layers")
        else:
            self.log_text.append("[UI] No render layers found")
    
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

