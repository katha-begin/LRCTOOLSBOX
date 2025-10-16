"""
Error Monitor Widget

Provides real-time error monitoring and debugging capabilities for the LRC Toolbox.
"""

from typing import Optional, Dict, Any
import json

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

from ...utils.error_handler import error_handler, ErrorSeverity, ErrorCategory


class ErrorMonitorWidget(QtWidgets.QWidget):
    """
    Error Monitor widget for real-time error tracking and debugging.

    Features:
    - Real-time error display
    - Error filtering and search
    - Error export functionality
    - Error statistics
    """

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the Error Monitor widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._setup_ui()
        self._connect_signals()
        self._setup_refresh_timer()
        self._refresh_errors()

        print("Error Monitor Widget initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header with title and controls
        self._create_header()
        layout.addWidget(self.header_widget)

        # Error statistics
        self._create_statistics()
        layout.addWidget(self.stats_widget)

        # Error list
        self._create_error_list()
        layout.addWidget(self.error_list)

        # Footer with actions
        self._create_footer()
        layout.addWidget(self.footer_widget)

    def _create_header(self) -> None:
        """Create header with title and controls."""
        self.header_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(self.header_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title_label = QtWidgets.QLabel("Error Monitor")
        title_font = QtGui.QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        layout.addStretch()

        # Auto-refresh checkbox
        self.auto_refresh_check = QtWidgets.QCheckBox("Auto-refresh")
        self.auto_refresh_check.setChecked(True)
        layout.addWidget(self.auto_refresh_check)

        # Refresh button
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.setMaximumWidth(80)
        layout.addWidget(self.refresh_btn)

    def _create_statistics(self) -> None:
        """Create error statistics display."""
        self.stats_widget = QtWidgets.QGroupBox("Error Statistics")
        layout = QtWidgets.QGridLayout(self.stats_widget)

        # Total errors
        layout.addWidget(QtWidgets.QLabel("Total Errors:"), 0, 0)
        self.total_errors_label = QtWidgets.QLabel("0")
        self.total_errors_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.total_errors_label, 0, 1)

        # By severity
        layout.addWidget(QtWidgets.QLabel("Critical:"), 0, 2)
        self.critical_label = QtWidgets.QLabel("0")
        self.critical_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.critical_label, 0, 3)

        layout.addWidget(QtWidgets.QLabel("Errors:"), 0, 4)
        self.errors_label = QtWidgets.QLabel("0")
        self.errors_label.setStyleSheet("color: orange; font-weight: bold;")
        layout.addWidget(self.errors_label, 0, 5)

        layout.addWidget(QtWidgets.QLabel("Warnings:"), 1, 0)
        self.warnings_label = QtWidgets.QLabel("0")
        self.warnings_label.setStyleSheet("color: #DAA520; font-weight: bold;")
        layout.addWidget(self.warnings_label, 1, 1)

        layout.addWidget(QtWidgets.QLabel("Info:"), 1, 2)
        self.info_label = QtWidgets.QLabel("0")
        self.info_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.info_label, 1, 3)

        # Add stretch
        layout.setColumnStretch(6, 1)

    def _create_error_list(self) -> None:
        """Create error list display."""
        # Filter controls
        filter_widget = QtWidgets.QWidget()
        filter_layout = QtWidgets.QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        filter_layout.addWidget(QtWidgets.QLabel("Filter:"))

        # Severity filter
        self.severity_filter = QtWidgets.QComboBox()
        self.severity_filter.addItems([
            "All",
            ErrorSeverity.CRITICAL,
            ErrorSeverity.ERROR,
            ErrorSeverity.WARNING,
            ErrorSeverity.INFO
        ])
        filter_layout.addWidget(self.severity_filter)

        # Category filter
        self.category_filter = QtWidgets.QComboBox()
        self.category_filter.addItems([
            "All Categories",
            ErrorCategory.FILE_OPERATION,
            ErrorCategory.MAYA_INTEGRATION,
            ErrorCategory.SETTINGS,
            ErrorCategory.TEMPLATE_MANAGEMENT,
            ErrorCategory.NAVIGATION,
            ErrorCategory.UI,
            ErrorCategory.GENERAL
        ])
        filter_layout.addWidget(self.category_filter)

        filter_layout.addStretch()

        # Search box
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Search errors...")
        self.search_edit.setMaximumWidth(200)
        filter_layout.addWidget(self.search_edit)

        # Error list table
        self.error_table = QtWidgets.QTableWidget()
        self.error_table.setColumnCount(5)
        self.error_table.setHorizontalHeaderLabels([
            "Time", "Severity", "Category", "Message", "Details"
        ])

        # Set column widths
        header = self.error_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 80)   # Time
        header.resizeSection(1, 70)   # Severity
        header.resizeSection(2, 120)  # Category
        header.resizeSection(3, 300)  # Message

        self.error_table.setAlternatingRowColors(True)
        self.error_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.error_table.setSortingEnabled(True)

        # Add to main layout
        error_list_layout = QtWidgets.QVBoxLayout()
        error_list_layout.addWidget(filter_widget)
        error_list_layout.addWidget(self.error_table)

        self.error_list = QtWidgets.QWidget()
        self.error_list.setLayout(error_list_layout)

    def _create_footer(self) -> None:
        """Create footer with action buttons."""
        self.footer_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(self.footer_widget)
        layout.setContentsMargins(0, 4, 0, 0)

        # Clear errors button
        self.clear_btn = QtWidgets.QPushButton("Clear All")
        self.clear_btn.setStyleSheet("QPushButton { color: red; }")
        layout.addWidget(self.clear_btn)

        layout.addStretch()

        # Export button
        self.export_btn = QtWidgets.QPushButton("Export Log...")
        layout.addWidget(self.export_btn)

        # Details button
        self.details_btn = QtWidgets.QPushButton("View Details")
        self.details_btn.setEnabled(False)
        layout.addWidget(self.details_btn)

    def _connect_signals(self) -> None:
        """Connect UI signals to handlers."""
        self.refresh_btn.clicked.connect(self._refresh_errors)
        self.clear_btn.clicked.connect(self._clear_errors)
        self.export_btn.clicked.connect(self._export_errors)
        self.details_btn.clicked.connect(self._view_error_details)

        # Filter signals
        self.severity_filter.currentTextChanged.connect(self._apply_filters)
        self.category_filter.currentTextChanged.connect(self._apply_filters)
        self.search_edit.textChanged.connect(self._apply_filters)

        # Selection signals
        self.error_table.itemSelectionChanged.connect(self._on_selection_changed)

        # Auto-refresh
        self.auto_refresh_check.toggled.connect(self._toggle_auto_refresh)

    def _setup_refresh_timer(self) -> None:
        """Setup auto-refresh timer."""
        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.timeout.connect(self._refresh_errors)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def _refresh_errors(self) -> None:
        """Refresh error display."""
        try:
            # Get error summary
            summary = error_handler.get_error_summary()

            # Update statistics
            self._update_statistics(summary)

            # Update error table
            self._update_error_table(summary)

        except Exception as e:
            print(f"Error refreshing error monitor: {e}")

    def _update_statistics(self, summary: Dict[str, Any]) -> None:
        """Update error statistics display."""
        total_errors = summary.get("total_errors", 0)
        self.total_errors_label.setText(str(total_errors))

        by_severity = summary.get("by_severity", {})
        self.critical_label.setText(str(by_severity.get(ErrorSeverity.CRITICAL, 0)))
        self.errors_label.setText(str(by_severity.get(ErrorSeverity.ERROR, 0)))
        self.warnings_label.setText(str(by_severity.get(ErrorSeverity.WARNING, 0)))
        self.info_label.setText(str(by_severity.get(ErrorSeverity.INFO, 0)))

    def _update_error_table(self, summary: Dict[str, Any]) -> None:
        """Update error table with recent errors."""
        recent_errors = summary.get("recent_errors", [])

        self.error_table.setRowCount(len(recent_errors))

        for row, error in enumerate(recent_errors):
            # Time
            timestamp = error.get("timestamp", "")
            time_str = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp
            self.error_table.setItem(row, 0, QtWidgets.QTableWidgetItem(time_str))

            # Severity
            severity = error.get("severity", "")
            severity_item = QtWidgets.QTableWidgetItem(severity)

            # Color code by severity
            if severity == ErrorSeverity.CRITICAL:
                severity_item.setBackground(QtGui.QColor("#FFCDD2"))  # Light red
            elif severity == ErrorSeverity.ERROR:
                severity_item.setBackground(QtGui.QColor("#FFE0B2"))  # Light orange
            elif severity == ErrorSeverity.WARNING:
                severity_item.setBackground(QtGui.QColor("#FFF9C4"))  # Light yellow
            else:
                severity_item.setBackground(QtGui.QColor("#E3F2FD"))  # Light blue

            self.error_table.setItem(row, 1, severity_item)

            # Category
            category = error.get("category", "")
            self.error_table.setItem(row, 2, QtWidgets.QTableWidgetItem(category))

            # Message
            message = error.get("message", "")
            if len(message) > 100:
                message = message[:97] + "..."
            self.error_table.setItem(row, 3, QtWidgets.QTableWidgetItem(message))

            # Details indicator
            has_details = bool(error.get("context") or error.get("traceback"))
            details_item = QtWidgets.QTableWidgetItem("Yes" if has_details else "No")
            self.error_table.setItem(row, 4, details_item)

        # Apply current filters
        self._apply_filters()

    def _apply_filters(self) -> None:
        """Apply current filters to the error table."""
        severity_filter = self.severity_filter.currentText()
        category_filter = self.category_filter.currentText()
        search_text = self.search_edit.text().lower()

        for row in range(self.error_table.rowCount()):
            show_row = True

            # Severity filter
            if severity_filter != "All":
                severity_item = self.error_table.item(row, 1)
                if severity_item and severity_item.text() != severity_filter:
                    show_row = False

            # Category filter
            if category_filter != "All Categories":
                category_item = self.error_table.item(row, 2)
                if category_item and category_item.text() != category_filter:
                    show_row = False

            # Search filter
            if search_text:
                message_item = self.error_table.item(row, 3)
                if message_item and search_text not in message_item.text().lower():
                    show_row = False

            self.error_table.setRowHidden(row, not show_row)

    def _clear_errors(self) -> None:
        """Clear all errors."""
        reply = QtWidgets.QMessageBox.question(
            self, "Clear Errors",
            "Are you sure you want to clear all error records?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            error_handler.clear_errors()
            self._refresh_errors()

    def _export_errors(self) -> None:
        """Export error log to file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Error Log",
            f"lrc_toolbox_errors_{QtCore.QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            if error_handler.export_error_log(file_path):
                QtWidgets.QMessageBox.information(
                    self, "Export Complete",
                    f"Error log exported successfully to:\n{file_path}"
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Export Failed",
                    "Failed to export error log."
                )

    def _view_error_details(self) -> None:
        """View details of selected error."""
        current_row = self.error_table.currentRow()
        if current_row < 0:
            return

        # Get error summary to find the error
        summary = error_handler.get_error_summary()
        recent_errors = summary.get("recent_errors", [])

        if current_row < len(recent_errors):
            error = recent_errors[current_row]
            self._show_error_details_dialog(error)

    def _show_error_details_dialog(self, error: Dict[str, Any]) -> None:
        """Show error details in a dialog."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Error Details")
        dialog.setModal(True)
        dialog.resize(600, 400)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Error information
        info_text = f"""
<b>Timestamp:</b> {error.get('timestamp', 'Unknown')}<br>
<b>Severity:</b> {error.get('severity', 'Unknown')}<br>
<b>Category:</b> {error.get('category', 'Unknown')}<br>
<b>Exception Type:</b> {error.get('exception_type', 'None')}<br>
<br>
<b>Message:</b><br>
{error.get('message', 'No message')}
        """

        info_label = QtWidgets.QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Context information
        if error.get('context'):
            layout.addWidget(QtWidgets.QLabel("<b>Context:</b>"))
            context_text = QtWidgets.QTextEdit()
            context_text.setMaximumHeight(100)
            context_text.setPlainText(json.dumps(error['context'], indent=2))
            context_text.setReadOnly(True)
            layout.addWidget(context_text)

        # Traceback information
        if error.get('traceback'):
            layout.addWidget(QtWidgets.QLabel("<b>Traceback:</b>"))
            traceback_text = QtWidgets.QTextEdit()
            traceback_text.setPlainText(error['traceback'])
            traceback_text.setReadOnly(True)
            layout.addWidget(traceback_text)

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec_()

    def _on_selection_changed(self) -> None:
        """Handle selection change in error table."""
        has_selection = len(self.error_table.selectedItems()) > 0
        self.details_btn.setEnabled(has_selection)

    def _toggle_auto_refresh(self, enabled: bool) -> None:
        """Toggle auto-refresh timer."""
        if enabled:
            self.refresh_timer.start()
        else:
            self.refresh_timer.stop()

    def closeEvent(self, event) -> None:
        """Handle widget close event."""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().closeEvent(event)