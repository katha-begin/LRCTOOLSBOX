# LRC Toolbox v2.0 - Batch Render Manager Release

## 🎉 New Feature: GPU-Accelerated Batch Rendering

The LRC Toolbox now includes a complete batch rendering system with real-time monitoring, automatic crash detection, and a clean log viewer interface.

---

## ✨ Key Features

### 1. Popup Log Viewer
- **No Script Editor Spam**: All logs display in a dedicated popup window
- **Process Management**: Switch between multiple render processes
- **Export Logs**: Copy to clipboard or save to file
- **Auto-scroll**: Automatically follows latest log messages
- **Clean Interface**: Monospace font for easy reading

### 2. Automatic Output Path Detection
- **Respects Render Settings**: Uses your configured output paths
- **Publish Directory**: Outputs to `publish/` directory, not `.tmp/`
- **Path Format**: `{project}/scene/{ep}/{seq}/{shot}/{dept}/publish/{version}/{layer}/{layer}/`
- **Completion Message**: Shows output path when render finishes

### 3. Real-time Progress Tracking
- **Frame-by-Frame**: Updates progress as each frame completes
- **Visual Progress Bar**: Shows 0% to 100% completion
- **Supports Multiple Renderers**: Arnold and Redshift
- **Live Updates**: No need to refresh

### 4. Automatic Crash Detection
- **2-Second Monitoring**: Checks process health every 2 seconds
- **Return Code Detection**: Identifies failure types
- **UI Updates**: Automatically marks failed renders
- **Error Messages**: Displays specific error information

### 5. Stable Render Method Selection
- **Priority 1**: Render.exe (Maya's native batch renderer - most stable)
- **Priority 2**: mayapy with custom script (flexible fallback)
- **Priority 3**: mayapy basic render (last resort)
- **Automatic Fallback**: Tries next method if one fails

### 6. Context-Aware Temp Files
- **Hierarchical Structure**: Mirrors project organization
- **Shot Context**: `.tmp/{ep}/{seq}/{shot}/{dept}/{layer}/`
- **Asset Context**: `.tmp/{cat}/{subcat}/{asset}/{dept}/{layer}/`
- **Version Tracking**: Includes version number in filename

---

## 📋 Usage Guide

### Starting a Batch Render

1. **Open LRC Toolbox**
   - Maya menu: `LRC Toolbox → Open LRC Toolbox`
   - Or run: `lrcToolboxOpen()`

2. **Go to Batch Render Tab**
   - Click "Batch Render" tab in the toolbox

3. **Configure Render**
   - **Layer**: Select from Render Setup layers
   - **Frame Range**: Enter frames (e.g., `1-10`, `1,5,10`, `1-10x2`)
   - **Renderer**: Choose Arnold or Redshift
   - **GPU**: Select GPU (optional)

4. **Start Render**
   - Click "Start Render" button
   - Progress bar updates in real-time

5. **View Logs**
   - Click "Open Log Viewer" button
   - Watch render progress
   - See output path on completion

---

## 🎯 Frame Range Syntax

### Simple Range
```
1-10        # Frames 1 to 10
```

### Specific Frames
```
1,5,10      # Only frames 1, 5, and 10
```

### Frame Step
```
1-10x2      # Every 2nd frame (1, 3, 5, 7, 9)
```

### Combined
```
1-5,10,20-30x2    # Frames 1-5, 10, and 20-30 (every 2nd)
```

---

## 🔧 Technical Details

### Render Methods

**Render.exe (Priority 1)**
- Maya's official batch renderer
- Most stable and reliable
- Works with all renderers
- Proper error handling

**mayapy Custom (Priority 2)**
- Python-based rendering
- Flexible but can crash
- Used as fallback

**mayapy Basic (Priority 3)**
- Simple Python render
- Last resort option

### Output Path Resolution

The system reads your render settings and constructs the correct output path:

**Your Render Settings:**
```
W:/SWA/all/scene/{ep}/{seq}/{shot}/lighting/publish/{version}/<RenderLayer>/<RenderLayer>/<RenderLayer>.####.ext
```

**Actual Output:**
```
W:/SWA/all/scene/Ep01/sq0040/SH0200/lighting/publish/v005/MASTER_CHAR_A/MASTER_CHAR_A/
```

### Process Monitoring

- **Check Interval**: Every 2 seconds
- **Return Codes**:
  - `0` = Success
  - `1` = General error
  - `204` = Invalid command flag
  - `210/211` = Render failure
  - `None` = Process crashed

---

## 🐛 Troubleshooting

### Render Fails Immediately

**Check:**
1. Renderer license (Redshift requires Maxon login)
2. Scene file is saved
3. Render layers exist in Render Setup
4. Frame range syntax is correct

**Solutions:**
- For Redshift: Log into Maxon licensing
- For Arnold: Should work without license
- Check log viewer for specific errors

### Progress Stuck at 0%

**Possible Causes:**
- Render initializing (wait a few seconds)
- Frame progress not detected in logs
- Process crashed before rendering

**Solutions:**
- Open log viewer to see actual progress
- Check for error messages
- Verify renderer is working

### Output Path Wrong

**Requirements:**
- Render settings must have correct path configured
- Scene file must be saved
- Path is read from render settings, not constructed

**Check:**
- Open Render Settings → Common tab
- Verify "File name prefix" is correct
- Should include `<RenderLayer>` tokens

---

## 📦 Installation

The batch render manager is included in LRC Toolbox v2.0. No additional installation required.

**Requirements:**
- Maya 2022 or later
- Arnold or Redshift renderer
- Windows OS (tested on Windows 10/11)

---

## 🚀 What's New in This Release

### Added
- ✅ Complete batch render system
- ✅ Popup log viewer dialog
- ✅ Real-time progress tracking
- ✅ Automatic crash detection
- ✅ Output path parsing from render settings
- ✅ Context-aware temp file management
- ✅ Frame range parser with step support

### Fixed
- ✅ Render.exe priority (now most stable method)
- ✅ Output path respects render settings
- ✅ Progress tracking from render logs
- ✅ Process monitoring with return codes
- ✅ Invalid command flags removed

### Improved
- ✅ Clean log management (no script editor spam)
- ✅ Better error messages
- ✅ Stable render execution
- ✅ User-friendly interface

---

## 📞 Support

**For Issues:**
1. Check the log viewer for error messages
2. Verify renderer licenses
3. Check render settings configuration
4. Review frame range syntax

**Common Solutions:**
- Restart Maya if module changes
- Verify scene is saved
- Check Render Setup layers exist
- Ensure renderer plugins are loaded

---

## 🎊 Summary

The Batch Render Manager provides:
- ✅ Clean popup log viewer
- ✅ Correct output paths from render settings
- ✅ Real-time progress tracking
- ✅ Automatic crash detection
- ✅ Stable rendering with Render.exe
- ✅ Easy-to-use interface

**Ready to use! Open LRC Toolbox and start batch rendering!** 🎬

---

**Version**: 2.0.0  
**Release Date**: October 2025  
**Branch**: publish/batch-render-manager

