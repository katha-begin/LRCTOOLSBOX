# -*- coding: utf-8 -*-
"""
Process Manager

Manages subprocess execution for batch rendering with real-time log capture
and process monitoring.
"""

import subprocess
import threading
import queue
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from .models import RenderProcess, ProcessStatus


class ProcessManager:
    """
    Manages render subprocess execution.
    
    Features:
    - Subprocess execution with environment variables
    - Real-time stdout/stderr capture
    - Process monitoring and control
    - Timeout handling
    """
    
    def __init__(self):
        """Initialize process manager."""
        self._active_processes: Dict[str, subprocess.Popen] = {}
        self._log_threads: Dict[str, threading.Thread] = {}
        self._log_queues: Dict[str, queue.Queue] = {}
    
    def start_process(self, process_id: str, command: list, 
                     environment: Dict[str, str],
                     log_callback: Optional[Callable[[str, str], None]] = None) -> bool:
        """
        Start render process.
        
        Args:
            process_id: Unique process ID
            command: Command as list of strings
            environment: Environment variables
            log_callback: Callback for log messages (process_id, message)
            
        Returns:
            True if process started successfully, False otherwise
        """
        try:
            print(f"[ProcessMgr] Starting process: {process_id}")
            print(f"[ProcessMgr] Command: {' '.join(command)}")
            print(f"[ProcessMgr] GPU: {environment.get('CUDA_VISIBLE_DEVICES', 'N/A')}")
            
            # Start subprocess
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=environment,
                universal_newlines=True,
                bufsize=1
            )
            
            self._active_processes[process_id] = process
            
            # Start log capture thread
            if log_callback:
                log_queue = queue.Queue()
                self._log_queues[process_id] = log_queue
                
                log_thread = threading.Thread(
                    target=self._capture_logs,
                    args=(process_id, process, log_callback, log_queue),
                    daemon=True
                )
                log_thread.start()
                self._log_threads[process_id] = log_thread
            
            print(f"[ProcessMgr] Process started: PID {process.pid}")
            return True
            
        except Exception as e:
            print(f"[ProcessMgr] Failed to start process: {e}")
            return False
    
    def _capture_logs(self, process_id: str, process: subprocess.Popen,
                     callback: Callable[[str, str], None],
                     log_queue: queue.Queue) -> None:
        """
        Capture process logs in separate thread.
        
        Args:
            process_id: Process ID
            process: Subprocess instance
            callback: Log callback function
            log_queue: Queue for log messages
        """
        try:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                
                line = line.rstrip()
                
                # Add to queue
                log_queue.put(line)
                
                # Call callback
                try:
                    callback(process_id, line)
                except Exception as e:
                    print(f"[ProcessMgr] Log callback error: {e}")
            
        except Exception as e:
            print(f"[ProcessMgr] Log capture error: {e}")
        
        finally:
            # Signal end of logs
            log_queue.put(None)
    
    def is_process_running(self, process_id: str) -> bool:
        """
        Check if process is still running.

        Args:
            process_id: Process ID

        Returns:
            True if process is running, False otherwise
        """
        process = self._active_processes.get(process_id)

        if not process:
            return False

        return process.poll() is None
    
    def get_process_return_code(self, process_id: str) -> Optional[int]:
        """
        Get process return code.
        
        Args:
            process_id: Process ID
            
        Returns:
            Return code or None if process still running
        """
        process = self._active_processes.get(process_id)
        
        if not process:
            return None
        
        return process.poll()
    
    def wait_for_process(self, process_id: str, timeout: Optional[float] = None) -> int:
        """
        Wait for process to complete.
        
        Args:
            process_id: Process ID
            timeout: Timeout in seconds (None = no timeout)
            
        Returns:
            Process return code
            
        Raises:
            subprocess.TimeoutExpired: If timeout exceeded
        """
        process = self._active_processes.get(process_id)
        
        if not process:
            raise ValueError(f"Process not found: {process_id}")
        
        return process.wait(timeout=timeout)
    
    def kill_process(self, process_id: str) -> bool:
        """
        Kill process forcefully.
        
        Args:
            process_id: Process ID
            
        Returns:
            True if process killed, False otherwise
        """
        process = self._active_processes.get(process_id)
        
        if not process:
            return False
        
        try:
            process.kill()
            process.wait(timeout=5)
            print(f"[ProcessMgr] Killed process: {process_id}")
            return True
            
        except Exception as e:
            print(f"[ProcessMgr] Failed to kill process: {e}")
            return False
    
    def terminate_process(self, process_id: str) -> bool:
        """
        Terminate process gracefully.
        
        Args:
            process_id: Process ID
            
        Returns:
            True if process terminated, False otherwise
        """
        process = self._active_processes.get(process_id)
        
        if not process:
            return False
        
        try:
            process.terminate()
            process.wait(timeout=10)
            print(f"[ProcessMgr] Terminated process: {process_id}")
            return True
            
        except subprocess.TimeoutExpired:
            # Force kill if terminate didn't work
            return self.kill_process(process_id)
            
        except Exception as e:
            print(f"[ProcessMgr] Failed to terminate process: {e}")
            return False
    
    def cleanup_process(self, process_id: str) -> None:
        """
        Cleanup process resources.
        
        Args:
            process_id: Process ID
        """
        # Remove from active processes
        if process_id in self._active_processes:
            del self._active_processes[process_id]
        
        # Wait for log thread to finish
        if process_id in self._log_threads:
            thread = self._log_threads[process_id]
            if thread.is_alive():
                thread.join(timeout=2)
            del self._log_threads[process_id]
        
        # Clear log queue
        if process_id in self._log_queues:
            del self._log_queues[process_id]
        
        print(f"[ProcessMgr] Cleaned up process: {process_id}")
    
    def get_active_process_count(self) -> int:
        """
        Get number of active processes.
        
        Returns:
            Number of active processes
        """
        return len(self._active_processes)
    
    def get_active_process_ids(self) -> list:
        """
        Get list of active process IDs.
        
        Returns:
            List of process IDs
        """
        return list(self._active_processes.keys())
    
    def cleanup_all(self) -> None:
        """Cleanup all processes."""
        for process_id in list(self._active_processes.keys()):
            self.terminate_process(process_id)
            self.cleanup_process(process_id)
        
        print("[ProcessMgr] All processes cleaned up")

