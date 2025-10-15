# -*- coding: utf-8 -*-
"""
Floating Process Table Window

Detachable window for monitoring render processes.
"""

from typing import Optional, List
from datetime import datetime

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

from ..core.models import ProcessStatus


class FloatingProcessTable(QtWidgets.QDialog):
    """
    Floating window for render process monitoring.
    
    Features:
    - Detachable from main widget
    - Resizable and movable
    - Always-on-top option
    - Auto-refresh from API
    """
    
    def __init__(self, api, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize floating process table.
        
        Args:
            api: BatchRenderAPI instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._api = api
        
        # Window settings
        self.setWindowTitle("Render Processes - LRC Toolbox")
        self.setMinimumSize(800, 400)
        self.resize(1000, 600)
        
        # Make it a tool window (stays on top of Maya)
        self.setWindowFlags(
            QtCore.Qt.Window | 
            QtCore.Qt.WindowStaysOnTopHint
        )
        
        # Setup UI
        self._setup_ui()
        
        # Setup refresh timer
        self._refresh_timer = QtCore.QTimer()
        self._refresh_timer.timeout.connect(self._refresh_table)
        self._refresh_timer.start(1000)  # Refresh every second
        
        print("[FloatingProcessTable] Initialized")
    
    def _setup_ui(self) -> None:
        """Setup user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(8)
        
        self.status_label = QtWidgets.QLabel("Active Jobs: 0 / Total: 0")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        header_layout.addWidget(self.status_label)
        
        header_layout.addStretch()
        
        # Always on top checkbox
        self.always_on_top_check = QtWidgets.QCheckBox("Always On Top")
        self.always_on_top_check.setChecked(True)
        self.always_on_top_check.toggled.connect(self._toggle_always_on_top)
        header_layout.addWidget(self.always_on_top_check)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_table)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Process table
        self.process_table = QtWidgets.QTableWidget()
        self.process_table.setColumnCount(7)
        self.process_table.setHorizontalHeaderLabels([
            "Layer", "Frames", "GPU", "Status", "Progress", "Time", "Actions"
        ])
        self.process_table.horizontalHeader().setStretchLastSection(True)
        self.process_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.process_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.process_table.setAlternatingRowColors(True)
        self.process_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.process_table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Set column widths
        self.process_table.setColumnWidth(0, 150)  # Layer
        self.process_table.setColumnWidth(1, 100)  # Frames
        self.process_table.setColumnWidth(2, 60)   # GPU
        self.process_table.setColumnWidth(3, 100)  # Status
        self.process_table.setColumnWidth(4, 150)  # Progress
        self.process_table.setColumnWidth(5, 100)  # Time
        
        layout.addWidget(self.process_table)
        
        # Footer with controls
        footer_layout = QtWidgets.QHBoxLayout()
        footer_layout.setSpacing(8)
        
        self.auto_refresh_check = QtWidgets.QCheckBox("Auto Refresh")
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.toggled.connect(self._toggle_auto_refresh)
        footer_layout.addWidget(self.auto_refresh_check)
        
        footer_layout.addStretch()
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
    
    def _toggle_always_on_top(self, checked: bool) -> None:
        """Toggle always-on-top window flag."""
        if checked:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
        self.show()  # Need to show again after changing flags
    
    def _toggle_auto_refresh(self, checked: bool) -> None:
        """Toggle auto-refresh timer."""
        if checked:
            self._refresh_timer.start(1000)
        else:
            self._refresh_timer.stop()
    
    def _refresh_table(self) -> None:
        """Refresh process table from API."""
        processes = self._api.get_render_status()
        
        self.process_table.setRowCount(len(processes))
        
        # Update status label
        active_count = sum(1 for p in processes if p.status in [
            ProcessStatus.RENDERING, ProcessStatus.INITIALIZING, ProcessStatus.WAITING
        ])
        self.status_label.setText(f"Active Jobs: {active_count} / Total: {len(processes)}")
        
        for row, process in enumerate(processes):
            # Column 0: Layer
            layer_item = QtWidgets.QTableWidgetItem(process.layer_name)
            layer_item.setData(QtCore.Qt.UserRole, process.process_id)
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
            
            # Progress bar
            progress_widget = QtWidgets.QWidget()
            progress_layout = QtWidgets.QHBoxLayout(progress_widget)
            progress_layout.setContentsMargins(2, 2, 2, 2)
            
            progress_bar = QtWidgets.QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            progress_bar.setValue(int(process.progress))
            progress_bar.setFormat(progress_text)
            progress_bar.setTextVisible(True)
            progress_layout.addWidget(progress_bar)
            
            self.process_table.setCellWidget(row, 4, progress_widget)
            
            # Column 5: Time
            if process.start_time:
                elapsed = datetime.now() - process.start_time
                minutes = int(elapsed.total_seconds() / 60)
                seconds = int(elapsed.total_seconds() % 60)
                time_text = f"{minutes}m {seconds}s"
            else:
                time_text = "N/A"
            self.process_table.setItem(row, 5, QtWidgets.QTableWidgetItem(time_text))
            
            # Column 6: Actions (removed - use right-click menu or main window button)
            # Empty cell - actions available via right-click context menu
            self.process_table.setItem(row, 6, QtWidgets.QTableWidgetItem(""))
    
    def _show_context_menu(self, position) -> None:
        """Show context menu for process table."""
        row = self.process_table.rowAt(position.y())
        if row < 0:
            return
        
        process_id_item = self.process_table.item(row, 0)
        if not process_id_item:
            return
        
        process_id = process_id_item.data(QtCore.Qt.UserRole)
        if not process_id:
            return
        
        # Create context menu
        menu = QtWidgets.QMenu(self)
        
        view_logs_action = menu.addAction("View Logs")
        view_logs_action.triggered.connect(lambda: self._view_logs(process_id))
        
        menu.exec_(self.process_table.viewport().mapToGlobal(position))
    
    def _view_logs(self, process_id: str) -> None:
        """View logs for a process."""
        # Get process info
        processes = self._api.get_render_status()
        process = None
        for p in processes:
            if p.process_id == process_id:
                process = p
                break
        
        if not process:
            return
        
        # Show logs in message box
        log_text = "\n".join(process.log_messages[-50:])  # Last 50 lines
        
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(f"Logs: {process.layer_name}")
        msg_box.setText(f"Process: {process_id}\nLayer: {process.layer_name}")
        msg_box.setDetailedText(log_text)
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.exec_()
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self._refresh_timer.stop()
        super().closeEvent(event)

