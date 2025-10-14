# -*- coding: utf-8 -*-
"""
GPU Utilities

CUDA GPU detection and management utilities for batch rendering.
Provides GPU information and availability checking.
"""

import subprocess
from typing import List, Optional
from ..core.models import GPUInfo


def detect_cuda_gpus() -> List[GPUInfo]:
    """
    Detect CUDA-compatible GPUs.
    
    Uses multiple detection methods with fallback:
    1. Try pynvml (NVIDIA Management Library)
    2. Fallback to nvidia-smi command
    3. Return empty list if no GPUs found
    
    Returns:
        List of GPUInfo objects for detected GPUs
    """
    # Try Method 1: pynvml
    gpus = _detect_with_pynvml()
    if gpus:
        return gpus
    
    # Try Method 2: nvidia-smi
    gpus = _detect_with_nvidia_smi()
    if gpus:
        return gpus
    
    # No GPUs detected
    print("[GPU] No CUDA GPUs detected")
    return []


def _detect_with_pynvml() -> List[GPUInfo]:
    """
    Detect GPUs using pynvml library.
    
    Returns:
        List of GPUInfo objects or empty list if pynvml not available
    """
    try:
        import pynvml
        
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        
        gpus = []
        for i in range(gpu_count):
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                
                # Handle both bytes and string returns
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                # Try to get compute capability
                try:
                    major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
                    compute_cap = f"{major}.{minor}"
                except:
                    compute_cap = None
                
                gpu_info = GPUInfo(
                    device_id=i,
                    name=name,
                    memory_total=memory_info.total,
                    memory_free=memory_info.free,
                    is_available=True,
                    compute_capability=compute_cap
                )
                gpus.append(gpu_info)
                
            except Exception as e:
                print(f"[GPU] Error reading GPU {i}: {e}")
                continue
        
        pynvml.nvmlShutdown()
        
        if gpus:
            print(f"[GPU] Detected {len(gpus)} GPUs using pynvml")
        
        return gpus
        
    except ImportError:
        print("[GPU] pynvml not available, trying nvidia-smi")
        return []
    except Exception as e:
        print(f"[GPU] pynvml detection failed: {e}")
        return []


def _detect_with_nvidia_smi() -> List[GPUInfo]:
    """
    Detect GPUs using nvidia-smi command.
    
    Returns:
        List of GPUInfo objects or empty list if nvidia-smi not available
    """
    try:
        # Run nvidia-smi to list GPUs
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,memory.total,memory.free', 
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return []
        
        gpus = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            
            try:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 4:
                    device_id = int(parts[0])
                    name = parts[1]
                    memory_total = int(parts[2]) * 1024 * 1024  # Convert MB to bytes
                    memory_free = int(parts[3]) * 1024 * 1024  # Convert MB to bytes
                    
                    gpu_info = GPUInfo(
                        device_id=device_id,
                        name=name,
                        memory_total=memory_total,
                        memory_free=memory_free,
                        is_available=True,
                        compute_capability=None
                    )
                    gpus.append(gpu_info)
                    
            except Exception as e:
                print(f"[GPU] Error parsing nvidia-smi line: {e}")
                continue
        
        if gpus:
            print(f"[GPU] Detected {len(gpus)} GPUs using nvidia-smi")
        
        return gpus
        
    except FileNotFoundError:
        print("[GPU] nvidia-smi not found")
        return []
    except Exception as e:
        print(f"[GPU] nvidia-smi detection failed: {e}")
        return []


def get_gpu_count() -> int:
    """
    Get number of available CUDA GPUs.
    
    Returns:
        Number of GPUs detected
    """
    gpus = detect_cuda_gpus()
    return len(gpus)


def is_gpu_available(gpu_id: int) -> bool:
    """
    Check if specific GPU is available.
    
    Args:
        gpu_id: GPU device ID
        
    Returns:
        True if GPU exists and is available, False otherwise
    """
    gpus = detect_cuda_gpus()
    
    for gpu in gpus:
        if gpu.device_id == gpu_id:
            return gpu.is_available
    
    return False


def get_gpu_info(gpu_id: int) -> Optional[GPUInfo]:
    """
    Get information for specific GPU.
    
    Args:
        gpu_id: GPU device ID
        
    Returns:
        GPUInfo object or None if GPU not found
    """
    gpus = detect_cuda_gpus()
    
    for gpu in gpus:
        if gpu.device_id == gpu_id:
            return gpu
    
    return None


def format_memory_size(bytes_size: int) -> str:
    """
    Format memory size in human-readable format.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string (e.g., "24.0 GB")
    """
    gb = bytes_size / (1024 ** 3)
    return f"{gb:.1f} GB"

