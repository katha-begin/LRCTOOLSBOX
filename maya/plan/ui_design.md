# LRC Manager UI Design Specification

## 📋 Overview

This document provides comprehensive UI design specifications for the modular refactoring of the LRC Manager tool. The design preserves all existing functionality and workflows while enabling modular component development with placeholder backend functions.

**Design Constraints:**
- ✅ **Preserve Existing Logic**: No changes to tool functionality or business logic
- ✅ **Maintain Current Workflow**: Exact same user workflows as documented in user journey
- ✅ **UI-Only Focus**: Design affects presentation layer only, not underlying operations
- ✅ **Modular Architecture**: Support UI-first development with placeholder backends

## 🏗️ Current Implementation Architecture

### Directory Structure (Updated to Match Current Implementation)
```
maya/lrc_toolbox/
├── __init__.py
├── core/                    # Business logic and data models
│   ├── __init__.py
│   ├── models.py           # Data structures and schemas (TO IMPLEMENT)
│   ├── project_manager.py  # ProjectStructure → here (TO IMPLEMENT)
│   ├── version_manager.py  # VersionManager → here (TO IMPLEMENT)
│   ├── template_manager.py # Template management system (TO IMPLEMENT)
│   ├── light_manager.py    # Enhanced light operations (TO IMPLEMENT)
│   └── render_setup_api.py # RenderSetupManager → here (TO IMPLEMENT)
├── utils/                   # Helper functions and shared components
│   ├── __init__.py
│   ├── file_operations.py  # File system utilities (TO IMPLEMENT)
│   ├── naming_conventions.py # Naming rule management (TO IMPLEMENT)
│   ├── regex_tools.py      # RegexConverter → here (TO IMPLEMENT)
│   └── maya_helpers.py     # Maya-specific helpers (TO IMPLEMENT)
├── ui/                     # User interface components (PRIORITY 1)
│   ├── __init__.py
│   ├── main_window.py      # Main UI structure (PARTIALLY IMPLEMENTED)
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── asset_navigator.py    # Enhanced asset/shot navigation (TO IMPLEMENT)
│   │   ├── template_widget.py    # Context-aware template management (TO IMPLEMENT)
│   │   ├── render_setup_widget.py # Render setup UI (TO IMPLEMENT)
│   │   ├── light_manager_widget.py # Enhanced light management (TO IMPLEMENT)
│   │   ├── regex_tools_widget.py  # Regex tools UI (TO IMPLEMENT)
│   │   └── settings_widget.py     # Settings UI (TO IMPLEMENT)
│   └── dialogs/
│       ├── __init__.py
│       ├── version_dialog.py     # Version save dialog (TO IMPLEMENT)
│       ├── template_dialog.py    # Template creation dialog (TO IMPLEMENT)
│       └── inheritance_dialog.py # Template inheritance dialog (TO IMPLEMENT)
├── importers/              # Data ingestion and file reading
│   ├── __init__.py
│   ├── base_importer.py    # Base importer interface (TO IMPLEMENT)
│   ├── scene_importer.py   # Scene file import (TO IMPLEMENT)
│   ├── light_importer.py   # Light-only import (TO IMPLEMENT)
│   └── render_setup_importer.py # Render setup import (TO IMPLEMENT)
├── exporters/              # Data output and file writing
│   ├── __init__.py
│   ├── base_exporter.py    # Base exporter interface (TO IMPLEMENT)
│   ├── scene_exporter.py   # Scene file export (TO IMPLEMENT)
│   ├── light_exporter.py   # Light-only export (TO IMPLEMENT)
│   ├── template_exporter.py # Template export (TO IMPLEMENT)
│   └── render_setup_exporter.py # Render setup export (TO IMPLEMENT)
├── config/
│   ├── __init__.py
│   ├── settings.py         # Application settings (✅ IMPLEMENTED)
│   └── defaults.py         # Default configurations (✅ IMPLEMENTED)
├── tests/                  # Test files
│   └── __init__.py
└── main.py                 # Entry point and UI launcher (PARTIALLY IMPLEMENTED)
```

## 🏗️ Overall Architecture

### Main Window Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ Render Setup Manager v2.0                                      │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Tab Widget (QTabWidget)                                     │ │
│ │ ┌─────┬─────┬─────┬─────┬─────────┐                         │ │
│ │ │🏠   │🎨   │💡   │🔧   │⚙️       │                         │ │
│ │ │Asset│Render│Light│Regex│Settings │                         │ │
│ │ │/Shot│Setup │Mgr  │Tools│         │                         │ │
│ │ └─────┴─────┴─────┴─────┴─────────┘                         │ │
│ │                                                             │ │
│ │ [Active Tab Content Area]                                   │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Window Properties
- **Type**: QMainWindow (dockable in Maya)
- **Minimum Size**: 700x900 pixels
- **Docking Areas**: Right, Left (preferred: Right)
- **Resizable**: Yes
- **Title**: "Render Setup Manager v2.0"

## 🏠 Tab 1: Asset/Shot Navigator

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ Project Settings                                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Project Root: [V:\SWA\all                    ] [Browse]     │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────┬─────────────────────────────────────┐ │
│ │ 🎬 Shot Navigator       │ 🎨 Asset Navigator                  │ │
│ │ ┌─────────────────────┐ │ ┌─────────────────────────────────┐ │ │
│ │ │ Episode: [Ep01  ▼]  │ │ │ Category: [Sets     ▼]         │ │ │
│ │ │ Sequence:[sq0010▼]  │ │ │ Subcategory:[interior▼]        │ │ │
│ │ │ Shot:    [SH0010▼]  │ │ │ Asset:   [Kitchen  ▼]          │ │ │
│ │ └─────────────────────┘ │ └─────────────────────────────────┘ │ │
│ │                         │                                     │ │
│ │ Shot Files:             │ Asset Files:                        │ │
│ │ ┌─────────────────────┐ │ ┌─────────────────────────────────┐ │ │
│ │ │👑 hero_v005.ma      │ │ │📋 kitchen_template.ma           │ │ │
│ │ │📋 template.ma       │ │ │👑 kitchen_hero.ma               │ │ │
│ │ │📝 scene_v004.ma     │ │ │📝 kitchen_v003.ma               │ │ │
│ │ │📝 scene_v003.ma     │ │ │📝 kitchen_v002.ma               │ │ │
│ │ │                     │ │ │                                 │ │ │
│ │ └─────────────────────┘ │ └─────────────────────────────────┘ │ │
│ │                         │                                     │ │
│ │ [🔄 Refresh]            │ [🔄 Refresh]                        │ │
│ │ [💾 Save Version]       │ [💾 Save Version]                   │ │
│ │ [📤 Export Template]    │ [📤 Export Template]                │ │
│ └─────────────────────────┴─────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ 🎬 File Operations                                              │
│ [📂 Open Selected] [🔗 Reference Selected] [📥 Import Selected] │
└─────────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### Project Settings Group
- **Type**: QGroupBox with horizontal layout
- **Components**:
  - Label: "Project Root:"
  - LineEdit: `root_path_edit` (editable path)
  - Button: "Browse" (opens QFileDialog)

#### Shot Navigator Section
- **Type**: QGroupBox("🎬 Shot Navigator") with vertical layout
- **Hierarchy Controls**:
  - Episode ComboBox: `episode_combo` (cascading selection)
  - Sequence ComboBox: `sequence_combo` (filtered by episode)
  - Shot ComboBox: `shot_combo` (filtered by sequence)
- **File List**: QListWidget with custom item formatting
- **Action Buttons**: Vertical layout with emoji icons

#### Asset Navigator Section
- **Type**: QGroupBox("🎨 Asset Navigator") with vertical layout
- **Hierarchy Controls**:
  - Category ComboBox: `asset_category_combo`
  - Subcategory ComboBox: `asset_subcategory_combo`
  - Asset ComboBox: `asset_combo`
- **File List**: QListWidget with custom item formatting
- **Action Buttons**: Vertical layout with emoji icons

#### File List Formatting
```python
# File type icons and color coding
file_type_icons = {
    'hero': '👑',      # Gold background (255, 215, 0, 50)
    'template': '📋',  # Green background (0, 255, 0, 50)
    'version': '📝'    # Light blue background (135, 206, 235, 50)
}

# Display format: "{icon} {filename} - {timestamp}"
# Example: "👑 scene_hero.ma - 2024-01-15 14:30"
```

#### Context Menu Structure
```
Right-click on file item:
├── 📂 Open
├── 🔗 Reference  
├── 📥 Import
├── ─────────────
├── 📁 Show in Explorer
├── 📋 Copy Path
└── 👑 Make Hero (version files only)
```

### User Interaction Flows

#### Shot Selection Flow
1. User selects Episode → triggers `on_episode_changed()`
2. System populates Sequence combo → triggers `on_sequence_changed()`
3. System populates Shot combo → triggers `on_shot_changed()`
4. System refreshes file list → calls `refresh_shot_files()`

#### File Operation Flow
1. User selects file from list
2. User double-clicks OR uses context menu OR clicks operation button
3. System calls appropriate import method with file path and operation type
4. System displays success/error message

#### Template Management Integration Flow
1. User navigates to specific asset/shot using navigator
2. System displays available templates for current context
3. User can import existing templates specific to current asset/shot
4. User creates/modifies render layers and lighting within context
5. User publishes work as new template to current asset/shot location
6. Template becomes available for inheritance by similar assets/shots



## 🎨 Tab 2: Render Setup

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ 📋 Template Management                                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Name: [template_name                    ] [Create Template] │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Templates:                                                      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ forest_master_template.json                                 │ │
│ │ interior_basic_template.json                                │ │
│ │ exterior_day_template.json                                  │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ [Load Template] [Delete Template]                              │
├─────────────────────────────────────────────────────────────────┤
│ 📤 Import/Export                                                │
│ [Export Render Setup] [Import Render Setup]                    │
└─────────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### Template Management Group
- **Type**: QGroupBox("📋 Template Management")
- **Template Creation**:
  - LineEdit: `template_name_edit` with placeholder "Template name..."
  - Button: "Create Template"
- **Template List**: QListWidget showing available templates
- **Template Actions**: Horizontal layout with Load/Delete buttons

#### Import/Export Group
- **Type**: QGroupBox("📤 Import/Export")
- **Buttons**: Export and Import render setup configurations

### User Interaction Flows

#### Template Creation Flow (Master Setup - Sarah's Workflow)
1. User enters template name
2. User clicks "Create Template"
3. System serializes current render setup
4. System saves template to user preferences directory
5. System refreshes template list

#### Template Loading Flow (Key Shot Inheritance - Mike's Workflow)
1. User selects template from list
2. User clicks "Load Template"
3. System applies template to current scene
4. System creates render layers and collections
5. System reports success/failure



## 💡 Tab 3: Light Manager

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ 💡 Light Naming                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Prefix: [key        ▼]  Index: [001]  Suffix: [lgt     ▼]  │ │
│ │                                                             │ │
│ │ Preview: key_001_lgt                                        │ │
│ │                                                             │ │
│ │ [Apply to Selected Lights]                                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ 📤 Light Import/Export                                          │
│ [Export Lights Only] [Import Lights Only]                      │
├─────────────────────────────────────────────────────────────────┤
│ Scene Lights                                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ SEQ001_MASTER_SUN_primary_001                               │ │
│ │ SEQ001_MASTER_SKY_fill_001                                  │ │
│ │ SEQ001_MASTER_ATMOS_godrays_001                             │ │
│ │ SHOT045_FACE_key_hero_001                                   │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ [Refresh Light List]                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### Light Naming Group
- **Type**: QGroupBox("💡 Light Naming") with grid layout
- **Controls**:
  - Prefix ComboBox: `light_prefix_combo` (editable, pre-populated)
  - Index SpinBox: `light_index_spin` (1-999, zero-padded)
  - Suffix ComboBox: `light_suffix_combo` (editable, pre-populated)
- **Preview Label**: Real-time name generation display
- **Apply Button**: Applies naming to selected lights in scene

#### Light Import/Export Group
- **Type**: QGroupBox("📤 Light Import/Export")
- **Buttons**: Export/Import light-only files

#### Scene Lights Group
- **Light List**: QListWidget showing all lights in current scene
- **Refresh Button**: Updates light list from Maya scene

### User Interaction Flows

#### Light Naming Flow (Supports All User Personas)
1. User selects lights in Maya scene
2. User configures prefix, index, suffix in tool
3. Preview updates in real-time
4. User clicks "Apply to Selected Lights"
5. System renames lights according to naming rules

#### Light Export Flow (Master Setup Distribution)
1. User clicks "Export Lights Only"
2. System opens file dialog
3. System exports only light objects to selected file
4. System reports export success/failure



## 🔧 Tab 4: Regex Tools

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ 🔧 DAG Path to Regex Converter                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ DAG Paths (one per line):                                   │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ |forest_environment_trees_*                             │ │ │
│ │ │ |character_*                                            │ │ │
│ │ │ |props_hero_*                                           │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │                                                             │ │
│ │ ☑ Escape Special Characters  ☑ Convert Wildcards           │ │
│ │                                                             │ │
│ │ [Convert to Regex]                                          │ │
│ │                                                             │ │
│ │ Generated Regex:                                            │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ (|forest_environment_trees_.*|character_.*|props_hero_.*)│ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ ⚡ Quick Tools                                                  │
│ [Selected Objects to Regex]                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### DAG Path Converter Group
- **Type**: QGroupBox("🔧 DAG Path to Regex Converter")
- **Input Area**: QTextEdit (max height: 100px) for DAG path input
- **Options**: Two checkboxes for conversion settings
- **Convert Button**: Processes input and generates regex
- **Output Area**: QTextEdit (max height: 80px, read-only) for generated regex

#### Quick Tools Group
- **Type**: QGroupBox("⚡ Quick Tools")
- **Button**: "Selected Objects to Regex" - converts Maya selection to regex pattern

### User Interaction Flows

#### Regex Conversion Flow (Collection Setup Support)
1. User enters DAG paths (one per line) in input area
2. User configures conversion options (checkboxes)
3. User clicks "Convert to Regex"
4. System processes paths and generates regex pattern
5. System displays result in output area (user can copy)


## ⚙️ Tab 5: Settings

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ ⚙️ Naming Convention Rules                                      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Separator:      [_]                                         │ │
│ │ Index Padding:  [2]                                         │ │
│ │ Case:           [lower ▼]                                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ [💾 Save Settings]                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### Naming Convention Rules Group
- **Type**: QGroupBox("⚙️ Naming Convention Rules") with form layout
- **Controls**:
  - Separator LineEdit: `separator_edit` (default: "_")
  - Padding SpinBox: `padding_spin` (1-5, default: 2)
  - Case ComboBox: `case_combo` (lower/upper/title, default: lower)
- **Save Button**: Persists settings to user preferences

### User Interaction Flows

#### Settings Configuration Flow
1. User modifies naming convention settings
2. User clicks "Save Settings"
3. System saves settings to JSON file in user preferences
4. System updates light manager naming rules
5. System reports save success/failure

## 🔗 Maya Integration & Docking

### Docking Specifications
```python
# Maya docking configuration
dock_control = cmds.dockControl(
    "renderSetupManagerDock",
    label="Render Setup Manager v2.0",
    area="right",                    # Preferred docking area
    content=ui.objectName(),
    allowedArea=["right", "left"],   # Allowed docking areas
    sizeable=True,                   # User can resize
    width=700,                       # Default width
    height=900                       # Default height
)
```

### Integration Requirements
- **Parent Window**: Maya main window (via `get_maya_main_window()`)
- **PySide Integration**: Uses shiboken for Maya UI integration
- **Window Management**: Handles existing instance cleanup
- **Fallback Behavior**: Creates standalone window if docking fails

### Error Handling
- **Graceful Degradation**: Falls back to standalone window if docking fails
- **Instance Management**: Cleans up existing instances before creating new ones
- **User Feedback**: Provides console messages for success/failure states

## 📱 Responsive Design Considerations

### Minimum Size Constraints
- **Window**: 700x900 pixels minimum
- **Tab Content**: Adapts to available space
- **File Lists**: Minimum 200px height, expands with window
- **Text Areas**: Fixed heights where specified, otherwise flexible

### Layout Behavior
- **Horizontal Sections**: Asset/Shot navigator uses 50/50 split
- **Vertical Stacking**: All other layouts stack vertically
- **Button Sizing**: Consistent button heights, text-based widths
- **Spacing**: Standard Qt spacing (6px) between elements

## 🎨 Visual Design Standards

### Color Coding System
```python
# File type background colors (RGBA)
HERO_COLOR = QColor(255, 215, 0, 50)      # Gold
TEMPLATE_COLOR = QColor(0, 255, 0, 50)    # Green  
VERSION_COLOR = QColor(135, 206, 235, 50) # Light Blue
```

### Typography
- **Preview Text**: Bold, green color (#4CAF50) for light name preview
- **File Names**: Standard system font
- **Labels**: Standard Qt label styling
- **Buttons**: Standard Qt button styling with emoji icons

### Icon Usage
- **Emoji Icons**: Used consistently throughout interface
- **File Type Icons**: 👑 (hero), 📋 (template), 📝 (version)
- **Tab Icons**: 🏠 🎨 💡 🔧 ⚙️
- **Action Icons**: 🔄 💾 📤 📂 🔗 📥 📁 📋

## 📐 Wireframes

### Main Window Wireframe
```
┌─────────────────────────────────────────────────────────────────┐
│ [×] Render Setup Manager v2.0                            [_][□][×]│
├─────────────────────────────────────────────────────────────────┤
│ ┌───┬───┬───┬───┬───┐                                           │
│ │🏠 │🎨 │💡 │🔧 │⚙️ │ ← Tab Headers                            │
│ └───┴───┴───┴───┴───┘                                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                                                             │ │
│ │                                                             │ │
│ │                                                             │ │
│ │                Tab Content Area                             │ │
│ │                (700x850 minimum)                            │ │
│ │                                                             │ │
│ │                                                             │ │
│ │                                                             │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Enhanced Asset/Shot Navigator Tab Wireframe (with Template Management)
```
┌─────────────────────────────────────────────────────────────────┐
│ Project Settings                                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Project Root: [____________________] [Browse]               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────┬─────────────────────────────────────┐ │
│ │ 🎬 Shot Navigator       │ 🎨 Asset Navigator                  │ │
│ │ ┌─────────────────────┐ │ ┌─────────────────────────────────┐ │ │
│ │ │ Episode:  [____▼]   │ │ │ Category:    [____▼]            │ │ │
│ │ │ Sequence: [____▼]   │ │ │ Subcategory: [____▼]            │ │ │
│ │ │ Shot:     [____▼]   │ │ │ Asset:       [____▼]            │ │ │
│ │ └─────────────────────┘ │ └─────────────────────────────────┘ │ │
│ │                         │                                     │ │
│ │ Shot Files:             │ Asset Files:                        │ │
│ │ ┌─────────────────────┐ │ ┌─────────────────────────────────┐ │ │
│ │ │ [File List]         │ │ │ [File List]                     │ │ │
│ │ │ • 👑 hero_v005.ma   │ │ │ • 📋 template.ma                │ │ │
│ │ │ • 📋 template.ma    │ │ │ • 👑 hero.ma                    │ │ │
│ │ │ • 📝 scene_v004.ma  │ │ │ • 📝 asset_v003.ma              │ │ │
│ │ │ • 📝 scene_v003.ma  │ │ │ • 📝 asset_v002.ma              │ │ │
│ │ │                     │ │ │                                 │ │ │
│ │ └─────────────────────┘ │ └─────────────────────────────────┘ │ │
│ │                         │                                     │ │
│ │ [🔄 Refresh]            │ [🔄 Refresh]                        │ │
│ │ [💾 Save Version]       │ [💾 Save Version]                   │ │
│ │ [📤 Export Template]    │ [📤 Export Template]                │ │
│ └─────────────────────────┴─────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ 📋 Context Templates (Current: Ep01/sq0010/SH0010)             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Available Templates:                                        │ │
│ │ • 🏛️ SEQ001_MASTER (inherited from sequence)               │ │
│ │ • 🔑 SHOT_045_KEY (key shot template)                      │ │
│ │ • 📋 forest_lighting_base.json                             │ │
│ │ • 📋 character_closeup.json                                │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ [📥 Import Template] [📤 Publish Template] [🔗 Inherit From]    │
├─────────────────────────────────────────────────────────────────┤
│ 🎬 File Operations                                              │
│ [📂 Open] [🔗 Reference] [📥 Import]                            │
└─────────────────────────────────────────────────────────────────┘
```

### Enhanced Light Manager Tab Wireframe (Context-Aware Naming)
```
┌─────────────────────────────────────────────────────────────────┐
│ 💡 Light Naming (Context: Ep01/sq0010/SH0010)                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Selected Lights: 3 lights                                   │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ Pattern: {sequence}_{shot}_{type}_{purpose}_{index}     │ │ │
│ │ │                                                         │ │ │
│ │ │ Sequence: [SQ001     ] Shot: [SH020     ]              │ │ │
│ │ │ Type:     [LGT    ▼ ] Purpose: [key   ▼ ]              │ │ │
│ │ │ Start Index: [001]    Padding: [3]                     │ │ │
│ │ │                                                         │ │ │
│ │ │ Preview:                                                │ │ │
│ │ │ • directionalLight1 → SQ001_SH020_LGT_key_001          │ │ │
│ │ │ • areaLight1 → SQ001_SH020_LGT_key_002                 │ │ │
│ │ │ • spotLight1 → SQ001_SH020_LGT_key_003                 │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ │                                    [Apply] [Cancel]        │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ 📤 Light Import/Export                                          │
│ [Export Lights Only] [Import Lights Only]                      │
├─────────────────────────────────────────────────────────────────┤
│ Scene Lights                                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • SEQ001_MASTER_SUN_primary_001                             │ │
│ │ • SEQ001_MASTER_SKY_fill_001                                │ │
│ │ • SEQ001_MASTER_ATMOS_godrays_001                           │ │
│ │ • SHOT045_FACE_key_hero_001                                 │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ [Refresh Light List]                                            │
└─────────────────────────────────────────────────────────────────┘
```

## � Enhanced Template Management System

### Template Organization Structure
Templates are organized hierarchically to match the project structure, providing context-aware template management:

```
V:\SWA\all\
├── scene\
│   ├── Ep01\
│   │   ├── sq0010\
│   │   │   ├── SH0010\
│   │   │   │   ├── lighting\
│   │   │   │   │   ├── templates\          # Shot-specific template packages
│   │   │   │   │   │   ├── sq010_SH0010_master_pkg\
│   │   │   │   │   │   │   ├── sq010_SH0010_light_master.ma
│   │   │   │   │   │   │   ├── render_layers.json
│   │   │   │   │   │   │   ├── render_settings.json (optional)
│   │   │   │   │   │   │   ├── aovs.json (optional)
│   │   │   │   │   │   │   └── package_info.json (dependency tracking)
│   │   │   │   │   │   ├── sq010_SH0010_key_pkg\
│   │   │   │   │   │   │   ├── sq010_SH0010_light_key.ma
│   │   │   │   │   │   │   ├── render_layers.json
│   │   │   │   │   │   │   ├── render_settings.json (optional)
│   │   │   │   │   │   │   ├── aovs.json (optional)
│   │   │   │   │   │   │   └── package_info.json
│   │   │   │   │   │   └── sq010_SH0010_micro_pkg\
│   │   │   │   │   │       ├── sq010_SH0010_light_micro.ma
│   │   │   │   │   │       ├── render_layers.json
│   │   │   │   │   │       └── package_info.json
│   │   │   │   │   └── version\
│   │   │   │   └── SH0020\
│   │   │   └── templates\                  # Sequence-level template packages
│   │   │       ├── sq010_master_pkg\
│   │   │       │   ├── sq010_light_master.ma
│   │   │       │   ├── render_layers.json
│   │   │       │   ├── render_settings.json
│   │   │       │   └── package_info.json
│   │   │       └── forest_lighting_pkg\
│   │   │           ├── sq010_forest_light_key.ma
│   │   │           ├── render_layers.json
│   │   │           └── package_info.json
│   │   └── templates\                      # Episode-level template packages
│   │       └── ep01_master_pkg\
│   │           ├── ep01_light_master.ma
│   │           ├── render_layers.json
│   │           ├── render_settings.json
│   │           ├── aovs.json
│   │           └── package_info.json
│   └── templates\                          # Global scene template packages
└── asset\
    ├── Sets\
    │   ├── interior\
    │   │   ├── Kitchen\
    │   │   │   ├── lighting\
    │   │   │   │   ├── templates\          # Asset-specific template packages
    │   │   │   │   │   ├── kitchen_day_master_pkg\
    │   │   │   │   │   │   ├── kitchen_day_light_rig_master.ma
    │   │   │   │   │   │   ├── render_layers.json
    │   │   │   │   │   │   ├── render_settings.json
    │   │   │   │   │   │   └── package_info.json
    │   │   │   │   │   └── kitchen_night_key_pkg\
    │   │   │   │   │       ├── kitchen_night_light_rig_key.ma
    │   │   │   │   │       ├── render_layers.json
    │   │   │   │   │       └── package_info.json
    │   │   │   │   └── version\
    │   │   │   └── LivingRoom\
    │   │   └── templates\                  # Subcategory template packages
    │   │       └── interior_base_pkg\
    │   │           ├── interior_base_light_rig_master.ma
    │   │           ├── render_layers.json
    │   │           └── package_info.json
    │   └── templates\                      # Category template packages
    │       └── sets_master_pkg\
    │           ├── sets_master_light_rig_master.ma
    │           ├── render_layers.json
    │           ├── render_settings.json
    │           └── package_info.json
    └── templates\                          # Global asset template packages
```

### Template Types and Inheritance Hierarchy

#### Template Package Types
1. **🏛️ Master Template Packages**: Comprehensive base setups (created by Senior Artists)
   - **Package Contents**: Maya light rig (.ma) + render layers (JSON) + render settings (JSON) + AOVs (JSON) + dependency info (JSON)
   - **Maya Naming**:
     - Assets: `{assetName}_{description}_light_rig_master.ma` (e.g., `bedroom_day_light_rig_master.ma`)
     - Shots: `{context}_light_master.ma` (e.g., `sq010_SH0010_light_master.ma`)

2. **🔑 Key Shot Template Packages**: Enhanced templates for hero shots (created by Mid-Level Artists)
   - **Package Contents**: Enhanced Maya light rig (.ma) + specialized render layers (JSON) + optional settings/AOVs + dependency info (JSON)
   - **Maya Naming**:
     - Assets: `{assetName}_{description}_light_rig_key.ma` (e.g., `bedroom_dramatic_light_rig_key.ma`)
     - Shots: `{context}_light_key.ma` (e.g., `sq010_SH0010_light_key.ma`)

3. **📋 Standard Template Packages**: General-purpose templates for common scenarios
   - **Package Contents**: Standard Maya light rig (.ma) + basic render layers (JSON) + dependency info (JSON)
   - **Maya Naming**:
     - Assets: `{assetName}_{description}_light_rig_standard.ma`
     - Shots: `{context}_light_standard.ma`

4. **🎯 Micro Template Packages**: Small adjustments and variations (created by Junior Artists)
   - **Package Contents**: Minimal Maya light adjustments (.ma) + override render layers (JSON) + dependency info (JSON)
   - **Maya Naming**:
     - Assets: `{assetName}_{description}_light_rig_micro.ma`
     - Shots: `{context}_light_micro.ma`

#### Render Layer Template Naming Convention

**Format**: `{context}_{element}_{variance}`

**Naming Rules**:
- **Context**: MASTER, SHOT, ASSET context identifier
- **Element**: BG (Background), CHAR (Character), ATMOS (Atmosphere), FX (Effects)
- **Variance**: A, B, C (A is standard/default, ATMOS omits variance)

**Standard Examples**:
```
MASTER_BG_A        # Master background layer (standard)
MASTER_BG_B        # Master background layer (variant B)
MASTER_CHAR_A      # Master character layer (standard)
MASTER_CHAR_B      # Master character layer (variant B)
MASTER_ATMOS       # Master atmosphere layer (no variance)
MASTER_FX_A        # Master effects layer (standard)
MASTER_FX_C        # Master effects layer (variant C)
```

**Shot-Specific Examples**:
```
SH0010_BG_A        # Shot-specific background layer
SH0010_CHAR_A      # Shot-specific character layer
SH0010_ATMOS       # Shot-specific atmosphere layer
SH0010_FX_A        # Shot-specific effects layer
```

**Asset-Specific Examples**:
```
KITCHEN_BG_A       # Asset-specific background layer
KITCHEN_CHAR_A     # Asset-specific character layer
KITCHEN_ATMOS      # Asset-specific atmosphere layer
KITCHEN_FX_B       # Asset-specific effects layer (variant B)
```

**Variance Usage Guidelines**:
- **A**: Standard/default layer configuration
- **B**: Alternative configuration (e.g., different lighting mood)
- **C**: Special/experimental configuration
- **ATMOS**: Always omits variance suffix (atmospheric layers are unique)

#### Inheritance Chain
```
Global Template
    ↓
Episode/Category Master Template (Sarah creates)
    ↓
Sequence/Subcategory Template
    ↓
Key Shot Template (Mike enhances)
    ↓
Child Shot Micro-Adjustments (Jenny applies)
```

### Context-Aware Template Management

#### Template Discovery
When user navigates to a specific asset/shot, the system automatically discovers available templates:

1. **Local Templates**: Templates specific to current asset/shot
2. **Inherited Templates**: Templates from parent hierarchy levels
3. **Similar Context Templates**: Templates from similar assets/shots
4. **Global Templates**: Universal templates applicable to any context

#### Template Package Display Format
```python
template_package_info = {
    'package_name': 'sq010_SH0010_master_pkg',
    'type': 'master',  # 'master', 'key', 'standard', 'micro'
    'level': 'shot',  # 'global', 'episode', 'sequence', 'shot', 'asset'
    'inheritance_source': 'sq010_master_pkg',
    'created_by': 'Sarah',
    'created_date': datetime.now(),
    'description': 'Master lighting setup for dramatic forest sequence',
    'compatible_contexts': ['forest', 'outdoor', 'daylight'],
    'package_contents': {
        'maya_light_file': 'sq010_SH0010_light_master.ma',
        'render_layers': 'render_layers.json',
        'render_settings': 'render_settings.json',  # optional
        'aovs': 'aovs.json',  # optional
        'dependency_info': 'package_info.json'
    },
    'dependencies': {
        'parent_template': 'sq010_master_pkg_v002',
        'maya_version': '2024.1',
        'renderer': 'Arnold 7.2.4.0',
        'last_updated': datetime.now()
    }
}
```

## 📦 Enhanced Template Browser and Import/Export System

### Template Package Browser Interface

#### Package List Display
```
┌─────────────────────────────────────────────────────────────────┐
│ Template Packages for: sq010_SH0010                            │
├─────────────────────────────────────────────────────────────────┤
│ 🏛️ sq010_SH0010_master_pkg                    [Import Package] │
│   ├── 💡 sq010_SH0010_light_master.ma                         │
│   ├── 📋 render_layers.json                                   │
│   ├── ⚙️ render_settings.json                                 │
│   ├── 🎨 aovs.json                                            │
│   └── 📄 package_info.json                                    │
│                                                                 │
│ 🔑 sq010_SH0010_key_pkg                       [Import Package] │
│   ├── 💡 sq010_SH0010_light_key.ma                           │
│   ├── 📋 render_layers.json                                   │
│   └── 📄 package_info.json                                    │
│                                                                 │
│ 🎯 sq010_SH0010_micro_pkg                     [Import Package] │
│   ├── 💡 sq010_SH0010_light_micro.ma                         │
│   ├── 📋 render_layers.json                                   │
│   └── 📄 package_info.json                                    │
└─────────────────────────────────────────────────────────────────┘
```

#### Individual File Import Options
```
┌─────────────────────────────────────────────────────────────────┐
│ Import Options for: sq010_SH0010_master_pkg                    │
├─────────────────────────────────────────────────────────────────┤
│ Select Components to Import:                                    │
│ ☑️ Maya Light Rig (sq010_SH0010_light_master.ma)              │
│ ☑️ Render Layers (render_layers.json)                         │
│ ☑️ Render Settings (render_settings.json)                     │
│ ☑️ AOVs Configuration (aovs.json)                              │
│                                                                 │
│ Import Mode:                                                    │
│ ○ Replace Existing   ● Additive (if possible)                  │
│                                                                 │
│ Scene Conflict Resolution:                                      │
│ ☑️ Check for existing lights before import                     │
│ ☑️ Rename conflicting objects                                  │
│ ☑️ Preserve existing render layers                             │
│                                                                 │
│                           [Import Selected] [Cancel]           │
└─────────────────────────────────────────────────────────────────┘
```

### Export Module Interface

#### Package Export Dialog
```
┌─────────────────────────────────────────────────────────────────┐
│ Export Template Package                                         │
├─────────────────────────────────────────────────────────────────┤
│ Package Name: [sq010_SH0010_hero_pkg                        ] │
│ Package Type: [Key Shot Template ▼]                            │
│                                                                 │
│ Export Components:                                              │
│ ☑️ Maya Light Rig                                              │
│   └── Export Selection: ○ All Lights  ● Selected Lights       │
│ ☑️ Render Layers                                               │
│   └── Layers: ☑️ beauty ☑️ diffuse ☑️ specular ☑️ shadow     │
│ ☑️ Render Settings                                             │
│ ☑️ AOVs Configuration                                          │
│                                                                 │
│ Dependency Tracking:                                            │
│ Parent Template: [sq010_master_pkg_v003           ▼]          │
│ Description: [Hero lighting for dramatic reveal scene       ] │
│                                                                 │
│ Export Location:                                                │
│ [V:\SWA\all\scene\Ep01\sq0010\SH0010\lighting\templates\    ] │
│                                                                 │
│                    [Export Package] [Export Individual] [Cancel] │
└─────────────────────────────────────────────────────────────────┘
```

#### Individual File Export Options
```
┌─────────────────────────────────────────────────────────────────┐
│ Individual Export Options                                       │
├─────────────────────────────────────────────────────────────────┤
│ Export Type: [Maya Light Rig ▼]                               │
│                                                                 │
│ Maya Light File:                                                │
│ Filename: [sq010_SH0010_light_hero.ma                       ] │
│ Selection: ○ All Scene Lights  ● Selected Lights Only          │
│ Include: ☑️ Light Transforms ☑️ Light Attributes ☑️ Textures   │
│                                                                 │
│ OR                                                              │
│                                                                 │
│ Render Layers JSON:                                             │
│ Filename: [render_layers_hero.json                          ] │
│ Layers: ☑️ beauty ☑️ diffuse ☑️ specular ☑️ shadow           │
│                                                                 │
│ OR                                                              │
│                                                                 │
│ Render Settings JSON:                                           │
│ Filename: [render_settings_hero.json                        ] │
│ Include: ☑️ Arnold Settings ☑️ Maya Settings ☑️ Camera Settings │
│                                                                 │
│                              [Export] [Cancel]                 │
└─────────────────────────────────────────────────────────────────┘
```

### Scene Conflict Detection and Resolution

#### Import Conflict Dialog
```
┌─────────────────────────────────────────────────────────────────┐
│ Import Conflicts Detected                                       │
├─────────────────────────────────────────────────────────────────┤
│ The following conflicts were found in the current scene:        │
│                                                                 │
│ 🚨 Light Name Conflicts:                                       │
│ • keyLight1 (exists) → keyLight1_imported                      │
│ • rimLight1 (exists) → rimLight1_imported                      │
│                                                                 │
│ 🚨 Render Layer Conflicts:                                     │
│ • beauty (exists) → Replace ○  Keep Both ●  Skip ○            │
│ • diffuse (exists) → Replace ○  Keep Both ●  Skip ○           │
│                                                                 │
│ Resolution Options:                                             │
│ ☑️ Auto-rename conflicting objects                             │
│ ☑️ Preserve existing render layer overrides                    │
│ ☑️ Create backup of current scene before import                │
│                                                                 │
│                    [Proceed with Import] [Cancel] [Review]     │
└─────────────────────────────────────────────────────────────────┘
```

### Package Dependency Tracking

#### package_info.json Structure
```json
{
    "package_name": "sq010_SH0010_master_pkg",
    "package_version": "v001",
    "package_type": "master",
    "created_date": "2025-09-15T10:30:00Z",
    "created_by": "Sarah",
    "description": "Master lighting setup for forest sequence",
    "maya_version": "2024.1",
    "renderer": "Arnold 7.2.4.0",
    "dependencies": {
        "parent_template": "sq010_master_pkg_v002",
        "inherited_from": ["ep01_master_pkg_v001"],
        "required_assets": ["forest_environment_v003", "character_rigs_v012"]
    },
    "contents": {
        "maya_light_file": {
            "filename": "sq010_SH0010_light_master.ma",
            "light_count": 12,
            "light_types": ["directionalLight", "spotLight", "areaLight"],
            "checksum": "a1b2c3d4e5f6"
        },
        "render_layers": {
            "filename": "render_layers.json",
            "layer_count": 8,
            "layers": ["beauty", "diffuse", "specular", "shadow", "reflection"],
            "checksum": "f6e5d4c3b2a1"
        },
        "render_settings": {
            "filename": "render_settings.json",
            "renderer": "Arnold",
            "checksum": "1a2b3c4d5e6f"
        },
        "aovs": {
            "filename": "aovs.json",
            "aov_count": 15,
            "checksum": "6f5e4d3c2b1a"
        }
    },
    "compatibility": {
        "contexts": ["forest", "outdoor", "daylight"],
        "asset_types": ["environment", "character"],
        "shot_types": ["wide", "medium", "close"]
    }
}
```

## �🔄 User Flow Diagrams

### Enhanced Template-Integrated User Workflows

#### Initial Setup Phase Flow
```
[Navigate to Asset/Shot] → [Load Reference Geometry] → [Discover Available Templates]
   ↓
[Import Existing Templates] → [Review Template Compatibility] → [Apply Base Setup]
   ↓
[Verify Context Integration] → [Ready for Creation Phase]
```

#### Creation Phase Flow (Context-Aware)
```
[Create New Render Layers] → [Reference Light Templates] → [Apply Context Naming]
   ↓
[Configure Layer Collections] → [Set up Context-Specific AOVs] → [Test Integration]
   ↓
[Validate Template Inheritance] → [Ready for Publishing Phase]
```

#### Publishing Phase Flow
```
[Export Render Layer Config] → [Export Lighting Setup] → [Generate Template Metadata]
   ↓
[Save to Context Location] → [Update Template Hierarchy] → [Mark Available for Inheritance]
   ↓
[Notify Similar Contexts] → [End: Template Published and Available]
```

### Master Setup Creation Flow (Senior Artist - Sarah)
```
[Start] → [Open Tool] → [Navigate to Sequence] → [Create Master Template]
   ↓
[Configure Base Lights] → [Set up Master Layers] → [Test Across Shot Types] → [Publish Master Template]
   ↓
[Document Template Usage] → [Mark as Sequence Master] → [End: Master Ready for Key Shot Enhancement]
```

### Key Shot Adaptation Flow (Mid-Level Artist - Mike)
```
[Start] → [Navigate to Key Shot] → [Inherit Master Template] → [Create Key Shot Enhancement]
   ↓
[Add Hero Lighting] → [Extend Master Collections] → [Add Shot-Specific AOVs] → [Test Master Integration]
   ↓
[Publish Key Shot Template] → [Document Enhancements] → [Mark Available for Child Shots] → [End: Key Shot Template Ready]
```

### Child Shot Assignment Flow (Junior Artist - Jenny)
```
[Start] → [Navigate to Child Shot] → [Discover Key Shot Templates] → [Select Compatible Template]
   ↓
[Apply Template Inheritance] → [Review Context Integration] → [Make Micro-Adjustments] → [Test Template Compatibility]
   ↓
[Save Micro-Template] → [Consistency Check] → [End: Child Shot Complete with Micro-Template Saved]
```

### Director Change Propagation Flow (Production Scenario)
```
[Director Feedback] → [Senior Artist Opens Master] → [Make Master Changes] → [System Calculates Impact]
   ↓
[Automatic Propagation] → [Update All Dependent Shots] → [Team Reviews Changes] → [Manual Fix Conflicts]
   ↓
[Validation Complete] → [End: Sequence Updated Consistently]
```

## 🎯 Detailed User Interaction Flows

### File Selection and Import Flow
```
User Action: Double-click file in list
   ↓
System: Get file info from item data
   ↓
System: Call import_selected_file("reference")
   ↓
Backend: asset_shot_navigator.import_file(filepath, "reference")
   ↓
Maya API: cmds.file(filepath, reference=True, namespace=":")
   ↓
System: Display success/error message
   ↓
End: File referenced in scene
```

### Context Menu Interaction Flow
```
User Action: Right-click on file item
   ↓
System: Show context menu with options
   ↓
User Action: Select menu option (e.g., "Make Hero")
   ↓
System: Get file info from item data
   ↓
Backend: version_manager.create_hero_link(source, hero_path)
   ↓
File System: Create symlink/copy file
   ↓
System: Refresh file list to show new hero
   ↓
End: Hero file created and displayed
```

### Cascading Selection Flow (Episode → Sequence → Shot)
```
User Action: Select episode from combo
   ↓
Signal: episode_combo.currentTextChanged.emit(episode)
   ↓
Slot: on_episode_changed(episode)
   ↓
Backend: project_structure.get_sequences(episode)
   ↓
System: sequence_combo.clear() + addItems(sequences)
   ↓
Signal: sequence_combo.currentTextChanged.emit(sequence)
   ↓
Slot: on_sequence_changed(sequence)
   ↓
Backend: project_structure.get_shots(episode, sequence)
   ↓
System: shot_combo.clear() + addItems(shots)
   ↓
Signal: shot_combo.currentTextChanged.emit(shot)
   ↓
Slot: on_shot_changed(shot)
   ↓
System: refresh_shot_files()
   ↓
End: File list populated for selected shot
```

## 🔧 Technical Implementation Details



This comprehensive UI design specification provides the complete blueprint for implementing the modular LRC Manager interface while preserving all existing functionality and supporting the UI-first development approach with placeholder backends.
