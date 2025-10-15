# -*- coding: utf-8 -*-
"""
Test GPU Detection Fix

Quick test to verify the nvidia-smi fix works in Maya.
"""

def test_gpu_fix():
    """Test the fixed GPU detection."""
    print("\n" + "="*60)
    print("GPU DETECTION FIX TEST")
    print("="*60)
    
    # Test the fixed detection
    print("\n[TEST] Running detect_cuda_gpus()...")
    try:
        from lrc_toolbox.utils.gpu_utils import detect_cuda_gpus
        
        print("  Calling detect_cuda_gpus()...")
        gpus = detect_cuda_gpus()
        
        if gpus:
            print(f"\n  ✓ SUCCESS! Detected {len(gpus)} GPU(s):")
            for gpu in gpus:
                mem_gb = gpu.memory_total / (1024**3) if gpu.memory_total > 0 else 0
                print(f"    GPU {gpu.device_id}: {gpu.name}")
                if mem_gb > 0:
                    print(f"      Memory: {mem_gb:.1f} GB")
                print(f"      Available: {gpu.is_available}")
                if gpu.compute_capability:
                    print(f"      Compute: {gpu.compute_capability}")
        else:
            print("\n  ✗ No GPUs detected")
            print("\n  Possible solutions:")
            print("    1. Install pynvml: pip install pynvml")
            print("    2. Check NVIDIA drivers are installed")
            print("    3. Check Maya Script Editor for error messages")
            
    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")


# Run the test
if __name__ == "__main__":
    test_gpu_fix()
else:
    # When imported, provide easy function to run
    print("GPU Fix Test loaded. Run: test_gpu_fix()")

