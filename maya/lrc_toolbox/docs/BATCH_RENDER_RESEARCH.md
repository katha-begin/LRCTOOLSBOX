# Batch Render Command Research

## Research Summary

Investigation into proper Maya batch rendering commands, flags, and common crash causes.

---

## Common Crash Causes

### 1. UI Commands in Batch Mode ⚠️

**Most Common Crash:**
```
Error: UI commands can't be run in batch mode
```

**Cause:**
- Scripts calling UI commands (e.g., `window`, `button`, `textField`)
- Plugins with UI initialization in batch mode
- userSetup.mel/py files with UI code

**Solution:**
- Check if Maya is in batch mode before UI commands
- Use `maya.standalone.initialize(name='python')` properly
- Disable UI-dependent plugins in batch mode

---

### 2. Missing maya.standalone.initialize() Arguments

**Issue:**
```python
import maya.standalone
maya.standalone.initialize()  # ❌ Missing name argument
```

**Better:**
```python
import maya.standalone
maya.standalone.initialize(name='python')  # ✅ Specify interpreter
```

**Why:**
- `name='python'` tells Maya to run in Python mode
- Prevents some initialization issues
- More stable for batch rendering

---

### 3. Render.exe Missing Critical Flags

**Current Implementation:**
```bash
Render.exe -r redshift -rl MASTER_BG_A -s 1 -e 24 scene.ma
```

**Missing Flags:**
- `-proj` - Project directory
- `-rd` - Render output directory
- `-im` - Image name prefix
- `-of` - Output format
- `-x` - Width
- `-y` - Height
- `-pad` - Frame padding
- `-fnc` - Frame number format

---

## Maya Render.exe Flags (Complete List)

### Essential Flags

| Flag | Description | Example |
|------|-------------|---------|
| `-r <renderer>` | Renderer name | `-r redshift` |
| `-rl <layer>` | Render layer | `-rl MASTER_BG_A` |
| `-s <frame>` | Start frame | `-s 1` |
| `-e <frame>` | End frame | `-e 24` |
| `-b <step>` | Frame step/by | `-b 2` |
| `-proj <path>` | Project directory | `-proj V:/SWA/all` |
| `-rd <path>` | Render output directory | `-rd V:/SWA/all/images` |
| `-im <name>` | Image name prefix | `-im SH0010_MASTER_BG_A` |

### Output Format Flags

| Flag | Description | Example |
|------|-------------|---------|
| `-of <format>` | Output format | `-of exr` |
| `-x <width>` | Image width | `-x 1920` |
| `-y <height>` | Image height | `-y 1080` |
| `-pad <num>` | Frame padding | `-pad 4` |
| `-fnc <format>` | Frame number format | `-fnc name.#.ext` |

### Quality Flags

| Flag | Description | Example |
|------|-------------|---------|
| `-cam <camera>` | Camera name | `-cam renderCam` |
| `-rgb` | Render RGB | `-rgb` |
| `-alpha` | Render alpha | `-alpha` |
| `-depth` | Render depth | `-depth` |

### Performance Flags

| Flag | Description | Example |
|------|-------------|---------|
| `-n <threads>` | Number of threads | `-n 8` |
| `-preRender <mel>` | Pre-render MEL | `-preRender "source setup.mel"` |
| `-postRender <mel>` | Post-render MEL | `-postRender "source cleanup.mel"` |

### Debugging Flags

| Flag | Description | Example |
|------|-------------|---------|
| `-v <level>` | Verbosity level (0-5) | `-v 5` |
| `-log <file>` | Log file path | `-log render.log` |

---

## mayapy Batch Rendering Best Practices

### 1. Proper Initialization

```python
import sys
import maya.standalone

# Initialize with name argument
maya.standalone.initialize(name='python')

# Check if in batch mode
import maya.cmds as cmds
is_batch = cmds.about(batch=True)
print(f"Batch mode: {is_batch}")
```

### 2. Error Handling

```python
try:
    import maya.standalone
    maya.standalone.initialize(name='python')
    
    import maya.cmds as cmds
    
    # Your render code here
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)  # Exit with error code
finally:
    try:
        maya.standalone.uninitialize()
    except:
        pass
```

### 3. Avoid UI Commands

```python
# ❌ BAD - Will crash in batch mode
import maya.cmds as cmds
cmds.window()
cmds.button()

# ✅ GOOD - Check batch mode first
import maya.cmds as cmds
if not cmds.about(batch=True):
    cmds.window()
    cmds.button()
```

### 4. Plugin Loading

```python
# Load required plugins
import maya.cmds as cmds

plugins = ['redshift4maya', 'mtoa', 'vrayformaya']
for plugin in plugins:
    try:
        if not cmds.pluginInfo(plugin, query=True, loaded=True):
            cmds.loadPlugin(plugin, quiet=True)
            print(f"Loaded plugin: {plugin}")
    except:
        print(f"Failed to load plugin: {plugin}")
```

### 5. Scene File Handling

```python
# Open scene with error handling
import maya.cmds as cmds

scene_file = "path/to/scene.ma"

try:
    cmds.file(scene_file, open=True, force=True, ignoreVersion=True)
    print(f"Opened scene: {scene_file}")
except Exception as e:
    print(f"Failed to open scene: {e}")
    sys.exit(1)
```

---

## Recommended Command Structure

### For Render.exe (Priority 1)

```bash
Render.exe \
  -r redshift \
  -rl MASTER_BG_A \
  -s 1 \
  -e 24 \
  -b 1 \
  -proj "V:/SWA/all" \
  -rd "V:/SWA/all/images/Ep01/sq0010/SH0010" \
  -im "SH0010_MASTER_BG_A" \
  -of exr \
  -pad 4 \
  -fnc name.#.ext \
  -v 5 \
  "V:/SWA/all/scene/Ep01/sq0010/SH0010/lighting/version/SH0010_lighting_v001.ma"
```

### For mayapy Custom Script (Priority 2)

```python
# -*- coding: utf-8 -*-
"""Batch Render Script with Proper Error Handling"""

import sys
import traceback

def main():
    try:
        # Initialize Maya standalone
        import maya.standalone
        maya.standalone.initialize(name='python')
        
        import maya.cmds as cmds
        
        # Verify batch mode
        if not cmds.about(batch=True):
            print("WARNING: Not running in batch mode")
        
        # Load required plugins
        plugins = ['redshift4maya']
        for plugin in plugins:
            try:
                if not cmds.pluginInfo(plugin, query=True, loaded=True):
                    cmds.loadPlugin(plugin, quiet=True)
            except:
                pass
        
        # Open scene
        scene_file = "path/to/scene.ma"
        cmds.file(scene_file, open=True, force=True, ignoreVersion=True)
        
        # Set render layer
        layer_name = "MASTER_BG_A"
        cmds.editRenderLayerGlobals(currentRenderLayer=layer_name)
        
        # Set renderer
        cmds.setAttr("defaultRenderGlobals.currentRenderer", "redshift", type="string")
        
        # Render frames
        frames = [1, 2, 3, 4, 5]
        for frame in frames:
            print(f"Rendering frame {frame}")
            cmds.currentTime(frame)
            cmds.render()
        
        print("Render complete!")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        return 1
        
    finally:
        try:
            maya.standalone.uninitialize()
        except:
            pass

if __name__ == "__main__":
    sys.exit(main())
```

---

## Environment Variables

### Critical Environment Variables

```bash
# GPU selection
CUDA_VISIBLE_DEVICES=0

# CPU threads
OMP_NUM_THREADS=8

# Maya project
MAYA_PROJECT=V:/SWA/all

# Plugin paths (if needed)
MAYA_PLUG_IN_PATH=V:/SWA/all/plugins

# Script paths (if needed)
MAYA_SCRIPT_PATH=V:/SWA/all/scripts
```

---

## Common Issues and Solutions

### Issue 1: "UI commands can't be run in batch mode"

**Solution:**
1. Check userSetup.mel/py for UI commands
2. Wrap UI code in batch mode check
3. Disable UI-dependent plugins

### Issue 2: Renderer not found

**Solution:**
1. Load renderer plugin explicitly
2. Check plugin path
3. Verify renderer name spelling

### Issue 3: Scene file not found

**Solution:**
1. Use absolute paths
2. Check file permissions
3. Verify file exists before rendering

### Issue 4: Output directory not writable

**Solution:**
1. Create output directory before rendering
2. Check write permissions
3. Use `-rd` flag to specify output directory

### Issue 5: Memory crash

**Solution:**
1. Reduce image resolution
2. Limit number of threads
3. Render fewer frames at once
4. Check available RAM

---

## Testing Commands

### Test 1: Verify Render.exe

```bash
Render.exe -help
```

### Test 2: Test mayapy

```bash
mayapy -c "import maya.standalone; maya.standalone.initialize(name='python'); print('OK')"
```

### Test 3: Test Scene Opening

```bash
mayapy -c "import maya.standalone; maya.standalone.initialize(name='python'); import maya.cmds as cmds; cmds.file('scene.ma', open=True); print('OK')"
```

---

## Recommendations for Implementation

### Priority 1: Fix Render.exe Command

Add missing flags:
- `-proj` for project directory
- `-rd` for output directory
- `-im` for image name
- `-of` for output format
- `-v 5` for verbose logging

### Priority 2: Fix mayapy Script

Add proper error handling:
- `try/except/finally` blocks
- `sys.exit()` with error codes
- Traceback printing
- Plugin loading verification

### Priority 3: Add Batch Mode Checks

Prevent UI command crashes:
- Check `cmds.about(batch=True)`
- Wrap UI code conditionally
- Disable UI plugins in batch mode

### Priority 4: Add Logging

Better debugging:
- Verbose output (`-v 5`)
- Log files
- Progress reporting
- Error messages

---

## Next Steps

1. Update `_build_render_exe_command()` with all required flags
2. Update `_create_custom_render_script()` with proper error handling
3. Add batch mode checks to prevent UI crashes
4. Add plugin loading verification
5. Add comprehensive logging
6. Test with various crash scenarios

