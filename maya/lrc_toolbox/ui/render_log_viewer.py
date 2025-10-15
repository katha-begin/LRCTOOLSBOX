# -*- coding: utf-8 -*-
"""
Render Log Viewer Dialog

Popup window for viewing render logs without spamming script editor.
"""

from PySide2 import QtWidgets, QtCore, QtGui


class RenderLogViewer(QtWidgets.QDialog):
    """
    Dialog for viewing render logs.
    
    Features:
    - Real-time log updates
    - Auto-scroll to bottom
    - Copy to clipboard
    - Save to file
    - Clear logs
    - Filter by process
    """
    
    def __init__(self, parent=None):
        """Initialize log viewer dialog."""
        super(RenderLogViewer, self).__init__(parent)
        
        self.setWindowTitle("Batch Render Logs")
        self.setMinimumSize(800, 600)
        
        # Store logs per process
        self._process_logs = {}  # {process_id: [log_lines]}
        self._current_process = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Top toolbar
        toolbar_layout = QtWidgets.QHBoxLayout()
        
        # Process selector
        toolbar_layout.addWidget(QtWidgets.QLabel("Process:"))
        self.process_combo = QtWidgets.QComboBox()
        self.process_combo.setMinimumWidth(200)
        toolbar_layout.addWidget(self.process_combo)
        
        toolbar_layout.addStretch()
        
        # Auto-scroll checkbox
        self.auto_scroll_check = QtWidgets.QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        toolbar_layout.addWidget(self.auto_scroll_check)
        
        # Clear button
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.setMaximumWidth(80)
        toolbar_layout.addWidget(self.clear_btn)
        
        # Copy button
        self.copy_btn = QtWidgets.QPushButton("Copy All")
        self.copy_btn.setMaximumWidth(80)
        toolbar_layout.addWidget(self.copy_btn)
        
        # Save button
        self.save_btn = QtWidgets.QPushButton("Save...")
        self.save_btn.setMaximumWidth(80)
        toolbar_layout.addWidget(self.save_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Log text area
        self.log_text = QtWidgets.QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        
        # Use monospace font
        font = QtGui.QFont("Courier New", 9)
        self.log_text.setFont(font)
        
        layout.addWidget(self.log_text)
        
        # Bottom status bar
        status_layout = QtWidgets.QHBoxLayout()
        
        self.status_label = QtWidgets.QLabel("No logs")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.setMaximumWidth(80)
        status_layout.addWidget(self.close_btn)
        
        layout.addLayout(status_layout)
    
    def _connect_signals(self):
        """Connect UI signals."""
        self.process_combo.currentTextChanged.connect(self._on_process_changed)
        self.clear_btn.clicked.connect(self._on_clear)
        self.copy_btn.clicked.connect(self._on_copy)
        self.save_btn.clicked.connect(self._on_save)
        self.close_btn.clicked.connect(self.close)
    
    def add_process(self, process_id: str, display_name: str = None):
        """
        Add a new process to the log viewer.
        
        Args:
            process_id: Process ID
            display_name: Display name for combo box (optional)
        """
        if process_id not in self._process_logs:
            self._process_logs[process_id] = []
            
            # Add to combo box
            display = display_name or process_id
            self.process_combo.addItem(display, process_id)
            
            # Select if first process
            if self.process_combo.count() == 1:
                self._current_process = process_id
                self._update_display()
    
    def add_log(self, process_id: str, message: str):
        """
        Add log message for a process.
        
        Args:
            process_id: Process ID
            message: Log message
        """
        if process_id not in self._process_logs:
            self.add_process(process_id)
        
        # Store log
        self._process_logs[process_id].append(message)
        
        # Update display if this is the current process
        if process_id == self._current_process:
            self.log_text.appendPlainText(message)
            
            # Auto-scroll to bottom
            if self.auto_scroll_check.isChecked():
                scrollbar = self.log_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            
            # Update status
            total_lines = len(self._process_logs[process_id])
            self.status_label.setText(f"{total_lines} lines")
    
    def add_completion_message(self, process_id: str, success: bool, output_path: str = None):
        """
        Add completion message with output path.
        
        Args:
            process_id: Process ID
            success: Whether render succeeded
            output_path: Path to rendered images
        """
        separator = "=" * 80
        
        if success:
            message = f"\n{separator}\n"
            message += "✅ RENDER COMPLETED SUCCESSFULLY\n"
            message += f"{separator}\n"
            if output_path:
                message += f"Output: {output_path}\n"
                message += f"{separator}\n"
        else:
            message = f"\n{separator}\n"
            message += "❌ RENDER FAILED\n"
            message += f"{separator}\n"
        
        self.add_log(process_id, message)
    
    def _on_process_changed(self, text: str):
        """Handle process selection change."""
        index = self.process_combo.currentIndex()
        if index >= 0:
            process_id = self.process_combo.itemData(index)
            self._current_process = process_id
            self._update_display()
    
    def _update_display(self):
        """Update log display for current process."""
        self.log_text.clear()
        
        if self._current_process and self._current_process in self._process_logs:
            logs = self._process_logs[self._current_process]
            self.log_text.setPlainText("\n".join(logs))
            
            # Update status
            self.status_label.setText(f"{len(logs)} lines")
            
            # Scroll to bottom
            if self.auto_scroll_check.isChecked():
                scrollbar = self.log_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
        else:
            self.status_label.setText("No logs")
    
    def _on_clear(self):
        """Clear logs for current process."""
        if self._current_process:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Clear Logs",
                f"Clear all logs for {self._current_process}?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                self._process_logs[self._current_process] = []
                self._update_display()
    
    def _on_copy(self):
        """Copy all logs to clipboard."""
        if self._current_process and self._current_process in self._process_logs:
            logs = "\n".join(self._process_logs[self._current_process])
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(logs)
            
            QtWidgets.QMessageBox.information(
                self,
                "Copied",
                "Logs copied to clipboard"
            )
    
    def _on_save(self):
        """Save logs to file."""
        if not self._current_process or self._current_process not in self._process_logs:
            return
        
        # Get save path
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Logs",
            f"{self._current_process}_log.txt",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            try:
                logs = "\n".join(self._process_logs[self._current_process])
                with open(file_path, 'w') as f:
                    f.write(logs)
                
                QtWidgets.QMessageBox.information(
                    self,
                    "Saved",
                    f"Logs saved to:\n{file_path}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save logs:\n{e}"
                )
    
    def clear_all(self):
        """Clear all logs for all processes."""
        self._process_logs.clear()
        self.process_combo.clear()
        self._current_process = None
        self._update_display()

