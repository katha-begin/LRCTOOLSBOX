# Batch Render Manager - Features

## Overview

The Batch Render Manager provides GPU-accelerated batch rendering with automatic fallback, real-time monitoring, and a clean log viewer interface.

---

## ✨ Key Features

### 1. Popup Log Viewer
**No more script editor spam!**

- **Separate Window**: Logs open in a dedicated dialog window
- **Process Selector**: Switch between different render processes
- **Auto-scroll**: Automatically scroll to latest logs
- **Copy to Clipboard**: Copy all logs with one click
- **Save to File**: Export logs to text file
- **Clear Logs**: Clear logs per process
- **Monospace Font**: Easy-to-read Courier font

**How to Use:**
1. Click "Open Log Viewer" button in Batch Render tab
2. Select process from dropdown
3. Watch logs update in real-time
4. Copy/save logs as needed

---

### 2. Output Path Display
**Know where your renders are!**

When a render completes successfully, the output path is displayed:
- In the log viewer completion message
- In the Maya console
- Format: `{scene_dir}/images/{layer_name}`

**Example:**
```
================================================================================
✅ RENDER COMPLETED SUCCESSFULLY
================================================================================
Output: V:/SWA/all/scene/Ep01/sq0010/SH0010/lighting/images/MASTER_BG_A
================================================================================
```

---

### 3. Automatic Render Method Selection

**Priority Order (AUTO mode):**
1. **Render.exe** - Maya's native batch renderer (most stable)
2. **mayapy + custom script** - Flexible but can crash
3. **mayapy + basic render** - Fallback option

**Why Render.exe First?**
- ✅ Most stable and reliable
- ✅ No Python initialization issues
- ✅ Better error handling
- ✅ Production-ready
- ✅ Works with all renderers (Arnold, Redshift, etc.)

---

### 4. Real-time Progress Tracking

**Progress Bar Updates:**
- Parses frame completion from logs
- Supports Arnold and Redshift
- Updates UI in real-time
- Shows 0% → 100% progress

**Frame Detection:**
- Arnold: `"Rendering frame 5 of 10"`
- Redshift: `"Rendering layer 'X', frame 5 (5/10)"`

---

### 5. Crash Detection & Monitoring

**Automatic Process Monitoring:**
- Checks every 2 seconds
- Detects crashed processes
- Shows return codes
- Updates UI status to FAILED
- Displays error messages

**Return Codes:**
- `0` = Success
- `1` = General error
- `204` = Invalid command flag
- `210/211` = Render failure
- `None` = Process crashed before starting

---

### 6. Context-Aware Temp Paths

**Hierarchical Structure:**

**For Shots:**
```
{project_root}/scene/.tmp/{ep}/{seq}/{shot}/{dept}/{layer}/
render_{shot}_{dept}_v{version}_{timestamp}_{pid}.ma
```

**For Assets:**
```
{project_root}/asset/.tmp/{cat}/{subcat}/{asset}/{dept}/{layer}/
render_{asset}_{dept}_v{version}_{timestamp}_{pid}.ma
```

**Fallback:**
```
~/Documents/maya_batch_tmp/{layer}/
render_unknown_{timestamp}_{pid}.ma
```

---

## 🎯 Usage Guide

### Starting a Batch Render

1. **Select Render Layer**
   - Choose from Render Setup layers dropdown
   - Layers are automatically detected

2. **Set Frame Range**
   - Simple: `1-10` (frames 1 to 10)
   - Specific: `1,5,10` (frames 1, 5, and 10)
   - Step: `1-10x2` (every 2nd frame)
   - Combined: `1-5,10,20-30x2`

3. **Choose Renderer**
   - Arnold (included with Maya)
   - Redshift (requires license)
   - Other renderers as available

4. **Select GPU** (optional)
   - Auto-detect available GPUs
   - Choose specific GPU for rendering

5. **Click Start Render**
   - Process starts immediately
   - Progress bar updates in real-time
   - Open log viewer to see details

---

### Viewing Logs

1. **Click "Open Log Viewer"**
   - Opens popup dialog window
   - Shows all render processes

2. **Select Process**
   - Use dropdown to switch between processes
   - Each process has separate logs

3. **Monitor Progress**
   - Logs update in real-time
   - Auto-scroll keeps latest visible
   - See frame-by-frame progress

4. **After Completion**
   - Output path is displayed
   - Copy or save logs if needed
   - Check for any errors

---

## 🐛 Troubleshooting

### Render Fails Immediately

**Check:**
1. **Renderer License** - Redshift requires Maxon login
2. **Scene File** - Ensure scene is saved
3. **Render Layers** - Verify layers exist in Render Setup
4. **Frame Range** - Check syntax is correct

**Solutions:**
- For Redshift: Log into Maxon licensing
- For Arnold: Should work without license
- Check log viewer for specific error messages

---

### Progress Stuck at 0%

**Possible Causes:**
1. Render hasn't started yet (initializing)
2. Frame progress not detected in logs
3. Process crashed before rendering

**Solutions:**
- Wait a few seconds for initialization
- Open log viewer to see actual progress
- Check for error messages in logs

---

### Script Editor Spam

**This is now fixed!**
- Logs go to popup log viewer
- Script editor only shows important messages
- Open log viewer to see detailed logs

---

### Output Path Not Shown

**Requirements:**
- Render must complete successfully (return code 0)
- Scene file must be saved
- Output path is calculated from scene location

**Format:**
```
{scene_directory}/images/{layer_name}/
```

---

## 📝 Known Limitations

### Redshift Licensing
- Requires Maxon account login
- Must be logged in for batch rendering
- Use Arnold as alternative if no license

### mayapy Instability
- Can crash with black screen
- Render.exe is more stable (now Priority 1)
- mayapy used as fallback only

### Progress Parsing
- Depends on renderer log format
- Currently supports Arnold and Redshift
- Other renderers may not show progress

---

## 🚀 Future Enhancements

### Planned Features
- [ ] Email notification on completion
- [ ] Render queue management
- [ ] Multiple layer rendering
- [ ] Render farm integration
- [ ] Custom output path configuration
- [ ] Render presets/templates

---

## 📞 Support

**If you encounter issues:**
1. Check the log viewer for error messages
2. Look for return codes in console
3. Verify renderer licenses
4. Check scene file is saved
5. Review frame range syntax

**Common Error Codes:**
- `204` = Invalid command flag
- `210/211` = Render failure (check license)
- `None` = Process crashed (check logs)

---

## 🎉 Summary

The Batch Render Manager now provides:
- ✅ Clean popup log viewer (no script editor spam)
- ✅ Output path display on completion
- ✅ Real-time progress tracking
- ✅ Automatic crash detection
- ✅ Stable Render.exe priority
- ✅ Context-aware temp paths
- ✅ Easy log management (copy/save)

**Enjoy batch rendering!** 🎬

