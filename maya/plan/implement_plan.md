# LRC Manager Refactoring Implementation Plan - UI-First Approach

## 📋 Overview

This document outlines the comprehensive refactoring plan for transforming the monolithic `lrc_manager.py` (1829 lines) into a modular architecture with clear separation of concerns. **This plan prioritizes UI development first with placeholder backend functions to enable immediate user testing and feedback.**

## 🎯 Enhanced Refactoring Objectives

### Primary Goals
1. **Separate into distinct modules**: Core, Utils, UI, Importers, Exporters
2. **User-Centered Design**: Maintain manual control over all operations
3. **Template-Driven Architecture**: Context-aware template management with inheritance
4. **Context-Aware Operations**: All operations respect current asset/shot navigation context
5. **Flexible Architecture**: Support multiple workflows and edge cases with template inheritance
6. **Modular Independence**: Each function/module works independently
7. **Rebuild-Capable**: Enable complete reconstruction from exported data
8. **API-Driven**: Use Maya Render Setup Python API exclusively
9. **Pattern-Based Naming**: Consistent naming patterns based on project context

### Code Quality Standards
- Google-style docstrings for all functions, classes, and modules
- Black code formatter for consistent styling
- flake8 linting compliance
- Comprehensive unit and integration testing

## 🏗️ Current Code Analysis

### Existing Classes (7 total, 1829 lines)
- **ProjectStructure** (110 lines): File system navigation
- **VersionManager** (130 lines): Version control and hero files
- **AssetShotNavigator** (106 lines): High-level navigation
- **RenderSetupManager** (117 lines): Maya Render Setup operations
- **LightManager** (85 lines): Light operations and naming
- **RegexConverter** (31 lines): DAG path to regex conversion
- **RenderSetupUI** (1020 lines): Complete UI implementation ⚠️ MASSIVE

### Key Dependencies
- **Maya APIs**: cmds, mel, OpenMayaUI, Render Setup modules
- **UI Framework**: PySide2/PySide6 with shiboken
- **System Libraries**: os, shutil, subprocess, glob, json, re, datetime

## 🏛️ Proposed Modular Architecture

```
maya/src/lrc_toolbox/
├── __init__.py
├── core/                    # Business logic and data models
│   ├── __init__.py
│   ├── models.py           # Data structures and schemas
│   ├── project_manager.py  # ProjectStructure → here (PLACEHOLDER FIRST)
│   ├── version_manager.py  # VersionManager → here (PLACEHOLDER FIRST)
│   ├── template_manager.py # Template management system (PLACEHOLDER FIRST)
│   ├── light_manager.py    # Enhanced light operations (PLACEHOLDER FIRST)
│   └── render_setup_api.py # RenderSetupManager → here (PLACEHOLDER FIRST)
├── utils/                   # Helper functions and shared components
│   ├── __init__.py
│   ├── file_operations.py  # File system utilities (PLACEHOLDER FIRST)
│   ├── naming_conventions.py # Naming rule management (PLACEHOLDER FIRST)
│   ├── regex_tools.py      # RegexConverter → here (PLACEHOLDER FIRST)
│   └── maya_helpers.py     # Maya-specific helpers (PLACEHOLDER FIRST)
├── ui/                     # User interface components (PRIORITY 1)
│   ├── __init__.py
│   ├── main_window.py      # Main UI structure (IMPLEMENT FIRST)
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── asset_navigator.py    # Enhanced asset/shot navigation with templates (IMPLEMENT FIRST)
│   │   ├── template_widget.py    # Context-aware template management (IMPLEMENT FIRST)
│   │   ├── render_setup_widget.py # Render setup UI (IMPLEMENT FIRST)
│   │   ├── light_manager_widget.py # Enhanced light management with patterns (IMPLEMENT FIRST)
│   │   ├── regex_tools_widget.py  # Regex tools UI (IMPLEMENT FIRST)
│   │   └── settings_widget.py     # Settings UI (IMPLEMENT FIRST)
│   └── dialogs/
│       ├── __init__.py
│       ├── version_dialog.py     # Version save dialog (IMPLEMENT FIRST)
│       ├── template_dialog.py    # Template creation dialog (IMPLEMENT FIRST)
│       └── inheritance_dialog.py # Template inheritance dialog (IMPLEMENT FIRST)
├── importers/              # Data ingestion and file reading
│   ├── __init__.py
│   ├── base_importer.py    # Base importer interface (PLACEHOLDER FIRST)
│   ├── scene_importer.py   # Scene file import (PLACEHOLDER FIRST)
│   ├── light_importer.py   # Light-only import (PLACEHOLDER FIRST)
│   └── render_setup_importer.py # Render setup import (PLACEHOLDER FIRST)
├── exporters/              # Data output and file writing
│   ├── __init__.py
│   ├── base_exporter.py    # Base exporter interface (PLACEHOLDER FIRST)
│   ├── scene_exporter.py   # Scene file export (PLACEHOLDER FIRST)
│   ├── light_exporter.py   # Light-only export (PLACEHOLDER FIRST)
│   ├── template_exporter.py # Template export (PLACEHOLDER FIRST)
│   └── render_setup_exporter.py # Render setup export (PLACEHOLDER FIRST)
├── config/
│   ├── __init__.py
│   ├── settings.py         # Application settings (PLACEHOLDER FIRST)
│   └── defaults.py         # Default configurations (PLACEHOLDER FIRST)
└── main.py                 # Entry point and UI launcher (IMPLEMENT FIRST)
```

## 🎭 Placeholder Implementation Strategy

### UI-First Development Approach
The refactoring prioritizes UI components to enable immediate user testing and feedback. All backend modules start as placeholders with realistic mock data.

### Placeholder Function Examples

#### Core Module Placeholders
```python
# core/project_manager.py (Phase 1 - Placeholder)
class ProjectManager:
    """Placeholder ProjectManager with mock data for UI development."""

    def __init__(self, root_path="V:/SWA/all"):
        self.root_path = root_path
        self._mock_data = self._generate_mock_data()

    def get_episodes(self):
        """Return mock episodes for UI testing."""
        return ["Ep01", "Ep02", "Ep03", "Ep04", "Ep05"]

    def get_sequences(self, episode):
        """Return mock sequences for UI testing."""
        return [f"sq{i:04d}" for i in range(10, 50, 10)]

    def get_shots(self, episode, sequence):
        """Return mock shots for UI testing."""
        return [f"SH{i:04d}" for i in range(10, 100, 10)]

    # ... more placeholder methods with realistic mock data

# core/version_manager.py (Phase 1 - Placeholder)
class VersionManager:
    """Placeholder VersionManager with mock responses."""

    def save_with_version(self, lighting_dir, base_name, description="", create_hero=True):
        """Mock version save that always succeeds."""
        return True, f"Mock: Saved version 5: {base_name}_v0005.ma\nMock: Hero link created"

    def get_versions(self, version_dir):
        """Return mock version data."""
        return [
            {'file': 'scene_v0001.ma', 'version': 1, 'path': '/mock/path/v0001.ma'},
            {'file': 'scene_v0002.ma', 'version': 2, 'path': '/mock/path/v0002.ma'},
            {'file': 'scene_v0003.ma', 'version': 3, 'path': '/mock/path/v0003.ma'},
        ]
```

#### Import/Export Placeholders
```python
# importers/scene_importer.py (Phase 1 - Placeholder)
class SceneImporter:
    """Placeholder scene importer with mock responses."""

    def import_file(self, filepath, import_type="reference"):
        """Mock import that always succeeds."""
        filename = filepath.split('/')[-1] if '/' in filepath else filepath
        return True, f"Mock: Successfully {import_type}ed: {filename}"

# exporters/scene_exporter.py (Phase 1 - Placeholder)
class SceneExporter:
    """Placeholder scene exporter with mock responses."""

    def export_template(self, path_type, base_name, *args):
        """Mock export that always succeeds."""
        template_name = f"{base_name}_template.ma"
        return True, f"Mock: Template exported: {template_name}"
```

### Mock Data Strategy
- **Realistic Data**: Placeholders return data that matches expected real-world formats
- **Consistent Responses**: Same inputs always return same mock outputs for predictable UI behavior
- **Success Bias**: Most operations return success to enable UI flow testing
- **Error Simulation**: Some placeholders include optional error simulation for testing error handling

### UI Development Benefits
1. **Immediate Feedback**: UI can be tested and refined without waiting for backend implementation
2. **Parallel Development**: UI and backend can be developed simultaneously by different team members
3. **User Testing**: Stakeholders can provide feedback on interface before backend complexity is added
4. **Rapid Iteration**: UI changes can be made quickly without backend dependencies
5. **Integration Testing**: UI-backend integration can be tested incrementally as real functions replace placeholders
6. **Risk Mitigation**: UI issues discovered early before significant backend investment
7. **Stakeholder Engagement**: Visual progress maintains stakeholder interest and involvement

## 🔄 UI-First Development Advantages

### Why UI-First Approach?
- **User-Centric Development**: Ensures the interface meets user needs from day one
- **Early Validation**: Validates workflows and user interactions before complex backend development
- **Reduced Rework**: UI feedback incorporated before backend constraints are established
- **Faster Time-to-Demo**: Working interface available for demonstrations within days
- **Team Coordination**: UI developers can work independently while backend team focuses on core logic
- **Iterative Refinement**: Interface can be polished and perfected while backend is being implemented

### Placeholder-to-Real Transition Strategy
1. **Consistent APIs**: Placeholder functions maintain same signatures as final implementations
2. **Gradual Replacement**: Replace one module at a time without breaking UI functionality
3. **Testing Continuity**: UI tests continue working as placeholders are replaced
4. **User Transparency**: Users experience no disruption during backend implementation
5. **Rollback Capability**: Can revert to placeholders if real implementation has issues

## 📅 Implementation Timeline (6 Weeks) - UI-First Approach

### Phase 1: UI Components with Placeholder Backend (Week 1-2)
**Priority: HIGHEST - Immediate user testing and feedback**

#### Step 1.1: Create Module Structure with Placeholders
- [ ] Create directory structure as outlined above
- [ ] Set up all `__init__.py` files with proper imports
- [ ] Create base configuration files (`config/settings.py`, `config/defaults.py`)
- [ ] Set up development environment (Black, flake8, pytest)
- [ ] **Create placeholder modules with stub functions for all backend components**

#### Step 1.2: Enhanced Placeholder Backend Implementation
- [ ] Create `core/project_manager.py` with placeholder `ProjectManager` class
- [ ] Create `core/version_manager.py` with placeholder `VersionManager` class
- [ ] Create `core/template_manager.py` with placeholder `TemplateManager` class (NEW)
- [ ] Create `core/render_setup_api.py` with placeholder `RenderSetupAPI` class
- [ ] Create `core/light_manager.py` with enhanced placeholder `LightManager` class
- [ ] Create all `utils/` modules with placeholder functions returning mock data
- [ ] Create all `importers/` and `exporters/` with placeholder success responses
- [ ] **All placeholders return realistic mock data including template hierarchies**

#### Step 1.3: Main Window Structure
- [ ] Extract main window setup → `ui/main_window.py`
- [ ] Create tab management system
- [ ] Implement docking functionality
- [ ] Connect to placeholder backend APIs
- [ ] **Ensure UI is fully functional with mock data**

#### Step 1.4: Enhanced Widget Extraction (LARGEST EFFORT - Week 2)
- [ ] `ui/widgets/asset_navigator.py` - Enhanced asset/shot navigation with templates (500+ lines)
  - [ ] Connect to placeholder `ProjectManager`, `VersionManager`, and `TemplateManager`
  - [ ] Display mock episodes, sequences, shots, and files
  - [ ] Implement context-aware template discovery and display
  - [ ] Add template management controls (import, publish, inherit)
  - [ ] Implement all UI interactions with placeholder responses
- [ ] `ui/widgets/template_widget.py` - Context-aware template management (NEW)
  - [ ] Connect to placeholder `TemplateManager`
  - [ ] Display template hierarchy and inheritance chains
  - [ ] Implement template operations with mock responses
- [ ] `ui/widgets/render_setup_widget.py` - Render setup management
  - [ ] Connect to placeholder `RenderSetupAPI`
  - [ ] Display mock templates and render layers
- [ ] `ui/widgets/light_manager_widget.py` - Enhanced light management with patterns
  - [ ] Connect to placeholder `LightManager`
  - [ ] Implement pattern-based naming with context awareness
  - [ ] Display mock light lists and real-time naming previews
- [ ] `ui/widgets/regex_tools_widget.py` - Regex tools
  - [ ] Connect to placeholder regex utilities
- [ ] `ui/widgets/settings_widget.py` - Settings management
  - [ ] Connect to placeholder settings system

#### Step 1.5: Enhanced Dialog Components
- [ ] `ui/dialogs/version_dialog.py` - Version save dialog
- [ ] `ui/dialogs/template_dialog.py` - Template creation dialog
- [ ] `ui/dialogs/inheritance_dialog.py` - Template inheritance dialog (NEW)
- [ ] Implement proper signal/slot connections with placeholder backends
- [ ] **Create `main.py` entry point for immediate UI testing with template features**

### Phase 2: Core Business Logic Implementation (Week 3)
**Priority: HIGH - Replace placeholders with real functionality**

#### Step 2.1: Core Data Management
- [ ] Implement real `ProjectStructure` → `core/project_manager.py`
- [ ] Implement real `VersionManager` → `core/version_manager.py`
- [ ] Implement real `TemplateManager` → `core/template_manager.py` (NEW)
- [ ] Create `core/models.py` for data structures including template metadata
- [ ] **Replace placeholder functions with real implementations**
- [ ] **Test UI integration with real backend**

#### Step 2.2: Enhanced Render Setup and Light Management
- [ ] Implement real render setup logic → `core/render_setup_api.py`
- [ ] Create clean API wrapper around Maya Render Setup
- [ ] Implement enhanced light operations → `core/light_manager.py`
- [ ] Add pattern-based naming system with context awareness
- [ ] Implement template import/export functionality
- [ ] **Replace placeholder functions with Maya API calls**
- [ ] **Verify UI functionality with real Maya integration and template system**

### Phase 3: Utilities and Tools Implementation (Week 4)
**Priority: MEDIUM - Supporting functionality**

#### Step 3.1: Utility Modules
- [ ] Implement real `RegexConverter` → `utils/regex_tools.py`
- [ ] Implement file operations → `utils/file_operations.py`
- [ ] Implement naming logic → `utils/naming_conventions.py`
  - **Render Layer Naming**: `{context}_{element}_{variance}` format
    - Context: MASTER, SHOT, ASSET identifiers
    - Element: BG, CHAR, ATMOS, FX
    - Variance: A (default), B, C (ATMOS omits variance)
    - Examples: MASTER_BG_A, MASTER_CHAR_A, MASTER_ATMOS, MASTER_FX_A
- [ ] Create `utils/maya_helpers.py`
- [ ] **Replace all placeholder utility functions**

#### Step 3.2: Configuration and Settings
- [ ] Implement real settings management system
- [ ] Create persistent configuration storage
- [ ] **Replace placeholder settings with real functionality**

### Phase 4: Import/Export System Implementation (Week 5)
**Priority: MEDIUM - Data flow functionality**

#### Step 4.1: Base Import/Export Classes
- [ ] Implement real `importers/base_importer.py` with common interface
- [ ] Implement real `exporters/base_exporter.py` with common interface
- [ ] Define real error handling and progress reporting
- [ ] **Replace placeholder import/export responses**

#### Step 4.2: Specific Importers and Exporters
- [ ] Implement all specific importer classes with real Maya operations
- [ ] Implement all specific exporter classes with real Maya operations
- [ ] **Replace placeholder success responses with real file operations**
- [ ] Test round-trip import/export workflows

### Phase 5: Integration, Testing, and Polish (Week 6)
**Priority: HIGH - Quality assurance and finalization**

#### Step 5.1: Final Integration
- [ ] Remove all remaining placeholder functions
- [ ] Verify all UI components work with real backend
- [ ] Test complete workflows end-to-end
- [ ] Create backward compatibility layer
- [ ] Performance optimization

#### Step 5.2: Testing and Documentation
- [ ] Unit tests for all real implementations (80%+ coverage)
- [ ] Integration tests for complete workflows
- [ ] UI component tests
- [ ] Maya API interaction tests
- [ ] Update documentation with real API signatures

## ⚠️ Breaking Changes and Migration Strategy

### Potential Breaking Changes
1. **Import statements** - All imports change from single file to modular
2. **Class instantiation** - Different initialization parameters
3. **Method signatures** - Methods moved or modified
4. **Configuration storage** - Settings reorganization

### Migration Strategy
1. **Backward Compatibility Layer**: Create `legacy.py` with old interface
2. **Gradual Migration**: Keep original file as deprecated wrapper
3. **Clear Documentation**: Before/after examples and migration guide
4. **Version Tagging**: Tag current version before refactoring

## 🧪 Testing Strategy

### Unit Tests Structure
```python
tests/
├── test_core/
│   ├── test_project_manager.py
│   ├── test_version_manager.py
│   └── test_render_setup_api.py
├── test_utils/
│   ├── test_file_operations.py
│   ├── test_naming_conventions.py
│   └── test_regex_tools.py
├── test_importers/
└── test_exporters/
```

### Testing Approach
- **Unit Tests**: Mock Maya APIs, test individual functions
- **Integration Tests**: Test complete workflows in Maya environment
- **UI Tests**: Test widget interactions and signal/slot connections
- **Performance Tests**: Benchmark before/after refactoring

## 📏 Code Quality Implementation

### Google-Style Docstrings Template
```python
def create_hero_link(self, source_file: str, hero_path: str) -> tuple[bool, str]:
    """Create hero file using Windows symlink or fallback methods.
    
    Args:
        source_file: Path to the source version file.
        hero_path: Path where hero file should be created.
        
    Returns:
        A tuple containing:
            - bool: True if successful, False otherwise.
            - str: Success/error message describing the operation result.
            
    Raises:
        OSError: If file system operations fail.
        PermissionError: If insufficient permissions for link creation.
        
    Example:
        >>> version_manager = VersionManager()
        >>> success, message = version_manager.create_hero_link(
        ...     "/path/to/scene_v001.ma", 
        ...     "/path/to/scene_hero.ma"
        ... )
        >>> print(f"Success: {success}, Message: {message}")
    """
```

### Black Configuration
```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py37', 'py38', 'py39']
include = '\.pyi?$'
```

### Flake8 Configuration
```ini
# .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist
```

## 🎯 Success Criteria - UI-First Approach

### Phase 1 Success Criteria (UI with Placeholders)
- [ ] **Working UI Interface**: All tabs and widgets functional with mock data
- [ ] **User Interaction**: All buttons, menus, and dialogs respond appropriately
- [ ] **Visual Consistency**: UI matches original design and behavior
- [ ] **Placeholder Integration**: All UI components successfully connect to placeholder backends
- [ ] **Immediate Testing**: Stakeholders can interact with and provide feedback on UI

### Functional Requirements (Final)
- [ ] All existing functionality preserved
- [ ] User workflows unchanged
- [ ] Performance maintained or improved
- [ ] Maya API compatibility maintained
- [ ] **Seamless Transition**: Users cannot tell when placeholders are replaced with real functionality

### Quality Requirements
- [ ] 80%+ test coverage (applied as real functions replace placeholders)
- [ ] All code passes Black formatting
- [ ] All code passes flake8 linting
- [ ] All functions have Google-style docstrings
- [ ] No circular dependencies between modules
- [ ] **UI Responsiveness**: Interface remains responsive during all operations

### Architectural Requirements
- [ ] Clear separation of concerns
- [ ] Modular independence verified
- [ ] API consistency across modules
- [ ] Backward compatibility maintained
- [ ] **Placeholder-to-Real Migration**: Smooth transition from mock to real implementations

## 🚀 Next Steps - UI-First Implementation

### Immediate Actions (Week 1)
1. **Review and Approve UI-First Approach**: Confirm prioritization of UI development
2. **Set Up Development Environment**: Configure Black, flake8, pytest
3. **Create Development Branch**: Start UI-first refactoring in isolated branch
4. **Begin Phase 1**: Create module structure with comprehensive placeholders
5. **Implement Main UI Window**: Get basic interface running with mock data

### Week 1 Deliverables
- [ ] **Working UI Demo**: Functional interface with all tabs and basic interactions
- [ ] **Placeholder Backend**: All backend modules with realistic mock responses
- [ ] **User Testing Ready**: Interface ready for stakeholder feedback and testing
- [ ] **Development Framework**: Environment set up for parallel UI/backend development

### Ongoing Process
- **Daily UI Testing**: Continuous testing of interface functionality
- **Weekly Stakeholder Reviews**: Regular feedback sessions on UI design and workflow
- **Incremental Backend Integration**: Replace placeholders with real functionality one module at a time
- **Continuous Integration**: Ensure UI continues working as backend is implemented

## 📞 Support and Resources

- **Documentation**: Maintain updated API documentation
- **Code Reviews**: Peer review for each phase
- **Testing**: Continuous integration setup
- **Rollback Plan**: Clear rollback strategy if issues arise

---

**Document Version**: 1.0  
**Last Updated**: 2025-09-15  
**Estimated Effort**: 6 weeks (1 developer)  
**Risk Level**: Medium (well-planned, gradual approach)
