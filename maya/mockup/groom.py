# =============================================================================
# SWA Tools — Projection remap + Groom matcher (Anim → Groom)
# Groom-first scan; BLENDSHAPE LIVES ON GROOM; ANIM IS TARGET; weight = 1.0
# =============================================================================

import maya.cmds as cmds

# Qt imports (Maya 2020+ ships PySide2)
try:
    from PySide2 import QtWidgets, QtCore
    from shiboken2 import wrapInstance
except Exception:
    from PySide6 import QtWidgets, QtCore
    from shiboken6 import wrapInstance

import maya.OpenMayaUI as omui

WIN_TITLE  = "SWA Tools — Projection remap + Groom matcher"
WIN_OBJECT = "EE_Place3D_BS_Tools_Main"

# -----------------------------------------------------------------------------
# Common helpers
# -----------------------------------------------------------------------------

def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)

def _short(node):
    return node.split(":")[-1]

def _list_namespaces():
    ns = (cmds.namespaceInfo(listOnlyNamespaces=True) or [])
    bad = {"UI", "shared"}
    out = []
    for n in ns:
        if n in bad:
            continue
        if cmds.ls(n + ":*", long=True):
            out.append(n)
    return sorted(out, key=lambda x: (x.count(":"), x))

def _unlock_trs(node):
    for ch in ("translateX","translateY","translateZ",
               "rotateX","rotateY","rotateZ",
               "scaleX","scaleY","scaleZ"):
        a = "{}.{}".format(node, ch)
        if cmds.objExists(a):
            try:
                if cmds.getAttr(a, lock=True):
                    cmds.setAttr(a, lock=False)
                cmds.setAttr(a, keyable=True)
            except Exception:
                pass

def _first_mesh_shape(xform):
    """Return first non-intermediate mesh shape under transform."""
    shapes = cmds.listRelatives(xform, shapes=True, ni=True, fullPath=True) or []
    for s in shapes:
        if cmds.nodeType(s) == "mesh" and not cmds.getAttr(s + ".intermediateObject"):
            return s
    return None

# -----------------------------------------------------------------------------
# TAB 1: Place3D Linker logic (copy TRS + constraints)
# -----------------------------------------------------------------------------

def _delete_existing_constraints_on(node):
    cons = []
    for ctype in ("parentConstraint", "scaleConstraint"):
        cons += cmds.listRelatives(node, type=ctype, parent=False) or []
        cons += cmds.listConnections(node, s=True, d=False, type=ctype) or []
    for c in set(cons):
        try:
            cmds.delete(c)
        except Exception:
            pass

def _snap_trs_world(src_xform, dst_node, dry_run=False):
    """Copy TRS from src transform → dst place3dTexture (world T/R, local S)."""
    _unlock_trs(dst_node)
    t = cmds.xform(src_xform, q=True, ws=True, t=True)
    r = cmds.xform(src_xform, q=True, ws=True, ro=True)
    s = cmds.getAttr(src_xform + ".scale")[0]
    if dry_run:
        return "would-set T{} R{} S{}".format(
            [round(v,3) for v in t], [round(v,3) for v in r], [round(v,3) for v in s])
    try:
        cmds.xform(dst_node, ws=True, t=t)
        cmds.xform(dst_node, ws=True, ro=r)
        cmds.setAttr(dst_node + ".scale", *s, type="double3")
        return "snapped TRS"
    except Exception as e:
        return "error: {}".format(e)

def _parent_and_scale_constrain(src_xform, dst_node, force=False, dry_run=False):
    if dry_run:
        return "would parentConstraint -mo + scaleConstraint -mo"
    try:
        if force:
            _delete_existing_constraints_on(dst_node)
        if not cmds.listRelatives(dst_node, type="parentConstraint"):
            cmds.parentConstraint(src_xform, dst_node, mo=True,
                                  name="EE_{}_pcon".format(_short(dst_node)))
        if not cmds.listRelatives(dst_node, type="scaleConstraint"):
            cmds.scaleConstraint(src_xform, dst_node, mo=True,
                                 name="EE_{}_scon".format(_short(dst_node)))
        return "constrained"
    except Exception as e:
        return "error: {}".format(e)

def _find_place3d_pairs_by_place(shader_ns, geo_ns, place_suffix, geo_suffix, allow_fuzzy=True):
    """Key from place3dTexture (shader NS); match geo transform (geo NS)."""
    pairs = []
    places = cmds.ls(shader_ns + ":*", type="place3dTexture") or []
    geos   = cmds.ls(geo_ns   + ":*", type="transform") or []
    geo_map = { _short(g): g for g in geos }

    for p in places:
        sp = _short(p)
        base = sp[:-len(place_suffix)] if place_suffix and sp.endswith(place_suffix) else sp
        wanted = base + (geo_suffix or "")
        xform = geo_map.get(wanted)

        if not xform and allow_fuzzy:
            for s, full in geo_map.items():
                if (not geo_suffix and s.startswith(base)) or (geo_suffix and s.startswith(base) and s.endswith(geo_suffix)):
                    xform = full
                    break

        pairs.append({"place": p, "xform": xform, "base": base, "status": "ok" if xform else "missing"})
    return pairs

# -----------------------------------------------------------------------------
# TAB 2: BlendShape logic (Anim → Groom), groom-first scan
# -----------------------------------------------------------------------------

def _existing_blendShape_on(shape):
    """Return first blendShape node affecting this shape."""
    hist = cmds.listHistory(shape, pruneDagObjects=True) or []
    bs = [h for h in hist if cmds.nodeType(h) == "blendShape"]
    return bs[0] if bs else None

def _blendshape_anim_to_groom(anim_xform, groom_xform,
                              add_to_existing=True, create_if_missing=True,
                              force_delete_existing=False, dry_run=False):
    """
    Create/add blendShape where:
      Base (deformer lives): Groom mesh
      Target added:          Anim mesh
    Always sets the new/created target weight to 1.0.
    """
    anim_shape  = _first_mesh_shape(anim_xform)   # target
    groom_shape = _first_mesh_shape(groom_xform)  # base

    if not anim_shape or not groom_shape:
        return "no mesh shape (anim:{}, groom:{})".format(bool(anim_shape), bool(groom_shape))

    if dry_run:
        return "would BS: target={} -> base={}".format(_short(anim_shape), _short(groom_shape))

    bs = _existing_blendShape_on(groom_shape)  # BLENDSHAPE ON GROOM (BASE)

    try:
        if bs and force_delete_existing:
            cmds.delete(bs)
            bs = None
    except Exception:
        pass

    try:
        if not bs:
            if not create_if_missing:
                return "no BS on base (skipped)"
            bs_name = "BS_{}".format(_short(groom_xform))
            # Create blendShape on GROOM with ANIM as first target
            bs = cmds.blendShape(anim_shape, groom_shape, foc=True, name=bs_name, origin="world")[0]
            # ensure weight[0] = 1.0
            cmds.blendShape(bs, e=True, w=[(0, 1.0)])
            return "created {} (w0=1.0)".format(bs)

        if not add_to_existing:
            return "existing {} (skipped add)".format(bs)

        next_index = cmds.blendShape(bs, q=True, wc=True)
        # Add ANIM as new target on the blendShape that lives on GROOM
        cmds.blendShape(bs, e=True, t=(groom_shape, next_index, anim_shape, 1.0))
        cmds.setAttr("{}.weight[{}]".format(bs, next_index), 1.0)
        return "added target to {} (w{}=1.0)".format(bs, next_index)

    except Exception as e:
        return "error: {}".format(e)

def _pairs_groom_first(anim_ns, groom_ns, anim_suffix, groom_suffix, allow_fuzzy=True):
    """
    Scan GROOM transforms first (we only process what groom has).
    For each groom transform {base+groom_suffix}, find anim {base+anim_suffix}.
    """
    pairs = []
    groom_xforms = cmds.ls(groom_ns + ":*" + groom_suffix, type="transform") or []
    anim_xforms  = cmds.ls(anim_ns  + ":*" + anim_suffix,  type="transform") or []
    anim_map = { _short(a): a for a in anim_xforms }

    for groom in groom_xforms:
        sg = _short(groom)
        base = sg[:-len(groom_suffix)] if groom_suffix and sg.endswith(groom_suffix) else sg
        wanted = base + (anim_suffix or "")
        anim = anim_map.get(wanted)

        if not anim and allow_fuzzy:
            for s, full in anim_map.items():
                if (not anim_suffix and s.startswith(base)) or (anim_suffix and s.startswith(base) and s.endswith(anim_suffix)):
                    anim = full
                    break

        pairs.append({"groomXform": groom, "animXform": anim, "base": base, "status": "ok" if anim else "missing"})
    return pairs

# -----------------------------------------------------------------------------
# UI — Tabs
# -----------------------------------------------------------------------------

class Place3DTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Place3DTab, self).__init__(parent)
        self._build(); self._wire(); self._refresh_namespaces()

    def _build(self):
        layout = QtWidgets.QVBoxLayout(self)

        row_ns = QtWidgets.QHBoxLayout()
        self.geo_ns    = QtWidgets.QComboBox(); self.geo_ns.setEditable(True)
        self.shader_ns = QtWidgets.QComboBox(); self.shader_ns.setEditable(True)
        self.btn_refresh_ns = QtWidgets.QPushButton("↻")
        row_ns.addWidget(QtWidgets.QLabel("Geo NS"))
        row_ns.addWidget(self.geo_ns, 2)
        row_ns.addSpacing(10)
        row_ns.addWidget(QtWidgets.QLabel("Shader NS"))
        row_ns.addWidget(self.shader_ns, 2)
        row_ns.addWidget(self.btn_refresh_ns, 0)
        layout.addLayout(row_ns)

        row_suffix = QtWidgets.QHBoxLayout()
        self.edit_geo_suffix   = QtWidgets.QLineEdit("_Grp")
        self.edit_place_suffix = QtWidgets.QLineEdit("_Place3dTexture")
        row_suffix.addWidget(QtWidgets.QLabel("Geo Suffix"))
        row_suffix.addWidget(self.edit_geo_suffix)
        row_suffix.addSpacing(10)
        row_suffix.addWidget(QtWidgets.QLabel("Place3D Suffix"))
        row_suffix.addWidget(self.edit_place_suffix)
        layout.addLayout(row_suffix)

        row_opts = QtWidgets.QHBoxLayout()
        self.chk_dry_run = QtWidgets.QCheckBox("Dry Run"); self.chk_dry_run.setChecked(True)
        self.chk_force   = QtWidgets.QCheckBox("Force delete old constraints")
        self.chk_fuzzy   = QtWidgets.QCheckBox("Fuzzy match"); self.chk_fuzzy.setChecked(True)
        row_opts.addWidget(self.chk_dry_run); row_opts.addWidget(self.chk_force); row_opts.addWidget(self.chk_fuzzy); row_opts.addStretch(1)
        layout.addLayout(row_opts)

        row_btns = QtWidgets.QHBoxLayout()
        self.btn_scan  = QtWidgets.QPushButton("Scan (Place3D → Geo)")
        self.btn_apply = QtWidgets.QPushButton("Snap and constrain"); self.btn_apply.setStyleSheet("font-weight: bold;")
        row_btns.addStretch(1); row_btns.addWidget(self.btn_scan); row_btns.addWidget(self.btn_apply)
        layout.addLayout(row_btns)

        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["place3dTexture (Shader)", "Transform (Geo)", "Match", "Result"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        self.log = QtWidgets.QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMaximumHeight(140)
        layout.addWidget(self.log)

    def _wire(self):
        self.btn_refresh_ns.clicked.connect(self._refresh_namespaces)
        self.btn_scan.clicked.connect(self._do_scan)
        self.btn_apply.clicked.connect(self._do_apply)

    def _refresh_namespaces(self):
        ns = _list_namespaces()
        self.geo_ns.clear(); self.shader_ns.clear()
        self.geo_ns.addItems(ns); self.shader_ns.addItems(ns)
        for i in range(self.shader_ns.count()):
            if "Shade" in self.shader_ns.itemText(i):
                self.shader_ns.setCurrentIndex(i)

    def _log(self, msg): self.log.appendPlainText(msg)

    def _do_scan(self):
        geo_ns    = self.geo_ns.currentText().strip()
        shader_ns = self.shader_ns.currentText().strip()
        geo_suffix   = self.edit_geo_suffix.text()
        place_suffix = self.edit_place_suffix.text()
        fuzzy = self.chk_fuzzy.isChecked()

        if not geo_ns or not shader_ns:
            self._log("Select namespaces first.")
            return

        self.pairs = _find_place3d_pairs_by_place(shader_ns, geo_ns, place_suffix, geo_suffix, fuzzy)
        self._populate(self.pairs)
        missing = sum(1 for p in self.pairs if not p["xform"])
        self._log("Scan: {} place3dTexture, {} missing transforms".format(len(self.pairs), missing))

    def _populate(self, pairs):
        self.table.setRowCount(0)
        for p in pairs:
            r = self.table.rowCount(); self.table.insertRow(r)
            self.table.setItem(r,0,QtWidgets.QTableWidgetItem(p["place"]))
            self.table.setItem(r,1,QtWidgets.QTableWidgetItem(p["xform"] or "—"))
            match_item = QtWidgets.QTableWidgetItem("OK" if p["xform"] else "Missing")
            match_item.setForeground(QtCore.Qt.darkGreen if p["xform"] else QtCore.Qt.red)
            self.table.setItem(r,2,match_item)
            self.table.setItem(r,3,QtWidgets.QTableWidgetItem("-"))
        self.table.resizeColumnsToContents()

    def _do_apply(self):
        dry = self.chk_dry_run.isChecked()
        force = self.chk_force.isChecked()
        for r in range(self.table.rowCount()):
            place = self.table.item(r,0).text()
            xform = self.table.item(r,1).text()
            if xform == "—":
                self.table.item(r,3).setText("No transform"); continue
            s = _snap_trs_world(xform, place, dry)
            c = _parent_and_scale_constrain(xform, place, force, dry)
            res = "{} | {}".format(s, c)
            self.table.item(r,3).setText(res)
            self._log("{}  <--  {}  ::  {}".format(place, xform, res))
        self._log("=== Place3D Apply done (DryRun={}, Force={}) ===".format(dry, force))

# ---- BlendShape Tab (Anim → Groom; BASE=GROOM, TARGET=ANIM) -----------------

class BlendShapeTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(BlendShapeTab, self).__init__(parent)
        self._build(); self._wire(); self._refresh_namespaces()

    def _build(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Namespaces
        row_ns = QtWidgets.QHBoxLayout()
        self.anim_ns  = QtWidgets.QComboBox(); self.anim_ns.setEditable(True)
        self.groom_ns = QtWidgets.QComboBox(); self.groom_ns.setEditable(True)
        self.btn_refresh = QtWidgets.QPushButton("↻")
        row_ns.addWidget(QtWidgets.QLabel("Anim NS (Targets)"))
        row_ns.addWidget(self.anim_ns, 2)
        row_ns.addSpacing(10)
        row_ns.addWidget(QtWidgets.QLabel("Groom NS (Bases)"))
        row_ns.addWidget(self.groom_ns, 2)
        row_ns.addWidget(self.btn_refresh, 0)
        layout.addLayout(row_ns)

        # Suffixes
        row_suffix = QtWidgets.QHBoxLayout()
        self.anim_suffix  = QtWidgets.QLineEdit("_Geo")
        self.groom_suffix = QtWidgets.QLineEdit("_GroomGeo")
        row_suffix.addWidget(QtWidgets.QLabel("Anim Suffix"))
        row_suffix.addWidget(self.anim_suffix)
        row_suffix.addSpacing(10)
        row_suffix.addWidget(QtWidgets.QLabel("Groom Suffix"))
        row_suffix.addWidget(self.groom_suffix)
        layout.addLayout(row_suffix)

        # Options
        row_opts = QtWidgets.QHBoxLayout()
        self.chk_dry    = QtWidgets.QCheckBox("Dry Run"); self.chk_dry.setChecked(True)
        self.chk_add    = QtWidgets.QCheckBox("Add to existing BS"); self.chk_add.setChecked(True)
        self.chk_create = QtWidgets.QCheckBox("Create if missing"); self.chk_create.setChecked(True)
        self.chk_force  = QtWidgets.QCheckBox("Force delete existing BS on base")
        self.chk_fuzzy  = QtWidgets.QCheckBox("Fuzzy match"); self.chk_fuzzy.setChecked(True)
        row_opts.addWidget(self.chk_dry); row_opts.addWidget(self.chk_add); row_opts.addWidget(self.chk_create)
        row_opts.addWidget(self.chk_force); row_opts.addWidget(self.chk_fuzzy); row_opts.addStretch(1)
        layout.addLayout(row_opts)

        # Buttons
        row_btns = QtWidgets.QHBoxLayout()
        self.btn_scan  = QtWidgets.QPushButton("Scan (Groom-first: Anim → Groom)")
        self.btn_apply = QtWidgets.QPushButton("Create/Add BlendShapes"); self.btn_apply.setStyleSheet("font-weight: bold;")
        row_btns.addStretch(1); row_btns.addWidget(self.btn_scan); row_btns.addWidget(self.btn_apply)
        layout.addLayout(row_btns)

        # Table
        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Groom Transform (Base)", "Anim Transform (Target)", "Match", "Action", "Result"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        # Log
        self.log = QtWidgets.QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMaximumHeight(140)
        layout.addWidget(self.log)

    def _wire(self):
        self.btn_refresh.clicked.connect(self._refresh_namespaces)
        self.btn_scan.clicked.connect(self._do_scan)
        self.btn_apply.clicked.connect(self._do_apply)

    def _refresh_namespaces(self):
        ns = _list_namespaces()
        self.anim_ns.clear(); self.groom_ns.clear()
        self.anim_ns.addItems(ns); self.groom_ns.addItems(ns)
        for i in range(self.groom_ns.count()):
            if "Groom" in self.groom_ns.itemText(i):
                self.groom_ns.setCurrentIndex(i)

    def _log(self, msg): self.log.appendPlainText(msg)

    def _do_scan(self):
        anim_ns  = self.anim_ns.currentText().strip()
        groom_ns = self.groom_ns.currentText().strip()
        asuf = self.anim_suffix.text()
        gsuf = self.groom_suffix.text()
        fuzzy = self.chk_fuzzy.isChecked()

        if not anim_ns or not groom_ns:
            self._log("Select Anim and Groom namespaces first."); return

        # Groom-first scan
        self.pairs = _pairs_groom_first(anim_ns, groom_ns, asuf, gsuf, fuzzy)
        self._populate(self.pairs)

        missing = sum(1 for p in self.pairs if not p["animXform"])
        self._log("Scan: {} groom candidates, {} missing anim matches".format(len(self.pairs), missing))

    def _populate(self, pairs):
        self.table.setRowCount(0)
        for p in pairs:
            r = self.table.rowCount(); self.table.insertRow(r)
            self.table.setItem(r,0,QtWidgets.QTableWidgetItem(p["groomXform"]))
            self.table.setItem(r,1,QtWidgets.QTableWidgetItem(p["animXform"] or "—"))
            match_item = QtWidgets.QTableWidgetItem("OK" if p["animXform"] else "Missing")
            match_item.setForeground(QtCore.Qt.darkGreen if p["animXform"] else QtCore.Qt.red)
            self.table.setItem(r,2,match_item)

            act = "Add to existing" if self.chk_add.isChecked() else "Create new"
            if not self.chk_create.isChecked():
                act = "Add only (no create)"
            if self.chk_force.isChecked():
                act += " | Force delete existing"
            self.table.setItem(r,3,QtWidgets.QTableWidgetItem(act))

            self.table.setItem(r,4,QtWidgets.QTableWidgetItem("-"))
        self.table.resizeColumnsToContents()

    def _do_apply(self):
        dry    = self.chk_dry.isChecked()
        add    = self.chk_add.isChecked()
        create = self.chk_create.isChecked()
        force  = self.chk_force.isChecked()

        for r in range(self.table.rowCount()):
            groom = self.table.item(r,0).text()  # base (blendShape lives here)
            anim  = self.table.item(r,1).text()  # target
            if anim == "—":
                self.table.item(r,4).setText("No anim match"); continue

            res = _blendshape_anim_to_groom(
                anim_xform=anim,
                groom_xform=groom,
                add_to_existing=add,
                create_if_missing=create,
                force_delete_existing=force,
                dry_run=dry
            )
            self.table.item(r,4).setText(res)
            self._log("{}  (base=groom)  ←  {}  (target=anim)  ::  {}".format(groom, anim, res))

        self._log("=== BlendShape Apply done (DryRun={}, Add={}, Create={}, Force={}) ==="
                  .format(dry, add, create, force))

# -----------------------------------------------------------------------------
# Main window
# -----------------------------------------------------------------------------

class MainTools(QtWidgets.QDialog):
    def __init__(self, parent=_maya_main_window()):
        # ensure single instance
        for w in QtWidgets.QApplication.topLevelWidgets():
            if w.objectName() == WIN_OBJECT:
                w.close(); w.deleteLater()

        super(MainTools, self).__init__(parent)
        self.setObjectName(WIN_OBJECT)
        self.setWindowTitle(WIN_TITLE)
        self.setMinimumWidth(980)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(Place3DTab(), "Place3D Linker")
        tabs.addTab(BlendShapeTab(), "BlendShape Builder (Anim → Groom)")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(tabs)

def show():
    dlg = MainTools()
    dlg.show()
    return dlg

show()
