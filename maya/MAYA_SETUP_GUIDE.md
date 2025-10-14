# LRC Toolbox v2.0 - Maya Setup Guide

## 🚀 **Quick Setup (Recommended)**

### **Step 1: Update Maya.env**

**Location**: `Documents\maya\2022\Maya.env` (adjust for your Maya version)

**Add these lines to Maya.env:**
```bash
PYTHONPATH=E:\dev\LRCtoolsbox\LRCtoolsbox\maya;$PYTHONPATH
MAYA_PLUG_IN_PATH=E:\dev\LRCtoolsbox\LRCtoolsbox\maya\plugins;$MAYA_PLUG_IN_PATH
```

### **Step 2: Restart Maya**

### **Step 3: Load Plugin**
1. Go to **Windows > Settings/Preferences > Plug-in Manager**
2. Find **`lrc_toolbox_plugin.py`** (should be only ONE entry now)
3. Check **"Loaded"** ✅
4. Check **"Auto load"** ✅ (optional, for automatic loading)

### **Step 4: Launch UI**
- **Menu**: `LRC Toolbox > Open Toolbox`
- **Command**: `lrcToolboxOpen()`
- **Python**: `cmds.lrcToolboxOpen()`

## 🔧 **File Structure (Clean)**

```
E:\dev\LRCtoolsbox\LRCtoolsbox\maya\
├── plugins\
│   └── lrc_toolbox_plugin.py     # ← ONLY plugin file Maya sees
├── lrc_toolbox\                  # ← Package directory
│   ├── main.py
│   ├── ui\
│   │   ├── main_window.py
│   │   └── widgets\
│   │       └── asset_navigator.py
│   └── config\
│       └── settings.py
├── test_ui.py                    # ← Not in plugin path
├── install_plugin.py             # ← Not in plugin path
└── README_MAYA_PLUGIN.md         # ← Not in plugin path
```

## ✅ **Why This Fixes the Issues:**

1. **Single Plugin Entry** - Only `plugins/lrc_toolbox_plugin.py` is in the plugin path
2. **No `__file__` Errors** - Test scripts are outside plugin directory
3. **Clean Plugin Manager** - Only one LRC Toolbox entry
4. **Proper Path Resolution** - Plugin correctly finds the lrc_toolbox package

## 🧪 **Test the Setup:**

### **Method 1: Menu**
1. Look for **"LRC Toolbox"** menu in Maya's main menu bar
2. Click **"LRC Toolbox > Open Toolbox"**

### **Method 2: Command**
```python
# In Maya Script Editor (Python tab):
import maya.cmds as cmds
cmds.lrcToolboxOpen()
```

### **Method 3: Direct Python**
```python
# In Maya Script Editor (Python tab):
import sys
sys.path.insert(0, r"E:\dev\LRCtoolsbox\LRCtoolsbox\maya")
from lrc_toolbox.main import create_dockable_ui
ui = create_dockable_ui()
```

## 🎯 **Expected Result:**

When successful, you should see:
- **Dockable window** on the right side of Maya
- **5 tabs**: Asset/Shot, Render Setup, Light Manager, Regex Tools, Settings
- **Functional Asset Navigator** with dropdown menus and file lists
- **Status bar** showing context updates
- **LRC Toolbox menu** in Maya's menu bar

## 🔧 **Troubleshooting:**

### **Plugin Won't Load**
```python
# Check if paths are set correctly:
import sys
print("Python paths:")
for path in sys.path:
    if "LRCtoolsbox" in path:
        print(f"  ✅ {path}")

import maya.cmds as cmds
plugin_paths = cmds.pluginInfo(query=True, listPluginsPath=True)
print("Plugin paths:")
for path in plugin_paths:
    if "LRCtoolsbox" in path:
        print(f"  ✅ {path}")
```

### **Multiple Plugin Entries**
- Make sure only `plugins/lrc_toolbox_plugin.py` is in the plugin path
- Remove any other `.py` files from plugin directories
- Restart Maya after cleaning up

### **UI Won't Open**
```python
# Try direct import test:
try:
    from lrc_toolbox.main import create_dockable_ui
    print("✅ Import successful")
    ui = create_dockable_ui()
    print("✅ UI created successfully")
except Exception as e:
    print(f"❌ Error: {e}")
```

## 📋 **Current Functionality:**

### **✅ Working Features:**
- **Asset Navigator** - Complete implementation
  - Project settings with browse dialog
  - Episode/Sequence/Shot navigation
  - Asset Category/Subcategory/Asset navigation
  - File lists with mock data
  - Context menus (right-click files)
  - Action buttons with mock responses

### **🚧 Placeholder Features:**
- **Render Setup** - Framework ready
- **Light Manager** - Framework ready
- **Regex Tools** - Framework ready
- **Settings** - Framework ready

## 🎉 **Success Indicators:**

When everything is working correctly:
1. **Single plugin entry** in Plugin Manager
2. **LRC Toolbox menu** appears in Maya
3. **Dockable UI** opens with 5 tabs
4. **Asset Navigator** responds to interactions
5. **Status bar** updates with context changes
6. **No error messages** in Script Editor

---

**Ready to test the enhanced template management system!** 🚀
