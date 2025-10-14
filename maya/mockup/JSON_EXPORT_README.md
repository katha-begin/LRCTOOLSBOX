# JSON Export Functionality for Shot Data

## Overview

The enhanced `save_and_setting.py` script now includes automatic JSON export functionality that exports shot data for external use whenever Maya scene files are saved. This allows external applications, pipeline tools, and other systems to access shot information without needing to open Maya.

## Export Trigger

The JSON export is automatically triggered when:
- **Save Increment**: Using the "Save Increment" button in the UI
- **Save As**: Using the "Save As (.ma)" button in the UI

The export happens **after** the Maya scene file is successfully saved.

## Export Location

JSON files are exported to the following path pattern:
```
{project_root}\{project}\all\scene\{ep}\{seq}\{shot}\.{ep}_{seq}_{shot}.json
```

### Example:
```
V:\SWA\all\scene\Ep01\sq0010\SH0045\.Ep01_sq0010_SH0045.json
```

The filename starts with a dot (.) to make it a hidden file on Unix systems and clearly distinguish it as metadata.

## Export Behavior

### Smart Export Logic:
1. **New File**: Creates new JSON file with shot data
2. **Existing File**: Compares current data with existing data
3. **Same Data**: Skips export (no file modification)
4. **Different Data**: Replaces existing file with new data
5. **No Backup**: Does not create backup files (as requested)

### Auto-Detection:
- Automatically detects shot nodes in the current scene
- Uses shot node specified in the UI if available
- Falls back to first available shot node if multiple exist
- Logs appropriate messages for user feedback

## JSON Data Structure

The exported JSON contains the following sections:

### 1. Metadata
```json
{
  "metadata": {
    "export_timestamp": "2024-01-15T14:30:45.123456",
    "maya_version": "Maya 2024.0",
    "scene_file": "V:/SWA/all/scene/Ep01/sq0010/SH0045/lighting/version/Ep01_sq0010_SH0045_lighting_master_v003.ma",
    "shot_node": "shotShape1",
    "show_code": "SWA"
  }
}
```

### 2. Shot Information
```json
{
  "shot_info": {
    "episode": "Ep01",
    "sequence": "sq0010", 
    "shot": "SH0045",
    "shot_name": "Ep01_sq0010_SH0045",
    "start_frame": 1001,
    "end_frame": 1120,
    "frame_count": 120,
    "version": "v003"
  }
}
```

### 3. Render Settings
```json
{
  "render_settings": {
    "current_renderer": "redshift",
    "animation_enabled": true,
    "extension_padding": 4,
    "frame_step": 1.0,
    "image_file_prefix": "W:/SWA/all/scene/Ep01/sq0010/SH0045/lighting/publish/v003/<RenderLayer>/<RenderLayer>"
  }
}
```

### 4. Timeline Settings
```json
{
  "timeline_settings": {
    "playback_start": 1001.0,
    "playback_end": 1120.0,
    "animation_start": 1001.0,
    "animation_end": 1120.0
  }
}
```

### 5. Shot Attributes (Optional)
```json
{
  "shot_attributes": {
    "sequenceStartFrame": 1001.0,
    "sequenceEndFrame": 1120.0,
    "scale": 1.0,
    "preHold": 0.0,
    "postHold": 0.0,
    "clipIn": 1001.0,
    "clipOut": 1120.0,
    "clipDuration": 120.0,
    "sourceStart": 1001.0,
    "sourceEnd": 1120.0,
    "sourceDuration": 120.0
  }
}
```

## Testing

### Manual Testing
Run the test script in Maya Script Editor:
```python
exec(open(r'E:\dev\LRCtoolsbox\LRCtoolsbox\maya\mockup\test_json_export.py').read())
```

### Test Coverage:
- Shot node detection
- Data extraction from shot nodes
- JSON path generation
- Full export process
- Duplicate export detection
- File creation verification

## API Functions

### Core Functions:

#### `export_shot_data_to_json(shot_node, project_root="V:/", show_code="SWA")`
Main export function that handles the complete export process.

**Parameters:**
- `shot_node` (str): Maya shot node name
- `project_root` (str): Project root directory (default: "V:/")
- `show_code` (str): Show/project code (default: "SWA")

**Returns:**
- `tuple`: (success: bool, file_path: str, data_or_error: dict)

#### `_extract_shot_data_from_node(shot_node, show_code="SWA")`
Extracts comprehensive shot data from a Maya shot node.

#### `_get_json_export_path(project_root, show, ep, seq, shot)`
Generates the JSON export file path following the specified pattern.

## Integration with External Tools

External applications can:

1. **Monitor JSON files** for changes using file system watchers
2. **Parse shot data** without opening Maya
3. **Access render settings** for pipeline automation
4. **Get frame ranges** for render farm submission
5. **Track version information** for asset management

## Error Handling

The system includes comprehensive error handling:
- Missing shot nodes
- Invalid file paths
- Permission errors
- JSON serialization errors
- Maya API errors

All errors are logged to the UI log panel and Maya's script editor.

## Performance

- **Fast Export**: Only exports when data changes
- **Small Files**: JSON files are typically 1-3KB
- **No Blocking**: Export happens after save, doesn't slow down save process
- **Minimal Overhead**: Efficient data comparison prevents unnecessary writes

## Compatibility

- **Maya Versions**: Compatible with Maya 2018+
- **Python**: Works with Python 2.7 and 3.x
- **File Systems**: Works on Windows, macOS, and Linux
- **Network Drives**: Supports UNC paths and mapped drives
