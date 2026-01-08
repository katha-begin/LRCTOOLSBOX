import maya.cmds as cmds
import maya.OpenMayaUI as omui

from PySide2 import QtCore, QtWidgets
from shiboken2 import wrapInstance


# ============================================================
# Maya window helper
# ============================================================

def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is None:
        return None
    return wrapInstance(int(ptr), QtWidgets.QWidget)


# ============================================================
# Alembic Hold Logic
# ============================================================

def _sanitize_name(name: str) -> str:
    return name.replace(":", "_").replace("|", "_")

def _safe_disconnect(dst_attr: str) -> None:
    src = cmds.listConnections(dst_attr, s=True, d=False, p=True) or []
    if src:
        try:
            cmds.disconnectAttr(src[0], dst_attr)
        except Exception:
            pass

def _hold_rhs_expression(start: float, hold_n: int) -> str:
    # sample_time = floor((t - start)/N)*N + start
    return f"floor((time1.outTime - {start})/{hold_n})*{hold_n} + {start}"

def apply_hold(alembic_nodes, hold_n: int) -> None:
    if not alembic_nodes:
        return
    hold_n = max(int(hold_n), 1)

    start = cmds.playbackOptions(q=True, min=True)
    rhs = _hold_rhs_expression(start, hold_n)

    for abc in alembic_nodes:
        if not cmds.objExists(abc) or cmds.nodeType(abc) != "AlembicNode":
            continue

        _safe_disconnect(f"{abc}.time")

        exp_name = _sanitize_name(abc) + "_hold_expr"
        if cmds.objExists(exp_name):
            try:
                cmds.delete(exp_name)
            except Exception:
                pass

        cmds.expression(
            name=exp_name,
            s=f"{abc}.time = {rhs};",
            ae=True,
            uc="all"
        )

def remove_hold(alembic_nodes) -> None:
    if not alembic_nodes:
        return

    for abc in alembic_nodes:
        if not cmds.objExists(abc) or cmds.nodeType(abc) != "AlembicNode":
            continue

        exp_name = _sanitize_name(abc) + "_hold_expr"
        if cmds.objExists(exp_name):
            try:
                cmds.delete(exp_name)
            except Exception:
                pass

        src = cmds.listConnections(f"{abc}.time", s=True, d=False, p=True) or []
        if not src:
            try:
                cmds.connectAttr("time1.outTime", f"{abc}.time", force=True)
            except Exception:
                pass


# ============================================================
# Namespace inference for tree grouping (your logic + minor tweaks)
# ============================================================

def _ns_root_from_name(node_name: str):
    return node_name.split(":", 1)[0] if ":" in node_name else None

def _type_prefix(ns_root: str) -> str:
    if not ns_root or ns_root == "NO_NAMESPACE":
        return "NO_NAMESPACE"
    return ns_root.split("_", 1)[0]

def _infer_asset_namespace_from_alembicnode(abc_node: str) -> str:
    candidates = []

    downstream = cmds.listConnections(abc_node, s=False, d=True) or []
    ignore_types = {
        "time", "unitConversion", "expression", "animCurveUU",
        "AlembicNode", "AlembicTimeControl"
    }

    for n in downstream:
        if not cmds.objExists(n):
            continue
        t = cmds.nodeType(n)

        if t in ignore_types:
            continue

        if t in ("mesh", "nurbsCurve", "nurbsSurface", "subdiv", "locator", "camera"):
            ns = _ns_root_from_name(n)
            if ns:
                candidates.append(ns)

            parents = cmds.listRelatives(n, parent=True, fullPath=False) or []
            for p in parents:
                ns2 = _ns_root_from_name(p)
                if ns2:
                    candidates.append(ns2)

        elif t == "transform":
            ns = _ns_root_from_name(n)
            if ns:
                candidates.append(ns)

    if candidates:
        counts = {}
        for ns in candidates:
            counts[ns] = counts.get(ns, 0) + 1
        best = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        return best

    ns_self = _ns_root_from_name(abc_node)
    if ns_self:
        return ns_self

    return "NO_NAMESPACE"


# ============================================================
# Keep-travel solver (FAST) — single vertex, single bake, drives whole character group
# Goal: Frame 2 pose = frame 1, but translate to match frame 2 position.
# ============================================================

def _normalize_vertex_to_transform(vtx: str) -> str:
    """
    Accept both:
      meshTransform.vtx[12]
      meshShape.vtx[12]
    and normalize to transform component.
    """
    if ".vtx[" not in vtx:
        return vtx

    base = vtx.split(".vtx[", 1)[0]
    rest = ".vtx[" + vtx.split(".vtx[", 1)[1]

    if cmds.objExists(base) and cmds.nodeType(base) == "mesh":
        parent = cmds.listRelatives(base, parent=True, fullPath=False) or []
        if parent:
            return parent[0] + rest

    return vtx

def _mesh_shape_from_transform(xform: str):
    shapes = cmds.listRelatives(xform, shapes=True, ni=True, fullPath=False) or []
    for s in shapes:
        if cmds.nodeType(s) == "mesh":
            return s
    return None

def _find_driving_alembic(mesh_shape: str):
    # Typical connection: AlembicNode.outPolyMesh -> meshShape.inMesh
    src = cmds.listConnections(mesh_shape + ".inMesh", s=True, d=False) or []
    for n in src:
        if cmds.nodeType(n) == "AlembicNode":
            return n
    # Fallback: history scan
    hist = cmds.listHistory(mesh_shape, pruneDagObjects=True) or []
    for n in hist:
        if cmds.nodeType(n) == "AlembicNode":
            return n
    return None

def _all_mesh_transforms_in_namespace(ns_root: str):
    meshes = cmds.ls(ns_root + ":*", type="mesh") or []
    xforms = []
    for shp in meshes:
        xf = (cmds.listRelatives(shp, parent=True, fullPath=False) or [None])[0]
        if xf and xf not in xforms:
            xforms.append(xf)
    return xforms

def _dag_chain_to_root(node: str):
    chain = []
    cur = node
    while cur:
        chain.append(cur)
        parents = cmds.listRelatives(cur, parent=True, fullPath=False) or []
        cur = parents[0] if parents else None
    return chain

def _lowest_common_parent(nodes):
    if not nodes:
        return None
    chains = [_dag_chain_to_root(n) for n in nodes]
    common = set(chains[0])
    for ch in chains[1:]:
        common &= set(ch)
    if not common:
        return None

    # choose common node closest to meshes
    def score(c):
        s = 0
        for ch in chains:
            s += ch.index(c) if c in ch else 999999
        return s

    return sorted(common, key=score)[0]

def _hold_time(frame: int, start: int, hold_n: int) -> int:
    n = max(int(hold_n), 1)
    return int(((frame - start) // n) * n + start)

def _set_alembic_manual_time(abc: str):
    _safe_disconnect(abc + ".time")

def _set_alembic_time_value(abc: str, tval: int):
    cmds.setAttr(abc + ".time", float(tval))

def _delete_if_exists(node: str):
    if cmds.objExists(node):
        try:
            cmds.delete(node)
        except:
            pass

def _build_keep_travel_from_vertex(
    vtx: str,
    hold_n: int,
    apply_constraint: bool,
    use_tree_nodes_for_hold: bool,
    alembic_nodes_for_hold: list,
    target_mode: str,  # "namespace_common_parent" or "mesh_transform"
    axes_mask=(True, True, True),  # X,Y,Z
    show_progress=True,
    suspend_viewport=True
):
    """
    Builds a baked offset locator:
      offset(frame) = P(frame) - P(heldTime(frame))
    then:
      - applies alembic hold expression to target AlembicNode(s)
      - optionally pointConstraints the character group/transform to that locator
    """
    hold_n = max(int(hold_n), 1)

    vtx = _normalize_vertex_to_transform(vtx)
    mesh_xform = vtx.split(".vtx[", 1)[0]
    if not cmds.objExists(mesh_xform) or cmds.nodeType(mesh_xform) != "transform":
        raise RuntimeError("Vertex must resolve to a mesh transform. Got: %s" % mesh_xform)

    ns_root = _ns_root_from_name(mesh_xform) or "NO_NAMESPACE"
    mesh_shape = _mesh_shape_from_transform(mesh_xform)
    if not mesh_shape:
        raise RuntimeError("Can't find mesh shape under: %s" % mesh_xform)

    sample_abc = _find_driving_alembic(mesh_shape)
    if not sample_abc:
        raise RuntimeError("Can't find AlembicNode driving selected vertex mesh.")

    # Target transform to move (all pieces)
    if target_mode == "namespace_common_parent" and ns_root != "NO_NAMESPACE":
        mesh_xforms = _all_mesh_transforms_in_namespace(ns_root)
        target = _lowest_common_parent(mesh_xforms) or mesh_xform
    else:
        target = mesh_xform

    # Which alembic nodes should be held?
    if use_tree_nodes_for_hold and alembic_nodes_for_hold:
        hold_abcs = [n for n in alembic_nodes_for_hold if cmds.objExists(n) and cmds.nodeType(n) == "AlembicNode"]
    else:
        # Auto: all AlembicNodes that live in the same inferred namespace group as the sample node.
        # This is conservative and matches how you group in the tree.
        inferred_ns = _infer_asset_namespace_from_alembicnode(sample_abc)
        hold_abcs = []
        for abc in cmds.ls(type="AlembicNode") or []:
            if _infer_asset_namespace_from_alembicnode(abc) == inferred_ns:
                hold_abcs.append(abc)

    # Locator + constraint names
    base = _sanitize_name(ns_root if ns_root != "NO_NAMESPACE" else mesh_xform)
    offset_loc = base + "_POSEHOLD_offsetWorld_LOC"
    con_name   = base + "_POSEHOLD_pointCons"

    # Range
    start = int(cmds.playbackOptions(q=True, min=True))
    end   = int(cmds.playbackOptions(q=True, max=True))

    # Build/clear locator
    if not cmds.objExists(offset_loc):
        cmds.spaceLocator(name=offset_loc)
    try:
        cmds.parent(offset_loc, world=True)
    except:
        pass

    # Make locator visible while debugging (user can hide later)
    cmds.setAttr(offset_loc + ".visibility", 1)

    try:
        cmds.cutKey(offset_loc, at=["tx","ty","tz"], clear=True)
    except:
        pass

    # Cache target base world pos once
    cmds.currentTime(start, e=True)
    target_base_world = cmds.xform(target, q=True, ws=True, t=True)

    # Speed: suspend viewport
    if suspend_viewport:
        try:
            cmds.refresh(suspend=True)
        except:
            pass

    # Manual drive time for sample alembic only
    _set_alembic_manual_time(sample_abc)

    pos_cache = {}

    if show_progress:
        cmds.progressWindow(
            title="PoseHold + KeepTravel",
            progress=0,
            maxValue=(end - start + 1),
            status="Caching vertex positions...",
            isInterruptable=True
        )

    try:
        # Pass 1: cache P(frame)
        for i, f in enumerate(range(start, end + 1), start=1):
            if show_progress:
                if cmds.progressWindow(q=True, isCancelled=True):
                    raise RuntimeError("Cancelled.")
                cmds.progressWindow(e=True, progress=i, status=f"Caching P({f})")

            cmds.currentTime(f, e=True)
            _set_alembic_time_value(sample_abc, f)
            pos_cache[f] = cmds.xform(vtx, q=True, ws=True, t=True)

        # Pass 2: bake locator keys
        if show_progress:
            cmds.progressWindow(e=True, progress=0, status="Baking offset keys...")

        for i, f in enumerate(range(start, end + 1), start=1):
            if show_progress:
                if cmds.progressWindow(q=True, isCancelled=True):
                    raise RuntimeError("Cancelled.")
                cmds.progressWindow(e=True, progress=i, status=f"Baking {f}")

            p_t = pos_cache[f]
            th = _hold_time(f, start, hold_n)
            p_th = pos_cache.get(th, p_t)

            off = [p_t[0] - p_th[0], p_t[1] - p_th[1], p_t[2] - p_th[2]]

            world_pos = [
                target_base_world[0] + (off[0] if axes_mask[0] else 0.0),
                target_base_world[1] + (off[1] if axes_mask[1] else 0.0),
                target_base_world[2] + (off[2] if axes_mask[2] else 0.0),
            ]

            cmds.xform(offset_loc, ws=True, t=world_pos)
            cmds.setKeyframe(offset_loc, at=["tx", "ty", "tz"], t=f)

    finally:
        if show_progress:
            try:
                cmds.progressWindow(endProgress=True)
            except:
                pass
        if suspend_viewport:
            try:
                cmds.refresh(suspend=False)
                cmds.refresh(f=True)
            except:
                pass

    # Apply HOLD to chosen Alembic nodes
    apply_hold(hold_abcs, hold_n)

    # Optionally constrain the target to baked locator (this is the "parenting" behavior)
    if apply_constraint:
        if cmds.objExists(con_name):
            _delete_if_exists(con_name)
        try:
            cmds.pointConstraint(offset_loc, target, mo=False, name=con_name)
        except Exception as e:
            raise RuntimeError(
                "Cannot constrain target '%s'. Likely locked by reference.\n"
                "Workaround: create a non-referenced driver group above the reference and constrain that.\n\nError: %s"
                % (target, e)
            )

    return {
        "ns_root": ns_root,
        "target": target,
        "sample_abc": sample_abc,
        "hold_abcs": hold_abcs,
        "offset_loc": offset_loc,
        "constraint": con_name if apply_constraint else ""
    }

def remove_keep_travel(ns_or_mesh: str):
    """
    Remove baked keep-travel setup by deleting:
      *_POSEHOLD_offsetWorld_LOC
      *_POSEHOLD_pointCons
    based on sanitized key from namespace or mesh.
    """
    key = _sanitize_name(ns_or_mesh)
    loc = key + "_POSEHOLD_offsetWorld_LOC"
    con = key + "_POSEHOLD_pointCons"
    _delete_if_exists(con)
    _delete_if_exists(loc)


# ============================================================
# Qt GUI
# ============================================================

class AlembicHoldOnNWindow(QtWidgets.QDialog):
    WINDOW_NAME = "AlembicHoldOnNWindow_Qt"

    def __init__(self, parent=maya_main_window()):
        super().__init__(parent)
        self.setObjectName(self.WINDOW_NAME)
        self.setWindowTitle("Alembic Hold (On N) + Keep Travel")
        self.setMinimumSize(620, 760)

        self._build_ui()
        self.refresh_tree()

    # ---------------- UI ----------------

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        # Hold settings
        settings_group = QtWidgets.QGroupBox("Hold Settings")
        settings_layout = QtWidgets.QHBoxLayout(settings_group)

        self.hold_spin = QtWidgets.QSpinBox()
        self.hold_spin.setRange(1, 240)
        self.hold_spin.setValue(2)

        settings_layout.addWidget(QtWidgets.QLabel("Hold every N frames (On N):"))
        settings_layout.addWidget(self.hold_spin)
        settings_layout.addStretch()

        self.refresh_btn = QtWidgets.QPushButton("Refresh List")
        self.apply_sel_btn = QtWidgets.QPushButton("Apply Hold to Selected")
        self.remove_sel_btn = QtWidgets.QPushButton("Remove Hold from Selected")

        settings_layout.addWidget(self.refresh_btn)
        settings_layout.addWidget(self.apply_sel_btn)
        settings_layout.addWidget(self.remove_sel_btn)

        main_layout.addWidget(settings_group)

        # Tree
        tree_group = QtWidgets.QGroupBox("AlembicNodes (Grouped by inferred asset namespace)")
        tree_layout = QtWidgets.QVBoxLayout(tree_group)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Group / Namespace / AlembicNode"])
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree.setUniformRowHeights(True)
        tree_layout.addWidget(self.tree)

        main_layout.addWidget(tree_group)

        # Keep travel group
        kt_group = QtWidgets.QGroupBox("Pose Hold + Keep Travel (2=pose1 but translate to frame2)")
        kt_layout = QtWidgets.QVBoxLayout(kt_group)

        row1 = QtWidgets.QHBoxLayout()
        self.scope_combo = QtWidgets.QComboBox()
        self.scope_combo.addItems([
            "Hold scope: Use selected AlembicNodes (tree)",
            "Hold scope: Auto from selected vertex namespace",
        ])
        row1.addWidget(self.scope_combo)

        self.apply_constraint_chk = QtWidgets.QCheckBox("Apply constraint to target (move whole character)")
        self.apply_constraint_chk.setChecked(True)
        row1.addWidget(self.apply_constraint_chk)

        kt_layout.addLayout(row1)

        row2 = QtWidgets.QHBoxLayout()
        self.target_combo = QtWidgets.QComboBox()
        self.target_combo.addItems([
            "Target: Namespace common parent (all pieces)",
            "Target: Only this mesh transform",
        ])
        row2.addWidget(self.target_combo)

        row2.addWidget(QtWidgets.QLabel("Affect axes:"))
        self.axis_x = QtWidgets.QCheckBox("X"); self.axis_x.setChecked(True)
        self.axis_y = QtWidgets.QCheckBox("Y"); self.axis_y.setChecked(True)
        self.axis_z = QtWidgets.QCheckBox("Z"); self.axis_z.setChecked(True)
        row2.addWidget(self.axis_x); row2.addWidget(self.axis_y); row2.addWidget(self.axis_z)
        row2.addStretch()

        kt_layout.addLayout(row2)

        row3 = QtWidgets.QHBoxLayout()
        self.build_keeptravel_btn = QtWidgets.QPushButton("Build Hold + Keep Travel from Selected Vertex")
        self.build_keeptravel_btn.setToolTip("Select ONE vertex on character (pelvis/hip). Builds travel offset + applies hold.")
        self.build_holdonly_from_vertex_btn = QtWidgets.QPushButton("Apply Hold to Vertex Asset (No Travel Fix)")
        self.remove_keeptravel_btn = QtWidgets.QPushButton("Remove Keep Travel (by Vertex Asset)")
        row3.addWidget(self.build_keeptravel_btn)
        row3.addWidget(self.build_holdonly_from_vertex_btn)
        row3.addWidget(self.remove_keeptravel_btn)
        kt_layout.addLayout(row3)

        self.status_label = QtWidgets.QLabel("Tip: Select a pelvis/hip vertex (Geo.vtx[] or GeoShape.vtx[]) then press Build.")
        self.status_label.setWordWrap(True)
        kt_layout.addWidget(self.status_label)

        main_layout.addWidget(kt_group)

        # Bottom buttons
        btn_row = QtWidgets.QHBoxLayout()
        self.apply_all_btn = QtWidgets.QPushButton("Apply Hold to ALL")
        self.remove_all_btn = QtWidgets.QPushButton("Remove Hold from ALL")
        self.select_scene_btn = QtWidgets.QPushButton("Select AlembicNodes in Scene")
        self.close_btn = QtWidgets.QPushButton("Close")

        btn_row.addWidget(self.apply_all_btn)
        btn_row.addWidget(self.remove_all_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.select_scene_btn)
        btn_row.addWidget(self.close_btn)

        main_layout.addLayout(btn_row)

        # Signals
        self.refresh_btn.clicked.connect(self.refresh_tree)
        self.apply_sel_btn.clicked.connect(self.apply_to_selected)
        self.remove_sel_btn.clicked.connect(self.remove_from_selected)
        self.apply_all_btn.clicked.connect(self.apply_to_all)
        self.remove_all_btn.clicked.connect(self.remove_from_all)
        self.select_scene_btn.clicked.connect(self.select_in_scene)
        self.close_btn.clicked.connect(self.close)

        self.build_keeptravel_btn.clicked.connect(self.build_keep_travel_from_vertex)
        self.build_holdonly_from_vertex_btn.clicked.connect(self.apply_hold_from_vertex_asset)
        self.remove_keeptravel_btn.clicked.connect(self.remove_keep_travel_from_vertex)

    # ---------------- Tree ----------------

    def refresh_tree(self):
        self.tree.clear()

        abc_nodes = cmds.ls(type="AlembicNode") or []
        abc_nodes.sort()

        groups = {}  # groups[type_prefix][ns_root] = [AlembicNode...]
        for abc in abc_nodes:
            ns_root = _infer_asset_namespace_from_alembicnode(abc)
            type_key = _type_prefix(ns_root)
            groups.setdefault(type_key, {}).setdefault(ns_root, []).append(abc)

        for type_key in sorted(groups.keys()):
            type_item = QtWidgets.QTreeWidgetItem([type_key])
            type_item.setFirstColumnSpanned(True)
            self.tree.addTopLevelItem(type_item)

            for ns_root in sorted(groups[type_key].keys()):
                ns_item = QtWidgets.QTreeWidgetItem([ns_root])
                type_item.addChild(ns_item)

                for abc in sorted(groups[type_key][ns_root]):
                    node_item = QtWidgets.QTreeWidgetItem([abc])
                    node_item.setData(0, QtCore.Qt.UserRole, abc)
                    ns_item.addChild(node_item)

            type_item.setExpanded(True)

        self.tree.resizeColumnToContents(0)

    def _selected_alembic_nodes(self):
        nodes = []
        for item in self.tree.selectedItems():
            node = item.data(0, QtCore.Qt.UserRole)
            if isinstance(node, str) and node:
                nodes.append(node)
        out = []
        for n in nodes:
            if n not in out:
                out.append(n)
        return out

    # ---------------- Hold actions ----------------

    def apply_to_selected(self):
        nodes = self._selected_alembic_nodes()
        hold_n = int(self.hold_spin.value())
        apply_hold(nodes, hold_n)
        cmds.inViewMessage(amg=f'Applied <hl>ON{hold_n}</hl> hold to {len(nodes)} AlembicNode(s).',
                           pos='topCenter', fade=True)

    def remove_from_selected(self):
        nodes = self._selected_alembic_nodes()
        remove_hold(nodes)
        cmds.inViewMessage(amg=f'Removed hold from {len(nodes)} AlembicNode(s).',
                           pos='topCenter', fade=True)

    def apply_to_all(self):
        nodes = cmds.ls(type="AlembicNode") or []
        hold_n = int(self.hold_spin.value())
        apply_hold(nodes, hold_n)
        cmds.inViewMessage(amg=f'Applied <hl>ON{hold_n}</hl> hold to ALL ({len(nodes)}) AlembicNode(s).',
                           pos='topCenter', fade=True)

    def remove_from_all(self):
        nodes = cmds.ls(type="AlembicNode") or []
        remove_hold(nodes)
        cmds.inViewMessage(amg=f'Removed hold from ALL ({len(nodes)}) AlembicNode(s).',
                           pos='topCenter', fade=True)

    def select_in_scene(self):
        nodes = self._selected_alembic_nodes()
        cmds.select(nodes, r=True) if nodes else cmds.select(clear=True)

    # ---------------- Vertex-driven workflow ----------------

    def _get_selected_vertex(self):
        sel = cmds.ls(sl=True, fl=True) or []
        for s in sel:
            if ".vtx[" in s:
                return s
        return None

    def apply_hold_from_vertex_asset(self):
        """Apply HOLD only, but automatically scope to the vertex asset if user chose auto."""
        vtx = self._get_selected_vertex()
        if not vtx:
            self.status_label.setText("No vertex selected. Select ONE pelvis vertex and try again.")
            return

        hold_n = int(self.hold_spin.value())

        # Decide scope
        if self.scope_combo.currentIndex() == 0:
            # selected in tree
            nodes = self._selected_alembic_nodes()
            apply_hold(nodes, hold_n)
            self.status_label.setText(f"Hold ON{hold_n} applied to {len(nodes)} selected AlembicNode(s).")
            return

        # Auto from vertex asset: we run a lightweight keep-travel builder in 'hold only' mode (no bake),
        # reusing the same inference method: use sample alembic, then apply hold to all in inferred namespace.
        vtx_norm = _normalize_vertex_to_transform(vtx)
        mesh_xform = vtx_norm.split(".vtx[", 1)[0]
        mesh_shape = _mesh_shape_from_transform(mesh_xform)
        if not mesh_shape:
            self.status_label.setText("Could not find mesh shape from selected vertex.")
            return

        sample_abc = _find_driving_alembic(mesh_shape)
        if not sample_abc:
            self.status_label.setText("Could not find AlembicNode driving that mesh.")
            return

        inferred_ns = _infer_asset_namespace_from_alembicnode(sample_abc)
        hold_abcs = []
        for abc in cmds.ls(type="AlembicNode") or []:
            if _infer_asset_namespace_from_alembicnode(abc) == inferred_ns:
                hold_abcs.append(abc)

        apply_hold(hold_abcs, hold_n)
        self.status_label.setText(f"Hold ON{hold_n} applied to asset group '{inferred_ns}' ({len(hold_abcs)} AlembicNodes).")

    def build_keep_travel_from_vertex(self):
        vtx = self._get_selected_vertex()
        if not vtx:
            self.status_label.setText("No vertex selected. Select ONE pelvis/hip vertex and try again.")
            return

        hold_n = int(self.hold_spin.value())
        apply_constraint = self.apply_constraint_chk.isChecked()

        use_tree = (self.scope_combo.currentIndex() == 0)
        tree_nodes = self._selected_alembic_nodes() if use_tree else []

        target_mode = "namespace_common_parent" if self.target_combo.currentIndex() == 0 else "mesh_transform"

        axes_mask = (self.axis_x.isChecked(), self.axis_y.isChecked(), self.axis_z.isChecked())

        try:
            info = _build_keep_travel_from_vertex(
                vtx=vtx,
                hold_n=hold_n,
                apply_constraint=apply_constraint,
                use_tree_nodes_for_hold=use_tree,
                alembic_nodes_for_hold=tree_nodes,
                target_mode=target_mode,
                axes_mask=axes_mask,
                show_progress=True,
                suspend_viewport=True
            )
        except Exception as e:
            self.status_label.setText("ERROR: %s" % e)
            raise

        msg = f"Built keep-travel for {info['ns_root']} | target={info['target']} | holdNodes={len(info['hold_abcs'])}"
        if apply_constraint:
            msg += " | constraint=ON"
        else:
            msg += " | constraint=OFF (bake only)"
        self.status_label.setText(msg)

        cmds.inViewMessage(
            amg=f"Built <hl>ON{hold_n}</hl> keep-travel for <hl>{info['ns_root']}</hl>",
            pos="topCenter", fade=True
        )

    def remove_keep_travel_from_vertex(self):
        vtx = self._get_selected_vertex()
        if not vtx:
            self.status_label.setText("No vertex selected. Select a vertex from the asset you want to clean.")
            return

        vtx_norm = _normalize_vertex_to_transform(vtx)
        mesh_xform = vtx_norm.split(".vtx[", 1)[0]
        ns_root = _ns_root_from_name(mesh_xform) or mesh_xform

        remove_keep_travel(ns_root)

        self.status_label.setText(f"Removed keep-travel nodes for key: {ns_root}")
        cmds.inViewMessage(amg=f"Removed keep-travel nodes for <hl>{ns_root}</hl>", pos="topCenter", fade=True)


def show_alembic_hold_on_n_ui():
    # Close existing window if open
    for w in QtWidgets.QApplication.allWidgets():
        if w.objectName() == AlembicHoldOnNWindow.WINDOW_NAME:
            try:
                w.close()
                w.deleteLater()
            except Exception:
                pass

    dlg = AlembicHoldOnNWindow()
    dlg.show()
    return dlg


# Execute
show_alembic_hold_on_n_ui()
