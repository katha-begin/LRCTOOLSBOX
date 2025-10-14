# -*- coding: utf-8 -*-
"""
Batch Render API

Main orchestration API for batch rendering operations with automatic fallback system.
Provides unified interface for UI and CLI access to batch rendering functionality.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from PySide2 import QtCore
    Signal = QtCore.Signal
    QObject = QtCore.QObject
except ImportError:
    # Fallback for non-Qt environments
    class QObject:
        pass
    def Signal(*args):
        return None

from .models import (
    RenderConfig, RenderProcess, SystemInfo, ProcessStatus,
    RenderMethod, RenderMode, GPUInfo
)
from ..config.batch_render_defaults import get_batch_render_defaults


class BatchRenderAPI(QObject):
    """
    Main API for batch rendering operations.
    
    Provides unified interface for:
    - Starting and stopping batch renders
    - Monitoring render progress
    - Managing render processes
    - System resource detection
    - Automatic fallback handling
    
    Signals:
        render_started: Emitted when render process starts (process_id: str)
        render_progress: Emitted on progress update (process_id: str, progress: float)
        render_completed: Emitted when render completes (process_id: str, success: bool)
        render_log: Emitted for log messages (process_id: str, message: str)
        system_info_updated: Emitted when system info changes (info: SystemInfo)
    """
    
    # Signals for UI communication (only if Qt available)
    if Signal is not None:
        render_started = Signal(str)  # process_id
        render_progress = Signal(str, float)  # process_id, progress
        render_completed = Signal(str, bool)  # process_id, success
        render_log = Signal(str, str)  # process_id, message
        system_info_updated = Signal(object)  # SystemInfo
    
    def __init__(self):
        """Initialize Batch Render API."""
        if QObject != object:
            super().__init__()
        
        self._settings = get_batch_render_defaults()
        self._processes: Dict[str, RenderProcess] = {}
        self._system_info: Optional[SystemInfo] = None
        self._initialized = False
        
        # Lazy-loaded managers (will be initialized when needed)
        self._system_detector = None
        self._execution_manager = None
        self._process_manager = None
    
    def initialize(self) -> bool:
        """
        Initialize the batch render system.
        
        Detects system resources and prepares for rendering.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
        
        try:
            # Detect system resources
            self._system_info = self._detect_system_resources()
            
            if hasattr(self, 'system_info_updated'):
                self.system_info_updated.emit(self._system_info)
            
            self._initialized = True
            print("[BatchRenderAPI] Initialized successfully")
            return True
            
        except Exception as e:
            print(f"[BatchRenderAPI] Initialization failed: {e}")
            return False
    
    def _detect_system_resources(self) -> SystemInfo:
        """
        Detect system resources (GPU/CPU).

        Returns:
            SystemInfo object with detected resources
        """
        # Lazy-load system detector
        if self._system_detector is None:
            from .system_detector import SystemDetector
            self._system_detector = SystemDetector()

        return self._system_detector.detect_system_info()
    
    def start_batch_render(self, config: RenderConfig) -> bool:
        """
        Start batch render with given configuration.
        
        Args:
            config: Render configuration
            
        Returns:
            True if render started successfully, False otherwise
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        try:
            # Create process ID
            process_id = self._generate_process_id()
            
            # Create render process
            process = RenderProcess(
                process_id=process_id,
                layer_name=config.layers[0] if config.layers else "default",
                frame_range=config.frame_range,
                status=ProcessStatus.INITIALIZING,
                render_method=config.render_method
            )
            
            self._processes[process_id] = process
            
            # Emit signal
            if hasattr(self, 'render_started'):
                self.render_started.emit(process_id)
            
            print(f"[BatchRenderAPI] Started render process: {process_id}")
            print(f"  Layer: {process.layer_name}")
            print(f"  Frames: {config.frame_range}")
            print(f"  GPU: {config.gpu_id}")
            
            # TODO: Actually start the render process
            # This will be implemented in TASK-004 and TASK-005
            
            return True
            
        except Exception as e:
            print(f"[BatchRenderAPI] Failed to start render: {e}")
            return False
    
    def stop_all_renders(self) -> bool:
        """
        Stop all active render processes.
        
        Returns:
            True if all processes stopped successfully, False otherwise
        """
        try:
            for process_id, process in self._processes.items():
                if process.status in [ProcessStatus.RENDERING, ProcessStatus.WAITING]:
                    process.status = ProcessStatus.CANCELLED
                    print(f"[BatchRenderAPI] Cancelled process: {process_id}")
            
            return True
            
        except Exception as e:
            print(f"[BatchRenderAPI] Failed to stop renders: {e}")
            return False
    
    def get_render_status(self) -> List[RenderProcess]:
        """
        Get status of all render processes.
        
        Returns:
            List of RenderProcess objects
        """
        return list(self._processes.values())
    
    def get_system_info(self) -> Optional[SystemInfo]:
        """
        Get system information.
        
        Returns:
            SystemInfo object or None if not initialized
        """
        if not self._initialized:
            self.initialize()
        
        return self._system_info
    
    def get_process_by_id(self, process_id: str) -> Optional[RenderProcess]:
        """
        Get render process by ID.
        
        Args:
            process_id: Process ID
            
        Returns:
            RenderProcess object or None if not found
        """
        return self._processes.get(process_id)
    
    def _generate_process_id(self) -> str:
        """
        Generate unique process ID.
        
        Returns:
            Unique process ID string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        process_num = len(self._processes) + 1
        return f"p{process_num:03d}_{timestamp}"
    
    def cleanup(self) -> None:
        """Cleanup resources and stop all processes."""
        try:
            self.stop_all_renders()
            self._processes.clear()
            self._initialized = False
            print("[BatchRenderAPI] Cleanup completed")
            
        except Exception as e:
            print(f"[BatchRenderAPI] Cleanup error: {e}")

