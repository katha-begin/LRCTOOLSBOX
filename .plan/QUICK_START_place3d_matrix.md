# Place3D Matrix Linker - Quick Start Guide

## 🚀 Implementation Summary

**Branch:** `feature/place3d-matrix-linker` ✅ Created  
**Status:** Ready to implement  
**Time Estimate:** 6-10 hours

---

## 📋 What We're Building

### The Problem
Current Place3D linker uses **constraints** (parentConstraint + scaleConstraint):
- Creates 2 nodes per link
- Moderate performance
- Clutters Maya scene

### The Solution
New **matrix-based** method using decomposeMatrix:
- Creates 1 node per link
- Better performance
- Cleaner scene graph
- Modern Maya best practice

### The Approach
**Non-breaking enhancement** with user choice:
- ✅ Keep existing constraint method (default)
- ✅ Add new matrix method (optional)
- ✅ User chooses via checkbox
- ✅ Standalone tab for testing

---

## 🎯 Key Implementation Points

### 1. Simplified Matrix Connection
```python
# NO parentInverseMatrix needed (user confirmed)
src_xform.worldMatrix[0] → decomposeMatrix.inputMatrix
decomposeMatrix.outputTranslate → dst_node.translate
decomposeMatrix.outputRotate → dst_node.rotate
decomposeMatrix.outputScale → dst_node.scale
decomposeMatrix.outputShear → dst_node.shear
```

### 2. No Separate Scale Handling
- Scale is automatically handled by decomposeMatrix
- No need for special scale constraint logic
- Simpler implementation than constraint method

### 3. Node Naming
- decomposeMatrix node: `EE_{shortNodeName}_decomp`
- Consistent with existing `EE_{nodeName}_pcon/scon` pattern

---

## 📝 Implementation Checklist

### Phase 1: Core Functions (2-3 hours)
```
[ ] TASK-001: Create _matrix_transfer_transform() function
    - Create decomposeMatrix node
    - Connect worldMatrix → inputMatrix
    - Connect outputs → translate/rotate/scale/shear
    - Add dry_run and force options
    - Test in Maya Script Editor

[ ] TASK-002: Create _delete_existing_matrix_connections() function
    - Find connected decomposeMatrix nodes
    - Delete matrix nodes
    - Test cleanup

[ ] TASK-003: Test core functions
    - Create test scene
    - Verify connections work
    - Compare with constraint method
```

### Phase 2: New UI Tab (2-3 hours)
```
[ ] TASK-004: Create MatrixPlace3DTab class
    - Copy Place3DTab structure
    - Update to use matrix method
    - Add UI labels

[ ] TASK-005: Add tab to main window
    - Insert after existing Place3D tab
    - Test tab switching

[ ] TASK-006: Test standalone tab
    - Test scan operation
    - Test apply operation
    - Test with multiple pairs
```

### Phase 3: Shot Build Integration (1-2 hours)
```
[ ] TASK-007: Add checkbox to ShotBuildTab
    - Add "Use Matrix Method" checkbox
    - Add tooltip
    - Default to unchecked (constraint method)

[ ] TASK-008: Update _auto_place3d_linker()
    - Check checkbox state
    - Call appropriate function
    - Update logging

[ ] TASK-009: Update _auto_place3d_single_asset()
    - Check checkbox state
    - Call appropriate function
    - Update logging
```

### Phase 4: Testing & Documentation (1-2 hours)
```
[ ] TASK-010: Integration testing
    - Test complete shot build (matrix)
    - Test complete shot build (constraint)
    - Test both methods in same scene

[ ] TASK-011: Update documentation
    - Update docstrings
    - Add comments
    - Update this plan

[ ] TASK-012: Code cleanup
    - Remove debug code
    - Ensure consistent style
    - Final error handling
```

---

## 🔧 Code Snippets

### Core Matrix Function Template
```python
def _matrix_transfer_transform(src_xform, dst_node, force=False, dry_run=False):
    """Transfer transform using matrix decomposition."""
    if dry_run:
        return "would create decomposeMatrix connection"
    
    try:
        # Unlock transform attributes
        _unlock_trs(dst_node)
        
        # Create decomposeMatrix node
        decomp_name = "EE_{}_decomp".format(_short(dst_node))
        decomp = cmds.createNode("decomposeMatrix", name=decomp_name)
        
        # Connect worldMatrix → inputMatrix
        cmds.connectAttr(
            "{}.worldMatrix[0]".format(src_xform),
            "{}.inputMatrix".format(decomp),
            force=True
        )
        
        # Connect outputs → dst_node
        cmds.connectAttr("{}.outputTranslate".format(decomp), "{}.translate".format(dst_node), force=True)
        cmds.connectAttr("{}.outputRotate".format(decomp), "{}.rotate".format(dst_node), force=True)
        cmds.connectAttr("{}.outputScale".format(decomp), "{}.scale".format(dst_node), force=True)
        cmds.connectAttr("{}.outputShear".format(decomp), "{}.shear".format(dst_node), force=True)
        
        return "matrix-linked"
    except Exception as e:
        return "error: {}".format(e)
```

### Checkbox Integration Template
```python
# In _auto_place3d_linker() or _auto_place3d_single_asset()
if self.use_matrix_method_checkbox.isChecked():
    # Use matrix method
    result = _matrix_transfer_transform(xform, place, force=False, dry_run=False)
    method = "Matrix"
else:
    # Use constraint method (existing)
    snap_result = _snap_trs_world(xform, place, dry_run=False)
    result = _parent_and_scale_constrain(xform, place, force=False, dry_run=False)
    method = "Constraint"

self._log("[PLACE3D] {} <-- {} :: {} ({})".format(place, xform, result, method))
```

---

## 🧪 Testing Commands

### Test in Maya Script Editor
```python
# Test matrix transfer
import maya.cmds as cmds

# Create test objects
src = cmds.polyCube(name="test_src")[0]
dst = cmds.shadingNode("place3dTexture", asUtility=True, name="test_dst")

# Apply matrix transfer
result = _matrix_transfer_transform(src, dst)
print("Result:", result)

# Verify connections
print("Connections:", cmds.listConnections(dst, source=True, destination=False))

# Test cleanup
_delete_existing_matrix_connections(dst)
print("After cleanup:", cmds.listConnections(dst, source=True, destination=False))
```

---

## 📊 Success Criteria

Before marking complete:
- ✅ Matrix function creates correct connections
- ✅ Cleanup function removes connections
- ✅ Standalone tab works independently
- ✅ Shot build works with matrix method
- ✅ Shot build works with constraint method (default)
- ✅ No breaking changes to existing code
- ✅ Code is clean and documented

---

## 🚨 Important Notes

### What NOT to Do
- ❌ Don't remove or modify `_parent_and_scale_constrain()`
- ❌ Don't change default behavior (keep constraint as default)
- ❌ Don't add parentInverseMatrix (simplified approach)
- ❌ Don't handle scale separately (decomposeMatrix handles it)

### What TO Do
- ✅ Keep constraint method working
- ✅ Add matrix method as alternative
- ✅ Let user choose via checkbox
- ✅ Test both methods thoroughly
- ✅ Document everything

---

## 📁 Files to Modify

### Main File
- `maya/mockup/igl_shot_build.py`

### Sections to Add/Modify
1. **Add new functions** (after line 4763):
   - `_matrix_transfer_transform()`
   - `_delete_existing_matrix_connections()`

2. **Add new class** (after line 4954):
   - `MatrixPlace3DTab`

3. **Modify ShotBuildTab** (around line 340):
   - Add checkbox in `_build()` method

4. **Modify _auto_place3d_linker** (line 2390):
   - Add method selection logic

5. **Modify _auto_place3d_single_asset** (line 3062):
   - Add method selection logic

6. **Modify main window** (around line 5734):
   - Add new tab

---

## 🔗 Related Documents

- **Full Plan:** `.plan/implement_feature_place3d_matrix.md`
- **Summary:** `.plan/FEATURE_SUMMARY_place3d_matrix.md`
- **This Guide:** `.plan/QUICK_START_place3d_matrix.md`

---

## 🎯 Next Action

**Start with TASK-001:**
1. Open `maya/mockup/igl_shot_build.py`
2. Find line 4763 (after `_parent_and_scale_constrain()`)
3. Add `_matrix_transfer_transform()` function
4. Test in Maya Script Editor
5. Move to TASK-002

---

**Ready to implement!** 🚀

