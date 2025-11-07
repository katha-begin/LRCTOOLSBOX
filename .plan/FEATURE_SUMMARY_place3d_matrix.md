# Place3D Matrix Linker - Feature Summary

## 🎯 Quick Overview

**Feature:** Matrix-Based Place3D Linker  
**Branch:** `feature/place3d-matrix-linker`  
**Type:** Non-breaking enhancement  
**Estimated Time:** 6-10 hours

---

## 📌 What We're Building

A new **matrix-based method** for linking Place3D texture nodes to geometry transforms, as an alternative to the current constraint-based approach.

### Current Method (Constraint-Based)
```
Geometry Transform
    ↓ (parentConstraint)
    ↓ (scaleConstraint)
Place3D Texture Node
```
- Creates 2 constraint nodes per link
- Moderate performance
- More nodes in scene

### New Method (Matrix-Based)
```
Geometry Transform.worldMatrix[0]
    ↓
decomposeMatrix.inputMatrix
    ↓
    ├─→ outputTranslate → Place3D.translate
    ├─→ outputRotate → Place3D.rotate
    ├─→ outputScale → Place3D.scale
    └─→ outputShear → Place3D.shear
```
- Creates 1 decomposeMatrix node per link
- Better performance
- Cleaner scene graph
- Direct matrix decomposition

---

## 🎨 User Experience

### 1. Standalone Testing Tab
Users get a new tab: **"Matrix Place3D Linker"**
- Same interface as existing Place3D tab
- Uses matrix method instead of constraints
- Independent testing environment

### 2. Shot Build Integration
Users get a checkbox in Shot Build tab:
```
☐ Use Matrix Method (instead of Constraints)
```
- **Unchecked (default):** Uses existing constraint method
- **Checked:** Uses new matrix method
- Works in all build workflows

---

## 🔧 Technical Changes

### New Functions
1. `_matrix_transfer_transform()` - Core matrix linking function
2. `_delete_existing_matrix_connections()` - Cleanup function
3. `MatrixPlace3DTab` - New UI tab class

### Modified Functions
1. `_auto_place3d_linker()` - Add method selection
2. `_auto_place3d_single_asset()` - Add method selection
3. `ShotBuildTab._build()` - Add checkbox UI

### Unchanged Functions
- `_parent_and_scale_constrain()` - Keep for backward compatibility
- `_snap_trs_world()` - Still used for initial positioning
- All other shot build functions

---

## ✅ Key Benefits

1. **Non-Breaking:** Existing workflows continue to work
2. **User Choice:** Users decide which method to use
3. **Better Performance:** Matrix decomposition is faster than constraints
4. **Cleaner Scenes:** Fewer nodes in Maya outliner
5. **Future-Proof:** Modern Maya best practice

---

## 📋 Implementation Steps (Simplified)

### Step 1: Create Core Matrix Function
- Build `_matrix_transfer_transform()` function
- Create decomposeMatrix node
- Connect worldMatrix → inputMatrix
- Connect outputs to translate/rotate/scale/shear

### Step 2: Create Standalone UI Tab
- Copy existing Place3D tab structure
- Replace constraint calls with matrix calls
- Add to main window tab widget

### Step 3: Integrate with Shot Build
- Add checkbox to Scene Setup section
- Update auto Place3D functions to check checkbox
- Call appropriate method based on user choice

### Step 4: Test Everything
- Test standalone tab
- Test shot build with matrix method
- Test shot build with constraint method
- Verify both methods can coexist

---

## 🧪 Testing Checklist

- [ ] Matrix function works with simple Place3D pair
- [ ] Cleanup function removes matrix connections
- [ ] Standalone tab scans and applies correctly
- [ ] Shot build works with matrix method enabled
- [ ] Shot build works with matrix method disabled (default)
- [ ] Both methods can exist in same scene
- [ ] No errors in Maya script editor
- [ ] Performance is equal or better than constraints

---

## 📊 Success Metrics

| Metric | Target |
|--------|--------|
| Breaking Changes | 0 |
| New Bugs | 0 |
| User Choice | ✅ Checkbox works |
| Performance | Equal or better |
| Code Quality | Clean, documented |

---

## 🚀 Deployment Plan

1. **Development:** Implement on `feature/place3d-matrix-linker` branch
2. **Testing:** Thorough testing in Maya with real assets
3. **Review:** Code review and cleanup
4. **Merge:** Merge to main branch when all tests pass
5. **Documentation:** Update user documentation

---

## 💡 Why This Approach?

### Why Not Replace Constraints Entirely?
- **Backward Compatibility:** Existing scenes may rely on constraints
- **User Familiarity:** Some users prefer constraints
- **Risk Mitigation:** Gradual adoption is safer

### Why Add a Checkbox?
- **User Control:** Let users choose what works for them
- **Testing:** Easy to compare both methods
- **Migration Path:** Users can switch when ready

### Why a Standalone Tab?
- **Testing:** Independent environment for validation
- **Learning:** Users can experiment safely
- **Debugging:** Easier to isolate issues

---

## 📝 Notes for Implementation

### Simplified Matrix Connection
Based on user feedback, we're using a **simplified approach**:
- ✅ Direct worldMatrix → decomposeMatrix connection
- ❌ No parentInverseMatrix multiplication needed
- ✅ Scale handled automatically by decomposeMatrix
- ✅ Shear included for completeness

### Node Naming Convention
- decomposeMatrix nodes: `EE_{nodeName}_decomp`
- Consistent with existing `EE_{nodeName}_pcon/scon` pattern

### Default Behavior
- **Default:** Constraint method (unchecked)
- **Reason:** Backward compatibility and user familiarity
- **Future:** May switch default after user feedback

---

## 🔗 Related Documents

- **Full Implementation Plan:** `.plan/implement_feature_place3d_matrix.md`
- **Current Implementation:** `maya/mockup/igl_shot_build.py` (Lines 4717-4763)
- **Place3D Tab:** `maya/mockup/igl_shot_build.py` (Lines 4843-4954)

---

## 👥 Stakeholders

- **Users:** Get better performance and cleaner scenes
- **Developers:** Modern, maintainable code
- **Pipeline:** Non-breaking enhancement to existing workflow

---

**Status:** ✅ Plan Complete - Ready for Implementation  
**Next Action:** Begin TASK-001 - Create `_matrix_transfer_transform()` function

