"""
SETS Instance Builder for Maya
Builds SETS with instance optimization - references geometry ONCE per unique
component and uses Maya instances for duplicates.

Process:
1. List SETS files from anim publish path ({root}/{project}/all/scene/{ep}/{seq}/{shot}/anim/publish/{version}/)
2. Import SETS alembic → gets locators with transforms
3. Walk locators → extract component names → group by component (find duplicates)
4. For FIRST locator of each component: Reference geo + shader as MASTER
5. For DUPLICATE locators: Create instance of master's geo, parent to locator

This reduces scene complexity from N references to 1 reference + (N-1) instances.

Author: Pipeline Tools
Version: 1.0.0
"""

import maya.cmds as cmds
import os
import re
from collections import defaultdict


# ============================================================================
# Helper Functions (matching igl_shot_build.py patterns)
# ============================================================================

def _short(node):
    """Get short name from full path."""
    return node.split(":")[-1] if node else node


def _ensure_group_exists(group_name):
    """Ensure a group exists in the scene, create if not."""
    if not cmds.objExists(group_name):
        cmds.group(empty=True, name=group_name)
        print("[SETS Builder] Created group: {}".format(group_name))
    return group_name


def _get_sets_group():
    """Get or create the SETS_Grp."""
    return _ensure_group_exists("Sets_Grp")


# ============================================================================
# Component Info Classes
# ============================================================================

class ComponentLocator:
    """Information about a locator and its component."""
    def __init__(self, locator_path, component_name, component_id):
        self.locator_path = locator_path  # Full Maya path
        self.locator_short = locator_path.split("|")[-1]
        self.component_name = component_name  # e.g., "CBDAExtAreaLowA"
        self.component_id = component_id  # e.g., "001"
        self.is_master = False
        self.master_geo_path = None  # Set after master is created


class ComponentGroup:
    """Group of locators referencing the same component asset."""
    def __init__(self, component_name, geo_file, shader_file):
        self.component_name = component_name
        self.geo_file = geo_file
        self.shader_file = shader_file
        self.locators = []  # List of ComponentLocator
        self.master_geo_group = None  # Path to master's Geo_Grp after creation

    def add_locator(self, locator):
        self.locators.append(locator)

    @property
    def count(self):
        return len(self.locators)

    @property
    def has_duplicates(self):
        return self.count > 1

    @property
    def master_locator(self):
        return self.locators[0] if self.locators else None

    @property
    def duplicate_locators(self):
        return self.locators[1:] if len(self.locators) > 1 else []


# ============================================================================
# SETS Instance Builder Class
# ============================================================================

class SetsInstanceBuilder:
    """
    Builds SETS with instance optimization.

    Usage:
        builder = SetsInstanceBuilder(root_path, project)
        builder.build_sets_with_instances(sets_abc_file)
    """

    # Asset search locations (same as igl_shot_build.py)
    SEARCH_LOCATIONS = [
        ("Setdress", "interior"),
        ("Setdress", "exterior"),
        ("Props", "object")
    ]

    def __init__(self, root_path, project, log_callback=None):
        """
        Initialize builder.

        Args:
            root_path: Root path (e.g., "V:/SWA")
            project: Project name (e.g., "SWA")
            log_callback: Optional callback for logging (fn(message))
        """
        self.root_path = root_path
        self.project = project
        self.log_callback = log_callback
        self.component_groups = {}  # component_name -> ComponentGroup

    def _log(self, message):
        """Log a message."""
        print(message)
        if self.log_callback:
            self.log_callback(message)

    def _log_verbose(self, message):
        """Log verbose message (debug level)."""
        print("  " + message)

    # ========================================================================
    # File Discovery
    # ========================================================================

    def list_sets_files(self, ep, seq, shot, version):
        """
        List SETS alembic files from anim publish path.

        Path: {root}/{project}/all/scene/{ep}/{seq}/{shot}/anim/publish/{version}/
        Filter: *_SETS_*.abc

        Returns:
            List of (filename, full_path) tuples
        """
        publish_path = os.path.join(
            self.root_path, self.project, "all", "scene",
            ep, seq, shot, "anim", "publish", version
        )

        if not os.path.exists(publish_path):
            self._log("[ERROR] Publish path does not exist: {}".format(publish_path))
            return []

        sets_files = []
        for filename in os.listdir(publish_path):
            if "_SETS_" in filename and filename.endswith(".abc"):
                full_path = os.path.join(publish_path, filename)
                sets_files.append((filename, full_path))

        self._log("[SETS Builder] Found {} SETS files in {}".format(len(sets_files), publish_path))
        return sets_files

    def list_versions(self, ep, seq, shot):
        """List available versions for a shot."""
        publish_base = os.path.join(
            self.root_path, self.project, "all", "scene",
            ep, seq, shot, "anim", "publish"
        )

        if not os.path.exists(publish_base):
            return []

        versions = []
        for item in os.listdir(publish_base):
            if item.startswith("v") and os.path.isdir(os.path.join(publish_base, item)):
                versions.append(item)

        return sorted(versions, reverse=True)  # Latest first

    # ========================================================================
    # Asset Path Discovery (matching igl_shot_build.py logic)
    # ========================================================================

    def _find_asset_files(self, component_name):
        """
        Find geometry and shader files for a component.
        Searches in priority order: Setdress/interior, Setdress/exterior, Props/object

        Returns:
            (geo_file, shader_file) or (None, None) if not found
        """
        for category, subdir in self.SEARCH_LOCATIONS:
            base_path = os.path.join(
                self.root_path, self.project, "all", "asset",
                category, subdir, component_name, "hero"
            )
            geo_file = os.path.join(base_path, "{}_geo.abc".format(component_name))
            shader_file = os.path.join(base_path, "{}_rsshade.ma".format(component_name))

            if os.path.exists(geo_file):
                self._log_verbose("Found asset in {}/{}: {}".format(category, subdir, component_name))
                return geo_file, shader_file

        self._log("[WARNING] Asset not found: {}".format(component_name))
        return None, None

    # ========================================================================
    # Build Process
    # ========================================================================

    def build_sets_with_instances(self, sets_abc_file, progress_callback=None):
        """
        Main build function - imports SETS alembic and builds with instance optimization.

        Args:
            sets_abc_file: Full path to SETS alembic file
            progress_callback: Optional fn(step, total, message)

        Returns:
            dict with build statistics
        """
        self.component_groups.clear()
        stats = {
            "locators_found": 0,
            "unique_components": 0,
            "masters_created": 0,
            "instances_created": 0,
            "errors": []
        }

        # Extract namespace from filename
        # Format: Ep04_sq0070_SH0180__SETS_CentralBusinessDistrictAExt_001.abc
        filename = os.path.basename(sets_abc_file)
        match = re.match(r".*__(SETS_[^.]+)\.abc", filename)
        if not match:
            self._log("[ERROR] Invalid SETS filename format: {}".format(filename))
            stats["errors"].append("Invalid filename format")
            return stats

        namespace = match.group(1)  # e.g., "SETS_CentralBusinessDistrictAExt_001"
        self._log("\n" + "="*60)
        self._log("[SETS Builder] Building: {}".format(filename))
        self._log("[SETS Builder] Namespace: {}".format(namespace))
        self._log("="*60)

        if progress_callback:
            progress_callback(1, 5, "Importing alembic...")

        # Step 1: Ensure SETS_Grp exists
        sets_grp = _get_sets_group()

        # Step 2: Import alembic
        imported_namespace = self._import_sets_alembic(sets_abc_file, namespace)
        if not imported_namespace:
            stats["errors"].append("Failed to import alembic")
            return stats

        if progress_callback:
            progress_callback(2, 5, "Analyzing locators...")

        # Step 3: Walk locators and group by component
        self._analyze_locators(imported_namespace)
        stats["locators_found"] = sum(g.count for g in self.component_groups.values())
        stats["unique_components"] = len(self.component_groups)

        self._log("\n[SETS Builder] Analysis complete:")
        self._log("  - Total locators: {}".format(stats["locators_found"]))
        self._log("  - Unique components: {}".format(stats["unique_components"]))
        duplicates = sum(1 for g in self.component_groups.values() if g.has_duplicates)
        self._log("  - Components with duplicates: {}".format(duplicates))

        if progress_callback:
            progress_callback(3, 5, "Building masters...")

        # Step 4: Build masters (reference geo + shader for first locator of each component)
        masters_built = self._build_masters(imported_namespace)
        stats["masters_created"] = masters_built

        if progress_callback:
            progress_callback(4, 5, "Creating instances...")

        # Step 5: Create instances for duplicates
        instances_created = self._create_instances()
        stats["instances_created"] = instances_created

        if progress_callback:
            progress_callback(5, 5, "Organizing hierarchy...")

        # Step 6: Parent main group to Sets_Grp
        self._organize_hierarchy(imported_namespace, sets_grp)

        self._log("\n" + "="*60)
        self._log("[SETS Builder] Build complete!")
        self._log("  - Masters: {} references".format(stats["masters_created"]))
        self._log("  - Instances: {}".format(stats["instances_created"]))
        self._log("  - Total references saved: {}".format(
            stats["locators_found"] - stats["masters_created"]))
        self._log("="*60)

        return stats


    def _import_sets_alembic(self, abc_file, namespace):
        """
        Import SETS alembic file with namespace.

        Returns:
            namespace string if successful, None on failure
        """
        try:
            # Create namespace if not exists (matching igl_shot_build.py)
            if not cmds.namespace(exists=namespace):
                cmds.namespace(add=namespace)
                self._log("[SETS Builder] Created namespace: {}".format(namespace))

            # Store current namespace
            current_ns = cmds.namespaceInfo(currentNamespace=True)

            # Set namespace and import
            cmds.namespace(set=namespace)
            cmds.AbcImport(abc_file, mode="import", fitTimeRange=False)
            self._log("[SETS Builder] Imported alembic: {}".format(os.path.basename(abc_file)))

            # Restore namespace
            cmds.namespace(set=current_ns)

            return namespace

        except Exception as e:
            self._log("[ERROR] Failed to import alembic: {}".format(str(e)))
            return None

    def _analyze_locators(self, namespace):
        """
        Walk through imported locators and group by component name.

        Locator format: {namespace}:{componentName}_{id}_Loc
        Example: SETS_CBD_001:CBDAExtAreaLowA_001_Loc
        """
        self.component_groups.clear()

        # Find all locators in namespace
        locators = cmds.ls("{}:*_Loc".format(namespace), type="transform", long=True) or []
        self._log("[SETS Builder] Found {} locators".format(len(locators)))

        for loc_path in locators:
            loc_short = _short(loc_path.split("|")[-1])

            # Parse locator name: {componentName}_{id}_Loc
            if not loc_short.endswith("_Loc"):
                continue

            # Extract component name and ID
            # e.g., "CBDAExtAreaLowA_001_Loc" -> component="CBDAExtAreaLowA", id="001"
            parts = loc_short.replace("_Loc", "").split("_")
            if len(parts) < 2:
                self._log_verbose("Skipping invalid locator: {}".format(loc_short))
                continue

            component_id = parts[-1]  # "001"
            component_name = "_".join(parts[:-1])  # "CBDAExtAreaLowA"

            # Find asset files for this component
            if component_name not in self.component_groups:
                geo_file, shader_file = self._find_asset_files(component_name)
                if not geo_file:
                    self._log("[WARNING] Skipping component (no asset): {}".format(component_name))
                    continue
                self.component_groups[component_name] = ComponentGroup(
                    component_name, geo_file, shader_file
                )

            # Add locator to group
            locator_info = ComponentLocator(loc_path, component_name, component_id)
            self.component_groups[component_name].add_locator(locator_info)
            self._log_verbose("Added locator: {} -> {}".format(loc_short, component_name))

        # Log summary
        for name, group in self.component_groups.items():
            self._log("[SETS Builder] Component '{}': {} locator(s) {}".format(
                name, group.count,
                "(DUPLICATES)" if group.has_duplicates else ""
            ))

    def _build_masters(self, set_namespace):
        """
        Build master references for each unique component.
        Only the FIRST locator of each component gets actual references.

        Returns:
            Number of masters built
        """
        masters_built = 0

        for component_name, group in self.component_groups.items():
            if not group.master_locator:
                continue

            master_loc = group.master_locator
            self._log("\n[MASTER] Building: {} (under {})".format(
                component_name, master_loc.locator_short))

            try:
                # Create nested namespace for this component
                # Format: SETS_CBD_001:CBDAExtAreaLowA_001
                component_ns = "{}_{}".format(component_name, master_loc.component_id)
                full_component_ns = "{}:{}".format(set_namespace, component_ns)

                # Reference geometry
                if group.geo_file and os.path.exists(group.geo_file):
                    cmds.file(group.geo_file, reference=True, namespace=full_component_ns)
                    self._log("  Referenced geo: {}".format(os.path.basename(group.geo_file)))

                    # Find the Geo_Grp in referenced geometry
                    ref_nodes = cmds.ls("{}:*".format(full_component_ns), type="transform", long=True) or []
                    top_level_nodes = []

                    for node in ref_nodes:
                        parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
                        if not parents or parents[0] == "|":
                            top_level_nodes.append(node)

                    # Parent to locator and reset transform
                    for top_node in top_level_nodes:
                        cmds.parent(top_node, master_loc.locator_path)
                        cmds.xform(top_node, translation=[0, 0, 0], rotation=[0, 0, 0])
                        cmds.xform(top_node, scale=[1, 1, 1])
                        self._log("  Parented {} to locator (reset transform)".format(
                            top_node.split("|")[-1]))

                        # Store master geo path for instancing
                        group.master_geo_group = top_node

                    # Reference shader
                    if group.shader_file and os.path.exists(group.shader_file):
                        shader_ns = "{}_shade".format(full_component_ns)
                        cmds.file(group.shader_file, reference=True, namespace=shader_ns)
                        self._log("  Referenced shader: {}".format(os.path.basename(group.shader_file)))

                        # Assign shaders using stored mapping
                        self._assign_shaders(full_component_ns, shader_ns)

                master_loc.is_master = True
                masters_built += 1

            except Exception as e:
                self._log("[ERROR] Failed to build master for {}: {}".format(component_name, str(e)))

        return masters_built



    def _create_instances(self):
        """
        Create instances for duplicate locators (all except master).

        Instance workflow (matching ref2ints.py logic):
        1. Get master geo group path
        2. Create instance of master
        3. Parent instance to duplicate locator
        4. Reset instance local transform to identity (locator provides position)

        Returns:
            Number of instances created
        """
        instances_created = 0

        for component_name, group in self.component_groups.items():
            if not group.has_duplicates:
                continue

            if not group.master_geo_group:
                self._log("[WARNING] No master geo for {}, skipping instances".format(component_name))
                continue

            self._log("\n[INSTANCES] Creating {} instances for {}".format(
                len(group.duplicate_locators), component_name))

            for dup_loc in group.duplicate_locators:
                try:
                    # Create instance name
                    # Format: {componentName}_{id}_instance
                    instance_name = "{}_{}_{}_instance".format(
                        component_name, dup_loc.component_id,
                        group.master_geo_group.split("|")[-1].replace(":", "_")
                    )

                    # Create instance of master geometry
                    instance = cmds.instance(group.master_geo_group, name=instance_name)[0]

                    # Parent instance to duplicate locator
                    cmds.parent(instance, dup_loc.locator_path)

                    # Reset transform to identity (locator provides world position)
                    # This matches igl_shot_build.py and ref2ints.py behavior
                    cmds.xform(instance, translation=[0, 0, 0], rotation=[0, 0, 0])
                    cmds.xform(instance, scale=[1, 1, 1])

                    self._log("  Created instance: {} -> {}".format(
                        instance_name, dup_loc.locator_short))
                    instances_created += 1

                except Exception as e:
                    self._log("[ERROR] Failed to create instance for {}: {}".format(
                        dup_loc.locator_short, str(e)))

        return instances_created

    def _assign_shaders(self, geo_ns, shader_ns):
        """
        Assign shaders to geometry using stored mapping.
        This matches the logic in igl_shot_build.py._assign_component_shaders()
        """
        try:
            self._log("  Assigning shaders: {} -> {}".format(shader_ns, geo_ns))

            # Find shading groups in shader namespace
            shader_sgs = cmds.ls("{}:*".format(shader_ns), type="shadingEngine") or []

            if not shader_sgs:
                self._log("[WARNING] No shading groups found in: {}".format(shader_ns))
                return

            for sg in shader_sgs:
                # Get stored assignment mapping from attribute
                assign_attr = "{}.snow__assign_shade".format(sg)
                if not cmds.attributeQuery("snow__assign_shade", node=sg, exists=True):
                    continue

                mapping = cmds.getAttr(assign_attr) or ""
                if not mapping:
                    continue

                # Parse mapping and find matching shapes
                for pattern in mapping.split(","):
                    pattern = pattern.strip()
                    if not pattern:
                        continue

                    # Find shapes matching pattern in geo namespace
                    search_pattern = "{}:*{}*".format(geo_ns, pattern)
                    matches = cmds.ls(search_pattern, type="mesh", long=True) or []

                    for shape in matches:
                        try:
                            cmds.sets(shape, edit=True, forceElement=sg)
                        except Exception:
                            pass

            self._log("  Shader assignment complete")

        except Exception as e:
            self._log("[WARNING] Shader assignment error: {}".format(str(e)))

    def _organize_hierarchy(self, namespace, sets_grp):
        """
        Organize the imported hierarchy under Sets_Grp.
        """
        try:
            # Find the main imported group
            main_groups = cmds.ls("{}:*".format(namespace), type="transform", long=True) or []

            top_level = []
            for grp in main_groups:
                parents = cmds.listRelatives(grp, parent=True, fullPath=True) or []
                if not parents or parents[0] == "|":
                    top_level.append(grp)

            for grp in top_level:
                try:
                    # Only parent if not already under Sets_Grp
                    current_parent = cmds.listRelatives(grp, parent=True, fullPath=True)
                    if current_parent and sets_grp in current_parent[0]:
                        continue
                    cmds.parent(grp, sets_grp)
                    self._log("[SETS Builder] Parented {} to {}".format(
                        grp.split("|")[-1], sets_grp))
                except Exception:
                    pass

        except Exception as e:
            self._log("[WARNING] Could not organize hierarchy: {}".format(str(e)))


# ============================================================================
# Convenience Functions
# ============================================================================

def build_sets_with_instances(root_path, project, sets_abc_file, log_callback=None):
    """
    Convenience function to build SETS with instance optimization.

    Args:
        root_path: Root path (e.g., "V:/SWA")
        project: Project name (e.g., "SWA")
        sets_abc_file: Full path to SETS alembic file
        log_callback: Optional callback for logging

    Returns:
        dict with build statistics
    """
    builder = SetsInstanceBuilder(root_path, project, log_callback)
    return builder.build_sets_with_instances(sets_abc_file)


def list_sets_files(root_path, project, ep, seq, shot, version):
    """
    Convenience function to list SETS files.

    Returns:
        List of (filename, full_path) tuples
    """
    builder = SetsInstanceBuilder(root_path, project)
    return builder.list_sets_files(ep, seq, shot, version)


# ============================================================================
# Test Function (for Maya Script Editor)
# ============================================================================

def test_build():
    """
    Test function - run in Maya Script Editor.

    Usage:
        import sets_instance_builder
        sets_instance_builder.test_build()
    """
    print("\n" + "="*60)
    print("SETS Instance Builder - Test")
    print("="*60)

    # Example paths - modify for your environment
    root_path = "V:/SWA"
    project = "SWA"
    ep = "Ep04"
    seq = "sq0070"
    shot = "SH0180"
    version = "v001"

    builder = SetsInstanceBuilder(root_path, project)

    # List available SETS files
    sets_files = builder.list_sets_files(ep, seq, shot, version)
    print("\nAvailable SETS files:")
    for filename, path in sets_files:
        print("  - {}".format(filename))

    if sets_files:
        # Build first SETS file with instances
        print("\nBuilding first SETS file with instances...")
        filename, path = sets_files[0]
        stats = builder.build_sets_with_instances(path)
        print("\nBuild stats: {}".format(stats))
    else:
        print("\nNo SETS files found!")

    print("\n" + "="*60)