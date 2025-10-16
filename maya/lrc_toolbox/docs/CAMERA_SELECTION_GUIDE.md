# Camera Selection in Maya Batch Rendering

## 🎥 How Maya Chooses Which Camera to Render

### TL;DR - Quick Answer

**Render.exe uses the RENDERABLE CAMERA attribute, NOT the active viewport camera.**

---

## 📋 Detailed Investigation

### Question
> "How does render choose camera to render? Is it use renderable camera from render setting or active viewport?"

### Answer

**Maya batch rendering (Render.exe) uses:**
1. ✅ **Renderable camera attribute** (`camera.renderable = True`)
2. ❌ **NOT the active viewport camera**
3. ❌ **NOT from render settings** (no camera stored in render globals)

---

## 🔍 How It Works

### 1. Renderable Camera Attribute

Each camera in Maya has a `.renderable` attribute:

```python
import maya.cmds as cmds

# Check if camera is renderable
is_renderable = cmds.getAttr("renderCam.renderable")

# Set camera as renderable
cmds.setAttr("renderCam.renderable", True)

# Disable camera from rendering
cmds.setAttr("renderCam.renderable", False)
```

**Location in Maya UI:**
- Select camera
- Open Attribute Editor
- Go to camera shape tab (e.g., `renderCamShape`)
- Look for **"Renderable"** checkbox

---

### 2. Active Viewport Camera (NOT USED)

The camera you see in the viewport is **ONLY for interactive viewing**.

**Batch rendering IGNORES:**
- Which viewport is active
- Which camera you're looking through
- Which panel has focus

**Example:**
```
Viewport shows: persp
Renderable camera: renderCam
Batch render uses: renderCam ✅ (not persp)
```

---

### 3. Multiple Renderable Cameras

**Problem:**
If multiple cameras have `renderable=True`, Render.exe will use the **FIRST** one it finds.

**Order is unpredictable!** It depends on:
- Scene file order
- Maya's internal camera list
- NOT alphabetical or creation order

**Solution:**
Always ensure **ONLY ONE** camera is renderable.

---

## 🛠️ How to Control Camera Selection

### Method 1: Set Renderable Attribute (Recommended)

**Before batch rendering:**

```python
import maya.cmds as cmds

# Disable all cameras
all_cameras = cmds.ls(type='camera')
for cam in all_cameras:
    cmds.setAttr(f"{cam}.renderable", False)

# Enable only the camera you want
cmds.setAttr("renderCamShape.renderable", True)
```

**Helper function:**

```python
def ensure_single_renderable_camera(camera_name):
    """Ensure only specified camera is renderable."""
    # Disable all
    all_cameras = cmds.ls(type='camera')
    for cam in all_cameras:
        cmds.setAttr(f"{cam}.renderable", False)
    
    # Enable specified camera
    shapes = cmds.listRelatives(camera_name, shapes=True, type='camera')
    if shapes:
        cmds.setAttr(f"{shapes[0]}.renderable", True)
        print(f"Set {camera_name} as renderable camera")

# Usage
ensure_single_renderable_camera("renderCam")
```

---

### Method 2: Use -cam Flag (Override)

**Command line flag:**

```bash
Render.exe -r redshift -rl MASTER_BG_A -cam renderCam -s 1 -e 10 scene.ma
```

**Advantages:**
- ✅ Overrides renderable attribute
- ✅ Explicit camera selection
- ✅ No need to modify scene file

**Disadvantages:**
- ❌ Requires knowing camera name
- ❌ Must add flag to every render command
- ❌ Can't use with AUTO mode (scene must have correct settings)

---

## 📊 Comparison Table

| Method | Uses Renderable Attr | Uses Viewport | Uses -cam Flag | Priority |
|--------|---------------------|---------------|----------------|----------|
| **Render.exe (default)** | ✅ Yes | ❌ No | ❌ No | 1 |
| **Render.exe -cam** | ❌ No (overridden) | ❌ No | ✅ Yes | 2 |
| **Interactive Render** | ⚠️ Optional | ✅ Yes | ❌ No | N/A |

---

## 🎯 Best Practices

### 1. Always Set Renderable Camera

**Before batch rendering:**
```python
# In your scene setup
ensure_single_renderable_camera("renderCam")
cmds.file(save=True)
```

### 2. Verify Camera Before Rendering

**Check which camera will render:**
```python
def get_renderable_cameras():
    """Get list of renderable cameras."""
    cameras = []
    for cam in cmds.ls(type='camera'):
        if cmds.getAttr(f"{cam}.renderable"):
            transform = cmds.listRelatives(cam, parent=True, type='transform')
            if transform:
                cameras.append(transform[0])
    return cameras

# Check before rendering
renderable = get_renderable_cameras()
if len(renderable) == 0:
    print("ERROR: No renderable camera!")
elif len(renderable) > 1:
    print(f"WARNING: Multiple renderable cameras: {renderable}")
else:
    print(f"OK: Renderable camera: {renderable[0]}")
```

### 3. Include in Shot Setup

**Add to your shot setup workflow:**
```python
def setup_shot_for_rendering(shot_node, camera_name="renderCam"):
    """Complete shot setup including camera."""
    # ... existing shot setup code ...
    
    # Ensure correct camera is renderable
    ensure_single_renderable_camera(camera_name)
    
    # Save scene
    cmds.file(save=True)
    
    print(f"Shot ready for rendering with camera: {camera_name}")
```

---

## 🚨 Common Issues

### Issue 1: Wrong Camera Renders

**Symptom:**
Batch render uses different camera than expected.

**Cause:**
Multiple cameras have `renderable=True`, or wrong camera is renderable.

**Solution:**
```python
# Check which cameras are renderable
renderable = get_renderable_cameras()
print(f"Renderable cameras: {renderable}")

# Fix: Set correct camera
ensure_single_renderable_camera("renderCam")
```

---

### Issue 2: "No Renderable Camera" Error

**Symptom:**
Render fails with "No renderable camera found" error.

**Cause:**
All cameras have `renderable=False`.

**Solution:**
```python
# Enable your render camera
cmds.setAttr("renderCamShape.renderable", True)
```

---

### Issue 3: Viewport Camera vs Render Camera

**Symptom:**
"I'm looking through renderCam but it renders from persp!"

**Cause:**
Viewport camera ≠ Renderable camera

**Solution:**
```python
# Viewport camera (for viewing)
active_cam = cmds.modelPanel("modelPanel4", query=True, camera=True)
print(f"Viewing through: {active_cam}")

# Renderable camera (for batch rendering)
renderable = get_renderable_cameras()
print(f"Will render from: {renderable}")

# Make them match
ensure_single_renderable_camera(active_cam)
```

---

## 🔧 Integration with LRC Toolbox

### Current Implementation

The batch render manager **does NOT** currently set camera selection.

**It assumes:**
- Scene file has correct renderable camera set
- Only one camera is renderable
- User has configured camera before batch rendering

### Potential Enhancement

**Option 1: Add camera selector to UI**
```python
# In batch_render_widget.py
camera_combo = QComboBox()
camera_combo.addItems(get_renderable_cameras())
```

**Option 2: Add -cam flag support**
```python
# In render_execution_manager.py
if config.camera:
    command.extend(["-cam", config.camera])
```

**Option 3: Auto-verify before rendering**
```python
# In batch_render_api.py
def start_batch_render(self, config):
    # Verify camera
    renderable = get_renderable_cameras()
    if len(renderable) != 1:
        raise RuntimeError(f"Expected 1 renderable camera, found {len(renderable)}")
    
    # Continue with render...
```

---

## 📝 Summary

### Key Takeaways

1. ✅ **Render.exe uses `camera.renderable` attribute**
2. ❌ **NOT the active viewport camera**
3. ⚠️ **Only ONE camera should be renderable**
4. 🔧 **Use `-cam` flag to override**
5. 📋 **Always verify camera before batch rendering**

### Recommended Workflow

```python
# 1. Set up shot
setup_shot_for_rendering(shot_node, camera_name="renderCam")

# 2. Verify camera
renderable = get_renderable_cameras()
assert len(renderable) == 1, f"Expected 1 camera, found {len(renderable)}"

# 3. Start batch render
api.start_batch_render(config)
```

---

## 🧪 Testing

Run the test script to verify camera selection in your scene:

```python
# In Maya Script Editor
exec(open("maya/lrc_toolbox/tests/test_camera_selection.py").read())
```

This will show:
- All cameras in scene
- Which cameras are renderable
- Active viewport camera
- Recommendations

---

**Document Version:** 1.0  
**Last Updated:** October 2025  
**Related Files:**
- `tests/test_camera_selection.py` - Test script
- `core/render_execution_manager.py` - Render command builder
- `core/batch_render_api.py` - Batch render API

