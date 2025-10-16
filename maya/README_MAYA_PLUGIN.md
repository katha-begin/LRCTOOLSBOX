# LRC Toolbox v2.0 - Maya Plugin Installation Guide

## 🚀 Quick Installation

### Method 1: Automatic Installation (Recommended)
1. Open Maya
2. In the Script Editor (Python tab), run:
   ```python
   import sys
   sys.path.append(r"E:\dev\LRCtoolsbox\LRCtoolsbox\maya")  # Adjust path as needed
   import install_plugin
   install_plugin.install_plugin()
   ```

### Method 2: Manual Installation
1. Copy `lrc_toolbox_plugin.py` to your Maya plugins directory:
   - **Windows**: `Documents/maya/2024/plug-ins/`
   - **macOS**: `~/Library/Preferences/Autodesk/maya/2024/plug-ins/`
   - **Linux**: `~/maya/2024/plug-ins/`

2. Copy the entire `lrc_toolbox` folder to the same plugins directory

3. Load the plugin in Maya:
   - Go to **Windows > Settings/Preferences > Plug-in Manager**
   - Find `lrc_toolbox_plugin.py` in the list
   - Check **"Loaded"** to load the plugin
   - Check **"Auto load"** to load automatically on Maya startup

## 🎯 Usage

### Opening the Toolbox
- **Menu**: `LRC Toolbox > Open Toolbox`
- **Command**: `lrcToolboxOpen()` in Script Editor
- **Python**: `cmds.lrcToolboxOpen()`

### Features Available
- ✅ **Asset/Shot Navigator** - Full implementation with context-aware navigation
- 🚧 **Render Setup** - Placeholder (ready for implementation)
- 🚧 **Light Manager** - Placeholder (ready for implementation)  
- 🚧 **Regex Tools** - Placeholder (ready for implementation)
- 🚧 **Settings** - Placeholder (ready for implementation)

## 🏗️ Current Implementation Status

### ✅ Completed (Ready for Use)
- **Main Window Structure** - Tab-based interface with Maya docking
- **Asset Navigator Widget** - Complete with:
  - Project settings configuration
  - Dual navigation (Shot + Asset)
  - File lists with context menus
  - Mock data and realistic interactions
  - Context change notifications

### 🚧 Placeholder Tabs (UI Framework Ready)
- **Render Setup** - Template management framework ready
- **Light Manager** - Pattern-based naming framework ready
- **Regex Tools** - DAG path conversion framework ready
- **Settings** - Configuration framework ready

## 🧪 Testing the Implementation

### Standalone Testing (Outside Maya)
```python
# From the project root directory
python -c "import sys; sys.path.insert(0, '.'); from maya.lrc_toolbox.main import main; main()"
```

### Maya Testing
1. Load the plugin as described above
2. Open via menu: `LRC Toolbox > Open Toolbox`
3. Test the Asset Navigator:
   - Change Episode/Sequence/Shot selections
   - Change Asset Category/Subcategory/Asset selections
   - Right-click on file lists for context menus
   - Try action buttons (Refresh, Open, Reference, etc.)
   - Watch status bar for context updates

## 📋 Asset Navigator Features

### Project Settings
- Project root path configuration
- Browse button for directory selection
- Automatic settings persistence

### Shot Navigator
- Episode → Sequence → Shot hierarchy
- Dynamic dropdown population
- Shot files list with version information
- Context menus for file operations

### Asset Navigator  
- Category → Subcategory → Asset hierarchy
- Dynamic dropdown population
- Asset files list with version information
- Context menus for file operations

### Action Buttons
- **Refresh** - Update all file lists
- **Open** - Open selected file
- **Reference** - Reference selected file
- **Import** - Import selected file
- **Save Version** - Save current scene as new version
- **Export Template** - Export current setup as template

### Context Menus (Right-click on files)
- **Open** - Open file in Maya
- **Reference** - Reference file into current scene
- **Import** - Import file contents
- **Show in Explorer** - Open file location
- **Copy Path** - Copy file path to clipboard
- **Make Hero** - Promote version to hero file (for version files)

## 🔧 Troubleshooting

### Plugin Won't Load
- Check that both `lrc_toolbox_plugin.py` and `lrc_toolbox/` folder are in plugins directory
- Verify Python path in Maya Script Editor
- Check Maya Script Editor for error messages

### UI Won't Open
- Try running `lrcToolboxOpen()` in Script Editor
- Check for error messages in Maya Script Editor
- Verify PySide2/PySide6 is available in Maya

### Missing Features
- Current implementation focuses on Asset Navigator
- Other tabs are placeholders ready for implementation
- All placeholder functions provide realistic mock responses

## 🚀 Next Development Steps

The UI framework is complete and ready for backend implementation:

1. **Render Setup Tab** - Implement Maya Render Setup API integration
2. **Light Manager Tab** - Implement light naming and management
3. **Regex Tools Tab** - Implement DAG path regex conversion
4. **Settings Tab** - Implement configuration management
5. **Backend Integration** - Replace placeholder functions with real Maya operations

## 📞 Support

For issues or questions:
- Check Maya Script Editor for error messages
- Verify file paths and permissions
- Test standalone mode first before Maya integration
- Ensure Maya version compatibility (2020+)

---

**LRC Toolbox v2.0** - Enhanced Template Management & Context-Aware Workflows
