# Batch Render Manager - Technical Specification

## 🏗️ **Architecture Overview**

**Design Pattern:** Model-View-Controller with Service Layer  
**Integration:** Standalone dialog with LRC Toolbox framework integration  
**Communication:** Signal-slot pattern for UI updates, subprocess pipes for render communication  

## 📁 **Module Structure**

```
maya/lrc_toolbox/
├── core/
│   ├── batch_render_api.py          # Main API and orchestration
│   ├── system_detector.py           # Hardware detection and resource management
│   └── render_process_manager.py    # Subprocess lifecycle management
├── ui/
│   └── dialogs/
│       ├── batch_render_dialog.py   # Main UI dialog
│       └── render_progress_widget.py # Progress monitoring component
├── utils/
│   ├── gpu_utils.py                 # CUDA/GPU detection utilities
│   ├── frame_parser.py              # Frame range parsing and validation
│   ├── render_subprocess.py         # Individual render process wrapper
│   └── temp_file_manager.py         # Temporary file lifecycle management
├── cli/
│   └── batch_render_cli.py          # Command-line interface
└── config/
    └── batch_render_defaults.py     # Default configuration values
```

## 🔧 **Core Components**

### **1. BatchRenderAPI (core/batch_render_api.py)**
```python
class BatchRenderAPI:
    """Main orchestration class for batch rendering operations."""
    
    def __init__(self):
        self.system_detector = SystemDetector()
        self.process_manager = RenderProcessManager()
        self.temp_manager = TempFileManager()
        
    def start_batch_render(self, config: RenderConfig) -> bool
    def stop_all_renders(self) -> bool
    def get_render_status(self) -> List[RenderStatus]
    def get_system_info(self) -> SystemInfo
```

**Key Responsibilities:**
- Coordinate all batch render operations
- Manage resource allocation and process scheduling
- Provide unified API for UI and CLI access
- Handle error recovery and cleanup

### **2. SystemDetector (core/system_detector.py)**
```python
class SystemDetector:
    """Hardware detection and resource management."""
    
    def detect_cuda_gpus(self) -> List[GPUInfo]
    def detect_cpu_info(self) -> CPUInfo
    def get_available_resources(self) -> ResourceInfo
    def reserve_maya_resources(self) -> None
```

**Key Features:**
- CUDA GPU detection using pynvml or nvidia-ml-py
- CPU core and thread detection
- Memory availability checking
- Resource reservation for Maya session

### **3. RenderProcessManager (core/render_process_manager.py)**
```python
class RenderProcessManager:
    """Manages multiple render subprocess lifecycles."""
    
    def create_render_process(self, config: ProcessConfig) -> RenderProcess
    def monitor_processes(self) -> None
    def terminate_process(self, process_id: str) -> bool
    def get_process_status(self, process_id: str) -> ProcessStatus
```

**Process Management:**
- Subprocess creation and monitoring
- Resource allocation per process
- Inter-process communication
- Graceful termination and cleanup

## 🎨 **User Interface Specification**

### **Main Dialog Layout (ui/dialogs/batch_render_dialog.py)**

```python
class BatchRenderDialog(QtWidgets.QDialog):
    """Main batch render management dialog."""
    
    # UI Sections
    - system_info_widget: SystemInfoWidget
    - render_config_widget: RenderConfigWidget  
    - active_renders_table: ActiveRendersTable
    - logs_monitor: LogsMonitorWidget
    - control_buttons: ControlButtonsWidget
```

### **UI Component Specifications:**

#### **System Info Widget**
```
┌─────────────────────────────────────────────────────────────┐
│ System Resources                                            │
│ ┌─────────────────┬─────────────────┬─────────────────────┐ │
│ │ CUDA GPUs: 2    │ Available: 1    │ Reserved for Maya:1 │ │
│ │ GPU Memory: 24GB│ Available: 12GB │ In Use: 12GB        │ │
│ │ CPU Cores: 16   │ Available: 12   │ Reserved: 4         │ │
│ └─────────────────┴─────────────────┴─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### **Render Configuration Widget**
```
┌─────────────────────────────────────────────────────────────┐
│ Render Configuration                                        │
│ Render Layers:                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [x] MASTER_BG_A    [ ] MASTER_CHAR_A   [ ] MASTER_FX_A  │ │
│ │ [ ] MASTER_ATMOS_A [x] All Active Layers               │ │
│ └─────────────────────────────────────────────────────────┘ │
│ Frame Range: [1,10-20,50        ] Step: [1  ]              │
│ GPU Allocation: [1] CPU Threads: [4]                       │
│ Mode: [x] Separate Layers  [ ] Combined Rendering          │
└─────────────────────────────────────────────────────────────┘
```

#### **Active Renders Table**
```
┌─────────────────────────────────────────────────────────────┐
│ Active Renders                                              │
│ ┌─────┬──────────────┬───────┬──────────┬─────────────────┐ │
│ │ PID │ Layer        │ Frame │ Progress │ Status          │ │
│ ├─────┼──────────────┼───────┼──────────┼─────────────────┤ │
│ │ 001 │ MASTER_BG_A  │ 15/20 │ ████░░░  │ Rendering       │ │
│ │ 002 │ MASTER_CHAR_A│ Queue │ ░░░░░░░  │ Waiting         │ │
│ │ 003 │ MASTER_FX_A  │ 5/10  │ ██░░░░░  │ Rendering       │ │
│ └─────┴──────────────┴───────┴──────────┴─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 **Data Flow Architecture**

### **Render Process Flow**
```
1. User Configuration → RenderConfig object
2. System Detection → Available resources
3. Scene Preparation → Temporary .ma files
4. Process Creation → mayapy subprocesses
5. Progress Monitoring → Real-time updates
6. Completion/Cleanup → File management
```

### **Communication Patterns**

#### **UI ↔ API Communication**
```python
# Signal-slot pattern for real-time updates
batch_api.render_started.connect(ui.on_render_started)
batch_api.progress_updated.connect(ui.on_progress_updated)
batch_api.render_completed.connect(ui.on_render_completed)
```

#### **API ↔ Subprocess Communication**
```python
# Pipe-based communication for process monitoring
process = subprocess.Popen([mayapy_path, render_script], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
```

## 🗄️ **Data Models**

### **Core Data Structures**

```python
@dataclass
class GPUInfo:
    device_id: int
    name: str
    memory_total: int
    memory_free: int
    compute_capability: Tuple[int, int]
    is_available: bool

@dataclass
class RenderConfig:
    layers: List[str]
    frame_range: str
    gpu_count: int
    cpu_threads: int
    render_mode: RenderMode  # SEPARATE or COMBINED
    output_settings: Dict[str, Any]

@dataclass
class RenderProcess:
    process_id: str
    layer_name: str
    frame_range: List[int]
    status: ProcessStatus
    progress: float
    start_time: datetime
    temp_file_path: str
    subprocess_handle: subprocess.Popen
```

## 🔧 **SIMPLIFIED Technical Implementation**

### **Core Workflow (Simple!)**
```
1. User clicks "Start Render"
2. Save current scene → temp/render_sceneName_timestamp_layer.ma
3. Launch Maya Render.exe with CUDA_VISIBLE_DEVICES=1
4. Capture stdout/stderr for real-time logs
5. Display progress in UI
6. Cleanup temp files when done
```

### **GPU Detection Implementation (Simple)**
```python
def detect_cuda_gpus() -> int:
    """Detect number of CUDA GPUs - simple version."""
    try:
        import pynvml
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        pynvml.nvmlShutdown()
        return gpu_count
    except:
        # Fallback: try nvidia-smi command
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '-L'],
                                  capture_output=True, text=True)
            return len([l for l in result.stdout.split('\n') if 'GPU' in l])
        except:
            return 0  # No CUDA GPUs found
```

### **Frame Range Parsing**
```python
def parse_frame_range(frame_string: str) -> List[int]:
    """Parse flexible frame range syntax."""
    frames = set()
    
    for part in frame_string.split(','):
        part = part.strip()
        
        if 'x' in part:  # Step syntax: "1-100x5"
            range_part, step = part.split('x')
            start, end = map(int, range_part.split('-'))
            step = int(step)
            
            # Always include first and last frames
            frames.add(start)
            frames.add(end)
            
            # Add stepped frames
            for frame in range(start, end + 1, step):
                frames.add(frame)
                
        elif '-' in part:  # Range syntax: "10-20"
            start, end = map(int, part.split('-'))
            frames.update(range(start, end + 1))
            
        else:  # Single frame: "5"
            frames.add(int(part))
    
    return sorted(list(frames))
```

### **Batch Render Execution (SIMPLIFIED - Using Maya Render.exe)**
```python
def start_batch_render(scene_file: str, layer: str, frames: str, gpu_id: int = 1):
    """Start batch render using Maya's native Render command."""
    import subprocess
    import platform
    import os

    # Detect platform
    is_windows = platform.system() == 'Windows'

    # Get Maya Render executable
    if is_windows:
        render_exe = r"C:\Program Files\Autodesk\Maya2024\bin\Render.exe"
    else:
        render_exe = "/usr/autodesk/maya2024/bin/Render"

    # Build command
    cmd = [
        render_exe,
        "-r", "redshift",           # Renderer
        "-rl", layer,               # Render layer
        "-s", frames.split('-')[0], # Start frame
        "-e", frames.split('-')[1] if '-' in frames else frames, # End frame
        scene_file
    ]

    # Set GPU environment variable
    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = str(gpu_id)

    # Execute render process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )

    return process
```

### **Real-time Log Capture (Simple)**
```python
def monitor_render_process(process: subprocess.Popen):
    """Monitor render process and capture logs in real-time."""
    while True:
        # Read stdout line by line
        line = process.stdout.readline()
        if not line:
            break

        # Parse Maya render output
        if "Rendering" in line:
            print(f"[RENDER] {line.strip()}")
        elif "Error" in line or "Warning" in line:
            print(f"[ERROR] {line.strip()}")
        else:
            print(f"[LOG] {line.strip()}")

        # Update UI (emit signal)
        log_signal.emit(line.strip())

    # Get return code
    return_code = process.wait()
    return return_code == 0
```

## 🔌 **External Integration (SIMPLIFIED)**

### **Command-Line Interface**
```bash
# Windows
python -m lrc_toolbox.cli.batch_render_cli --scene "shot001.ma" --layer "MASTER_BG_A" --frames "1-24" --gpu 1

# Linux
python -m lrc_toolbox.cli.batch_render_cli --scene "shot001.ma" --layer "MASTER_BG_A" --frames "1-24" --gpu 1
```

### **API Integration (Simple)**
```python
# From Nuke or other tools
from lrc_toolbox.core.batch_render_api import BatchRenderAPI

api = BatchRenderAPI()
success = api.render_layer(
    scene_file="shot001.ma",
    layer="MASTER_BG_A",
    frames="1-24",
    gpu_id=1
)
```

## 🖥️ **Platform Support**

### **Windows Support**
- ✅ Maya Render.exe path detection
- ✅ CUDA_VISIBLE_DEVICES environment variable
- ✅ Windows-style paths and commands
- ✅ PowerShell/CMD compatibility

### **Linux Support**
- ✅ Maya Render binary path detection
- ✅ CUDA_VISIBLE_DEVICES environment variable
- ✅ Linux-style paths and commands
- ✅ Bash/shell compatibility

### **Cross-Platform Implementation**
```python
import platform
import os

def get_maya_render_executable():
    """Get Maya Render executable for current platform."""
    system = platform.system()

    if system == 'Windows':
        return r"C:\Program Files\Autodesk\Maya2024\bin\Render.exe"
    elif system == 'Linux':
        return "/usr/autodesk/maya2024/bin/Render"
    else:
        raise NotImplementedError(f"Platform {system} not supported")
```

---

**Document Version:** 1.0  
**Last Updated:** 2024-10-14  
**Status:** Draft - Technical Review Required  
**Dependencies:** pynvml, Maya 2024+, CUDA Toolkit
