"""
Reference to Instance Converter Tool for Maya (v2.1)
Converts duplicate references under locators to instances for optimization.

Supports naming convention:
SET_{setName}_{identifier}:{assetName}_{identifier}_{kind}:{assetName}_{identifier}_{identifier}_{kind}

Example hierarchy:
SETS_CentralBusinessDistrictAExt_001:CBDAExtAreaLowA_Grp
├── SETS_CentralBusinessDistrictAExt_001:CBDAExtAreaLowA_001_Loc
│   └── SETS_CentralBusinessDistrictAExt_001:CBDAExtAreaLowA_001:Geo_Grp
├── SETS_CentralBusinessDistrictAExt_001:CBDAExtAreaLowA_002_Loc
│   └── SETS_CentralBusinessDistrictAExt_001:CBDAExtAreaLowA_002:Geo_Grp
...

Duplicate Detection:
- Groups references by their Alembic file path (normalized, without copy numbers)
- Assets referencing the same .abc file are considered duplicates

Instance Conversion:
- Keeps first instance as "master" (retains original reference)
- Converts other instances to Maya instances (shares geometry)
- Shaders are preserved since they're shared across all duplicates

Author: Pipeline Tools
Version: 2.1.0
"""

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from collections import defaultdict
import re

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance


def get_maya_main_window():
    """Get Maya's main window as a Qt object."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


def _reassign_shaders_to_instance(instance_transform, master_transform):
    """
    Re-assign correct shaders to instance by copying master's shader assignments.

    When Maya creates an instance with cmds.instance(), it automatically connects
    the instance to initialShadingGroup (lambert1). This causes the instance to have
    TWO shader connections:
    1. instObjGroups[0] -> initialShadingGroup (lambert1) - WRONG
    2. instObjGroups[1] -> Correct shading group - CORRECT

    Simply disconnecting from initialShadingGroup causes the viewport to display green
    (indicating no shader assigned).

    The correct solution is to RE-ASSIGN the correct shaders to the instance using
    cmds.sets(shape, e=True, forceElement=shadingGroup). This will:
    - Remove the connection to initialShadingGroup
    - Properly connect to the correct shading group
    - Ensure viewport displays correctly (not green)
    - Ensure rendering uses the correct shader

    Args:
        instance_transform: The transform node of the instance
        master_transform: The transform node of the master geometry
    """
    try:
        # Get all shape nodes under the master
        master_shapes = cmds.listRelatives(master_transform, allDescendents=True,
                                          type="mesh", fullPath=True) or []

        if not master_shapes:
            return

        # Get all shape nodes under the instance (same shapes, different instObjGroups)
        instance_shapes = cmds.listRelatives(instance_transform, allDescendents=True,
                                            type="mesh", fullPath=True) or []

        if not instance_shapes:
            return

        # For each master shape, find its shading groups and re-assign to instance shape
        for master_shape in master_shapes:
            # Find all shading groups connected to this master shape
            # Check instObjGroups connections
            shading_groups = cmds.listConnections(
                "{}.instObjGroups".format(master_shape),
                type="shadingEngine",
                source=False,
                destination=True
            ) or []

            # Remove duplicates and filter out initialShadingGroup
            shading_groups = list(set(shading_groups))
            shading_groups = [sg for sg in shading_groups if sg != "initialShadingGroup"]

            if not shading_groups:
                continue

            # Find corresponding instance shape (same shape node, different transform path)
            # Get the shape name without the transform path
            master_shape_name = master_shape.split("|")[-1]

            # Find matching instance shape
            instance_shape = None
            for inst_shp in instance_shapes:
                inst_shape_name = inst_shp.split("|")[-1]
                if inst_shape_name == master_shape_name:
                    instance_shape = inst_shp
                    break

            if not instance_shape:
                continue

            # Re-assign each shading group to the instance shape
            # This will automatically disconnect from initialShadingGroup
            for sg in shading_groups:
                try:
                    cmds.sets(instance_shape, e=True, forceElement=sg)
                except Exception as e:
                    # Silently fail - may already be assigned
                    pass

    except Exception as e:
        # Silently fail - shader assignment should still work
        pass


def normalize_ref_file(ref_file):
    """
    Normalize reference file path for comparison.
    Strips copy numbers like {1}, {2} from path and normalizes slashes.

    Input:  "V:/path/to/asset.abc{2}" or "V:\\path\\to\\asset.abc"
    Output: "V:/path/to/asset.abc"
    """
    # Remove copy number suffix {N}
    normalized = re.sub(r'\{\d+\}$', '', ref_file)
    # Normalize path separators
    normalized = normalized.replace('\\', '/')
    return normalized


class LocatorAssetInfo:
    """Information about an asset found under a locator."""
    def __init__(self, locator, geo_group, reference_node, namespace, ref_file):
        self.locator = locator          # Short name for display
        self.geo_group = geo_group      # Short name for display
        self.reference_node = reference_node
        self.namespace = namespace
        self.ref_file = ref_file
        self.world_matrix = None
        # Full paths for Maya operations (set by HierarchyAnalyzer)
        self.locator_path = None
        self.geo_group_path = None

    def get_locator_path(self):
        """Get the full path to locator, fallback to short name."""
        return self.locator_path or self.locator

    def get_geo_group_path(self):
        """Get the full path to geo group, fallback to short name."""
        return self.geo_group_path or self.geo_group

    def capture_transform(self):
        """Capture the world transform of the geo group."""
        geo_path = self.get_geo_group_path()
        if cmds.objExists(geo_path):
            self.world_matrix = cmds.xform(geo_path, query=True, worldSpace=True, matrix=True)
            return True
        return False


class DuplicateReferenceGroup:
    """Group of duplicate references of the same asset file."""
    def __init__(self, ref_file, asset_name):
        self.ref_file = ref_file
        self.asset_name = asset_name
        self.instances = []  # List of LocatorAssetInfo
        
    def add_instance(self, info):
        self.instances.append(info)
        
    @property
    def count(self):
        return len(self.instances)
    
    @property
    def is_duplicate(self):
        return self.count > 1
    
    @property
    def master(self):
        """Return the first instance as master."""
        return self.instances[0] if self.instances else None
    
    @property
    def slaves(self):
        """Return all instances except the master."""
        return self.instances[1:] if len(self.instances) > 1 else []


class HierarchyAnalyzer:
    """
    Analyzes Maya scene hierarchy to find duplicate references.

    Pattern recognition:
    - {namespace}:{name}_Grp -> Group containing locators
    - {namespace}:{name}_{num}_Loc -> Locator for asset placement
    - {namespace}:{assetNS}:Geo_Grp -> Referenced geometry under locator

    Duplicate Detection:
    - Groups by normalized alembic file path
    - Same .abc file = duplicate references
    """

    def __init__(self):
        self.duplicate_groups = []  # List of DuplicateReferenceGroup
        self.all_assets = []  # All LocatorAssetInfo found
        self.parent_groups = {}  # parent_grp -> list of LocatorAssetInfo

    def analyze(self, root_group, progress_callback=None):
        """
        Analyze hierarchy starting from root_group.
        Returns list of DuplicateReferenceGroup objects.
        """
        self.duplicate_groups.clear()
        self.all_assets.clear()
        self.parent_groups.clear()

        if not cmds.objExists(root_group):
            cmds.warning(f"Root group '{root_group}' does not exist.")
            return []

        print(f"[Analyzer] Starting analysis from: {root_group}")

        # Find all potential asset groups (ending with _Grp)
        self._walk_hierarchy(root_group, progress_callback)

        print(f"[Analyzer] Found {len(self.all_assets)} referenced assets under locators")

        # Group by reference file to find duplicates
        self._group_by_reference()

        print(f"[Analyzer] Created {len(self.duplicate_groups)} reference groups")

        return self.duplicate_groups

    def _walk_hierarchy(self, node, progress_callback=None, depth=0):
        """Recursively walk hierarchy to find locators with referenced assets."""
        if depth > 100:  # Safety limit
            return

        if not cmds.objExists(node):
            return

        # Get children - use fullPath to avoid ambiguity with namespaced nodes
        children = cmds.listRelatives(node, children=True, fullPath=True, type='transform') or []

        for child_path in children:
            short_name = child_path.split('|')[-1]

            # Check if this is a locator (ends with _Loc or contains _Loc)
            if short_name.endswith('_Loc') or '_Loc' in short_name:
                self._process_locator(child_path, node)

            # Always recurse to find nested structures
            self._walk_hierarchy(child_path, progress_callback, depth + 1)

    def _process_locator(self, locator_path, parent_group):
        """Process a locator to find referenced assets underneath."""
        if not cmds.objExists(locator_path):
            return

        locator_short = locator_path.split('|')[-1]

        # Get children of locator (use fullPath)
        children = cmds.listRelatives(locator_path, children=True, fullPath=True, type='transform') or []

        for child_path in children:
            child_short = child_path.split('|')[-1]

            # Check if child is referenced
            ref_info = self._get_reference_info(child_path)
            if ref_info:
                namespace, ref_node, ref_file = ref_info

                asset_info = LocatorAssetInfo(
                    locator=locator_short,  # Store short name for display
                    geo_group=child_short,   # Store short name for display
                    reference_node=ref_node,
                    namespace=namespace,
                    ref_file=ref_file
                )
                # Store full paths for operations
                asset_info.locator_path = locator_path
                asset_info.geo_group_path = child_path

                self.all_assets.append(asset_info)

                # Track by parent group
                parent_short = parent_group.split('|')[-1] if '|' in parent_group else parent_group
                if parent_short not in self.parent_groups:
                    self.parent_groups[parent_short] = []
                self.parent_groups[parent_short].append(asset_info)

                print(f"[Analyzer] Found: {namespace} under {locator_short}")

    def _get_reference_info(self, node):
        """
        Get reference information for a node.
        Returns (namespace, reference_node, reference_file) or None.
        """
        try:
            if cmds.referenceQuery(node, isNodeReferenced=True):
                ref_node = cmds.referenceQuery(node, referenceNode=True)
                # Use withoutCopyNumber to get clean file path
                ref_file = cmds.referenceQuery(ref_node, filename=True, withoutCopyNumber=True)
                namespace = cmds.referenceQuery(ref_node, namespace=True).lstrip(':')
                return (namespace, ref_node, ref_file)
        except Exception as e:
            pass
        return None

    def _group_by_reference(self):
        """Group assets by their normalized reference file to find duplicates."""
        file_groups = defaultdict(list)

        for asset in self.all_assets:
            # Normalize file path for comparison
            normalized_path = normalize_ref_file(asset.ref_file)
            file_groups[normalized_path].append(asset)

        # Create DuplicateReferenceGroup for each file
        for ref_file, assets in file_groups.items():
            # Extract asset name from file path (e.g., CBDAExtAreaLowA_geo.abc -> CBDAExtAreaLowA_geo)
            filename = ref_file.rsplit('/', 1)[-1]  # Get filename
            asset_name = filename.rsplit('.', 1)[0]  # Remove extension

            group = DuplicateReferenceGroup(ref_file, asset_name)
            for asset in assets:
                group.add_instance(asset)

            self.duplicate_groups.append(group)

            if group.is_duplicate:
                print(f"[Analyzer] DUPLICATE: {asset_name} ({group.count} refs)")

        # Sort by count (duplicates first)
        self.duplicate_groups.sort(key=lambda x: x.count, reverse=True)


class InstanceConverter:
    """Converts duplicate references to instances."""

    def __init__(self):
        self.log_messages = []

    def log(self, message):
        """Add a log message."""
        self.log_messages.append(message)
        print(message)

    def clear_log(self):
        """Clear log messages."""
        self.log_messages.clear()

    def convert_group(self, duplicate_group, dry_run=False):
        """
        Convert a DuplicateReferenceGroup to instances.

        Args:
            duplicate_group: DuplicateReferenceGroup to convert
            dry_run: If True, only log what would happen

        Returns:
            bool: True if successful
        """
        if not duplicate_group.is_duplicate:
            self.log(f"Skipping {duplicate_group.asset_name} - only one reference")
            return False

        self.log(f"\n{'='*60}")
        self.log(f"Converting: {duplicate_group.asset_name}")
        self.log(f"Reference file: {duplicate_group.ref_file}")
        self.log(f"Total instances: {duplicate_group.count}")
        self.log(f"{'='*60}")

        master = duplicate_group.master
        slaves = duplicate_group.slaves

        master_geo_path = master.get_geo_group_path()

        self.log(f"\nMaster (will keep): {master.namespace}")
        self.log(f"  Locator: {master.locator}")
        self.log(f"  Geo Group: {master.geo_group}")

        if not cmds.objExists(master_geo_path):
            self.log(f"ERROR: Master geo group does not exist: {master_geo_path}")
            return False

        # Process each slave
        success_count = 0
        for i, slave in enumerate(slaves, 1):
            self.log(f"\n--- Slave {i}/{len(slaves)}: {slave.namespace} ---")

            if self._convert_slave_to_instance(slave, master, dry_run):
                success_count += 1
            else:
                self.log(f"WARNING: Failed to convert slave {slave.namespace}")

        self.log(f"\n✓ Converted {success_count}/{len(slaves)} slaves to instances")
        return True

    def _convert_slave_to_instance(self, slave, master, dry_run=False):
        """
        Convert a single slave reference to an instance of the master.

        Steps:
        1. Capture transform of slave geo
        2. Create instance of master geo
        3. Apply transform to instance
        4. Parent instance to slave's locator
        5. Remove slave reference
        """
        slave_locator_path = slave.get_locator_path()
        slave_geo_path = slave.get_geo_group_path()
        master_geo_path = master.get_geo_group_path()

        self.log(f"  Locator: {slave.locator}")
        self.log(f"  Geo Group: {slave.geo_group}")

        # Validate using full paths
        if not cmds.objExists(slave_locator_path):
            self.log(f"  ERROR: Locator does not exist: {slave_locator_path}")
            return False

        if not cmds.objExists(slave_geo_path):
            self.log(f"  ERROR: Geo group does not exist: {slave_geo_path}")
            return False

        if not cmds.objExists(master_geo_path):
            self.log(f"  ERROR: Master geo group does not exist: {master_geo_path}")
            return False

        if dry_run:
            self.log(f"  [DRY RUN] Would create instance and remove reference")
            return True

        try:
            # 1. Capture world transform from slave geo
            world_matrix = cmds.xform(slave_geo_path, query=True, worldSpace=True, matrix=True)
            self.log(f"  ✓ Captured transform")

            # 2. Create instance of master geo
            # Use namespace-safe name for instance
            instance_name = slave.namespace.replace(':', '_') + "_instance"
            instance = cmds.instance(master_geo_path, name=instance_name)[0]
            self.log(f"  ✓ Created instance: {instance}")

            # 3. Re-assign correct shaders to instance
            # Maya automatically connects new instances to initialShadingGroup (lambert1)
            # We need to re-assign the correct shaders from the master to the instance
            _reassign_shaders_to_instance(instance, master_geo_path)
            self.log(f"  ✓ Re-assigned shaders from master")

            # 4. Apply transform to instance
            cmds.xform(instance, worldSpace=True, matrix=world_matrix)
            self.log(f"  ✓ Applied transform")

            # 5. Parent instance to slave's locator
            cmds.parent(instance, slave_locator_path)
            self.log(f"  ✓ Parented to locator")

            # 6. Remove the slave reference using referenceNode (safer than file path)
            cmds.file(removeReference=True, referenceNode=slave.reference_node)
            self.log(f"  ✓ Removed reference: {slave.namespace}")
            
            return True
            
        except Exception as e:
            self.log(f"  ERROR: {str(e)}")
            return False
    
    def convert_multiple_groups(self, groups, progress_callback=None, dry_run=False):
        """
        Convert multiple DuplicateReferenceGroups.
        
        Args:
            groups: List of DuplicateReferenceGroup
            progress_callback: Function(current, total, message)
            dry_run: If True, only log what would happen
        """
        self.clear_log()
        
        # Filter to only duplicates
        duplicate_groups = [g for g in groups if g.is_duplicate]
        
        if not duplicate_groups:
            self.log("No duplicate references to convert.")
            return
        
        total = len(duplicate_groups)
        self.log(f"Starting conversion of {total} duplicate reference groups...")
        
        for i, group in enumerate(duplicate_groups, 1):
            if progress_callback:
                progress_callback(i, total, f"Converting: {group.asset_name}")
            
            self.convert_group(group, dry_run)
        
        self.log(f"\n{'='*60}")
        self.log(f"Conversion complete! Processed {total} groups.")
        self.log(f"{'='*60}")


# ============================================================================
# UI Components
# ============================================================================

class AssetTreeWidget(QtWidgets.QTreeWidget):
    """Custom tree widget for displaying assets."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setHeaderLabels([
            "Asset / Reference",
            "Namespace", 
            "Locator",
            "Status"
        ])
        
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setRootIsDecorated(True)
        
        # Set column widths
        header = self.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        
        self.setColumnWidth(0, 300)
        
    def populate(self, duplicate_groups):
        """Populate tree with DuplicateReferenceGroup objects."""
        self.clear()
        
        duplicate_count = 0
        single_count = 0
        
        for group in duplicate_groups:
            # Create top-level item for asset file
            group_item = QtWidgets.QTreeWidgetItem()
            group_item.setData(0, QtCore.Qt.UserRole, group)
            
            # Icon based on duplicate status
            if group.is_duplicate:
                icon = "⚠️"
                color = QtGui.QColor("#ff9900")
                status = f"DUPLICATE ({group.count} refs)"
                group_item.setCheckState(0, QtCore.Qt.Unchecked)
                duplicate_count += group.count
            else:
                icon = "✓"
                color = QtGui.QColor("#666666")
                status = "Single reference"
                single_count += 1
            
            group_item.setText(0, f"{icon} {group.asset_name}")
            group_item.setForeground(0, QtGui.QBrush(color))
            group_item.setText(3, status)
            
            # Add child items for each instance
            for i, instance in enumerate(group.instances):
                instance_item = QtWidgets.QTreeWidgetItem()
                instance_item.setData(0, QtCore.Qt.UserRole, instance)
                
                # Mark master vs slave
                if i == 0 and group.is_duplicate:
                    prefix = "👑 Master"
                    instance_color = QtGui.QColor("#00aa00")
                elif group.is_duplicate:
                    prefix = "📋 Slave"
                    instance_color = QtGui.QColor("#ffaa00")
                else:
                    prefix = "📄"
                    instance_color = QtGui.QColor("#888888")
                
                instance_item.setText(0, f"  {prefix}")
                instance_item.setText(1, instance.namespace)
                instance_item.setText(2, instance.locator.split(':')[-1] if ':' in instance.locator else instance.locator)
                instance_item.setForeground(0, QtGui.QBrush(instance_color))
                
                group_item.addChild(instance_item)
            
            self.addTopLevelItem(group_item)
            
            # Auto-expand duplicates
            if group.is_duplicate:
                group_item.setExpanded(True)
        
        return duplicate_count, single_count
    
    def get_checked_groups(self):
        """Return list of checked DuplicateReferenceGroup objects."""
        checked = []
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.checkState(0) == QtCore.Qt.Checked:
                group = item.data(0, QtCore.Qt.UserRole)
                if group:
                    checked.append(group)
        return checked
    
    def select_all_duplicates(self):
        """Check all duplicate groups."""
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            group = item.data(0, QtCore.Qt.UserRole)
            if group and group.is_duplicate:
                item.setCheckState(0, QtCore.Qt.Checked)
    
    def select_none(self):
        """Uncheck all groups."""
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            try:
                item.setCheckState(0, QtCore.Qt.Unchecked)
            except:
                pass


class ReferenceToInstanceUI(QtWidgets.QDialog):
    """Main UI for Reference to Instance Converter."""
    
    WINDOW_TITLE = "Reference to Instance Converter v2.0"
    
    def __init__(self, parent=get_maya_main_window()):
        super().__init__(parent)
        
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(800, 700)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        self.analyzer = HierarchyAnalyzer()
        self.converter = InstanceConverter()
        self.duplicate_groups = []
        
        self._create_ui()
        self._create_connections()
        
    def _create_ui(self):
        """Build the UI."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        
        # === Header ===
        header_label = QtWidgets.QLabel(
            "Convert duplicate references to instances for better scene performance."
        )
        header_label.setStyleSheet("color: #888; font-style: italic;")
        main_layout.addWidget(header_label)
        
        # === Step 1: Root Selection ===
        step1 = self._create_step_group("Step 1: Select Root Group", "1")
        step1_layout = step1.layout()
        
        root_layout = QtWidgets.QHBoxLayout()
        
        self.root_edit = QtWidgets.QLineEdit()
        self.root_edit.setPlaceholderText("Select root group (e.g., Sets_Grp) in Maya Outliner...")
        self.root_edit.setReadOnly(True)
        
        self.get_selected_btn = QtWidgets.QPushButton("◀ Get Selected")
        self.get_selected_btn.setFixedWidth(120)
        self.get_selected_btn.setToolTip("Use currently selected object in Maya as root")
        
        root_layout.addWidget(self.root_edit)
        root_layout.addWidget(self.get_selected_btn)
        step1_layout.addLayout(root_layout)
        
        main_layout.addWidget(step1)
        
        # === Step 2: Analyze ===
        step2 = self._create_step_group("Step 2: Analyze Hierarchy", "2")
        step2_layout = step2.layout()
        
        self.analyze_btn = QtWidgets.QPushButton("🔍 Analyze References")
        self.analyze_btn.setMinimumHeight(36)
        self.analyze_btn.setEnabled(False)
        step2_layout.addWidget(self.analyze_btn)
        
        main_layout.addWidget(step2)
        
        # === Step 3: Review Assets ===
        step3 = self._create_step_group("Step 3: Review & Select Assets", "3")
        step3_layout = step3.layout()
        
        # Stats bar
        stats_layout = QtWidgets.QHBoxLayout()
        self.stats_label = QtWidgets.QLabel("No assets analyzed yet")
        self.stats_label.setStyleSheet("color: #888;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        step3_layout.addLayout(stats_layout)
        
        # Asset tree
        self.asset_tree = AssetTreeWidget()
        self.asset_tree.setMinimumHeight(250)
        step3_layout.addWidget(self.asset_tree)
        
        # Selection buttons
        sel_layout = QtWidgets.QHBoxLayout()
        self.select_all_btn = QtWidgets.QPushButton("Select All Duplicates")
        self.select_none_btn = QtWidgets.QPushButton("Select None")
        self.preview_btn = QtWidgets.QPushButton("Preview in Maya")
        
        sel_layout.addWidget(self.select_all_btn)
        sel_layout.addWidget(self.select_none_btn)
        sel_layout.addStretch()
        sel_layout.addWidget(self.preview_btn)
        step3_layout.addLayout(sel_layout)
        
        main_layout.addWidget(step3)
        
        # === Step 4: Execute ===
        step4 = self._create_step_group("Step 4: Convert to Instances", "4")
        step4_layout = step4.layout()
        
        # Progress
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        step4_layout.addWidget(self.progress_bar)
        
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("color: #888;")
        step4_layout.addWidget(self.status_label)
        
        # Execute buttons
        exec_layout = QtWidgets.QHBoxLayout()
        
        self.dry_run_btn = QtWidgets.QPushButton("🔬 Dry Run (Preview)")
        self.dry_run_btn.setMinimumHeight(40)
        self.dry_run_btn.setToolTip("Preview what would happen without making changes")
        
        self.convert_btn = QtWidgets.QPushButton("🚀 Convert Selected")
        self.convert_btn.setMinimumHeight(40)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5a2d;
                color: white;
                font-weight: bold;
                border: 1px solid #3d7a3d;
            }
            QPushButton:hover {
                background-color: #3d7a3d;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
        """)
        
        exec_layout.addWidget(self.dry_run_btn)
        exec_layout.addWidget(self.convert_btn)
        step4_layout.addLayout(exec_layout)
        
        main_layout.addWidget(step4)
        
        # === Log Output ===
        log_group = QtWidgets.QGroupBox("Log Output")
        log_layout = QtWidgets.QVBoxLayout(log_group)
        
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                background-color: #1a1a1a;
                color: #cccccc;
            }
        """)
        
        log_btn_layout = QtWidgets.QHBoxLayout()
        self.clear_log_btn = QtWidgets.QPushButton("Clear Log")
        log_btn_layout.addStretch()
        log_btn_layout.addWidget(self.clear_log_btn)
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(log_btn_layout)
        
        main_layout.addWidget(log_group)
        
    def _create_step_group(self, title, number):
        """Create a styled group box for a step."""
        group = QtWidgets.QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        layout = QtWidgets.QVBoxLayout(group)
        return group
        
    def _create_connections(self):
        """Connect signals to slots."""
        self.get_selected_btn.clicked.connect(self._on_get_selected)
        self.root_edit.textChanged.connect(self._on_root_changed)
        self.analyze_btn.clicked.connect(self._on_analyze)
        self.select_all_btn.clicked.connect(self.asset_tree.select_all_duplicates)
        self.select_none_btn.clicked.connect(self.asset_tree.select_none)
        self.preview_btn.clicked.connect(self._on_preview_in_maya)
        self.dry_run_btn.clicked.connect(self._on_dry_run)
        self.convert_btn.clicked.connect(self._on_convert)
        self.clear_log_btn.clicked.connect(self.log_text.clear)
        self.asset_tree.itemDoubleClicked.connect(self._on_tree_double_click)
        
    def _log(self, message, color=None):
        """Add message to log with optional color."""
        if color:
            self.log_text.append(f'<span style="color:{color}">{message}</span>')
        else:
            self.log_text.append(message)
        
        # Auto-scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def _on_get_selected(self):
        """Get currently selected object as root."""
        sel = cmds.ls(selection=True, long=False)
        if sel:
            self.root_edit.setText(sel[0])
            self._log(f"Root set to: {sel[0]}", "#88cc88")
        else:
            self._log("Please select a root group in Maya", "#ffaa00")
            
    def _on_root_changed(self, text):
        """Enable analyze button when root is set."""
        self.analyze_btn.setEnabled(bool(text))
        
    def _on_analyze(self):
        """Analyze hierarchy for duplicate references."""
        root = self.root_edit.text()
        if not root:
            return

        if not cmds.objExists(root):
            self._log(f"Error: '{root}' does not exist", "#ff6666")
            return

        self._log(f"\nAnalyzing hierarchy under: {root}")
        self.asset_tree.clear()
        self.status_label.setText("Analyzing...")

        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        QtWidgets.QApplication.processEvents()

        try:
            self.duplicate_groups = self.analyzer.analyze(root)

            # Debug: log what was found
            self._log(f"[Debug] Found {len(self.all_assets_found())} referenced assets")
            self._log(f"[Debug] Grouped into {len(self.duplicate_groups)} reference groups")

            # Populate tree
            dup_count, single_count = self.asset_tree.populate(self.duplicate_groups)

            # Update stats
            dup_groups = sum(1 for g in self.duplicate_groups if g.is_duplicate)
            self.stats_label.setText(
                f"Found: {len(self.duplicate_groups)} asset types | "
                f"{dup_groups} with duplicates ({dup_count} refs) | "
                f"{single_count} single refs"
            )

            if dup_groups > 0:
                self.stats_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
                self._log(f"✓ Found {dup_groups} asset types with duplicate references!", "#ffaa00")
            else:
                self.stats_label.setStyleSheet("color: #88cc88;")
                self._log("✓ No duplicate references found.", "#88cc88")

            self.status_label.setText("Analysis complete")

        except Exception as e:
            import traceback
            self._log(f"Error during analysis: {e}", "#ff6666")
            self._log(traceback.format_exc(), "#ff6666")
            self.status_label.setText("Analysis failed")
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def all_assets_found(self):
        """Return all assets found by analyzer (for debugging)."""
        return self.analyzer.all_assets if hasattr(self.analyzer, 'all_assets') else []
            
    def _on_preview_in_maya(self):
        """Select items in Maya for preview."""
        item = self.asset_tree.currentItem()
        if not item:
            return

        data = item.data(0, QtCore.Qt.UserRole)

        if isinstance(data, DuplicateReferenceGroup):
            # Select all locators for this group (use full paths)
            locs = []
            for inst in data.instances:
                loc_path = inst.get_locator_path()
                if cmds.objExists(loc_path):
                    locs.append(loc_path)
            if locs:
                cmds.select(locs, replace=True)
                self._log(f"Selected {len(locs)} locators")
        elif isinstance(data, LocatorAssetInfo):
            # Select this specific locator (use full path)
            loc_path = data.get_locator_path()
            if cmds.objExists(loc_path):
                cmds.select(loc_path, replace=True)
                self._log(f"Selected: {data.locator}")

    def _on_tree_double_click(self, item, column):
        """Handle double-click on tree item."""
        self._on_preview_in_maya()
        
    def _on_dry_run(self):
        """Perform dry run (preview only)."""
        selected = self.asset_tree.get_checked_groups()
        if not selected:
            self._log("No groups selected for conversion", "#ffaa00")
            return
        
        self._log(f"\n{'='*50}", "#88cc88")
        self._log("DRY RUN - No changes will be made", "#88cc88")
        self._log(f"{'='*50}", "#88cc88")
        
        self._execute_conversion(selected, dry_run=True)
        
    def _on_convert(self):
        """Execute conversion."""
        selected = self.asset_tree.get_checked_groups()
        if not selected:
            self._log("No groups selected for conversion", "#ffaa00")
            return
        
        # Confirmation dialog
        total_refs = sum(g.count for g in selected)
        to_convert = sum(g.count - 1 for g in selected)  # All except masters
        
        result = QtWidgets.QMessageBox.question(
            self,
            "Confirm Conversion",
            f"This will convert {to_convert} references to instances.\n\n"
            f"• {len(selected)} asset types selected\n"
            f"• {to_convert} references will be removed\n"
            f"• {len(selected)} master references will be kept\n\n"
            "This operation CANNOT be undone!\n\n"
            "Continue?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if result != QtWidgets.QMessageBox.Yes:
            return
        
        self._log(f"\n{'='*50}", "#ff9900")
        self._log("CONVERTING - Making actual changes", "#ff9900")
        self._log(f"{'='*50}", "#ff9900")
        
        self._execute_conversion(selected, dry_run=False)
        
    def _execute_conversion(self, groups, dry_run=False):
        """Execute the conversion process."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.convert_btn.setEnabled(False)
        self.dry_run_btn.setEnabled(False)
        
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        
        try:
            def progress_callback(current, total, message):
                progress = int((current / total) * 100)
                self.progress_bar.setValue(progress)
                self.status_label.setText(message)
                QtWidgets.QApplication.processEvents()
            
            self.converter.convert_multiple_groups(groups, progress_callback, dry_run)
            
            # Display converter log
            for msg in self.converter.log_messages:
                if "ERROR" in msg:
                    self._log(msg, "#ff6666")
                elif "✓" in msg:
                    self._log(msg, "#88cc88")
                elif "WARNING" in msg:
                    self._log(msg, "#ffaa00")
                else:
                    self._log(msg)
            
            if not dry_run:
                self.status_label.setText("Conversion complete!")
                self._log("\n✓ Conversion complete!", "#88cc88")
                self._log("Click 'Analyze References' to refresh the list.", "#88cc88")

                # Update tree items to show converted status instead of auto-refresh
                # This preserves the UI state so user can see what was converted
                for group in groups:
                    self._mark_group_as_converted(group)

            else:
                self.status_label.setText("Dry run complete")

        except Exception as e:
            import traceback
            self._log(f"Error: {e}", "#ff6666")
            self._log(traceback.format_exc(), "#ff6666")
            self.status_label.setText(f"Error: {e}")
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.progress_bar.setVisible(False)
            self.convert_btn.setEnabled(True)
            self.dry_run_btn.setEnabled(True)

    def _mark_group_as_converted(self, group):
        """Mark a group as converted in the tree without full refresh."""
        # Find the tree item for this group and update its appearance
        root = self.asset_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item_data = item.data(0, QtCore.Qt.UserRole)
            if item_data and hasattr(item_data, 'ref_file'):
                if normalize_ref_file(item_data.ref_file) == normalize_ref_file(group.ref_file):
                    # Mark as converted
                    item.setText(0, f"✓ {group.asset_name} [CONVERTED]")
                    item.setForeground(0, QtGui.QBrush(QtGui.QColor("#88cc88")))
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsUserCheckable)
                    break


def show():
    """Show the Reference to Instance Converter UI."""
    global ref_to_instance_ui

    try:
        ref_to_instance_ui.close()
        ref_to_instance_ui.deleteLater()
    except:
        pass

    ref_to_instance_ui = ReferenceToInstanceUI()
    ref_to_instance_ui.show()
    return ref_to_instance_ui


def debug_analyze(root_group):
    """
    Debug function to test the analyzer outside the UI.

    Usage in Maya Script Editor:
        import ref2ints
        ref2ints.debug_analyze("SETS_CentralBusinessDistrictAExt_001:CBDAExtAreaLowA_Grp")
    """
    print(f"\n{'='*60}")
    print(f"DEBUG ANALYSIS: {root_group}")
    print(f"{'='*60}")

    if not cmds.objExists(root_group):
        print(f"ERROR: Root group does not exist: {root_group}")
        return

    analyzer = HierarchyAnalyzer()
    groups = analyzer.analyze(root_group)

    print(f"\n[Results]")
    print(f"Total assets found: {len(analyzer.all_assets)}")
    print(f"Total reference groups: {len(groups)}")

    for i, asset in enumerate(analyzer.all_assets):
        print(f"\n  Asset {i+1}:")
        print(f"    Locator: {asset.locator}")
        print(f"    Geo: {asset.geo_group}")
        print(f"    Namespace: {asset.namespace}")
        print(f"    Ref File: {asset.ref_file}")
        print(f"    Locator Path: {asset.locator_path}")
        print(f"    Geo Path: {asset.geo_group_path}")

    print(f"\n[Reference Groups]")
    for group in groups:
        status = "DUPLICATE" if group.is_duplicate else "Single"
        print(f"\n  {group.asset_name}: {group.count} refs ({status})")
        print(f"    File: {group.ref_file}")
        for j, inst in enumerate(group.instances):
            role = "Master" if j == 0 else "Slave"
            print(f"      [{role}] {inst.namespace}")

    return groups


# Allow running from Maya Script Editor
if __name__ == "__main__":
    show()