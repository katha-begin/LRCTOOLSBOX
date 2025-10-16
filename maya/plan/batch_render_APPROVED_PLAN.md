# Batch Render Manager - APPROVED IMPLEMENTATION PLAN ✅

## 🎯 **APPROVED APPROACH**

**Decision:** Original (Detailed) Approach with **Three-Level Fallback System**

---

## 🔄 **Three-Level Fallback System**

```
┌─────────────────────────────────────────────────────────────┐
│                    START RENDER REQUEST                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PRIORITY 1: mayapy with Custom Script (FLEXIBLE)          │
│  ✅ Full Maya API access                                    │
│  ✅ Custom per-frame logic                                  │
│  ✅ Pipeline integration                                    │
│  ✅ Scene modification                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓ (if fails)
┌─────────────────────────────────────────────────────────────┐
│  PRIORITY 2: Maya Render.exe (RELIABLE FALLBACK)           │
│  ✅ Battle-tested by Autodesk                               │
│  ✅ Handles edge cases                                      │
│  ✅ Proper license management                               │
│  ✅ Native renderer integration                             │
└─────────────────────────────────────────────────────────────┘
                            ↓ (if fails)
┌─────────────────────────────────────────────────────────────┐
│  PRIORITY 3: Basic mayapy Render (MINIMAL FALLBACK)        │
│  ✅ Minimal dependencies                                    │
│  ✅ Always available                                        │
│  ✅ Last resort guarantee                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    RENDER COMPLETE ✅                        │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ **Key Benefits**

### **1. Maximum Flexibility**
- ✅ Full Maya Python API access
- ✅ Custom render logic per frame
- ✅ Pipeline integration hooks
- ✅ Scene modification before render
- ✅ Non-contiguous frame ranges (1,5,10,20)

### **2. Guaranteed Reliability**
- ✅ Three fallback levels ensure rendering ALWAYS works
- ✅ Automatic fallback on failure
- ✅ Production-ready error handling
- ✅ Battle-tested Render.exe as backup

### **3. Platform Support**
- ✅ Windows support (Render.exe, mayapy.exe)
- ✅ Linux support (Render, mayapy)
- ✅ Cross-platform GPU control (CUDA_VISIBLE_DEVICES)

### **4. Future-Proof**
- ✅ Easy to extend Priority 1 with new features
- ✅ Fallbacks ensure backward compatibility
- ✅ Modular architecture for incremental improvements

---

## 📋 **Implementation Tasks (10 Tasks, 28-42 hours)**

### **Phase 1: Core Foundation (8-12 hours)**

**TASK-001: Create Batch Render Foundation** (2-3 hours)
- Core API with fallback system
- RenderExecutionManager class
- Data models (RenderConfig, ProcessStatus, etc.)
- Signal-slot communication

**TASK-002: Implement System Detection** (3-4 hours)
- CUDA GPU detection
- CPU core detection
- mayapy path detection
- Render.exe path detection
- Resource allocation management

**TASK-003: Build Frame Range Parser** (3-4 hours)
- Parse "1,5,10-20" syntax
- Parse "1-100x5" (step) syntax
- Always include first/last frames
- Validation and error handling

---

### **Phase 2: Render Execution (9-13 hours)**

**TASK-004: Implement Priority 1 Renderer (mayapy custom)** (4-5 hours)
- Custom script generation
- Full Maya API integration
- Per-frame custom logic
- Pipeline hooks (pre/post render)
- Non-contiguous frame support

**TASK-005: Implement Priority 2 Fallback (Render.exe)** (2-3 hours)
- Render.exe command building
- Cross-platform support (Windows/Linux)
- GPU control with CUDA_VISIBLE_DEVICES
- Contiguous frame range support

**TASK-006: Implement Priority 3 Fallback (basic mayapy)** (1-2 hours)
- Minimal render script
- Last resort rendering
- Simple and reliable

**TASK-007: Subprocess Management** (2-3 hours)
- Process creation and monitoring
- Real-time log capture
- Process lifecycle management
- Graceful termination

---

### **Phase 3: UI & Monitoring (7-11 hours)**

**TASK-008: Build Batch Render Dialog UI** (4-5 hours)
- Dashboard layout
- System info display (GPU/CPU)
- Render configuration panel
- Layer selection
- Frame range input
- Active renders table
- Control buttons

**TASK-009: Implement Progress Monitoring & Logging** (3-4 hours)
- Real-time progress tracking
- Log capture and display
- Process status updates
- Error reporting

---

### **Phase 4: Integration & Testing (4-6 hours)**

**TASK-010: File Management, CLI & Testing** (4-6 hours)
- Temporary file management
- Cleanup with retention (keep latest 5)
- Command-line interface
- Integration with LRC Toolbox
- End-to-end testing
- Documentation

---

## 🏗️ **Module Structure**

```
maya/lrc_toolbox/
├── core/
│   ├── batch_render_api.py              # Main API orchestration
│   ├── render_execution_manager.py      # Fallback system manager
│   ├── system_detector.py               # GPU/CPU detection
│   └── render_process_manager.py        # Subprocess management
├── ui/dialogs/
│   ├── batch_render_dialog.py           # Main UI dialog
│   └── render_progress_widget.py        # Progress monitoring
├── utils/
│   ├── gpu_utils.py                     # CUDA utilities
│   ├── frame_parser.py                  # Frame range parsing
│   ├── render_subprocess.py             # Process wrapper
│   └── temp_file_manager.py             # File lifecycle
├── cli/
│   └── batch_render_cli.py              # Command-line interface
└── config/
    └── batch_render_defaults.py         # Configuration
```

---

## 🎯 **Core Features**

### **Render Execution:**
- ✅ Priority 1: mayapy custom script (flexible)
- ✅ Priority 2: Render.exe fallback (reliable)
- ✅ Priority 3: Basic mayapy fallback (minimal)
- ✅ Automatic fallback on failure
- ✅ GPU control (reserve GPU 0 for Maya, use GPU 1 for batch)

### **Frame Range Support:**
- ✅ Comma-separated: "1,5,10,20"
- ✅ Ranges: "10-20"
- ✅ Steps: "1-100x5" (always include first/last)
- ✅ Combined: "1,10-20,50,60-70x2"
- ✅ Non-contiguous patterns

### **Render Layer Support:**
- ✅ Individual layer selection
- ✅ All active layers mode
- ✅ Separate rendering (each layer independent)
- ✅ Combined rendering (all layers together)

### **File Management:**
- ✅ Temp files: `render_{sceneName}_{timestamp}_{layer}_{pid}.ma`
- ✅ Automatic cleanup
- ✅ Keep latest 5 files for debugging
- ✅ Output follows current render settings

### **Monitoring:**
- ✅ Real-time progress tracking
- ✅ Frame-by-frame updates
- ✅ Comprehensive logging
- ✅ Error capture and display
- ✅ Process status indicators

### **External Integration:**
- ✅ Command-line interface
- ✅ Programmatic API
- ✅ JSON configuration
- ✅ Nuke/external tool integration

---

## 📅 **Implementation Schedule**

### **Week 1: Foundation & Core (Days 1-4)**
- **Day 1:** TASK-001 + TASK-002 (Foundation + System Detection)
- **Day 2:** TASK-003 + TASK-005 (Frame Parser + Priority 2 Fallback)
- **Day 3:** TASK-004 (Priority 1 - mayapy custom)
- **Day 4:** TASK-006 + TASK-007 (Priority 3 + Subprocess Management)

### **Week 2: UI & Integration (Days 5-7)**
- **Day 5:** TASK-008 (UI Dialog)
- **Day 6:** TASK-009 (Progress Monitoring)
- **Day 7:** TASK-010 (File Management, CLI, Testing)

---

## 🚀 **Implementation Strategy**

### **Phase 1: Reliable Foundation First**
1. Implement Priority 2 (Render.exe) first
2. Ensure basic rendering works reliably
3. Test on Windows and Linux

### **Phase 2: Add Flexibility**
4. Implement Priority 1 (mayapy custom)
5. Add custom logic and pipeline hooks
6. Test advanced features

### **Phase 3: Complete System**
7. Add Priority 3 (minimal fallback)
8. Implement UI and monitoring
9. Add CLI and external integration
10. Complete testing and documentation

---

## ✅ **Success Criteria**

### **Functional:**
- [ ] All three render priorities working
- [ ] Automatic fallback on failure
- [ ] GPU control (GPU 0 for Maya, GPU 1 for batch)
- [ ] Real-time progress and logs
- [ ] Windows and Linux support

### **Performance:**
- [ ] Maya remains responsive during batch rendering
- [ ] UI updates within 100ms
- [ ] Proper GPU/CPU resource allocation
- [ ] <80% CPU usage during rendering

### **Reliability:**
- [ ] >95% render completion rate
- [ ] Graceful error handling
- [ ] No Maya session crashes
- [ ] Automatic recovery from failures

---

## 🎉 **Ready to Implement!**

**All planning complete:**
- ✅ Requirements defined
- ✅ Architecture designed
- ✅ Fallback system specified
- ✅ Tasks broken down
- ✅ Timeline estimated

**Next Steps:**
1. Create feature branch: `feature/batch-render-manager`
2. Begin TASK-001: Create Batch Render Foundation
3. Follow phase-by-phase implementation
4. Test each component thoroughly

---

**Document Version:** 1.0 (FINAL APPROVED)  
**Last Updated:** 2024-10-14  
**Status:** ✅ APPROVED - Ready for Implementation  
**Estimated Completion:** 28-42 hours (7-10 working days)
