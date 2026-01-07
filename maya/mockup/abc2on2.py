import maya.cmds as cmds
import maya.OpenMayaUI as omui

from PySide2 import QtCore, QtWidgets
from shiboken2 import wrapInstance


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is None:
        return None
    return wrapInstance(int(ptr), QtWidgets.QWidget)


# ----------------------------
# Alembic Hold Logic
# ----------------------------

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
    # Maya expression: sample_time = floor((t - start)/N)*N + start
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

        # Reconnect default time driver if nothing drives it
        src = cmds.listConnections(f"{abc}.time", s=True, d=False, p=True) or []
        if not src:
            try:
                cmds.connectAttr("time1.outTime", f"{abc}.time", force=True)
            except Exception:
                pass


# ----------------------------
# Namespace inference (fixes missing SETS_* assets)
# ----------------------------

def _ns_root_from_name(node_name: str):
    # "SETS_env_city:foo:bar" -> "SETS_env_city"
    return node_name.split(":", 1)[0] if ":" in node_name else None


def _type_prefix(ns_root: str) -> str:
    # "CHAR_xx_xx" -> "CHAR", "SETS_env_city" -> "SETS"
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


# ----------------------------
# Qt GUI
# ----------------------------

class AlembicHoldOnNWindow(QtWidgets.QDialog):
    WINDOW_NAME = "AlembicHoldOnNWindow_Qt"

    def __init__(self, parent=maya_main_window()):
        super().__init__(parent)
        self.setObjectName(self.WINDOW_NAME)
        self.setWindowTitle("Alembic Hold (On N)")
        self.setMinimumSize(560, 620)

        self._build_ui()
        self.refresh_tree()

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        settings_group = QtWidgets.QGroupBox("Hold Settings")
        settings_layout = QtWidgets.QHBoxLayout(settings_group)

        self.hold_spin = QtWidgets.QSpinBox()
        self.hold_spin.setRange(1, 240)
        self.hold_spin.setValue(2)

        settings_layout.addWidget(QtWidgets.QLabel("Hold every N frames (On N):"))
        settings_layout.addWidget(self.hold_spin)
        settings_layout.addStretch()

        self.refresh_btn = QtWidgets.QPushButton("Refresh List")
        self.apply_sel_btn = QtWidgets.QPushButton("Apply to Selected")
        self.remove_sel_btn = QtWidgets.QPushButton("Remove from Selected")

        settings_layout.addWidget(self.refresh_btn)
        settings_layout.addWidget(self.apply_sel_btn)
        settings_layout.addWidget(self.remove_sel_btn)

        main_layout.addWidget(settings_group)

        tree_group = QtWidgets.QGroupBox("AlembicNodes (Grouped by inferred asset namespace)")
        tree_layout = QtWidgets.QVBoxLayout(tree_group)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Group / Namespace / AlembicNode"])
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree.setUniformRowHeights(True)

        tree_layout.addWidget(self.tree)
        main_layout.addWidget(tree_group)

        btn_row = QtWidgets.QHBoxLayout()
        self.apply_all_btn = QtWidgets.QPushButton("Apply to ALL")
        self.remove_all_btn = QtWidgets.QPushButton("Remove from ALL")
        self.select_scene_btn = QtWidgets.QPushButton("Select in Scene")
        self.close_btn = QtWidgets.QPushButton("Close")

        btn_row.addWidget(self.apply_all_btn)
        btn_row.addWidget(self.remove_all_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.select_scene_btn)
        btn_row.addWidget(self.close_btn)

        main_layout.addLayout(btn_row)

        self.refresh_btn.clicked.connect(self.refresh_tree)
        self.apply_sel_btn.clicked.connect(self.apply_to_selected)
        self.remove_sel_btn.clicked.connect(self.remove_from_selected)
        self.apply_all_btn.clicked.connect(self.apply_to_all)
        self.remove_all_btn.clicked.connect(self.remove_from_all)
        self.select_scene_btn.clicked.connect(self.select_in_scene)
        self.close_btn.clicked.connect(self.close)

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
                    node_item.setData(0, QtCore.Qt.UserRole, abc)  # store AlembicNode name
                    ns_item.addChild(node_item)

            type_item.setExpanded(True)

        self.tree.resizeColumnToContents(0)

    def _selected_alembic_nodes(self):
        nodes = []
        for item in self.tree.selectedItems():
            node = item.data(0, QtCore.Qt.UserRole)
            if isinstance(node, str) and node:
                nodes.append(node)

        # unique, stable
        out = []
        for n in nodes:
            if n not in out:
                out.append(n)
        return out

    def apply_to_selected(self):
        nodes = self._selected_alembic_nodes()
        hold_n = int(self.hold_spin.value())
        apply_hold(nodes, hold_n)
        cmds.inViewMessage(
            amg=f'Applied <hl>ON{hold_n}</hl> hold to {len(nodes)} AlembicNode(s).',
            pos='topCenter', fade=True
        )

    def remove_from_selected(self):
        nodes = self._selected_alembic_nodes()
        remove_hold(nodes)
        cmds.inViewMessage(
            amg=f'Removed hold from {len(nodes)} AlembicNode(s).',
            pos='topCenter', fade=True
        )

    def apply_to_all(self):
        nodes = cmds.ls(type="AlembicNode") or []
        hold_n = int(self.hold_spin.value())
        apply_hold(nodes, hold_n)
        cmds.inViewMessage(
            amg=f'Applied <hl>ON{hold_n}</hl> hold to ALL ({len(nodes)}) AlembicNode(s).',
            pos='topCenter', fade=True
        )

    def remove_from_all(self):
        nodes = cmds.ls(type="AlembicNode") or []
        remove_hold(nodes)
        cmds.inViewMessage(
            amg=f'Removed hold from ALL ({len(nodes)}) AlembicNode(s).',
            pos='topCenter', fade=True
        )

    def select_in_scene(self):
        nodes = self._selected_alembic_nodes()
        cmds.select(nodes, r=True) if nodes else cmds.select(clear=True)


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


# Execute when script is run (either directly or via plugin)
show_alembic_hold_on_n_ui()



