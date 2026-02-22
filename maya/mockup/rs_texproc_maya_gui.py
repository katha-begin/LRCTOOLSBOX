# rs_texproc_maya_gui.py
# -*- coding: utf-8 -*-
"""
Maya GUI: Batch convert textures using Redshift Texture Processor.

Features:
- Output saved next to source by default (no -path).
- OCIO config path from env OCIO, with default fallback.
- Use OCIO file_rules (-useociorules) OR GUI rule mapping (-cs per file).
- Skip if output exists (default ON). If OFF, force with -noskip.
"""

import os
import fnmatch
import subprocess
from pathlib import Path

import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui

DEFAULT_OCIO = "T:/pipeline/ocio/aces_2.0/studio-config-v1.0.0_aces-v1.3_ocio-v2.0.ocio"

# Default rules for colorspace mapping
DEFAULT_RULES = [
    # name,        glob pattern,           extensions,           colorspace (must exist in active config)
    ("DIFFUSE",    "*[dD]iffuse*",         "*",                  "Utility - sRGB - Texture"),
    ("BASECOLOR",  "*[bB]ase[cC]olor*",    "*",                  "Utility - sRGB - Texture"),
    ("EMISSIVE",   "*[eE]missive*",        "*",                  "Utility - sRGB - Texture"),
    ("MATTPAINT",  "*",                    "jpg jpeg",           "Utility - sRGB - Texture"),
    ("EXR",        "*",                    "exr",                "ACES - ACEScg"),
    ("HDR",        "*",                    "hdr",                "Utility - Linear - Rec.709"),
    ("Default",    "*",                    "*",                  "Utility - Raw"),
]

# Texture node types and their file attributes (from tex_dedup.py)
TEXTURE_NODE_TYPES = {
    'file': 'fileTextureName',
    'aiImage': 'filename',
    'RedshiftNormalMap': 'tex0',
    'RedshiftSprite': 'tex0',
    'RedshiftDomeLight': 'tex0',
    'PxrTexture': 'filename',
    'PxrNormalMap': 'filename',
}


def _norm(p: str) -> str:
    """Normalize path to use forward slashes."""
    return p.replace("\\", "/")


def _path_exists(p: str) -> bool:
    """Check if path exists, handling both forward and backslashes."""
    if not p:
        return False
    # Convert to OS-native path for os.path.exists()
    return os.path.exists(p.replace("/", os.sep))


def _ocio_from_env_or_default() -> str:
    ocio = (os.environ.get("OCIO") or "").strip()
    return ocio if ocio else DEFAULT_OCIO


def _guess_texproc_exe() -> str:
    # Common Win locations; user can browse if different
    candidates = [
        r"C:\ProgramData\Redshift\bin\redshiftTextureProcessor.exe",
        r"C:\ProgramData\redshift\bin\redshiftTextureProcessor.exe",
        r"C:\ProgramData\Redshift\bin\redshiftTextureProcessor",
        r"C:\ProgramData\redshift\bin\redshiftTextureProcessor",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return ""


def _collect_files(inputs: list, recursive: bool) -> list:
    """Collect files from inputs, handling UDIM and other special placeholders."""
    out = []
    for it in inputs:
        if not it:
            continue

        # Check if path contains UDIM placeholder - expand to actual tiles
        if "<UDIM>" in it or "<udim>" in it:
            tiles = _expand_udim_tiles(it)
            if tiles:
                out.extend(tiles)
            else:
                # No tiles found, log warning but continue
                print(f"Warning: No UDIM tiles found for pattern: {it}")
            continue

        # Handle other placeholders (just add as-is for now)
        if "<tile>" in it or "<TILE>" in it:
            out.append(_norm(it))
            continue

        try:
            p = Path(it)
            if p.is_file():
                out.append(str(p))
            elif p.is_dir():
                if recursive:
                    out.extend([str(f) for f in p.rglob("*") if f.is_file()])
                else:
                    out.extend([str(f) for f in p.glob("*") if f.is_file()])
        except (OSError, ValueError):
            # If pathlib can't handle the path (invalid characters, etc.),
            # check if it's a valid file path using os.path
            if os.path.isfile(it):
                out.append(_norm(it))
            elif os.path.isdir(it):
                if recursive:
                    for root, dirs, files in os.walk(it):
                        for f in files:
                            out.append(_norm(os.path.join(root, f)))
                else:
                    for f in os.listdir(it):
                        full_path = os.path.join(it, f)
                        if os.path.isfile(full_path):
                            out.append(_norm(full_path))

    # de-dupe preserving order
    seen = set()
    uniq = []
    for f in out:
        k = os.path.normcase(os.path.abspath(f))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(f)
    return uniq


def _expand_udim_tiles(udim_path: str) -> list:
    """
    Expand UDIM pattern to actual tile files.
    E.g., 'texture_<UDIM>.png' -> ['texture_1001.png', 'texture_1002.png', ...]

    Returns list of existing tile files, or empty list if no tiles found.
    """
    if "<UDIM>" not in udim_path and "<udim>" not in udim_path:
        return []

    # Replace UDIM placeholder with wildcard pattern
    pattern = udim_path.replace("<UDIM>", "????").replace("<udim>", "????")

    # Convert to OS-native path for glob operations
    pattern_native = pattern.replace("/", os.sep)

    # Get directory and pattern
    dir_path = os.path.dirname(pattern_native)
    file_pattern = os.path.basename(pattern_native)

    if not dir_path:
        dir_path = "."

    if not os.path.isdir(dir_path):
        return []

    # Find all matching files
    import glob
    matching_files = glob.glob(os.path.join(dir_path, file_pattern))

    # Normalize results back to forward slashes
    return sorted([_norm(f) for f in matching_files])


def _match_rule_colorspace(filepath: str, rules=None) -> str:
    """Apply RULES (glob over basename/stem) with extension constraints."""
    if rules is None:
        rules = DEFAULT_RULES

    p = Path(filepath)
    basename = p.name
    stem = p.stem
    ext = p.suffix.lower().lstrip(".")

    for rule_name, pattern, exts, cs in rules:
        exts_norm = exts.strip().lower()

        # extension filter
        if exts_norm != "*":
            allowed = set(exts_norm.split())
            if ext not in allowed:
                continue

        # glob match
        if fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(stem, pattern):
            return cs

    return "Utility - Raw"


def _expected_rstexbin_path(src_file: str, out_dir: str = "") -> str:
    """
    Predict output .rstexbin path.
    If out_dir empty -> next to source: <src_stem>.rstexbin (replaces extension)
    If out_dir set  -> <out_dir>/<src_stem>.rstexbin
    """
    src = Path(src_file)
    # Replace extension with .rstexbin (e.g., texture.jpeg -> texture.rstexbin)
    rstexbin_name = src.stem + ".rstexbin"

    if out_dir:
        return _norm(str(Path(out_dir) / rstexbin_name))
    return _norm(str(src.parent / rstexbin_name))


def _build_cmd(texproc_exe: str, in_file: str, ocio_file: str,
               use_ocio_rules: bool, out_dir: str,
               colorspace: str, write_log: bool, force: bool) -> list:
    """
    Build redshiftTextureProcessor command.
    - If out_dir empty => omit -path => output next to source.
    - If force True => pass -noskip (reprocess).
    """
    texproc_exe = _norm(texproc_exe)
    in_file = _norm(in_file)
    ocio_file = _norm(ocio_file)

    ocio_dir = _norm(str(Path(ocio_file).parent))

    cmd = [texproc_exe, in_file]

    if out_dir:
        cmd += ["-path", _norm(out_dir)]

    # OCIO: doc uses -ociopath as folder; env OCIO as file also works.
    cmd += ["-ociopath", ocio_dir]

    if use_ocio_rules:
        cmd += ["-useociorules"]
    else:
        cmd += ["-cs", colorspace]

    if write_log:
        cmd += ["-log"]

    if force:
        cmd += ["-noskip"]

    return cmd


def _scan_scene_textures():
    """
    Scan the entire Maya scene for all texture files.
    Returns list of tuples: (texture_path, node_name, node_type, has_rstexbin)
    """
    textures = []
    seen_paths = set()

    for node_type, attr_name in TEXTURE_NODE_TYPES.items():
        try:
            nodes = cmds.ls(type=node_type) or []
            for node in nodes:
                full_attr = f"{node}.{attr_name}"

                if not cmds.objExists(full_attr):
                    continue

                try:
                    tex_path = cmds.getAttr(full_attr) or ""
                except:
                    tex_path = ""

                if not tex_path:
                    continue

                # Normalize path
                tex_path_norm = _norm(tex_path)

                # Check if already seen
                path_key = os.path.normcase(os.path.abspath(tex_path_norm))
                if path_key in seen_paths:
                    continue
                seen_paths.add(path_key)

                # Check if .rstexbin exists (use expected output path logic)
                rstexbin_path = _expected_rstexbin_path(tex_path_norm, out_dir="")
                has_rstexbin = _path_exists(rstexbin_path)

                textures.append((tex_path_norm, node, node_type, has_rstexbin))

        except Exception as e:
            print(f"Error scanning {node_type}: {e}")
            continue

    return textures


class ConversionWorker(QtCore.QThread):
    """Worker thread for running texture conversions without freezing Maya."""

    # Signals
    progress_updated = QtCore.Signal(int, int, str)  # current, total, message
    conversion_finished = QtCore.Signal(int, int)  # success_count, total_count
    log_message = QtCore.Signal(str)  # log message

    def __init__(self, plan, env, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.env = env
        self.to_run = [x for x in plan if not x["skipped"]]
        self._is_cancelled = False

    def cancel(self):
        """Cancel the conversion process."""
        self._is_cancelled = True

    def run(self):
        """Run the conversion process in a separate thread."""
        ok = 0
        total = len(self.to_run)

        self.log_message.emit("\n--- RUN ---")
        self.log_message.emit(f"Running: {total} | Skipping: {len(self.plan)-total}")

        for idx, item in enumerate(self.to_run):
            if self._is_cancelled:
                self.log_message.emit("\n[ERROR] Conversion cancelled by user.")
                break

            cmdline = item["cmd"]
            src_file = item["src"]

            # Update progress
            self.progress_updated.emit(idx + 1, total, f"Processing: {os.path.basename(src_file)}")

            try:
                startupinfo = None
                if os.name == "nt":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                res = subprocess.run(
                    cmdline,
                    env=self.env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    startupinfo=startupinfo,
                )

                out = (res.stdout or "").strip()
                if out:
                    self.log_message.emit(out)

                if res.returncode == 0:
                    ok += 1
                    self.log_message.emit(f"[OK] [{idx+1}/{total}] {os.path.basename(src_file)}")
                else:
                    self.log_message.emit(f"[ERROR] return code {res.returncode} | {src_file}")

            except Exception as e:
                self.log_message.emit(f"[ERROR] running command: {e}")

        self.log_message.emit(f"\n[OK] Done. Success: {ok}/{total}")
        self.conversion_finished.emit(ok, total)


class RSTextureProcessorMayaUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Redshift Texture Processor Batch (Maya)")
        self.setMinimumWidth(860)

        # --- Paths ---
        self.ed_texproc = QtWidgets.QLineEdit(_guess_texproc_exe())
        self.btn_texproc = QtWidgets.QPushButton("Browse…")

        self.ed_ocio = QtWidgets.QLineEdit(_ocio_from_env_or_default())
        self.btn_ocio = QtWidgets.QPushButton("Browse…")

        # --- Mode ---
        self.rb_ocio = QtWidgets.QRadioButton("Use OCIO file_rules (-useociorules)  [recommended]")
        self.rb_gui = QtWidgets.QRadioButton("Use GUI RULES (map → -cs per file)")
        self.rb_ocio.setChecked(True)

        # --- Output behavior (default next to source) ---
        self.chk_custom_out = QtWidgets.QCheckBox("Custom output folder (-path)")
        self.chk_custom_out.setChecked(False)
        self.ed_out = QtWidgets.QLineEdit("")
        self.ed_out.setEnabled(False)
        self.btn_out = QtWidgets.QPushButton("Browse…")
        self.btn_out.setEnabled(False)
        self.lbl_out_hint = QtWidgets.QLabel("Default: output is saved next to the source image.")

        # --- Options ---
        self.chk_recursive = QtWidgets.QCheckBox("Recursive (folders)")
        self.chk_recursive.setChecked(True)

        # Simplified skip checkbox (checked = skip, unchecked = force with -noskip)
        self.chk_skip_exist = QtWidgets.QCheckBox("Skip if .rstexbin already exists")
        self.chk_skip_exist.setChecked(True)  # <-- default skip ON
        self.chk_skip_exist.setToolTip("When checked: skip existing files. When unchecked: force reprocess with -noskip")

        self.chk_log = QtWidgets.QCheckBox("Write log (-log)")
        self.chk_log.setChecked(True)

        # --- Update Scene Option ---
        self.chk_update_scene = QtWidgets.QCheckBox("Update scene file nodes to .rstexbin after conversion")
        self.chk_update_scene.setChecked(False)
        self.chk_update_scene.setToolTip("After conversion, update Maya file nodes to point to .rstexbin files")

        # --- Inputs Table (replaces list widget) ---
        self.table_inputs = QtWidgets.QTableWidget()
        self.table_inputs.setColumnCount(5)
        self.table_inputs.setHorizontalHeaderLabels(["Texture Path", "Node", "Type", "Tiles", ".rstexbin"])
        self.table_inputs.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table_inputs.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table_inputs.setAlternatingRowColors(True)
        self.table_inputs.horizontalHeader().setStretchLastSection(False)
        self.table_inputs.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table_inputs.setColumnWidth(1, 150)
        self.table_inputs.setColumnWidth(2, 100)
        self.table_inputs.setColumnWidth(3, 80)
        self.table_inputs.setColumnWidth(4, 80)

        # Enable right-click context menu
        self.table_inputs.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_inputs.customContextMenuRequested.connect(self._on_table_context_menu)

        self.btn_add_files = QtWidgets.QPushButton("Add Files…")
        self.btn_add_folder = QtWidgets.QPushButton("Add Folder…")
        self.btn_add_from_scene = QtWidgets.QPushButton("Add From Scene (All Textures)")
        self.btn_remove = QtWidgets.QPushButton("Remove Selected")
        self.btn_clear = QtWidgets.QPushButton("Clear")

        # --- Actions ---
        self.btn_preview = QtWidgets.QPushButton("Preview")
        self.btn_run = QtWidgets.QPushButton("Run Conversion")
        self.btn_cancel = QtWidgets.QPushButton("Cancel")
        self.btn_cancel.setEnabled(False)

        # --- Progress Bar ---
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.lbl_progress = QtWidgets.QLabel("")
        self.lbl_progress.setVisible(False)

        self.txt_log = QtWidgets.QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(240)

        # Worker thread
        self.worker = None

        # Rules (start with defaults, can be edited in Rules tab)
        self.rules = list(DEFAULT_RULES)

        # --- Create Tab Widget ---
        self.tab_widget = QtWidgets.QTabWidget()

        # Main Tab
        main_tab = QtWidgets.QWidget()
        self._create_main_tab_layout(main_tab)
        self.tab_widget.addTab(main_tab, "Conversion")

        # Rules Tab
        rules_tab = QtWidgets.QWidget()
        self._create_rules_tab_layout(rules_tab)
        self.tab_widget.addTab(rules_tab, "Rules Config")

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)

        # --- Signals ---
        self.btn_texproc.clicked.connect(self._browse_texproc)
        self.btn_ocio.clicked.connect(self._browse_ocio)
        self.chk_custom_out.toggled.connect(self._toggle_out)
        self.btn_out.clicked.connect(self._browse_out)

        self.btn_add_files.clicked.connect(self._add_files)
        self.btn_add_folder.clicked.connect(self._add_folder)
        self.btn_add_from_scene.clicked.connect(self._add_from_scene)
        self.btn_remove.clicked.connect(self._remove_selected)
        self.btn_clear.clicked.connect(self._clear_table)

        self.btn_preview.clicked.connect(self._preview)
        self.btn_run.clicked.connect(self._run)
        self.btn_cancel.clicked.connect(self._cancel_conversion)

    def _create_main_tab_layout(self, parent):
        """Create the main conversion tab layout."""
        form = QtWidgets.QFormLayout()

        row1 = QtWidgets.QHBoxLayout()
        row1.addWidget(self.ed_texproc)
        row1.addWidget(self.btn_texproc)
        form.addRow("redshiftTextureProcessor:", row1)

        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(self.ed_ocio)
        row2.addWidget(self.btn_ocio)
        form.addRow("OCIO config (.ocio):", row2)

        modes = QtWidgets.QHBoxLayout()
        modes.addWidget(self.rb_ocio)
        modes.addWidget(self.rb_gui)
        form.addRow("Mode:", modes)

        outrow = QtWidgets.QHBoxLayout()
        outrow.addWidget(self.chk_custom_out)
        outrow.addWidget(self.ed_out)
        outrow.addWidget(self.btn_out)
        form.addRow("Output:", outrow)
        form.addRow("", self.lbl_out_hint)

        opts = QtWidgets.QHBoxLayout()
        opts.addWidget(self.chk_recursive)
        opts.addStretch(1)
        opts.addWidget(self.chk_skip_exist)
        opts.addWidget(self.chk_log)
        form.addRow("Options:", opts)

        # Update scene option
        form.addRow("", self.chk_update_scene)

        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(self.btn_add_files)
        btns.addWidget(self.btn_add_folder)
        btns.addWidget(self.btn_add_from_scene)
        btns.addWidget(self.btn_remove)
        btns.addWidget(self.btn_clear)
        btns.addStretch(1)
        btns.addWidget(self.btn_preview)
        btns.addWidget(self.btn_run)
        btns.addWidget(self.btn_cancel)

        main = QtWidgets.QVBoxLayout(parent)
        main.addLayout(form)
        main.addWidget(QtWidgets.QLabel("Inputs:"))
        main.addWidget(self.table_inputs)
        main.addLayout(btns)

        # Progress section
        main.addWidget(self.lbl_progress)
        main.addWidget(self.progress_bar)
        main.addWidget(QtWidgets.QLabel("Log / Preview:"))
        main.addWidget(self.txt_log)

    def _create_rules_tab_layout(self, parent):
        """Create the rules configuration tab layout."""
        # Rules table
        self.table_rules = QtWidgets.QTableWidget()
        self.table_rules.setColumnCount(4)
        self.table_rules.setHorizontalHeaderLabels(["Name", "Glob Pattern", "Extensions", "Colorspace"])
        self.table_rules.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table_rules.setAlternatingRowColors(True)
        self.table_rules.horizontalHeader().setStretchLastSection(True)
        self.table_rules.setColumnWidth(0, 120)
        self.table_rules.setColumnWidth(1, 150)
        self.table_rules.setColumnWidth(2, 100)

        # Populate with default rules
        self._populate_rules_table()

        # Buttons
        btn_add_rule = QtWidgets.QPushButton("Add Rule")
        btn_remove_rule = QtWidgets.QPushButton("Remove Selected")
        btn_reset_rules = QtWidgets.QPushButton("Reset to Defaults")
        btn_move_up = QtWidgets.QPushButton("Move Up")
        btn_move_down = QtWidgets.QPushButton("Move Down")

        btn_add_rule.clicked.connect(self._add_rule)
        btn_remove_rule.clicked.connect(self._remove_rule)
        btn_reset_rules.clicked.connect(self._reset_rules)
        btn_move_up.clicked.connect(self._move_rule_up)
        btn_move_down.clicked.connect(self._move_rule_down)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(btn_add_rule)
        btn_layout.addWidget(btn_remove_rule)
        btn_layout.addWidget(btn_move_up)
        btn_layout.addWidget(btn_move_down)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_reset_rules)

        info_label = QtWidgets.QLabel(
            "Rules are applied in order from top to bottom. First matching rule wins.\n"
            "Use '*' for any pattern/extension. Glob patterns: * (any), ? (single char), [abc] (char set)"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")

        layout = QtWidgets.QVBoxLayout(parent)
        layout.addWidget(info_label)
        layout.addWidget(self.table_rules)
        layout.addLayout(btn_layout)

    # ---------- helpers ----------
    def _log(self, msg: str):
        self.txt_log.appendPlainText(msg)

    def _toggle_out(self, on: bool):
        self.ed_out.setEnabled(on)
        self.btn_out.setEnabled(on)
        if not on:
            self.ed_out.setText("")

    def _browse_texproc(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select redshiftTextureProcessor", "", "Executable (*)")
        if p:
            self.ed_texproc.setText(_norm(p))

    def _browse_ocio(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select OCIO config", "", "OCIO config (*.ocio)")
        if p:
            self.ed_ocio.setText(_norm(p))

    def _browse_out(self):
        p = QtWidgets.QFileDialog.getExistingDirectory(self, "Select output folder")
        if p:
            self.ed_out.setText(_norm(p))

    def _add_files(self):
        """Add files from file dialog."""
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Add textures", "", "Images (*.*)")
        for f in files:
            self._add_texture_to_table(_norm(f), "", "manual", False)

    def _add_folder(self):
        """Add folder path to table (will be expanded during collection)."""
        p = QtWidgets.QFileDialog.getExistingDirectory(self, "Add folder")
        if p:
            self._add_texture_to_table(_norm(p), "", "folder", False)

    def _add_from_scene(self):
        """Scan entire Maya scene for ALL texture files."""
        self._log("Scanning scene for textures...")

        textures = _scan_scene_textures()

        if not textures:
            self._log("No textures found in scene.")
            return

        # Add to table
        for tex_path, node, node_type, has_rstexbin in textures:
            self._add_texture_to_table(tex_path, node, node_type, has_rstexbin)

        self._log(f"Added {len(textures)} textures from scene (all node types).")

    def _add_texture_to_table(self, path, node, node_type, has_rstexbin):
        """Add a texture entry to the table."""
        # Check if already exists
        for row in range(self.table_inputs.rowCount()):
            if self.table_inputs.item(row, 0).text() == path:
                return  # Already exists

        row = self.table_inputs.rowCount()
        self.table_inputs.insertRow(row)

        # Check if this is a UDIM pattern
        is_udim = "<UDIM>" in path or "<udim>" in path

        # Get tile count
        tile_count = 0
        if is_udim:
            tiles = _expand_udim_tiles(path)
            tile_count = len(tiles)

        # Display path (without tile count in path column)
        self.table_inputs.setItem(row, 0, QtWidgets.QTableWidgetItem(path))
        self.table_inputs.setItem(row, 1, QtWidgets.QTableWidgetItem(node))

        # Show node type with UDIM indicator
        node_type_display = f"{node_type} (UDIM)" if is_udim else node_type
        self.table_inputs.setItem(row, 2, QtWidgets.QTableWidgetItem(node_type_display))

        # Tiles column: show count for UDIM, empty for regular textures
        if is_udim:
            tiles_item = QtWidgets.QTableWidgetItem(str(tile_count))
            tiles_item.setTextAlignment(QtCore.Qt.AlignCenter)
            tiles_item.setForeground(QtGui.QColor(100, 150, 200))  # Blue for UDIM
        else:
            tiles_item = QtWidgets.QTableWidgetItem("-")
            tiles_item.setTextAlignment(QtCore.Qt.AlignCenter)
            tiles_item.setForeground(QtGui.QColor(150, 150, 150))  # Gray for non-UDIM

        self.table_inputs.setItem(row, 3, tiles_item)

        # .rstexbin status column
        status_item = QtWidgets.QTableWidgetItem("YES" if has_rstexbin else "NO")
        status_item.setTextAlignment(QtCore.Qt.AlignCenter)
        if has_rstexbin:
            status_item.setForeground(QtGui.QColor(0, 150, 0))  # Green
        else:
            status_item.setForeground(QtGui.QColor(200, 0, 0))  # Red

        self.table_inputs.setItem(row, 4, status_item)

    def _clear_table(self):
        """Clear all entries from the table."""
        self.table_inputs.setRowCount(0)

    def _refresh_table_status(self):
        """Refresh .rstexbin status for all textures in the table."""
        # Get current output directory setting
        out_dir = self.ed_out.text().strip() if self.chk_custom_out.isChecked() else ""

        for row in range(self.table_inputs.rowCount()):
            texture_path = self.table_inputs.item(row, 0).text()

            # Check if UDIM pattern
            is_udim = "<UDIM>" in texture_path or "<udim>" in texture_path

            if is_udim:
                # For UDIM, expand tiles and check if .rstexbin exists next to each tile
                tiles = _expand_udim_tiles(texture_path)
                rstexbin_count = 0

                for tile in tiles:
                    # Simple: replace extension with .rstexbin
                    # E.g., catStompyBody_SheenRoughness_1001.png -> catStompyBody_SheenRoughness_1001.rstexbin
                    tile_path = Path(tile)
                    rstexbin_file = tile_path.parent / (tile_path.stem + ".rstexbin")
                    rstexbin_path = _norm(str(rstexbin_file))

                    if _path_exists(rstexbin_path):
                        rstexbin_count += 1

                # Update status: show count of converted tiles
                status_text = f"{rstexbin_count}/{len(tiles)}"
                status_item = QtWidgets.QTableWidgetItem(status_text)
                status_item.setTextAlignment(QtCore.Qt.AlignCenter)

                # Color based on conversion progress
                if rstexbin_count == len(tiles):
                    status_item.setForeground(QtGui.QColor(0, 150, 0))  # Green - all done
                elif rstexbin_count > 0:
                    status_item.setForeground(QtGui.QColor(200, 150, 0))  # Orange - partial
                else:
                    status_item.setForeground(QtGui.QColor(200, 0, 0))  # Red - none done
            else:
                # For regular textures, check expected output path
                expected_output = _expected_rstexbin_path(texture_path, out_dir=out_dir)
                has_rstexbin = _path_exists(expected_output)
                status_text = "YES" if has_rstexbin else "NO"
                status_item = QtWidgets.QTableWidgetItem(status_text)
                status_item.setTextAlignment(QtCore.Qt.AlignCenter)

                if has_rstexbin:
                    status_item.setForeground(QtGui.QColor(0, 150, 0))  # Green
                else:
                    status_item.setForeground(QtGui.QColor(200, 0, 0))  # Red

            self.table_inputs.setItem(row, 4, status_item)

    def _on_table_context_menu(self, pos):
        """Handle right-click context menu on table."""
        item = self.table_inputs.itemAt(pos)
        if not item:
            return

        row = item.row()
        texture_path = self.table_inputs.item(row, 0).text()

        # Create context menu
        menu = QtWidgets.QMenu(self)

        # Inspect action
        action_inspect = menu.addAction("Inspect Texture")
        action_inspect.triggered.connect(lambda: self._inspect_texture(texture_path))

        # Open folder action
        action_open_folder = menu.addAction("Open Folder")
        action_open_folder.triggered.connect(lambda: self._open_texture_folder(texture_path))

        # Show UDIM tiles action (only for UDIM textures)
        if "<UDIM>" in texture_path or "<udim>" in texture_path:
            menu.addSeparator()
            action_show_tiles = menu.addAction("Show UDIM Tiles")
            action_show_tiles.triggered.connect(lambda: self._show_udim_tiles(texture_path))

        # Show menu at cursor position
        menu.exec_(self.table_inputs.mapToGlobal(pos))

    def _inspect_texture(self, texture_path):
        """Open texture inspection window."""
        self._log(f"\n--- TEXTURE INSPECTION ---")
        self._log(f"Path: {texture_path}")

        # Get current output directory setting
        out_dir = self.ed_out.text().strip() if self.chk_custom_out.isChecked() else ""

        # Check if UDIM
        is_udim = "<UDIM>" in texture_path or "<udim>" in texture_path

        if is_udim:
            tiles = _expand_udim_tiles(texture_path)
            self._log(f"Type: UDIM Pattern")
            self._log(f"Tiles Found: {len(tiles)}")
            if tiles:
                self._log(f"\nTile Files:")
                for tile in tiles:
                    exists = "[OK]" if _path_exists(tile) else "[X]"
                    size = os.path.getsize(tile.replace("/", os.sep)) if _path_exists(tile) else 0
                    size_mb = size / (1024 * 1024)
                    self._log(f"  {exists} {os.path.basename(tile)} ({size_mb:.2f} MB)")
        else:
            # Regular texture
            self._log(f"Type: Single Texture")
            if _path_exists(texture_path):
                size = os.path.getsize(texture_path.replace("/", os.sep))
                size_mb = size / (1024 * 1024)
                self._log(f"Size: {size_mb:.2f} MB")
                self._log(f"Status: [OK] File exists")

                # Check for .rstexbin using expected output path logic
                rstexbin_path = _expected_rstexbin_path(texture_path, out_dir=out_dir)
                if _path_exists(rstexbin_path):
                    rstexbin_size = os.path.getsize(rstexbin_path.replace("/", os.sep))
                    rstexbin_mb = rstexbin_size / (1024 * 1024)
                    self._log(f".rstexbin: [OK] Exists ({rstexbin_mb:.2f} MB)")
                else:
                    self._log(f".rstexbin: [X] Not found")
            else:
                self._log(f"Status: [X] File not found")

        self._log("")

    def _open_texture_folder(self, texture_path):
        """Open the folder containing the texture."""
        import subprocess
        import platform

        # Get directory
        if "<UDIM>" in texture_path or "<udim>" in texture_path:
            # For UDIM, open the directory of the pattern
            folder = os.path.dirname(texture_path)
        else:
            folder = os.path.dirname(texture_path)

        if not os.path.isdir(folder):
            self._log(f"ERROR: Folder not found: {folder}")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", folder])
            else:  # Linux
                subprocess.Popen(["xdg-open", folder])
            self._log(f"Opened folder: {folder}")
        except Exception as e:
            self._log(f"ERROR: Could not open folder: {e}")

    def _show_udim_tiles(self, texture_path):
        """Show all UDIM tiles in a detailed view."""
        tiles = _expand_udim_tiles(texture_path)

        self._log(f"\n--- UDIM TILES DETAIL ---")
        self._log(f"Pattern: {texture_path}")
        self._log(f"Total Tiles: {len(tiles)}\n")

        if not tiles:
            self._log("No tiles found!")
            return

        total_size = 0
        for i, tile in enumerate(tiles, 1):
            if _path_exists(tile):
                size = os.path.getsize(tile.replace("/", os.sep))
                total_size += size
                size_mb = size / (1024 * 1024)
                self._log(f"  {i:2d}. {os.path.basename(tile)} ({size_mb:.2f} MB)")
            else:
                self._log(f"  {i:2d}. {os.path.basename(tile)} ([X] NOT FOUND)")

        total_mb = total_size / (1024 * 1024)
        self._log(f"\nTotal Size: {total_mb:.2f} MB")
        self._log("")

    def _remove_selected(self):
        """Remove selected rows from the table."""
        selected_rows = set()
        for item in self.table_inputs.selectedItems():
            selected_rows.add(item.row())

        for row in sorted(selected_rows, reverse=True):
            self.table_inputs.removeRow(row)

    def _gather(self):
        texproc = self.ed_texproc.text().strip()
        ocio = self.ed_ocio.text().strip()

        out_dir = self.ed_out.text().strip() if self.chk_custom_out.isChecked() else ""

        recursive = self.chk_recursive.isChecked()
        use_ocio_rules = self.rb_ocio.isChecked()

        skip_exist = self.chk_skip_exist.isChecked()
        force = not skip_exist  # Simplified: unchecked = force

        write_log = self.chk_log.isChecked()

        # Collect from table (column 0 = texture path)
        inputs = []
        for row in range(self.table_inputs.rowCount()):
            path_item = self.table_inputs.item(row, 0)
            if path_item:
                inputs.append(path_item.text())

        files = _collect_files(inputs, recursive=recursive)

        return texproc, ocio, out_dir, use_ocio_rules, skip_exist, force, write_log, files

    def _make_cmds_and_plan(self):
        texproc, ocio, out_dir, use_ocio_rules, skip_exist, force, write_log, files = self._gather()

        plan = []  # list of dicts: {src, out, cs, cmd, skipped}
        for f in files:
            cs = "" if use_ocio_rules else _match_rule_colorspace(f, self.rules)
            out_path = _expected_rstexbin_path(f, out_dir=out_dir)
            out_exists = os.path.exists(out_path)

            skipped = bool(skip_exist and out_exists)
            cmdline = _build_cmd(
                texproc_exe=texproc,
                in_file=f,
                ocio_file=ocio,
                use_ocio_rules=use_ocio_rules,
                out_dir=out_dir,
                colorspace=cs,
                write_log=write_log,
                force=force,
            )
            plan.append(dict(src=f, out=out_path, cs=cs, cmd=cmdline, skipped=skipped))

        return plan

    # ---------- actions ----------
    def _preview(self):
        self.txt_log.clear()
        texproc, ocio, out_dir, use_ocio_rules, skip_exist, force, write_log, files = self._gather()

        if not texproc or not os.path.exists(texproc):
            self._log(f"ERROR: redshiftTextureProcessor not found: {texproc}")
            return
        if not ocio or not os.path.exists(ocio):
            self._log(f"ERROR: OCIO config not found: {ocio}")
            return

        self._log(f"OCIO file : {ocio}")
        self._log(f"OCIO dir  : {Path(ocio).parent}")
        self._log(f"Mode      : {'OCIO file_rules (-useociorules)' if use_ocio_rules else 'GUI RULES (-cs per file)'}")
        self._log(f"Output    : {'Next to source (default)' if not out_dir else out_dir}")
        self._log(f"Recursive : {self.chk_recursive.isChecked()}")
        self._log(f"Skip exist: {skip_exist}")
        self._log(f"Force     : {force}  (applies only if Skip exist is OFF)")
        self._log(f"Files     : {len(files)}")
        self._log("")

        plan = self._make_cmds_and_plan()
        shown = 0
        for item in plan:
            if shown >= 60:
                break
            tag = "[SKIP]" if item["skipped"] else "     "
            cmd_str = " ".join([f'"{x}"' if " " in x else x for x in item["cmd"]])
            if use_ocio_rules:
                self._log(f"{tag} {cmd_str}")
            else:
                self._log(f"{tag} -cs \"{item['cs']}\" | {cmd_str}")
            shown += 1

        skipped_count = sum(1 for x in plan if x["skipped"])
        if len(plan) > shown:
            self._log(f"... ({len(plan)-shown} more)")
        self._log(f"\nPlanned: {len(plan)} | Skipped: {skipped_count} | Will run: {len(plan)-skipped_count}")

    def _cancel_conversion(self):
        """Cancel the running conversion."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self._log("\n[WARNING] Cancelling conversion...")

    def _on_progress_updated(self, current, total, message):
        """Update progress bar and label."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.lbl_progress.setText(f"{message} ({current}/{total})")

    def _on_log_message(self, message):
        """Append log message from worker thread."""
        self.txt_log.appendPlainText(message)

    def _on_conversion_finished(self, success_count, total_count):
        """Handle conversion completion."""
        # Hide progress bar
        self.progress_bar.setVisible(False)
        self.lbl_progress.setVisible(False)

        # Re-enable buttons
        self.btn_run.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_cancel.setEnabled(False)

        # Refresh .rstexbin status in table
        self._refresh_table_status()

        # Update scene if requested
        if self.chk_update_scene.isChecked() and success_count > 0:
            self._update_scene_file_nodes()

    def _update_scene_file_nodes(self):
        """Update Maya file nodes to point to .rstexbin files."""
        self._log("\n--- UPDATE SCENE ---")

        _, ocio, out_dir, _, _, _, _, files = self._gather()

        # Build mapping of source files to .rstexbin files
        file_map = {}
        for f in files:
            rstexbin_path = _expected_rstexbin_path(f, out_dir=out_dir)
            if os.path.exists(rstexbin_path):
                file_map[_norm(f)] = _norm(rstexbin_path)

        if not file_map:
            self._log("No .rstexbin files found to update in scene.")
            return

        # Update file nodes
        updated_count = 0
        file_nodes = cmds.ls(type="file") or []

        for node in file_nodes:
            try:
                current_path = cmds.getAttr(node + ".fileTextureName")
                if not current_path:
                    continue

                current_norm = _norm(current_path)

                # Check if this file was converted
                if current_norm in file_map:
                    new_path = file_map[current_norm]
                    cmds.setAttr(node + ".fileTextureName", new_path, type="string")
                    self._log(f"[OK] Updated {node}: {os.path.basename(new_path)}")
                    updated_count += 1

            except Exception as e:
                self._log(f"[ERROR] Error updating {node}: {e}")

        self._log(f"\n[OK] Updated {updated_count} file node(s) in scene.")

    # ---------- Rules Table Methods ----------
    def _populate_rules_table(self):
        """Populate rules table with current rules."""
        self.table_rules.setRowCount(0)
        for name, pattern, exts, colorspace in self.rules:
            row = self.table_rules.rowCount()
            self.table_rules.insertRow(row)
            self.table_rules.setItem(row, 0, QtWidgets.QTableWidgetItem(name))
            self.table_rules.setItem(row, 1, QtWidgets.QTableWidgetItem(pattern))
            self.table_rules.setItem(row, 2, QtWidgets.QTableWidgetItem(exts))
            self.table_rules.setItem(row, 3, QtWidgets.QTableWidgetItem(colorspace))

    def _add_rule(self):
        """Add a new rule to the table."""
        row = self.table_rules.rowCount()
        self.table_rules.insertRow(row)
        self.table_rules.setItem(row, 0, QtWidgets.QTableWidgetItem("NEW_RULE"))
        self.table_rules.setItem(row, 1, QtWidgets.QTableWidgetItem("*"))
        self.table_rules.setItem(row, 2, QtWidgets.QTableWidgetItem("*"))
        self.table_rules.setItem(row, 3, QtWidgets.QTableWidgetItem("Utility - Raw"))
        self._sync_rules_from_table()

    def _remove_rule(self):
        """Remove selected rules from the table."""
        selected_rows = set()
        for item in self.table_rules.selectedItems():
            selected_rows.add(item.row())
        for row in sorted(selected_rows, reverse=True):
            self.table_rules.removeRow(row)
        self._sync_rules_from_table()

    def _reset_rules(self):
        """Reset rules to defaults."""
        self.rules = list(DEFAULT_RULES)
        self._populate_rules_table()

    def _move_rule_up(self):
        """Move selected rule up in priority."""
        current_row = self.table_rules.currentRow()
        if current_row > 0:
            self._swap_table_rows(current_row, current_row - 1)
            self.table_rules.setCurrentCell(current_row - 1, 0)
            self._sync_rules_from_table()

    def _move_rule_down(self):
        """Move selected rule down in priority."""
        current_row = self.table_rules.currentRow()
        if current_row < self.table_rules.rowCount() - 1:
            self._swap_table_rows(current_row, current_row + 1)
            self.table_rules.setCurrentCell(current_row + 1, 0)
            self._sync_rules_from_table()

    def _swap_table_rows(self, row1, row2):
        """Swap two rows in the rules table."""
        for col in range(self.table_rules.columnCount()):
            item1 = self.table_rules.takeItem(row1, col)
            item2 = self.table_rules.takeItem(row2, col)
            self.table_rules.setItem(row1, col, item2)
            self.table_rules.setItem(row2, col, item1)

    def _sync_rules_from_table(self):
        """Sync self.rules from table contents."""
        self.rules = []
        for row in range(self.table_rules.rowCount()):
            name = self.table_rules.item(row, 0).text() if self.table_rules.item(row, 0) else ""
            pattern = self.table_rules.item(row, 1).text() if self.table_rules.item(row, 1) else "*"
            exts = self.table_rules.item(row, 2).text() if self.table_rules.item(row, 2) else "*"
            colorspace = self.table_rules.item(row, 3).text() if self.table_rules.item(row, 3) else "Utility - Raw"
            self.rules.append((name, pattern, exts, colorspace))

    def _run(self):
        self._preview()

        _, ocio, _, _, _, _, _, files = self._gather()
        if not files:
            self._log("No files to process.")
            return

        env = os.environ.copy()
        env["OCIO"] = _norm(ocio)  # set file for robustness

        plan = self._make_cmds_and_plan()
        to_run = [x for x in plan if not x["skipped"]]

        if not to_run:
            self._log("\nNothing to run (all files skipped).")
            return

        # Show progress bar
        self.progress_bar.setVisible(True)
        self.lbl_progress.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(to_run))

        # Disable buttons during conversion
        self.btn_run.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.btn_cancel.setEnabled(True)

        # Create and start worker thread
        self.worker = ConversionWorker(plan, env)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.log_message.connect(self._on_log_message)
        self.worker.conversion_finished.connect(self._on_conversion_finished)
        self.worker.start()


def show_rs_texproc_maya_ui():
    # Prevent duplicate windows
    for w in QtWidgets.QApplication.topLevelWidgets():
        if w.objectName() == "RSTextureProcessorMayaUI":
            w.close()

    dlg = RSTextureProcessorMayaUI(parent=QtWidgets.QApplication.activeWindow())
    dlg.setObjectName("RSTextureProcessorMayaUI")
    dlg.show()
    return dlg


# Usage in Maya Script Editor (Python):
# import rs_texproc_maya_gui
# rs_texproc_maya_gui.show_rs_texproc_maya_ui()