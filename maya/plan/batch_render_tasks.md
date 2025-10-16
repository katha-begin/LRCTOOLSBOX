# Batch Render Manager - Task Breakdown

## 📋 **Task Overview**

**Total Tasks:** 10  
**Estimated Time:** 32-46 hours  
**Development Phases:** 4  
**Completion Target:** 7-10 working days  

---

## 🏗️ **PHASE 1: Foundation & System Detection (8-12 hours)**

### **TASK-001: Create Batch Render Feature Foundation**
**Estimated Time:** 2-3 hours  
**Priority:** High  
**Dependencies:** None  

#### **Objectives:**
- Set up core module structure for batch rendering
- Create base classes and interfaces
- Establish data models and communication patterns
- Integration framework with LRC Toolbox

#### **Deliverables:**
- `maya/lrc_toolbox/core/batch_render_api.py` - Main API class
- `maya/lrc_toolbox/config/batch_render_defaults.py` - Configuration defaults
- Data models for RenderConfig, ProcessStatus, SystemInfo
- Signal-slot communication interfaces

#### **Acceptance Criteria:**
- [ ] BatchRenderAPI class created with core methods
- [ ] Data models defined with proper type hints
- [ ] Configuration system integrated
- [ ] Basic error handling implemented
- [ ] Unit tests for core classes

#### **Technical Notes:**
```python
# Core API structure
class BatchRenderAPI:
    def start_batch_render(self, config: RenderConfig) -> bool
    def stop_all_renders(self) -> bool
    def get_render_status(self) -> List[RenderStatus]
    def get_system_info(self) -> SystemInfo
```

---

### **TASK-002: Implement System Detection & Resource Management**
**Estimated Time:** 3-4 hours  
**Priority:** High  
**Dependencies:** TASK-001  

#### **Objectives:**
- Detect CUDA GPUs with memory information
- Detect CPU cores and threading capabilities
- Implement resource reservation for Maya session
- Create resource monitoring and allocation system

#### **Deliverables:**
- `maya/lrc_toolbox/core/system_detector.py` - Hardware detection
- `maya/lrc_toolbox/utils/gpu_utils.py` - GPU utilities
- Resource allocation and monitoring logic
- System info display data structures

#### **Acceptance Criteria:**
- [ ] CUDA GPU detection using pynvml
- [ ] CPU core and thread detection
- [ ] Resource reservation (1 GPU for Maya)
- [ ] Available resource calculation
- [ ] Error handling for missing CUDA/drivers
- [ ] Unit tests with mocked hardware

#### **Technical Notes:**
```python
# GPU detection implementation
def detect_cuda_gpus() -> List[GPUInfo]:
    import pynvml
    # Implementation with error handling
```

---

### **TASK-003: Build Frame Range Parser & Validation**
**Estimated Time:** 3-4 hours  
**Priority:** Medium  
**Dependencies:** TASK-001  

#### **Objectives:**
- Parse flexible frame range syntax
- Support steps with first/last frame inclusion
- Implement validation and error reporting
- Create comprehensive test coverage

#### **Deliverables:**
- `maya/lrc_toolbox/utils/frame_parser.py` - Frame parsing logic
- Validation functions with error messages
- Unit tests for all syntax variations
- Documentation for supported syntax

#### **Acceptance Criteria:**
- [ ] Parse comma-separated frames: "1,5,10"
- [ ] Parse ranges: "10-20"
- [ ] Parse steps: "1-100x5" with first/last inclusion
- [ ] Validate syntax and report errors
- [ ] Handle edge cases and invalid input
- [ ] 100% test coverage for parser

#### **Technical Notes:**
```python
# Supported syntax examples
"1,5,10-20" → [1, 5, 10, 11, 12, ..., 20]
"1-100x5" → [1, 6, 11, ..., 96, 100]  # Always include first/last
```

---

## 🔧 **PHASE 2: Core Functionality (12-16 hours)**

### **TASK-004: Create Render Layer Selection & Scene Preparation**
**Estimated Time:** 4-5 hours  
**Priority:** High  
**Dependencies:** TASK-001, TASK-003  

#### **Objectives:**
- Integrate with Maya Render Setup API
- Implement layer detection and selection
- Create scene file preparation for batch rendering
- Develop temporary file management

#### **Deliverables:**
- Render layer detection from Maya Render Setup
- Layer selection logic (individual vs all active)
- Scene preparation for subprocess rendering
- `maya/lrc_toolbox/utils/temp_file_manager.py`

#### **Acceptance Criteria:**
- [ ] Detect all render layers in current scene
- [ ] Support individual layer selection
- [ ] Support "all active layers" mode
- [ ] Create temporary scene files for rendering
- [ ] Unique filename generation
- [ ] Proper scene state preservation

#### **Technical Notes:**
```python
# Filename format
"render_{sceneName}_{timestamp}_{layerName}_{processId}.ma"
```

---

### **TASK-005: Develop Subprocess Management System**
**Estimated Time:** 4-6 hours  
**Priority:** High  
**Dependencies:** TASK-002, TASK-004  

#### **Objectives:**
- Create mayapy subprocess management
- Implement process monitoring and communication
- Handle resource allocation per process
- Develop process lifecycle management

#### **Deliverables:**
- `maya/lrc_toolbox/core/render_process_manager.py`
- `maya/lrc_toolbox/utils/render_subprocess.py`
- Process monitoring and status tracking
- Inter-process communication system

#### **Acceptance Criteria:**
- [ ] Create mayapy subprocesses for rendering
- [ ] Monitor process status and progress
- [ ] Handle process termination and cleanup
- [ ] Resource allocation per process
- [ ] Error capture and reporting
- [ ] Graceful process shutdown

#### **Technical Notes:**
```python
# Subprocess creation
process = subprocess.Popen([mayapy_path, render_script], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
```

---

### **TASK-006: Build Batch Render Dialog UI**
**Estimated Time:** 4-5 hours  
**Priority:** High  
**Dependencies:** TASK-001, TASK-002  

#### **Objectives:**
- Create main batch render dialog
- Implement dashboard-style layout
- Build system info and configuration panels
- Create active renders monitoring table

#### **Deliverables:**
- `maya/lrc_toolbox/ui/dialogs/batch_render_dialog.py`
- System info display widget
- Render configuration panel
- Active renders table with progress bars
- Control buttons and status indicators

#### **Acceptance Criteria:**
- [ ] Clean dashboard layout with table design
- [ ] System resource display (GPU/CPU status)
- [ ] Render layer selection interface
- [ ] Frame range input with validation
- [ ] Active renders table with progress
- [ ] Start/Stop/Cancel controls
- [ ] Real-time UI updates

#### **Technical Notes:**
```python
# UI layout structure
class BatchRenderDialog(QtWidgets.QDialog):
    - system_info_widget: SystemInfoWidget
    - render_config_widget: RenderConfigWidget  
    - active_renders_table: ActiveRendersTable
    - control_buttons: ControlButtonsWidget
```

---

## 📊 **PHASE 3: Monitoring & Integration (8-12 hours)**

### **TASK-007: Implement Progress Monitoring & Logging**
**Estimated Time:** 3-4 hours  
**Priority:** High  
**Dependencies:** TASK-005, TASK-006  

#### **Objectives:**
- Create real-time progress tracking
- Implement log capture and display
- Build process status management
- Develop UI update mechanisms

#### **Deliverables:**
- `maya/lrc_toolbox/ui/dialogs/render_progress_widget.py`
- Progress tracking and status updates
- Log monitoring and display system
- Real-time UI refresh mechanisms

#### **Acceptance Criteria:**
- [ ] Real-time progress updates per process
- [ ] Frame-by-frame progress tracking
- [ ] Comprehensive logging with timestamps
- [ ] Error capture and display
- [ ] Process status indicators
- [ ] Log filtering and search

#### **Technical Notes:**
```python
# Progress update signals
render_progress_updated.emit(process_id, frame, total_frames)
render_log_message.emit(timestamp, level, message)
```

---

### **TASK-008: Add File Management & Cleanup System**
**Estimated Time:** 2-3 hours  
**Priority:** Medium  
**Dependencies:** TASK-004, TASK-005  

#### **Objectives:**
- Implement temporary file lifecycle management
- Create cleanup with retention policy
- Handle output file organization
- Develop error recovery and cleanup

#### **Deliverables:**
- Enhanced `temp_file_manager.py` with cleanup
- Retention policy (keep latest 5 files)
- Output file organization
- Error recovery mechanisms

#### **Acceptance Criteria:**
- [ ] Automatic cleanup of temporary files
- [ ] Retain latest 5 files for debugging
- [ ] Proper cleanup on application exit
- [ ] Handle file conflicts and errors
- [ ] Output file organization
- [ ] Disk space monitoring

#### **Technical Notes:**
```python
# Cleanup policy
def cleanup_temp_files(keep_latest: int = 5):
    # Keep latest N files, remove older ones
```

---

### **TASK-009: Create Command-Line Interface & API**
**Estimated Time:** 3-5 hours  
**Priority:** Medium  
**Dependencies:** TASK-001, TASK-005  

#### **Objectives:**
- Build standalone CLI for external tools
- Create programmatic API design
- Implement JSON configuration support
- Enable integration with external tools (Nuke, etc.)

#### **Deliverables:**
- `maya/lrc_toolbox/cli/batch_render_cli.py`
- Command-line argument parsing
- JSON configuration file support
- API documentation and examples

#### **Acceptance Criteria:**
- [ ] Command-line interface with arguments
- [ ] JSON configuration file support
- [ ] Programmatic API for external tools
- [ ] Integration examples (Nuke, etc.)
- [ ] Error handling and validation
- [ ] Usage documentation

#### **Technical Notes:**
```bash
# CLI usage examples
mayapy -m lrc_toolbox.cli.batch_render_cli \
    --scene "shot001.ma" \
    --layers "MASTER_BG_A" \
    --frames "1-24"
```

---

## ✅ **PHASE 4: Testing & Documentation (4-6 hours)**

### **TASK-010: Integration Testing & Documentation**
**Estimated Time:** 4-6 hours  
**Priority:** High  
**Dependencies:** All previous tasks  

#### **Objectives:**
- Comprehensive end-to-end testing
- Performance testing under load
- Create user and developer documentation
- Integration with LRC Toolbox main window

#### **Deliverables:**
- Integration tests for complete workflows
- Performance benchmarks and optimization
- User documentation and tutorials
- Developer API documentation
- Integration with main LRC Toolbox UI

#### **Acceptance Criteria:**
- [ ] End-to-end workflow testing
- [ ] Error scenario validation
- [ ] Performance testing under load
- [ ] Maya stability during batch rendering
- [ ] External integration testing
- [ ] Complete user documentation
- [ ] Developer API documentation
- [ ] Integration with main window

#### **Technical Notes:**
```python
# Integration point in main_window.py
def _create_menu_bar(self):
    batch_render_action = QtWidgets.QAction("Batch Render Manager", self)
    batch_render_action.triggered.connect(self._open_batch_render_dialog)
```

---

## 📊 **Task Dependencies**

```
TASK-001 (Foundation)
├── TASK-002 (System Detection)
├── TASK-003 (Frame Parser)
└── TASK-004 (Layer Selection)
    └── TASK-005 (Subprocess Management)
        ├── TASK-006 (UI Dialog)
        ├── TASK-007 (Progress Monitoring)
        └── TASK-008 (File Management)
            └── TASK-009 (CLI & API)
                └── TASK-010 (Testing & Documentation)
```

## 🎯 **Completion Criteria**

### **Phase Completion Requirements:**
- [ ] **Phase 1:** System detection and parsing working
- [ ] **Phase 2:** Core rendering functionality operational
- [ ] **Phase 3:** Full UI and external integration complete
- [ ] **Phase 4:** Tested, documented, and integrated

### **Final Acceptance:**
- [ ] All 10 tasks completed with acceptance criteria met
- [ ] Integration testing passed
- [ ] Documentation complete
- [ ] Code review and quality standards met
- [ ] User acceptance testing successful

---

## 📅 **Implementation Schedule**

### **Week 1: Foundation & Core (Days 1-4)**
- **Day 1:** TASK-001 + TASK-002 (Foundation + System Detection)
- **Day 2:** TASK-003 + TASK-004 (Frame Parser + Layer Selection)
- **Day 3:** TASK-005 (Subprocess Management)
- **Day 4:** TASK-006 (UI Dialog)

### **Week 2: Integration & Testing (Days 5-7)**
- **Day 5:** TASK-007 + TASK-008 (Progress Monitoring + File Management)
- **Day 6:** TASK-009 (CLI & API)
- **Day 7:** TASK-010 (Testing & Documentation)

## 🔄 **Daily Deliverables**

### **Day 1 Deliverables:**
- Core API structure and data models
- CUDA GPU detection working
- Resource allocation system functional

### **Day 2 Deliverables:**
- Frame range parsing with all syntax support
- Render layer detection from Maya Render Setup
- Temporary file management system

### **Day 3 Deliverables:**
- mayapy subprocess creation and monitoring
- Process lifecycle management
- Resource allocation per process

### **Day 4 Deliverables:**
- Complete batch render dialog UI
- System info and configuration panels
- Active renders monitoring table

### **Day 5 Deliverables:**
- Real-time progress tracking
- Log capture and display system
- File cleanup with retention policy

### **Day 6 Deliverables:**
- Command-line interface functional
- External tool integration ready
- JSON configuration support

### **Day 7 Deliverables:**
- Complete integration testing
- User and developer documentation
- LRC Toolbox integration complete

---

**Document Version:** 1.0
**Last Updated:** 2024-10-14
**Status:** Ready for Implementation
**Next Action:** Create feature branch and begin TASK-001 implementation
