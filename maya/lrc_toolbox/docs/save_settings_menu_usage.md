# Save & Settings Tool - Simple Installation Guide

## 📁 **SIMPLE PLUGIN SOLUTION** (No Hardcoded Paths)

The plugin now uses **relative paths only** - it finds the `save_and_setting.py` script in the same location as the plugin itself!

### **Required Directory Structure:**
```
maya/
├── plugins/
│   └── lrc_toolbox_plugin.py
├── mockup/
│   └── save_and_setting.py
└── lrc_toolbox/
    └── (other toolbox files)
```

### **How to Use:**

1. **Load the Plugin**:
   - Go to `Window > Settings/Preferences > Plug-in Manager`
   - Find `lrc_toolbox_plugin.py`
   - Check "Loaded" and "Auto load"

2. **Use the Menu**:
   - Go to `LRC Toolbox > Save & Settings Tool`
   - The plugin automatically finds the script using relative paths! ✅

## 🔧 **Troubleshooting**

### If the Menu Item Doesn't Work:

1. **Check Installation Structure**:
   - Make sure `save_and_setting.py` is in `maya/mockup/` folder
   - Make sure `lrc_toolbox_plugin.py` is in `maya/plugins/` folder
   - Both should be in the same `maya/` directory

2. **Check Plugin Loading**:
   - Go to `Window > Settings/Preferences > Plug-in Manager`
   - Find `lrc_toolbox_plugin.py` and make sure it's loaded
   - Look for any error messages in the Script Editor

3. **Manual Test**:
   ```python
   # Test the plugin command directly in Script Editor:
   import maya.cmds as cmds
   cmds.lrcOpenSaveSettings()
   ```

### Expected Behavior:
- ✅ Plugin loads without errors
- ✅ Menu item appears: `LRC Toolbox > Save & Settings Tool`
- ✅ Clicking menu opens the Save & Settings UI
- ✅ No hardcoded paths needed - everything is relative!



## What You Get

When you click the menu item, it will:
1. ✅ **Execute the original script** - No modifications, just direct execution
2. ✅ **Open the full UI** - Both Settings and Scene I/O tabs
3. ✅ **All original functionality** - Shot setup, render settings, file management
4. ✅ **Same interface** - Familiar UI that you're already using

## Features Available

The tool provides all the original functionality:

### Settings Tab
- Shot node detection and parsing
- Render settings application (frames, prefix, Redshift)
- Version tracking and management
- Real-time logging

### Scene I/O Tab
- Project navigation (Show/Episode/Sequence/Shot)
- File operations (Open, Save As, Save Increment)
- Directory scanning and file listing
- Version checking and preview

## Troubleshooting

### "Save & Settings script not found"
- Check that the file exists at: `maya/mockup/save_and_setting.py`
- Verify the plugin path is correct

### Menu item not visible
- Make sure the LRC Toolbox plugin is loaded
- Check `Window > Settings/Preferences > Plug-in Manager`
- Look for `lrc_toolbox_plugin.py` and ensure it's checked

### Script errors
- Check Maya's Script Editor for detailed error messages
- Ensure all required paths (V:/ drive, etc.) are accessible

## Technical Details

### Implementation
- **No integration** - The original script runs as-is
- **Direct execution** - Uses `exec(open(script_path).read())`
- **Menu integration** - Added to LRC Toolbox plugin menu
- **Error handling** - Proper error messages if script not found

### File Locations
- **Plugin**: `maya/plugins/lrc_toolbox_plugin.py`
- **Original Script**: `maya/mockup/save_and_setting.py`
- **Test Script**: `maya/lrc_toolbox/examples/maya_test_save_settings.py`

### Function Added
```python
def lrc_open_save_settings_tool():
    """Open the Save & Settings tool from mockup directory."""
    # Finds and executes the original save_and_setting.py script
```

## Benefits

1. **Easy Access** - One click from Maya menu
2. **No Changes** - Original script unchanged
3. **Familiar Interface** - Same UI you're used to
4. **Full Functionality** - All features preserved
5. **Quick Testing** - Test script provided

---

This integration provides convenient access to your existing Save & Settings tool without any modifications to the original functionality.
