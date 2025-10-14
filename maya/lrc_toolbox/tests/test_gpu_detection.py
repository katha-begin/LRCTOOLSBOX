# -*- coding: utf-8 -*-
"""
GPU Detection Test Script

Run this in Maya Script Editor to debug GPU detection issues.
"""

def test_gpu_detection():
    """Test GPU detection with detailed output."""
    print("\n" + "="*60)
    print("GPU DETECTION TEST")
    print("="*60)
    
    # Test 1: Check pynvml
    print("\n[TEST 1] Checking pynvml library...")
    try:
        import pynvml
        print("  ✓ pynvml is installed")
        
        try:
            pynvml.nvmlInit()
            gpu_count = pynvml.nvmlDeviceGetCount()
            print(f"  ✓ pynvml detected {gpu_count} GPU(s)")
            
            for i in range(gpu_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                mem_gb = memory_info.total / (1024**3)
                print(f"    GPU {i}: {name} ({mem_gb:.1f} GB)")
            
            pynvml.nvmlShutdown()
            
        except Exception as e:
            print(f"  ✗ pynvml error: {e}")
            
    except ImportError:
        print("  ✗ pynvml not installed")
        print("    Install with: pip install pynvml")
    
    # Test 2: Check nvidia-smi
    print("\n[TEST 2] Checking nvidia-smi command...")
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,memory.total', 
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("  ✓ nvidia-smi is available")
            lines = result.stdout.strip().split('\n')
            print(f"  ✓ nvidia-smi detected {len(lines)} GPU(s)")
            for line in lines:
                print(f"    {line}")
        else:
            print(f"  ✗ nvidia-smi failed with code {result.returncode}")
            print(f"    Error: {result.stderr}")
            
    except FileNotFoundError:
        print("  ✗ nvidia-smi not found in PATH")
    except Exception as e:
        print(f"  ✗ nvidia-smi error: {e}")
    
    # Test 3: Check LRC Toolbox detection
    print("\n[TEST 3] Checking LRC Toolbox GPU detection...")
    try:
        from lrc_toolbox.utils.gpu_utils import detect_cuda_gpus
        
        gpus = detect_cuda_gpus()
        
        if gpus:
            print(f"  ✓ LRC Toolbox detected {len(gpus)} GPU(s)")
            for gpu in gpus:
                mem_gb = gpu.memory_total / (1024**3)
                print(f"    GPU {gpu.device_id}: {gpu.name} ({mem_gb:.1f} GB)")
                print(f"      Available: {gpu.is_available}")
                print(f"      Compute: {gpu.compute_capability}")
        else:
            print("  ✗ LRC Toolbox detected 0 GPUs")
            
    except Exception as e:
        print(f"  ✗ LRC Toolbox detection error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Check system detector
    print("\n[TEST 4] Checking System Detector...")
    try:
        from lrc_toolbox.core.system_detector import SystemDetector
        
        detector = SystemDetector()
        system_info = detector.detect_system_info()
        
        print(f"  GPU Count: {system_info.gpu_count}")
        print(f"  Available GPUs: {system_info.available_gpus}")
        print(f"  Reserved GPUs: {system_info.reserved_gpu_count}")
        
        if system_info.gpus:
            print(f"  Detected GPUs:")
            for gpu in system_info.gpus:
                mem_gb = gpu.memory_total / (1024**3)
                status = "Available" if gpu.is_available else "Reserved"
                print(f"    GPU {gpu.device_id}: {gpu.name} ({mem_gb:.1f} GB) - {status}")
        else:
            print("  No GPUs in system_info")
            
    except Exception as e:
        print(f"  ✗ System Detector error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")


# Run the test
if __name__ == "__main__":
    test_gpu_detection()
else:
    # When imported, provide easy function to run
    print("GPU Detection Test loaded. Run: test_gpu_detection()")

