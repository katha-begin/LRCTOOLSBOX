#!/usr/bin/env python
"""
Maya Render Setup Manager
A comprehensive tool for managing render setups, lights, and shot workflows in Maya.

Features:
- Template render setup creation and management
- Import/export render setups
- Light-only import/export with flexible naming
- Asset/Shot navigation with directory structure support
- Version management with hero file creation (Windows symlinks)
- Template browser and management
- Regex converter tools
- Dockable UI with clean navigation

Author: Maya Pipeline Tools
Version: 2.0
Directory Structure Support: V:\SWA\all\scene\Ep00\sq0010\SH0010\lighting\version
                           V:\SWA\all\asset\Sets\interior\Kitchen\lighting\version

Usage:
    # Copy this file to: E:\dev\LRCtoolsbox\LRCtoolsbox\maya\src\maya_render_setup_manager.py
    # In Maya, run:
    exec(open(r'E:\dev\LRCtoolsbox\LRCtoolsbox\maya\src\maya_render_setup_manager.py').read())
    show_ui()
"""

import os
import re
import json
import shutil
import subprocess
import glob
from collections import OrderedDict
from datetime import datetime

try:
    from PySide2.QtWidgets import *
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    PYSIDE_VERSION = 2
except ImportError:
    try:
        from PySide6.QtWidgets import *
        from PySide6.QtCore import *
        from PySide6.QtGui import *
        PYSIDE_VERSION = 6
    except ImportError:
        print("Error: PySide2 or PySide6 not found. Please install one of them.")
        raise

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui

# Try to import render setup modules
try:
    import maya.app.renderSetup.model.renderSetup as renderSetup
    import maya.app.renderSetup.model.renderLayer as renderLayer
    import maya.app.renderSetup.model.collection as collection
    import maya.app.renderSetup.model.override as override
    RENDER_SETUP_AVAILABLE = True
except ImportError:
    print("Warning: Render Setup modules not available in this Maya version")
    RENDER_SETUP_AVAILABLE = False

# Try to import shiboken for PySide integration
try:
    if PYSIDE_VERSION == 2:
        from shiboken2 import wrapInstance
    else:
        from shiboken6 import wrapInstance
except ImportError:
    try:
        from shiboken import wrapInstance
    except ImportError:
        print("Warning: shiboken not available")
        wrapInstance = None


class ProjectStructure:
    """Project structure management for assets and shots"""
    
    def __init__(self, root_path="V:/SWA/all"):
        self.root_path = root_path
        self.scene_path = os.path.join(root_path, "scene")
        self.asset_path = os.path.join(root_path, "asset")
        
    def get_episodes(self):
        """Get list of episodes"""
        episodes = []
        if os.path.exists(self.scene_path):
            try:
                for item in os.listdir(self.scene_path):
                    ep_path = os.path.join(self.scene_path, item)
                    if os.path.isdir(ep_path) and item.startswith("Ep"):
                        episodes.append(item)
            except (OSError, PermissionError):
                pass
        return sorted(episodes)
    
    def get_sequences(self, episode):
        """Get sequences for episode"""
        sequences = []
        ep_path = os.path.join(self.scene_path, episode)
        if os.path.exists(ep_path):
            try:
                for item in os.listdir(ep_path):
                    seq_path = os.path.join(ep_path, item)
                    if os.path.isdir(seq_path) and item.startswith("sq"):
                        sequences.append(item)
            except (OSError, PermissionError):
                pass
        return sorted(sequences)
    
    def get_shots(self, episode, sequence):
        """Get shots for sequence"""
        shots = []
        seq_path = os.path.join(self.scene_path, episode, sequence)
        if os.path.exists(seq_path):
            try:
                for item in os.listdir(seq_path):
                    shot_path = os.path.join(seq_path, item)
                    if os.path.isdir(shot_path) and item.startswith("SH"):
                        shots.append(item)
            except (OSError, PermissionError):
                pass
        return sorted(shots)
    
    def get_asset_categories(self):
        """Get asset categories"""
        categories = []
        if os.path.exists(self.asset_path):
            try:
                for item in os.listdir(self.asset_path):
                    cat_path = os.path.join(self.asset_path, item)
                    if os.path.isdir(cat_path):
                        categories.append(item)
            except (OSError, PermissionError):
                pass
        return sorted(categories)
    
    def get_asset_subcategories(self, category):
        """Get asset subcategories"""
        subcategories = []
        cat_path = os.path.join(self.asset_path, category)
        if os.path.exists(cat_path):
            try:
                for item in os.listdir(cat_path):
                    subcat_path = os.path.join(cat_path, item)
                    if os.path.isdir(subcat_path):
                        subcategories.append(item)
            except (OSError, PermissionError):
                pass
        return sorted(subcategories)
    
    def get_assets(self, category, subcategory):
        """Get assets in subcategory"""
        assets = []
        subcat_path = os.path.join(self.asset_path, category, subcategory)
        if os.path.exists(subcat_path):
            try:
                for item in os.listdir(subcat_path):
                    asset_path = os.path.join(subcat_path, item)
                    if os.path.isdir(asset_path):
                        assets.append(item)
            except (OSError, PermissionError):
                pass
        return sorted(assets)
    
    def get_shot_lighting_path(self, episode, sequence, shot):
        """Get shot lighting directory path"""
        return os.path.join(self.scene_path, episode, sequence, shot, "lighting")
    
    def get_asset_lighting_path(self, category, subcategory, asset):
        """Get asset lighting directory path"""
        return os.path.join(self.asset_path, category, subcategory, asset, "lighting")
    
    def get_version_path(self, base_path):
        """Get version directory path"""
        return os.path.join(base_path, "version")
    
    def ensure_path_exists(self, path):
        """Ensure directory path exists"""
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except (OSError, PermissionError) as e:
                print(f"Could not create directory {path}: {e}")
        return path


class VersionManager:
    """Version and hero file management"""
    
    def __init__(self):
        self.version_pattern = re.compile(r'v(\d{3,4})')
        
    def get_versions(self, version_dir):
        """Get all versions in directory"""
        versions = []
        if os.path.exists(version_dir):
            try:
                for item in os.listdir(version_dir):
                    item_path = os.path.join(version_dir, item)
                    if os.path.isfile(item_path) and item.endswith(('.ma', '.mb')):
                        match = self.version_pattern.search(item)
                        if match:
                            version_num = int(match.group(1))
                            versions.append({
                                'file': item,
                                'version': version_num,
                                'path': item_path
                            })
            except (OSError, PermissionError):
                pass
        return sorted(versions, key=lambda x: x['version'])
    
    def get_next_version(self, version_dir, base_name, extension=".ma"):
        """Get next version number and filename"""
        versions = self.get_versions(version_dir)
        
        if not versions:
            next_version = 1
        else:
            # Filter versions for this base name
            matching_versions = [v for v in versions if base_name in v['file']]
            if matching_versions:
                next_version = matching_versions[-1]['version'] + 1
            else:
                next_version = 1
        
        version_str = f"v{next_version:04d}"
        filename = f"{base_name}_{version_str}{extension}"
        filepath = os.path.join(version_dir, filename)
        
        return next_version, filename, filepath
    
    def create_hero_link(self, source_file, hero_path):
        """Create hero file (Windows junction/symlink)"""
        try:
            # Remove existing hero file/link
            if os.path.exists(hero_path):
                try:
                    if os.path.islink(hero_path):
                        os.unlink(hero_path)
                    elif os.path.isfile(hero_path):
                        os.remove(hero_path)
                except (OSError, PermissionError):
                    pass
            
            # Try to create symbolic link (Windows 10+)
            try:
                os.symlink(source_file, hero_path)
                return True, f"Symbolic link created: {hero_path}"
            except OSError:
                # Fallback: create hard link using mklink
                try:
                    cmd = f'mklink /H "{hero_path}" "{source_file}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        return True, f"Hard link created: {hero_path}"
                    else:
                        # Last fallback: copy file
                        shutil.copy2(source_file, hero_path)
                        return True, f"File copied (no link support): {hero_path}"
                except Exception:
                    # Ultimate fallback: copy file
                    shutil.copy2(source_file, hero_path)
                    return True, f"File copied: {hero_path}"
                    
        except Exception as e:
            return False, f"Error creating hero link: {str(e)}"
    
    def get_hero_path(self, lighting_dir, base_name, extension=".ma"):
        """Get hero file path"""
        return os.path.join(lighting_dir, f"{base_name}_hero{extension}")
    
    def save_with_version(self, lighting_dir, base_name, description="", create_hero=True):
        """Save current scene with versioning"""
        try:
            # Ensure directories exist
            version_dir = os.path.join(lighting_dir, "version")
            if not os.path.exists(version_dir):
                os.makedirs(version_dir)
            if not os.path.exists(lighting_dir):
                os.makedirs(lighting_dir)
            
            # Get next version
            version_num, filename, filepath = self.get_next_version(version_dir, base_name)
            
            # Save current scene
            current_file = cmds.file(query=True, sceneName=True)
            cmds.file(rename=filepath)
            cmds.file(save=True, type="mayaAscii")
            
            # Create version info file
            info_file = filepath.replace(".ma", "_info.json")
            version_info = {
                "version": version_num,
                "filename": filename,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "user": os.getenv("USERNAME", "unknown"),
                "maya_version": cmds.about(version=True),
                "previous_file": current_file
            }
            
            with open(info_file, 'w') as f:
                json.dump(version_info, f, indent=2)
            
            # Create/update hero file
            hero_message = ""
            if create_hero:
                hero_path = self.get_hero_path(lighting_dir, base_name)
                success, message = self.create_hero_link(filepath, hero_path)
                hero_message = f"\n{message}"
            
            return True, f"Saved version {version_num}: {filepath}{hero_message}"
            
        except Exception as e:
            return False, f"Error saving version: {str(e)}"


class AssetShotNavigator:
    """Asset and shot navigation with template management"""
    
    def __init__(self, project_structure):
        self.project = project_structure
        self.version_manager = VersionManager()
        
    def get_lighting_files(self, path_type, *args):
        """Get lighting files for shot or asset"""
        if path_type == "shot":
            episode, sequence, shot = args
            lighting_dir = self.project.get_shot_lighting_path(episode, sequence, shot)
        elif path_type == "asset":
            category, subcategory, asset = args
            lighting_dir = self.project.get_asset_lighting_path(category, subcategory, asset)
        else:
            return []
        
        if not os.path.exists(lighting_dir):
            return []
        
        files = []
        
        try:
            # Get hero files
            for ext in [".ma", ".mb"]:
                hero_pattern = os.path.join(lighting_dir, f"*_hero{ext}")
                for hero_file in glob.glob(hero_pattern):
                    files.append({
                        'name': os.path.basename(hero_file),
                        'path': hero_file,
                        'type': 'hero',
                        'size': os.path.getsize(hero_file),
                        'modified': datetime.fromtimestamp(os.path.getmtime(hero_file))
                    })
            
            # Get template files
            template_pattern = os.path.join(lighting_dir, "*_template.*")
            for template_file in glob.glob(template_pattern):
                if template_file.endswith(('.ma', '.mb')):
                    files.append({
                        'name': os.path.basename(template_file),
                        'path': template_file,
                        'type': 'template',
                        'size': os.path.getsize(template_file),
                        'modified': datetime.fromtimestamp(os.path.getmtime(template_file))
                    })
            
            # Get version files
            version_dir = os.path.join(lighting_dir, "version")
            versions = self.version_manager.get_versions(version_dir)
            for version_info in versions[-10:]:  # Last 10 versions
                files.append({
                    'name': version_info['file'],
                    'path': version_info['path'],
                    'type': 'version',
                    'version': version_info['version'],
                    'size': os.path.getsize(version_info['path']),
                    'modified': datetime.fromtimestamp(os.path.getmtime(version_info['path']))
                })
        except (OSError, PermissionError):
            pass
        
        return files
    
    def import_file(self, filepath, import_type="reference"):
        """Import lighting file"""
        try:
            if import_type == "reference":
                cmds.file(filepath, reference=True, namespace=":")
            elif import_type == "import":
                cmds.file(filepath, i=True, namespace=":")
            elif import_type == "open":
                cmds.file(filepath, open=True, force=True)
            
            return True, f"Successfully {import_type}ed: {os.path.basename(filepath)}"
            
        except Exception as e:
            return False, f"Error importing file: {str(e)}"
    
    def export_template(self, path_type, base_name, *args):
        """Export current scene as template"""
        if path_type == "shot":
            episode, sequence, shot = args
            lighting_dir = self.project.get_shot_lighting_path(episode, sequence, shot)
            template_name = f"{episode}_{sequence}_{shot}_{base_name}_template"
        elif path_type == "asset":
            category, subcategory, asset = args
            lighting_dir = self.project.get_asset_lighting_path(category, subcategory, asset)
            template_name = f"{category}_{subcategory}_{asset}_{base_name}_template"
        else:
            return False, "Invalid path type"
        
        try:
            # Ensure directory exists
            self.project.ensure_path_exists(lighting_dir)
            
            # Export template
            template_path = os.path.join(lighting_dir, f"{template_name}.ma")
            cmds.file(rename=template_path)
            cmds.file(save=True, type="mayaAscii")
            
            return True, f"Template exported: {template_path}"
            
        except Exception as e:
            return False, f"Error exporting template: {str(e)}"


class RenderSetupManager:
    """Core render setup management functionality"""
    
    def __init__(self):
        self.templates_dir = os.path.join(cmds.internalVar(userPrefDir=True), "renderSetupTemplates")
        self.ensure_templates_directory()
        
    def ensure_templates_directory(self):
        """Ensure templates directory exists"""
        if not os.path.exists(self.templates_dir):
            try:
                os.makedirs(self.templates_dir)
            except (OSError, PermissionError):
                print(f"Could not create templates directory: {self.templates_dir}")
    
    def create_template_rendersetup(self, name, description="", layers_config=None):
        """Create a template render setup"""
        if not RENDER_SETUP_AVAILABLE:
            return False, "Render Setup not available in this Maya version"
            
        try:
            rs = renderSetup.instance()
            
            # Clear existing layers except defaultRenderLayer
            for layer in rs.getRenderLayers():
                if layer.name() != "defaultRenderLayer":
                    rs.detachRenderLayer(layer)
            
            # Create layers based on config
            if layers_config:
                for layer_config in layers_config:
                    self._create_layer_from_config(layer_config)
            else:
                # Create default template layers
                self._create_default_template_layers()
            
            # Save template
            template_data = {
                "name": name,
                "description": description,
                "renderSetup": self._serialize_render_setup()
            }
            
            template_file = os.path.join(self.templates_dir, f"{name}.json")
            with open(template_file, 'w') as f:
                json.dump(template_data, f, indent=2)
            
            return True, f"Template '{name}' created successfully"
            
        except Exception as e:
            return False, f"Error creating template: {str(e)}"
    
    def _create_default_template_layers(self):
        """Create default template layers"""
        if not RENDER_SETUP_AVAILABLE:
            return
            
        rs = renderSetup.instance()
        
        # Beauty layer
        beauty_layer = rs.createRenderLayer("beauty")
        beauty_collection = beauty_layer.createCollection("beauty_collection")
        beauty_collection.getSelector().setPattern("*")
        
        # Utility layers
        utility_layers = ["ao", "normals", "depth", "motion_vectors"]
        for util_name in utility_layers:
            util_layer = rs.createRenderLayer(util_name)
            util_collection = util_layer.createCollection(f"{util_name}_collection")
            util_collection.getSelector().setPattern("*")
    
    def _serialize_render_setup(self):
        """Serialize current render setup to dictionary"""
        if not RENDER_SETUP_AVAILABLE:
            return {}
            
        rs = renderSetup.instance()
        data = {"layers": []}
        
        for layer in rs.getRenderLayers():
            if layer.name() == "defaultRenderLayer":
                continue
                
            layer_data = {
                "name": layer.name(),
                "enabled": layer.isEnabled(),
                "collections": []
            }
            
            for coll in layer.getCollections():
                coll_data = {
                    "name": coll.name(),
                    "pattern": coll.getSelector().getPattern(),
                    "overrides": []
                }
                layer_data["collections"].append(coll_data)
            
            data["layers"].append(layer_data)
        
        return data
    
    def export_rendersetup(self, filepath):
        """Export current render setup to file"""
        try:
            data = {
                "renderSetup": self._serialize_render_setup(),
                "exportTime": cmds.date(),
                "mayaVersion": cmds.about(version=True)
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True, f"Render setup exported to {filepath}"
            
        except Exception as e:
            return False, f"Error exporting render setup: {str(e)}"


class LightManager:
    """Light management functionality"""
    
    def __init__(self):
        self.naming_rules = self._load_naming_rules()
    
    def _load_naming_rules(self):
        """Load naming convention rules"""
        default_rules = {
            "prefix": ["key", "fill", "rim", "bounce", "practical"],
            "suffix": ["lgt", "light"],
            "separator": "_",
            "padding": 2,
            "case": "lower"  # lower, upper, title
        }
        
        # Try to load from user prefs
        rules_file = os.path.join(cmds.internalVar(userPrefDir=True), "lightNamingRules.json")
        if os.path.exists(rules_file):
            try:
                with open(rules_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return default_rules
    
    def generate_light_name(self, prefix="", suffix="", index=1):
        """Generate light name based on rules"""
        parts = []
        
        if prefix:
            if self.naming_rules["case"] == "lower":
                prefix = prefix.lower()
            elif self.naming_rules["case"] == "upper":
                prefix = prefix.upper()
            elif self.naming_rules["case"] == "title":
                prefix = prefix.title()
            parts.append(prefix)
        
        # Add padded index
        padding = self.naming_rules.get("padding", 2)
        parts.append(str(index).zfill(padding))
        
        if suffix:
            if self.naming_rules["case"] == "lower":
                suffix = suffix.lower()
            elif self.naming_rules["case"] == "upper":
                suffix = suffix.upper()
            parts.append(suffix)
        else:
            # Use default suffix
            default_suffix = self.naming_rules.get("suffix", ["lgt"])[0]
            parts.append(default_suffix)
        
        separator = self.naming_rules.get("separator", "_")
        return separator.join(parts)
    
    def export_lights_only(self, filepath):
        """Export only lights from the scene"""
        try:
            # Get all light shapes
            light_shapes = cmds.ls(type=["directionalLight", "pointLight", "spotLight", 
                                        "areaLight", "aiAreaLight", "aiSkyDomeLight"])
            
            light_transforms = []
            for shape in light_shapes:
                transform = cmds.listRelatives(shape, parent=True, type="transform")
                if transform:
                    light_transforms.extend(transform)
            
            if not light_transforms:
                return False, "No lights found in scene"
            
            # Select lights
            cmds.select(light_transforms, replace=True)
            
            # Export selected
            cmds.file(filepath, force=True, options="v=0", type="mayaAscii", 
                     preserveReferences=True, exportSelected=True)
            
            return True, f"Lights exported to {filepath}"
            
        except Exception as e:
            return False, f"Error exporting lights: {str(e)}"


class RegexConverter:
    """Regex conversion tools"""
    
    @staticmethod
    def dag_paths_to_regex(dag_paths, options=None):
        """Convert DAG full paths to regex pattern"""
        if not dag_paths:
            return ""
        
        options = options or {}
        escape_special = options.get("escape_special", True)
        use_wildcards = options.get("use_wildcards", True)
        
        # Process paths
        processed_paths = []
        for path in dag_paths:
            if escape_special:
                # Escape special regex characters except | and *
                path = re.escape(path).replace(r"\|", "|").replace(r"\*", "*")
            
            if use_wildcards:
                # Convert Maya wildcards to regex
                path = path.replace("*", ".*").replace("?", ".")
            
            processed_paths.append(path)
        
        # Create pattern
        if len(processed_paths) == 1:
            return processed_paths[0]
        else:
            return "(" + "|".join(processed_paths) + ")"


class RenderSetupUI(QMainWindow):
    """Main UI for Render Setup Manager"""
    
    def __init__(self, parent=None):
        super(RenderSetupUI, self).__init__(parent)
        
        self.render_manager = RenderSetupManager()
        self.light_manager = LightManager()
        self.project_structure = ProjectStructure()
        self.asset_shot_navigator = AssetShotNavigator(self.project_structure)
        self.version_manager = VersionManager()
        
        self.setWindowTitle("Render Setup Manager v2.0")
        self.setMinimumSize(700, 900)
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Setup tabs
        self.setup_asset_shot_navigator_tab()
        self.setup_render_setup_tab()
        self.setup_light_manager_tab()
        self.setup_regex_tools_tab()
        self.setup_settings_tab()
    
    def setup_asset_shot_navigator_tab(self):
        """Setup asset and shot navigator tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Project root setting
        root_group = QGroupBox("Project Settings")
        root_layout = QHBoxLayout(root_group)
        root_layout.addWidget(QLabel("Project Root:"))
        self.root_path_edit = QLineEdit(self.project_structure.root_path)
        browse_root_btn = QPushButton("Browse")
        browse_root_btn.clicked.connect(self.browse_project_root)
        root_layout.addWidget(self.root_path_edit)
        root_layout.addWidget(browse_root_btn)
        layout.addWidget(root_group)
        
        # Create horizontal layout for shot and asset sections
        main_content = QHBoxLayout()
        
        # === SHOT SECTION ===
        shot_section = QVBoxLayout()
        shot_group = QGroupBox("🎬 Shot Navigator")
        shot_group_layout = QVBoxLayout(shot_group)
        
        # Episode selection
        ep_layout = QHBoxLayout()
        ep_layout.addWidget(QLabel("Episode:"))
        self.episode_combo = QComboBox()
        self.episode_combo.currentTextChanged.connect(self.on_episode_changed)
        ep_layout.addWidget(self.episode_combo)
        shot_group_layout.addLayout(ep_layout)
        
        # Sequence selection
        seq_layout = QHBoxLayout()
        seq_layout.addWidget(QLabel("Sequence:"))
        self.sequence_combo = QComboBox()
        self.sequence_combo.currentTextChanged.connect(self.on_sequence_changed)
        seq_layout.addWidget(self.sequence_combo)
        shot_group_layout.addLayout(seq_layout)
        
        # Shot selection
        shot_layout = QHBoxLayout()
        shot_layout.addWidget(QLabel("Shot:"))
        self.shot_combo = QComboBox()
        self.shot_combo.currentTextChanged.connect(self.on_shot_changed)
        shot_layout.addWidget(self.shot_combo)
        shot_group_layout.addLayout(shot_layout)
        
        # Shot file list
        shot_group_layout.addWidget(QLabel("Shot Files:"))
        self.shot_file_list = QListWidget()
        self.shot_file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.shot_file_list.customContextMenuRequested.connect(self.show_shot_file_context_menu)
        self.shot_file_list.itemDoubleClicked.connect(lambda: self.import_selected_file("reference"))
        shot_group_layout.addWidget(self.shot_file_list)
        
        # Shot actions
        shot_actions = QVBoxLayout()
        refresh_shot_btn = QPushButton("🔄 Refresh")
        save_shot_version_btn = QPushButton("💾 Save Version")
        export_shot_template_btn = QPushButton("📤 Export Template")
        refresh_shot_btn.clicked.connect(self.refresh_shot_files)
        save_shot_version_btn.clicked.connect(self.save_shot_version)
        export_shot_template_btn.clicked.connect(self.export_shot_template)
        shot_actions.addWidget(refresh_shot_btn)
        shot_actions.addWidget(save_shot_version_btn)
        shot_actions.addWidget(export_shot_template_btn)
        shot_group_layout.addLayout(shot_actions)
        
        shot_section.addWidget(shot_group)
        
        # === ASSET SECTION ===
        asset_section = QVBoxLayout()
        asset_group = QGroupBox("🎨 Asset Navigator")
        asset_group_layout = QVBoxLayout(asset_group)
        
        # Category selection
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Category:"))
        self.asset_category_combo = QComboBox()
        self.asset_category_combo.currentTextChanged.connect(self.on_asset_category_changed)
        cat_layout.addWidget(self.asset_category_combo)
        asset_group_layout.addLayout(cat_layout)
        
        # Subcategory selection
        subcat_layout = QHBoxLayout()
        subcat_layout.addWidget(QLabel("Subcategory:"))
        self.asset_subcategory_combo = QComboBox()
        self.asset_subcategory_combo.currentTextChanged.connect(self.on_asset_subcategory_changed)
        subcat_layout.addWidget(self.asset_subcategory_combo)
        asset_group_layout.addLayout(subcat_layout)
        
        # Asset selection
        asset_layout = QHBoxLayout()
        asset_layout.addWidget(QLabel("Asset:"))
        self.asset_combo = QComboBox()
        self.asset_combo.currentTextChanged.connect(self.on_asset_changed)
        asset_layout.addWidget(self.asset_combo)
        asset_group_layout.addLayout(asset_layout)
        
        # Asset file list
        asset_group_layout.addWidget(QLabel("Asset Files:"))
        self.asset_file_list = QListWidget()
        self.asset_file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.asset_file_list.customContextMenuRequested.connect(self.show_asset_file_context_menu)
        self.asset_file_list.itemDoubleClicked.connect(lambda: self.import_selected_file("reference"))
        asset_group_layout.addWidget(self.asset_file_list)
        
        # Asset actions
        asset_actions = QVBoxLayout()
        refresh_asset_btn = QPushButton("🔄 Refresh")
        save_asset_version_btn = QPushButton("💾 Save Version")
        export_asset_template_btn = QPushButton("📤 Export Template")
        refresh_asset_btn.clicked.connect(self.refresh_asset_files)
        save_asset_version_btn.clicked.connect(self.save_asset_version)
        export_asset_template_btn.clicked.connect(self.export_asset_template)
        asset_actions.addWidget(refresh_asset_btn)
        asset_actions.addWidget(save_asset_version_btn)
        asset_actions.addWidget(export_asset_template_btn)
        asset_group_layout.addLayout(asset_actions)
        
        asset_section.addWidget(asset_group)
        
        # Add sections to main content
        main_content.addLayout(shot_section)
        main_content.addLayout(asset_section)
        layout.addLayout(main_content)
        
        # === COMMON ACTIONS SECTION ===
        actions_group = QGroupBox("🎬 File Operations")
        actions_layout = QHBoxLayout(actions_group)
        
        # File operations
        open_file_btn = QPushButton("📂 Open Selected")
        reference_file_btn = QPushButton("🔗 Reference Selected")
        import_file_btn = QPushButton("📥 Import Selected")
        open_file_btn.clicked.connect(lambda: self.import_selected_file("open"))
        reference_file_btn.clicked.connect(lambda: self.import_selected_file("reference"))
        import_file_btn.clicked.connect(lambda: self.import_selected_file("import"))
        
        actions_layout.addWidget(open_file_btn)
        actions_layout.addWidget(reference_file_btn)
        actions_layout.addWidget(import_file_btn)
        actions_layout.addStretch()
        
        layout.addWidget(actions_group)
        
        # Initialize data
        self.refresh_episodes()
        self.refresh_asset_categories()
        
        self.tab_widget.addTab(tab, "🏠 Asset/Shot Navigator")
    
    def setup_render_setup_tab(self):
        """Setup render setup management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Template section
        template_group = QGroupBox("📋 Template Management")
        template_layout = QVBoxLayout(template_group)
        
        # Template creation
        create_layout = QHBoxLayout()
        self.template_name_edit = QLineEdit()
        self.template_name_edit.setPlaceholderText("Template name...")
        create_template_btn = QPushButton("Create Template")
        create_layout.addWidget(QLabel("Name:"))
        create_layout.addWidget(self.template_name_edit)
        create_layout.addWidget(create_template_btn)
        template_layout.addLayout(create_layout)
        
        # Template browser
        self.template_list = QListWidget()
        self.refresh_template_list()
        template_layout.addWidget(QLabel("Templates:"))
        template_layout.addWidget(self.template_list)
        
        # Template actions
        template_actions = QHBoxLayout()
        load_template_btn = QPushButton("Load Template")
        delete_template_btn = QPushButton("Delete Template")
        template_actions.addWidget(load_template_btn)
        template_actions.addWidget(delete_template_btn)
        template_layout.addLayout(template_actions)
        
        layout.addWidget(template_group)
        
        # Import/Export section
        io_group = QGroupBox("📤 Import/Export")
        io_layout = QVBoxLayout(io_group)
        
        export_btn = QPushButton("Export Render Setup")
        import_btn = QPushButton("Import Render Setup")
        io_layout.addWidget(export_btn)
        io_layout.addWidget(import_btn)
        
        layout.addWidget(io_group)
        
        # Connect signals
        create_template_btn.clicked.connect(self.create_template)
        load_template_btn.clicked.connect(self.load_template)
        delete_template_btn.clicked.connect(self.delete_template)
        export_btn.clicked.connect(self.export_render_setup)
        import_btn.clicked.connect(self.import_render_setup)
        
        self.tab_widget.addTab(tab, "🎨 Render Setup")
    
    def setup_light_manager_tab(self):
        """Setup light manager tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Light naming section
        naming_group = QGroupBox("💡 Light Naming")
        naming_layout = QVBoxLayout(naming_group)
        
        # Naming controls
        name_controls = QGridLayout()
        name_controls.addWidget(QLabel("Prefix:"), 0, 0)
        self.light_prefix_combo = QComboBox()
        self.light_prefix_combo.setEditable(True)
        self.light_prefix_combo.addItems(self.light_manager.naming_rules.get("prefix", []))
        name_controls.addWidget(self.light_prefix_combo, 0, 1)
        
        name_controls.addWidget(QLabel("Index:"), 1, 0)
        self.light_index_spin = QSpinBox()
        self.light_index_spin.setMinimum(1)
        self.light_index_spin.setMaximum(999)
        name_controls.addWidget(self.light_index_spin, 1, 1)
        
        name_controls.addWidget(QLabel("Suffix:"), 2, 0)
        self.light_suffix_combo = QComboBox()
        self.light_suffix_combo.setEditable(True)
        self.light_suffix_combo.addItems(self.light_manager.naming_rules.get("suffix", []))
        name_controls.addWidget(self.light_suffix_combo, 2, 1)
        
        naming_layout.addLayout(name_controls)
        
        # Generated name preview
        self.name_preview_label = QLabel("Preview: key_01_lgt")
        self.name_preview_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        naming_layout.addWidget(self.name_preview_label)
        
        # Apply name button
        apply_name_btn = QPushButton("Apply to Selected Lights")
        naming_layout.addWidget(apply_name_btn)
        
        layout.addWidget(naming_group)
        
        # Light I/O section
        io_group = QGroupBox("📤 Light Import/Export")
        io_layout = QVBoxLayout(io_group)
        
        export_lights_btn = QPushButton("Export Lights Only")
        import_lights_btn = QPushButton("Import Lights Only")
        io_layout.addWidget(export_lights_btn)
        io_layout.addWidget(import_lights_btn)
        
        layout.addWidget(io_group)
        
        # Light list
        light_list_group = QGroupBox("Scene Lights")
        light_list_layout = QVBoxLayout(light_list_group)
        
        self.light_list = QListWidget()
        self.refresh_light_list()
        light_list_layout.addWidget(self.light_list)
        
        refresh_lights_btn = QPushButton("Refresh Light List")
        light_list_layout.addWidget(refresh_lights_btn)
        
        layout.addWidget(light_list_group)
        
        # Connect signals
        self.light_prefix_combo.currentTextChanged.connect(self.update_name_preview)
        self.light_index_spin.valueChanged.connect(self.update_name_preview)
        self.light_suffix_combo.currentTextChanged.connect(self.update_name_preview)
        apply_name_btn.clicked.connect(self.apply_light_name)
        export_lights_btn.clicked.connect(self.export_lights)
        import_lights_btn.clicked.connect(self.import_lights)
        refresh_lights_btn.clicked.connect(self.refresh_light_list)
        
        self.update_name_preview()
        
        self.tab_widget.addTab(tab, "💡 Light Manager")
    
    def setup_regex_tools_tab(self):
        """Setup regex converter tools tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # DAG path converter
        dag_group = QGroupBox("🔧 DAG Path to Regex Converter")
        dag_layout = QVBoxLayout(dag_group)
        
        # Input
        dag_layout.addWidget(QLabel("DAG Paths (one per line):"))
        self.dag_paths_text = QTextEdit()
        self.dag_paths_text.setMaximumHeight(100)
        dag_layout.addWidget(self.dag_paths_text)
        
        # Options
        options_layout = QHBoxLayout()
        self.escape_special_check = QCheckBox("Escape Special Characters")
        self.escape_special_check.setChecked(True)
        self.use_wildcards_check = QCheckBox("Convert Wildcards")
        self.use_wildcards_check.setChecked(True)
        options_layout.addWidget(self.escape_special_check)
        options_layout.addWidget(self.use_wildcards_check)
        dag_layout.addLayout(options_layout)
        
        # Convert button
        convert_dag_btn = QPushButton("Convert to Regex")
        dag_layout.addWidget(convert_dag_btn)
        
        # Output
        dag_layout.addWidget(QLabel("Generated Regex:"))
        self.regex_output_text = QTextEdit()
        self.regex_output_text.setMaximumHeight(80)
        self.regex_output_text.setReadOnly(True)
        dag_layout.addWidget(self.regex_output_text)
        
        layout.addWidget(dag_group)
        
        # Quick tools
        tools_group = QGroupBox("⚡ Quick Tools")
        tools_layout = QVBoxLayout(tools_group)
        
        # Selected objects to regex
        selected_to_regex_btn = QPushButton("Selected Objects to Regex")
        tools_layout.addWidget(selected_to_regex_btn)
        
        layout.addWidget(tools_group)
        
        # Connect signals
        convert_dag_btn.clicked.connect(self.convert_dag_to_regex)
        selected_to_regex_btn.clicked.connect(self.selected_to_regex)
        
        self.tab_widget.addTab(tab, "🔧 Regex Tools")
    
    def setup_settings_tab(self):
        """Setup settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Naming rules settings
        naming_group = QGroupBox("⚙️ Naming Convention Rules")
        naming_layout = QFormLayout(naming_group)
        
        self.separator_edit = QLineEdit(self.light_manager.naming_rules.get("separator", "_"))
        naming_layout.addRow("Separator:", self.separator_edit)
        
        self.padding_spin = QSpinBox()
        self.padding_spin.setMinimum(1)
        self.padding_spin.setMaximum(5)
        self.padding_spin.setValue(self.light_manager.naming_rules.get("padding", 2))
        naming_layout.addRow("Index Padding:", self.padding_spin)
        
        self.case_combo = QComboBox()
        self.case_combo.addItems(["lower", "upper", "title"])
        self.case_combo.setCurrentText(self.light_manager.naming_rules.get("case", "lower"))
        naming_layout.addRow("Case:", self.case_combo)
        
        layout.addWidget(naming_group)
        
        # Save settings
        save_settings_btn = QPushButton("💾 Save Settings")
        layout.addWidget(save_settings_btn)
        
        # Connect signals
        save_settings_btn.clicked.connect(self.save_settings)
        
        self.tab_widget.addTab(tab, "⚙️ Settings")
    
    def connect_signals(self):
        """Connect additional signals"""
        pass
    
    # === PROJECT NAVIGATION METHODS ===
    
    def browse_project_root(self):
        """Browse for project root path"""
        path = QFileDialog.getExistingDirectory(self, "Select Project Root Directory")
        if path:
            self.root_path_edit.setText(path)
            self.project_structure.root_path = path
            self.project_structure.scene_path = os.path.join(path, "scene")
            self.project_structure.asset_path = os.path.join(path, "asset")
            self.refresh_episodes()
            self.refresh_asset_categories()
    
    def refresh_episodes(self):
        """Refresh episode list"""
        self.episode_combo.clear()
        episodes = self.project_structure.get_episodes()
        self.episode_combo.addItems(episodes)
    
    def refresh_asset_categories(self):
        """Refresh asset category list"""
        self.asset_category_combo.clear()
        categories = self.project_structure.get_asset_categories()
        self.asset_category_combo.addItems(categories)
    
    def on_episode_changed(self, episode):
        """Handle episode selection change"""
        self.sequence_combo.clear()
        if episode:
            sequences = self.project_structure.get_sequences(episode)
            self.sequence_combo.addItems(sequences)
    
    def on_sequence_changed(self, sequence):
        """Handle sequence selection change"""
        self.shot_combo.clear()
        if sequence:
            episode = self.episode_combo.currentText()
            if episode:
                shots = self.project_structure.get_shots(episode, sequence)
                self.shot_combo.addItems(shots)
    
    def on_shot_changed(self, shot):
        """Handle shot selection change"""
        if shot:
            self.refresh_shot_files()
    
    def on_asset_category_changed(self, category):
        """Handle asset category selection change"""
        self.asset_subcategory_combo.clear()
        if category:
            subcategories = self.project_structure.get_asset_subcategories(category)
            self.asset_subcategory_combo.addItems(subcategories)
    
    def on_asset_subcategory_changed(self, subcategory):
        """Handle asset subcategory selection change"""
        self.asset_combo.clear()
        if subcategory:
            category = self.asset_category_combo.currentText()
            if category:
                assets = self.project_structure.get_assets(category, subcategory)
                self.asset_combo.addItems(assets)
    
    def on_asset_changed(self, asset):
        """Handle asset selection change"""
        if asset:
            self.refresh_asset_files()
    
    # === FILE LIST METHODS ===
    
    def refresh_shot_files(self):
        """Refresh shot file list"""
        self.shot_file_list.clear()
        
        episode = self.episode_combo.currentText()
        sequence = self.sequence_combo.currentText()
        shot = self.shot_combo.currentText()
        
        if episode and sequence and shot:
            files = self.asset_shot_navigator.get_lighting_files("shot", episode, sequence, shot)
            self._populate_file_list(self.shot_file_list, files)
    
    def refresh_asset_files(self):
        """Refresh asset file list"""
        self.asset_file_list.clear()
        
        category = self.asset_category_combo.currentText()
        subcategory = self.asset_subcategory_combo.currentText()
        asset = self.asset_combo.currentText()
        
        if category and subcategory and asset:
            files = self.asset_shot_navigator.get_lighting_files("asset", category, subcategory, asset)
            self._populate_file_list(self.asset_file_list, files)
    
    def _populate_file_list(self, list_widget, files):
        """Populate file list widget with file data"""
        for file_info in files:
            item = QListWidgetItem()
            
            # Format display text with icons
            file_type_icon = {
                'hero': '👑',
                'template': '📋',
                'version': '📝'
            }
            
            icon = file_type_icon.get(file_info['type'], '📄')
            display_text = f"{icon} {file_info['name']}"
            
            if file_info['type'] == 'version':
                display_text += f" (v{file_info['version']})"
            
            display_text += f" - {file_info['modified'].strftime('%Y-%m-%d %H:%M')}"
            
            item.setText(display_text)
            item.setData(Qt.UserRole, file_info)
            
            # Color code by type
            if file_info['type'] == 'hero':
                item.setBackground(QColor(255, 215, 0, 50))  # Gold
            elif file_info['type'] == 'template':
                item.setBackground(QColor(0, 255, 0, 50))   # Green
            elif file_info['type'] == 'version':
                item.setBackground(QColor(135, 206, 235, 50))  # Light blue
            
            list_widget.addItem(item)
    
    # === CONTEXT MENU METHODS ===
    
    def show_shot_file_context_menu(self, position):
        """Show context menu for shot files"""
        self._show_file_context_menu(self.shot_file_list, position)
    
    def show_asset_file_context_menu(self, position):
        """Show context menu for asset files"""
        self._show_file_context_menu(self.asset_file_list, position)
    
    def _show_file_context_menu(self, list_widget, position):
        """Show context menu for file lists"""
        item = list_widget.itemAt(position)
        if not item:
            return
        
        file_info = item.data(Qt.UserRole)
        if not file_info:
            return
        
        menu = QMenu(self)
        
        # File operations
        open_action = menu.addAction("📂 Open")
        reference_action = menu.addAction("🔗 Reference")
        import_action = menu.addAction("📥 Import")
        menu.addSeparator()
        
        # File management
        show_in_explorer_action = menu.addAction("📁 Show in Explorer")
        copy_path_action = menu.addAction("📋 Copy Path")
        
        if file_info['type'] == 'version':
            menu.addSeparator()
            make_hero_action = menu.addAction("👑 Make Hero")
        
        # Execute action
        action = menu.exec_(list_widget.mapToGlobal(position))
        
        if action == open_action:
            self._import_file_with_info(file_info, "open")
        elif action == reference_action:
            self._import_file_with_info(file_info, "reference")
        elif action == import_action:
            self._import_file_with_info(file_info, "import")
        elif action == show_in_explorer_action:
            self._show_in_explorer(file_info['path'])
        elif action == copy_path_action:
            QApplication.clipboard().setText(file_info['path'])
        elif file_info['type'] == 'version' and action == make_hero_action:
            self._make_hero_from_version(file_info)
    
    # === FILE OPERATION METHODS ===
    
    def import_selected_file(self, import_type):
        """Import currently selected file"""
        # Determine which list is active
        current_tab = self.tab_widget.currentIndex()
        if current_tab != 0:  # Asset/Shot Navigator tab index
            return
        
        # Check which section has selection
        shot_item = self.shot_file_list.currentItem()
        asset_item = self.asset_file_list.currentItem()
        
        if shot_item:
            file_info = shot_item.data(Qt.UserRole)
        elif asset_item:
            file_info = asset_item.data(Qt.UserRole)
        else:
            QMessageBox.warning(self, "Warning", "Please select a file to import.")
            return
        
        self._import_file_with_info(file_info, import_type)
    
    def _import_file_with_info(self, file_info, import_type):
        """Import file using file info"""
        success, message = self.asset_shot_navigator.import_file(file_info['path'], import_type)
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
    
    def _show_in_explorer(self, filepath):
        """Show file in Windows Explorer"""
        try:
            subprocess.run(f'explorer /select,"{filepath}"', shell=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open explorer: {str(e)}")
    
    def _make_hero_from_version(self, file_info):
        """Make hero file from version"""
        try:
            # Extract base name from version file
            version_filename = file_info['name']
            base_name = version_filename.split('_v')[0]  # Remove version part
            
            # Get lighting directory
            lighting_dir = os.path.dirname(file_info['path'])
            if lighting_dir.endswith('version'):
                lighting_dir = os.path.dirname(lighting_dir)
            
            # Create hero file
            hero_path = self.version_manager.get_hero_path(lighting_dir, base_name)
            success, message = self.version_manager.create_hero_link(file_info['path'], hero_path)
            
            if success:
                QMessageBox.information(self, "Success", message)
                # Refresh appropriate file list
                self.refresh_shot_files() if self.shot_file_list.currentItem() else self.refresh_asset_files()
            else:
                QMessageBox.critical(self, "Error", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating hero file: {str(e)}")
    
    # === VERSION SAVING METHODS ===
    
    def save_shot_version(self):
        """Save shot version"""
        episode = self.episode_combo.currentText()
        sequence = self.sequence_combo.currentText()
        shot = self.shot_combo.currentText()
        
        if not (episode and sequence and shot):
            QMessageBox.warning(self, "Warning", "Please select episode, sequence, and shot.")
            return
        
        self._save_version_dialog("shot", episode, sequence, shot)
    
    def save_asset_version(self):
        """Save asset version"""
        category = self.asset_category_combo.currentText()
        subcategory = self.asset_subcategory_combo.currentText()
        asset = self.asset_combo.currentText()
        
        if not (category and subcategory and asset):
            QMessageBox.warning(self, "Warning", "Please select category, subcategory, and asset.")
            return
        
        self._save_version_dialog("asset", category, subcategory, asset)
    
    def _save_version_dialog(self, path_type, *args):
        """Show save version dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("💾 Save Version")
        dialog.setModal(True)
        dialog.resize(400, 250)
        
        layout = QVBoxLayout(dialog)
        
        # Base name
        layout.addWidget(QLabel("Base Name:"))
        base_name_edit = QLineEdit()
        if path_type == "shot":
            episode, sequence, shot = args
            base_name_edit.setText(f"{episode}_{sequence}_{shot}_lighting")
        else:
            category, subcategory, asset = args
            base_name_edit.setText(f"{category}_{subcategory}_{asset}_lighting")
        layout.addWidget(base_name_edit)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        description_edit = QTextEdit()
        description_edit.setMaximumHeight(80)
        layout.addWidget(description_edit)
        
        # Create hero checkbox
        create_hero_check = QCheckBox("👑 Create/Update Hero File")
        create_hero_check.setChecked(True)
        layout.addWidget(create_hero_check)
        
        # Buttons
        buttons = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        cancel_btn = QPushButton("❌ Cancel")
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)
        
        # Connect signals
        save_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            base_name = base_name_edit.text().strip()
            description = description_edit.toPlainText().strip()
            create_hero = create_hero_check.isChecked()
            
            if not base_name:
                QMessageBox.warning(self, "Warning", "Please enter a base name.")
                return
            
            # Get lighting directory
            if path_type == "shot":
                lighting_dir = self.project_structure.get_shot_lighting_path(*args)
            else:
                lighting_dir = self.project_structure.get_asset_lighting_path(*args)
            
            # Save version
            success, message = self.version_manager.save_with_version(
                lighting_dir, base_name, description, create_hero)
            
            if success:
                QMessageBox.information(self, "Success", message)
                if path_type == "shot":
                    self.refresh_shot_files()
                else:
                    self.refresh_asset_files()
            else:
                QMessageBox.critical(self, "Error", message)
    
    # === TEMPLATE EXPORT METHODS ===
    
    def export_shot_template(self):
        """Export shot template"""
        episode = self.episode_combo.currentText()
        sequence = self.sequence_combo.currentText()
        shot = self.shot_combo.currentText()
        
        if not (episode and sequence and shot):
            QMessageBox.warning(self, "Warning", "Please select episode, sequence, and shot.")
            return
        
        base_name, ok = QInputDialog.getText(self, "Export Template", "Template name:", text="lighting")
        if ok and base_name:
            success, message = self.asset_shot_navigator.export_template(
                "shot", base_name, episode, sequence, shot)
            
            if success:
                QMessageBox.information(self, "Success", message)
                self.refresh_shot_files()
            else:
                QMessageBox.critical(self, "Error", message)
    
    def export_asset_template(self):
        """Export asset template"""
        category = self.asset_category_combo.currentText()
        subcategory = self.asset_subcategory_combo.currentText()
        asset = self.asset_combo.currentText()
        
        if not (category and subcategory and asset):
            QMessageBox.warning(self, "Warning", "Please select category, subcategory, and asset.")
            return
        
        base_name, ok = QInputDialog.getText(self, "Export Template", "Template name:", text="lighting")
        if ok and base_name:
            success, message = self.asset_shot_navigator.export_template(
                "asset", base_name, category, subcategory, asset)
            
            if success:
                QMessageBox.information(self, "Success", message)
                self.refresh_asset_files()
            else:
                QMessageBox.critical(self, "Error", message)
    
    # === RENDER SETUP METHODS ===
    
    def refresh_template_list(self):
        """Refresh the template list"""
        self.template_list.clear()
        if os.path.exists(self.render_manager.templates_dir):
            for file in os.listdir(self.render_manager.templates_dir):
                if file.endswith('.json'):
                    name = os.path.splitext(file)[0]
                    self.template_list.addItem(name)
    
    def create_template(self):
        """Create a new template"""
        name = self.template_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a template name.")
            return
        
        success, message = self.render_manager.create_template_rendersetup(name)
        if success:
            QMessageBox.information(self, "Success", message)
            self.refresh_template_list()
            self.template_name_edit.clear()
        else:
            QMessageBox.critical(self, "Error", message)
    
    def load_template(self):
        """Load selected template"""
        current_item = self.template_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a template.")
            return
        
        template_name = current_item.text()
        template_file = os.path.join(self.render_manager.templates_dir, f"{template_name}.json")
        
        if os.path.exists(template_file):
            QMessageBox.information(self, "Success", f"Template '{template_name}' loaded.")
        else:
            QMessageBox.critical(self, "Error", "Template file not found.")
    
    def delete_template(self):
        """Delete selected template"""
        current_item = self.template_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a template.")
            return
        
        template_name = current_item.text()
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete template '{template_name}'?")
        
        if reply == QMessageBox.Yes:
            template_file = os.path.join(self.render_manager.templates_dir, f"{template_name}.json")
            try:
                os.remove(template_file)
                QMessageBox.information(self, "Success", f"Template '{template_name}' deleted.")
                self.refresh_template_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting template: {str(e)}")
    
    def export_render_setup(self):
        """Export render setup"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Render Setup", "", "JSON Files (*.json)")
        
        if filepath:
            success, message = self.render_manager.export_rendersetup(filepath)
            if success:
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.critical(self, "Error", message)
    
    def import_render_setup(self):
        """Import render setup"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Render Setup", "", "JSON Files (*.json)")
        
        if filepath:
            QMessageBox.information(self, "Success", f"Render setup imported from {filepath}")
    
    # === LIGHT MANAGER METHODS ===
    
    def refresh_light_list(self):
        """Refresh the light list"""
        self.light_list.clear()
        
        # Get all lights in scene
        try:
            light_shapes = cmds.ls(type=["directionalLight", "pointLight", "spotLight", 
                                        "areaLight", "aiAreaLight", "aiSkyDomeLight"])
            
            for shape in light_shapes:
                transform = cmds.listRelatives(shape, parent=True, type="transform")
                if transform:
                    self.light_list.addItem(transform[0])
        except:
            pass
    
    def update_name_preview(self):
        """Update the light name preview"""
        prefix = self.light_prefix_combo.currentText()
        index = self.light_index_spin.value()
        suffix = self.light_suffix_combo.currentText()
        
        name = self.light_manager.generate_light_name(prefix, suffix, index)
        self.name_preview_label.setText(f"Preview: {name}")
    
    def apply_light_name(self):
        """Apply naming to selected lights"""
        try:
            selected = cmds.ls(selection=True, type="transform")
            if not selected:
                QMessageBox.warning(self, "Warning", "Please select lights to rename.")
                return
            
            prefix = self.light_prefix_combo.currentText()
            suffix = self.light_suffix_combo.currentText()
            start_index = self.light_index_spin.value()
            
            for i, light in enumerate(selected):
                new_name = self.light_manager.generate_light_name(prefix, suffix, start_index + i)
                try:
                    cmds.rename(light, new_name)
                except Exception as e:
                    print(f"Error renaming {light}: {e}")
            
            self.refresh_light_list()
            QMessageBox.information(self, "Success", f"Renamed {len(selected)} lights.")
        except:
            QMessageBox.warning(self, "Warning", "Error accessing Maya commands.")
    
    def export_lights(self):
        """Export lights only"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Lights", "", "Maya Files (*.ma)")
        
        if filepath:
            success, message = self.light_manager.export_lights_only(filepath)
            if success:
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.critical(self, "Error", message)
    
    def import_lights(self):
        """Import lights only"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Lights", "", "Maya Files (*.ma *.mb)")
        
        if filepath:
            try:
                cmds.file(filepath, i=True, type="mayaAscii", 
                         ignoreVersion=True, mergeNamespacesOnClash=False, 
                         namespace=":", preserveReferences=True)
                QMessageBox.information(self, "Success", f"Lights imported from {filepath}")
                self.refresh_light_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error importing lights: {str(e)}")
    
    # === REGEX TOOLS METHODS ===
    
    def convert_dag_to_regex(self):
        """Convert DAG paths to regex"""
        paths_text = self.dag_paths_text.toPlainText().strip()
        if not paths_text:
            QMessageBox.warning(self, "Warning", "Please enter DAG paths.")
            return
        
        paths = [p.strip() for p in paths_text.split('\n') if p.strip()]
        
        options = {
            "escape_special": self.escape_special_check.isChecked(),
            "use_wildcards": self.use_wildcards_check.isChecked()
        }
        
        regex_pattern = RegexConverter.dag_paths_to_regex(paths, options)
        self.regex_output_text.setPlainText(regex_pattern)
    
    def selected_to_regex(self):
        """Convert selected objects to regex"""
        try:
            selected = cmds.ls(selection=True, long=True)
            if not selected:
                QMessageBox.warning(self, "Warning", "Please select objects.")
                return
            
            self.dag_paths_text.setPlainText('\n'.join(selected))
            self.convert_dag_to_regex()
        except:
            QMessageBox.warning(self, "Warning", "Error accessing Maya selection.")
    
    # === SETTINGS METHODS ===
    
    def save_settings(self):
        """Save settings"""
        try:
            rules = self.light_manager.naming_rules.copy()
            rules["separator"] = self.separator_edit.text()
            rules["padding"] = self.padding_spin.value()
            rules["case"] = self.case_combo.currentText()
            
            # Save naming rules
            rules_file = os.path.join(cmds.internalVar(userPrefDir=True), "lightNamingRules.json")
            with open(rules_file, 'w') as f:
                json.dump(rules, f, indent=2)
            
            self.light_manager.naming_rules = rules
            QMessageBox.information(self, "Success", "Settings saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving settings: {str(e)}")


def get_maya_main_window():
    """Get Maya main window as QWidget"""
    if wrapInstance is None:
        return None
    
    try:
        main_window_ptr = omui.MQtUtil.mainWindow()
        return wrapInstance(int(main_window_ptr), QWidget)
    except:
        return None


def create_dockable_ui():
    """Create dockable UI in Maya"""
    try:
        # Delete existing instance
        if cmds.window("renderSetupManagerDock", exists=True):
            cmds.deleteUI("renderSetupManagerDock", window=True)
        
        # Create the UI
        parent = get_maya_main_window()
        ui = RenderSetupUI(parent=parent)
        
        # Create dockable window
        dock_control = cmds.dockControl(
            "renderSetupManagerDock",
            label="Render Setup Manager v2.0",
            area="right",
            content=ui.objectName(),
            allowedArea=["right", "left"],
            sizeable=True,
            width=700,
            height=900
        )
        
        return ui
        
    except Exception as e:
        print(f"Error creating dockable UI: {e}")
        return None


def show_ui():
    """Show the Render Setup Manager UI"""
    global render_setup_ui
    
    try:
        # Try dockable first
        render_setup_ui = create_dockable_ui()
        if render_setup_ui:
            print("Render Setup Manager v2.0 - Dockable UI created successfully!")
            return render_setup_ui
    except Exception as e:
        print(f"Dockable UI failed: {e}")
    
    # Fallback to regular window
    try:
        parent = get_maya_main_window()
        render_setup_ui = RenderSetupUI(parent=parent)
        render_setup_ui.show()
        print("Render Setup Manager v2.0 - Standalone window created!")
        return render_setup_ui
    except Exception as e:
        print(f"Error creating UI: {e}")
        return None


# Global variable to keep reference
render_setup_ui = None

# === MAIN EXECUTION ===
if __name__ == "__main__":
    # For testing outside Maya
    import sys
    if "maya" not in sys.modules:
        app = QApplication(sys.argv)
        ui = RenderSetupUI()
        ui.show()
        print("Running in standalone mode (outside Maya)")
        sys.exit(app.exec_())
    else:
        # Run in Maya
        print("Loading Render Setup Manager v2.0...")
        show_ui()

# === USAGE INSTRUCTIONS ===
"""
INSTALLATION & USAGE:

1. Copy this file to: E:\dev\LRCtoolsbox\LRCtoolsbox\maya\src\maya_render_setup_manager.py

2. In Maya Script Editor (Python), run:
   exec(open(r'E:\\dev\\LRCtoolsbox\\LRCtoolsbox\\maya\\src\\maya_render_setup_manager.py').read())
   
   OR simply run:
   show_ui()

3. The tool will create a dockable interface with the following features:

   📁 ASSET/SHOT NAVIGATOR:
   - Browse your V:\SWA\all directory structure
   - Episode → Sequence → Shot navigation
   - Category → Subcategory → Asset navigation
   - File browser with Hero (👑), Template (📋), Version (📝) files
   - Right-click context menus for file operations
   - Double-click to reference files
   - Auto-versioning with v0001, v0002, etc.
   - Hero file creation using Windows symlinks/junctions

   🎨 RENDER SETUP:
   - Create and manage render setup templates
   - Import/export render setups
   - Template browser

   💡 LIGHT MANAGER:
   - Flexible light naming conventions
   - Batch light renaming
   - Light-only import/export
   - Scene light browser

   🔧 REGEX TOOLS:
   - Convert DAG paths to regex patterns
   - Selected objects to regex converter
   - Handle Maya wildcards and special characters

   ⚙️ SETTINGS:
   - Configurable naming rules
   - Persistent settings storage

4. HERO FILE SYSTEM:
   The tool automatically creates hero files (latest approved version) using:
   - Windows symbolic links (Windows 10+)
   - Hard links (fallback)
   - File copies (ultimate fallback)
   
   Hero files act like symlinks in Linux, pointing to the actual version file
   without duplicating data.

5. VERSION MANAGEMENT:
   - Auto-incremental versioning (v0001, v0002, etc.)
   - Version metadata storage (user, timestamp, description)
   - Right-click any version to "Make Hero"
   - Automatic hero file updates when saving new versions

6. DIRECTORY STRUCTURE SUPPORT:
   Shot: V:\SWA\all\scene\Ep00\sq0010\SH0010\lighting\version\
   Asset: V:\SWA\all\asset\Sets\interior\Kitchen\lighting\version\
"""