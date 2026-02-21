"""
Texture Reference Analyzer for Maya
Analyzes texture files across references to identify duplicates and help merge them.

Features:
- List all texture file nodes and their paths
- Group textures by file path to find duplicates
- Group textures by namespace/reference
- Show which references use each texture
- Identify opportunities to share textures across references
- Preview and remap texture connections

Author: Pipeline Tools
Version: 1.1.0
"""

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from collections import defaultdict
import os
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


class TextureInfo:
    """Information about a texture file node."""
    def __init__(self, node_name, file_path, reference_node=None, namespace=None):
        self.node_name = node_name
        self.file_path = file_path
        self.file_path_normalized = self._normalize_path(file_path)
        self.reference_node = reference_node
        self.namespace = namespace or ""
        self.is_referenced = reference_node is not None
        self.connected_shaders = []
        self.connected_objects = []
        self.node_type = ""
        
    def _normalize_path(self, path):
        """Normalize path for comparison."""
        if not path:
            return ""
        normalized = os.path.normpath(path).replace("\\", "/").lower()
        return normalized
    
    @property
    def file_name(self):
        """Get just the filename."""
        return os.path.basename(self.file_path) if self.file_path else ""
    
    @property
    def file_exists(self):
        """Check if file exists on disk."""
        if not self.file_path:
            return False
        expanded = os.path.expandvars(self.file_path)
        return os.path.exists(expanded)
    
    @property
    def short_node_name(self):
        """Get node name without namespace."""
        if ':' in self.node_name:
            return self.node_name.split(':')[-1]
        return self.node_name
    
    def __repr__(self):
        return f"TextureInfo({self.node_name}, {self.file_name}, ns={self.namespace})"


class TextureDuplicateGroup:
    """Group of textures sharing the same file path."""
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_path_normalized = os.path.normpath(file_path).replace("\\", "/").lower() if file_path else ""
        self.textures = []
        
    def add_texture(self, texture_info):
        self.textures.append(texture_info)
        
    @property
    def count(self):
        return len(self.textures)
    
    @property
    def is_duplicate(self):
        return self.count > 1
    
    @property
    def reference_count(self):
        """Number of unique references using this texture."""
        refs = set()
        for tex in self.textures:
            if tex.reference_node:
                refs.add(tex.reference_node)
            else:
                refs.add("_scene_")
        return len(refs)
    
    @property
    def namespaces(self):
        """List of unique namespaces."""
        ns = set()
        for tex in self.textures:
            ns.add(tex.namespace if tex.namespace else "(scene)")
        return sorted(ns)
    
    @property
    def file_name(self):
        return os.path.basename(self.file_path) if self.file_path else ""
    
    @property
    def master_texture(self):
        return self.textures[0] if self.textures else None
    
    @property
    def slave_textures(self):
        return self.textures[1:] if len(self.textures) > 1 else []


class NamespaceGroup:
    """Group of textures belonging to the same namespace/reference."""
    def __init__(self, namespace, reference_node=None, ref_file=None):
        self.namespace = namespace
        self.reference_node = reference_node
        self.ref_file = ref_file
        self.textures = []
        self.texture_by_path = defaultdict(list)  # normalized_path -> [TextureInfo]
        
    def add_texture(self, texture_info):
        self.textures.append(texture_info)
        self.texture_by_path[texture_info.file_path_normalized].append(texture_info)
        
    @property
    def count(self):
        return len(self.textures)
    
    @property
    def unique_path_count(self):
        """Number of unique texture paths."""
        return len(self.texture_by_path)
    
    @property
    def display_name(self):
        return self.namespace if self.namespace else "(Scene - Local)"
    
    @property
    def ref_file_name(self):
        if self.ref_file:
            return os.path.basename(self.ref_file)
        return ""
    
    def get_shared_textures_with(self, other_group):
        """Find textures shared with another namespace group."""
        shared = []
        for path in self.texture_by_path:
            if path in other_group.texture_by_path:
                shared.append({
                    'path': path,
                    'file_name': os.path.basename(self.textures[0].file_path) if self.textures else path,
                    'this_textures': self.texture_by_path[path],
                    'other_textures': other_group.texture_by_path[path]
                })
        return shared


class TextureAnalyzer:
    """Analyzes textures in the Maya scene."""
    
    FILE_NODE_TYPES = ['file', 'aiImage', 'RedshiftNormalMap', 'RedshiftSprite', 
                       'RedshiftDomeLight', 'PxrTexture', 'PxrNormalMap']
    
    FILE_ATTRS = {
        'file': 'fileTextureName',
        'aiImage': 'filename',
        'RedshiftNormalMap': 'tex0',
        'RedshiftSprite': 'tex0',
        'RedshiftDomeLight': 'tex0',
        'PxrTexture': 'filename',
        'PxrNormalMap': 'filename',
    }
    
    def __init__(self):
        self.all_textures = []
        self.duplicate_groups = []  # Grouped by path
        self.namespace_groups = []  # Grouped by namespace
        self.debug_log = []
        
    def log(self, msg):
        self.debug_log.append(msg)
        print(msg)
        
    def analyze(self, progress_callback=None):
        """Analyze all textures in the scene."""
        self.all_textures.clear()
        self.duplicate_groups.clear()
        self.namespace_groups.clear()
        self.debug_log.clear()
        
        self.log("Starting texture analysis...")
        
        # Find all file nodes
        all_file_nodes = []
        for node_type in self.FILE_NODE_TYPES:
            try:
                nodes = cmds.ls(type=node_type) or []
                all_file_nodes.extend([(n, node_type) for n in nodes])
            except:
                pass
        
        self.log(f"Found {len(all_file_nodes)} texture file nodes")
        
        # Analyze each file node
        total = len(all_file_nodes)
        for i, (node, node_type) in enumerate(all_file_nodes):
            if progress_callback:
                progress_callback(i + 1, total, f"Analyzing: {node}")
            
            texture_info = self._analyze_file_node(node, node_type)
            if texture_info:
                self.all_textures.append(texture_info)
        
        self.log(f"Analyzed {len(self.all_textures)} textures with valid paths")
        
        # Group by file path
        self._group_by_path()
        
        # Group by namespace
        self._group_by_namespace()
        
        # Get shader connections
        self._find_shader_connections()
        
        return self.duplicate_groups
    
    def _analyze_file_node(self, node, node_type):
        """Analyze a single file node."""
        attr_name = self.FILE_ATTRS.get(node_type, 'fileTextureName')
        full_attr = f"{node}.{attr_name}"
        
        if not cmds.objExists(full_attr):
            return None
        
        try:
            file_path = cmds.getAttr(full_attr) or ""
        except:
            file_path = ""
        
        if not file_path:
            return None
        
        # Check if referenced
        reference_node = None
        namespace = ""
        
        try:
            if cmds.referenceQuery(node, isNodeReferenced=True):
                reference_node = cmds.referenceQuery(node, referenceNode=True)
                namespace = cmds.referenceQuery(reference_node, namespace=True).lstrip(':')
        except:
            pass
        
        tex_info = TextureInfo(
            node_name=node,
            file_path=file_path,
            reference_node=reference_node,
            namespace=namespace
        )
        tex_info.node_type = node_type
        
        return tex_info
    
    def _group_by_path(self):
        """Group textures by their normalized file path."""
        path_groups = defaultdict(list)
        
        for tex in self.all_textures:
            key = tex.file_path_normalized
            path_groups[key].append(tex)
        
        for file_path, textures in path_groups.items():
            original_path = textures[0].file_path
            group = TextureDuplicateGroup(original_path)
            for tex in textures:
                group.add_texture(tex)
            self.duplicate_groups.append(group)
        
        self.duplicate_groups.sort(key=lambda x: x.count, reverse=True)
        
        dup_count = sum(1 for g in self.duplicate_groups if g.is_duplicate)
        self.log(f"Found {dup_count} texture paths with duplicates")
    
    def _group_by_namespace(self):
        """Group textures by their namespace/reference."""
        ns_dict = {}
        
        for tex in self.all_textures:
            ns = tex.namespace or ""
            
            if ns not in ns_dict:
                ref_file = None
                if tex.reference_node:
                    try:
                        ref_file = cmds.referenceQuery(tex.reference_node, filename=True, shortName=True)
                    except:
                        pass
                ns_dict[ns] = NamespaceGroup(ns, tex.reference_node, ref_file)
            
            ns_dict[ns].add_texture(tex)
        
        self.namespace_groups = list(ns_dict.values())
        self.namespace_groups.sort(key=lambda x: (x.namespace == "", x.namespace))
        
        self.log(f"Found {len(self.namespace_groups)} namespaces/references")
    
    def _find_shader_connections(self):
        """Find what shaders each texture connects to."""
        for tex in self.all_textures:
            try:
                connections = cmds.listConnections(tex.node_name, 
                                                   source=False, 
                                                   destination=True,
                                                   type='shadingDependNode') or []
                materials = cmds.listConnections(tex.node_name,
                                                 source=False,
                                                 destination=True,
                                                 type='lambert') or []
                tex.connected_shaders = list(set(connections + materials))
            except:
                pass
    
    def find_cross_reference_duplicates(self):
        """
        Find textures that are duplicated across different references.
        Returns list of dicts with sharing info.
        """
        cross_ref_dups = []
        
        for group in self.duplicate_groups:
            if not group.is_duplicate:
                continue
            
            # Check if textures span multiple namespaces
            namespaces = set()
            for tex in group.textures:
                namespaces.add(tex.namespace or "(scene)")
            
            if len(namespaces) > 1:
                cross_ref_dups.append({
                    'file_path': group.file_path,
                    'file_name': group.file_name,
                    'namespaces': sorted(namespaces),
                    'textures': group.textures,
                    'count': group.count
                })
        
        return cross_ref_dups


class TextureMerger:
    """Handles merging/remapping of duplicate textures."""
    
    def __init__(self):
        self.log_messages = []
        
    def log(self, msg):
        self.log_messages.append(msg)
        print(msg)
        
    def clear_log(self):
        self.log_messages.clear()
    
    def get_texture_connections(self, texture_node):
        """Get all outgoing connections from a texture node."""
        connections = []
        
        try:
            conns = cmds.listConnections(texture_node, 
                                         source=False, 
                                         destination=True,
                                         connections=True,
                                         plugs=True) or []
            
            for i in range(0, len(conns), 2):
                source_plug = conns[i]
                dest_plug = conns[i + 1]
                connections.append((source_plug, dest_plug))
                
        except Exception as e:
            self.log(f"Error getting connections for {texture_node}: {e}")
        
        return connections
    
    def remap_texture_connections(self, slave_texture, master_texture, dry_run=False):
        """Remap all connections from slave texture to master texture."""
        self.log(f"\nRemapping: {slave_texture.node_name}")
        self.log(f"  -> Master: {master_texture.node_name}")
        
        if not cmds.objExists(slave_texture.node_name):
            self.log(f"  ERROR: Slave node does not exist")
            return False
        
        if not cmds.objExists(master_texture.node_name):
            self.log(f"  ERROR: Master node does not exist")
            return False
        
        connections = self.get_texture_connections(slave_texture.node_name)
        self.log(f"  Found {len(connections)} connections to remap")
        
        if dry_run:
            for src, dst in connections:
                self.log(f"  [DRY RUN] Would remap: {src} -> {dst}")
            return True
        
        success_count = 0
        for src_plug, dst_plug in connections:
            try:
                src_attr = src_plug.split('.')[-1]
                new_src = f"{master_texture.node_name}.{src_attr}"
                
                if not cmds.objExists(new_src):
                    self.log(f"  WARNING: Attribute {new_src} doesn't exist, skipping")
                    continue
                
                dst_node = dst_plug.split('.')[0]
                try:
                    if cmds.referenceQuery(dst_node, isNodeReferenced=True):
                        self.log(f"  SKIP: {dst_plug} is referenced (cannot modify)")
                        continue
                except:
                    pass
                
                if cmds.isConnected(src_plug, dst_plug):
                    cmds.disconnectAttr(src_plug, dst_plug)
                
                cmds.connectAttr(new_src, dst_plug, force=True)
                self.log(f"  ✓ Remapped: {new_src} -> {dst_plug}")
                success_count += 1
                
            except Exception as e:
                self.log(f"  ERROR remapping {src_plug} -> {dst_plug}: {e}")
        
        self.log(f"  Remapped {success_count}/{len(connections)} connections")
        return success_count > 0
    
    def merge_duplicate_group(self, duplicate_group, dry_run=False):
        """Merge a group of duplicate textures."""
        if not duplicate_group.is_duplicate:
            self.log(f"Skipping {duplicate_group.file_name} - not a duplicate")
            return False
        
        self.log(f"\n{'='*60}")
        self.log(f"Merging duplicates for: {duplicate_group.file_name}")
        self.log(f"File path: {duplicate_group.file_path}")
        self.log(f"Total instances: {duplicate_group.count}")
        self.log(f"{'='*60}")
        
        master = duplicate_group.master_texture
        slaves = duplicate_group.slave_textures
        
        self.log(f"\nMaster (keep): {master.node_name}")
        self.log(f"  Namespace: {master.namespace or '(scene)'}")
        
        for i, slave in enumerate(slaves, 1):
            self.log(f"\nSlave {i}/{len(slaves)}: {slave.node_name}")
            self.log(f"  Namespace: {slave.namespace or '(scene)'}")
            self.remap_texture_connections(slave, master, dry_run)
        
        return True


# ============================================================================
# UI Components
# ============================================================================

class TextureTreeWidget(QtWidgets.QTreeWidget):
    """Tree widget for displaying textures grouped by path."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setHeaderLabels([
            "Texture Path / Node",
            "Namespace/Reference",
            "Count",
            "Status"
        ])
        
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setRootIsDecorated(True)
        self.setSortingEnabled(True)
        
        header = self.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        self.setColumnWidth(0, 450)
        self.setColumnWidth(1, 200)
        self.setColumnWidth(2, 60)
        
    def populate(self, duplicate_groups, show_single=True, filter_text=""):
        """Populate tree with texture groups."""
        self.clear()
        
        dup_count = 0
        single_count = 0
        total_textures = 0
        
        filter_lower = filter_text.lower()
        
        for group in duplicate_groups:
            if filter_lower:
                match = (filter_lower in group.file_path.lower() or
                        filter_lower in group.file_name.lower() or
                        any(filter_lower in tex.namespace.lower() for tex in group.textures))
                if not match:
                    continue
            
            if not show_single and not group.is_duplicate:
                single_count += 1
                total_textures += 1
                continue
            
            group_item = QtWidgets.QTreeWidgetItem()
            group_item.setData(0, QtCore.Qt.UserRole, group)
            
            if group.is_duplicate:
                icon = "⚠️"
                color = QtGui.QColor("#ff9900")
                status = f"DUPLICATE - {group.reference_count} refs"
                group_item.setCheckState(0, QtCore.Qt.Unchecked)
                dup_count += 1
            else:
                icon = "✓"
                color = QtGui.QColor("#666666")
                status = "Unique"
                single_count += 1
            
            if group.textures and not group.textures[0].file_exists:
                icon = "❌"
                color = QtGui.QColor("#ff4444")
                status += " (MISSING)"
            
            group_item.setText(0, f"{icon} {group.file_name}")
            group_item.setToolTip(0, group.file_path)
            group_item.setForeground(0, QtGui.QBrush(color))
            group_item.setText(2, str(group.count))
            group_item.setText(3, status)
            
            total_textures += group.count
            
            for i, tex in enumerate(group.textures):
                tex_item = QtWidgets.QTreeWidgetItem()
                tex_item.setData(0, QtCore.Qt.UserRole, tex)
                
                if i == 0 and group.is_duplicate:
                    prefix = "👑"
                    tex_color = QtGui.QColor("#00cc00")
                elif group.is_duplicate:
                    prefix = "📋"
                    tex_color = QtGui.QColor("#ffaa00")
                else:
                    prefix = "📄"
                    tex_color = QtGui.QColor("#888888")
                
                tex_item.setText(0, f"    {prefix} {tex.node_name}")
                tex_item.setText(1, tex.namespace or "(scene)")
                tex_item.setForeground(0, QtGui.QBrush(tex_color))
                
                if tex.connected_shaders:
                    shader_str = ", ".join(tex.connected_shaders[:3])
                    if len(tex.connected_shaders) > 3:
                        shader_str += f" (+{len(tex.connected_shaders)-3})"
                    tex_item.setText(3, f"→ {shader_str}")
                
                group_item.addChild(tex_item)
            
            self.addTopLevelItem(group_item)
            
            if group.is_duplicate:
                group_item.setExpanded(True)
        
        return total_textures, dup_count, single_count
    
    def get_checked_groups(self):
        checked = []
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.checkState(0) == QtCore.Qt.Checked:
                group = item.data(0, QtCore.Qt.UserRole)
                if group and group.is_duplicate:
                    checked.append(group)
        return checked
    
    def get_all_duplicate_groups(self):
        groups = []
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            group = item.data(0, QtCore.Qt.UserRole)
            if group and group.is_duplicate:
                groups.append(group)
        return groups
    
    def select_all_duplicates(self):
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            group = item.data(0, QtCore.Qt.UserRole)
            if group and group.is_duplicate:
                item.setCheckState(0, QtCore.Qt.Checked)
    
    def select_none(self):
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            try:
                item.setCheckState(0, QtCore.Qt.Unchecked)
            except:
                pass


class NamespaceTreeWidget(QtWidgets.QTreeWidget):
    """Tree widget for displaying textures grouped by namespace."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setHeaderLabels([
            "Namespace / Texture",
            "File Path",
            "Count",
            "Reference File"
        ])
        
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setRootIsDecorated(True)
        self.setSortingEnabled(True)
        
        header = self.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        self.setColumnWidth(0, 350)
        self.setColumnWidth(1, 300)
        self.setColumnWidth(2, 60)
        
    def populate(self, namespace_groups, filter_text=""):
        """Populate tree with namespace groups."""
        self.clear()
        
        filter_lower = filter_text.lower()
        
        total_namespaces = 0
        total_textures = 0
        
        for ns_group in namespace_groups:
            # Apply filter
            if filter_lower:
                match = (filter_lower in ns_group.namespace.lower() or
                        filter_lower in (ns_group.ref_file or "").lower() or
                        any(filter_lower in tex.file_path.lower() for tex in ns_group.textures))
                if not match:
                    continue
            
            total_namespaces += 1
            
            # Create namespace item
            ns_item = QtWidgets.QTreeWidgetItem()
            ns_item.setData(0, QtCore.Qt.UserRole, ns_group)
            
            # Icon based on whether it's referenced or local
            if ns_group.namespace:
                icon = "📦"
                color = QtGui.QColor("#6699cc")
            else:
                icon = "🏠"
                color = QtGui.QColor("#88cc88")
            
            ns_item.setText(0, f"{icon} {ns_group.display_name}")
            ns_item.setText(2, str(ns_group.count))
            ns_item.setText(3, ns_group.ref_file_name or "(local)")
            ns_item.setForeground(0, QtGui.QBrush(color))
            ns_item.setExpanded(False)
            
            # Group textures by path within this namespace
            for path, textures in sorted(ns_group.texture_by_path.items()):
                total_textures += len(textures)
                
                if len(textures) == 1:
                    # Single texture - show directly
                    tex = textures[0]
                    tex_item = QtWidgets.QTreeWidgetItem()
                    tex_item.setData(0, QtCore.Qt.UserRole, tex)
                    tex_item.setText(0, f"    📄 {tex.short_node_name}")
                    tex_item.setText(1, tex.file_name)
                    tex_item.setToolTip(1, tex.file_path)
                    tex_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#888888")))
                    
                    if not tex.file_exists:
                        tex_item.setText(0, f"    ❌ {tex.short_node_name}")
                        tex_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#ff4444")))
                        tex_item.setText(3, "MISSING")
                    
                    ns_item.addChild(tex_item)
                else:
                    # Multiple textures with same path - group them
                    path_item = QtWidgets.QTreeWidgetItem()
                    path_item.setText(0, f"    ⚠️ {textures[0].file_name}")
                    path_item.setText(1, f"{len(textures)} nodes, same file")
                    path_item.setToolTip(1, textures[0].file_path)
                    path_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#ffaa00")))
                    path_item.setText(2, str(len(textures)))
                    
                    for tex in textures:
                        tex_item = QtWidgets.QTreeWidgetItem()
                        tex_item.setData(0, QtCore.Qt.UserRole, tex)
                        tex_item.setText(0, f"        📄 {tex.short_node_name}")
                        tex_item.setText(1, tex.node_type)
                        tex_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#888888")))
                        path_item.addChild(tex_item)
                    
                    ns_item.addChild(path_item)
            
            self.addTopLevelItem(ns_item)
        
        return total_namespaces, total_textures
    
    def expand_all_namespaces(self):
        """Expand all top-level namespace items."""
        for i in range(self.topLevelItemCount()):
            self.topLevelItem(i).setExpanded(True)
    
    def collapse_all_namespaces(self):
        """Collapse all top-level namespace items."""
        for i in range(self.topLevelItemCount()):
            self.topLevelItem(i).setExpanded(False)


class CrossRefTreeWidget(QtWidgets.QTreeWidget):
    """Tree widget showing textures shared across references."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setHeaderLabels([
            "Shared Texture",
            "Used By Namespaces",
            "Count",
            "Potential Savings"
        ])
        
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setRootIsDecorated(True)
        
        header = self.header()
        header.setStretchLastSection(True)
        self.setColumnWidth(0, 350)
        self.setColumnWidth(1, 300)
        self.setColumnWidth(2, 60)
        
    def populate(self, cross_ref_dups):
        """Populate with cross-reference duplicates."""
        self.clear()
        
        total_potential_savings = 0
        
        for dup in cross_ref_dups:
            item = QtWidgets.QTreeWidgetItem()
            item.setData(0, QtCore.Qt.UserRole, dup)
            
            item.setText(0, f"🔗 {dup['file_name']}")
            item.setToolTip(0, dup['file_path'])
            item.setText(1, ", ".join(dup['namespaces']))
            item.setText(2, str(dup['count']))
            
            savings = dup['count'] - 1
            total_potential_savings += savings
            item.setText(3, f"-{savings} textures")
            
            item.setForeground(0, QtGui.QBrush(QtGui.QColor("#ff9900")))
            
            # Add child items for each texture
            for tex in dup['textures']:
                tex_item = QtWidgets.QTreeWidgetItem()
                tex_item.setData(0, QtCore.Qt.UserRole, tex)
                tex_item.setText(0, f"    📄 {tex.node_name}")
                tex_item.setText(1, tex.namespace or "(scene)")
                tex_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#888888")))
                item.addChild(tex_item)
            
            item.setExpanded(True)
            self.addTopLevelItem(item)
        
        return len(cross_ref_dups), total_potential_savings


class TextureAnalyzerUI(QtWidgets.QDialog):
    """Main UI for Texture Analyzer."""
    
    WINDOW_TITLE = "Texture Reference Analyzer v1.1"
    
    def __init__(self, parent=get_maya_main_window()):
        super().__init__(parent)
        
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(1000, 850)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        self.analyzer = TextureAnalyzer()
        self.merger = TextureMerger()
        self.duplicate_groups = []
        
        self._create_ui()
        self._create_connections()
        
    def _create_ui(self):
        """Build the UI."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        
        # === Header ===
        header = QtWidgets.QLabel(
            "Analyze texture files across references to identify duplicates.\n"
            "View by texture path or by namespace/reference."
        )
        header.setStyleSheet("color: #888; font-style: italic;")
        main_layout.addWidget(header)
        
        # === Step 1: Analyze ===
        step1 = self._create_group("Step 1: Analyze Scene Textures")
        step1_layout = step1.layout()
        
        analyze_layout = QtWidgets.QHBoxLayout()
        
        self.analyze_btn = QtWidgets.QPushButton("🔍 Analyze All Textures")
        self.analyze_btn.setMinimumHeight(36)
        
        self.refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        self.refresh_btn.setFixedWidth(100)
        
        analyze_layout.addWidget(self.analyze_btn)
        analyze_layout.addWidget(self.refresh_btn)
        step1_layout.addLayout(analyze_layout)
        
        main_layout.addWidget(step1)
        
        # === Step 2: Review with Tabs ===
        step2 = self._create_group("Step 2: Review Textures")
        step2_layout = step2.layout()
        
        # Filter bar
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(QtWidgets.QLabel("Filter:"))
        self.filter_edit = QtWidgets.QLineEdit()
        self.filter_edit.setPlaceholderText("Filter by path, filename, or namespace...")
        self.filter_edit.setClearButtonEnabled(True)
        filter_layout.addWidget(self.filter_edit)
        step2_layout.addLayout(filter_layout)
        
        # Stats
        self.stats_label = QtWidgets.QLabel("No textures analyzed yet")
        self.stats_label.setStyleSheet("color: #888;")
        step2_layout.addWidget(self.stats_label)
        
        # Tab widget for different views
        self.view_tabs = QtWidgets.QTabWidget()
        
        # Tab 1: Group by Path
        path_tab = QtWidgets.QWidget()
        path_layout = QtWidgets.QVBoxLayout(path_tab)
        
        path_options = QtWidgets.QHBoxLayout()
        self.show_single_cb = QtWidgets.QCheckBox("Show unique textures")
        self.show_single_cb.setChecked(False)
        path_options.addWidget(self.show_single_cb)
        path_options.addStretch()
        path_layout.addLayout(path_options)
        
        self.texture_tree = TextureTreeWidget()
        path_layout.addWidget(self.texture_tree)
        
        path_btn_layout = QtWidgets.QHBoxLayout()
        self.select_all_btn = QtWidgets.QPushButton("☑ Select All Duplicates")
        self.select_none_btn = QtWidgets.QPushButton("☐ Select None")
        self.select_in_maya_btn = QtWidgets.QPushButton("👁 Select in Maya")
        path_btn_layout.addWidget(self.select_all_btn)
        path_btn_layout.addWidget(self.select_none_btn)
        path_btn_layout.addStretch()
        path_btn_layout.addWidget(self.select_in_maya_btn)
        path_layout.addLayout(path_btn_layout)
        
        self.view_tabs.addTab(path_tab, "📁 Group by Texture Path")
        
        # Tab 2: Group by Namespace
        ns_tab = QtWidgets.QWidget()
        ns_layout = QtWidgets.QVBoxLayout(ns_tab)
        
        self.namespace_tree = NamespaceTreeWidget()
        ns_layout.addWidget(self.namespace_tree)
        
        ns_btn_layout = QtWidgets.QHBoxLayout()
        self.expand_all_btn = QtWidgets.QPushButton("▼ Expand All")
        self.collapse_all_btn = QtWidgets.QPushButton("▶ Collapse All")
        self.select_ns_maya_btn = QtWidgets.QPushButton("👁 Select in Maya")
        ns_btn_layout.addWidget(self.expand_all_btn)
        ns_btn_layout.addWidget(self.collapse_all_btn)
        ns_btn_layout.addStretch()
        ns_btn_layout.addWidget(self.select_ns_maya_btn)
        ns_layout.addLayout(ns_btn_layout)
        
        self.view_tabs.addTab(ns_tab, "📦 Group by Namespace")
        
        # Tab 3: Cross-Reference Duplicates
        cross_tab = QtWidgets.QWidget()
        cross_layout = QtWidgets.QVBoxLayout(cross_tab)
        
        cross_info = QtWidgets.QLabel(
            "These textures are loaded multiple times by different references.\n"
            "Merging them would reduce memory usage."
        )
        cross_info.setStyleSheet("color: #cc8800;")
        cross_layout.addWidget(cross_info)
        
        self.cross_ref_tree = CrossRefTreeWidget()
        cross_layout.addWidget(self.cross_ref_tree)
        
        self.cross_stats_label = QtWidgets.QLabel("")
        self.cross_stats_label.setStyleSheet("color: #88cc88; font-weight: bold;")
        cross_layout.addWidget(self.cross_stats_label)
        
        self.view_tabs.addTab(cross_tab, "🔗 Cross-Reference Duplicates")
        
        step2_layout.addWidget(self.view_tabs)
        
        main_layout.addWidget(step2)
        
        # === Step 3: Merge ===
        step3 = self._create_group("Step 3: Merge Duplicate Textures")
        step3_layout = step3.layout()
        
        merge_info = QtWidgets.QLabel(
            "Merging will reconnect shaders to use a single texture instead of duplicates.\n"
            "⚠️ Only non-referenced connections can be remapped. Referenced shaders cannot be modified."
        )
        merge_info.setStyleSheet("color: #cc8800;")
        step3_layout.addWidget(merge_info)
        
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        step3_layout.addWidget(self.progress_bar)
        
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("color: #888;")
        step3_layout.addWidget(self.status_label)
        
        btn_layout = QtWidgets.QHBoxLayout()
        
        self.dry_run_btn = QtWidgets.QPushButton("🔬 Dry Run (Preview)")
        self.dry_run_btn.setMinimumHeight(40)
        
        self.merge_btn = QtWidgets.QPushButton("🔗 Merge Selected")
        self.merge_btn.setMinimumHeight(40)
        self.merge_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5a2d;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3d7a3d; }
        """)
        
        self.merge_all_btn = QtWidgets.QPushButton("🔗 Merge ALL Duplicates")
        self.merge_all_btn.setMinimumHeight(40)
        self.merge_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #5a2d2d;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7a3d3d; }
        """)
        
        self.export_btn = QtWidgets.QPushButton("📋 Export List")
        self.export_btn.setMinimumHeight(40)
        
        btn_layout.addWidget(self.dry_run_btn)
        btn_layout.addWidget(self.merge_btn)
        btn_layout.addWidget(self.merge_all_btn)
        btn_layout.addWidget(self.export_btn)
        step3_layout.addLayout(btn_layout)
        
        main_layout.addWidget(step3)
        
        # === Log ===
        log_group = QtWidgets.QGroupBox("Log Output")
        log_layout = QtWidgets.QVBoxLayout(log_group)
        
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
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
        
    def _create_group(self, title):
        """Create styled group box."""
        group = QtWidgets.QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        QtWidgets.QVBoxLayout(group)
        return group
    
    def _create_connections(self):
        """Connect signals."""
        self.analyze_btn.clicked.connect(self._on_analyze)
        self.refresh_btn.clicked.connect(self._on_analyze)
        self.filter_edit.textChanged.connect(self._on_filter_changed)
        self.show_single_cb.stateChanged.connect(self._on_filter_changed)
        self.select_all_btn.clicked.connect(self.texture_tree.select_all_duplicates)
        self.select_none_btn.clicked.connect(self.texture_tree.select_none)
        self.select_in_maya_btn.clicked.connect(self._on_select_in_maya)
        self.select_ns_maya_btn.clicked.connect(self._on_select_ns_in_maya)
        self.expand_all_btn.clicked.connect(self.namespace_tree.expand_all_namespaces)
        self.collapse_all_btn.clicked.connect(self.namespace_tree.collapse_all_namespaces)
        self.export_btn.clicked.connect(self._on_export)
        self.dry_run_btn.clicked.connect(self._on_dry_run)
        self.merge_btn.clicked.connect(self._on_merge_selected)
        self.merge_all_btn.clicked.connect(self._on_merge_all)
        self.clear_log_btn.clicked.connect(self.log_text.clear)
        self.texture_tree.itemDoubleClicked.connect(self._on_tree_double_click)
        self.namespace_tree.itemDoubleClicked.connect(self._on_ns_tree_double_click)
        self.cross_ref_tree.itemDoubleClicked.connect(self._on_cross_tree_double_click)
        
    def _log(self, msg, color=None):
        """Add to log."""
        if color:
            self.log_text.append(f'<span style="color:{color}">{msg}</span>')
        else:
            self.log_text.append(msg)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def _on_analyze(self):
        """Analyze scene textures."""
        self._log(f"\n{'='*50}")
        self._log("Analyzing scene textures...")
        self.status_label.setText("Analyzing...")
        
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        QtWidgets.QApplication.processEvents()
        
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            def progress_callback(current, total, msg):
                self.progress_bar.setValue(int((current / total) * 100))
                QtWidgets.QApplication.processEvents()
            
            self.duplicate_groups = self.analyzer.analyze(progress_callback)
            
            # Refresh all views
            self._refresh_all_views()
            
            # Stats
            total_tex = len(self.analyzer.all_textures)
            dup_groups = sum(1 for g in self.duplicate_groups if g.is_duplicate)
            dup_textures = sum(g.count for g in self.duplicate_groups if g.is_duplicate)
            potential_savings = sum(g.count - 1 for g in self.duplicate_groups if g.is_duplicate)
            
            self.stats_label.setText(
                f"Total: {total_tex} textures | "
                f"{len(self.duplicate_groups)} unique paths | "
                f"{len(self.analyzer.namespace_groups)} namespaces | "
                f"{dup_groups} duplicated paths | "
                f"Savings: {potential_savings} textures"
            )
            
            if dup_groups > 0:
                self.stats_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
                self._log(f"✓ Found {dup_groups} texture paths with duplicates!", "#ffaa00")
            else:
                self.stats_label.setStyleSheet("color: #88cc88;")
                self._log("✓ No duplicate textures found.", "#88cc88")
            
            self.status_label.setText("Analysis complete")
            
        except Exception as e:
            self._log(f"Error: {e}", "#ff6666")
            import traceback
            self._log(traceback.format_exc(), "#ff6666")
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.progress_bar.setVisible(False)
    
    def _refresh_all_views(self):
        """Refresh all tree views."""
        filter_text = self.filter_edit.text()
        show_single = self.show_single_cb.isChecked()
        
        # Path view
        self.texture_tree.populate(self.duplicate_groups, show_single, filter_text)
        
        # Namespace view
        self.namespace_tree.populate(self.analyzer.namespace_groups, filter_text)
        
        # Cross-reference view
        cross_ref_dups = self.analyzer.find_cross_reference_duplicates()
        count, savings = self.cross_ref_tree.populate(cross_ref_dups)
        self.cross_stats_label.setText(
            f"Found {count} textures shared across references. "
            f"Potential savings: {savings} texture nodes."
        )
    
    def _on_filter_changed(self):
        """Handle filter change."""
        self._refresh_all_views()
        
    def _on_tree_double_click(self, item, column):
        """Handle double-click on path tree."""
        self._on_select_in_maya()
    
    def _on_ns_tree_double_click(self, item, column):
        """Handle double-click on namespace tree."""
        self._on_select_ns_in_maya()
    
    def _on_cross_tree_double_click(self, item, column):
        """Handle double-click on cross-ref tree."""
        data = item.data(0, QtCore.Qt.UserRole)
        if isinstance(data, TextureInfo):
            if cmds.objExists(data.node_name):
                cmds.select(data.node_name, replace=True)
                self._log(f"Selected: {data.node_name}")
        elif isinstance(data, dict):
            nodes = [tex.node_name for tex in data['textures'] if cmds.objExists(tex.node_name)]
            if nodes:
                cmds.select(nodes, replace=True)
                self._log(f"Selected {len(nodes)} texture nodes")
        
    def _on_select_in_maya(self):
        """Select texture node in Maya from path tree."""
        item = self.texture_tree.currentItem()
        if not item:
            return
        
        data = item.data(0, QtCore.Qt.UserRole)
        
        if isinstance(data, TextureDuplicateGroup):
            nodes = [tex.node_name for tex in data.textures if cmds.objExists(tex.node_name)]
            if nodes:
                cmds.select(nodes, replace=True)
                self._log(f"Selected {len(nodes)} texture nodes")
        elif isinstance(data, TextureInfo):
            if cmds.objExists(data.node_name):
                cmds.select(data.node_name, replace=True)
                self._log(f"Selected: {data.node_name}")
    
    def _on_select_ns_in_maya(self):
        """Select texture node in Maya from namespace tree."""
        item = self.namespace_tree.currentItem()
        if not item:
            return
        
        data = item.data(0, QtCore.Qt.UserRole)
        
        if isinstance(data, NamespaceGroup):
            nodes = [tex.node_name for tex in data.textures if cmds.objExists(tex.node_name)]
            if nodes:
                cmds.select(nodes, replace=True)
                self._log(f"Selected {len(nodes)} texture nodes from {data.display_name}")
        elif isinstance(data, TextureInfo):
            if cmds.objExists(data.node_name):
                cmds.select(data.node_name, replace=True)
                self._log(f"Selected: {data.node_name}")
    
    def _on_export(self):
        """Export texture list to file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Texture List", "", "CSV Files (*.csv);;Text Files (*.txt)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w') as f:
                f.write("Namespace,Texture Node,File Path,File Name,Is Duplicate,Duplicate Count,File Exists\n")
                for group in self.duplicate_groups:
                    for tex in group.textures:
                        f.write(f'"{tex.namespace or "(scene)}",'
                               f'"{tex.node_name}",'
                               f'"{group.file_path}",'
                               f'"{group.file_name}",'
                               f'{group.is_duplicate},'
                               f'{group.count},'
                               f'{tex.file_exists}\n')
            
            self._log(f"✓ Exported to: {file_path}", "#88cc88")
        except Exception as e:
            self._log(f"Error exporting: {e}", "#ff6666")
    
    def _on_dry_run(self):
        """Dry run merge."""
        selected = self.texture_tree.get_checked_groups()
        if not selected:
            selected = self.texture_tree.get_all_duplicate_groups()
        
        if not selected:
            self._log("No duplicate groups to process", "#ffaa00")
            return
        
        self._log(f"\n{'='*50}", "#88ccff")
        self._log("DRY RUN - No changes will be made", "#88ccff")
        self._log(f"{'='*50}")
        
        self._execute_merge(selected, dry_run=True)
        
    def _on_merge_selected(self):
        """Merge selected groups."""
        selected = self.texture_tree.get_checked_groups()
        if not selected:
            self._log("No groups selected. Check boxes to select.", "#ffaa00")
            return
        self._confirm_and_merge(selected)
        
    def _on_merge_all(self):
        """Merge all duplicates."""
        all_dups = self.texture_tree.get_all_duplicate_groups()
        if not all_dups:
            self._log("No duplicates to merge", "#ffaa00")
            return
        self._confirm_and_merge(all_dups)
    
    def _confirm_and_merge(self, groups):
        """Confirm and execute merge."""
        total = sum(g.count - 1 for g in groups)
        
        result = QtWidgets.QMessageBox.question(
            self,
            "Confirm Merge",
            f"This will remap {total} duplicate texture connections.\n\n"
            f"• {len(groups)} texture paths selected\n"
            f"• Referenced connections cannot be modified\n\n"
            "Continue?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if result != QtWidgets.QMessageBox.Yes:
            return
        
        self._log(f"\n{'='*50}", "#ff9900")
        self._log("MERGING - Making changes", "#ff9900")
        self._log(f"{'='*50}")
        
        self._execute_merge(groups, dry_run=False)
        
    def _execute_merge(self, groups, dry_run=False):
        """Execute the merge."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        
        try:
            self.merger.clear_log()
            
            total = len(groups)
            for i, group in enumerate(groups, 1):
                self.progress_bar.setValue(int((i / total) * 100))
                self.status_label.setText(f"Processing: {group.file_name}")
                QtWidgets.QApplication.processEvents()
                
                self.merger.merge_duplicate_group(group, dry_run)
            
            for msg in self.merger.log_messages:
                if "ERROR" in msg:
                    self._log(msg, "#ff6666")
                elif "✓" in msg:
                    self._log(msg, "#88cc88")
                elif "SKIP" in msg or "WARNING" in msg:
                    self._log(msg, "#ffaa00")
                elif "DRY RUN" in msg:
                    self._log(msg, "#88ccff")
                else:
                    self._log(msg)
            
            if not dry_run:
                self._log("\n✓ Merge complete!", "#88cc88")
                self.status_label.setText("Merge complete!")
            else:
                self.status_label.setText("Dry run complete")
                
        except Exception as e:
            self._log(f"Error: {e}", "#ff6666")
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.progress_bar.setVisible(False)


def show():
    """Show the Texture Analyzer UI."""
    global texture_analyzer_ui
    
    try:
        texture_analyzer_ui.close()
        texture_analyzer_ui.deleteLater()
    except:
        pass
    
    texture_analyzer_ui = TextureAnalyzerUI()
    texture_analyzer_ui.show()
    return texture_analyzer_ui


if __name__ == "__main__":
    show()