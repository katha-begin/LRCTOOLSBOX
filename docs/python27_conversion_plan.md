# Python 2.7 Conversion Plan

## Files to Convert

1. `maya/mockup/camera_reference_cleanup.py` → `maya/mockup/camera_reference_cleanup_py27.py`
2. `maya/mockup/ref2ints.py` → `maya/mockup/ref2ints_py27.py`
3. `maya/mockup/sets_instance_test.py` → `maya/mockup/sets_instance_test_py27.py`

## Required Changes for Python 2.7 Compatibility

### 1. F-String Conversion (ref2ints.py - 75+ instances)

**Python 3 (f-strings)**:
```python
print(f"Found {count} items")
self.log(f"Error: {error}")
```

**Python 2.7 (.format())**:
```python
print("Found {} items".format(count))
self.log("Error: {}".format(error))
```

### 2. Maya API Changes (camera_reference_cleanup.py)

**Python 3**:
```python
import maya.api.OpenMaya as om2  # OpenMaya 2.0 (Maya 2017+)
```

**Python 2.7**:
```python
import maya.OpenMaya as om  # OpenMaya 1.0 (compatible with older Maya)
```

**Note**: This requires rewriting frustum calculation code to use OpenMaya 1.0 API

### 3. PySide Version Handling (All files)

**Current** (already compatible):
```python
try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance
```

**Python 2.7** (add PySide fallback):
```python
try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance
except ImportError:
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        from shiboken6 import wrapInstance
    except ImportError:
        from PySide import QtGui, QtCore
        from PySide import QtGui as QtWidgets  # PySide uses QtGui for widgets
        from shiboken import wrapInstance
```

### 4. Print Function (All files)

**Already compatible** - all files use `print()` function style

### 5. Dictionary Methods

**Already compatible** - no issues found with `.keys()`, `.values()`, `.items()`

### 6. String Formatting

**sets_instance_test.py**: Already uses `.format()` - ✅ Compatible
**ref2ints.py**: Uses f-strings extensively - ❌ Needs conversion

## Conversion Statistics

### camera_reference_cleanup.py
- **F-strings**: 0 (already uses .format())
- **Maya API**: Uses `maya.api.OpenMaya` (needs conversion to OpenMaya 1.0)
- **PySide**: Already has fallback
- **Estimated changes**: ~50 lines (API conversion)

### ref2ints.py
- **F-strings**: 75+ instances
- **Maya API**: Uses `maya.cmds` only (compatible)
- **PySide**: Already has fallback
- **Estimated changes**: ~75 lines (f-string conversion)

### sets_instance_test.py
- **F-strings**: 0 (already uses .format())
- **Maya API**: Uses `maya.cmds` only (compatible)
- **PySide**: Already has fallback
- **Estimated changes**: ~5 lines (PySide fallback enhancement)

## Total Estimated Changes
- **Lines to modify**: ~130 lines across 3 files
- **New files to create**: 3 files with `_py27` suffix

## Testing Recommendations

After conversion, test in Maya 2016 or earlier (Python 2.7) environment:

1. **Import Test**: Verify all modules import without errors
2. **UI Test**: Open each tool's UI and verify layout
3. **Functionality Test**: Test core functions (analyze, convert, build)
4. **Maya API Test**: Verify frustum calculation works (camera_reference_cleanup)

## Proceed with Conversion?

This will create 3 new files with Python 2.7 compatible code. The original Python 3 versions will remain unchanged.

