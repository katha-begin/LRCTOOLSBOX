# Unicode Error Fix Guide

## 🐛 The Problem

**Error Message:**
```
UnicodeDecodeError: 'charmap' codec can't decode byte 0x81 in position 17095: character maps to <undefined>
```

**Why This Happens:**
- The `lrc_manager.py` file contains **emoji and Unicode characters** (🎬, 💡, 📋, etc.)
- Windows Python uses `charmap` codec by default, which can't decode these characters
- When you run `exec(open('file.py').read())`, Python tries to read with wrong encoding

---

## ✅ The Solution

The file has been **fixed** with proper UTF-8 encoding! 

### What Was Fixed:

1. **Added UTF-8 encoding declaration** at top of file:
   ```python
   # -*- coding: utf-8 -*-
   ```

2. **Fixed all file operations** to use UTF-8:
   ```python
   # BEFORE (causes error):
   with open(filepath, 'r') as f:
   
   # AFTER (fixed):
   with open(filepath, 'r', encoding='utf-8') as f:
   ```

3. **Updated usage examples** to use UTF-8:
   ```python
   # BEFORE (causes error):
   exec(open(r'path/to/file.py').read())
   
   # AFTER (fixed):
   exec(open(r'path/to/file.py', encoding='utf-8').read())
   ```

---

## 🚀 How to Use the Fixed Version

### Method 1: Pull Latest from GitHub (Recommended)

```bash
cd T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX
git pull origin master
```

Then **restart Maya** and load again.

---

### Method 2: Load with UTF-8 Encoding

If you can't pull the latest version, use this command:

```python
# In Maya Script Editor (Python tab):
exec(open(r'T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX/maya/mockup/lrc_manager.py', encoding='utf-8').read())
show_ui()
```

**Replace the path** with your actual path!

---

## 🔧 Diagnostic & Fix Script

If you're still having issues, run the diagnostic script:

### Step 1: Load the Fix Script

```python
# In Maya Script Editor (Python tab):
exec(open(r'T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX/maya/mockup/FIX_UNICODE_ERROR.py', encoding='utf-8').read())
```

### Step 2: Run the Fix

```python
# For T: drive:
fix_unicode_error(r'T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX/maya/lrc_toolbox')

# For V: drive:
fix_unicode_error(r'V:/SWA/tools/git/swaLRC/maya/lrc_toolbox')

# For E: drive:
fix_unicode_error(r'E:/dev/LRCtoolsbox/LRCtoolsbox/maya/lrc_toolbox')
```

### Step 3: Restart Maya

**Important:** You MUST restart Maya after running the fix!

---

## 🎯 Why Some Machines Work and Others Don't

Even with the same git version, machines can behave differently:

### 1. **Python Bytecode Cache** ⭐ Most Common
- Old `.pyc` files cached before the fix
- **Solution:** Clear cache and restart Maya

### 2. **Modules Already Loaded**
- Maya has old version in memory
- **Solution:** Unload modules or restart Maya

### 3. **Different Python Versions**
- Python 2.7 vs 3.7 handle encoding differently
- **Solution:** Use `encoding='utf-8'` parameter

### 4. **Network Drive Caching**
- T: drive may cache old files
- **Solution:** Pull latest and clear cache

### 5. **File Permissions**
- Some machines can't read/write files
- **Solution:** Check permissions

---

## 📋 Complete Fix Checklist

Run these steps **in order** on failing machines:

### ✅ Step 1: Pull Latest Code
```bash
cd T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX
git pull origin master
```

### ✅ Step 2: Clear Python Cache
```python
# In Maya Script Editor:
import sys, os, shutil
toolbox_path = r"T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX/maya/lrc_toolbox"
for root, dirs, files in os.walk(toolbox_path):
    for file in files:
        if file.endswith('.pyc'):
            os.remove(os.path.join(root, file))
    if '__pycache__' in dirs:
        shutil.rmtree(os.path.join(root, '__pycache__'))
print("Cache cleared!")
```

### ✅ Step 3: Restart Maya
Close and reopen Maya completely.

### ✅ Step 4: Load Fresh
```python
# In Maya Script Editor:
import sys
sys.path.insert(0, r"T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX/maya")
from lrc_toolbox.main import create_dockable_ui
ui = create_dockable_ui()
```

---

## 🔍 Verify the Fix

Check if your file has the UTF-8 encoding:

```python
# In Maya Script Editor:
filepath = r"T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX/maya/mockup/lrc_manager.py"
with open(filepath, 'rb') as f:
    first_lines = f.read(200)
    if b'utf-8' in first_lines:
        print("✅ File has UTF-8 encoding!")
    else:
        print("❌ File missing UTF-8 encoding - pull latest from git!")
```

---

## 📝 For Developers

If you're creating new Python files with Unicode characters:

### Always Add UTF-8 Encoding Declaration:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Your module docstring here
"""
```

### Always Use UTF-8 for File Operations:

```python
# Reading files:
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Writing files:
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

# Executing files:
exec(open(filepath, encoding='utf-8').read())
```

---

## 🆘 Still Having Issues?

### Run Full Diagnostic:

```python
exec(open(r'T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX/maya/mockup/FIX_UNICODE_ERROR.py', encoding='utf-8').read())
diagnose_toolbox(r'T:/pipeline/development/maya/LRCtoolsBOX/LRCTOOLSBOX/maya/lrc_toolbox')
```

This will show:
- Path existence and permissions
- Python version and encoding
- Loaded modules
- Cache files
- File encoding status

---

## 📦 Summary

| Issue | Status | Solution |
|-------|--------|----------|
| UnicodeDecodeError | ✅ Fixed | Added UTF-8 encoding |
| Cached .pyc files | ✅ Fixed | Clear cache script provided |
| Modules in memory | ✅ Fixed | Unload script provided |
| File operations | ✅ Fixed | All use UTF-8 now |
| Usage examples | ✅ Fixed | Updated with encoding |

---

**The fix is now in GitHub master branch!** 🎉

Pull the latest code and restart Maya to get the fix.

