# Place3D Matrix Linker - Feature Implementation Plan

## 📋 Overview

This document outlines the implementation plan for adding a new **Matrix-Based Place3D Linker** as an alternative to the existing constraint-based method. The new method will use Maya's `decomposeMatrix` node for cleaner, more performant transform connections.

**Branch:** `feature/place3d-matrix-linker`
**Target File:** `maya/mockup/igl_shot_build.py`
**Status:** Implementation Complete - Ready for Testing

**Progress:**
- ✅ Phase 1: Core Functions (COMPLETE)
- ✅ Phase 2: New UI Tab (COMPLETE)
- ✅ Phase 3: Shot Build Integration (COMPLETE)
- ⏳ Phase 4: Testing & Documentation (IN PROGRESS)

---

## 🎯 Goals

1. **Non-Breaking Implementation:** Add new matrix method without affecting existing constraint-based workflow
2. **User Choice:** Provide UI checkbox to let users choose between constraint and matrix methods
3. **Standalone UI Tab:** Create dedicated tab for testing and using the new matrix method
4. **Performance Improvement:** Leverage matrix connections for better performance
5. **Cleaner Scene:** Reduce constraint node clutter in Maya scenes

---

## 🏗️ Architecture Design

### Method Comparison

| Aspect | Current (Constraint) | New (Matrix) |
|--------|---------------------|--------------|
| **Connection Type** | parentConstraint + scaleConstraint | decomposeMatrix node |
| **Node Count** | 2 nodes per link | 1 node per link |
| **Performance** | Moderate (constraint evaluation) | Better (direct matrix decomposition) |
| **Maintain Offset** | Parent: No, Scale: Yes | Handled via initial snap |
| **Scene Cleanup** | More constraint nodes | Cleaner node graph |

### New Components

```
igl_shot_build.py
├── [NEW] _matrix_transfer_transform()          # Core matrix linking function
├── [NEW] _delete_existing_matrix_connections() # Cleanup function
├── [NEW] MatrixPlace3DTab                      # New UI tab
├── [MODIFIED] ShotBuildTab                     # Add method selection checkbox
├── [MODIFIED] _auto_place3d_linker()           # Support both methods
├── [MODIFIED] _auto_place3d_single_asset()     # Support both methods
└── [KEEP] _parent_and_scale_constrain()        # Keep existing for backward compatibility
```

---

## 🔧 Technical Implementation

### Step 1: Core Matrix Function

**Function:** `_matrix_transfer_transform(src_xform, dst_node, force=False, dry_run=False)`

**Implementation Details:**

```python
def _matrix_transfer_transform(src_xform, dst_node, force=False, dry_run=False):
    """
    Transfer transform from src to dst using matrix decomposition.
    
    Method:
    1. Create decomposeMatrix node
    2. Connect src_xform.worldMatrix[0] → decomposeMatrix.inputMatrix
    3. Connect decomposeMatrix outputs → dst_node (translate, rotate, scale, shear)
    
    Args:
        src_xform (str): Source transform node
        dst_node (str): Destination place3dTexture node
        force (bool): If True, remove existing matrix connections
        dry_run (bool): If True, only report what would be done
    
    Returns:
        str: Status message ("matrix-linked", "error: ...", etc.)
    """
```

**Connection Schema:**
```
src_xform.worldMatrix[0] 
    ↓
decomposeMatrix.inputMatrix
    ↓
    ├─→ decomposeMatrix.outputTranslate → dst_node.translate
    ├─→ decomposeMatrix.outputRotate → dst_node.rotate
    ├─→ decomposeMatrix.outputScale → dst_node.scale
    └─→ decomposeMatrix.outputShear → dst_node.shear
```

**Node Naming Convention:**
- decomposeMatrix node: `EE_{shortNodeName}_decomp`

**Key Points:**
- ✅ No parentInverseMatrix needed (simplified approach)
- ✅ Scale handled automatically by decomposeMatrix
- ✅ Shear attribute included for completeness
- ✅ Unlock all transform attributes before connecting

---

### Step 2: Cleanup Function

**Function:** `_delete_existing_matrix_connections(node)`

**Implementation Details:**

```python
def _delete_existing_matrix_connections(node):
    """
    Remove existing decomposeMatrix connections from node.
    
    Searches for:
    - decomposeMatrix nodes connected to translate/rotate/scale/shear
    - Removes the decomposeMatrix node itself
    
    Args:
        node (str): Node to clean up
    """
```

**Cleanup Process:**
1. Find all decomposeMatrix nodes connected to node's transform attributes
2. Delete the decomposeMatrix nodes
3. Unlock transform attributes if needed

---

### Step 3: New UI Tab - MatrixPlace3DTab

**Class:** `MatrixPlace3DTab(QtWidgets.QWidget)`

**UI Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ Matrix-Based Place3D Linker                             │
├─────────────────────────────────────────────────────────┤
│ Geo Suffix:  [_Grp        ]  Place3D Suffix: [_Place3dTexture] │
│                                                         │
│ Options:                                                │
│ ☐ Dry Run    ☐ Force Replace    ☑ Allow Fuzzy Match   │
│                                                         │
│ [Scan (Place3D → Geo)]  [Apply Matrix Transfer]        │
├─────────────────────────────────────────────────────────┤
│ Table: place3dTexture | Transform | Match | Result     │
│ ...                                                     │
├─────────────────────────────────────────────────────────┤
│ Log Output                                              │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Same scanning logic as existing Place3DTab
- Uses `_matrix_transfer_transform()` instead of constraints
- Shares namespace dropdowns from main window
- Independent testing environment

---

### Step 4: Shot Build Integration

**Modification:** `ShotBuildTab` class

**Add UI Checkbox:**
```python
# In Scene Setup section
self.use_matrix_method_checkbox = QtWidgets.QCheckBox("Use Matrix Method (instead of Constraints)")
self.use_matrix_method_checkbox.setToolTip("Use decomposeMatrix nodes instead of parent/scale constraints")
self.use_matrix_method_checkbox.setChecked(False)  # Default to constraint method
```

**Update Build Functions:**

1. **`_auto_place3d_linker()`** (Line 2390)
   - Check `self.use_matrix_method_checkbox.isChecked()`
   - Call appropriate function based on checkbox state

2. **`_auto_place3d_single_asset()`** (Line 3062)
   - Check `self.use_matrix_method_checkbox.isChecked()`
   - Call appropriate function based on checkbox state

**Implementation Pattern:**
```python
# Determine which method to use
if self.use_matrix_method_checkbox.isChecked():
    result = _matrix_transfer_transform(xform, place, force=False, dry_run=False)
    method_name = "Matrix"
else:
    snap_result = _snap_trs_world(xform, place, dry_run=False)
    result = _parent_and_scale_constrain(xform, place, force=False, dry_run=False)
    method_name = "Constraint"

self._log("[PLACE3D] {} <-- {} :: {} ({})".format(place, xform, result, method_name))
```

---

## 📝 Implementation Tasks

### Phase 1: Core Functions (2-3 hours) ✅ COMPLETE

- [x] **TASK-001:** Create `_matrix_transfer_transform()` function ✅
  - Implement decomposeMatrix node creation
  - Connect worldMatrix to inputMatrix
  - Connect outputs to translate/rotate/scale/shear
  - Add error handling and dry_run support
  - Test with simple Place3D pairs

- [x] **TASK-002:** Create `_delete_existing_matrix_connections()` function ✅
  - Find connected decomposeMatrix nodes
  - Delete matrix nodes
  - Test cleanup functionality

- [ ] **TASK-003:** Test core functions in Maya Script Editor
  - Create test scene with Place3D pairs
  - Verify matrix connections work correctly
  - Verify cleanup works correctly
  - Compare behavior with constraint method

### Phase 2: New UI Tab (2-3 hours) ✅ COMPLETE

- [x] **TASK-004:** Create `MatrixPlace3DTab` class ✅
  - Copy structure from existing `Place3DTab`
  - Update UI labels to indicate "Matrix Method"
  - Wire scan button to use existing `_find_place3d_pairs_by_place()`
  - Wire apply button to use `_matrix_transfer_transform()`

- [x] **TASK-005:** Add tab to main window ✅
  - Insert new tab after existing Place3D tab
  - Test tab switching and functionality
  - Verify namespace sharing works correctly

- [ ] **TASK-006:** Test standalone tab functionality
  - Test scan operation
  - Test apply operation (dry run and real)
  - Test force replace option
  - Test with multiple Place3D pairs

### Phase 3: Shot Build Integration (1-2 hours) ✅ COMPLETE

- [x] **TASK-007:** Add method selection checkbox to ShotBuildTab ✅
  - Add checkbox in Scene Setup section
  - Add tooltip explaining the difference
  - Set default to constraint method (backward compatible)

- [x] **TASK-008:** Update `_auto_place3d_linker()` function ✅
  - Add method selection logic
  - Call appropriate function based on checkbox
  - Update logging to indicate which method was used

- [x] **TASK-009:** Update `_auto_place3d_single_asset()` function ✅
  - Add method selection logic
  - Call appropriate function based on checkbox
  - Update logging to indicate which method was used

### Phase 4: Testing & Documentation (1-2 hours)

- [ ] **TASK-010:** Integration testing
  - Test complete shot build with matrix method
  - Test complete shot build with constraint method
  - Test switching between methods
  - Test with various asset types (CHAR, PROP, SETS)

- [ ] **TASK-011:** Update documentation
  - Update function docstrings
  - Add comments explaining matrix method
  - Update this implementation plan with results

- [ ] **TASK-012:** Code cleanup
  - Remove debug print statements
  - Ensure consistent code style
  - Add final error handling

---

## 🧪 Testing Strategy

### Unit Tests

1. **Matrix Function Test:**
   - Create simple transform and place3dTexture
   - Apply matrix transfer
   - Verify connections exist
   - Verify transform values match

2. **Cleanup Function Test:**
   - Create matrix connections
   - Run cleanup
   - Verify nodes are removed
   - Verify no errors

### Integration Tests

1. **Standalone Tab Test:**
   - Load test scene with multiple Place3D pairs
   - Scan and apply matrix method
   - Verify all pairs are linked correctly

2. **Shot Build Test:**
   - Build complete shot with matrix method enabled
   - Verify all assets have matrix connections
   - Compare with constraint method results

3. **Mixed Method Test:**
   - Build some assets with constraints
   - Build other assets with matrix
   - Verify both methods coexist

---

## 📊 Success Criteria

- ✅ New matrix method works correctly for all Place3D pairs
- ✅ Existing constraint method continues to work unchanged
- ✅ Users can choose method via checkbox
- ✅ Standalone tab allows independent testing
- ✅ No breaking changes to existing workflows
- ✅ Performance improvement measurable (optional)
- ✅ Code is clean and well-documented

---

## 🚨 Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing workflows | Keep constraint method as default, test thoroughly |
| Matrix method doesn't work for all cases | Extensive testing with various asset types |
| Performance issues | Test with large scenes, compare with constraints |
| User confusion | Clear UI labels, tooltips, documentation |

---

## 📅 Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Core Functions | 2-3 hours | None |
| Phase 2: New UI Tab | 2-3 hours | Phase 1 complete |
| Phase 3: Shot Build Integration | 1-2 hours | Phase 1 complete |
| Phase 4: Testing & Documentation | 1-2 hours | All phases complete |
| **Total** | **6-10 hours** | - |

---

## 🔄 Future Enhancements

1. **Migration Tool:** Convert existing constraint-based scenes to matrix method
2. **Performance Metrics:** Add timing comparison between methods
3. **Batch Conversion:** Convert all Place3D links in scene at once
4. **Preference Storage:** Remember user's method preference
5. **Visual Feedback:** Highlight which method is used in scene (node colors, etc.)

---

## 📚 References

- Maya decomposeMatrix node documentation
- Current constraint implementation: Lines 4749-4763
- Place3D tab implementation: Lines 4843-4954
- Shot build integration points: Lines 2390-2448, 3062-3082

---

## ✅ Acceptance Criteria

Before merging this feature:

1. All tasks completed and tested
2. No regression in existing constraint method
3. Matrix method works in all contexts (standalone tab, shot build, single asset)
4. Code reviewed and cleaned
5. Documentation updated
6. User can successfully choose between methods
7. Both methods can coexist in same scene

---

**Last Updated:** 2025-11-07  
**Status:** Ready for Implementation  
**Next Step:** Begin TASK-001 - Create core matrix function

