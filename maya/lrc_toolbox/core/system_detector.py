# -*- coding: utf-8 -*-
"""
System Detector

Hardware detection and resource management for batch rendering.
Detects GPUs, CPUs, and Maya executables with resource allocation.
"""

import os
import platform
import multiprocessing
from typing import Optional, Tuple, List
from pathlib import Path

from .models import SystemInfo, GPUInfo
from ..utils.gpu_utils import detect_cuda_gpus
from ..config.batch_render_defaults import get_batch_render_defaults


class SystemDetector:
    """
    System hardware detection and resource management.
    
    Detects:
    - CUDA GPUs with memory information
    - CPU cores and threads
    - Maya executables (mayapy, Render.exe)
    - Available resources after reservation
    """
    
    def __init__(self):
        """Initialize system detector."""
        self._settings = get_batch_render_defaults()
        self._system_info: Optional[SystemInfo] = None
        self._mayapy_path: Optional[str] = None
        self._render_exe_path: Optional[str] = None
    
    def detect_system_info(self) -> SystemInfo:
        """
        Detect complete system information.
        
        Returns:
            SystemInfo object with all detected resources
        """
        # Detect GPUs
        gpus = detect_cuda_gpus()
        gpu_count = len(gpus)
        
        # Detect CPU
        cpu_cores, cpu_threads = self._detect_cpu_info()
        
        # Calculate available resources
        reserved_gpus = self._settings["gpu_allocation"]["reserve_for_maya"]
        reserved_cpu = self._settings["cpu_allocation"]["reserve_for_maya"]
        
        available_gpus = max(0, gpu_count - reserved_gpus)
        available_cpu_threads = max(0, cpu_threads - reserved_cpu)
        
        # Mark GPUs as available/reserved
        for i, gpu in enumerate(gpus):
            gpu.is_available = i >= reserved_gpus
        
        self._system_info = SystemInfo(
            gpu_count=gpu_count,
            gpus=gpus,
            cpu_cores=cpu_cores,
            cpu_threads=cpu_threads,
            available_gpus=available_gpus,
            available_cpu_threads=available_cpu_threads,
            reserved_gpu_count=reserved_gpus,
            reserved_cpu_threads=reserved_cpu
        )
        
        self._print_system_info()
        
        return self._system_info
    
    def _detect_cpu_info(self) -> Tuple[int, int]:
        """
        Detect CPU cores and threads.
        
        Returns:
            Tuple of (physical_cores, logical_threads)
        """
        try:
            # Get logical CPU count (threads)
            cpu_threads = multiprocessing.cpu_count()
            
            # Try to get physical cores (not always available)
            try:
                import psutil
                cpu_cores = psutil.cpu_count(logical=False)
                if cpu_cores is None:
                    cpu_cores = cpu_threads // 2  # Estimate
            except ImportError:
                # Estimate physical cores as half of threads (assumes hyperthreading)
                cpu_cores = cpu_threads // 2
            
            print(f"[CPU] Detected {cpu_cores} cores, {cpu_threads} threads")
            return cpu_cores, cpu_threads
            
        except Exception as e:
            print(f"[CPU] Detection failed: {e}")
            return 4, 8  # Fallback values
    
    def find_mayapy_executable(self) -> Optional[str]:
        """
        Find mayapy executable path.
        
        Searches common Maya installation locations.
        
        Returns:
            Path to mayapy executable or None if not found
        """
        if self._mayapy_path:
            return self._mayapy_path
        
        system = platform.system()
        
        # Common Maya versions to check
        maya_versions = ['2024', '2025', '2023', '2022']
        
        if system == 'Windows':
            # Windows paths
            base_paths = [
                r"C:\Program Files\Autodesk\Maya{version}\bin\mayapy.exe",
                r"C:\Program Files (x86)\Autodesk\Maya{version}\bin\mayapy.exe",
            ]
            
            for version in maya_versions:
                for base_path in base_paths:
                    path = base_path.format(version=version)
                    if os.path.exists(path):
                        self._mayapy_path = path
                        print(f"[Maya] Found mayapy: {path}")
                        return path
        
        elif system == 'Linux':
            # Linux paths
            base_paths = [
                "/usr/autodesk/maya{version}/bin/mayapy",
                "/opt/autodesk/maya{version}/bin/mayapy",
            ]
            
            for version in maya_versions:
                for base_path in base_paths:
                    path = base_path.format(version=version)
                    if os.path.exists(path):
                        self._mayapy_path = path
                        print(f"[Maya] Found mayapy: {path}")
                        return path
        
        print("[Maya] mayapy not found in standard locations")
        return None
    
    def find_render_executable(self) -> Optional[str]:
        """
        Find Maya Render executable path.
        
        Searches common Maya installation locations.
        
        Returns:
            Path to Render executable or None if not found
        """
        if self._render_exe_path:
            return self._render_exe_path
        
        system = platform.system()
        
        # Common Maya versions to check
        maya_versions = ['2024', '2025', '2023', '2022']
        
        if system == 'Windows':
            # Windows paths
            base_paths = [
                r"C:\Program Files\Autodesk\Maya{version}\bin\Render.exe",
                r"C:\Program Files (x86)\Autodesk\Maya{version}\bin\Render.exe",
            ]
            
            for version in maya_versions:
                for base_path in base_paths:
                    path = base_path.format(version=version)
                    if os.path.exists(path):
                        self._render_exe_path = path
                        print(f"[Maya] Found Render.exe: {path}")
                        return path
        
        elif system == 'Linux':
            # Linux paths
            base_paths = [
                "/usr/autodesk/maya{version}/bin/Render",
                "/opt/autodesk/maya{version}/bin/Render",
            ]
            
            for version in maya_versions:
                for base_path in base_paths:
                    path = base_path.format(version=version)
                    if os.path.exists(path):
                        self._render_exe_path = path
                        print(f"[Maya] Found Render: {path}")
                        return path
        
        print("[Maya] Render executable not found in standard locations")
        return None
    
    def get_available_gpu_ids(self) -> List[int]:
        """
        Get list of available GPU IDs for batch rendering.
        
        Returns:
            List of GPU device IDs available for use
        """
        if not self._system_info:
            self.detect_system_info()
        
        available_ids = []
        for gpu in self._system_info.gpus:
            if gpu.is_available:
                available_ids.append(gpu.device_id)
        
        return available_ids
    
    def get_recommended_gpu_id(self) -> int:
        """
        Get recommended GPU ID for batch rendering.
        
        Returns:
            Recommended GPU device ID (defaults to 1)
        """
        available_ids = self.get_available_gpu_ids()
        
        if available_ids:
            return available_ids[0]
        
        # Fallback to GPU 1 if detection failed
        return self._settings["gpu_allocation"]["default_batch_gpu"]
    
    def get_recommended_cpu_threads(self) -> int:
        """
        Get recommended CPU thread count for batch rendering.
        
        Returns:
            Recommended number of CPU threads
        """
        if not self._system_info:
            self.detect_system_info()
        
        # Use half of available threads, or default from settings
        recommended = self._system_info.available_cpu_threads // 2
        
        if recommended < 1:
            recommended = self._settings["cpu_allocation"]["default_batch_threads"]
        
        return recommended
    
    def _print_system_info(self) -> None:
        """Print detected system information."""
        if not self._system_info:
            return
        
        print("\n" + "=" * 60)
        print("SYSTEM INFORMATION")
        print("=" * 60)
        
        # GPU info
        print(f"\nGPUs: {self._system_info.gpu_count} total, "
              f"{self._system_info.available_gpus} available for batch")
        
        for gpu in self._system_info.gpus:
            status = "AVAILABLE" if gpu.is_available else "RESERVED"
            mem_gb = gpu.memory_total / (1024 ** 3)
            print(f"  GPU {gpu.device_id}: {gpu.name} ({mem_gb:.1f} GB) - {status}")
        
        # CPU info
        print(f"\nCPU: {self._system_info.cpu_cores} cores, "
              f"{self._system_info.cpu_threads} threads")
        print(f"  Available for batch: {self._system_info.available_cpu_threads} threads")
        
        print("=" * 60 + "\n")

