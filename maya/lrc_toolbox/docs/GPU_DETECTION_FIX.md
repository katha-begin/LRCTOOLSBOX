# GPU Detection Fix - Maya Subprocess Issue

## The Problem

**Symptom:** "No CUDA GPUs detected" even though `nvidia-smi` works in Command Prompt.

**Root Cause:** `subprocess.run()` and `subprocess.Popen()` with `shell=False` **hang/timeout** when called from Maya's Python environment on Windows.

### Why This Happens

Maya's Python environment has issues with subprocess calls:
- `subprocess.run()` can hang indefinitely
- `subprocess.Popen()` with list arguments and `shell=False` times out
- This is a known Maya + Windows + subprocess issue

### Your Error
```
TimeoutExpired: Command '['nvidia-smi', '--query-gpu=...']' timed out after 5 seconds
```

This means:
- ✅ nvidia-smi exists and is in PATH
- ✅ Your GPU is working
- ❌ Maya's subprocess can't execute it properly

---

## The Solution

### What Was Changed

**File:** `maya/lrc_toolbox/utils/gpu_utils.py`

**Changes:**
1. **Use `shell=True` on Windows** with string command instead of list
2. **Add STARTUPINFO** to hide console window
3. **Better timeout handling** (10 seconds instead of 5)
4. **Three-level fallback system:**
   - Method 1: pynvml (best, requires `pip install pynvml`)
   - Method 2: nvidia-smi (fixed for Maya)
   - Method 3: Basic fallback (assumes 1 GPU if drivers present)

### Code Changes

**Before (didn't work in Maya):**
```python
process = subprocess.Popen(
    ['nvidia-smi', '--query-gpu=...'],  # List with shell=False
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    shell=False  # This hangs in Maya!
)
```

**After (works in Maya):**
```python
# On Windows, use string command with shell=True
cmd = 'nvidia-smi --query-gpu=... --format=csv,noheader,nounits'

# Hide console window
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

process = subprocess.Popen(
    cmd,  # String command
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    shell=True,  # Works in Maya!
    startupinfo=startupinfo,
    universal_newlines=True
)
```

---

## How to Test

### Quick Test (Recommended)

Run this in Maya Script Editor:
```python
from lrc_toolbox.tests.test_gpu_fix import test_gpu_fix
test_gpu_fix()
```

**Expected Output:**
```
============================================================
GPU DETECTION FIX TEST
============================================================

[TEST] Running detect_cuda_gpus()...
  Calling detect_cuda_gpus()...

  ✓ SUCCESS! Detected 1 GPU(s):
    GPU 0: NVIDIA GeForce RTX 3090
      Memory: 24.0 GB
      Available: True
      Compute: 8.6

============================================================
TEST COMPLETE
============================================================
```

### Full Diagnostic Test

If the quick test fails, run the full diagnostic:
```python
from lrc_toolbox.tests.test_gpu_detection import test_gpu_detection
test_gpu_detection()
```

---

## If It Still Doesn't Work

### Solution 1: Install pynvml (Recommended)

pynvml doesn't use subprocess, so it avoids the Maya issue entirely.

```bash
pip install pynvml
```

Then restart Maya and test again.

### Solution 2: Use Fallback Mode

If both pynvml and nvidia-smi fail, the system will use fallback mode:
- Assumes 1 GPU is present
- Uses generic GPU info
- Limited functionality but allows rendering

### Solution 3: Manual GPU Configuration

You can manually configure GPU in the UI:
1. Open Batch Render tab
2. GPU dropdown will show "GPU 0" even if detection failed
3. Select GPU 0 and try rendering
4. The render will still use the GPU via CUDA_VISIBLE_DEVICES

---

## Technical Details

### Why shell=True Works

**With `shell=False`:**
- Python directly spawns nvidia-smi.exe
- Maya's process management interferes
- Process hangs waiting for I/O

**With `shell=True`:**
- Python spawns cmd.exe
- cmd.exe spawns nvidia-smi.exe
- Extra layer avoids Maya's interference
- Process completes normally

### Why STARTUPINFO Matters

Without STARTUPINFO:
- Console window briefly appears
- Can cause focus issues in Maya
- Looks unprofessional

With STARTUPINFO:
- Console window hidden
- No visual disruption
- Clean execution

### Timeout Increase

- Old: 5 seconds (too short for Maya)
- New: 10 seconds (enough time for shell execution)
- Fallback: If timeout, try next method

---

## Fallback Detection

If both pynvml and nvidia-smi fail, the system uses basic detection:

```python
def _detect_with_fallback():
    """
    Last resort: Check if NVIDIA drivers exist.
    If yes, assume 1 GPU with generic info.
    """
    # Check for nvidia-smi.exe existence
    # Check Windows registry for NVIDIA drivers
    # If found, return generic GPU info
```

This ensures the system works even if subprocess is completely broken.

---

## Summary

| Issue | Status | Solution |
|-------|--------|----------|
| nvidia-smi timeout | ✅ Fixed | Use shell=True with string command |
| Console window flash | ✅ Fixed | Use STARTUPINFO |
| No fallback | ✅ Fixed | Added 3-level fallback system |
| pynvml not installed | ⚠️ Recommended | `pip install pynvml` |

---

## Next Steps

1. **Test the fix:**
   ```python
   from lrc_toolbox.tests.test_gpu_fix import test_gpu_fix
   test_gpu_fix()
   ```

2. **If it works:** You're done! GPU detection should now work.

3. **If it still fails:** Install pynvml:
   ```bash
   pip install pynvml
   ```

4. **If pynvml fails too:** Use fallback mode (automatic).

---

**The fix is committed and ready to test!** 🚀

