# Instance Shader Assignment Fix - Research & Implementation

## Problem Description

When using `cmds.instance()` to create geometry instances in Maya, the instances were rendering with the default lambert1 shader instead of the correct shaders from the master geometry.

### Root Cause

1. **Maya's Automatic Behavior**: When `cmds.instance()` creates an instance, Maya automatically connects it to `initialShadingGroup` (lambert1)
2. **Dual Connections**: This causes instances to have TWO shader connections:
   - `instObjGroups[0]` → `initialShadingGroup` (lambert1) - **WRONG**
   - `instObjGroups[1]` → Correct shading group - **CORRECT**
3. **Render Priority**: The connection to `initialShadingGroup` takes priority, causing incorrect rendering

## Initial Attempted Solution (INCORRECT)

**Approach**: Disconnect instance from `initialShadingGroup`

```python
def _disconnect_from_initial_shading_group(instance_transform):
    # Find connections to initialShadingGroup
    # Disconnect them
    cmds.disconnectAttr(src_plug, dst_plug)
```

**Problem with this approach**:
- Viewport displays geometry as **GREEN** (indicating no shader assigned)
- While rendering might work, viewport feedback is broken
- Maya interprets disconnected geometry as having no shader

## Research Findings

### Maya Viewport Green Color
- **Green in viewport = No shader assigned**
- This is Maya's standard way of indicating missing shader assignments
- Occurs when geometry has no connection to any shading group

### Maya Instance Shading System
- Instances share the same shape node as the master
- Each instance has its own `instObjGroups[n]` entry
- Shading groups connect via: `shape.instObjGroups[n]` → `shadingGroup.dagSetMembers[m]`

### Correct Maya Workflow
- Use `cmds.sets(shape, edit=True, forceElement=shadingGroup)` to assign shaders
- This command:
  1. Removes any existing shading group connections (including `initialShadingGroup`)
  2. Creates proper connection to the specified shading group
  3. Ensures both viewport and render use the correct shader

## Correct Solution (IMPLEMENTED)

**Approach**: Re-assign correct shaders to instance shapes

```python
def _reassign_shaders_to_instance(instance_transform, master_transform):
    """
    Re-assign correct shaders to instance by copying master's shader assignments.
    """
    # 1. Get master's shape nodes
    master_shapes = cmds.listRelatives(master_transform, allDescendents=True, type="mesh", fullPath=True)
    
    # 2. Get instance's shape nodes
    instance_shapes = cmds.listRelatives(instance_transform, allDescendents=True, type="mesh", fullPath=True)
    
    # 3. For each master shape, find its shading groups
    for master_shape in master_shapes:
        shading_groups = cmds.listConnections(
            f"{master_shape}.instObjGroups",
            type="shadingEngine",
            source=False,
            destination=True
        )
        
        # Filter out initialShadingGroup
        shading_groups = [sg for sg in shading_groups if sg != "initialShadingGroup"]
        
        # 4. Find matching instance shape
        # 5. Re-assign shading groups to instance
        for sg in shading_groups:
            cmds.sets(instance_shape, e=True, forceElement=sg)
```

### Why This Works

1. **Automatic Cleanup**: `cmds.sets()` with `forceElement` automatically removes existing connections
2. **Proper Connection**: Creates correct connection to the right shading group
3. **Viewport Display**: Geometry displays with correct shader (not green)
4. **Render Correctness**: Rendering uses the correct shader

## Implementation

### Files Modified
1. `maya/mockup/sets_instance_test.py` - Instance Set Builder tool
2. `maya/mockup/ref2ints.py` - Ref2Instance converter tool

### Changes Made
- Renamed `_disconnect_from_initial_shading_group()` → `_reassign_shaders_to_instance()`
- Added `master_transform` parameter to find master's shading groups
- Changed logic from disconnect to re-assign using `cmds.sets()`

### Commit
**19fea12** - fix(instance-shader): Re-assign shaders instead of disconnecting to prevent green viewport

## Testing Recommendations

1. **Viewport Test**: Check that instances display with correct colors (not green)
2. **Render Test**: Verify instances render with correct shaders
3. **Multi-Material Test**: Test geometry with multiple materials assigned to different faces
4. **Renderer Test**: Test with Arnold, Redshift, or other renderers in use

## References

- Maya Documentation: `cmds.sets()` with `forceElement` parameter
- Maya Forums: Green viewport indicates no shader assignment
- Tech-Artists.org: Maya instance shader assignment patterns

