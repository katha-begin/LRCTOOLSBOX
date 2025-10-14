# -*- coding: utf-8 -*-
"""
Batch Render Default Configuration

Default settings for batch render manager including GPU allocation,
process limits, and file management settings.
"""

from typing import Dict, Any

# Default batch render settings
DEFAULT_BATCH_RENDER_SETTINGS = {
    "gpu_allocation": {
        "reserve_for_maya": 1,  # Number of GPUs to reserve for Maya session
        "default_batch_gpu": 1,  # Default GPU ID for batch rendering (0-indexed)
        "auto_detect": True,  # Auto-detect available GPUs
    },
    "cpu_allocation": {
        "reserve_for_maya": 4,  # Number of CPU cores to reserve for Maya
        "default_batch_threads": 4,  # Default CPU threads for batch rendering
        "auto_detect": True,  # Auto-detect available CPU cores
    },
    "process_management": {
        "max_concurrent_processes": 4,  # Maximum concurrent render processes
        "process_timeout": 3600,  # Process timeout in seconds (1 hour)
        "auto_restart_on_failure": False,  # Auto-restart failed processes
    },
    "file_management": {
        "temp_directory": "./temp",  # Temporary file directory
        "temp_file_pattern": "render_{scene}_{timestamp}_{layer}_{pid}.ma",
        "cleanup_on_exit": True,  # Cleanup temp files on exit
        "keep_latest_files": 5,  # Number of latest temp files to keep
        "auto_cleanup_age_hours": 24,  # Auto-cleanup files older than N hours
    },
    "render_execution": {
        "default_method": "auto",  # auto, mayapy_custom, render_exe, mayapy_basic
        "fallback_enabled": True,  # Enable automatic fallback
        "renderer": "redshift",  # Default renderer
        "use_render_layers": True,  # Use render layers
    },
    "frame_range": {
        "default_range": "1-24",  # Default frame range
        "default_step": 1,  # Default frame step
        "always_include_first_last": True,  # Always include first/last frames with steps
    },
    "logging": {
        "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
        "log_to_file": True,  # Save logs to file
        "log_directory": "./logs",  # Log file directory
        "max_log_lines": 10000,  # Maximum log lines to keep in memory
    },
    "ui_preferences": {
        "auto_refresh_interval": 2000,  # UI refresh interval in milliseconds
        "show_system_info": True,  # Show system info panel
        "show_progress_bars": True,  # Show progress bars in table
        "log_font_size": 9,  # Log display font size
    },
}


def get_batch_render_defaults() -> Dict[str, Any]:
    """
    Get default batch render settings.
    
    Returns:
        Dictionary containing default batch render settings
    """
    return DEFAULT_BATCH_RENDER_SETTINGS.copy()


def get_gpu_defaults() -> Dict[str, Any]:
    """
    Get default GPU allocation settings.
    
    Returns:
        Dictionary containing GPU allocation defaults
    """
    return DEFAULT_BATCH_RENDER_SETTINGS["gpu_allocation"].copy()


def get_cpu_defaults() -> Dict[str, Any]:
    """
    Get default CPU allocation settings.
    
    Returns:
        Dictionary containing CPU allocation defaults
    """
    return DEFAULT_BATCH_RENDER_SETTINGS["cpu_allocation"].copy()


def get_process_defaults() -> Dict[str, Any]:
    """
    Get default process management settings.
    
    Returns:
        Dictionary containing process management defaults
    """
    return DEFAULT_BATCH_RENDER_SETTINGS["process_management"].copy()


def get_file_management_defaults() -> Dict[str, Any]:
    """
    Get default file management settings.
    
    Returns:
        Dictionary containing file management defaults
    """
    return DEFAULT_BATCH_RENDER_SETTINGS["file_management"].copy()

