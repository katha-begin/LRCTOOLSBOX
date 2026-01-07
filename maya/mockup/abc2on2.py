import maya.cmds as cmds

# ----------------------------
# Qt Compatibility (PySide2 / PySide1)
# ----------------------------
QtCore = None
QtWidgets = None
wrapInstance = None

try:
    from PySide2 import QtCore, QtWidgets
    from shiboken2 import wrapInstance
except:
    try:
        from PySide import QtCore, QtGui
        QtWidgets = QtGui
        from shiboken import wrapInstance
    except:
        raise RuntimeError("PySide2/PySide not found. Check your Maya version / Python environment.")

import maya.OpenMayaUI as omui

# Python 2/3 compatibility
import sys
if sys.version_info.major >= 3:
    long = int
    basestring = str


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is None:
        return None
    return wrapInstance(long(ptr), QtWidgets.QWidget)


# ----------------------------
# Alembic Hold Logic
# ----------------------------

def _sanitize_name(name):
    return name.replace(':', '_').replace('|', '_')

def _safe_disconnect(dst_attr):
    src = cmds.listConnections(dst_attr, s=True, d=False, p=True) or []
    if src:
        try:
            cmds.disconnectAttr(src[0], dst_attr)
        except:
            pass

def _hold_rhs_expression(start, hold_n):
    return "floor((time1.outTime - %s)/%d)*%d + %s" % (start, hold_n, hold_n, start)

def apply_hold(alembic_nodes, hold_n):
    if not alembic_nodes:
        return
    if hold_n < 1:
        hold_n = 1

    start = cmds.playbackOptions(q=True, min=True)
    rhs = _hold_rhs_expression(start, hold_n)

    for abc in alembic_nodes:
        if not cmds.objExists(abc) or cmds.nodeType(abc) != "AlembicNode":
            continue

        _safe_disconnect(abc + ".time")

        exp_name = _sanitize_name(abc) + "_hold_expr"
        if cmds.objExists(exp_name):
            try:
                cmds.delete(exp_name)
            except:
                pass

        cmds.expression(
            name=exp_name,
            s="%s.time = %s;" % (abc, rhs),
            ae=True,
            uc="all"
        )

def remove_hold(alembic_nodes):
    if not alembic_nodes:
        return

    for abc in alembic_nodes:
        if not cmds.objExists(abc) or cmds.nodeType(abc) != "AlembicNode":
            continue

        exp_name = _sanitize_name(abc) + "_hold_expr"
        if cmds.objExists(exp_name):
            try:
                cmds.delete(exp_name)
            except:
                pass

        src = cmds.listConnections(abc + ".time", s=True, d=False, p=True) or []
        if not src:
            try:
                cmds.connectAttr("time1.outTime", abc + ".time", force=True)
            except:
                pass


# ----------------------------
# Namespace + grouping helpers
# ----------------------------

def _ns_root_from_name(node_name):
    """
    Return left-most namespace segment:
      "SETS_env_city:foo:bar" -> "SETS_env_city"
      "node" -> None
    """
    if ":" in node_name:
        return node_name.split(":", 1)[0]
    return None

def _type_prefix(ns_root):
    """
    "CHAR_xx_xx" -> "CHAR"
    "SETS_env_city" -> "SETS"
    """
    if not ns_root or ns_root == "NO_NAMESPACE":
        return "NO_NAMESPACE"
    return ns_root.split("_", 1)[0]

def _infer_asset_namespace_from_alembicnode(abc_node):
    """
    Best-effort: infer namespace from the *driven* nodes (shapes/transforms).
    This fixes cases where AlembicNode is not namespaced but its outputs are.
    """
    candidates = []

    # Downstream connections (what the AlembicNode drives)
    downstream = cmds.listConnections(abc_node, s=False, d=True) or []

    # Keep likely driven scene nodes; ignore time/utility clutter
    ignore_types = set([
        "time", "unitConversion", "expression", "animCurveUU",
        "AlembicNode", "AlembicTimeControl"
    ])

    for n in downstream:
        if not cmds.objExists(n):
            continue
        t = cmds.nodeType(n)

        if t in ignore_types:
            continue

        # If it's a shape, check its transform too
        if t in ("mesh", "nurbsCurve", "nurbsSurface", "subdiv", "locator", "camera"):
            ns = _ns_root_from_name(n)
            if ns:
                candidates.append(ns)
            parents = cmds.listRelatives(n, parent=True, fullPath=False) or []
            for p in parents:
                ns2 = _ns_root_from_name(p)
                if ns2:
                    candidates.append(ns2)

        # If it's a transform, use it
        elif t == "transform":
            ns = _ns_root_from_name(n)
            if ns:
                candidates.append(ns)

    # Pick most common namespace among candidates
    if candidates:
        counts = {}
        for ns in candidates:
            counts[ns] = counts.get(ns, 0) + 1
        # sort by count desc, then name
        best = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        return best

    # Fallback: namespace on the AlembicNode itself (sometimes it has one)
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
        super(AlembicHoldOnNWindow, self).__init__(parent)
        self.setObjectName(self.WINDOW_NAME)
        self.setWindowTitle("Alembic Hold (On N)")
        self.setMinimumWidth(560)
        self.setMinimumHeight(620)

        self._build_ui()
        self.refresh_tree()

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        settings_group = QtWidgets.QGroupBox("Hold Settings")
        settings_layout = QtWidgets.QHBoxLayout(settings_group)

        self.hold_spin = QtWidgets.QSpinBox()
        self.hold_spin.setMinimum(1)
        self.hold_spin.setMaximum(120)
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

        # groups[type_prefix][namespace_root] = [(alembicNodeName, displayName)]
        groups = {}

        for abc in abc_nodes:
            ns_root = _infer_asset_namespace_from_alembicnode(abc)
            type_key = _type_prefix(ns_root)

            # Store the AlembicNode name; display shows inferred ns too
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
            if node and isinstance(node, basestring):
                nodes.append(node)
        out = []
        for n in nodes:
            if n not in out:
                out.append(n)
        return out

    def apply_to_selected(self):
        nodes = self._selected_alembic_nodes()
        hold_n = int(self.hold_spin.value())
        apply_hold(nodes, hold_n)
        cmds.inViewMessage(amg='Applied <hl>ON%d</hl> hold to %d AlembicNode(s).' % (hold_n, len(nodes)),
                           pos='topCenter', fade=True)

    def remove_from_selected(self):
        nodes = self._selected_alembic_nodes()
        remove_hold(nodes)
        cmds.inViewMessage(amg='Removed hold from %d AlembicNode(s).' % len(nodes),
                           pos='topCenter', fade=True)

    def apply_to_all(self):
        nodes = cmds.ls(type="AlembicNode") or []
        hold_n = int(self.hold_spin.value())
        apply_hold(nodes, hold_n)
        cmds.inViewMessage(amg='Applied <hl>ON%d</hl> hold to ALL (%d) AlembicNode(s).' % (hold_n, len(nodes)),
                           pos='topCenter', fade=True)

    def remove_from_all(self):
        nodes = cmds.ls(type="AlembicNode") or []
        remove_hold(nodes)
        cmds.inViewMessage(amg='Removed hold from ALL (%d) AlembicNode(s).' % len(nodes),
                           pos='topCenter', fade=True)

    def select_in_scene(self):
        nodes = self._selected_alembic_nodes()
        if nodes:
            cmds.select(nodes, r=True)
        else:
            cmds.select(clear=True)


def show_alembic_hold_on_n_ui():
    # close existing
    for w in QtWidgets.QApplication.allWidgets():
        if w.objectName() == AlembicHoldOnNWindow.WINDOW_NAME:
            try:
                w.close()
                w.deleteLater()
            except:
                pass

    dlg = AlembicHoldOnNWindow()
    dlg.show()
    return dlg


# Auto-execute when run directly (not when imported by plugin)
if __name__ == "__main__":
    show_alembic_hold_on_n_ui()
else:
    # When imported by plugin, just execute the function
    show_alembic_hold_on_n_ui()
