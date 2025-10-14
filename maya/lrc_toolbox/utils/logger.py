"""
Logging System for LRC Toolbox

This module provides comprehensive logging functionality for directory access,
file operations, network performance, and error tracking.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional


class LRCLogger:
    """
    Centralized logging system for LRC Toolbox.
    
    Provides structured logging for different components with appropriate
    levels and formatting for development and production use.
    """
    
    _instance: Optional['LRCLogger'] = None
    _initialized = False
    
    def __new__(cls) -> 'LRCLogger':
        """Singleton pattern for logger."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logger if not already initialized."""
        if not self._initialized:
            self._setup_logging()
            LRCLogger._initialized = True
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f'lrc_toolbox_{timestamp}.log')
        
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Create component-specific loggers
        self.directory_logger = logging.getLogger('lrc.directory')
        self.file_ops_logger = logging.getLogger('lrc.file_ops')
        self.network_logger = logging.getLogger('lrc.network')
        self.ui_logger = logging.getLogger('lrc.ui')
        self.maya_logger = logging.getLogger('lrc.maya')
        
        self.directory_logger.info("Logging system initialized")
    
    def log_directory_access(self, path: str, operation: str, success: bool = True, 
                           error: Optional[str] = None, item_count: Optional[int] = None) -> None:
        """
        Log directory access operations.
        
        Args:
            path: Directory path being accessed
            operation: Type of operation (scan, check, create)
            success: Whether operation succeeded
            error: Error message if failed
            item_count: Number of items found (for scan operations)
        """
        if success:
            if item_count is not None:
                self.directory_logger.info(f"Directory {operation}: {path} - Found {item_count} items")
            else:
                self.directory_logger.info(f"Directory {operation}: {path} - Success")
        else:
            self.directory_logger.error(f"Directory {operation} failed: {path} - Error: {error}")
    
    def log_file_operation(self, operation: str, source: str, dest: Optional[str] = None,
                          success: bool = True, error: Optional[str] = None,
                          file_count: Optional[int] = None, progress: Optional[tuple] = None) -> None:
        """
        Log file operations.
        
        Args:
            operation: Type of operation (copy, move, delete, scan)
            source: Source file/directory path
            dest: Destination path (for copy/move operations)
            success: Whether operation succeeded
            error: Error message if failed
            file_count: Total number of files in operation
            progress: Tuple of (current, total) for progress tracking
        """
        if progress:
            current, total = progress
            self.file_ops_logger.debug(f"File {operation} progress: {current}/{total} - {os.path.basename(source)}")
        elif success:
            if file_count:
                self.file_ops_logger.info(f"Starting file {operation}: {file_count} files from {source}")
            elif dest:
                self.file_ops_logger.info(f"File {operation}: {source} -> {dest} - Success")
            else:
                self.file_ops_logger.info(f"File {operation}: {source} - Success")
        else:
            if dest:
                self.file_ops_logger.error(f"File {operation} failed: {source} -> {dest} - Error: {error}")
            else:
                self.file_ops_logger.error(f"File {operation} failed: {source} - Error: {error}")
    
    def log_network_performance(self, path: str, operation: str, duration: float,
                              warning_threshold: float = 2.0) -> None:
        """
        Log network performance for remote operations.
        
        Args:
            path: Network path being accessed
            operation: Type of operation
            duration: Time taken in seconds
            warning_threshold: Threshold for slow operation warning
        """
        duration_ms = duration * 1000
        
        if duration > warning_threshold:
            self.network_logger.warning(f"Slow {operation} detected: {path} took {duration:.2f}s")
        else:
            self.network_logger.debug(f"Network {operation} response time: {duration_ms:.0f}ms for {path}")
    
    def log_project_root_change(self, old_root: str, new_root: str, source: str = "user") -> None:
        """
        Log project root changes.
        
        Args:
            old_root: Previous project root
            new_root: New project root
            source: Source of change (user, maya_fallback, etc.)
        """
        self.directory_logger.info(f"Project root changed ({source}): {old_root} -> {new_root}")
    
    def log_maya_fallback(self, original_root: str, maya_workspace: str, reason: str) -> None:
        """
        Log Maya workspace fallback usage.
        
        Args:
            original_root: Original project root that failed
            maya_workspace: Maya workspace directory used as fallback
            reason: Reason for fallback
        """
        self.maya_logger.warning(f"Using Maya workspace fallback: {original_root} not accessible ({reason}), using {maya_workspace}")
    
    def log_ui_operation(self, widget: str, operation: str, details: str = "") -> None:
        """
        Log UI operations and user interactions.
        
        Args:
            widget: Widget name
            operation: Operation performed
            details: Additional details
        """
        if details:
            self.ui_logger.info(f"UI {widget}: {operation} - {details}")
        else:
            self.ui_logger.info(f"UI {widget}: {operation}")
    
    def log_error(self, component: str, error: Exception, context: str = "") -> None:
        """
        Log errors with full context.
        
        Args:
            component: Component where error occurred
            error: Exception object
            context: Additional context information
        """
        error_msg = f"{component} error"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        # Use appropriate logger based on component
        if 'directory' in component.lower():
            self.directory_logger.error(error_msg, exc_info=True)
        elif 'file' in component.lower():
            self.file_ops_logger.error(error_msg, exc_info=True)
        elif 'network' in component.lower():
            self.network_logger.error(error_msg, exc_info=True)
        elif 'ui' in component.lower():
            self.ui_logger.error(error_msg, exc_info=True)
        elif 'maya' in component.lower():
            self.maya_logger.error(error_msg, exc_info=True)
        else:
            logging.error(error_msg, exc_info=True)


# Global logger instance
logger = LRCLogger()
