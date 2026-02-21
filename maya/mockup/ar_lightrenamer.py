# -*- coding: utf-8 -*-
"""
Maya Batch Rename Tool (Py2.7 + Py3 compatible)
- Renames ONLY the CURRENT Maya selection (no selection snapshot issues)
- Optional: pad trailing digits in Base Name (e.g. light1 -> light001)
- Optional: append numbering with padding

Author: Katha
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import re
import sys
import maya.cmds as cmds
from collections import defaultdict

# -----------------------------
# Python 2/3 Compatibility
# -----------------------------
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
    text_type = unicode  # noqa: F821
    string_types = (str, unicode)  # noqa: F821
else:
    text_type = str
    string_types = (str,)

# -----------------------------
# Qt Compatibility Layer
# -----------------------------
try:
    # Maya 2022+ (Python 3)
    from PySide2 import QtWidgets, QtCore, QtGui
    try:
        import shiboken2 as shiboken
    except Exception:
        shiboken = None
except ImportError:
    # Older Maya (Python 2.7)
    from PySide import QtGui as QtWidgets  # QtWidgets maps to QtGui in PySide1
    from PySide import QtCore, QtGui
    try:
        import shiboken
    except Exception:
        shiboken = None


# -----------------------------
# Text Conversion Helpers
# -----------------------------
def to_text(v):
    """Convert any value to text string (unicode in Py2, str in Py3)."""
    if v is None:
        return text_type("")
    if isinstance(v, text_type):
        return v
    if PY2 and isinstance(v, str):
        try:
            return v.decode('utf-8')
        except Exception:
            return text_type(v)
    try:
        return text_type(v)
    except Exception:
        return text_type("")


def safe_format(template, *args, **kwargs):
    """Safe string formatting that works in both Py2 and Py3."""
    try:
        return to_text(template).format(*args, **kwargs)
    except Exception:
        return to_text(template)


def get_maya_main_window():
    """Get Maya main window as QWidget."""
    if shiboken is None:
        return None
    try:
        import maya.OpenMayaUI as omui
    except Exception:
        return None

    ptr = omui.MQtUtil.mainWindow()
    if ptr is None:
        return None

    try:
        if PY2:
            return shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)  # noqa: F821
        else:
            return shiboken.wrapInstance(int(ptr), QtWidgets.QWidget)
    except Exception:
        return None


class MayaBatchRenameUI(QtWidgets.QDialog):
    """
    UI: shows selected objects (display only)
    Rename: ALWAYS uses current Maya selection at click time
    """

    def __init__(self, parent=None):
        super(MayaBatchRenameUI, self).__init__(parent)

        self.setWindowTitle("Maya Batch Rename Tool")
        self.setMinimumWidth(540)
        self.setMinimumHeight(680)

        self._selection_job = None

        self.init_ui()
        self._install_selection_job()
        self.refresh_ui_from_selection()

    # ---------------- UI ----------------
    def init_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        # Selection group
        selection_group = QtWidgets.QGroupBox("Selection (Display only) - Rename uses CURRENT Maya selection")
        selection_layout = QtWidgets.QVBoxLayout()

        top_row = QtWidgets.QHBoxLayout()
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_ui_from_selection)
        self.object_count_label = QtWidgets.QLabel("Objects: 0")
        top_row.addWidget(self.refresh_btn)
        top_row.addStretch()
        top_row.addWidget(self.object_count_label)
        selection_layout.addLayout(top_row)

        self.objects_list = QtWidgets.QListWidget()
        self.objects_list.setMaximumHeight(170)
        selection_layout.addWidget(self.objects_list)

        selection_group.setLayout(selection_layout)
        main_layout.addWidget(selection_group)

        # Rename options group
        rename_group = QtWidgets.QGroupBox("Rename Options")
        form = QtWidgets.QFormLayout()

        self.base_name_edit = QtWidgets.QLineEdit()
        self.base_name_edit.setPlaceholderText("e.g. light, keyLight1, propA12 ...")
        self.base_name_edit.textChanged.connect(self.update_preview)
        form.addRow("Base Name:", self.base_name_edit)

        self.prefix_edit = QtWidgets.QLineEdit()
        self.prefix_edit.setPlaceholderText("Optional prefix...")
        self.prefix_edit.textChanged.connect(self.update_preview)
        form.addRow("Prefix:", self.prefix_edit)

        self.suffix_edit = QtWidgets.QLineEdit()
        self.suffix_edit.setPlaceholderText("Optional suffix...")
        self.suffix_edit.textChanged.connect(self.update_preview)
        form.addRow("Suffix:", self.suffix_edit)

        # NEW: base-name digit padding
        base_pad_row = QtWidgets.QHBoxLayout()
        self.base_digit_pad_check = QtWidgets.QCheckBox("Pad trailing digits in Base Name")
        self.base_digit_pad_check.setChecked(True)
        self.base_digit_pad_check.toggled.connect(self.update_preview)
        base_pad_row.addWidget(self.base_digit_pad_check)

        base_pad_row.addWidget(QtWidgets.QLabel("Padding:"))
        self.base_digit_pad_spin = QtWidgets.QSpinBox()
        self.base_digit_pad_spin.setRange(1, 8)
        self.base_digit_pad_spin.setValue(3)
        self.base_digit_pad_spin.valueChanged.connect(self.update_preview)
        base_pad_row.addWidget(self.base_digit_pad_spin)
        base_pad_row.addStretch()

        form.addRow("Base Digit Padding:", base_pad_row)

        # numbering options (append)
        num_row = QtWidgets.QHBoxLayout()
        self.add_numbers_check = QtWidgets.QCheckBox("Append Numbers")
        self.add_numbers_check.setChecked(True)
        self.add_numbers_check.toggled.connect(self.update_preview)
        num_row.addWidget(self.add_numbers_check)

        num_row.addWidget(QtWidgets.QLabel("Start:"))
        self.start_number_spin = QtWidgets.QSpinBox()
        self.start_number_spin.setRange(0, 9999)
        self.start_number_spin.setValue(1)
        self.start_number_spin.valueChanged.connect(self.update_preview)
        num_row.addWidget(self.start_number_spin)

        num_row.addWidget(QtWidgets.QLabel("Padding:"))
        self.number_padding_spin = QtWidgets.QSpinBox()
        self.number_padding_spin.setRange(1, 8)
        self.number_padding_spin.setValue(2)
        self.number_padding_spin.valueChanged.connect(self.update_preview)
        num_row.addWidget(self.number_padding_spin)
        num_row.addStretch()

        form.addRow("Numbering:", num_row)

        # transform only
        self.rename_transform_check = QtWidgets.QCheckBox("Rename Transform Nodes Only (recommended)")
        self.rename_transform_check.setChecked(True)
        self.rename_transform_check.toggled.connect(self.update_preview)
        form.addRow("", self.rename_transform_check)

        rename_group.setLayout(form)
        main_layout.addWidget(rename_group)

        # Preview
        preview_group = QtWidgets.QGroupBox("Preview (what will be renamed)")
        preview_layout = QtWidgets.QVBoxLayout()
        self.preview_list = QtWidgets.QListWidget()
        self.preview_list.setMaximumHeight(190)
        preview_layout.addWidget(self.preview_list)
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)

        # Warning
        self.warning_label = QtWidgets.QLabel()
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("QLabel { color: #FF6B35; padding: 6px; }")
        main_layout.addWidget(self.warning_label)

        # Buttons
        btns = QtWidgets.QHBoxLayout()
        self.rename_btn = QtWidgets.QPushButton("Rename Selected Objects")
        self.rename_btn.clicked.connect(self.rename_objects)
        self.rename_btn.setStyleSheet("QPushButton { background-color: #4A90E2; color: white; padding: 8px; }")

        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.clicked.connect(self.close)

        btns.addWidget(self.rename_btn)
        btns.addWidget(self.close_btn)
        main_layout.addLayout(btns)

    # ---------------- selection tracking ----------------
    def _install_selection_job(self):
        """Install Maya selection change callback."""
        self._remove_selection_job()
        try:
            self._selection_job = cmds.scriptJob(
                event=["SelectionChanged", self.refresh_ui_from_selection],
                protected=True
            )
        except Exception:
            self._selection_job = None

    def _remove_selection_job(self):
        """Remove Maya selection change callback."""
        if self._selection_job and cmds.scriptJob(exists=self._selection_job):
            try:
                cmds.scriptJob(kill=self._selection_job, force=True)
            except Exception:
                pass
        self._selection_job = None

    def closeEvent(self, event):
        """Handle window close event."""
        self._remove_selection_job()
        super(MayaBatchRenameUI, self).closeEvent(event)

    # ---------------- core: selection + targets ----------------
    def _get_current_selection_long(self):
        """Get current Maya selection with long names."""
        return cmds.ls(sl=True, long=True) or []

    def _shape_to_transform(self, node):
        """Convert shape node to its parent transform node."""
        if not node or not cmds.objExists(node):
            return None
        if cmds.objectType(node) == 'transform':
            return node
        parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
        return parents[0] if parents else None

    def _get_targets_for_rename(self):
        """
        ALWAYS use current Maya selection at time of call.
        If transform-only is enabled, convert shapes -> parent transforms.
        """
        sel = self._get_current_selection_long()
        if not sel:
            return []

        if not self.rename_transform_check.isChecked():
            return [n for n in sel if cmds.objExists(n)]

        targets = []
        seen = set()
        for n in sel:
            t = self._shape_to_transform(n)
            if t and t not in seen and cmds.objExists(t):
                targets.append(t)
                seen.add(t)
        return targets

    # ---------------- naming helpers ----------------
    def _pad_base_trailing_digits(self, base):
        """
        If base ends with digits and option enabled:
          keyLight1 + pad(3) -> keyLight001
        """
        if not self.base_digit_pad_check.isChecked():
            return base

        m = re.match(r"^(.*?)(\d+)$", base)
        if not m:
            return base

        head, digits = m.group(1), m.group(2)
        pad = int(self.base_digit_pad_spin.value())
        return safe_format("{0}{1}", head, digits.zfill(pad))

    def _format_index_number(self, number):
        """Format index number with padding."""
        pad = int(self.number_padding_spin.value())
        format_str = "{0:0" + str(pad) + "d}"
        return format_str.format(number)

    def generate_new_name(self, index, total):
        """Generate new name for object at given index."""
        prefix = to_text(self.prefix_edit.text()).strip()
        base = to_text(self.base_name_edit.text()).strip()
        suffix = to_text(self.suffix_edit.text()).strip()

        if not base:
            base = "object"

        base = self._pad_base_trailing_digits(base)

        parts = []
        if prefix:
            parts.append(prefix)
        parts.append(base)

        if self.add_numbers_check.isChecked():
            start = int(self.start_number_spin.value())
            num = start + index
            parts.append(self._format_index_number(num))

        if suffix:
            parts.append(suffix)

        return "_".join(parts)

    # ---------------- UI update ----------------
    def refresh_ui_from_selection(self):
        """Refresh UI from current Maya selection."""
        sel = self._get_current_selection_long()

        self.objects_list.clear()
        for n in sel:
            short = n.split("|")[-1]
            item = QtWidgets.QListWidgetItem(short)
            item.setToolTip(n)
            self.objects_list.addItem(item)

        self.object_count_label.setText(safe_format("Objects: {0}", len(sel)))
        self.update_preview()

    def update_preview(self):
        """Update preview list with new names."""
        self.preview_list.clear()
        self.warning_label.clear()

        targets = self._get_targets_for_rename()
        if not targets:
            self.warning_label.setText("Select objects in Maya to rename.")
            return

        total = len(targets)
        new_names = []
        counts = defaultdict(int)

        for i, obj in enumerate(targets):
            new_name = self.generate_new_name(i, total)
            new_names.append(new_name)
            counts[new_name] += 1

            old = obj.split("|")[-1]
            preview_text = safe_format("{0}  ->  {1}", old, new_name)
            self.preview_list.addItem(preview_text)

        dups = [n for n, c in counts.items() if c > 1]
        if dups:
            msg = safe_format("WARNING: Duplicate new names generated: {0}", ", ".join(dups))
            self.warning_label.setText(msg)
            return

        # Conflicts against existing nodes (excluding our targets)
        conflicts = []
        target_set = set(targets)
        for nm in new_names:
            if cmds.objExists(nm):
                existing = cmds.ls(nm, long=True) or []
                if existing and existing[0] not in target_set:
                    conflicts.append(nm)

        if conflicts:
            show = conflicts[:5]
            msg = safe_format("WARNING: Names already exist in scene: {0}", ", ".join(show))
            if len(conflicts) > 5:
                msg = safe_format("{0} (+{1} more)", msg, len(conflicts) - 5)
            self.warning_label.setText(msg)

    # ---------------- rename action ----------------
    def rename_objects(self):
        """Rename selected objects."""
        targets = self._get_targets_for_rename()
        if not targets:
            QtWidgets.QMessageBox.warning(
                self,
                "No Objects",
                "No selected objects to rename.\n\nSelect objects in Maya."
            )
            return

        base = to_text(self.base_name_edit.text()).strip()
        if not base:
            QtWidgets.QMessageBox.warning(self, "No Base Name", "Please enter a base name!")
            return

        warn = to_text(self.warning_label.text()).strip()
        if warn.startswith("WARNING"):
            reply = QtWidgets.QMessageBox.question(
                self,
                "Potential Name Conflicts",
                "Potential duplicate or existing-name conflicts detected.\nMaya may auto-adjust names to avoid conflicts.\n\nContinue?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.No:
                return

        total = len(targets)
        errors = []
        renamed = 0

        cmds.undoInfo(openChunk=True)
        try:
            # reverse for safer hierarchy renaming
            for i, obj in enumerate(reversed(targets)):
                try:
                    new_name = self.generate_new_name(total - 1 - i, total)
                    cmds.rename(obj, new_name)
                    renamed += 1
                except Exception as e:
                    error_msg = safe_format("{0}: {1}", obj.split("|")[-1], to_text(e))
                    errors.append(error_msg)
        finally:
            cmds.undoInfo(closeChunk=True)

        if errors:
            msg = safe_format("Renamed {0} objects.\n\nErrors:\n{1}", renamed, "\n".join(errors[:10]))
            if len(errors) > 10:
                msg = safe_format("{0}\n... and {1} more", msg, len(errors) - 10)
            QtWidgets.QMessageBox.warning(self, "Rename Completed (with errors)", msg)
        else:
            msg = safe_format("Successfully renamed {0} objects!", renamed)
            QtWidgets.QMessageBox.information(self, "Success", msg)

        self.refresh_ui_from_selection()


# -----------------------------
# Show UI
# -----------------------------
def show_ui():
    """Show the Maya Batch Rename UI."""
    global maya_batch_rename_window
    try:
        maya_batch_rename_window.close()
        maya_batch_rename_window.deleteLater()
    except Exception:
        pass

    maya_batch_rename_window = MayaBatchRenameUI(parent=get_maya_main_window())
    maya_batch_rename_window.show()


if __name__ == "__main__":
    show_ui()
