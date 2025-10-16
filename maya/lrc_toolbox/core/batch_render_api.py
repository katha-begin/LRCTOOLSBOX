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

        # Process monitoring timer
        self._monitor_timer = None
        if Signal is not None:
            try:
                self._monitor_timer = QtCore.QTimer()
                self._monitor_timer.timeout.connect(self._check_process_status)
                self._monitor_timer.setInterval(2000)  # Check every 2 seconds
            except:
                pass

        # Queue management - CRITICAL FIX for concurrent job control
        self._job_queue: List[str] = []  # Stores process_ids, not configs
        self._max_concurrent_jobs = 1  # Default: 1 job at a time

        # GPU assignment tracking for auto mode
        self._next_gpu_index = 0  # Round-robin GPU assignment
    
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

    def set_max_concurrent_jobs(self, max_jobs: int) -> None:
        """
        Set maximum concurrent render jobs.

        Args:
            max_jobs: Maximum number of jobs to run concurrently (1-8)
        """
        self._max_concurrent_jobs = max(1, min(8, max_jobs))
        print(f"[BatchRenderAPI] Max concurrent jobs set to: {self._max_concurrent_jobs}")

        # Try to start queued jobs
        self._process_queue()

    def _get_active_job_count(self) -> int:
        """Get number of currently active (rendering) jobs.

        Note: WAITING jobs are queued, not active. Only count RENDERING and INITIALIZING.
        """
        return sum(1 for p in self._processes.values()
                  if p.status in [ProcessStatus.RENDERING, ProcessStatus.INITIALIZING])

    def _get_next_available_gpu(self) -> int:
        """
        Get next available GPU using round-robin distribution.

        Returns:
            GPU ID (1-based) to use for next job
        """
        # Get available GPUs from system info
        if self._system_info and self._system_info.gpus:
            gpu_count = len(self._system_info.gpus)

            # Round-robin assignment
            gpu_id = (self._next_gpu_index % gpu_count) + 1  # 1-based indexing
            self._next_gpu_index += 1

            return gpu_id
        else:
            # Fallback: use GPU 1 if no system info
            return 1

    def _process_queue(self) -> None:
        """Process job queue - start jobs if slots available."""
        active_count = self._get_active_job_count()

        # Start jobs while we have queue and available slots
        while self._job_queue and active_count < self._max_concurrent_jobs:
            process_id = self._job_queue.pop(0)
            process = self._processes.get(process_id)
            if process:
                print(f"[BatchRenderAPI] Starting queued job: {process.layer_name}")
                self._start_render_immediate(process_id)
                active_count += 1

    def start_batch_render(self, config: RenderConfig) -> bool:
        """
        Start batch render with given configuration.
        Uses queue system to respect max_concurrent_jobs limit.

        Args:
            config: Render configuration

        Returns:
            True if render queued/started successfully, False otherwise
        """
        if not self._initialized:
            if not self.initialize():
                return False

        # CRITICAL FIX: Create process entry immediately (even if queued)
        # This makes queued jobs visible in the UI

        # Create process ID
        process_id = self._generate_process_id()

        # Parse frames
        from ..utils.frame_parser import parse_frame_range
        frames = parse_frame_range(config.frame_range)

        # Create render process
        layer_name = config.layers[0] if config.layers else "defaultRenderLayer"

        process = RenderProcess(
            process_id=process_id,
            layer_name=layer_name,
            frame_range=config.frame_range,
            frames=frames,
            total_frames=len(frames),
            status=ProcessStatus.WAITING,  # Start as WAITING
            render_method=config.render_method,
            gpu_id=config.gpu_id,  # Store GPU ID
            start_time=None  # Will be set when actually starts
        )

        # Store config in process for later use
        if not hasattr(process, '_config'):
            process._config = config

        self._processes[process_id] = process

        # Emit signal so UI updates
        if hasattr(self, 'render_started'):
            self.render_started.emit(process_id)

        # Check if we can start immediately or need to queue
        active_count = self._get_active_job_count()

        print(f"[BatchRenderAPI] Job check: active={active_count}, max={self._max_concurrent_jobs}")

        if active_count < self._max_concurrent_jobs:
            # Start immediately
            print(f"[BatchRenderAPI] Starting job immediately ({active_count + 1}/{self._max_concurrent_jobs})")
            result = self._start_render_immediate(process_id)
            if not result:
                print(f"[BatchRenderAPI] ERROR: Failed to start job {process_id}")
                process.status = ProcessStatus.FAILED
                process.error_message = "Failed to start render process"
            return result
        else:
            # Add to queue (store process_id, not config)
            self._job_queue.append(process_id)
            print(f"[BatchRenderAPI] Job queued: {layer_name} (Queue size: {len(self._job_queue)})")
            return True

    def _start_render_immediate(self, process_id: str) -> bool:
        """
        Start render immediately for an existing process.

        Args:
            process_id: Process ID to start

        Returns:
            True if render started successfully, False otherwise
        """
        try:
            # Get existing process
            process = self._processes.get(process_id)
            if not process:
                print(f"[BatchRenderAPI] ERROR: Process {process_id} not found")
                return False

            # Get config from process
            config = getattr(process, '_config', None)
            if not config:
                print(f"[BatchRenderAPI] ERROR: No config found for process {process_id}")
                return False

            # Lazy-load managers
            if self._execution_manager is None:
                from .render_execution_manager import RenderExecutionManager
                self._execution_manager = RenderExecutionManager()
                self._execution_manager.detect_executables()

            if self._process_manager is None:
                from .process_manager import ProcessManager
                self._process_manager = ProcessManager()

            # Lazy-load scene preparation
            from .scene_preparation import ScenePreparation
            scene_prep = ScenePreparation()

            # Update process status and start time
            process.status = ProcessStatus.INITIALIZING
            process.start_time = datetime.now()

            layer_name = process.layer_name

            # Save temp scene
            temp_scene = scene_prep.save_temp_scene(layer_name, process_id)
            if not temp_scene:
                raise RuntimeError("Failed to save temporary scene")

            process.temp_file_path = temp_scene

            # Store original scene file for output path calculation
            process.scene_file = config.scene_file

            # Select render method
            method = self._execution_manager.select_render_method(config.render_method)
            process.render_method = method

            # Build command
            command = self._execution_manager.build_render_command(
                config, method, temp_scene
            )

            # Build environment
            environment = self._execution_manager.build_environment(config)

            # Start process
            success = self._process_manager.start_process(
                process_id,
                command,
                environment,
                log_callback=self._handle_log_message
            )

            if not success:
                raise RuntimeError("Failed to start render process")

            process.status = ProcessStatus.RENDERING

            # Emit signal
            if hasattr(self, 'render_started'):
                self.render_started.emit(process_id)

            # Start monitoring timer if not already running
            if self._monitor_timer and not self._monitor_timer.isActive():
                self._monitor_timer.start()
                print("[BatchRenderAPI] Started process monitoring timer")

            print(f"[BatchRenderAPI] Started render process: {process_id}")
            print(f"  Layer: {process.layer_name}")
            print(f"  Frames: {config.frame_range} ({process.total_frames} frames)")
            print(f"  GPU: {config.gpu_id}")
            print(f"  Method: {method.value}")

            return True

        except Exception as e:
            import traceback
            print(f"[BatchRenderAPI] ERROR: Failed to start render: {e}")
            print(f"[BatchRenderAPI] Traceback:\n{traceback.format_exc()}")

            # Update process status
            if process_id in self._processes:
                self._processes[process_id].status = ProcessStatus.FAILED
                self._processes[process_id].error_message = str(e)
                self._processes[process_id].end_time = datetime.now()

            return False
    
    def stop_all_renders(self) -> bool:
        """
        Stop all active render processes.

        Returns:
            True if all processes stopped successfully, False otherwise
        """
        try:
            if self._process_manager is None:
                # Still need to cancel WAITING jobs
                for process_id, process in self._processes.items():
                    if process.status in [ProcessStatus.WAITING, ProcessStatus.INITIALIZING]:
                        process.status = ProcessStatus.CANCELLED
                        process.end_time = datetime.now()
                        print(f"[BatchRenderAPI] Cancelled queued process: {process_id}")

                # Clear job queue
                self._job_queue.clear()
                return True

            for process_id, process in self._processes.items():
                if process.status in [ProcessStatus.RENDERING, ProcessStatus.WAITING, ProcessStatus.INITIALIZING]:
                    # Terminate process (only if actually running)
                    if process.status == ProcessStatus.RENDERING:
                        self._process_manager.terminate_process(process_id)

                    # Update status
                    process.status = ProcessStatus.CANCELLED
                    process.end_time = datetime.now()

                    print(f"[BatchRenderAPI] Cancelled process: {process_id}")

            # Clear job queue
            self._job_queue.clear()
            print(f"[BatchRenderAPI] Cleared job queue")

            # Stop monitoring timer if no active processes remain
            active_count = sum(1 for p in self._processes.values()
                              if p.status in [ProcessStatus.RENDERING, ProcessStatus.WAITING, ProcessStatus.INITIALIZING])

            if active_count == 0 and self._monitor_timer and self._monitor_timer.isActive():
                self._monitor_timer.stop()
                print("[BatchRenderAPI] Stopped process monitoring timer")

            return True

        except Exception as e:
            print(f"[BatchRenderAPI] Failed to stop renders: {e}")
            return False

    def _handle_log_message(self, process_id: str, message: str) -> None:
        """
        Handle log message from render process.

        Args:
            process_id: Process ID
            message: Log message
        """
        # Store log message
        if process_id in self._processes:
            process = self._processes[process_id]
            process.log_messages.append(message)

            # Emit log signal for UI
            if hasattr(self, 'render_log'):
                self.render_log.emit(process_id, message)

            # Parse progress from log
            # Look for frame completion messages from Arnold/Redshift
            import re

            # Arnold: "Rendering frame 5 of 10"
            # Redshift: "Rendering layer 'layer_name', frame 5 (5/10)"
            # Note: Redshift outputs multiple lines per frame (for each AOV/tile)
            # We need to track unique frames to avoid counting duplicates
            frame_match = re.search(r'frame\s+(\d+).*?[(/](\d+)[)/]', message, re.IGNORECASE)
            if frame_match:
                current_frame = int(frame_match.group(1))
                total_frames = int(frame_match.group(2))

                # Store total frames if not set
                if process.total_frames == 0:
                    process.total_frames = total_frames

                # Update current frame (track highest frame seen)
                if current_frame > process.current_frame:
                    process.current_frame = current_frame

                    # Calculate progress (cap at 100%)
                    if total_frames > 0:
                        progress = min(100.0, (current_frame / total_frames) * 100.0)

                        # Only update if progress increased
                        if progress > process.progress:
                            process.progress = progress

                            # Emit progress signal
                            if hasattr(self, 'render_progress'):
                                self.render_progress.emit(process_id, progress)

            # Parse output path from saved file messages
            # Redshift: "Saved file 'V:/path/to/file.exr'"
            # Arnold: "writing file 'V:/path/to/file.exr'"
            if not hasattr(process, 'output_path') or not process.output_path:
                output_match = re.search(r"(?:Saved file|writing file)\s+['\"]([^'\"]+)['\"]", message, re.IGNORECASE)
                if output_match:
                    import os
                    file_path = output_match.group(1)
                    # Get directory containing the rendered file
                    output_dir = os.path.dirname(file_path)
                    process.output_path = output_dir
                    print(f"[BatchRenderAPI] Detected output path: {output_dir}")

            # Detect render completion messages
            # Redshift: "Render complete"
            # Arnold: "render done"
            if re.search(r'render\s+(complete|done|finished)', message, re.IGNORECASE):
                print(f"[BatchRenderAPI] Detected render completion message for {process_id}")
                # Don't set status here - let process monitoring handle it
                # Just ensure progress is at 100%
                if process.progress < 100.0:
                    process.progress = 100.0
                    if hasattr(self, 'render_progress'):
                        self.render_progress.emit(process_id, 100.0)

            # Emit log signal
            if hasattr(self, 'render_log'):
                self.render_log.emit(process_id, message)
    
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
    
    def _check_process_status(self) -> None:
        """
        Check status of all active processes (called by timer).

        Detects crashed processes and updates their status.
        """
        if not self._process_manager:
            return

        crashed_processes = []

        for process_id, process in list(self._processes.items()):
            # Only check processes that should be running
            if process.status not in [ProcessStatus.RENDERING, ProcessStatus.INITIALIZING, ProcessStatus.WAITING]:
                continue

            # Check if process is still running
            is_running = self._process_manager.is_process_running(process_id)

            if not is_running:
                # Process stopped - check return code
                return_code = self._process_manager.get_process_return_code(process_id)

                if return_code is None:
                    # Process not found - might have crashed before starting
                    print(f"[BatchRenderAPI] Process {process_id} not found - marking as failed")
                    process.status = ProcessStatus.FAILED
                    process.error_message = "Process not found (crashed before starting)"
                    process.end_time = datetime.now()
                    crashed_processes.append((process_id, False))

                elif return_code == 0:
                    # Process completed successfully
                    print(f"[BatchRenderAPI] Process {process_id} completed successfully")
                    process.status = ProcessStatus.COMPLETED
                    process.progress = 100.0
                    process.end_time = datetime.now()

                    # Emit progress and completion signals
                    if hasattr(self, 'render_progress'):
                        self.render_progress.emit(process_id, 100.0)
                    if hasattr(self, 'render_completed'):
                        self.render_completed.emit(process_id, True)

                else:
                    # Process failed with error code
                    print(f"[BatchRenderAPI] Process {process_id} failed with return code {return_code}")
                    process.status = ProcessStatus.FAILED
                    process.error_message = f"Process exited with code {return_code}"
                    process.end_time = datetime.now()
                    crashed_processes.append((process_id, False))

                # Cleanup process resources
                self._process_manager.cleanup_process(process_id)

        # Emit signals for crashed processes
        for process_id, success in crashed_processes:
            if hasattr(self, 'render_completed'):
                self.render_completed.emit(process_id, success)

        # CRITICAL: Process queue when jobs complete
        if crashed_processes or any(p.status == ProcessStatus.COMPLETED for p in self._processes.values()):
            self._process_queue()

        # Stop timer if no active processes and no queue
        active_count = sum(1 for p in self._processes.values()
                          if p.status in [ProcessStatus.RENDERING, ProcessStatus.INITIALIZING, ProcessStatus.WAITING])

        if active_count == 0 and len(self._job_queue) == 0 and self._monitor_timer and self._monitor_timer.isActive():
            self._monitor_timer.stop()
            print("[BatchRenderAPI] Stopped process monitoring timer (no active processes or queue)")

    def cleanup(self) -> None:
        """Cleanup resources and stop all processes."""
        try:
            # Stop monitoring timer
            if self._monitor_timer and self._monitor_timer.isActive():
                self._monitor_timer.stop()

            self.stop_all_renders()

            # Cleanup process manager
            if self._process_manager:
                self._process_manager.cleanup_all()

            # Cleanup temp files
            from .scene_preparation import ScenePreparation
            scene_prep = ScenePreparation()
            scene_prep.cleanup_temp_files(keep_latest=5)

            self._processes.clear()
            self._initialized = False
            print("[BatchRenderAPI] Cleanup completed")

        except Exception as e:
            print(f"[BatchRenderAPI] Cleanup error: {e}")

