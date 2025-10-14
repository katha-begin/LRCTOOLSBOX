# -*- coding: utf-8 -*-
"""
Batch Render CLI

Command-line interface for batch rendering.
Supports automation and external tool integration (Nuke, etc.).
"""

import sys
import argparse
import time
from typing import Optional

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.batch_render_api import BatchRenderAPI
from core.models import RenderConfig, RenderMethod, RenderMode, ProcessStatus


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LRC Toolbox Batch Render CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Render specific layer with frame range
  python batch_render_cli.py --layer MASTER_BG_A --frames "1-24" --gpu 1
  
  # Render with custom method
  python batch_render_cli.py --layer MASTER_CHAR_A --frames "1,5,10,20" --method mayapy_custom
  
  # Render with step frames
  python batch_render_cli.py --layer MASTER_FX_A --frames "1-100x5" --gpu 1 --renderer redshift
  
  # Show system information
  python batch_render_cli.py --info
        """
    )
    
    # System info
    parser.add_argument(
        '--info',
        action='store_true',
        help='Show system information and exit'
    )
    
    # Render configuration
    parser.add_argument(
        '--layer',
        type=str,
        help='Render layer name'
    )
    
    parser.add_argument(
        '--frames',
        type=str,
        default='1-24',
        help='Frame range (e.g., "1-24", "1,5,10", "1-100x5")'
    )
    
    parser.add_argument(
        '--gpu',
        type=int,
        default=1,
        help='GPU device ID (default: 1)'
    )
    
    parser.add_argument(
        '--threads',
        type=int,
        default=4,
        help='CPU threads (default: 4)'
    )
    
    parser.add_argument(
        '--method',
        type=str,
        choices=['auto', 'mayapy_custom', 'render_exe', 'mayapy_basic'],
        default='auto',
        help='Render method (default: auto with fallback)'
    )
    
    parser.add_argument(
        '--renderer',
        type=str,
        default='redshift',
        choices=['redshift', 'arnold', 'vray'],
        help='Renderer (default: redshift)'
    )
    
    parser.add_argument(
        '--wait',
        action='store_true',
        help='Wait for render to complete'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=3600,
        help='Timeout in seconds (default: 3600)'
    )
    
    args = parser.parse_args()
    
    # Initialize API
    api = BatchRenderAPI()
    
    if not api.initialize():
        print("ERROR: Failed to initialize Batch Render API")
        return 1
    
    # Show system info
    if args.info:
        show_system_info(api)
        return 0
    
    # Validate render arguments
    if not args.layer:
        print("ERROR: --layer is required for rendering")
        parser.print_help()
        return 1
    
    # Create render config
    method_map = {
        'auto': RenderMethod.AUTO,
        'mayapy_custom': RenderMethod.MAYAPY_CUSTOM,
        'render_exe': RenderMethod.RENDER_EXE,
        'mayapy_basic': RenderMethod.MAYAPY_BASIC
    }
    
    config = RenderConfig(
        scene_file="",  # Will be set by API from current scene
        layers=[args.layer],
        frame_range=args.frames,
        gpu_id=args.gpu,
        cpu_threads=args.threads,
        render_method=method_map[args.method],
        renderer=args.renderer
    )
    
    print("\n" + "=" * 60)
    print("BATCH RENDER CONFIGURATION")
    print("=" * 60)
    print(f"Layer:    {args.layer}")
    print(f"Frames:   {args.frames}")
    print(f"GPU:      {args.gpu}")
    print(f"Threads:  {args.threads}")
    print(f"Method:   {args.method}")
    print(f"Renderer: {args.renderer}")
    print("=" * 60 + "\n")
    
    # Start render
    print("Starting batch render...")
    success = api.start_batch_render(config)
    
    if not success:
        print("ERROR: Failed to start batch render")
        return 1
    
    print("Batch render started successfully!")
    
    # Wait for completion if requested
    if args.wait:
        print(f"\nWaiting for render to complete (timeout: {args.timeout}s)...")
        result = wait_for_completion(api, args.timeout)
        
        if result:
            print("\nRender completed successfully!")
            return 0
        else:
            print("\nRender failed or timed out!")
            return 1
    
    return 0


def show_system_info(api: BatchRenderAPI) -> None:
    """
    Show system information.
    
    Args:
        api: BatchRenderAPI instance
    """
    system_info = api.get_system_info()
    
    if not system_info:
        print("ERROR: Failed to get system information")
        return
    
    print("\n" + "=" * 60)
    print("SYSTEM INFORMATION")
    print("=" * 60)
    
    # GPU info
    print(f"\nGPUs: {system_info.gpu_count} total, "
          f"{system_info.available_gpus} available for batch")
    
    for gpu in system_info.gpus:
        status = "AVAILABLE" if gpu.is_available else "RESERVED"
        mem_gb = gpu.memory_total / (1024 ** 3)
        print(f"  GPU {gpu.device_id}: {gpu.name} ({mem_gb:.1f} GB) - {status}")
    
    # CPU info
    print(f"\nCPU: {system_info.cpu_cores} cores, "
          f"{system_info.cpu_threads} threads")
    print(f"  Available for batch: {system_info.available_cpu_threads} threads")
    
    # Reserved resources
    print(f"\nReserved for Maya:")
    print(f"  GPUs: {system_info.reserved_gpu_count}")
    print(f"  CPU Threads: {system_info.reserved_cpu_threads}")
    
    print("=" * 60 + "\n")


def wait_for_completion(api: BatchRenderAPI, timeout: int) -> bool:
    """
    Wait for render to complete.
    
    Args:
        api: BatchRenderAPI instance
        timeout: Timeout in seconds
        
    Returns:
        True if completed successfully, False otherwise
    """
    start_time = time.time()
    last_status = None
    
    while True:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout:
            print(f"\nTimeout after {timeout}s")
            return False
        
        # Get render status
        processes = api.get_render_status()
        
        if not processes:
            print("\nNo active processes")
            return False
        
        # Check all processes
        all_done = True
        any_failed = False
        
        for process in processes:
            if process.status in [ProcessStatus.RENDERING, ProcessStatus.WAITING]:
                all_done = False
            
            if process.status == ProcessStatus.FAILED:
                any_failed = True
            
            # Print status update if changed
            status_key = f"{process.process_id}:{process.status.value}"
            if status_key != last_status:
                print(f"[{process.process_id}] {process.status.value} - "
                      f"Frame {process.current_frame}/{process.total_frames}")
                last_status = status_key
        
        # Check if all done
        if all_done:
            if any_failed:
                return False
            return True
        
        # Wait before next check
        time.sleep(2)


if __name__ == '__main__':
    sys.exit(main())

