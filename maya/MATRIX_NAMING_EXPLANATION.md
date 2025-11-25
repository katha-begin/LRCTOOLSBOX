# Matrix Method - Unique DecomposeMatrix Nodes Per Asset

## Correct Approach: Namespace-Based Unique Naming

Each asset MUST have its own unique decomposeMatrix node, identified by the asset's namespace.

### Why Unique Names Matter

**Problem with shared/auto-renamed nodes:**
```
Asset 1: Creates EE_Body_Place3dTexture_decomp
Asset 2: Creates EE_Body_Place3dTexture_decomp1  ❌ Auto-renamed by Maya
Asset 3: Creates EE_Body_Place3dTexture_decomp2  ❌ Auto-renamed by Maya
```

This is **WRONG** because:
- Node names are not predictable
- Can't identify which asset owns which decomposeMatrix
- Cleanup becomes difficult
- Re-running build may create duplicate nodes

**Correct approach with namespace-based naming:**
```
Asset 1: Creates EE_CHAR_Kit_001_shade_Body_Place3dTexture_decomp  ✅
Asset 2: Creates EE_CHAR_Fox_001_shade_Body_Place3dTexture_decomp  ✅
Asset 3: Creates EE_CHAR_Bear_001_shade_Body_Place3dTexture_decomp ✅
```

This is **CORRECT** because:
- Each name is unique and predictable
- Easy to identify which asset owns which node
- Can re-run build without creating duplicates
- Easy to cleanup by namespace

## Naming Formula

```python
decomp_name = "EE_{}_decomp".format(dst_node.replace(":", "_"))
```

### Breakdown

| Component | Description | Example |
|-----------|-------------|---------|
| `dst_node` | Full Place3D node with namespace | `CHAR_Kit_001_shade:Body_Place3dTexture` |
| `.replace(":", "_")` | Replace colon with underscore | `CHAR_Kit_001_shade_Body_Place3dTexture` |
| `"EE_{}_decomp"` | Add prefix and suffix | `EE_CHAR_Kit_001_shade_Body_Place3dTexture_decomp` |

## Complete Examples

### Example 1: Character with Body Place3D

**Asset:** CHAR_Kit_001
- **Geo Namespace:** `CHAR_Kit_001`
- **Shader Namespace:** `CHAR_Kit_001_shade`
- **Source Transform:** `CHAR_Kit_001:Body_Grp`
- **Destination Place3D:** `CHAR_Kit_001_shade:Body_Place3dTexture`
- **DecomposeMatrix Name:** `EE_CHAR_Kit_001_shade_Body_Place3dTexture_decomp`

### Example 2: Different Character, Same Place3D Name

**Asset:** CHAR_Fox_001
- **Geo Namespace:** `CHAR_Fox_001`
- **Shader Namespace:** `CHAR_Fox_001_shade`
- **Source Transform:** `CHAR_Fox_001:Body_Grp`
- **Destination Place3D:** `CHAR_Fox_001_shade:Body_Place3dTexture`
- **DecomposeMatrix Name:** `EE_CHAR_Fox_001_shade_Body_Place3dTexture_decomp`

**Result:** Both assets have unique decomposeMatrix nodes! ✅

### Example 3: Same Asset, Multiple Place3D Nodes

**Asset:** CHAR_Kit_001
- **Body Place3D:** `CHAR_Kit_001_shade:Body_Place3dTexture`
  - DecomposeMatrix: `EE_CHAR_Kit_001_shade_Body_Place3dTexture_decomp`
- **Head Place3D:** `CHAR_Kit_001_shade:Head_Place3dTexture`
  - DecomposeMatrix: `EE_CHAR_Kit_001_shade_Head_Place3dTexture_decomp`
- **Tail Place3D:** `CHAR_Kit_001_shade:Tail_Place3dTexture`
  - DecomposeMatrix: `EE_CHAR_Kit_001_shade_Tail_Place3dTexture_decomp`

**Result:** Each Place3D node has its own unique decomposeMatrix! ✅

## Connection Logic

The function checks if the destination node already has a connection:

```python
# Check if destination node already has a decomposeMatrix connection
existing_decomp = None
for attr in ["translate", "rotate", "scale"]:
    connections = cmds.listConnections(
        "{}.{}".format(dst_node, attr),
        source=True, destination=False, type="decomposeMatrix"
    ) or []
    if connections:
        existing_decomp = connections[0]
        break

if existing_decomp and not force:
    # Verify it's connected to the correct source
    ...
```

This ensures:
1. **Idempotent:** Can re-run build without errors
2. **Validates:** Checks if existing connection is correct
3. **Safe:** Won't create duplicate connections

## Verification

After running the build, you can verify the decomposeMatrix nodes:

```python
import maya.cmds as cmds

# List all decomposeMatrix nodes
decomp_nodes = cmds.ls(type="decomposeMatrix") or []

print(f"Found {len(decomp_nodes)} decomposeMatrix nodes:")
for node in decomp_nodes:
    # Get input connection (source)
    input_conn = cmds.listConnections(node + ".inputMatrix", plugs=True) or []
    
    # Get output connections (destination)
    output_conn = cmds.listConnections(node + ".outputTranslate", plugs=True) or []
    
    print(f"\n{node}")
    print(f"  Input:  {input_conn[0] if input_conn else 'None'}")
    print(f"  Output: {output_conn[0] if output_conn else 'None'}")
```

Expected output:
```
Found 3 decomposeMatrix nodes:

EE_CHAR_Kit_001_shade_Body_Place3dTexture_decomp
  Input:  CHAR_Kit_001:Body_Grp.worldMatrix[0]
  Output: CHAR_Kit_001_shade:Body_Place3dTexture.translate

EE_CHAR_Fox_001_shade_Body_Place3dTexture_decomp
  Input:  CHAR_Fox_001:Body_Grp.worldMatrix[0]
  Output: CHAR_Fox_001_shade:Body_Place3dTexture.translate

EE_CHAR_Bear_001_shade_Body_Place3dTexture_decomp
  Input:  CHAR_Bear_001:Body_Grp.worldMatrix[0]
  Output: CHAR_Bear_001_shade:Body_Place3dTexture.translate
```

## Comparison with Constraint Method

| Method | Naming Pattern | Uniqueness |
|--------|---------------|------------|
| **Constraint** | `EE_{short}_pcon` | ❌ Not unique across assets (but works because constraints are parented under destination) |
| **Matrix** | `EE_{namespace}_{short}_decomp` | ✅ Unique across all assets |

**Why the difference?**

- **Constraints** are created as **child nodes** under the destination transform, so they're automatically scoped by the destination's namespace
- **DecomposeMatrix** nodes are **standalone utility nodes** in the scene, so they need globally unique names

## Summary

✅ **DO:** Use full namespace in decomposeMatrix name
```python
decomp_name = "EE_{}_decomp".format(dst_node.replace(":", "_"))
# Result: EE_CHAR_Kit_001_shade_Body_Place3dTexture_decomp
```

❌ **DON'T:** Use short name (causes collisions)
```python
decomp_name = "EE_{}_decomp".format(_short(dst_node))
# Result: EE_Body_Place3dTexture_decomp (not unique!)
```

Each asset gets its own unique, identifiable decomposeMatrix node! 🎯

