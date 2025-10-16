# Batch Render Manager

GPU-accelerated batch rendering system for Maya with automatic fallback and real-time monitoring.

## Features

- **Three-Level Fallback System**: Automatic fallback from custom scripts to native Maya rendering
- **GPU Management**: Reserve GPU 0 for Maya, use GPU 1+ for batch rendering
- **Real-Time Monitoring**: Live log streaming and process status tracking
- **Flexible Frame Syntax**: Support for ranges, steps, and comma-separated frames
- **Cross-Platform**: Windows and Linux support
- **CLI & GUI**: Both command-line and graphical interfaces
- **Scene Preservation**: Automatic temporary file management

## Quick Start

### GUI Usage

1. Open LRC Toolbox in Maya
2. Navigate to "Batch Render" tab
3. Select render layer from dropdown
4. Enter frame range (e.g., `1-24`, `1,5,10`, `1-100x5`)
5. Choose GPU and render method
6. Click "Start Batch Render"

### CLI Usage

```bash
# Basic render
python batch_render_cli.py --layer MASTER_BG_A --frames "1-24" --gpu 1

# With custom method
python batch_render_cli.py --layer MASTER_CHAR_A --frames "1-100x5" --method mayapy_custom

# Show system info
python batch_render_cli.py --info

# Wait for completion
python batch_render_cli.py --layer MASTER_FX_A --frames "1-24" --wait
```

## Frame Range Syntax

The batch render system supports flexible frame range syntax:

### Single Frames
```
1,5,10,20
```
Renders frames 1, 5, 10, and 20.

### Ranges
```
10-20
```
Renders frames 10 through 20 (inclusive).

### Steps
```
1-100x5
```
Renders every 5th frame from 1 to 100, **always including first and last frames**.
Result: 1, 6, 11, 16, ..., 96, 100

### Combined
```
1,10-20,50,60-70x2
```
Combines all syntax types.

## Render Methods

The system uses a three-level priority fallback system:

### Priority 1: mayapy Custom Script (Most Flexible)
- Uses `mayapy` with custom Python script
- Allows pre/post render operations
- Full control over render process
- Best for complex pipelines

### Priority 2: Maya Render.exe (Most Reliable)
- Uses Maya's native batch renderer
- Battle-tested and stable
- Handles edge cases automatically
- Best for standard workflows

### Priority 3: mayapy Basic (Fallback)
- Simple `mayapy` with basic render
- Minimal functionality
- Last resort if others fail

### AUTO Mode (Recommended)
Automatically tries methods in priority order with fallback.

## GPU Configuration

### Default Allocation
- **GPU 0**: Reserved for Maya GUI session
- **GPU 1+**: Available for batch rendering

### Environment Variables
The system sets `CUDA_VISIBLE_DEVICES` to control GPU allocation:

```bash
# Windows
set CUDA_VISIBLE_DEVICES=1
Render.exe -r redshift -rl MASTER_BG_A scene.ma

# Linux
export CUDA_VISIBLE_DEVICES=1
Render -r redshift -rl MASTER_BG_A scene.ma
```

### Custom GPU Selection
You can specify different GPUs in the GUI or CLI:

```bash
python batch_render_cli.py --layer MASTER_BG_A --frames "1-24" --gpu 2
```

## System Requirements

### Minimum Requirements
- Maya 2022 or later
- CUDA-compatible GPU (NVIDIA)
- Python 3.7+
- 8GB RAM

### Recommended
- Maya 2024+
- 2+ NVIDIA GPUs (24GB+ VRAM each)
- 16+ CPU cores
- 32GB+ RAM

### Supported Platforms
- Windows 10/11
- Linux (CentOS 7+, Ubuntu 18.04+)

### Supported Renderers
- Redshift
- Arnold
- V-Ray

## Architecture

### Core Components

```
BatchRenderAPI
├── SystemDetector (GPU/CPU detection)
├── ScenePreparation (temp file management)
├── RenderExecutionManager (fallback system)
└── ProcessManager (subprocess control)
```

### Data Flow

1. **Scene Preparation**: Save current scene to temporary file
2. **System Detection**: Detect available GPUs and CPUs
3. **Method Selection**: Choose render method with fallback
4. **Command Building**: Build appropriate command for method
5. **Process Execution**: Start subprocess with GPU allocation
6. **Log Capture**: Stream logs in real-time
7. **Cleanup**: Remove temporary files

## Configuration

### Default Settings

Located in `config/batch_render_defaults.py`:

```python
DEFAULT_BATCH_RENDER_SETTINGS = {
    "gpu_allocation": {
        "reserve_for_maya": 1,  # GPUs reserved for Maya
        "default_batch_gpu": 1,  # Default batch GPU
    },
    "cpu_allocation": {
        "reserve_for_maya": 4,  # CPU cores reserved
        "default_batch_threads": 4,  # Default threads
    },
    "file_management": {
        "temp_directory": "./temp",
        "cleanup_on_exit": True,
        "keep_latest_files": 5,
    },
}
```

### Customization

Modify settings in the GUI Settings tab or edit configuration files directly.

## Troubleshooting

### GPU Not Detected
```
[GPU] No CUDA GPUs detected
```
**Solution**: Install NVIDIA drivers and CUDA toolkit.

### mayapy Not Found
```
[Maya] mayapy not found in standard locations
```
**Solution**: Ensure Maya is installed in standard location or set path manually.

### Render Failed
```
[Render] Render failed with error: ...
```
**Solution**: Check render logs for specific error. System will automatically try fallback methods.

### Scene Not Saved
```
[ScenePrep] Scene has unsaved changes
```
**Solution**: Save your scene before starting batch render.

## API Usage

### Python API

```python
from lrc_toolbox.core.batch_render_api import BatchRenderAPI
from lrc_toolbox.core.models import RenderConfig, RenderMethod

# Initialize API
api = BatchRenderAPI()
api.initialize()

# Create config
config = RenderConfig(
    scene_file="",  # Auto-detected
    layers=["MASTER_BG_A"],
    frame_range="1-24",
    gpu_id=1,
    render_method=RenderMethod.AUTO,
    renderer="redshift"
)

# Start render
success = api.start_batch_render(config)

# Monitor progress
processes = api.get_render_status()
for process in processes:
    print(f"{process.process_id}: {process.status.value}")

# Cleanup
api.cleanup()
```

## Performance Tips

1. **Use GPU 1+ for batch**: Keep GPU 0 for Maya GUI
2. **Optimize frame ranges**: Use steps for preview renders
3. **Monitor system resources**: Check GPU memory usage
4. **Clean temp files**: Regularly cleanup old temporary files
5. **Use AUTO method**: Let system choose best render method

## Known Limitations

- Single render layer per batch (multiple layers coming soon)
- No render farm integration (planned for future)
- Limited progress parsing (renderer-specific)

## Future Enhancements

- [ ] Multiple layer batch rendering
- [ ] Render farm integration
- [ ] Advanced progress parsing
- [ ] Email notifications
- [ ] Render statistics and analytics

## Support

For issues or questions:
1. Check troubleshooting section
2. Review render logs
3. Contact pipeline team

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-14  
**Author**: LRC Toolbox Team

