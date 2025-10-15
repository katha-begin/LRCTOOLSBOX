# -*- coding: utf-8 -*-
"""
Direct nvidia-smi Test Script

Tests nvidia-smi command directly to see what's happening.
"""

def test_nvidia_smi_direct():
    """Test nvidia-smi command directly with detailed output."""
    print("\n" + "="*60)
    print("NVIDIA-SMI DIRECT TEST")
    print("="*60)
    
    import subprocess
    
    # Test 1: Basic nvidia-smi
    print("\n[TEST 1] Running basic nvidia-smi...")
    try:
        result = subprocess.run(
            ['nvidia-smi'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"  Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("  ✓ nvidia-smi executed successfully")
            print("\n  Output (first 500 chars):")
            print("  " + "-"*56)
            output_lines = result.stdout[:500].split('\n')
            for line in output_lines:
                print(f"  {line}")
            print("  " + "-"*56)
        else:
            print(f"  ✗ nvidia-smi failed with code {result.returncode}")
            print(f"  Error: {result.stderr}")
            
    except FileNotFoundError:
        print("  ✗ nvidia-smi not found in PATH")
        return
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return
    
    # Test 2: nvidia-smi with query
    print("\n[TEST 2] Running nvidia-smi with query...")
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,memory.total,memory.free', 
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"  Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("  ✓ Query executed successfully")
            print(f"\n  Raw output:")
            print("  " + "-"*56)
            print(f"  '{result.stdout}'")
            print("  " + "-"*56)
            
            print(f"\n  Output length: {len(result.stdout)} characters")
            print(f"  Output (repr): {repr(result.stdout)}")
            
            # Parse output
            lines = result.stdout.strip().split('\n')
            print(f"\n  Number of lines: {len(lines)}")
            
            for i, line in enumerate(lines):
                print(f"\n  Line {i}: '{line}'")
                print(f"    Length: {len(line)}")
                print(f"    Stripped: '{line.strip()}'")
                
                if line.strip():
                    parts = [p.strip() for p in line.split(',')]
                    print(f"    Parts: {parts}")
                    print(f"    Number of parts: {len(parts)}")
                    
                    if len(parts) >= 4:
                        try:
                            device_id = int(parts[0])
                            name = parts[1]
                            memory_total = int(parts[2])
                            memory_free = int(parts[3])
                            
                            print(f"    ✓ Parsed successfully:")
                            print(f"      Device ID: {device_id}")
                            print(f"      Name: {name}")
                            print(f"      Memory Total: {memory_total} MB")
                            print(f"      Memory Free: {memory_free} MB")
                        except Exception as e:
                            print(f"    ✗ Parse error: {e}")
                    else:
                        print(f"    ✗ Not enough parts (need 4, got {len(parts)})")
        else:
            print(f"  ✗ Query failed with code {result.returncode}")
            print(f"  Stderr: {result.stderr}")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Test LRC Toolbox detection
    print("\n[TEST 3] Testing LRC Toolbox _detect_with_nvidia_smi()...")
    try:
        from lrc_toolbox.utils.gpu_utils import _detect_with_nvidia_smi
        
        gpus = _detect_with_nvidia_smi()
        
        if gpus:
            print(f"  ✓ Detected {len(gpus)} GPU(s)")
            for gpu in gpus:
                mem_gb = gpu.memory_total / (1024**3)
                print(f"    GPU {gpu.device_id}: {gpu.name} ({mem_gb:.1f} GB)")
        else:
            print("  ✗ No GPUs detected by LRC Toolbox")
            print("    Check output above to see where parsing failed")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Test full detection chain
    print("\n[TEST 4] Testing full detect_cuda_gpus()...")
    try:
        from lrc_toolbox.utils.gpu_utils import detect_cuda_gpus
        
        gpus = detect_cuda_gpus()
        
        if gpus:
            print(f"  ✓ Detected {len(gpus)} GPU(s)")
            for gpu in gpus:
                mem_gb = gpu.memory_total / (1024**3)
                print(f"    GPU {gpu.device_id}: {gpu.name} ({mem_gb:.1f} GB)")
        else:
            print("  ✗ No GPUs detected")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    print("\n📋 WHAT TO LOOK FOR:")
    print("  - TEST 1 should show your GPU info")
    print("  - TEST 2 should show CSV output with 4 values per line")
    print("  - TEST 3 should detect your GPU")
    print("  - If TEST 2 works but TEST 3 fails, there's a parsing issue")
    print("")


# Run the test
if __name__ == "__main__":
    test_nvidia_smi_direct()
else:
    # When imported, provide easy function to run
    print("nvidia-smi Direct Test loaded. Run: test_nvidia_smi_direct()")

