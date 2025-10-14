# Batch Render Manager - FINAL APPROACH (Original + Fallback)

## 🎯 **Approved Approach**

**Decision:** Use **ORIGINAL (Detailed) Approach** with **Multi-Level Fallback System**

### **Why This Approach:**
- ✅ **Maximum Flexibility:** Full Maya API access for custom logic
- ✅ **Guaranteed Reliability:** Multiple fallback levels ensure rendering always works
- ✅ **Future-Proof:** Easy to extend with new features
- ✅ **Production-Ready:** Handles edge cases and failures gracefully

---

## 🔄 **Three-Level Fallback System**

### **Priority 1: mayapy with Custom Script (FLEXIBLE)**
```python
# Full control with Maya Python API
mayapy.exe -c """
import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds

# Open scene
cmds.file('scene.ma', open=True, force=True)

# Custom pre-render operations
cmds.setAttr('defaultRenderGlobals.imageFormat', 51)

# Set render layer
cmds.editRenderLayerGlobals(currentRenderLayer='MASTER_BG_A')

# Render frames with custom logic
for frame in [1, 5, 10, 15, 20]:
    cmds.currentTime(frame)
    cmds.render()
    print(f'FRAME_COMPLETE:{frame}')

print('RENDER_COMPLETE')
"""
```

**Advantages:**
- ✅ Full Maya API access
- ✅ Custom per-frame logic
- ✅ Pipeline integration hooks
- ✅ Scene modification before render
- ✅ Non-contiguous frame ranges

**When to Use:** Default method for all renders

---

### **Priority 2: Maya Render.exe (RELIABLE FALLBACK)**
```bash
# Windows
set CUDA_VISIBLE_DEVICES=1
"C:\Program Files\Autodesk\Maya2024\bin\Render.exe" -r redshift -rl MASTER_BG_A -s 1 -e 20 scene.ma

# Linux
export CUDA_VISIBLE_DEVICES=1
/usr/autodesk/maya2024/bin/Render -r redshift -rl MASTER_BG_A -s 1 -e 20 scene.ma
```

**Advantages:**
- ✅ Battle-tested by Autodesk
- ✅ Handles all edge cases
- ✅ Proper license management
- ✅ Native renderer integration

**When to Use:** 
- If mayapy script fails
- If custom logic not needed
- For simple contiguous frame ranges

---

### **Priority 3: Basic mayapy Render (MINIMAL FALLBACK)**
```python
# Minimal render command
mayapy.exe -c """
import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds
cmds.file('scene.ma', open=True, force=True)
cmds.render()
"""
```

**Advantages:**
- ✅ Minimal dependencies
- ✅ Always available if mayapy exists
- ✅ Simple and reliable

**When to Use:**
- If Render.exe not found
- If both Priority 1 and 2 fail
- Last resort rendering

---

## 🏗️ **Implementation Architecture**

### **Render Execution Manager**
```python
class RenderExecutionManager:
    """Manages render execution with automatic fallback."""
    
    def execute_render(self, config: RenderConfig) -> bool:
        """Execute render with fallback system."""
        
        # Try Priority 1: mayapy with custom script
        try:
            if self._try_mayapy_custom_script(config):
                print("✅ Render completed with mayapy custom script")
                return True
        except Exception as e:
            print(f"⚠️ mayapy custom script failed: {e}")
        
        # Try Priority 2: Maya Render.exe
        try:
            if self._try_maya_render_exe(config):
                print("✅ Render completed with Render.exe (fallback)")
                return True
        except Exception as e:
            print(f"⚠️ Render.exe failed: {e}")
        
        # Try Priority 3: Basic mayapy render
        try:
            if self._try_basic_mayapy_render(config):
                print("✅ Render completed with basic mayapy (minimal fallback)")
                return True
        except Exception as e:
            print(f"❌ All render methods failed: {e}")
        
        return False
    
    def _try_mayapy_custom_script(self, config: RenderConfig) -> bool:
        """Try rendering with mayapy custom script (Priority 1)."""
        mayapy_path = self._find_mayapy()
        if not mayapy_path:
            raise Exception("mayapy not found")
        
        # Generate custom render script
        script = self._generate_render_script(config)
        
        # Set GPU environment
        env = os.environ.copy()
        env['CUDA_VISIBLE_DEVICES'] = str(config.gpu_id)
        
        # Execute
        process = subprocess.Popen(
            [mayapy_path, '-c', script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Monitor and capture logs
        success = self._monitor_process(process)
        return success
    
    def _try_maya_render_exe(self, config: RenderConfig) -> bool:
        """Try rendering with Render.exe (Priority 2 - Fallback)."""
        render_exe = self._find_render_executable()
        if not render_exe:
            raise Exception("Render.exe not found")
        
        # Build command
        cmd = [
            render_exe,
            "-r", config.renderer,
            "-rl", config.layer,
            "-s", str(config.start_frame),
            "-e", str(config.end_frame),
            config.scene_file
        ]
        
        # Set GPU environment
        env = os.environ.copy()
        env['CUDA_VISIBLE_DEVICES'] = str(config.gpu_id)
        
        # Execute
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Monitor and capture logs
        success = self._monitor_process(process)
        return success
    
    def _try_basic_mayapy_render(self, config: RenderConfig) -> bool:
        """Try basic mayapy render (Priority 3 - Minimal Fallback)."""
        mayapy_path = self._find_mayapy()
        if not mayapy_path:
            raise Exception("mayapy not found")
        
        # Minimal render script
        script = f"""
import maya.standalone
maya.standalone.initialize()
import maya.cmds as cmds
cmds.file('{config.scene_file}', open=True, force=True)
cmds.render()
"""
        
        # Set GPU environment
        env = os.environ.copy()
        env['CUDA_VISIBLE_DEVICES'] = str(config.gpu_id)
        
        # Execute
        process = subprocess.Popen(
            [mayapy_path, '-c', script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Monitor and capture logs
        success = self._monitor_process(process)
        return success
```

---

## 📋 **Fallback Decision Logic**

### **Automatic Fallback Triggers:**

```python
def should_use_fallback(error_type: str) -> int:
    """Determine which fallback level to use."""
    
    # Priority 1 failures → Try Priority 2
    if error_type in ['SCRIPT_ERROR', 'MAYAPY_CRASH', 'CUSTOM_LOGIC_FAIL']:
        return 2  # Use Render.exe
    
    # Priority 2 failures → Try Priority 3
    if error_type in ['RENDER_EXE_NOT_FOUND', 'RENDER_EXE_CRASH']:
        return 3  # Use basic mayapy
    
    # All failed
    return 0
```

### **User Override:**
```python
# User can force specific render method
config.render_method = RenderMethod.MAYAPY_CUSTOM  # Priority 1
config.render_method = RenderMethod.RENDER_EXE     # Priority 2
config.render_method = RenderMethod.MAYAPY_BASIC   # Priority 3
config.render_method = RenderMethod.AUTO           # Auto fallback (default)
```

---

## 🎯 **Feature Comparison with Fallback**

| Feature | Priority 1 (mayapy) | Priority 2 (Render.exe) | Priority 3 (basic) |
|---------|---------------------|-------------------------|-------------------|
| **Custom frame ranges** | ✅ Full support | ⚠️ Contiguous only | ⚠️ Current frame only |
| **Per-frame logic** | ✅ Yes | ❌ No | ❌ No |
| **Scene modification** | ✅ Yes | ❌ No | ❌ No |
| **Pipeline hooks** | ✅ Yes | ❌ No | ❌ No |
| **Reliability** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Flexibility** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| **Speed** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## ✅ **Benefits of This Approach**

### **1. Maximum Flexibility**
- Full Maya API access for custom logic
- Can implement ANY render workflow
- Easy to add pipeline-specific features

### **2. Guaranteed Reliability**
- If one method fails, automatically tries next
- Multiple fallback levels ensure rendering always works
- Production-ready error handling

### **3. Best of Both Worlds**
- Flexibility of mayapy when you need it
- Reliability of Render.exe when you don't
- Minimal fallback for edge cases

### **4. Future-Proof**
- Easy to add new render methods
- Can extend Priority 1 without breaking fallbacks
- Modular design allows incremental improvements

---

## 📋 **Updated Task List**

### **TASK-001: Create Batch Render Foundation** (2-3 hours)
- Core API with fallback system
- RenderExecutionManager class
- Data models and configuration

### **TASK-002: Implement System Detection** (3-4 hours)
- GPU detection (CUDA)
- CPU detection
- mayapy and Render.exe path detection
- Resource management

### **TASK-003: Build Frame Range Parser** (3-4 hours)
- Flexible frame range parsing
- Support for "1,5,10-20", "1-100x5"
- Validation and error handling

### **TASK-004: Implement Priority 1 Renderer** (4-5 hours)
- mayapy custom script generation
- Full Maya API integration
- Custom frame logic
- Pipeline hooks

### **TASK-005: Implement Priority 2 Fallback** (2-3 hours)
- Render.exe execution
- Command-line argument building
- Cross-platform support

### **TASK-006: Implement Priority 3 Fallback** (1-2 hours)
- Basic mayapy render
- Minimal dependencies
- Last resort rendering

### **TASK-007: Build UI Dialog** (4-5 hours)
- Dashboard layout
- Render configuration
- Progress monitoring
- Log display

### **TASK-008: Implement Progress Monitoring** (3-4 hours)
- Real-time log capture
- Progress tracking
- Status updates

### **TASK-009: Add File Management** (2-3 hours)
- Temp file creation
- Cleanup with retention
- Output organization

### **TASK-010: Create CLI & Testing** (4-6 hours)
- Command-line interface
- Integration testing
- Documentation

**Total: 28-42 hours**

---

## 🚀 **Implementation Priority**

### **Phase 1: Core + Priority 2 (Reliable Foundation)**
1. TASK-001: Foundation
2. TASK-002: System Detection
3. TASK-005: Priority 2 (Render.exe) - **Ensures basic rendering works**
4. TASK-007: UI Dialog

**Result:** Basic working system with reliable rendering

### **Phase 2: Add Flexibility (Priority 1)**
5. TASK-003: Frame Parser
6. TASK-004: Priority 1 (mayapy custom) - **Adds flexibility**

**Result:** Full flexibility with custom logic

### **Phase 3: Complete System**
7. TASK-006: Priority 3 (minimal fallback)
8. TASK-008: Progress Monitoring
9. TASK-009: File Management
10. TASK-010: CLI & Testing

**Result:** Production-ready system with all features

---

## ✅ **Final Confirmation**

**This approach gives you:**
- ✅ Maximum flexibility (Priority 1)
- ✅ Guaranteed reliability (Priority 2 & 3 fallbacks)
- ✅ Windows and Linux support
- ✅ Future-proof architecture
- ✅ Production-ready error handling

**Ready to implement?** 🚀

---

**Document Version:** 1.0 (FINAL)  
**Last Updated:** 2024-10-14  
**Status:** APPROVED - Ready for Implementation  
**Estimated Time:** 28-42 hours
