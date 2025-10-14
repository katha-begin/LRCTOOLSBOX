# -*- coding: utf-8 -*-
from __future__ import print_function
import os, re, glob, json
from datetime import datetime
import maya.cmds as cmds

WIN_ID = "EE_ShotSetup_RS_IO"

# ============================ Small helpers ============================

def _strip_ns(name):
    return name.split(":", 1)[-1] if ":" in name else name

def _set_if_exists(node, attr, value, value_type=None):
    plug = "{}.{}".format(node, attr)
    if not cmds.objExists(plug):
        return False
    try:
        if value_type:
            cmds.setAttr(plug, value, type=value_type)
        else:
            cmds.setAttr(plug, value)
        return True
    except Exception:
        return False

def _scene_version_from_filename(scene_path=None):
    if scene_path is None:
        scene_path = cmds.file(q=True, sn=True) or ""
    m = re.search(r'(v\d{3,})', os.path.basename(scene_path or ""), re.IGNORECASE)
    return m.group(1) if m else "v001"

def _log(msg):
    if cmds.scrollField(WIN_ID+"_log", exists=True):
        cmds.scrollField(WIN_ID+"_log", e=True, ip=999999)
        cmds.scrollField(WIN_ID+"_log", e=True, it=msg + "\n")
    print(msg)

# ============================ Shot detection & parsing ============================

def _list_shot_nodes():
    nodes = cmds.ls(type="shot") or []
    return sorted(set(nodes))

def _shot_pick_dialog(shots):
    def _ui():
        cmds.columnLayout(adjustableColumn=True)
        cmds.text(label="Multiple shot nodes found. Pick one:", align="left")
        om = cmds.optionMenu("EE_shotPickMenu", width=420)
        for s in shots:
            lbl = "{}  ({})".format(_strip_ns(s), s)
            cmds.menuItem(label=lbl, data=s)
        cmds.separator(h=6, style="none")
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=1,
                       columnWidth=[(1,260),(2,120)],
                       columnAttach=[(1,"both",0),(2,"both",0)])
        def _ok(*_):
            sel = cmds.optionMenu(om, q=True, v=True)
            m = re.search(r"\(([^)]+)\)$", sel)
            node = m.group(1) if m else sel
            cmds.layoutDialog(dismiss=node)
        def _cancel(*_):
            cmds.layoutDialog(dismiss="Cancel")
        cmds.button(label="OK", c=_ok)
        cmds.button(label="Cancel", c=_cancel)
        cmds.setParent("..")
    result = cmds.layoutDialog(t="Select Shot Node", ui=_ui)
    return None if result in ("", "Cancel") else result

def _pick_shot_node_ui():
    shots = _list_shot_nodes()
    if not shots:
        return None
    if len(shots) == 1:
        return shots[0]
    return _shot_pick_dialog(shots)

def _get_shot_frames(shot_node):
    sf = cmds.getAttr(shot_node + ".startFrame")
    ef = cmds.getAttr(shot_node + ".endFrame")
    return float(sf), float(ef)

def _parse_ep_seq_shot_from_name(name):
    base = _strip_ns(name)
    m = re.search(r'(?:^|_)EP?(\d+).*?[_-]sq(\d+).*?[_-]SH(\d+)', base, re.IGNORECASE)
    if not m:
        m2 = re.search(r'(EP?\d+).*(sq\d+).*(SH\d+)', base, re.IGNORECASE)
        if not m2:
            return None
        EP = re.search(r'\d+', m2.group(1)).group(0)
        seq = re.search(r'\d+', m2.group(2)).group(0)
        sh  = re.search(r'\d+', m2.group(3)).group(0)
    else:
        EP, seq, sh = m.group(1), m.group(2), m.group(3)
    return {"EP": "Ep{}".format(EP.zfill(2)),
            "seq": "sq{}".format(seq.zfill(4)),
            "shot": "SH{}".format(sh.zfill(4))}

def _parse_show_ep_seq_sh_from_path(scene_path):
    if not scene_path:
        return (None, None, None, None)
    parts = scene_path.replace("\\", "/").split("/")
    show = None
    for i, p in enumerate(parts):
        if p.lower() == "all" and i > 0:
            show = parts[i-1]
            break
    EP  = next((p for p in parts if re.match(r'^Ep\d{2}$', p, re.IGNORECASE)), None)
    seq = next((p for p in parts if re.match(r'^sq\d{4}$', p, re.IGNORECASE)), None)
    sh  = next((p for p in parts if re.match(r'^SH\d{4}$', p, re.IGNORECASE)), None)
    return (show, EP, seq, sh)

def _parse_show_ep_seq_sh_from_filename(scene_path):
    fn = os.path.basename(scene_path or "")
    m = re.search(r'(?:^|_)EP?(\d+).*?[_-]sq(\d+).*?[_-]SH(\d+)', fn, re.IGNORECASE)
    if not m:
        return (None, None, None, None)
    EP  = "Ep{}".format(m.group(1).zfill(2))
    seq = "sq{}".format(m.group(2).zfill(4))
    sh  = "SH{}".format(m.group(3).zfill(4))
    show, _, _, _ = _parse_show_ep_seq_sh_from_path(scene_path)
    return (show, EP, seq, sh)

def _parse_ep_seq_shot_from_scene(scene_path):
    """Parse episode, sequence, shot from scene path - wrapper for compatibility."""
    show, EP, seq, sh = _parse_show_ep_seq_sh_from_path(scene_path)
    if EP and seq and sh:
        return {"EP": EP, "seq": seq, "shot": sh}
    return None

# ============================ Paths & listing ============================

def _shot_root(drive_root, show, ep, sq, sh):
    return os.path.join(drive_root, show, "all", "scene", ep, sq, sh).replace("\\","/")

def _version_root_v(drive_root, show, ep, sq, sh):
    return os.path.join(_shot_root(drive_root, show, ep, sq, sh), "lighting", "version").replace("\\","/")

def _publish_root_w(show, ep, seq, shot):
    return os.path.join("W:/", show, "all", "scene", ep, seq, shot, "lighting", "publish").replace("\\","/")

def _list_scenes_recursive(version_root):
    if not os.path.isdir(version_root):
        return []
    out = []
    for ext in ("**/*.ma","**/*.mb"):
        out.extend(glob.glob(os.path.join(version_root, ext).replace("\\","/"), recursive=True))
    return sorted(out)

# ============================ JSON Export Functions ============================

def _extract_shot_data_from_node(shot_node, show_code="SWA"):
    """
    Extract comprehensive shot data from a Maya shot node for JSON export.

    Args:
        shot_node (str): Name of the Maya shot node
        show_code (str): Show/project code (default: "SWA")

    Returns:
        dict: Complete shot data structure
    """
    if not shot_node or not cmds.objExists(shot_node):
        raise RuntimeError("Shot node '{}' not found.".format(shot_node))

    # Get basic shot information
    start, end = _get_shot_frames(shot_node)

    # Get shot name and parse episode/sequence/shot info
    name_src = cmds.getAttr(shot_node + ".shotName") if cmds.objExists(shot_node + ".shotName") else shot_node
    id_parts = _parse_ep_seq_shot_from_name(name_src) or _parse_ep_seq_shot_from_scene(cmds.file(q=True, sn=True) or "")

    if not id_parts:
        raise RuntimeError("Could not parse Ep/seq/shot from shot node or scene name.")

    EP, seq, sh = id_parts["EP"], id_parts["seq"], id_parts["shot"]

    # Get current scene information
    current_scene = cmds.file(q=True, sn=True) or ""
    scene_version = _scene_version_from_filename(current_scene)

    # Get additional shot node attributes if they exist
    shot_data = {
        "metadata": {
            "export_timestamp": datetime.now().isoformat(),
            "maya_version": cmds.about(version=True),
            "scene_file": current_scene,
            "shot_node": shot_node,
            "show_code": show_code
        },
        "shot_info": {
            "episode": EP,
            "sequence": seq,
            "shot": sh,
            "shot_name": name_src,
            "start_frame": int(start),
            "end_frame": int(end),
            "frame_count": int(end - start + 1),
            "version": scene_version
        },
        "render_settings": {
            "current_renderer": cmds.getAttr("defaultRenderGlobals.currentRenderer") if cmds.objExists("defaultRenderGlobals.currentRenderer") else "unknown",
            "animation_enabled": bool(cmds.getAttr("defaultRenderGlobals.animation")) if cmds.objExists("defaultRenderGlobals.animation") else False,
            "extension_padding": cmds.getAttr("defaultRenderGlobals.extensionPadding") if cmds.objExists("defaultRenderGlobals.extensionPadding") else 4,
            "frame_step": cmds.getAttr("defaultRenderGlobals.byFrameStep") if cmds.objExists("defaultRenderGlobals.byFrameStep") else 1.0,
            "image_file_prefix": cmds.getAttr("defaultRenderGlobals.imageFilePrefix") if cmds.objExists("defaultRenderGlobals.imageFilePrefix") else ""
        },
        "timeline_settings": {
            "playback_start": cmds.playbackOptions(q=True, min=True),
            "playback_end": cmds.playbackOptions(q=True, max=True),
            "animation_start": cmds.playbackOptions(q=True, ast=True),
            "animation_end": cmds.playbackOptions(q=True, aet=True)
        }
    }

    # Add optional shot node attributes if they exist
    optional_attrs = [
        "sequenceStartFrame", "sequenceEndFrame", "scale", "preHold", "postHold",
        "clipIn", "clipOut", "clipDuration", "sourceStart", "sourceEnd", "sourceDuration"
    ]

    shot_attributes = {}
    for attr in optional_attrs:
        full_attr = "{}.{}".format(shot_node, attr)
        if cmds.objExists(full_attr):
            try:
                value = cmds.getAttr(full_attr)
                shot_attributes[attr] = value
            except Exception:
                pass

    if shot_attributes:
        shot_data["shot_attributes"] = shot_attributes

    return shot_data

def _get_json_export_path(project_root, show, ep, seq, shot):
    """
    Generate the JSON export file path following the pattern:
    {project_root}\{project}\all\scene\{ep}\{seq}\{shot}\.{ep}_{seq}_{shot}.json

    Args:
        project_root (str): Root project directory (e.g., "V:/")
        show (str): Show/project name
        ep (str): Episode (e.g., "Ep01")
        seq (str): Sequence (e.g., "sq0010")
        shot (str): Shot (e.g., "SH0010")

    Returns:
        str: Full path to JSON export file
    """
    filename = ".{}_{}_{}".format(ep, seq, shot) + ".json"
    export_path = os.path.join(project_root, show, "all", "scene", ep, seq, shot, filename)
    return export_path.replace("\\", "/")

def export_shot_data_to_json(shot_node, project_root="V:/", show_code="SWA"):
    """
    Export shot data to JSON file for external use.

    Args:
        shot_node (str): Maya shot node name
        project_root (str): Project root directory
        show_code (str): Show/project code

    Returns:
        tuple: (success: bool, file_path: str, data_or_error: dict)
    """
    try:
        # Extract shot data
        shot_data = _extract_shot_data_from_node(shot_node, show_code)

        # Get export path
        ep = shot_data["shot_info"]["episode"]
        seq = shot_data["shot_info"]["sequence"]
        shot = shot_data["shot_info"]["shot"]

        # Determine show name from current context or use show_code
        show = show_code
        if cmds.optionMenu(WIN_ID+"_showMenu", exists=True):
            ui_show = cmds.optionMenu(WIN_ID+"_showMenu", q=True, v=True)
            if ui_show:
                show = ui_show

        json_path = _get_json_export_path(project_root, show, ep, seq, shot)

        # Ensure directory exists
        json_dir = os.path.dirname(json_path)
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)

        # Check if file exists and compare data
        should_write = True
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    existing_data = json.load(f)

                # Compare relevant data (excluding timestamp)
                current_data_copy = shot_data.copy()
                existing_data_copy = existing_data.copy()

                # Remove timestamps for comparison
                if "metadata" in current_data_copy:
                    current_data_copy["metadata"].pop("export_timestamp", None)
                if "metadata" in existing_data_copy:
                    existing_data_copy["metadata"].pop("export_timestamp", None)

                # If data is the same, skip writing
                if current_data_copy == existing_data_copy:
                    should_write = False
                    _log("[JSON] Data unchanged, skipping export: {}".format(json_path))
                    return True, json_path, shot_data

            except (IOError, ValueError, KeyError):
                # If we can't read/parse existing file, write new one
                should_write = True

        if should_write:
            # Write JSON file
            with open(json_path, 'w') as f:
                json.dump(shot_data, f, indent=2, sort_keys=True)

            _log("[JSON] Exported shot data: {}".format(json_path))
            return True, json_path, shot_data

    except Exception as e:
        error_msg = "Failed to export shot data: {}".format(str(e))
        _log("[JSON ERROR] {}".format(error_msg))
        return False, "", {"error": error_msg}

def _export_shot_data_on_save(project_root, show_code):
    """
    Helper function to export shot data when saving Maya scene files.
    Automatically detects shot node and exports JSON data.

    Args:
        project_root (str): Project root directory
        show_code (str): Show/project code
    """
    try:
        # Try to get shot node from UI first
        shot_node = None
        if cmds.textField(WIN_ID+"_shotNode", exists=True):
            shot_node = cmds.textField(WIN_ID+"_shotNode", q=True, text=True).strip()

        # If no shot node in UI, try to auto-detect
        if not shot_node:
            shots = _list_shot_nodes()
            if len(shots) == 1:
                shot_node = shots[0]
            elif len(shots) > 1:
                # Use first shot node as fallback
                shot_node = shots[0]
                _log("[JSON] Multiple shot nodes found, using: {}".format(shot_node))

        if shot_node:
            success, json_path, data = export_shot_data_to_json(shot_node, project_root, show_code)
            if success:
                _log("[JSON] Auto-export completed: {}".format(os.path.basename(json_path)))
            else:
                _log("[JSON] Auto-export failed: {}".format(data.get("error", "Unknown error")))
        else:
            _log("[JSON] No shot node found for auto-export")

    except Exception as e:
        _log("[JSON ERROR] Auto-export failed: {}".format(str(e)))

# ============================ Version scan / increment (global) ============================

def _core_stem(ep, seq, shot):
    return "{}_{}_{}".format(ep, seq, shot)

def _scan_versions_global(version_root, ep, seq, shot):
    """
    Match: Ep##_sq####_SH####_lighting[_anything]_v###.ma
    """
    if not os.path.isdir(version_root):
        return []
    core = re.escape(_core_stem(ep, seq, shot))
    pat = re.compile(r'^' + core + r'_lighting(?:_.*)?_v(\d{3,})\.ma$', re.IGNORECASE)
    found = []
    for f in os.listdir(version_root):
        if not f.lower().endswith(".ma"):
            continue
        m = pat.match(f)
        if m:
            try:
                found.append(int(m.group(1)))
            except Exception:
                pass
    return sorted(found)

def _next_version_tag_global(version_root, ep, seq, shot):
    existing = _scan_versions_global(version_root, ep, seq, shot)
    nxt = 1 if not existing else (existing[-1] + 1)
    return "v{:03d}".format(nxt), existing

# ============================ Render & timeline ============================

def apply_settings_from_shot(shot_node, show_code="SWA"):
    """
    Render prefix version ALWAYS equals current scene file version.
    """
    if not shot_node or not cmds.objExists(shot_node):
        raise RuntimeError("Shot node not found.")

    start, end = _get_shot_frames(shot_node)

    name_src = cmds.getAttr(shot_node + ".shotName") if cmds.objExists(shot_node + ".shotName") else shot_node
    id_parts = _parse_ep_seq_shot_from_name(name_src) or _parse_ep_seq_shot_from_scene(cmds.file(q=True, sn=True) or "")
    if not id_parts:
        raise RuntimeError("Could not parse Ep/seq/shot (needs Ep##_sq####_SH#### in shot or scene name).")

    EP, seq, sh = id_parts["EP"], id_parts["seq"], id_parts["shot"]
    vtag = _scene_version_from_filename()

    # Core render globals
    _set_if_exists("defaultRenderGlobals", "animation", 1)
    _set_if_exists("defaultRenderGlobals", "startFrame", start)
    _set_if_exists("defaultRenderGlobals", "endFrame", end)
    _set_if_exists("defaultRenderGlobals", "byFrameStep", 1.0)

    if not _set_if_exists("defaultRenderGlobals", "extensionPadding", 4):
        _set_if_exists("defaultRenderGlobals", "periodInExt", 1)
        _set_if_exists("defaultRenderGlobals", "putFrameBeforeExt", 1)

    _set_if_exists("defaultRenderGlobals", "enableDefaultLight", 0)
    _set_if_exists("defaultRenderGlobals", "currentRenderer", "redshift", value_type="string")

    prefix = os.path.join(_publish_root_w(show_code, EP, seq, sh), vtag, "<RenderLayer>", "<RenderLayer>").replace("\\","/")
    _set_if_exists("defaultRenderGlobals", "imageFilePrefix", prefix, value_type="string")

    cmds.playbackOptions(min=start, max=end)
    cmds.playbackOptions(ast=start, aet=end)

    print("[ShotSetup] {} | frames {}-{} | {} {} {} | {}".format(shot_node, int(start), int(end), EP, seq, sh, vtag))
    print("[ShotSetup] imageFilePrefix -> {}".format(prefix))
    return {"EP":EP, "seq":seq, "shot":sh, "version":vtag, "start":start, "end":end, "prefix":prefix}

# ============================ UI state & binding ============================

_io_cache = None

def _populate_menus(show=None, ep=None, seq=None, shot=None):
    cmds.optionMenu(WIN_ID+"_showMenu", e=True, dai=True)
    shows = sorted(_io_cache.keys())
    for s in shows:
        cmds.menuItem(label=s, parent=WIN_ID+"_showMenu")
    if show in shows:
        cmds.optionMenu(WIN_ID+"_showMenu", e=True, v=show)
    else:
        cur = cmds.optionMenu(WIN_ID+"_showMenu", q=True, v=True) if shows else None
        cmds.optionMenu(WIN_ID+"_showMenu", e=True, v=(cur if cur in shows else (shows[0] if shows else "")))
    show = cmds.optionMenu(WIN_ID+"_showMenu", q=True, v=True)

    cmds.optionMenu(WIN_ID+"_epMenu", e=True, dai=True)
    eps = sorted((_io_cache.get(show, {}) or {}).keys())
    for e in eps:
        cmds.menuItem(label=e, parent=WIN_ID+"_epMenu")
    if ep in eps:
        cmds.optionMenu(WIN_ID+"_epMenu", e=True, v=ep)
    else:
        cur = cmds.optionMenu(WIN_ID+"_epMenu", q=True, v=True) if eps else None
        cmds.optionMenu(WIN_ID+"_epMenu", e=True, v=(cur if cur in eps else (eps[0] if eps else "")))
    ep = cmds.optionMenu(WIN_ID+"_epMenu", q=True, v=True)

    cmds.optionMenu(WIN_ID+"_seqMenu", e=True, dai=True)
    seqs = sorted((_io_cache.get(show, {}).get(ep, {}) or {}).keys())
    for q in seqs:
        cmds.menuItem(label=q, parent=WIN_ID+"_seqMenu")
    if seq in seqs:
        cmds.optionMenu(WIN_ID+"_seqMenu", e=True, v=seq)
    else:
        cur = cmds.optionMenu(WIN_ID+"_seqMenu", q=True, v=True) if seqs else None
        cmds.optionMenu(WIN_ID+"_seqMenu", e=True, v=(cur if cur in seqs else (seqs[0] if seqs else "")))
    seq = cmds.optionMenu(WIN_ID+"_seqMenu", q=True, v=True)

    cmds.optionMenu(WIN_ID+"_shotMenu", e=True, dai=True)
    shots = sorted((_io_cache.get(show, {}).get(ep, {}).get(seq, {}) or {}).keys())
    for h in shots:
        cmds.menuItem(label=h, parent=WIN_ID+"_shotMenu")
    if shot in shots:
        cmds.optionMenu(WIN_ID+"_shotMenu", e=True, v=shot)
    else:
        cur = cmds.optionMenu(WIN_ID+"_shotMenu", q=True, v=True) if shots else None
        cmds.optionMenu(WIN_ID+"_shotMenu", e=True, v=(cur if cur in shots else (shots[0] if shots else "")))

    _on_pick_shot()

def _autobind_from_scene():
    scene = cmds.file(q=True, sn=True) or ""
    show, EP, seq, sh = _parse_show_ep_seq_sh_from_path(scene)
    if not (EP and seq and sh):
        show2, EP2, seq2, sh2 = _parse_show_ep_seq_sh_from_filename(scene)
        show = show or show2
        EP   = EP  or EP2
        seq  = seq or seq2
        sh   = sh  or sh2
    if cmds.optionMenu(WIN_ID+"_showMenu", exists=True) and not show:
        show = cmds.optionMenu(WIN_ID+"_showMenu", q=True, v=True)
    if cmds.optionMenu(WIN_ID+"_epMenu", exists=True) and not EP:
        EP = cmds.optionMenu(WIN_ID+"_epMenu", q=True, v=True)
    if cmds.optionMenu(WIN_ID+"_seqMenu", exists=True) and not seq:
        seq = cmds.optionMenu(WIN_ID+"_seqMenu", q=True, v=True)
    if cmds.optionMenu(WIN_ID+"_shotMenu", exists=True) and not sh:
        sh = cmds.optionMenu(WIN_ID+"_shotMenu", q=True, v=True)
    _populate_menus(show, EP, seq, sh)
    _update_version_info_label()

# ============================ Scene I/O context & ops ============================

def _current_context():
    drive = cmds.textField(WIN_ID+"_drive", q=True, text=True).strip() or "V:/"
    show  = cmds.optionMenu(WIN_ID+"_showMenu", q=True, v=True)
    ep    = cmds.optionMenu(WIN_ID+"_epMenu",   q=True, v=True)
    sq    = cmds.optionMenu(WIN_ID+"_seqMenu",  q=True, v=True)
    sh    = cmds.optionMenu(WIN_ID+"_shotMenu", q=True, v=True)
    variance = cmds.textField(WIN_ID+"_variance", q=True, text=True).strip() or "master"
    return drive, show, ep, sq, sh, variance

def _refresh_tree(preserve=True, *_):
    cur_show = cmds.optionMenu(WIN_ID+"_showMenu", q=True, v=True) if preserve and cmds.optionMenu(WIN_ID+"_showMenu", exists=True) else None
    cur_ep   = cmds.optionMenu(WIN_ID+"_epMenu",   q=True, v=True) if preserve and cmds.optionMenu(WIN_ID+"_epMenu",   exists=True) else None
    cur_seq  = cmds.optionMenu(WIN_ID+"_seqMenu",  q=True, v=True) if preserve and cmds.optionMenu(WIN_ID+"_seqMenu",  exists=True) else None
    cur_shot = cmds.optionMenu(WIN_ID+"_shotMenu", q=True, v=True) if preserve and cmds.optionMenu(WIN_ID+"_shotMenu", exists=True) else None

    drive = cmds.textField(WIN_ID+"_drive", q=True, text=True).strip() or "V:/"
    drive = drive.replace("\\","/")
    if not os.path.isdir(drive):
        _log("[ERR] Drive not found: {}".format(drive))
        return

    cache = {}
    try:
        shows = sorted(next(os.walk(drive))[1])
    except StopIteration:
        shows = []
    for show in shows:
        show_scene = os.path.join(drive, show, "all", "scene").replace("\\","/")
        if not os.path.isdir(show_scene): continue
        cache[show] = {}
        try:
            eps = sorted([d for d in next(os.walk(show_scene))[1] if re.match(r'^Ep\d{2}$', d, re.IGNORECASE)])
        except StopIteration:
            eps = []
        for ep in eps:
            cache[show][ep] = {}
            ep_path = os.path.join(show_scene, ep).replace("\\","/")
            try:
                seqs = sorted([d for d in next(os.walk(ep_path))[1] if re.match(r'^sq\d{4}$', d, re.IGNORECASE)])
            except StopIteration:
                seqs = []
            for sq in seqs:
                cache[show][ep][sq] = {}
                sq_path = os.path.join(ep_path, sq).replace("\\","/")
                try:
                    shots = sorted([d for d in next(os.walk(sq_path))[1] if re.match(r'^SH\d{4}$', d, re.IGNORECASE)])
                except StopIteration:
                    shots = []
                for sh in shots:
                    cache[show][ep][sq][sh] = True

    global _io_cache
    _io_cache = cache

    if preserve and cur_show in _io_cache:
        _populate_menus(cur_show, cur_ep, cur_seq, cur_shot)
    else:
        _autobind_from_scene()

def _refresh_file_list_and_preview(*_):
    drive, show, ep, sq, sh, variance = _current_context()
    version_root = _version_root_v(drive, show, ep, sq, sh)
    files = _list_scenes_recursive(version_root)
    cmds.textScrollList(WIN_ID+"_fileList", e=True, removeAll=True)
    for f in files:
        cmds.textScrollList(WIN_ID+"_fileList", e=True, append=f)
    vtag = _scene_version_from_filename()
    preview = "{}_{}_{}_lighting_{}_{}.ma".format(ep, sq, sh, variance, vtag)
    cmds.textField(WIN_ID+"_preview", e=True, text=preview)
    _update_version_info_label()

def _on_open_scene(*_):
    sel = cmds.textScrollList(WIN_ID+"_fileList", q=True, si=True) or []
    if not sel:
        _log("[WARN] Select a scene to open.")
        return
    path = sel[0]
    try:
        cmds.file(path, o=True, f=True)
        _log("[OK] Opened: {}".format(path))
        _refresh_tree(preserve=True)
        _autobind_from_scene()
        _refresh_file_list_and_preview()
        node = _pick_shot_node_ui()
        if node and node != "Cancel":
            cmds.textField(WIN_ID+"_shotNode", e=True, text=node)
            _on_apply()  # sync prefix to current file version
    except Exception as e:
        _log("[ERR] " + str(e))

def _on_save_increment(*_):
    drive, show, ep, sq, sh, variance = _current_context()
    version_root = _version_root_v(drive, show, ep, sq, sh)
    if not os.path.isdir(version_root):
        try: os.makedirs(version_root)
        except Exception: pass
    nxt, _ = _next_version_tag_global(version_root, ep, sq, sh)
    target = os.path.join(version_root, "{}_{}_{}_lighting_{}_{}.ma".format(ep, sq, sh, variance, nxt)).replace("\\","/")
    try:
        cmds.file(rename=target)
        cmds.file(save=True, type="mayaAscii")
        _log("[SAVE] Increment -> {}".format(target))
        _refresh_file_list_and_preview()  # updates preview + version info
        _on_apply()                       # render prefix now matches this saved version
        _check_versions_info()            # log available versions; does not change current

        # Export shot data to JSON after successful save
        _export_shot_data_on_save(drive, show)

    except Exception as e:
        _log("[ERR] Failed to save: {}".format(e))

def _on_save_as(*_):
    drive, show, ep, sq, sh, variance = _current_context()
    version_root = _version_root_v(drive, show, ep, sq, sh)
    if not os.path.isdir(version_root):
        try: os.makedirs(version_root)
        except Exception: pass
    vtag = _scene_version_from_filename()
    target = os.path.join(version_root, "{}_{}_{}_lighting_{}_{}.ma".format(ep, sq, sh, variance, vtag)).replace("\\","/")
    if os.path.exists(target):
        _log("[WARN] File exists: {}".format(target))
    try:
        cmds.file(rename=target)
        cmds.file(save=True, type="mayaAscii")
        _log("[SAVE] {}".format(target))
        _refresh_file_list_and_preview()
        _on_apply()
        _check_versions_info()

        # Export shot data to JSON after successful save
        _export_shot_data_on_save(drive, show)

    except Exception as e:
        _log("[ERR] " + str(e))

# ============================ Version info label ============================

def _check_versions_info():
    drive, show, ep, sq, sh, variance = _current_context()
    version_root = _version_root_v(drive, show, ep, sq, sh)
    nxt, existing = _next_version_tag_global(version_root, ep, sq, sh)
    if existing:
        labels = ", ".join("v{:03d}".format(v) for v in existing)
        _log("[VERS] {}_{}_{} → found [{}], next {}".format(ep, sq, sh, labels, nxt))
    else:
        _log("[VERS] {}_{}_{} → none found, next {}".format(ep, sq, sh, nxt))
    return nxt

def _update_version_info_label():
    # Read-only status line: "Current: v### | Next: v###"
    current_v = _scene_version_from_filename()
    next_v = _check_versions_info()
    text = "Current: {0}    |    Next: {1}".format(current_v, next_v)
    if cmds.text(WIN_ID+"_versionInfo", exists=True):
        cmds.text(WIN_ID+"_versionInfo", e=True, label=text)

# ============================ Settings callbacks ============================

def _on_detect_shot(*_):
    node = _pick_shot_node_ui()
    if not node or node == "Cancel":
        _log("[WARN] No shot node selected/found.")
        return
    cmds.textField(WIN_ID+"_shotNode", e=True, text=node)

def _on_apply(*_):
    node = cmds.textField(WIN_ID+"_shotNode", q=True, text=True).strip()
    show_code = cmds.textField(WIN_ID+"_show", q=True, text=True).strip() or "SWA"
    try:
        info = apply_settings_from_shot(node, show_code=show_code)
        _log("[OK] Applied to render globals: {} {} {} {} | frames {}-{}".format(
            show_code, info["EP"], info["seq"], info["shot"], int(info["start"]), int(info["end"])
        ))
        _update_version_info_label()
    except Exception as e:
        _log("[ERR] " + str(e))

def _on_pick_show(*_):
    show = cmds.optionMenu(WIN_ID+"_showMenu", q=True, v=True)
    _populate_menus(show, None, None, None)

def _on_pick_ep(*_):
    show = cmds.optionMenu(WIN_ID+"_showMenu", q=True, v=True)
    ep   = cmds.optionMenu(WIN_ID+"_epMenu",   q=True, v=True)
    _populate_menus(show, ep, None, None)

def _on_pick_seq(*_):
    show = cmds.optionMenu(WIN_ID+"_showMenu", q=True, v=True)
    ep   = cmds.optionMenu(WIN_ID+"_epMenu",   q=True, v=True)
    seq  = cmds.optionMenu(WIN_ID+"_seqMenu",  q=True, v=True)
    _populate_menus(show, ep, seq, None)

def _on_pick_shot(*_):
    _refresh_file_list_and_preview()

def _on_variance_changed(*_):
    _refresh_file_list_and_preview()

# ============================ Window ============================

def show_ui():
    if cmds.window(WIN_ID, exists=True):
        cmds.deleteUI(WIN_ID, window=True)

    win = cmds.window(WIN_ID, title="Shot Setup + Redshift I/O", sizeable=True, widthHeight=(980, 660))
    form = cmds.formLayout(numberOfDivisions=100)
    tabs = cmds.tabLayout(parent=form, innerMarginWidth=8, innerMarginHeight=8)

    # --- Tab 1: Settings ---
    col1 = cmds.columnLayout(adjustableColumn=True)

    # Shot row (5)
    cmds.rowLayout(
        numberOfColumns=5, adjustableColumn=2,
        columnWidth=[(1,90),(2,420),(3,90),(4,90),(5,210)],
        columnAttach=[(1,'both',4),(2,'both',4),(3,'both',4),(4,'both',4),(5,'both',4)]
    )
    cmds.text(label="Shot Node:")
    cmds.textField(WIN_ID+"_shotNode", text="", editable=True)
    cmds.button(label="Detect…", c=_on_detect_shot)
    cmds.text(label="Show Code:")
    cmds.textField(WIN_ID+"_show", text="SWA")
    cmds.setParent("..")

    # Version info (not editable)
    cmds.rowLayout(
        numberOfColumns=2, adjustableColumn=2,
        columnWidth=[(1,90),(2,680)],
        columnAttach=[(1,'both',4),(2,'both',4)]
    )
    cmds.text(label="Version:")
    cmds.text(WIN_ID+"_versionInfo", label="Current: v001    |    Next: v001")
    cmds.setParent("..")

    # Apply
    cmds.rowLayout(
        numberOfColumns=2, adjustableColumn=2,
        columnWidth=[(1,160),(2,620)],
        columnAttach=[(1,'both',4),(2,'both',4)]
    )
    cmds.button(label="Apply Settings", bgc=(0.35,0.6,0.35), c=_on_apply)
    cmds.text(label="(Frames, render prefix W:/publish/<current v###>, Redshift, disable default light)")
    cmds.setParent("..")

    cmds.separator(h=10, style="in")
    cmds.scrollField(WIN_ID+"_log", height=200, editable=False, wordWrap=False)
    cmds.setParent("..")  # end Settings

    # --- Tab 2: Scene I/O ---
    col2 = cmds.columnLayout(adjustableColumn=True)

    # Drive + actions (8)
    cmds.rowLayout(
        numberOfColumns=8, adjustableColumn=2,
        columnWidth=[(1,120),(2,240),(3,110),(4,120),(5,140),(6,140),(7,160),(8,200)],
        columnAttach=[(1,'both',4),(2,'both',4),(3,'both',4),(4,'both',4),(5,'both',4),(6,'both',4),(7,'both',4),(8,'both',4)]
    )
    cmds.text(label="Scenes Drive:")
    cmds.textField(WIN_ID+"_drive", text="V:/")
    cmds.button(label="Refresh Tree", c=lambda *_: (_refresh_tree(preserve=True), _refresh_file_list_and_preview()))
    cmds.text(label="")
    cmds.button(label="Open Scene", c=_on_open_scene)
    cmds.button(label="Save As (.ma)", bgc=(0.35,0.6,0.35), c=_on_save_as)
    cmds.button(label="Save Increment", bgc=(0.35,0.6,0.85), c=_on_save_increment)
    cmds.button(label="Check Versions (log)", c=_check_versions_info)
    cmds.setParent("..")

    # Variance row (2)
    cmds.rowLayout(
        numberOfColumns=2, adjustableColumn=2,
        columnWidth=[(1,70),(2,600)],
        columnAttach=[(1,'both',4),(2,'both',4)]
    )
    cmds.text(label="Variance:")
    cmds.textField(WIN_ID+"_variance", text="master", cc=_on_variance_changed)
    cmds.setParent("..")

    # Pickers (8)
    cmds.rowLayout(
        numberOfColumns=8, adjustableColumn=8,
        columnWidth=[(1,60),(2,160),(3,40),(4,130),(5,40),(6,130),(7,40),(8,130)],
        columnAttach=[(1,'both',4),(2,'both',4),(3,'both',4),(4,'both',4),(5,'both',4),(6,'both',4),(7,'both',4),(8,'both',4)]
    )
    cmds.text(label="Show:")
    cmds.optionMenu(WIN_ID+"_showMenu", cc=_on_pick_show)
    cmds.text(label="EP:")
    cmds.optionMenu(WIN_ID+"_epMenu", cc=_on_pick_ep)
    cmds.text(label="Seq:")
    cmds.optionMenu(WIN_ID+"_seqMenu", cc=_on_pick_seq)
    cmds.text(label="Shot:")
    cmds.optionMenu(WIN_ID+"_shotMenu", cc=_on_pick_shot)
    cmds.setParent("..")

    # Preview + list (4)
    cmds.rowLayout(
        numberOfColumns=4, adjustableColumn=2,
        columnWidth=[(1,70),(2,420),(3,180),(4,240)],
        columnAttach=[(1,'both',4),(2,'both',4),(3,'both',4),(4,'both',4)]
    )
    cmds.text(label="Preview:")
    cmds.textField(WIN_ID+"_preview", text="", editable=False)
    cmds.text(label="(Recursive list below)")
    cmds.text(label="")
    cmds.setParent("..")

    cmds.text(label="Scenes under V:/…/lighting/version/ (recursive):")
    cmds.textScrollList(WIN_ID+"_fileList", height=280, allowMultiSelection=False)
    cmds.setParent("..")  # end Scene I/O

    cmds.tabLayout(tabs, e=True, tabLabel=((col1,"Settings"), (col2,"Scene I/O")))
    m=8
    cmds.formLayout(form, e=True,
        attachForm=[(tabs,'top',m),(tabs,'left',m),(tabs,'right',m),(tabs,'bottom',m)]
    )

    cmds.showWindow(win)

    # Initial bootstrap
    _refresh_tree(preserve=True)
    _autobind_from_scene()
    _refresh_file_list_and_preview()
    _update_version_info_label()

# ---------- Run ----------
show_ui()
