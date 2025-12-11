"""
SETS Instance Builder - Step-by-Step Test Tool

Test workflow:
1. Import SETS alembic -> SETS_Grp
2. Analyze locators to find components (like ref2ints.py)
3. Create master references (geo + shader)
4. Create instances for duplicates

Uses shared shader assignment logic from igl_shot_build.py

Author: Pipeline Tools
Version: 1.1.0
"""

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from collections import defaultdict
import os
import re
import json
import ast

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance


# =============================================================================
# Shared Shader Assignment Functions (from igl_shot_build.py)
# =============================================================================

def _strip_namespace(node_name):
    """Strip namespace from node name."""
    return node_name.split(':')[-1] if node_name else node_name


def _apply_namespace_to_path(src_dag_path, namespace):
    """Apply namespace to a DAG path."""
    if not src_dag_path or not src_dag_path.startswith("|"):
        return None
    parts = [p for p in src_dag_path.split("|") if p]
    new_parts = ["{}:{}".format(namespace, _strip_namespace(seg)) for seg in parts]
    return "|" + "|".join(new_parts)


def _resolve_shape_in_scene(stored_path, geo_namespace):
    """Resolve a shape path in the scene using namespace."""
    # Try full DAG reconstruction
    candidate = _apply_namespace_to_path(stored_path, geo_namespace)
    if candidate and cmds.objExists(candidate):
        if cmds.nodeType(candidate) in ("mesh", "nurbsSurface", "nurbsCurve", "subdiv", "aiStandIn"):
            return candidate
        if cmds.objectType(candidate, isAType="transform"):
            shapes = cmds.listRelatives(candidate, shapes=True, fullPath=True) or []
            if shapes:
                return shapes[0]
    # Fallback by leaf shape name within geo namespace
    leaf = _strip_namespace(stored_path.split("|")[-1]) if "|" in stored_path else _strip_namespace(stored_path)
    candidates = []
    for shp in cmds.ls(type=["mesh", "nurbsSurface", "nurbsCurve", "aiStandIn"], long=True) or []:
        if _strip_namespace(shp).lower() == leaf.lower():
            last_seg = shp.split("|")[-1]
            if ":" in last_seg and last_seg.split(":")[0] == geo_namespace:
                candidates.append(shp)
    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        target_segments = [s for s in stored_path.split("|") if s]
        target_wo_ns = [_strip_namespace(s) for s in target_segments]
        for shp in candidates:
            segs = [s for s in shp.split("|") if s]
            segs_wo_ns = [_strip_namespace(s) for s in segs]
            if segs_wo_ns[-len(target_wo_ns):] == target_wo_ns:
                return shp
        return candidates[0]
    return None


def _read_mapping_from_sg(sg):
    """Read snow__assign_shade mapping from shading group."""
    attr = "{}.snow__assign_shade".format(sg)
    if not cmds.objExists(attr):
        return []
    atype = cmds.getAttr(attr, type=True)
    try:
        if atype == "stringArray":
            arr = cmds.getAttr(attr)
            if isinstance(arr, (list, tuple)):
                if len(arr) == 2 and isinstance(arr[1], (list, tuple)):
                    return list(arr[1])
                return list(arr)
            return []
        elif atype == "string":
            raw = cmds.getAttr(attr)
            if not raw:
                return []
            try:
                val = json.loads(raw)
                if isinstance(val, list):
                    return [str(x) for x in val]
            except Exception:
                try:
                    val = ast.literal_eval(raw)
                    if isinstance(val, list):
                        return [str(x) for x in val]
                except Exception:
                    return [raw]
    except Exception:
        pass
    return []


def _sg_has_material_connection(sg):
    """Check if shading group has material connection."""
    for plug in ("rsSurfaceShader", "surfaceShader"):
        plg = "{}.{}".format(sg, plug)
        if cmds.objExists(plg):
            conns = cmds.listConnections(plg, source=True, destination=False) or []
            if conns:
                return conns[0]
    return None


def _assign_shapes_to_sg(shapes, sg):
    """Assign shapes to shading group."""
    assigned, failed = 0, []
    for shp in shapes:
        try:
            if not cmds.objExists(shp):
                failed.append((shp, "missing"))
                continue
            cmds.sets(shp, e=True, forceElement=sg)
            assigned += 1
        except Exception as e:
            failed.append((shp, str(e)))
    return assigned, failed


def scan_shader_assignments(shader_namespace):
    """Scan for shading groups with stored mapping data."""
    all_sg = cmds.ls(type="shadingEngine") or []
    hit = []
    for sg in all_sg:
        if not sg.startswith(shader_namespace + ":"):
            continue
        if cmds.objExists("{}.snow__assign_shade".format(sg)):
            mapping = _read_mapping_from_sg(sg)
            mat = _sg_has_material_connection(sg)
            hit.append((sg, mat, mapping))
    return hit


def plan_shader_assignments(geo_namespace, sg_entries):
    """Plan shader assignments using stored mapping data."""
    plan = []
    for sg, mat, stored_paths in sg_entries:
        resolved, unresolved = [], []
        for p in stored_paths:
            shp = _resolve_shape_in_scene(p, geo_namespace)
            if shp and cmds.objExists(shp):
                resolved.append(shp)
            else:
                unresolved.append(p)
        plan.append({
            "sg": sg,
            "material": mat,
            "targets": list(stored_paths),
            "resolved": sorted(list(set(resolved))),
            "unresolved": list(unresolved)
        })
    return plan


def assign_component_shaders(geo_ns, shader_ns, log_func=None):
    """
    Assign shaders to geometry using snow__assign_shade mapping.
    Shared logic from igl_shot_build.py.
    """
    def log(msg):
        if log_func:
            log_func(msg)
        else:
            print(msg)

    try:
        log("  [SHADER] Assigning shaders from {} to {}".format(shader_ns, geo_ns))

        shader_sgs = cmds.ls("{}:*".format(shader_ns), type="shadingEngine") or []
        if not shader_sgs:
            log("  [WARNING] No shading groups found in: {}".format(shader_ns))
            return 0

        log("  [INFO] Found {} shading groups".format(len(shader_sgs)))

        shader_assignments = scan_shader_assignments(shader_ns)
        if not shader_assignments:
            log("  [WARNING] No SGs with 'snow__assign_shade' mapping in {}".format(shader_ns))
            return 0

        log("  [INFO] Found {} SGs with snow__assign_shade".format(len(shader_assignments)))

        assignment_plan = plan_shader_assignments(geo_ns, shader_assignments)

        total_assigned = 0
        for entry in assignment_plan:
            sg = entry["sg"]
            targets = entry.get("resolved", [])

            if not targets:
                continue

            try:
                assigned, failed = _assign_shapes_to_sg(targets, sg)
                if assigned > 0:
                    total_assigned += assigned
                    log("  [OK] Assigned {} shapes to {}".format(assigned, sg.split(":")[-1]))
            except Exception as e:
                log("  [ERROR] Failed to assign {}: {}".format(sg, str(e)))

        log("  [COMPLETE] Total shapes assigned: {}".format(total_assigned))
        return total_assigned

    except Exception as e:
        log("  [ERROR] Shader assignment failed: {}".format(str(e)))
        return 0


def get_maya_main_window():
    """Get Maya's main window as a Qt object."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


# ============================================================================
# Data Classes
# ============================================================================

class ComponentInfo:
    """Information about a component found in a locator."""
    def __init__(self, locator_path, component_name, component_id):
        self.locator_path = locator_path
        self.locator_short = locator_path.split("|")[-1]
        self.component_name = component_name
        self.component_id = component_id
        self.is_master = False
        self.geo_group = None  # After master build: path to geometry group


class ComponentGroup:
    """Group of locators referencing the same component."""
    def __init__(self, component_name):
        self.component_name = component_name
        self.locators = []  # List of ComponentInfo
        self.geo_file = None
        self.shader_file = None
        self.master_geo_group = None  # Path to master geometry after build

    def add_locator(self, info):
        self.locators.append(info)

    @property
    def count(self):
        return len(self.locators)

    @property
    def has_duplicates(self):
        return self.count > 1

    @property
    def master(self):
        """First locator is master."""
        return self.locators[0] if self.locators else None

    @property
    def duplicates(self):
        """All locators except master."""
        return self.locators[1:] if self.count > 1 else []


# ============================================================================
# Core Functions
# ============================================================================

def ensure_sets_grp():
    """Create Sets_Grp if not exists."""
    if not cmds.objExists("Sets_Grp"):
        cmds.group(empty=True, name="Sets_Grp")
        print("[OK] Created Sets_Grp")
    return "Sets_Grp"


def import_sets_alembic(abc_file, namespace=None):
    """
    Import SETS alembic file.

    Args:
        abc_file: Path to alembic file
        namespace: Optional namespace (auto-generated if None)

    Returns:
        tuple: (namespace, imported_root_group)
    """
    if not os.path.exists(abc_file):
        raise FileNotFoundError("File not found: {}".format(abc_file))

    # Auto-generate namespace from filename
    # Ep04_sq0070_SH0180__SETS_CentralBusinessDistrictAExt_001.abc
    if namespace is None:
        filename = os.path.basename(abc_file)
        # Extract SETS_xxx_001 part
        match = re.search(r'(SETS_[A-Za-z0-9]+_\d+)', filename)
        if match:
            namespace = match.group(1)
        else:
            namespace = filename.replace(".abc", "").replace(".", "_")

    # Create namespace
    if not cmds.namespace(exists=namespace):
        cmds.namespace(add=namespace)
        print("[OK] Created namespace: {}".format(namespace))

    # Store current namespace
    current_ns = cmds.namespaceInfo(currentNamespace=True)

    try:
        # Set namespace and import
        cmds.namespace(setNamespace=namespace)
        cmds.AbcImport(abc_file, mode="import", fitTimeRange=False)
        print("[OK] Imported alembic into namespace: {}".format(namespace))
    finally:
        cmds.namespace(setNamespace=current_ns)

    # Parent to Sets_Grp
    sets_grp = ensure_sets_grp()
    top_level = cmds.ls("{}:*".format(namespace), type="transform") or []
    root_groups = []

    for node in top_level:
        parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
        if not parents or parents[0] == "|":
            try:
                cmds.parent(node, sets_grp)
                root_groups.append(node)
                print("[OK] Parented {} to {}".format(node, sets_grp))
            except Exception as e:
                print("[WARNING] Could not parent {}: {}".format(node, str(e)))

    return namespace, root_groups


def analyze_locators(namespace):
    """
    Analyze locators in namespace to find components and group duplicates.
    Similar to ref2ints.py analysis but for locators.

    Returns:
        dict: {component_name: ComponentGroup}
    """
    component_groups = {}

    # Find all locators in namespace
    locators = cmds.ls("{}:*_Loc".format(namespace), type="transform", long=True) or []
    print("\n[ANALYZE] Found {} locators in namespace {}".format(len(locators), namespace))

    for loc_path in locators:
        loc_short = loc_path.split("|")[-1]
        # Remove namespace prefix for parsing
        loc_name = loc_short.split(":")[-1] if ":" in loc_short else loc_short

        # Parse: CBDAExtAreaLowA_001_Loc -> component=CBDAExtAreaLowA, id=001
        if not loc_name.endswith("_Loc"):
            continue

        # Remove _Loc suffix
        name_without_suffix = loc_name[:-4]  # Remove "_Loc"

        # Split by underscore to get component name and ID
        parts = name_without_suffix.rsplit("_", 1)
        if len(parts) == 2:
            component_name = parts[0]
            component_id = parts[1]
        else:
            component_name = name_without_suffix
            component_id = "001"

        # Create ComponentInfo
        info = ComponentInfo(loc_path, component_name, component_id)

        # Add to group
        if component_name not in component_groups:
            component_groups[component_name] = ComponentGroup(component_name)
        component_groups[component_name].add_locator(info)

    # Print analysis summary
    print("\n[ANALYSIS SUMMARY]")
    total_locators = 0
    duplicates_found = 0
    for name, group in component_groups.items():
        total_locators += group.count
        if group.has_duplicates:
            duplicates_found += group.count - 1
            print("  {} x{} (DUPLICATE - {} instances can be created)".format(
                name, group.count, group.count - 1))
        else:
            print("  {} x{}".format(name, group.count))

    print("\nTotal: {} locators, {} unique components, {} potential instances".format(
        total_locators, len(component_groups), duplicates_found))

    return component_groups


def find_asset_files(component_name, root_path, project, verbose=True):
    """
    Find geometry and shader files for a component.

    Returns:
        tuple: (geo_file, shader_file) or (None, None)
    """
    search_locations = [
        ("Setdress", "interior"),
        ("Setdress", "exterior"),
        ("Props", "object")
    ]

    if verbose:
        print("\n[SEARCH] Looking for asset: {}".format(component_name))
        print("  Root: {}".format(root_path))
        print("  Project: {}".format(project))

    for category, subdir in search_locations:
        base_path = os.path.join(root_path, project, "all", "asset", category, subdir, component_name, "hero")
        geo_file = os.path.join(base_path, "{}_geo.abc".format(component_name))
        shader_file = os.path.join(base_path, "{}_rsshade.ma".format(component_name))

        if verbose:
            print("  Checking: {}".format(geo_file))

        if os.path.exists(geo_file):
            print("[FOUND] {} in {}/{}".format(component_name, category, subdir))
            print("  Geo: {}".format(geo_file))
            print("  Shader: {}".format(shader_file))
            return geo_file, shader_file

    print("[NOT FOUND] Asset files for: {}".format(component_name))
    print("  Searched paths:")
    for category, subdir in search_locations:
        base_path = os.path.join(root_path, project, "all", "asset", category, subdir, component_name, "hero")
        print("    - {}".format(base_path))
    return None, None


def build_master(group, set_namespace, root_path, project):
    """
    Build master reference for a component group.
    Master stays at ORIGIN (not parented to any locator).
    All locators will get instances later.

    Args:
        group: ComponentGroup
        set_namespace: SETS namespace (e.g., SETS_CentralBusinessDistrictAExt_001)
        root_path: Root path (e.g., V:/SWA)
        project: Project name (e.g., SWA)

    Returns:
        str: Path to master geometry group, or None if failed
    """
    if not group.locators:
        return None

    component_name = group.component_name

    # Find asset files
    geo_file, shader_file = find_asset_files(component_name, root_path, project)
    if not geo_file:
        print("[ERROR] Cannot build master for {}: asset files not found".format(component_name))
        return None

    group.geo_file = geo_file
    group.shader_file = shader_file

    # Create namespace for this master component
    # Format: SETS_xxx:ComponentName_master
    master_ns = "{}:{}_master".format(set_namespace, component_name)

    print("\n[MASTER] Building master for {} (stays at ORIGIN)".format(component_name))

    # Reference geometry
    try:
        cmds.file(geo_file, reference=True, namespace=master_ns)
        print("  [OK] Referenced geometry: {}".format(geo_file))
    except Exception as e:
        print("  [ERROR] Failed to reference geometry: {}".format(str(e)))
        return None

    # Find top-level geometry group (use long path for stability)
    geo_transforms = cmds.ls("{}:*".format(master_ns), type="transform", long=True) or []
    master_geo_group = None

    for node in geo_transforms:
        parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
        if not parents or parents[0] == "|":
            master_geo_group = node
            break

    if not master_geo_group:
        print("  [ERROR] Could not find top-level geometry in {}".format(master_ns))
        return None

    print("  [INFO] Master geo group: {}".format(master_geo_group))

    # Keep master at ORIGIN - do NOT parent to locator
    # Just reset transform to ensure it's at 0,0,0
    try:
        cmds.xform(master_geo_group, translation=[0, 0, 0], rotation=[0, 0, 0])
        cmds.xform(master_geo_group, scale=[1, 1, 1])
        print("  [OK] Master stays at ORIGIN (0,0,0)")
    except Exception as e:
        print("  [WARNING] Could not reset transform: {}".format(str(e)))

    # Reference shader and assign
    if shader_file and os.path.exists(shader_file):
        shader_ns = "{}_shade".format(master_ns)
        try:
            cmds.file(shader_file, reference=True, namespace=shader_ns)
            print("  [OK] Referenced shader: {}".format(shader_file))

            # Assign shaders using shared logic from igl_shot_build.py
            assign_component_shaders(master_ns, shader_ns)
        except Exception as e:
            print("  [ERROR] Failed to reference/assign shader: {}".format(str(e)))
    else:
        print("  [WARNING] Shader file not found: {}".format(shader_file))

    # Update group - master geo stays at origin
    group.master_geo_group = master_geo_group
    print("  [INFO] All {} locators will get instances".format(len(group.locators)))

    return master_geo_group


def build_single_asset(group, set_namespace, root_path, project):
    """
    Build a single (non-duplicate) asset directly to its locator.
    No instancing needed - just reference and parent.

    Args:
        group: ComponentGroup with only 1 locator
        set_namespace: SETS namespace
        root_path: Root path (e.g., V:/)
        project: Project name (e.g., SWA)

    Returns:
        str: Path to geometry group, or None if failed
    """
    if not group.locators:
        return None

    if group.has_duplicates:
        print("[SKIP] {} has duplicates - use Build Masters + Instances instead".format(group.component_name))
        return None

    loc_info = group.locators[0]
    component_name = group.component_name

    # Find asset files
    geo_file, shader_file = find_asset_files(component_name, root_path, project)
    if not geo_file:
        print("[ERROR] Cannot build {}: asset files not found".format(component_name))
        return None

    # Create namespace for this component
    # Format: SETS_xxx:ComponentName_001
    component_ns = "{}:{}_{}"	.format(set_namespace, component_name, loc_info.component_id)

    print("\n[SINGLE] Building {} -> {}".format(component_name, loc_info.locator_short))

    # Reference geometry
    try:
        cmds.file(geo_file, reference=True, namespace=component_ns)
        print("  [OK] Referenced geometry: {}".format(geo_file))
    except Exception as e:
        print("  [ERROR] Failed to reference geometry: {}".format(str(e)))
        return None

    # Find top-level geometry group
    geo_transforms = cmds.ls("{}:*".format(component_ns), type="transform") or []
    geo_group = None

    for node in geo_transforms:
        parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
        if not parents or parents[0] == "|":
            geo_group = node
            break

    if not geo_group:
        print("  [ERROR] Could not find top-level geometry in {}".format(component_ns))
        return None

    # Parent to locator and reset transform
    try:
        cmds.parent(geo_group, loc_info.locator_path)
        cmds.xform(geo_group, translation=[0, 0, 0], rotation=[0, 0, 0])
        cmds.xform(geo_group, scale=[1, 1, 1])
        print("  [OK] Parented to locator: {}".format(loc_info.locator_short))
    except Exception as e:
        print("  [ERROR] Failed to parent: {}".format(str(e)))

    # Reference shader and assign
    if shader_file and os.path.exists(shader_file):
        shader_ns = "{}_shade".format(component_ns)
        try:
            cmds.file(shader_file, reference=True, namespace=shader_ns)
            print("  [OK] Referenced shader: {}".format(shader_file))

            # Assign shaders using shared logic from igl_shot_build.py
            assign_component_shaders(component_ns, shader_ns)
        except Exception as e:
            print("  [ERROR] Failed to reference/assign shader: {}".format(str(e)))
    else:
        print("  [WARNING] Shader file not found: {}".format(shader_file))

    loc_info.geo_group = geo_group
    return geo_group


def create_instances(group):
    """
    Create instances for ALL locators (master stays at origin, all locators get instances).
    Following ref2ints.py pattern: instance master geo, parent to locator, reset transform.

    Args:
        group: ComponentGroup with master_geo_group already set

    Returns:
        int: Number of instances created
    """
    if not group.master_geo_group:
        print("[ERROR] No master geometry for {}".format(group.component_name))
        return 0

    if not group.locators:
        print("[INFO] No locators for {}".format(group.component_name))
        return 0

    instances_created = 0
    print("\n[INSTANCES] Creating {} instances for {} (all locators)".format(
        len(group.locators), group.component_name))

    # Create instance for EVERY locator (master stays at origin)
    for loc_info in group.locators:
        try:
            # Generate instance name
            instance_name = "{}_{}_{}_inst".format(
                group.component_name,
                loc_info.component_id,
                group.master_geo_group.split("|")[-1].replace(":", "_")
            )

            # Create instance of master geometry
            instance = cmds.instance(group.master_geo_group, name=instance_name)[0]

            # Parent to locator
            cmds.parent(instance, loc_info.locator_path)

            # Reset transform (locator provides world position)
            cmds.xform(instance, translation=[0, 0, 0], rotation=[0, 0, 0])
            cmds.xform(instance, scale=[1, 1, 1])

            print("  [OK] Instance: {} -> {}".format(instance_name, loc_info.locator_short))
            instances_created += 1
            loc_info.geo_group = instance

        except Exception as e:
            print("  [ERROR] Failed instance for {}: {}".format(loc_info.locator_short, str(e)))

    # Hide the original master geo (it stays at origin, instances are visible)
    if instances_created > 0:
        try:
            master_node = group.master_geo_group
            # Try to find the node if path changed
            if not cmds.objExists(master_node):
                # Try short name
                short_name = master_node.split("|")[-1]
                matches = cmds.ls(short_name, long=True) or []
                if matches:
                    master_node = matches[0]

            if cmds.objExists(master_node):
                cmds.setAttr("{}.visibility".format(master_node), 0)
                print("  [HIDE] Master geo hidden: {}".format(master_node))
            else:
                print("  [WARNING] Could not find master to hide: {}".format(group.master_geo_group))
        except Exception as e:
            print("  [WARNING] Could not hide master: {}".format(str(e)))

    return instances_created



# ============================================================================
# UI Class
# ============================================================================

class SetsInstanceTestUI(QtWidgets.QDialog):
    """Step-by-step test UI for SETS instance building - 3 Column Layout."""

    WINDOW_TITLE = "SETS Instance Builder v1.1"

    def __init__(self, parent=get_maya_main_window()):
        super().__init__(parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        # State
        self.current_namespace = None
        self.component_groups = {}  # {name: ComponentGroup}

        self._create_ui()
        self._create_connections()

    def _create_ui(self):
        """Build the 3-column UI layout."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # === Main Splitter (3 columns) ===
        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # =====================================================================
        # COLUMN 1: Controls (Left)
        # =====================================================================
        col1_widget = QtWidgets.QWidget()
        col1_layout = QtWidgets.QVBoxLayout(col1_widget)
        col1_layout.setContentsMargins(4, 4, 4, 4)
        col1_layout.setSpacing(8)

        # --- Shot Navigation ---
        nav_group = QtWidgets.QGroupBox("Shot Navigation")
        nav_layout = QtWidgets.QFormLayout(nav_group)
        nav_layout.setSpacing(4)

        self.root_edit = QtWidgets.QLineEdit("V:/")
        nav_layout.addRow("Root:", self.root_edit)

        self.project_combo = QtWidgets.QComboBox()
        nav_layout.addRow("Project:", self.project_combo)

        self.episode_combo = QtWidgets.QComboBox()
        nav_layout.addRow("Episode:", self.episode_combo)

        self.sequence_combo = QtWidgets.QComboBox()
        nav_layout.addRow("Sequence:", self.sequence_combo)

        self.shot_combo = QtWidgets.QComboBox()
        nav_layout.addRow("Shot:", self.shot_combo)

        self.version_combo = QtWidgets.QComboBox()
        nav_layout.addRow("Version:", self.version_combo)

        self.refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        nav_layout.addRow("", self.refresh_btn)

        col1_layout.addWidget(nav_group)

        # --- Step 1: Import ---
        step1_group = QtWidgets.QGroupBox("Step 1: Import SETS")
        step1_layout = QtWidgets.QVBoxLayout(step1_group)
        step1_layout.setSpacing(4)

        step1_layout.addWidget(QtWidgets.QLabel("SETS File:"))
        self.sets_file_combo = QtWidgets.QComboBox()
        self.sets_file_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        step1_layout.addWidget(self.sets_file_combo)

        self.load_sets_btn = QtWidgets.QPushButton("📂 Load Files")
        step1_layout.addWidget(self.load_sets_btn)

        browse_row = QtWidgets.QHBoxLayout()
        self.abc_file_edit = QtWidgets.QLineEdit()
        self.abc_file_edit.setPlaceholderText("Or browse...")
        self.browse_btn = QtWidgets.QPushButton("...")
        self.browse_btn.setFixedWidth(30)
        browse_row.addWidget(self.abc_file_edit)
        browse_row.addWidget(self.browse_btn)
        step1_layout.addLayout(browse_row)

        self.import_btn = QtWidgets.QPushButton("▶ Import SETS")
        self.import_btn.setStyleSheet("font-weight: bold; background-color: #2196F3; color: white; padding: 6px;")
        step1_layout.addWidget(self.import_btn)

        col1_layout.addWidget(step1_group)

        # --- Step 2: Analyze ---
        step2_group = QtWidgets.QGroupBox("Step 2: Analyze")
        step2_layout = QtWidgets.QVBoxLayout(step2_group)
        step2_layout.setSpacing(4)

        step2_layout.addWidget(QtWidgets.QLabel("Namespace:"))
        ns_row = QtWidgets.QHBoxLayout()
        self.namespace_edit = QtWidgets.QLineEdit()
        self.namespace_edit.setReadOnly(True)
        self.get_selected_ns_btn = QtWidgets.QPushButton("◀")
        self.get_selected_ns_btn.setFixedWidth(30)
        self.get_selected_ns_btn.setToolTip("Get namespace from selection")
        ns_row.addWidget(self.namespace_edit)
        ns_row.addWidget(self.get_selected_ns_btn)
        step2_layout.addLayout(ns_row)

        self.analyze_btn = QtWidgets.QPushButton("🔍 Analyze Locators")
        self.analyze_btn.setStyleSheet("font-weight: bold; padding: 6px;")
        step2_layout.addWidget(self.analyze_btn)

        col1_layout.addWidget(step2_group)

        # --- Step 3-4: Build ---
        step34_group = QtWidgets.QGroupBox("Step 3-4: Build")
        step34_layout = QtWidgets.QVBoxLayout(step34_group)
        step34_layout.setSpacing(4)

        step34_layout.addWidget(QtWidgets.QLabel("Duplicates (Masters + Instances):"))
        self.build_masters_btn = QtWidgets.QPushButton("🔨 Build Masters")
        self.build_masters_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 4px;")
        step34_layout.addWidget(self.build_masters_btn)

        self.create_instances_btn = QtWidgets.QPushButton("📋 Create Instances")
        self.create_instances_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 4px;")
        step34_layout.addWidget(self.create_instances_btn)

        self.build_all_btn = QtWidgets.QPushButton("⚡ Build All (3+4)")
        self.build_all_btn.setStyleSheet("font-weight: bold; background-color: #9C27B0; color: white; padding: 6px;")
        step34_layout.addWidget(self.build_all_btn)

        step34_layout.addWidget(QtWidgets.QLabel("Singles (Direct Reference):"))
        self.build_singles_btn = QtWidgets.QPushButton("📄 Build Singles")
        self.build_singles_btn.setStyleSheet("background-color: #607D8B; color: white; padding: 4px;")
        self.build_singles_btn.setToolTip("Build assets with only 1 locator (no instancing)")
        step34_layout.addWidget(self.build_singles_btn)

        col1_layout.addWidget(step34_group)

        col1_layout.addStretch()
        col1_widget.setMinimumWidth(220)
        col1_widget.setMaximumWidth(300)

        # =====================================================================
        # COLUMN 2: Component List (Center)
        # =====================================================================
        col2_widget = QtWidgets.QWidget()
        col2_layout = QtWidgets.QVBoxLayout(col2_widget)
        col2_layout.setContentsMargins(4, 4, 4, 4)
        col2_layout.setSpacing(4)

        # Header with selection buttons
        header_row = QtWidgets.QHBoxLayout()
        header_row.addWidget(QtWidgets.QLabel("<b>Components</b> (check items to process)"))
        header_row.addStretch()
        self.select_all_btn = QtWidgets.QPushButton("Select All Dup")
        self.select_all_btn.setFixedHeight(24)
        self.select_none_btn = QtWidgets.QPushButton("Select None")
        self.select_none_btn.setFixedHeight(24)
        header_row.addWidget(self.select_all_btn)
        header_row.addWidget(self.select_none_btn)
        col2_layout.addLayout(header_row)

        # Component Tree
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Component", "Count", "Status"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(20)
        tree_header = self.tree.header()
        tree_header.setStretchLastSection(True)
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 50)
        self.tree.setStyleSheet("""
            QTreeWidget::item { padding: 2px; }
            QTreeWidget::item:selected { background-color: #3daee9; }
        """)
        col2_layout.addWidget(self.tree)

        col2_widget.setMinimumWidth(350)

        # =====================================================================
        # COLUMN 3: Log Output (Right)
        # =====================================================================
        col3_widget = QtWidgets.QWidget()
        col3_layout = QtWidgets.QVBoxLayout(col3_widget)
        col3_layout.setContentsMargins(4, 4, 4, 4)
        col3_layout.setSpacing(4)

        # Log header
        log_header = QtWidgets.QHBoxLayout()
        log_header.addWidget(QtWidgets.QLabel("<b>Log Output</b>"))
        log_header.addStretch()
        self.clear_log_btn = QtWidgets.QPushButton("Clear")
        self.clear_log_btn.setFixedHeight(24)
        log_header.addWidget(self.clear_log_btn)
        col3_layout.addLayout(log_header)

        # Log text
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("""
            QPlainTextEdit {
                font-family: Consolas, 'Courier New', monospace;
                font-size: 11px;
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
        """)
        col3_layout.addWidget(self.log)

        col3_widget.setMinimumWidth(300)
        col3_widget.setMaximumWidth(450)

        # =====================================================================
        # Add columns to splitter
        # =====================================================================
        self.main_splitter.addWidget(col1_widget)
        self.main_splitter.addWidget(col2_widget)
        self.main_splitter.addWidget(col3_widget)

        # Set initial splitter sizes (Controls: 280, Components: stretch, Log: 380)
        self.main_splitter.setSizes([280, 500, 380])
        self.main_splitter.setStretchFactor(0, 0)  # Controls - fixed
        self.main_splitter.setStretchFactor(1, 1)  # Components - stretch
        self.main_splitter.setStretchFactor(2, 0)  # Log - fixed

        main_layout.addWidget(self.main_splitter)

        # =====================================================================
        # STATUS BAR (Bottom)
        # =====================================================================
        status_widget = QtWidgets.QWidget()
        status_layout = QtWidgets.QHBoxLayout(status_widget)
        status_layout.setContentsMargins(4, 4, 4, 4)
        status_layout.setSpacing(8)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%v / %m")
        status_layout.addWidget(self.progress_bar, 1)

        # Status labels
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("color: #888;")
        status_layout.addWidget(self.status_label)

        # Summary labels
        self.summary_label = QtWidgets.QLabel("")
        self.summary_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.summary_label)

        main_layout.addWidget(status_widget)

    def _create_connections(self):
        """Connect signals."""
        # Navigation dropdowns
        self.root_edit.textChanged.connect(self._on_root_changed)
        self.project_combo.currentTextChanged.connect(self._on_project_changed)
        self.episode_combo.currentTextChanged.connect(self._on_episode_changed)
        self.sequence_combo.currentTextChanged.connect(self._on_sequence_changed)
        self.shot_combo.currentTextChanged.connect(self._on_shot_changed)
        self.version_combo.currentTextChanged.connect(self._on_version_changed)
        self.refresh_btn.clicked.connect(self._refresh_projects)
        self.load_sets_btn.clicked.connect(self._load_sets_files)

        # Step 1
        self.browse_btn.clicked.connect(self._browse_file)
        self.import_btn.clicked.connect(self._import_alembic)

        # Step 2
        self.get_selected_ns_btn.clicked.connect(self._get_namespace_from_selection)
        self.analyze_btn.clicked.connect(self._analyze)

        # Selection
        self.select_all_btn.clicked.connect(self._select_all_duplicates)
        self.select_none_btn.clicked.connect(self._select_none)

        # Build
        self.build_masters_btn.clicked.connect(self._build_masters)
        self.create_instances_btn.clicked.connect(self._create_instances)
        self.build_all_btn.clicked.connect(self._build_all)
        self.build_singles_btn.clicked.connect(self._build_singles)

        # Log
        self.clear_log_btn.clicked.connect(self._clear_log)

        # Tree selection - show details in log
        self.tree.itemClicked.connect(self._on_tree_item_clicked)

        # Initial load
        self._refresh_projects()

    def _clear_log(self):
        """Clear log output."""
        self.log.clear()

    def _update_status(self, text):
        """Update status label."""
        self.status_label.setText(text)

    def _update_summary(self):
        """Update summary label based on component groups."""
        if not self.component_groups:
            self.summary_label.setText("")
            return

        dup_count = sum(1 for g in self.component_groups.values() if g.has_duplicates)
        single_count = sum(1 for g in self.component_groups.values() if not g.has_duplicates)
        checked = len(self._get_checked_groups())

        self.summary_label.setText(
            "📊 {} duplicates | {} singles | {} selected".format(dup_count, single_count, checked)
        )

    def _set_progress(self, value, maximum=100):
        """Set progress bar value."""
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)

    def _on_tree_item_clicked(self, item, column):
        """Handle tree item click - show component details in log."""
        component_name = item.data(0, QtCore.Qt.UserRole)
        if not component_name or component_name not in self.component_groups:
            return

        group = self.component_groups[component_name]

        self._log_msg("\n" + "─" * 50)
        self._log_msg("📦 Component: {}".format(component_name))
        self._log_msg("─" * 50)
        self._log_msg("  Count: {} locators".format(len(group.locators)))
        self._log_msg("  Type: {}".format("⚠️ DUPLICATE" if group.has_duplicates else "✓ Single"))

        if group.geo_file:
            self._log_msg("  Geo: {}".format(group.geo_file))
        if group.shader_file:
            self._log_msg("  Shader: {}".format(group.shader_file))
        if group.master_geo_group:
            self._log_msg("  Master: {}".format(group.master_geo_group))

        self._log_msg("\n  Locators:")
        for i, loc in enumerate(group.locators[:10]):  # Show first 10
            status = "✓" if loc.geo_group else "○"
            self._log_msg("    {} {} {}".format(status, loc.locator_short, loc.component_id))
        if len(group.locators) > 10:
            self._log_msg("    ... and {} more".format(len(group.locators) - 10))

    def _log_msg(self, msg):
        """Add message to log."""
        self.log.appendPlainText(msg)
        print(msg)

    # === Navigation Methods (similar to igl_shot_build.py) ===

    def _list_directories(self, path):
        """List directories in a path."""
        if not os.path.exists(path):
            return []
        try:
            return sorted([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
        except Exception:
            return []

    def _on_root_changed(self):
        """Handle root path change."""
        self._refresh_projects()

    def _refresh_projects(self):
        """Refresh project list."""
        root = self.root_edit.text().strip()
        if not root or not os.path.exists(root):
            return

        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        projects = self._list_directories(root)
        if projects:
            self.project_combo.addItems(projects)
            # Try to select SWA by default
            idx = self.project_combo.findText("SWA")
            if idx >= 0:
                self.project_combo.setCurrentIndex(idx)
        self.project_combo.blockSignals(False)
        self._on_project_changed()

    def _on_project_changed(self):
        """Handle project selection change."""
        self.episode_combo.blockSignals(True)
        self.episode_combo.clear()
        self.sequence_combo.clear()
        self.shot_combo.clear()
        self.version_combo.clear()
        self.sets_file_combo.clear()

        project = self.project_combo.currentText()
        if not project:
            self.episode_combo.blockSignals(False)
            return

        root = self.root_edit.text().strip()
        scene_path = os.path.join(root, project, "all", "scene")
        episodes = self._list_directories(scene_path)
        if episodes:
            self.episode_combo.addItems(episodes)
        self.episode_combo.blockSignals(False)
        self._on_episode_changed()

    def _on_episode_changed(self):
        """Handle episode selection change."""
        self.sequence_combo.blockSignals(True)
        self.sequence_combo.clear()
        self.shot_combo.clear()
        self.version_combo.clear()
        self.sets_file_combo.clear()

        episode = self.episode_combo.currentText()
        if not episode:
            self.sequence_combo.blockSignals(False)
            return

        root = self.root_edit.text().strip()
        project = self.project_combo.currentText()
        ep_path = os.path.join(root, project, "all", "scene", episode)
        sequences = self._list_directories(ep_path)
        if sequences:
            self.sequence_combo.addItems(sequences)
        self.sequence_combo.blockSignals(False)
        self._on_sequence_changed()

    def _on_sequence_changed(self):
        """Handle sequence selection change."""
        self.shot_combo.blockSignals(True)
        self.shot_combo.clear()
        self.version_combo.clear()
        self.sets_file_combo.clear()

        sequence = self.sequence_combo.currentText()
        if not sequence:
            self.shot_combo.blockSignals(False)
            return

        root = self.root_edit.text().strip()
        project = self.project_combo.currentText()
        episode = self.episode_combo.currentText()
        seq_path = os.path.join(root, project, "all", "scene", episode, sequence)
        shots = self._list_directories(seq_path)
        if shots:
            self.shot_combo.addItems(shots)
        self.shot_combo.blockSignals(False)
        self._on_shot_changed()

    def _on_shot_changed(self):
        """Handle shot selection change."""
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        self.sets_file_combo.clear()

        shot = self.shot_combo.currentText()
        if not shot:
            self.version_combo.blockSignals(False)
            return

        root = self.root_edit.text().strip()
        project = self.project_combo.currentText()
        episode = self.episode_combo.currentText()
        sequence = self.sequence_combo.currentText()

        # Path to anim publish versions
        publish_path = os.path.join(root, project, "all", "scene", episode, sequence, shot, "anim", "publish")
        versions = self._list_directories(publish_path)
        if versions:
            # Sort versions and select latest
            versions = sorted(versions, reverse=True)
            self.version_combo.addItems(versions)
        self.version_combo.blockSignals(False)
        self._on_version_changed()

    def _on_version_changed(self):
        """Handle version selection change."""
        self._load_sets_files()

    def _load_sets_files(self):
        """Load SETS files from selected shot/version."""
        self.sets_file_combo.clear()

        root = self.root_edit.text().strip()
        project = self.project_combo.currentText()
        episode = self.episode_combo.currentText()
        sequence = self.sequence_combo.currentText()
        shot = self.shot_combo.currentText()
        version = self.version_combo.currentText()

        if not all([root, project, episode, sequence, shot, version]):
            return

        publish_path = os.path.join(root, project, "all", "scene", episode, sequence, shot, "anim", "publish", version)

        if not os.path.exists(publish_path):
            self._log_msg("[WARNING] Path not found: {}".format(publish_path))
            return

        # Find *_SETS_*.abc files
        sets_files = []
        try:
            for f in os.listdir(publish_path):
                if f.endswith(".abc") and "_SETS_" in f:
                    full_path = os.path.join(publish_path, f)
                    sets_files.append((f, full_path))
        except Exception as e:
            self._log_msg("[ERROR] Failed to list files: {}".format(str(e)))
            return

        if sets_files:
            for filename, filepath in sets_files:
                self.sets_file_combo.addItem(filename, filepath)
            self._log_msg("[OK] Found {} SETS files in {}".format(len(sets_files), version))
        else:
            self._log_msg("[INFO] No SETS files found in {}".format(publish_path))

    def _browse_file(self):
        """Browse for SETS alembic file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select SETS Alembic File",
            "V:/SWA/all/scene",
            "Alembic Files (*.abc)"
        )
        if file_path:
            self.abc_file_edit.setText(file_path)

    def _import_alembic(self):
        """Import SETS alembic file."""
        # Check dropdown first, then browse field
        abc_file = None

        # Try dropdown selection first
        if self.sets_file_combo.currentIndex() >= 0:
            abc_file = self.sets_file_combo.currentData()

        # Fall back to browse field
        if not abc_file:
            abc_file = self.abc_file_edit.text().strip()

        if not abc_file:
            self._log_msg("[ERROR] Please select a SETS file from dropdown or browse")
            return

        if not os.path.exists(abc_file):
            self._log_msg("[ERROR] File not found: {}".format(abc_file))
            return

        self._log_msg("\n" + "="*60)
        self._log_msg("[STEP 1] Importing SETS Alembic...")
        self._log_msg("File: {}".format(abc_file))
        self._log_msg("="*60)

        try:
            namespace, root_groups = import_sets_alembic(abc_file)
            self.current_namespace = namespace
            self.namespace_edit.setText(namespace)
            self._log_msg("[OK] Import complete! Namespace: {}".format(namespace))
        except Exception as e:
            self._log_msg("[ERROR] Import failed: {}".format(str(e)))

    def _get_namespace_from_selection(self):
        """Get namespace from selected object."""
        sel = cmds.ls(selection=True) or []
        if not sel:
            self._log_msg("[ERROR] Nothing selected")
            return

        obj = sel[0]
        if ":" in obj:
            # Get top-level namespace
            ns = obj.split(":")[0]
            self.namespace_edit.setText(ns)
            self.current_namespace = ns
            self._log_msg("[OK] Got namespace from selection: {}".format(ns))
        else:
            self._log_msg("[ERROR] Selected object has no namespace")

    def _analyze(self):
        """Analyze locators in namespace."""
        namespace = self.namespace_edit.text().strip()
        if not namespace:
            self._log_msg("[ERROR] No namespace set. Import alembic first or get from selection.")
            return

        self._update_status("Analyzing...")
        self._log_msg("\n" + "="*60)
        self._log_msg("[STEP 2] Analyzing Locators...")
        self._log_msg("="*60)

        self.current_namespace = namespace
        self.component_groups = analyze_locators(namespace)

        # Populate tree
        self._populate_tree()

        # Update status and summary
        total = len(self.component_groups)
        dup = sum(1 for g in self.component_groups.values() if g.has_duplicates)
        self._log_msg("\n[OK] Found {} components ({} duplicates, {} singles)".format(
            total, dup, total - dup))
        self._update_status("Analysis complete")
        self._update_summary()

    def _populate_tree(self):
        """Populate tree with component groups (3 columns: Component, Count, Status)."""
        self.tree.clear()

        for name, group in sorted(self.component_groups.items()):
            # Create group item
            item = QtWidgets.QTreeWidgetItem()
            item.setData(0, QtCore.Qt.UserRole, name)  # Store component name for lookup

            # Set checkbox for duplicates
            if group.has_duplicates:
                item.setCheckState(0, QtCore.Qt.Unchecked)
                icon = "⚠️"
                color = QtGui.QColor("#ff9900")
                status = "⚠️ DUP ({} instances)".format(group.count - 1)
            else:
                icon = "✓"
                color = QtGui.QColor("#888888")
                status = "✓ Single"

            item.setText(0, "{} {}".format(icon, name))
            item.setText(1, str(group.count))
            item.setText(2, status)
            item.setForeground(0, QtGui.QBrush(color))

            # Add child items for locators
            for i, loc_info in enumerate(group.locators):
                child = QtWidgets.QTreeWidgetItem()
                loc_short = loc_info.locator_short.split(":")[-1]

                if group.has_duplicates:
                    child.setText(0, "    {}".format(loc_short))
                    child.setForeground(0, QtGui.QBrush(QtGui.QColor("#aaaaaa")))
                else:
                    child.setText(0, "    {}".format(loc_short))
                    child.setForeground(0, QtGui.QBrush(QtGui.QColor("#888888")))

                child.setText(1, loc_info.component_id)
                item.addChild(child)

            self.tree.addTopLevelItem(item)

            # Expand duplicates by default
            if group.has_duplicates:
                item.setExpanded(True)

    def _select_all_duplicates(self):
        """Check all duplicate groups."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            component_name = item.data(0, QtCore.Qt.UserRole)
            if component_name and component_name in self.component_groups:
                group = self.component_groups[component_name]
                if group.has_duplicates:
                    item.setCheckState(0, QtCore.Qt.Checked)
        self._update_summary()

    def _select_none(self):
        """Uncheck all groups."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            try:
                item.setCheckState(0, QtCore.Qt.Unchecked)
            except:
                pass
        self._update_summary()

    def _get_checked_groups(self):
        """Get list of checked ComponentGroup objects."""
        checked = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) == QtCore.Qt.Checked:
                component_name = item.data(0, QtCore.Qt.UserRole)
                if component_name and component_name in self.component_groups:
                    checked.append(self.component_groups[component_name])
        return checked

    def _build_masters(self):
        """Build master references for checked groups."""
        groups = self._get_checked_groups()
        if not groups:
            self._log_msg("[ERROR] No components selected. Check items to process.")
            return

        root_path = self.root_edit.text().strip()
        project = self.project_combo.currentText()
        namespace = self.current_namespace

        self._update_status("Building masters...")
        self._set_progress(0, len(groups))
        self._log_msg("\n" + "="*60)
        self._log_msg("[STEP 3] Building Masters...")
        self._log_msg("="*60)

        success_count = 0
        failed_count = 0
        for i, group in enumerate(groups):
            result = build_master(group, namespace, root_path, project)
            if result:
                success_count += 1
            else:
                failed_count += 1
            self._set_progress(i + 1, len(groups))
            QtWidgets.QApplication.processEvents()

        self._log_msg("\n[COMPLETE] Built {} masters ({} failed)".format(success_count, failed_count))
        self._update_status("Masters complete")
        self._populate_tree()

    def _create_instances(self):
        """Create instances for checked groups."""
        groups = self._get_checked_groups()
        if not groups:
            self._log_msg("[ERROR] No components selected. Check items to process.")
            return

        self._update_status("Creating instances...")
        self._set_progress(0, len(groups))
        self._log_msg("\n" + "="*60)
        self._log_msg("[STEP 4] Creating Instances...")
        self._log_msg("="*60)

        total_instances = 0
        for i, group in enumerate(groups):
            if group.master_geo_group:
                instances = create_instances(group)
                total_instances += instances
            else:
                self._log_msg("[SKIP] {} - no master built yet".format(group.component_name))
            self._set_progress(i + 1, len(groups))
            QtWidgets.QApplication.processEvents()

        self._log_msg("\n[COMPLETE] Created {} instances".format(total_instances))
        self._update_status("Instances complete")

    def _build_all(self):
        """
        Build EVERYTHING in one click:
        1. Build Masters for checked duplicates
        2. Create Instances for duplicates
        3. Build Singles (non-duplicates)
        """
        if not self.component_groups:
            self._log_msg("[ERROR] No components analyzed. Run Analyze first.")
            return

        root_path = self.root_edit.text().strip()
        project = self.project_combo.currentText()
        namespace = self.current_namespace

        # Get checked duplicate groups
        duplicate_groups = self._get_checked_groups()

        # Get all single (non-duplicate) components
        single_groups = [g for g in self.component_groups.values() if not g.has_duplicates]

        total_items = len(duplicate_groups) * 2 + len(single_groups)  # masters + instances + singles

        if total_items == 0:
            self._log_msg("[INFO] No components to build. Check duplicate items or ensure singles exist.")
            return

        self._update_status("Building all...")
        self._set_progress(0, total_items)
        self._log_msg("\n" + "="*60)
        self._log_msg("[BUILD ALL] Complete build: {} duplicates + {} singles".format(
            len(duplicate_groups), len(single_groups)))
        self._log_msg("="*60)

        total_masters = 0
        total_instances = 0
        total_singles = 0
        failed_count = 0
        progress_idx = 0

        # ----------------------------------------------------------------
        # STEP 1: Build Masters for duplicates
        # ----------------------------------------------------------------
        if duplicate_groups:
            self._log_msg("\n--- STEP 1: Building Masters ({} duplicates) ---".format(len(duplicate_groups)))

            for group in duplicate_groups:
                master = build_master(group, namespace, root_path, project)
                progress_idx += 1
                self._set_progress(progress_idx, total_items)
                QtWidgets.QApplication.processEvents()

                if master:
                    total_masters += 1
                else:
                    failed_count += 1

        # ----------------------------------------------------------------
        # STEP 2: Create Instances for duplicates
        # ----------------------------------------------------------------
        if duplicate_groups:
            self._log_msg("\n--- STEP 2: Creating Instances ---")

            for group in duplicate_groups:
                if group.master_geo_group:
                    instances = create_instances(group)
                    total_instances += instances

                progress_idx += 1
                self._set_progress(progress_idx, total_items)
                QtWidgets.QApplication.processEvents()

        # ----------------------------------------------------------------
        # STEP 3: Build Singles (non-duplicates)
        # ----------------------------------------------------------------
        if single_groups:
            self._log_msg("\n--- STEP 3: Building Singles ({} assets) ---".format(len(single_groups)))

            for group in single_groups:
                result = build_single_asset(group, namespace, root_path, project)
                if result:
                    total_singles += 1
                else:
                    failed_count += 1

                progress_idx += 1
                self._set_progress(progress_idx, total_items)
                QtWidgets.QApplication.processEvents()

        # ----------------------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------------------
        self._log_msg("\n" + "="*60)
        self._log_msg("[BUILD ALL COMPLETE]")
        self._log_msg("  Masters:   {}".format(total_masters))
        self._log_msg("  Instances: {}".format(total_instances))
        self._log_msg("  Singles:   {}".format(total_singles))
        if failed_count > 0:
            self._log_msg("  Failed:    {}".format(failed_count))
        self._log_msg("="*60)
        self._update_status("Build complete: {} masters, {} instances, {} singles".format(
            total_masters, total_instances, total_singles))
        self._populate_tree()

    def _build_singles(self):
        """Build non-duplicate (single) assets with direct references."""
        if not self.component_groups:
            self._log_msg("[ERROR] No components analyzed. Run Analyze first.")
            return

        root_path = self.root_edit.text().strip()
        project = self.project_combo.currentText()
        namespace = self.current_namespace

        # Find all single (non-duplicate) components
        single_groups = [g for g in self.component_groups.values() if not g.has_duplicates]

        if not single_groups:
            self._log_msg("[INFO] No non-duplicate components found.")
            return

        self._update_status("Building singles...")
        self._set_progress(0, len(single_groups))
        self._log_msg("\n" + "="*60)
        self._log_msg("[BUILD SINGLES] Building {} non-duplicate assets".format(len(single_groups)))
        self._log_msg("="*60)

        success_count = 0
        failed_count = 0

        for i, group in enumerate(single_groups):
            result = build_single_asset(group, namespace, root_path, project)
            if result:
                success_count += 1
            else:
                failed_count += 1
            self._set_progress(i + 1, len(single_groups))
            QtWidgets.QApplication.processEvents()

        self._log_msg("\n" + "="*60)
        self._log_msg("[COMPLETE] Built {} singles ({} failed)".format(success_count, failed_count))
        self._log_msg("="*60)
        self._update_status("Singles complete")
        self._populate_tree()


# ============================================================================
# Show Function
# ============================================================================

_ui_instance = None

def show():
    """Show the SETS Instance Test UI."""
    global _ui_instance

    try:
        if _ui_instance is not None:
            _ui_instance.close()
            _ui_instance.deleteLater()
    except:
        pass

    _ui_instance = SetsInstanceTestUI()
    _ui_instance.show()
    return _ui_instance


if __name__ == "__main__":
    show()