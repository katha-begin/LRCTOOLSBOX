# -*- coding: utf-8 -*-
"""
Batch Render Tests

Simple test script to verify batch render functionality.
Run in Maya Script Editor or standalone Python.
"""

def test_frame_parser():
    """Test frame range parser."""
    print("\n" + "=" * 60)
    print("TEST: Frame Parser")
    print("=" * 60)
    
    from lrc_toolbox.utils.frame_parser import parse_frame_range, format_frame_range
    
    # Test cases
    test_cases = [
        ("1,5,10", [1, 5, 10]),
        ("10-20", list(range(10, 21))),
        ("1-10x3", [1, 4, 7, 10]),
        ("1,10-15,20", [1, 10, 11, 12, 13, 14, 15, 20]),
    ]
    
    passed = 0
    failed = 0
    
    for input_str, expected in test_cases:
        try:
            result = parse_frame_range(input_str)
            if result == expected:
                print(f"  PASS: {input_str} -> {result}")
                passed += 1
            else:
                print(f"  FAIL: {input_str} -> {result} (expected {expected})")
                failed += 1
        except Exception as e:
            print(f"  ERROR: {input_str} -> {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_gpu_detection():
    """Test GPU detection."""
    print("\n" + "=" * 60)
    print("TEST: GPU Detection")
    print("=" * 60)
    
    from lrc_toolbox.utils.gpu_utils import detect_cuda_gpus, get_gpu_count
    
    try:
        gpus = detect_cuda_gpus()
        count = get_gpu_count()
        
        print(f"  Detected {count} GPUs")
        
        for gpu in gpus:
            mem_gb = gpu.memory_total / (1024 ** 3)
            status = "AVAILABLE" if gpu.is_available else "RESERVED"
            print(f"    GPU {gpu.device_id}: {gpu.name} ({mem_gb:.1f} GB) - {status}")
        
        print("\n  PASS: GPU detection successful")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_system_detector():
    """Test system detector."""
    print("\n" + "=" * 60)
    print("TEST: System Detector")
    print("=" * 60)
    
    from lrc_toolbox.core.system_detector import SystemDetector
    
    try:
        detector = SystemDetector()
        system_info = detector.detect_system_info()
        
        print(f"  GPUs: {system_info.gpu_count} total, {system_info.available_gpus} available")
        print(f"  CPU: {system_info.cpu_cores} cores, {system_info.cpu_threads} threads")
        print(f"  Available CPU threads: {system_info.available_cpu_threads}")
        
        # Test executable detection
        mayapy = detector.find_mayapy_executable()
        render_exe = detector.find_render_executable()
        
        print(f"\n  mayapy: {mayapy if mayapy else 'NOT FOUND'}")
        print(f"  Render.exe: {render_exe if render_exe else 'NOT FOUND'}")
        
        print("\n  PASS: System detection successful")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_render_execution_manager():
    """Test render execution manager."""
    print("\n" + "=" * 60)
    print("TEST: Render Execution Manager")
    print("=" * 60)
    
    from lrc_toolbox.core.render_execution_manager import RenderExecutionManager
    from lrc_toolbox.core.models import RenderMethod
    
    try:
        manager = RenderExecutionManager()
        
        # Detect executables
        executables = manager.detect_executables()
        print(f"  mayapy: {executables['mayapy'] if executables['mayapy'] else 'NOT FOUND'}")
        print(f"  Render.exe: {executables['render_exe'] if executables['render_exe'] else 'NOT FOUND'}")
        
        # Get available methods
        methods = manager.get_available_methods()
        print(f"\n  Available methods: {[m.value for m in methods]}")
        
        # Test method selection
        selected = manager.select_render_method(RenderMethod.AUTO)
        print(f"  Selected method (AUTO): {selected.value}")
        
        print("\n  PASS: Render execution manager working")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_batch_render_api():
    """Test batch render API initialization."""
    print("\n" + "=" * 60)
    print("TEST: Batch Render API")
    print("=" * 60)
    
    from lrc_toolbox.core.batch_render_api import BatchRenderAPI
    
    try:
        api = BatchRenderAPI()
        
        # Initialize
        success = api.initialize()
        if not success:
            print("  ERROR: Failed to initialize API")
            return False
        
        print("  API initialized successfully")
        
        # Get system info
        system_info = api.get_system_info()
        if system_info:
            print(f"  System info: {system_info.gpu_count} GPUs, "
                  f"{system_info.cpu_threads} CPU threads")
        
        # Cleanup
        api.cleanup()
        
        print("\n  PASS: Batch render API working")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("BATCH RENDER SYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        ("Frame Parser", test_frame_parser),
        ("GPU Detection", test_gpu_detection),
        ("System Detector", test_system_detector),
        ("Render Execution Manager", test_render_execution_manager),
        ("Batch Render API", test_batch_render_api),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\nFATAL ERROR in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{len(results)} passed")
    print("=" * 60 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    # Run tests
    success = run_all_tests()
    
    if success:
        print("All tests passed!")
    else:
        print("Some tests failed!")

