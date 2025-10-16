# LRC Toolbox v2.0 - Enhanced Template Management

A modular Maya lighting and render setup management tool with enhanced template management system and context-aware workflows.

## 🎯 Features

### Enhanced Template Management
- **Context-Aware Templates**: Templates organized by project hierarchy (Episode → Sequence → Shot)
- **Template Inheritance**: Master → Key Shot → Child Shot workflow support
- **Automatic Discovery**: Templates automatically discovered based on current navigation context
- **Template Types**: Master, Key Shot, Standard, and Micro templates with visual indicators

### Pattern-Based Light Naming
- **Context Integration**: Sequence and shot information auto-populated from navigation
- **Real-Time Preview**: See naming results before applying changes
- **Batch Operations**: Rename multiple lights with sequential indexing
- **Customizable Patterns**: Flexible naming patterns based on project requirements

### Modular Architecture
- **UI-First Development**: Functional interface with placeholder backends for immediate testing
- **Clear Separation**: Core business logic, utilities, UI components, and import/export systems
- **Maya Integration**: Dockable interface with fallback to standalone window
- **Extensible Design**: Easy to add new features and workflows

## 🏗️ Project Structure

```
maya/lrc_toolbox/
├── core/                    # Business logic and data models
│   ├── project_manager.py   # Project structure navigation
│   ├── version_manager.py   # Version control and hero files
│   ├── template_manager.py  # Template management system
│   ├── light_manager.py     # Enhanced light operations
│   ├── render_setup_api.py  # Maya Render Setup integration
│   └── models.py           # Data structures and schemas
├── utils/                   # Helper functions and shared components
│   ├── file_operations.py   # File system utilities
│   ├── naming_conventions.py # Naming rule management
│   ├── regex_tools.py       # DAG path to regex conversion
│   └── maya_helpers.py      # Maya-specific helpers
├── ui/                      # User interface components
│   ├── main_window.py       # Main application window
│   ├── widgets/             # Specialized UI widgets
│   │   ├── asset_navigator.py    # Enhanced asset/shot navigation
│   │   ├── template_widget.py    # Template management interface
│   │   ├── light_manager_widget.py # Pattern-based light naming
│   │   ├── render_setup_widget.py # Render setup management
│   │   ├── regex_tools_widget.py  # Regex conversion tools
│   │   └── settings_widget.py     # Configuration interface
│   └── dialogs/             # Dialog windows
│       ├── version_dialog.py     # Version save dialog
│       ├── template_dialog.py    # Template creation dialog
│       └── inheritance_dialog.py # Template inheritance dialog
├── importers/               # Data ingestion and file reading
├── exporters/               # Data output and file writing
├── config/                  # Configuration and settings
└── tests/                   # Unit and integration tests
```

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/lrc-toolbox/lrc-toolbox.git
cd lrc-toolbox
```

2. Install development dependencies:
```bash
pip install -e .[dev]
```

### Running in Maya

```python
# In Maya Script Editor
import sys
sys.path.append(r"E:/dev/LRCtoolsbox/LRCtoolsbox/maya")

from lrc_toolbox.main import create_dockable_ui
ui = create_dockable_ui()
```

### Standalone Development

```bash
cd maya
python -m lrc_toolbox.main
```

## 🧪 Development

### Code Quality Standards
- **Black** code formatting
- **flake8** linting compliance
- **Google-style** docstrings
- **Comprehensive** unit and integration testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest -m "ui"        # UI tests only
pytest -m "maya"      # Maya integration tests
```

### Code Formatting
```bash
# Format code
black maya/lrc_toolbox/

# Check linting
flake8 maya/lrc_toolbox/
```

## 📋 Implementation Status

### Phase 1: UI Components with Template Management ✅
- [x] Project structure created
- [x] Configuration system implemented
- [x] Main entry point created
- [ ] Placeholder backends (In Progress)
- [ ] UI widgets implementation (Planned)

### Phase 2: Backend Implementation (Planned)
- [ ] Real Maya API integration
- [ ] Template management system
- [ ] Pattern-based light naming
- [ ] File operations

### Phase 3: Advanced Features (Planned)
- [ ] Import/export system
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation

## 🎨 User Workflows Supported

### Senior Artist (Master Setup Creation)
1. Navigate to sequence level
2. Create comprehensive lighting setup
3. Configure render layers and collections
4. Publish as master template for inheritance

### Mid-Level Artist (Key Shot Enhancement)
1. Navigate to key shot
2. Inherit master template
3. Add hero lighting and shot-specific elements
4. Publish enhanced template for child shots

### Junior Artist (Child Shot Assignment)
1. Navigate to child shot
2. Discover and apply key shot template
3. Make micro-adjustments as needed
4. Save micro-template for similar shots

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the code quality standards
4. Add tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Maya Python API documentation
- PySide2/PySide6 Qt framework
- The lighting and rendering community for workflow insights
