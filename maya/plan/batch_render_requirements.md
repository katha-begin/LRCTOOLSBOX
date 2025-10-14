# Batch Render Manager - Requirements Specification

## 📋 **Project Overview**

**Feature Name:** Batch Render Manager  
**Version:** 1.0.0  
**Target Framework:** LRC Toolbox v2.0  
**Development Approach:** UI-First with Extensible API  
**Primary Use Case:** Local batch rendering with GPU/CPU management from Maya GUI  

## 🎯 **Core Requirements**

### **R1: System Detection & Resource Management**
- **R1.1:** Auto-detect CUDA-compatible GPUs with memory information
- **R1.2:** Detect CPU cores and threading capabilities
- **R1.3:** Reserve 1 GPU for Maya session, allocate remaining for batch rendering
- **R1.4:** Configurable CPU thread allocation with system resource preservation
- **R1.5:** Real-time resource monitoring and availability display

### **R2: Render Layer Management**
- **R2.1:** Detect and list all render layers from Maya Render Setup
- **R2.2:** Support user selection of specific render layers
- **R2.3:** Support "All Active Layers" rendering mode
- **R2.4:** Separate rendering: Each selected layer renders independently
- **R2.5:** Combined rendering: All active layers render together in single process
- **R2.6:** Use current scene render settings and layer states (no overrides)

### **R3: Frame Range Processing**
- **R3.1:** Support comma-separated frame lists: "1,5,10,20"
- **R3.2:** Support frame ranges: "10-20", "1-100"
- **R3.3:** Support step rendering: "1-100x5" (every 5th frame)
- **R3.4:** Always include first and last frames when using steps
- **R3.5:** No negative frame number support
- **R3.6:** Frame range validation and error reporting

### **R4: Background Processing**
- **R4.1:** Use mayapy subprocess for background rendering
- **R4.2:** Multiple concurrent render processes based on available resources
- **R4.3:** Process isolation to prevent Maya session interference
- **R4.4:** Automatic scene file preparation for each render process
- **R4.5:** Process monitoring and status tracking

### **R5: User Interface**
- **R5.1:** Separate dialog window (not integrated into main tabs)
- **R5.2:** Clean dashboard design with table-based layout
- **R5.3:** System information display (GPU/CPU status)
- **R5.4:** Render configuration panel
- **R5.5:** Active renders monitoring table
- **R5.6:** Real-time logs monitor
- **R5.7:** Process control buttons (Start/Stop/Cancel)

### **R6: File Management**
- **R6.1:** Create temporary scene files for each render process
- **R6.2:** Unique filename format: `render_{sceneName}_{timestamp}_{layerName}_{processId}.ma`
- **R6.3:** Automatic cleanup of temporary files
- **R6.4:** Retain latest 5 temporary files for debugging
- **R6.5:** Follow current Maya render settings for output format/quality

### **R7: Progress Monitoring & Logging**
- **R7.1:** Real-time progress tracking per render process
- **R7.2:** Frame-by-frame progress updates
- **R7.3:** Comprehensive logging with timestamps
- **R7.4:** Error capture and display
- **R7.5:** Process status indicators (Waiting/Rendering/Complete/Error)

### **R8: Extensibility & Integration**
- **R8.1:** Command-line interface for external tool integration
- **R8.2:** Programmatic API for batch render execution
- **R8.3:** Support for external calls from Nuke, other tools
- **R8.4:** Standalone execution capability
- **R8.5:** JSON-based configuration for automation

## 🚫 **Non-Requirements (Out of Scope)**

### **NR1: Advanced Features**
- Network/distributed rendering
- Render farm integration
- Custom render engine plugins
- Advanced render settings override
- Render queue persistence across Maya sessions

### **NR2: Platform Support**
- macOS/Linux support (Windows only initially)
- Non-CUDA GPU support (OpenCL, Metal)
- Cloud rendering integration
- Docker containerization

### **NR3: UI Features**
- Render preview/thumbnails
- Advanced scheduling
- Email notifications
- Render statistics/analytics
- Custom UI themes

## 📊 **Performance Requirements**

### **P1: Resource Management**
- **P1.1:** Maya session must remain responsive during batch rendering
- **P1.2:** GPU memory usage monitoring and allocation
- **P1.3:** CPU usage should not exceed 80% of available cores
- **P1.4:** Maximum 4 concurrent render processes (configurable)

### **P2: Response Times**
- **P2.1:** UI updates within 100ms for user interactions
- **P2.2:** Process status updates every 2 seconds
- **P2.3:** Log updates in real-time (< 500ms delay)
- **P2.4:** System detection within 5 seconds on startup

### **P3: Reliability**
- **P3.1:** Graceful handling of process failures
- **P3.2:** Automatic recovery from temporary file conflicts
- **P3.3:** Proper cleanup on unexpected shutdown
- **P3.4:** Error logging and user notification

## 🔒 **Security & Safety Requirements**

### **S1: File System Safety**
- **S1.1:** Temporary files created in designated temp directory only
- **S1.2:** No modification of original scene files
- **S1.3:** Proper file locking to prevent conflicts
- **S1.4:** Safe cleanup without affecting user data

### **S2: Process Safety**
- **S2.1:** Subprocess isolation from Maya main process
- **S2.2:** Resource limits to prevent system overload
- **S2.3:** Graceful termination of background processes
- **S2.4:** No elevation of privileges required

## 🧪 **Testing Requirements**

### **T1: Unit Testing**
- System detection functions
- Frame range parsing
- File management operations
- Resource allocation logic

### **T2: Integration Testing**
- Maya API integration
- Subprocess communication
- UI responsiveness during rendering
- Multi-process coordination

### **T3: User Acceptance Testing**
- Complete render workflows
- Error handling scenarios
- Resource management under load
- CLI/API functionality

## 📈 **Success Criteria**

### **Primary Success Metrics**
1. **Functionality:** Successfully render multiple layers/frames in background
2. **Performance:** Maya remains responsive during batch operations
3. **Reliability:** 95% success rate for render job completion
4. **Usability:** Intuitive UI requiring minimal user training

### **Secondary Success Metrics**
1. **Extensibility:** External tools can successfully call batch render API
2. **Resource Efficiency:** Optimal GPU/CPU utilization without system overload
3. **Error Recovery:** Graceful handling of 90% of error scenarios
4. **Documentation:** Complete user and developer documentation

## 🔄 **Future Enhancements (Post-v1.0)**

### **Phase 2 Features**
- CPU-based rendering support (Arnold CPU, Maya Software)
- Advanced frame range syntax (negative frames, complex patterns)
- Render queue persistence and scheduling
- Network rendering preparation

### **Phase 3 Features**
- Multi-platform support (macOS, Linux)
- Render farm integration hooks
- Advanced monitoring and analytics
- Custom render engine plugins

---

**Document Version:** 1.0  
**Last Updated:** 2024-10-14  
**Status:** Draft - Pending Approval  
**Next Review:** Upon implementation completion
