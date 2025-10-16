# LRC Toolbox - Load Commands

## 🚀 Quick Load (Copy-Paste into Maya Script Editor)

### Method 1: One-Line Command (Simplest - No Maya.env Required!)

**Copy this into Maya Script Editor (Python tab) and press Ctrl+Enter:**

```python
import sys, os; sys.path.insert(0, r"V:\SWA\tools\git\swaLRC\maya"); os.environ['MAYA_PLUG_IN_PATH'] = r"V:\SWA\tools\git\swaLRC\maya\plugins" + ";" + os.environ.get('MAYA_PLUG_IN_PATH', ''); from lrc_toolbox.main import create_dockable_ui; ui = create_dockable_ui()
```

**Shorter version (without plugin path):**

```python
import sys; sys.path.insert(0, r"V:\SWA\tools\git\swaLRC\maya"); from lrc_toolbox.main import create_dockable_ui; ui = create_dockable_ui()
```

---

### Method 2: Multi-Line Command (Easier to Read - No Maya.env Required!)

**Copy this into Maya Script Editor (Python tab) and press Ctrl+Enter:**

```python
import sys
import os

# Add to PYTHONPATH
sys.path.insert(0, r"V:\SWA\tools\git\swaLRC\maya")

# Add to MAYA_PLUG_IN_PATH (optional)
plugin_path = r"V:\SWA\tools\git\swaLRC\maya\plugins"
if 'MAYA_PLUG_IN_PATH' in os.environ:
    os.environ['MAYA_PLUG_IN_PATH'] = plugin_path + ";" + os.environ['MAYA_PLUG_IN_PATH']
else:
    os.environ['MAYA_PLUG_IN_PATH'] = plugin_path

# Load UI
from lrc_toolbox.main import create_dockable_ui
ui = create_dockable_ui()
```

**Shorter version (without plugin path):**

```python
import sys
sys.path.insert(0, r"V:\SWA\tools\git\swaLRC\maya")
from lrc_toolbox.main import create_dockable_ui
ui = create_dockable_ui()
```

---

### Method 3: Execute Script File

**Run this in Maya Script Editor (Python tab):**

```python
execfile(r"V:\SWA\tools\git\swaLRC\maya\QUICK_LOAD.py")
```

---

### Method 4: Use Loader Script

**Run this in Maya Script Editor (Python tab):**

```python
execfile(r"V:\SWA\tools\git\swaLRC\maya\load_lrc_toolbox.py")
```

---

## 🔧 For Different Paths

If your toolbox is in a different location, replace the path:

```python
# Example for different repository name:
import sys
sys.path.insert(0, r"V:\SWA\tools\git\NEW_REPO_NAME\maya")
from lrc_toolbox.main import create_dockable_ui
ui = create_dockable_ui()

# Example for different drive:
import sys
sys.path.insert(0, r"C:\tools\lrc_toolbox\maya")
from lrc_toolbox.main import create_dockable_ui
ui = create_dockable_ui()
```

---

## 📋 Troubleshooting

### Error: "SyntaxError: invalid syntax"

**Solution:** Make sure you're in the **Python** tab, not the MEL tab!

1. Open Script Editor
2. Look at the tabs at the bottom
3. Click **Python** (not MEL)
4. Paste the command
5. Press Ctrl+Enter

---

### Error: "No module named 'lrc_toolbox'"

**Solution:** Check if the path exists and is correct.

```python
import os
path = r"V:\SWA\tools\git\swaLRC\maya"
print("Path exists:", os.path.exists(path))
print("lrc_toolbox exists:", os.path.exists(os.path.join(path, "lrc_toolbox")))
```

If it prints `False`, update the path to the correct location.

---

### Error: "Path not found"

**Solution:** Find the correct path to your maya directory.

The path should point to the `maya` directory that contains:
- `lrc_toolbox/` folder
- `plugins/` folder
- `load_lrc_toolbox.py` file

Example structure:
```
V:\SWA\tools\git\swaLRC\maya\
├── lrc_toolbox\
│   ├── main.py
│   ├── core\
│   └── ui\
├── plugins\
│   └── lrc_toolbox_plugin.py
└── load_lrc_toolbox.py
```

---

## 🎯 Recommended Setup (One-Time)

Instead of running the command every time, set up Maya.env:

### Step 1: Edit Maya.env

**Location:** `C:\Users\<YourUsername>\Documents\maya\2022\Maya.env`

**Add these lines:**
```bash
PYTHONPATH=V:\SWA\tools\git\swaLRC\maya;$PYTHONPATH
MAYA_PLUG_IN_PATH=V:\SWA\tools\git\swaLRC\maya\plugins;$MAYA_PLUG_IN_PATH
```

### Step 2: Restart Maya

### Step 3: Load Plugin

1. Windows > Settings/Preferences > Plug-in Manager
2. Find `lrc_toolbox_plugin.py`
3. Check "Loaded" ✅
4. Check "Auto load" ✅

### Step 4: Use Menu

Now you can just use: **LRC Toolbox > Open Toolbox**

---

## 📝 Notes

- **Repository name doesn't matter** - The script works with any repo name (swaLRC, LRCtoolsbox, etc.)
- **Path is flexible** - Just update the path to match your environment
- **No hardcoded paths** - All paths are configurable
- **Works everywhere** - Development, production, any machine

---

## 🚀 Quick Reference

**Fastest way to load:**
```python
import sys; sys.path.insert(0, r"V:\SWA\tools\git\swaLRC\maya"); from lrc_toolbox.main import create_dockable_ui; ui = create_dockable_ui()
```

**Change path for your environment:**
- Replace `V:\SWA\tools\git\swaLRC\maya` with your actual path
- Make sure path points to the `maya` directory
- Path should contain `lrc_toolbox` folder

---

**That's it! Copy, paste, run!** ✅

