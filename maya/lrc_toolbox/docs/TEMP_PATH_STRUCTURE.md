# Temporary File Path Structure

## Overview

The Batch Render Manager uses a **context-aware hierarchical directory structure** for temporary render files. This ensures organized file management and easy cleanup based on project structure.

---

## Path Structure

### Shot Scenes

**Directory Structure:**
```
{project_root}/scene/.tmp/{episode}/{sequence}/{shot}/{department}/{layer_name}/
```

**Filename Format:**
```
render_{shot}_{department}_{version}_{timestamp}_{process_id}.ma
```

**Full Example:**
```
V:/SWA/all/scene/.tmp/Ep01/sq0010/SH0010/lighting/MASTER_BG_A/render_SH0010_lighting_v001_20250115_143022_12345.ma
```

**Path Components:**
- `V:/SWA/all/scene/` - Project scene root
- `.tmp/` - Hidden temp directory
- `Ep01/` - Episode
- `sq0010/` - Sequence
- `SH0010/` - Shot
- `lighting/` - Department
- `MASTER_BG_A/` - Render layer name
- `render_SH0010_lighting_v001_20250115_143022_12345.ma` - Temp file

---

### Asset Scenes

**Directory Structure:**
```
{project_root}/asset/.tmp/{category}/{subcategory}/{asset}/{department}/{layer_name}/
```

**Filename Format:**
```
render_{asset}_{department}_{version}_{timestamp}_{process_id}.ma
```

**Full Example:**
```
V:/SWA/all/asset/.tmp/characters/main/hero_char/lighting/HERO_CHAR_BG_A/render_hero_char_lighting_v002_20250115_143022_12347.ma
```

**Path Components:**
- `V:/SWA/all/asset/` - Project asset root
- `.tmp/` - Hidden temp directory
- `characters/` - Category
- `main/` - Subcategory
- `hero_char/` - Asset name
- `lighting/` - Department
- `HERO_CHAR_BG_A/` - Render layer name
- `render_hero_char_lighting_v002_20250115_143022_12347.ma` - Temp file

---

### Fallback (No Context Detected)

**Directory Structure:**
```
~/Documents/maya_batch_tmp/{layer_name}/
```

**Filename Format:**
```
render_{scene_name}_{version}_{timestamp}_{process_id}.ma
```

**Full Example (Windows):**
```
C:/Users/artist/Documents/maya_batch_tmp/MASTER_BG_A/render_test_scene_v001_20250115_143022_12349.ma
```

**Full Example (Mac/Linux):**
```
/Users/artist/Documents/maya_batch_tmp/MASTER_BG_A/render_test_scene_v001_20250115_143022_12349.ma
```

**When Fallback is Used:**
- Scene file not saved in standard project structure
- Scene path doesn't match shot/asset patterns
- Scene file saved in non-standard location (Desktop, Downloads, etc.)

---

## Filename Components

### Version Number

**Extracted from scene path:**
- Pattern: `_v001`, `_v002`, `_v0001`, etc.
- Case-insensitive
- Included in temp filename if found
- Example: `SH0010_lighting_v001.ma` → `v001`

### Timestamp

**Format:** `YYYYMMDD_HHMMSS`
- Example: `20250115_143022` = January 15, 2025, 2:30:22 PM
- Ensures unique filenames
- Useful for sorting by creation time

### Process ID

**Format:** Numeric string
- Unique identifier for each render process
- Helps track which temp file belongs to which render job
- Example: `12345`

---

## Benefits

### 1. Organized Structure
- ✅ Mirrors project directory structure
- ✅ Easy to navigate and find files
- ✅ Clear separation by shot/asset/layer

### 2. Easy Cleanup
- ✅ Delete entire shot/asset directories
- ✅ Layer-specific cleanup
- ✅ Department-specific cleanup
- ✅ Age-based cleanup across all locations

### 3. Context Awareness
- ✅ Automatically detects shot/asset context
- ✅ Uses project structure conventions
- ✅ Fallback for non-standard locations

### 4. Version Tracking
- ✅ Version number in filename
- ✅ Easy to identify which scene version was rendered
- ✅ Helps with debugging and troubleshooting

### 5. Hidden Directory
- ✅ `.tmp` directory is hidden (starts with dot)
- ✅ Doesn't clutter project directories
- ✅ Easy to exclude from version control

---

## Context Detection

### Shot Pattern

**Scene Path Pattern:**
```
{root}/scene/{episode}/{sequence}/{shot}/{department}/...
```

**Examples:**
- `V:/SWA/all/scene/Ep01/sq0010/SH0010/lighting/version/SH0010_lighting_v001.ma`
- `V:/SWA/all/scene/Ep02/sq0050/SH0050/compositing/SH0050_comp_v003.ma`

**Detected Components:**
- Episode: `Ep01`, `Ep02`, etc.
- Sequence: `sq0010`, `sq0050`, etc.
- Shot: `SH0010`, `SH0050`, etc.
- Department: `lighting`, `compositing`, etc.

### Asset Pattern

**Scene Path Pattern:**
```
{root}/asset/{category}/{subcategory}/{asset}/{department}/...
```

**Examples:**
- `V:/SWA/all/asset/characters/main/hero_char/lighting/version/hero_char_lighting_v002.ma`
- `V:/SWA/all/asset/props/weapons/sword/modeling/sword_model_v001.ma`

**Detected Components:**
- Category: `characters`, `props`, etc.
- Subcategory: `main`, `weapons`, etc.
- Asset: `hero_char`, `sword`, etc.
- Department: `lighting`, `modeling`, etc.

---

## Cleanup Operations

### Cleanup Methods

#### 1. Keep Latest N Files
```python
temp_manager.cleanup_temp_files(keep_latest=5)
```
- Keeps 5 most recent temp files
- Deletes older files
- Searches all temp locations

#### 2. Delete Files Older Than N Hours
```python
temp_manager.cleanup_old_files(max_age_hours=24)
```
- Deletes files older than 24 hours
- Keeps recent files
- Useful for automatic cleanup

#### 3. Delete All Temp Files
```python
temp_manager.cleanup_all()
```
- Deletes all temp files
- No retention
- Use with caution

#### 4. Delete Specific File
```python
temp_manager.delete_file(filepath)
```
- Deletes specific temp file
- Useful for manual cleanup

### Cleanup Locations

The cleanup methods search these locations:

1. **Current Scene Context**
   - Detects context from current Maya scene
   - Searches `.tmp` directory in scene/asset root

2. **User Documents Folder**
   - `~/Documents/maya_batch_tmp/`
   - Fallback location

3. **Custom Root**
   - Specify custom root directory
   - `temp_manager.cleanup_temp_files(temp_root="/path/to/root")`

---

## Usage Examples

### Generate Temp Path

```python
from lrc_toolbox.utils.temp_file_manager import TempFileManager

temp_manager = TempFileManager()

# Generate temp path for current scene
scene_path = "V:/SWA/all/scene/Ep01/sq0010/SH0010/lighting/version/SH0010_lighting_v001.ma"
layer_name = "MASTER_BG_A"
process_id = "12345"

temp_path = temp_manager.generate_temp_filepath(scene_path, layer_name, process_id)
print(temp_path)
# Output: V:/SWA/all/scene/.tmp/Ep01/sq0010/SH0010/lighting/MASTER_BG_A/render_SH0010_lighting_v001_20250115_143022_12345.ma
```

### List All Temp Files

```python
temp_files = temp_manager.get_temp_files()
print(f"Found {len(temp_files)} temp files")
for temp_file in temp_files:
    print(f"  - {temp_file}")
```

### Cleanup Old Files

```python
# Delete files older than 24 hours
deleted_count = temp_manager.cleanup_old_files(max_age_hours=24)
print(f"Deleted {deleted_count} old temp files")
```

---

## Testing

### Test Script

Run this in Maya Script Editor:

```python
from lrc_toolbox.tests.test_temp_path_construction import test_temp_path_construction
test_temp_path_construction()
```

This will test:
- Shot scene path generation
- Asset scene path generation
- Fallback path generation
- Version extraction
- Directory structure
- Cleanup operations

---

## Troubleshooting

### Issue: Temp files not found during cleanup

**Cause:** Cleanup searches specific locations

**Solution:**
1. Check if scene is saved in standard project structure
2. Verify `.tmp` directory exists
3. Check user Documents folder: `~/Documents/maya_batch_tmp/`
4. Specify custom root: `cleanup_temp_files(temp_root="/path/to/root")`

### Issue: Permission denied when creating temp directory

**Cause:** No write permission to project directory

**Solution:**
1. Check directory permissions
2. System will fallback to user Documents folder
3. Contact IT/admin for project directory access

### Issue: Version not included in filename

**Cause:** Scene filename doesn't contain version pattern

**Solution:**
1. Rename scene file to include version: `{name}_v001.ma`
2. Version pattern: `_v001`, `_v002`, `_v0001`, etc.
3. Temp file will still be created without version

---

## Summary

**Key Points:**
- ✅ Context-aware hierarchical structure
- ✅ Temp files under `/scene/.tmp` or `/asset/.tmp`
- ✅ Organized by episode/sequence/shot or category/subcategory/asset
- ✅ Department and layer-specific subdirectories
- ✅ Version number in filename
- ✅ Fallback to `~/Documents/maya_batch_tmp/`
- ✅ Automatic directory creation
- ✅ Comprehensive cleanup operations

**Benefits:**
- Easy to find and manage temp files
- Clean project structure
- Automatic cleanup
- Version tracking
- Context awareness

