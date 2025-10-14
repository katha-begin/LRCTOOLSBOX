"""
Error Handler System

Comprehensive error handling with graceful degradation, user-friendly messages,
and recovery mechanisms for the LRC Toolbox.
"""

import sys
import traceback
import functools
from typing import Optional, Callable, Any, Dict, List
from datetime import datetime
from pathlib import Path

try:
    from PySide2 import QtWidgets, QtCore
except ImportError:
    try:
        from PySide6 import QtWidgets, QtCore
    except ImportError:
        QtWidgets = None
        QtCore = None


class ErrorSeverity:
    """Error severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory:
    """Error categories for better classification."""
    FILE_OPERATION = "File Operation"
    MAYA_INTEGRATION = "Maya Integration"
    SETTINGS = "Settings"
    TEMPLATE_MANAGEMENT = "Template Management"
    NAVIGATION = "Navigation"
    UI = "User Interface"
    NETWORK = "Network"
    GENERAL = "General"


class ErrorRecord:
    """Individual error record."""

    def __init__(self,
                 message: str,
                 category: str = ErrorCategory.GENERAL,
                 severity: str = ErrorSeverity.ERROR,
                 exception: Optional[Exception] = None,
                 context: Optional[Dict[str, Any]] = None):
        """
        Initialize error record.

        Args:
            message: Error message
            category: Error category
            severity: Error severity level
            exception: Original exception if any
            context: Additional context information
        """
        self.timestamp = datetime.now()
        self.message = message
        self.category = category
        self.severity = severity
        self.exception = exception
        self.context = context or {}
        self.traceback_info = None

        if exception:
            self.traceback_info = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error record to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "category": self.category,
            "severity": self.severity,
            "exception_type": type(self.exception).__name__ if self.exception else None,
            "context": self.context,
            "traceback": self.traceback_info
        }

    def get_user_message(self) -> str:
        """Get user-friendly error message."""
        return f"[{self.category}] {self.message}"


class ErrorHandler:
    """
    Central error handler for the LRC Toolbox.

    Features:
    - Error logging and tracking
    - User-friendly error dialogs
    - Graceful degradation
    - Recovery suggestions
    - Error reporting
    """

    def __init__(self):
        """Initialize error handler."""
        self._errors: List[ErrorRecord] = []
        self._max_errors = 1000  # Maximum errors to keep in memory
        self._error_log_file = None
        self._maya_available = self._check_maya_availability()

        # Setup logging
        self._setup_error_logging()

        # Error recovery functions
        self._recovery_functions = {}
        self._register_default_recovery_functions()

    def _check_maya_availability(self) -> bool:
        """Check if Maya is available."""
        try:
            import maya.cmds as cmds
            return True
        except ImportError:
            return False

    def _setup_error_logging(self) -> None:
        """Setup error logging to file."""
        try:
            log_dir = Path.home() / ".lrc_toolbox" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

            self._error_log_file = log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"

        except Exception as e:
            print(f"Failed to setup error logging: {e}")

    def _register_default_recovery_functions(self) -> None:
        """Register default recovery functions."""
        self._recovery_functions.update({
            ErrorCategory.FILE_OPERATION: self._recover_file_operation,
            ErrorCategory.MAYA_INTEGRATION: self._recover_maya_integration,
            ErrorCategory.SETTINGS: self._recover_settings,
            ErrorCategory.TEMPLATE_MANAGEMENT: self._recover_template_management,
            ErrorCategory.NAVIGATION: self._recover_navigation
        })

    def handle_error(self,
                    message: str,
                    category: str = ErrorCategory.GENERAL,
                    severity: str = ErrorSeverity.ERROR,
                    exception: Optional[Exception] = None,
                    context: Optional[Dict[str, Any]] = None,
                    show_dialog: bool = True,
                    attempt_recovery: bool = True) -> bool:
        """
        Handle an error with comprehensive processing.

        Args:
            message: Error message
            category: Error category
            severity: Error severity
            exception: Original exception
            context: Additional context
            show_dialog: Whether to show error dialog
            attempt_recovery: Whether to attempt automatic recovery

        Returns:
            True if error was handled successfully, False otherwise
        """
        # Create error record
        error_record = ErrorRecord(message, category, severity, exception, context)

        # Add to error list
        self._errors.append(error_record)

        # Trim error list if needed
        if len(self._errors) > self._max_errors:
            self._errors = self._errors[-self._max_errors:]

        # Log error
        self._log_error(error_record)

        # Print to console
        print(f"[{severity}] {error_record.get_user_message()}")
        if error_record.traceback_info and severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            print(error_record.traceback_info)

        # Attempt recovery
        recovery_successful = False
        if attempt_recovery and category in self._recovery_functions:
            try:
                recovery_successful = self._recovery_functions[category](error_record)
                if recovery_successful:
                    print(f"Recovery successful for {category} error")
            except Exception as recovery_error:
                print(f"Recovery failed: {recovery_error}")

        # Show user dialog
        if show_dialog and QtWidgets:
            self._show_error_dialog(error_record, recovery_successful)

        return recovery_successful

    def _log_error(self, error_record: ErrorRecord) -> None:
        """Log error to file."""
        if not self._error_log_file:
            return

        try:
            log_entry = (
                f"[{error_record.timestamp.isoformat()}] "
                f"[{error_record.severity}] "
                f"[{error_record.category}] "
                f"{error_record.message}\n"
            )

            if error_record.context:
                log_entry += f"Context: {error_record.context}\n"

            if error_record.traceback_info:
                log_entry += f"Traceback:\n{error_record.traceback_info}\n"

            log_entry += "-" * 80 + "\n"

            with open(self._error_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)

        except Exception as e:
            print(f"Failed to log error: {e}")

    def _show_error_dialog(self, error_record: ErrorRecord, recovery_attempted: bool = False) -> None:
        """Show user-friendly error dialog."""
        try:
            if error_record.severity == ErrorSeverity.INFO:
                QtWidgets.QMessageBox.information(
                    None, "Information", error_record.get_user_message()
                )
            elif error_record.severity == ErrorSeverity.WARNING:
                QtWidgets.QMessageBox.warning(
                    None, "Warning", error_record.get_user_message()
                )
            else:
                # Error or Critical
                dialog_text = error_record.get_user_message()

                if recovery_attempted:
                    dialog_text += "\n\nAutomatic recovery was attempted."

                # Add suggestions based on category
                suggestions = self._get_error_suggestions(error_record.category)
                if suggestions:
                    dialog_text += f"\n\nSuggested actions:\n{suggestions}"

                if error_record.severity == ErrorSeverity.CRITICAL:
                    QtWidgets.QMessageBox.critical(None, "Critical Error", dialog_text)
                else:
                    QtWidgets.QMessageBox.warning(None, "Error", dialog_text)

        except Exception as e:
            print(f"Failed to show error dialog: {e}")

    def _get_error_suggestions(self, category: str) -> str:
        """Get error suggestions based on category."""
        suggestions = {
            ErrorCategory.FILE_OPERATION: (
                "• Check file permissions and disk space\n"
                "• Verify the file path exists\n"
                "• Try using a different file location"
            ),
            ErrorCategory.MAYA_INTEGRATION: (
                "• Ensure Maya is running\n"
                "• Check if the Maya plugin is loaded\n"
                "• Try restarting Maya"
            ),
            ErrorCategory.SETTINGS: (
                "• Try resetting settings to defaults\n"
                "• Check if settings file is writable\n"
                "• Verify configuration paths"
            ),
            ErrorCategory.TEMPLATE_MANAGEMENT: (
                "• Check template directory permissions\n"
                "• Verify template file format\n"
                "• Try refreshing the template browser"
            ),
            ErrorCategory.NAVIGATION: (
                "• Refresh the project structure\n"
                "• Check project root directory\n"
                "• Verify navigation context"
            )
        }

        return suggestions.get(category, "• Try restarting the application\n• Check the error log for details")

    # Recovery Functions
    def _recover_file_operation(self, error_record: ErrorRecord) -> bool:
        """Attempt to recover from file operation errors."""
        try:
            context = error_record.context
            if not context:
                return False

            file_path = context.get("file_path")
            operation = context.get("operation")

            if not file_path or not operation:
                return False

            # Try creating parent directory if it doesn't exist
            if operation in ["write", "save"] and file_path:
                parent_dir = Path(file_path).parent
                if not parent_dir.exists():
                    parent_dir.mkdir(parents=True, exist_ok=True)
                    print(f"Created missing directory: {parent_dir}")
                    return True

            # Try alternative file path
            if operation in ["read", "open"] and file_path:
                # Could implement fallback file locations here
                pass

            return False

        except Exception as e:
            print(f"File operation recovery failed: {e}")
            return False

    def _recover_maya_integration(self, error_record: ErrorRecord) -> bool:
        """Attempt to recover from Maya integration errors."""
        try:
            if not self._maya_available:
                # Try to check Maya availability again
                self._maya_available = self._check_maya_availability()
                return self._maya_available

            # Could implement Maya state recovery here
            return False

        except Exception as e:
            print(f"Maya integration recovery failed: {e}")
            return False

    def _recover_settings(self, error_record: ErrorRecord) -> bool:
        """Attempt to recover from settings errors."""
        try:
            # Try to reload settings from defaults
            from ..config.defaults import DEFAULT_SETTINGS
            from ..config.settings import settings

            # Reset problematic settings key if specified
            context = error_record.context
            if context and "settings_key" in context:
                key = context["settings_key"]
                default_value = self._get_nested_default(DEFAULT_SETTINGS, key)
                if default_value is not None:
                    settings.set(key, default_value)
                    print(f"Reset settings key '{key}' to default")
                    return True

            return False

        except Exception as e:
            print(f"Settings recovery failed: {e}")
            return False

    def _recover_template_management(self, error_record: ErrorRecord) -> bool:
        """Attempt to recover from template management errors."""
        try:
            # Could implement template cache clearing, directory recreation, etc.
            return False

        except Exception as e:
            print(f"Template management recovery failed: {e}")
            return False

    def _recover_navigation(self, error_record: ErrorRecord) -> bool:
        """Attempt to recover from navigation errors."""
        try:
            # Could implement project structure refresh, context reset, etc.
            return False

        except Exception as e:
            print(f"Navigation recovery failed: {e}")
            return False

    def _get_nested_default(self, defaults: Dict[str, Any], key: str) -> Any:
        """Get nested default value from key path."""
        try:
            keys = key.split(".")
            value = defaults
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return None

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics."""
        if not self._errors:
            return {"total_errors": 0}

        summary = {
            "total_errors": len(self._errors),
            "by_severity": {},
            "by_category": {},
            "recent_errors": []
        }

        # Count by severity and category
        for error in self._errors:
            summary["by_severity"][error.severity] = summary["by_severity"].get(error.severity, 0) + 1
            summary["by_category"][error.category] = summary["by_category"].get(error.category, 0) + 1

        # Recent errors (last 10)
        recent_errors = self._errors[-10:]
        summary["recent_errors"] = [
            {
                "timestamp": error.timestamp.isoformat(),
                "message": error.message,
                "category": error.category,
                "severity": error.severity
            }
            for error in recent_errors
        ]

        return summary

    def clear_errors(self) -> None:
        """Clear all error records."""
        self._errors.clear()
        print("Error records cleared")

    def export_error_log(self, file_path: str) -> bool:
        """Export error log to file."""
        try:
            import json

            error_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_errors": len(self._errors),
                "errors": [error.to_dict() for error in self._errors]
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False)

            print(f"Error log exported to: {file_path}")
            return True

        except Exception as e:
            print(f"Failed to export error log: {e}")
            return False


def error_handler_decorator(category: str = ErrorCategory.GENERAL,
                           severity: str = ErrorSeverity.ERROR,
                           show_dialog: bool = True,
                           attempt_recovery: bool = True,
                           fallback_return=None):
    """
    Decorator for automatic error handling.

    Args:
        category: Error category
        severity: Error severity
        show_dialog: Whether to show error dialog
        attempt_recovery: Whether to attempt recovery
        fallback_return: Value to return on error
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:200],  # Limit args length
                    "kwargs": str(kwargs)[:200]
                }

                error_handler.handle_error(
                    message=f"Error in {func.__name__}: {str(e)}",
                    category=category,
                    severity=severity,
                    exception=e,
                    context=context,
                    show_dialog=show_dialog,
                    attempt_recovery=attempt_recovery
                )

                return fallback_return
        return wrapper
    return decorator


# Global error handler instance
error_handler = ErrorHandler()


# Convenience functions
def handle_file_error(message: str, file_path: str = None, operation: str = None, exception: Exception = None):
    """Handle file operation errors."""
    context = {}
    if file_path:
        context["file_path"] = file_path
    if operation:
        context["operation"] = operation

    error_handler.handle_error(
        message=message,
        category=ErrorCategory.FILE_OPERATION,
        exception=exception,
        context=context
    )


def handle_maya_error(message: str, maya_command: str = None, exception: Exception = None):
    """Handle Maya integration errors."""
    context = {}
    if maya_command:
        context["maya_command"] = maya_command

    error_handler.handle_error(
        message=message,
        category=ErrorCategory.MAYA_INTEGRATION,
        exception=exception,
        context=context
    )


def handle_settings_error(message: str, settings_key: str = None, exception: Exception = None):
    """Handle settings errors."""
    context = {}
    if settings_key:
        context["settings_key"] = settings_key

    error_handler.handle_error(
        message=message,
        category=ErrorCategory.SETTINGS,
        exception=exception,
        context=context
    )


def handle_ui_error(message: str, widget_name: str = None, exception: Exception = None):
    """Handle UI errors."""
    context = {}
    if widget_name:
        context["widget_name"] = widget_name

    error_handler.handle_error(
        message=message,
        category=ErrorCategory.UI,
        exception=exception,
        context=context,
        severity=ErrorSeverity.WARNING  # UI errors are usually not critical
    )