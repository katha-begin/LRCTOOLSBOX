# Batch Render Manager - Troubleshooting Guide

## Quick Diagnostic Tests

Run these test scripts in Maya Script Editor to diagnose issues:

### Test GPU Detection
```python
from lrc_toolbox.tests.test_gpu_detection import test_gpu_detection
test_gpu_detection()
```

### Test Render Layer Detection
```python
from lrc_toolbox.tests.test_render_layer_detection import test_render_layer_detection
test_render_layer_detection()
```

---

## Issue 1: "No CUDA GPUs Detected"

### Symptoms
- UI shows "No CUDA GPUs detected (CPU rendering only)"
- GPU dropdown shows "CPU Rendering (No GPU)"
- You know you have a GPU installed

### Possible Causes & Solutions

#### Cause 1: pynvml Library Not Installed
**Check:**
```python
import pynvml  # If this fails, pynvml is not installed
```

**Solution:**
```bash
pip install pynvml
```

#### Cause 2: nvidia-smi Not in PATH
**Check:**
```bash
nvidia-smi
```

**Solution (Windows):**
1. Find nvidia-smi.exe location (usually `C:\Windows\System32\`)
2. Add to PATH environment variable
3. Restart Maya

**Solution (Linux):**
```bash
export PATH=$PATH:/usr/bin
```

#### Cause 3: NVIDIA Drivers Not Installed
**Check:**
- Open NVIDIA Control Panel
- Check Device Manager for GPU

**Solution:**
- Install latest NVIDIA drivers from nvidia.com
- Restart computer

#### Cause 4: GPU Not CUDA-Compatible
**Check:**
- Only NVIDIA GPUs with CUDA support are detected
- AMD/Intel GPUs won't be detected

**Solution:**
- Use CPU rendering mode
- Or upgrade to NVIDIA GPU

### Diagnostic Output
Run the GPU detection test and look for:
```
[TEST 1] Checking pynvml library...
  ✓ pynvml is installed
  ✓ pynvml detected 1 GPU(s)
    GPU 0: NVIDIA GeForce RTX 3090 (24.0 GB)
```

If you see errors, follow the solutions above.

---

## Issue 2: "No Render Setup Layers Found"

### Symptoms
- UI shows "No Render Setup layers found"
- Layer dropdown is empty
- You know you have layers in Render Setup

### Possible Causes & Solutions

#### Cause 1: Layers Are Disabled
**Check:**
1. Open Render Setup window
2. Look for layers in the list
3. Check if "Renderable" checkbox is unchecked

**Solution:**
1. Select each layer
2. Check the "Renderable" checkbox
3. Click "Refresh" in Batch Render UI

#### Cause 2: Using Legacy Render Layers
**Check:**
- Are you using the old "Render Layers" system?
- Batch Render only works with "Render Setup" (the new system)

**Solution:**
1. Open **Render Setup** window (not Render Layers)
2. Create layers in Render Setup
3. Migrate from legacy render layers if needed

#### Cause 3: get_all_layers Function Missing
**Check:**
```python
from lrc_toolbox.utils.render_layers import get_all_layers
layers = get_all_layers()
print(layers)  # Should show your layers
```

**Solution:**
- This was fixed in the latest commit
- Make sure you have the latest code

#### Cause 4: Render Setup Not Available
**Check:**
```python
from lrc_toolbox.utils.render_layers import is_available
print(is_available())  # Should be True
```

**Solution:**
- Make sure Render Setup is enabled in Maya
- Check Maya version (Render Setup available in Maya 2016.5+)

### Diagnostic Output
Run the render layer detection test and look for:
```
[TEST 2] Listing layers using Maya Render Setup API...
  Found 4 total layers:
    - defaultRenderLayer [DEFAULT]
    - MASTER_BG_A [ENABLED]
    - MASTER_CHAR_A [ENABLED]
    - MASTER_FX_A [ENABLED]
```

If you see 0 layers or all DISABLED, follow solutions above.

---

## Issue 3: Layers Detected But Not Showing in UI

### Symptoms
- Test script shows layers exist
- UI dropdown is still empty

### Solution
1. Click "Refresh" button next to layer dropdown
2. Check Maya Script Editor for errors
3. Restart LRC Toolbox:
   ```python
   from lrc_toolbox import main
   main.show()
   ```

---

## Issue 4: GPU Shows "0" Instead of Actual GPU

### Symptoms
- UI shows "GPU 0" but you expected different numbering

### Explanation
This is **CORRECT** behavior:
- GPU numbering starts at 0 (not 1)
- GPU 0 = First GPU
- GPU 1 = Second GPU
- etc.

**Single GPU System:**
- You have 1 GPU
- It's numbered GPU 0
- This is normal!

**Multi-GPU System:**
- GPU 0 = Reserved for Maya
- GPU 1+ = Available for batch

---

## Common Error Messages

### "pynvml not available, trying nvidia-smi"
**Meaning:** pynvml library not installed, falling back to nvidia-smi  
**Action:** Install pynvml: `pip install pynvml`

### "nvidia-smi not found"
**Meaning:** nvidia-smi command not in PATH  
**Action:** Add NVIDIA driver folder to PATH

### "No Render Setup layers found. Please create layers in Render Setup first."
**Meaning:** No enabled layers in Render Setup  
**Action:** Open Render Setup, create/enable layers

### "Failed to get render layers from Render Setup"
**Meaning:** Error accessing Render Setup API  
**Action:** Check Maya Script Editor for detailed error

---

## Step-by-Step Troubleshooting

### For GPU Issues:

1. **Run GPU Detection Test**
   ```python
   from lrc_toolbox.tests.test_gpu_detection import test_gpu_detection
   test_gpu_detection()
   ```

2. **Check Test Results**
   - TEST 1: pynvml status
   - TEST 2: nvidia-smi status
   - TEST 3: LRC Toolbox detection
   - TEST 4: System Detector

3. **Follow Solutions**
   - If TEST 1 fails: Install pynvml
   - If TEST 2 fails: Fix nvidia-smi PATH
   - If TEST 3 fails: Check LRC Toolbox installation
   - If TEST 4 fails: Check system detector code

### For Render Layer Issues:

1. **Run Render Layer Detection Test**
   ```python
   from lrc_toolbox.tests.test_render_layer_detection import test_render_layer_detection
   test_render_layer_detection()
   ```

2. **Check Test Results**
   - TEST 1: Render Setup availability
   - TEST 2: Maya API layer listing
   - TEST 3: list_layers() function
   - TEST 4: get_all_layers() function
   - TEST 5: ScenePreparation detection
   - TEST 6: Layer enabled status

3. **Follow Solutions**
   - If TEST 1 fails: Render Setup not available
   - If TEST 2 shows 0 layers: Create layers in Render Setup
   - If TEST 2 shows layers but TEST 5 shows 0: Layers are disabled
   - If TEST 6 shows DISABLED: Enable layers in Render Setup

---

## Getting Help

If issues persist after following this guide:

1. **Collect Information:**
   - Run both diagnostic tests
   - Copy full output
   - Note Maya version
   - Note OS (Windows/Linux)
   - Note GPU model

2. **Check Logs:**
   - Maya Script Editor output
   - LRC Toolbox log messages
   - Any error messages

3. **Provide Details:**
   - What you tried
   - What you expected
   - What actually happened
   - Test script output

---

## Quick Reference

### GPU Detection Requirements
- ✅ NVIDIA GPU with CUDA support
- ✅ NVIDIA drivers installed
- ✅ pynvml library OR nvidia-smi in PATH
- ✅ LRC Toolbox properly installed

### Render Layer Requirements
- ✅ Maya Render Setup (not legacy render layers)
- ✅ Layers created in Render Setup window
- ✅ Layers marked as "Renderable"
- ✅ LRC Toolbox properly installed

### Test Scripts Location
```
maya/lrc_toolbox/tests/test_gpu_detection.py
maya/lrc_toolbox/tests/test_render_layer_detection.py
```

### Import and Run
```python
# GPU Test
from lrc_toolbox.tests.test_gpu_detection import test_gpu_detection
test_gpu_detection()

# Render Layer Test
from lrc_toolbox.tests.test_render_layer_detection import test_render_layer_detection
test_render_layer_detection()
```

---

**Remember:** Run the diagnostic tests first! They will tell you exactly what's wrong.

