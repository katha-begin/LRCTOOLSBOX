import maya.cmds as cmds
import maya.api.OpenMaya as om2
from functools import partial
import math
import re

class ReferenceCleanupUI:
    def __init__(self):
        self.window_name = "refCleanupWin"
        self.window_title = "Reference Cleanup Tool"
        self.all_references = []
        self.visible_references = []
        self.invisible_references = []
        self.selected_camera = None
        self.frustum_padding = 1.1
        
        # Filter states
        self.filter_visible = {'GEO': True, 'SHADER': True, 'CHAR': True, 'PROP': True, 'SET': True, 'OTHER': True}
        self.filter_invisible = {'GEO': True, 'SHADER': True, 'CHAR': True, 'PROP': True, 'SET': True, 'OTHER': True}
        
    def parse_reference_type(self, ref_data):
        """
        Parse reference type from filename and namespace.
        Returns: dict with 'category', 'name', 'id', 'kind', 'type'
        """
        full_namespace = ref_data['namespace'].strip(':')
        filename = ref_data['short_name'].lower()

        # For nested namespaces like "SETS_CentralBusinessDistrictAExt_001:CBDAExtTreeA_016"
        # Extract only the LAST part for matching (CBDAExtTreeA_016)
        if ':' in full_namespace:
            namespace = full_namespace.split(':')[-1]  # Get last part after ':'
        else:
            namespace = full_namespace
        
        # Check if it's a camera
        if 'camera' in namespace.lower() or 'camera' in filename:
            return {
                'category': 'CAMERA',
                'name': namespace,
                'id': '',
                'kind': 'camera',
                'type': 'CAMERA',
                'display_type': 'CAMERA'
            }
        
        # Check if it's a shader (SDRS prefix or _shade/_rsshade in filename)
        if namespace.startswith('SDRS_') or '_shade' in filename or '_rsshade' in filename:
            # Parse shader namespace: SDRS_CBDAExtBuildA_Shade
            if namespace.startswith('SDRS_'):
                parts = namespace.split('_')
                # Get the asset name (remove SDRS_ prefix and _Shade suffix)
                name_parts = [p for p in parts[1:] if p.lower() not in ['shade', 'shader', 'shd']]
                name = '_'.join(name_parts) if name_parts else parts[1] if len(parts) > 1 else namespace
                
                return {
                    'category': 'SDRS',
                    'name': name,
                    'id': '',
                    'kind': 'Shade',
                    'type': 'SHADER',
                    'display_type': 'SHADER',
                    'shader_target': name  # Used for matching geo
                }
            else:
                # Extract name from filename if it has _shade pattern
                base_name = filename.replace('_shade.ma', '').replace('_rsshade.ma', '').replace('.ma', '')
                return {
                    'category': 'SHADER',
                    'name': base_name,
                    'id': '',
                    'kind': 'shade',
                    'type': 'SHADER',
                    'display_type': 'SHADER',
                    'shader_target': base_name
                }
        
        # Parse standard namespace: {CATEGORY}_{Name}_{ID}
        # Examples: CHAR_CatStompie_002, CBDAExtTreeC_154
        parts = namespace.split('_')
        
        # Check if it's a geometry file
        is_geo = '_geo' in filename or '.abc' in filename
        
        if len(parts) >= 2:
            # Check if first part is a known category
            first_part = parts[0].upper()
            known_categories = ['CHAR', 'PROP', 'VEH', 'ENV']
            
            if first_part in known_categories:
                # Has category prefix: CHAR_CatStompie_002
                category = first_part
                # Extract name without the last part (which is usually the ID)
                name_parts = parts[1:-1] if len(parts) > 2 else [parts[1]]
                name = '_'.join(name_parts)
                id_part = parts[-1] if len(parts) > 1 else ''
                
                # Determine type
                if is_geo:
                    kind = 'geo'
                    display_type = category
                else:
                    kind = 'asset'
                    display_type = category
                
                return {
                    'category': category,
                    'name': name,
                    'id': id_part,
                    'kind': kind,
                    'type': 'GEO' if is_geo else category,
                    'display_type': category,
                    'geo_name': name,  # Used for shader matching
                    'is_geo': is_geo
                }
            else:
                # No category prefix, likely SET: CBDAExtTreeC_154
                # Check if last part is a number (ID)
                if parts[-1].isdigit() or (len(parts[-1]) > 0 and parts[-1][0].isdigit()):
                    name = '_'.join(parts[:-1])
                    id_part = parts[-1]
                else:
                    name = '_'.join(parts)
                    id_part = ''
                
                return {
                    'category': 'SET',
                    'name': name,
                    'id': id_part,
                    'kind': 'geo' if is_geo else 'asset',
                    'type': 'GEO' if is_geo else 'SET',
                    'display_type': 'SET',
                    'geo_name': name,
                    'is_geo': is_geo
                }
        else:
            # Single part namespace
            return {
                'category': 'OTHER',
                'name': namespace,
                'id': '',
                'kind': 'unknown',
                'type': 'OTHER',
                'display_type': 'OTHER',
                'is_geo': is_geo
            }
    
    def find_related_geometry_by_name(self, shader_target):
        """
        Find all geometry references that match this shader target name.
        Returns list of ALL geo references (in any list) that match.
        """
        related_geos = []
        
        print(f"    Searching for geometry matching shader target: '{shader_target}'")
        
        # Search through ALL references
        for ref in self.all_references:
            ref_info = ref['ref_type']
            
            # Only check geometry files
            if not ref_info.get('is_geo', False):
                continue
            
            # Get geo name for comparison
            geo_name = ref_info.get('geo_name', '').lower()
            
            # Match shader target with geo name
            if geo_name and shader_target and geo_name == shader_target.lower():
                related_geos.append(ref)
                print(f"      Found matching geo: {ref['namespace']}")
        
        return related_geos
    
    def find_shaders_for_geometry(self, geo_ref_data):
        """
        Find all shader references that match this geometry.
        Returns list of shader references from ALL lists.
        """
        geo_info = geo_ref_data['ref_type']
        geo_name = geo_info.get('geo_name', '').lower()
        
        if not geo_name:
            return []
        
        matching_shaders = []
        
        print(f"  Searching for shaders matching geo: '{geo_name}'")
        
        # Search through ALL references for shaders
        for ref in self.all_references:
            ref_info = ref['ref_type']
            
            if ref_info['type'] == 'SHADER':
                shader_target = ref_info.get('shader_target', '').lower()
                
                print(f"    Checking shader: {ref['namespace']} (target: '{shader_target}')")
                
                if shader_target and shader_target == geo_name:
                    matching_shaders.append(ref)
                    print(f"      ✓ MATCH!")
        
        return matching_shaders
    
    def is_ref_in_list(self, ref_data, ref_list):
        """Check if a specific reference is in a list by comparing node"""
        for ref in ref_list:
            if ref['node'] == ref_data['node']:
                return True
        return False

    def _auto_restore_matching_shaders(self):
        """
        Automatically restore shaders that match geometry in the keep (visible) list.
        Called after initial scan to ensure shaders stay with their geometry.
        """
        print(f"\n{'='*60}")
        print(f"Auto-Restoring Shaders for Geometry in Keep List")
        print(f"{'='*60}")

        # Find all geometry in keep list
        geo_in_keep = [ref for ref in self.visible_references if ref['ref_type'].get('is_geo', False)]

        if not geo_in_keep:
            print("No geometry in keep list - skipping shader auto-restore")
            return

        print(f"Found {len(geo_in_keep)} geometry reference(s) in keep list")

        # Collect all geo names that need shaders
        geo_names_in_keep = set()
        for geo_ref in geo_in_keep:
            geo_name = geo_ref['ref_type'].get('geo_name', '').lower()
            if geo_name:
                geo_names_in_keep.add(geo_name)

        print(f"Unique geo names to match: {geo_names_in_keep}")

        # Find matching shaders in invisible list
        shaders_to_move = []

        for ref in self.invisible_references[:]:  # Copy list to avoid modification during iteration
            ref_info = ref['ref_type']

            if ref_info['type'] == 'SHADER':
                shader_target = ref_info.get('shader_target', '').lower()

                if shader_target and shader_target in geo_names_in_keep:
                    shaders_to_move.append(ref)
                    print(f"  -> Will auto-keep shader: {ref['namespace']} (matches '{shader_target}')")

        # Move shaders to visible list
        for shader_ref in shaders_to_move:
            actual_ref = self._safe_remove_ref(shader_ref, self.invisible_references)
            if actual_ref and not self.is_ref_in_list(actual_ref, self.visible_references):
                self.visible_references.append(actual_ref)

        print(f"\n✓ Auto-restored {len(shaders_to_move)} shader(s) to keep list")
        print(f"{'='*60}\n")

    def _find_ref_in_list_by_node(self, ref_data, ref_list):
        """
        Find the actual reference object in a list by node value.
        Returns the actual object from the list, or None if not found.
        This ensures we get the correct object reference for list operations.
        """
        target_node = ref_data['node']
        for ref in ref_list:
            if ref['node'] == target_node:
                return ref
        return None

    def _safe_remove_ref(self, ref_data, ref_list):
        """
        Safely remove a reference from list by node value, not object identity.
        Returns the removed reference if successful, None otherwise.
        """
        actual_ref = self._find_ref_in_list_by_node(ref_data, ref_list)
        if actual_ref:
            ref_list.remove(actual_ref)
            return actual_ref
        return None
    
    def get_ref_from_display_name(self, display_name, ref_list):
        """
        Get the actual reference data from a display name.
        Display name format: "[TYPE] namespace - filename"
        """
        # Extract namespace from display name
        # Format: "[SHADER] SDRS_CBDAExtBuildA_Shade - CBDAExtBuildA_rsshade.ma"
        try:
            # Remove the [TYPE] prefix
            parts = display_name.split('] ', 1)
            if len(parts) < 2:
                return None
            
            # Get namespace part (before " - ")
            namespace_part = parts[1].split(' - ')[0].strip()
            
            # Find matching reference in the list
            for ref in ref_list:
                if ref['namespace'] == namespace_part:
                    return ref
        except Exception as e:
            print(f"Error parsing display name '{display_name}': {str(e)}")
        
        return None
    
    def restore_shaders_for_selected(self):
        """
        Find shaders related to selected geometry in keep list and move them from remove to keep.
        """
        selected_items = cmds.textScrollList(self.visible_list, query=True, selectItem=True) or []
        if not selected_items:
            cmds.warning("No geometry selected in Keep list!")
            return
        
        print(f"\n{'='*60}")
        print(f"Restoring Shaders for Selected Geometry")
        print(f"{'='*60}")
        
        selected_geos = []
        for item in selected_items:
            ref_data = self.get_ref_from_display_name(item, self.visible_references)
            if ref_data and ref_data['ref_type'].get('is_geo', False):
                selected_geos.append(ref_data)
                print(f"\nSelected geo: {ref_data['namespace']}")
        
        if not selected_geos:
            cmds.warning("No geometry references selected!")
            return
        
        # Find all shaders for these geometries
        shaders_to_move = []
        
        for geo_ref in selected_geos:
            matching_shaders = self.find_shaders_for_geometry(geo_ref)
            
            print(f"  Found {len(matching_shaders)} matching shader(s)")
            
            for shader_ref in matching_shaders:
                # Check if shader is in invisible list
                if self.is_ref_in_list(shader_ref, self.invisible_references):
                    if not self.is_ref_in_list(shader_ref, shaders_to_move):
                        shaders_to_move.append(shader_ref)
                        print(f"    -> Will move: {shader_ref['namespace']}")
                else:
                    print(f"    -> Already in keep list: {shader_ref['namespace']}")
        
        if not shaders_to_move:
            cmds.confirmDialog(
                title='No Shaders Found',
                message='No shaders found in Remove list for selected geometry.\n\nShaders may already be in Keep list.',
                button=['OK']
            )
            print("\nNo shaders to move.")
            return
        
        # Move shaders to visible list (use safe removal by node value)
        for shader_ref in shaders_to_move:
            # Find and remove the actual object from invisible_references by node
            actual_ref = self._safe_remove_ref(shader_ref, self.invisible_references)
            if actual_ref and not self.is_ref_in_list(actual_ref, self.visible_references):
                self.visible_references.append(actual_ref)
        
        self.update_reference_lists()
        
        cmds.confirmDialog(
            title='Shaders Restored',
            message=f'Moved {len(shaders_to_move)} shader(s) to Keep list.',
            button=['OK']
        )
        
        print(f"\n✓ Successfully restored {len(shaders_to_move)} shader(s)")
        print(f"{'='*60}\n")
    
    def restore_all_shaders(self):
        """
        Go through all geometry in keep list and restore all related shaders from remove list.
        """
        print(f"\n{'='*60}")
        print(f"Restoring ALL Shaders for Geometry in Keep List")
        print(f"{'='*60}")
        
        # Find all geometry in keep list
        geo_in_keep = [ref for ref in self.visible_references if ref['ref_type'].get('is_geo', False)]
        
        if not geo_in_keep:
            cmds.warning("No geometry in Keep list!")
            return
        
        print(f"\nFound {len(geo_in_keep)} geometry reference(s) in keep list")
        
        # Find all shaders that should be kept
        shaders_to_move = []
        
        for geo_ref in geo_in_keep:
            print(f"\nChecking geo: {geo_ref['namespace']}")
            matching_shaders = self.find_shaders_for_geometry(geo_ref)
            
            print(f"  Found {len(matching_shaders)} matching shader(s)")
            
            for shader_ref in matching_shaders:
                # Check if shader is in invisible list
                if self.is_ref_in_list(shader_ref, self.invisible_references):
                    if not self.is_ref_in_list(shader_ref, shaders_to_move):
                        shaders_to_move.append(shader_ref)
                        print(f"    -> Will move: {shader_ref['namespace']}")
                else:
                    print(f"    -> Already in keep list: {shader_ref['namespace']}")
        
        if not shaders_to_move:
            cmds.confirmDialog(
                title='No Shaders to Restore',
                message='All shaders for geometry in Keep list are already in Keep list.',
                button=['OK']
            )
            print("\nNo shaders to move - all already in keep list.")
            return
        
        # Move shaders to visible list (use safe removal by node value)
        for shader_ref in shaders_to_move:
            # Find and remove the actual object from invisible_references by node
            actual_ref = self._safe_remove_ref(shader_ref, self.invisible_references)
            if actual_ref and not self.is_ref_in_list(actual_ref, self.visible_references):
                self.visible_references.append(actual_ref)
        
        self.update_reference_lists()
        
        cmds.confirmDialog(
            title='Shaders Restored',
            message=f'Moved {len(shaders_to_move)} shader(s) to Keep list.',
            button=['OK']
        )
        
        print(f"\n✓ Successfully restored {len(shaders_to_move)} shader(s)")
        print(f"{'='*60}\n")
        
    def create_ui(self):
        """Create the main UI window"""
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        
        self.window = cmds.window(
            self.window_name,
            title=self.window_title,
            widthHeight=(680, 820),
            sizeable=True
        )
        
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        # Title
        cmds.text(label="Reference Cleanup Tool", font="boldLabelFont", height=30)
        cmds.separator(height=10)
        
        # Camera Selection Section
        cmds.frameLayout(label="1. Select Camera", collapsable=False, marginHeight=10, marginWidth=10)
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAttach=[(1, 'left', 5), (3, 'right', 5)])
        cmds.text(label="Camera:", width=60)
        self.camera_field = cmds.textField(editable=False, placeholderText="No camera selected")
        cmds.button(label="Get Selected", width=100, command=self.get_selected_camera)
        cmds.setParent('..')
        
        # Frustum settings
        cmds.separator(height=10, style='none')
        cmds.text(label="Detection Settings:", align='left', font='boldLabelFont')
        cmds.separator(height=5, style='none')
        
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAttach=[(1, 'left', 5)])
        cmds.text(label="Frustum Padding:", width=100)
        self.padding_slider = cmds.floatSliderGrp(
            field=True,
            minValue=0.8,
            maxValue=1.5,
            value=1.1,
            step=0.05,
            precision=2,
            columnWidth=[(1, 50), (2, 50)],
            changeCommand=self.update_padding
        )
        cmds.setParent('..')
        
        cmds.text(
            label="Lower = Stricter (0.8 = only center, 1.5 = include edges)",
            align='left',
            font='smallPlainLabelFont',
            wordWrap=True
        )
        
        cmds.setParent('..')
        cmds.separator(height=10)
        
        # Analysis Section
        cmds.frameLayout(label="2. Analyze Scene", collapsable=False, marginHeight=10, marginWidth=10)
        cmds.columnLayout(adjustableColumn=True)
        cmds.button(
            label="Scan References in Camera View",
            height=35,
            backgroundColor=(0.4, 0.6, 0.4),
            command=self.scan_references
        )
        cmds.separator(height=5, style='none')
        self.scan_status = cmds.text(label="Status: Ready to scan", align='left', font='smallPlainLabelFont')
        cmds.setParent('..')
        cmds.setParent('..')
        
        cmds.separator(height=10)
        
        # Results Section
        cmds.frameLayout(label="3. Review References", collapsable=False, marginHeight=10, marginWidth=10)
        cmds.columnLayout(adjustableColumn=True)
        
        # Stats row
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=1)
        self.total_refs_text = cmds.text(label="Total: 0", align='left')
        self.visible_refs_text = cmds.text(label="Keep: 0", align='center')
        self.invisible_refs_text = cmds.text(label="Remove: 0", align='right')
        cmds.setParent('..')
        
        cmds.separator(height=10)
        
        # Tab layout
        self.tab_layout = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5)
        
        # === VISIBLE (KEEP) TAB ===
        visible_tab = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label="References to KEEP (visible in camera):", align='left', font='boldLabelFont')
        cmds.separator(height=5, style='none')
        
        # Filter checkboxes for visible
        cmds.rowLayout(numberOfColumns=7, columnWidth=[(1, 80), (2, 80), (3, 80), (4, 80), (5, 80), (6, 80)])
        self.vis_filter_geo = cmds.checkBox(label='GEO/SET', value=True, changeCommand=lambda x: self.update_filters('visible'))
        self.vis_filter_shader = cmds.checkBox(label='SHADER', value=True, changeCommand=lambda x: self.update_filters('visible'))
        self.vis_filter_char = cmds.checkBox(label='CHAR', value=True, changeCommand=lambda x: self.update_filters('visible'))
        self.vis_filter_prop = cmds.checkBox(label='PROP', value=True, changeCommand=lambda x: self.update_filters('visible'))
        self.vis_filter_other = cmds.checkBox(label='OTHER', value=True, changeCommand=lambda x: self.update_filters('visible'))
        cmds.setParent('..')
        
        cmds.separator(height=5, style='none')
        
        # Buttons for visible list - Row 1
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=1)
        cmds.button(label="Select All", command=lambda x: self.select_all_visible(True))
        cmds.button(label="Deselect All", command=lambda x: self.select_all_visible(False))
        cmds.setParent('..')
        
        # Buttons for visible list - Row 2
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=1)
        cmds.button(label="Move Selected to Remove List", command=self.move_to_invisible, backgroundColor=(0.6, 0.4, 0.4))
        cmds.button(label="Select in Scene", command=lambda x: self.select_reference_in_scene('visible'))
        cmds.button(label="Select from Viewport", command=lambda x: self.select_from_viewport('visible'),
                    backgroundColor=(0.5, 0.5, 0.3), annotation="Select items in list based on viewport selection")
        cmds.setParent('..')
        
        # Shader restore button
        cmds.separator(height=5, style='none')
        cmds.button(
            label="Restore Shaders for Selected Geometry",
            command=lambda x: self.restore_shaders_for_selected(),
            backgroundColor=(0.4, 0.5, 0.6),
            annotation="Find and restore shaders related to selected geometry from Remove list"
        )
        
        cmds.separator(height=5, style='none')
        
        self.visible_list = cmds.textScrollList(
            numberOfRows=8,
            allowMultiSelection=True,
            selectCommand=lambda: self.on_list_select('visible')
        )
        cmds.setParent('..')
        
        # === INVISIBLE (REMOVE) TAB ===
        invisible_tab = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label="References to REMOVE (not visible):", align='left', font='boldLabelFont')
        cmds.separator(height=5, style='none')
        
        # Filter checkboxes for invisible
        cmds.rowLayout(numberOfColumns=7, columnWidth=[(1, 80), (2, 80), (3, 80), (4, 80), (5, 80), (6, 80)])
        self.inv_filter_geo = cmds.checkBox(label='GEO/SET', value=True, changeCommand=lambda x: self.update_filters('invisible'))
        self.inv_filter_shader = cmds.checkBox(label='SHADER', value=True, changeCommand=lambda x: self.update_filters('invisible'))
        self.inv_filter_char = cmds.checkBox(label='CHAR', value=True, changeCommand=lambda x: self.update_filters('invisible'))
        self.inv_filter_prop = cmds.checkBox(label='PROP', value=True, changeCommand=lambda x: self.update_filters('invisible'))
        self.inv_filter_other = cmds.checkBox(label='OTHER', value=True, changeCommand=lambda x: self.update_filters('invisible'))
        cmds.setParent('..')
        
        cmds.separator(height=5, style='none')
        
        # Buttons for invisible list - Row 1
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=1)
        cmds.button(label="Select All", command=lambda x: self.select_all_invisible(True))
        cmds.button(label="Deselect All", command=lambda x: self.select_all_invisible(False))
        cmds.setParent('..')
        
        # Buttons for invisible list - Row 2
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=1)
        cmds.button(label="Move Selected to Keep List", command=self.move_to_visible, backgroundColor=(0.4, 0.6, 0.4))
        cmds.button(label="Select in Scene", command=lambda x: self.select_reference_in_scene('invisible'))
        cmds.button(label="Select from Viewport", command=lambda x: self.select_from_viewport('invisible'),
                    backgroundColor=(0.5, 0.5, 0.3), annotation="Select items in list based on viewport selection")
        cmds.setParent('..')
        
        cmds.separator(height=5, style='none')
        
        self.invisible_list = cmds.textScrollList(
            numberOfRows=8,
            allowMultiSelection=True,
            selectCommand=lambda: self.on_list_select('invisible')
        )
        cmds.setParent('..')
        
        cmds.tabLayout(
            self.tab_layout, 
            edit=True,
            tabLabel=((visible_tab, 'Keep List'), (invisible_tab, 'Remove List'))
        )
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        cmds.separator(height=10)
        
        # Shader Management Section
        cmds.frameLayout(label="Shader Management", collapsable=True, collapse=False, marginHeight=10, marginWidth=10)
        cmds.columnLayout(adjustableColumn=True)
        
        cmds.button(
            label="Restore ALL Shaders for Geometry in Keep List",
            height=35,
            backgroundColor=(0.35, 0.5, 0.65),
            command=lambda x: self.restore_all_shaders(),
            annotation="Scan all geometry in Keep list and restore related shaders from Remove list"
        )
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        cmds.separator(height=10)
        
        # Action Section
        cmds.frameLayout(label="4. Remove References", collapsable=False, marginHeight=10, marginWidth=10)
        cmds.columnLayout(adjustableColumn=True)
        
        self.remove_count_text = cmds.text(label="Ready to remove: 0 references", height=25)
        
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnAttach=[(1, 'both', 5), (2, 'both', 5)])
        cmds.button(
            label="Remove Selected from Remove List",
            height=40,
            backgroundColor=(0.7, 0.3, 0.3),
            command=self.remove_selected_references
        )
        cmds.button(
            label="Refresh Scan",
            height=40,
            command=self.refresh_lists
        )
        cmds.setParent('..')
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        cmds.separator(height=10)
        cmds.button(label="Close", height=30, command=self.close_window)
        
        cmds.showWindow(self.window)
    
    def update_padding(self, value):
        self.frustum_padding = value
    
    def update_filters(self, list_type):
        """Update filter states and refresh display"""
        if list_type == 'visible':
            self.filter_visible['GEO'] = cmds.checkBox(self.vis_filter_geo, query=True, value=True)
            self.filter_visible['SHADER'] = cmds.checkBox(self.vis_filter_shader, query=True, value=True)
            self.filter_visible['CHAR'] = cmds.checkBox(self.vis_filter_char, query=True, value=True)
            self.filter_visible['PROP'] = cmds.checkBox(self.vis_filter_prop, query=True, value=True)
            self.filter_visible['OTHER'] = cmds.checkBox(self.vis_filter_other, query=True, value=True)
        else:
            self.filter_invisible['GEO'] = cmds.checkBox(self.inv_filter_geo, query=True, value=True)
            self.filter_invisible['SHADER'] = cmds.checkBox(self.inv_filter_shader, query=True, value=True)
            self.filter_invisible['CHAR'] = cmds.checkBox(self.inv_filter_char, query=True, value=True)
            self.filter_invisible['PROP'] = cmds.checkBox(self.inv_filter_prop, query=True, value=True)
            self.filter_invisible['OTHER'] = cmds.checkBox(self.inv_filter_other, query=True, value=True)
        
        self.update_reference_lists()
    
    def should_show_reference(self, ref_data, list_type):
        """Check if reference should be shown based on filters"""
        filters = self.filter_visible if list_type == 'visible' else self.filter_invisible
        ref_info = ref_data['ref_type']
        display_type = ref_info['display_type']
        
        if display_type == 'SHADER':
            return filters['SHADER']
        elif display_type in ['CHAR']:
            return filters['CHAR']
        elif display_type in ['PROP']:
            return filters['PROP']
        elif display_type in ['GEO', 'SET']:
            return filters['GEO']
        else:
            return filters['OTHER']
    
    def select_all_visible(self, select_state):
        """Select or deselect all items in visible list"""
        if select_state:
            all_items = cmds.textScrollList(self.visible_list, query=True, allItems=True) or []
            for item in all_items:
                cmds.textScrollList(self.visible_list, edit=True, selectItem=item)
        else:
            cmds.textScrollList(self.visible_list, edit=True, deselectAll=True)
    
    def move_to_invisible(self, *args):
        """Move selected items from visible list to invisible list"""
        selected_items = cmds.textScrollList(self.visible_list, query=True, selectItem=True) or []
        if not selected_items:
            cmds.warning("No items selected to move!")
            return
        
        refs_to_move = []
        for item in selected_items:
            ref_data = self.get_ref_from_display_name(item, self.visible_references)
            if ref_data:
                refs_to_move.append(ref_data)
        
        # Move references (use safe removal by node value)
        for ref in refs_to_move:
            actual_ref = self._safe_remove_ref(ref, self.visible_references)
            if actual_ref and not self.is_ref_in_list(actual_ref, self.invisible_references):
                self.invisible_references.append(actual_ref)
        
        self.update_reference_lists()
        print(f"Moved {len(refs_to_move)} reference(s) to Remove list")
    
    def move_to_visible(self, *args):
        """Move selected items from invisible list to visible list"""
        selected_items = cmds.textScrollList(self.invisible_list, query=True, selectItem=True) or []
        if not selected_items:
            cmds.warning("No items selected to move!")
            return
        
        refs_to_move = []
        for item in selected_items:
            ref_data = self.get_ref_from_display_name(item, self.invisible_references)
            if ref_data:
                refs_to_move.append(ref_data)
        
        # Move references (use safe removal by node value)
        for ref in refs_to_move:
            actual_ref = self._safe_remove_ref(ref, self.invisible_references)
            if actual_ref and not self.is_ref_in_list(actual_ref, self.visible_references):
                self.visible_references.append(actual_ref)
        
        self.update_reference_lists()
        print(f"Moved {len(refs_to_move)} reference(s) to Keep list")
    
    def on_list_select(self, list_type):
        """Handle list selection"""
        self.update_remove_count()
    
    def get_selected_camera(self, *args):
        selection = cmds.ls(selection=True, type='transform')
        
        if not selection:
            cmds.warning("Please select a camera!")
            return
        
        camera = None
        for sel in selection:
            shapes = cmds.listRelatives(sel, shapes=True, type='camera')
            if shapes:
                camera = sel
                break
        
        if not camera:
            cmds.warning("Selected object is not a camera!")
            return
        
        self.selected_camera = camera
        cmds.textField(self.camera_field, edit=True, text=camera)
        cmds.text(self.scan_status, edit=True, label=f"Status: Camera '{camera}' selected. Ready to scan.")
        print(f"Camera selected: {camera}")
    
    def get_camera_frustum_planes(self):
        if not self.selected_camera:
            return None
        
        try:
            cam_shapes = cmds.listRelatives(self.selected_camera, shapes=True, type='camera')
            if not cam_shapes:
                return None
            
            cam_shape = cam_shapes[0]
            
            h_fov = math.radians(cmds.camera(cam_shape, q=True, hfv=True))
            v_fov = math.radians(cmds.camera(cam_shape, q=True, vfv=True))
            near_clip = cmds.camera(cam_shape, q=True, ncp=True)
            far_clip = cmds.camera(cam_shape, q=True, fcp=True)
            
            cam_matrix = cmds.xform(self.selected_camera, q=True, matrix=True, worldSpace=True)
            mat = om2.MMatrix(cam_matrix)
            
            cam_pos = om2.MVector(mat[12], mat[13], mat[14])
            forward = om2.MVector(-mat[8], -mat[9], -mat[10]).normalize()
            right = om2.MVector(mat[0], mat[1], mat[2]).normalize()
            up = om2.MVector(mat[4], mat[5], mat[6]).normalize()
            
            return {
                'position': cam_pos,
                'forward': forward,
                'right': right,
                'up': up,
                'h_fov': h_fov,
                'v_fov': v_fov,
                'near_clip': near_clip,
                'far_clip': far_clip
            }
            
        except Exception as e:
            print(f"Error getting camera frustum: {str(e)}")
            return None
    
    def is_bbox_in_frustum(self, bbox, frustum):
        if not frustum or not bbox or len(bbox) != 6:
            return False
        
        try:
            corners = [
                om2.MVector(bbox[0], bbox[1], bbox[2]),
                om2.MVector(bbox[3], bbox[1], bbox[2]),
                om2.MVector(bbox[0], bbox[4], bbox[2]),
                om2.MVector(bbox[3], bbox[4], bbox[2]),
                om2.MVector(bbox[0], bbox[1], bbox[5]),
                om2.MVector(bbox[3], bbox[1], bbox[5]),
                om2.MVector(bbox[0], bbox[4], bbox[5]),
                om2.MVector(bbox[3], bbox[4], bbox[5])
            ]
            
            for corner in corners:
                to_corner = corner - frustum['position']
                forward_dist = to_corner * frustum['forward']
                
                if forward_dist < frustum['near_clip'] or forward_dist > frustum['far_clip']:
                    continue
                
                right_dist = to_corner * frustum['right']
                up_dist = to_corner * frustum['up']
                
                half_width = forward_dist * math.tan(frustum['h_fov'] / 2.0) * self.frustum_padding
                half_height = forward_dist * math.tan(frustum['v_fov'] / 2.0) * self.frustum_padding
                
                if abs(right_dist) <= half_width and abs(up_dist) <= half_height:
                    return True
            
            return False
            
        except Exception as e:
            return False
    
    def get_visible_objects_in_camera(self):
        if not self.selected_camera:
            return []
        
        try:
            frustum = self.get_camera_frustum_planes()
            if not frustum:
                return []
            
            print(f"\nCamera Frustum Info:")
            print(f"  H-FOV: {math.degrees(frustum['h_fov']):.2f}°")
            print(f"  V-FOV: {math.degrees(frustum['v_fov']):.2f}°")
            print(f"  Padding: {self.frustum_padding}")
            
            all_meshes = cmds.ls(type='mesh', long=True)
            visible_objects = []
            
            for mesh in all_meshes:
                transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)
                if not transforms:
                    continue
                
                transform = transforms[0]
                
                try:
                    if not cmds.getAttr(transform + '.visibility'):
                        continue
                    
                    parent = transform
                    is_visible = True
                    while parent:
                        try:
                            if not cmds.getAttr(parent + '.visibility'):
                                is_visible = False
                                break
                        except:
                            pass
                        
                        parents = cmds.listRelatives(parent, parent=True, fullPath=True)
                        parent = parents[0] if parents else None
                    
                    if not is_visible:
                        continue
                    
                    if cmds.getAttr(mesh + '.intermediateObject'):
                        continue
                    
                    if cmds.getAttr(transform + '.overrideEnabled'):
                        display_type = cmds.getAttr(transform + '.overrideDisplayType')
                        if display_type in [1, 2]:
                            continue
                    
                    try:
                        bbox = cmds.exactWorldBoundingBox(transform)
                    except:
                        continue
                    
                    if self.is_bbox_in_frustum(bbox, frustum):
                        visible_objects.append(transform)
                    
                except:
                    continue
            
            print(f"Found {len(visible_objects)} visible mesh objects in frustum")
            return visible_objects
            
        except Exception as e:
            print(f"Error getting visible objects: {str(e)}")
            return []
    
    def scan_references(self, *args):
        if not self.selected_camera:
            cmds.warning("Please select a camera first!")
            return
        
        cmds.text(self.scan_status, edit=True, label="Status: Scanning scene...")
        cmds.refresh()
        
        all_refs = cmds.ls(type='reference')
        all_refs = [ref for ref in all_refs if ref not in ['sharedReferenceNode', '_UNKNOWN_REF_NODE_']]
        
        if not all_refs:
            cmds.warning("No references found in scene!")
            return
        
        print(f"\n{'='*60}")
        print(f"Scanning {len(all_refs)} references...")
        print(f"{'='*60}")
        
        visible_objects = self.get_visible_objects_in_camera()
        
        self.all_references = []
        self.visible_references = []
        self.invisible_references = []
        
        # Scan and categorize all references
        for ref in all_refs:
            try:
                ref_file = cmds.referenceQuery(ref, filename=True, withoutCopyNumber=True)
                ref_namespace = cmds.referenceQuery(ref, namespace=True)
                
                ref_data = {
                    'node': ref,
                    'file': ref_file,
                    'namespace': ref_namespace,
                    'short_name': ref_file.split('/')[-1]
                }
                
                # Parse reference type
                ref_data['ref_type'] = self.parse_reference_type(ref_data)
                
                self.all_references.append(ref_data)
                
                # Skip cameras - always keep
                if ref_data['ref_type']['type'] == 'CAMERA':
                    self.visible_references.append(ref_data)
                    print(f"  [CAMERA] {ref_namespace} - always kept")
                    continue
                
                # For GEOMETRY only, check frustum visibility
                if ref_data['ref_type'].get('is_geo', False):
                    ref_nodes = cmds.referenceQuery(ref, nodes=True, dagPath=True)
                    is_visible = False
                    
                    for ref_node in ref_nodes:
                        if ref_node in visible_objects:
                            is_visible = True
                            break
                        
                        try:
                            children = cmds.listRelatives(ref_node, allDescendents=True, fullPath=True, type='transform') or []
                            for child in children:
                                if child in visible_objects:
                                    is_visible = True
                                    break
                        except:
                            pass
                        
                        if is_visible:
                            break
                    
                    if is_visible:
                        self.visible_references.append(ref_data)
                        print(f"  [GEO-KEEP] {ref_namespace} - visible in frustum")
                    else:
                        self.invisible_references.append(ref_data)
                        print(f"  [GEO-REMOVE] {ref_namespace} - not in frustum")
                else:
                    # Non-geometry (shaders, etc.) - add to invisible for now
                    # They will be auto-restored after geometry scan is complete
                    self.invisible_references.append(ref_data)
                    print(f"  [{ref_data['ref_type']['type']}] {ref_namespace} - pending shader matching")

            except Exception as e:
                print(f"Error processing reference {ref}: {str(e)}")
                continue

        # AUTO-RESTORE SHADERS: Find shaders that match geometry in keep list
        self._auto_restore_matching_shaders()

        self.update_reference_lists()

        status_msg = f"Status: {len(self.visible_references)} to keep, {len(self.invisible_references)} to remove"
        cmds.text(self.scan_status, edit=True, label=status_msg)

        print(f"\n{'='*60}")
        print(f"Scan Complete:")
        print(f"  Total: {len(self.all_references)}")
        print(f"  Keep: {len(self.visible_references)} (geometry + matching shaders)")
        print(f"  Remove: {len(self.invisible_references)}")
        print(f"{'='*60}\n")
    
    def update_reference_lists(self):
        cmds.textScrollList(self.visible_list, edit=True, removeAll=True)
        cmds.textScrollList(self.invisible_list, edit=True, removeAll=True)
        
        cmds.text(self.total_refs_text, edit=True, label=f"Total: {len(self.all_references)}")
        cmds.text(self.visible_refs_text, edit=True, label=f"Keep: {len(self.visible_references)}")
        cmds.text(self.invisible_refs_text, edit=True, label=f"Remove: {len(self.invisible_references)}")
        
        # Populate visible list with filtering
        for ref_data in self.visible_references:
            if self.should_show_reference(ref_data, 'visible'):
                ref_info = ref_data['ref_type']
                display_name = f"[{ref_info['display_type']}] {ref_data['namespace']} - {ref_data['short_name']}"
                cmds.textScrollList(self.visible_list, edit=True, append=display_name)
        
        # Populate invisible list with filtering
        for ref_data in self.invisible_references:
            if self.should_show_reference(ref_data, 'invisible'):
                ref_info = ref_data['ref_type']
                display_name = f"[{ref_info['display_type']}] {ref_data['namespace']} - {ref_data['short_name']}"
                cmds.textScrollList(self.invisible_list, edit=True, append=display_name)
        
        self.update_remove_count()
    
    def select_all_invisible(self, select_state):
        if select_state:
            all_items = cmds.textScrollList(self.invisible_list, query=True, allItems=True) or []
            for item in all_items:
                cmds.textScrollList(self.invisible_list, edit=True, selectItem=item)
        else:
            cmds.textScrollList(self.invisible_list, edit=True, deselectAll=True)
        
        self.update_remove_count()
    
    def update_remove_count(self, *args):
        selected = cmds.textScrollList(self.invisible_list, query=True, selectItem=True) or []
        cmds.text(self.remove_count_text, edit=True, label=f"Ready to remove: {len(selected)} reference(s)")
    
    def select_from_viewport(self, list_type):
        """
        Select items in Keep/Remove list based on current viewport selection.
        Finds which references the selected objects belong to and selects them in the list.
        """
        # Get current viewport selection
        viewport_selection = cmds.ls(selection=True, long=True) or []
        if not viewport_selection:
            cmds.warning("No objects selected in viewport!")
            return

        # Determine which list and reference data to use
        if list_type == 'visible':
            ref_list = self.visible_references
            list_widget = self.visible_list
        else:
            ref_list = self.invisible_references
            list_widget = self.invisible_list

        # Get all items currently in the list (respects filters)
        all_list_items = cmds.textScrollList(list_widget, query=True, allItems=True) or []

        # Build a mapping of namespace -> display_name
        namespace_to_display = {}
        for ref_data in ref_list:
            ref_info = ref_data['ref_type']
            display_name = f"[{ref_info['display_type']}] {ref_data['namespace']} - {ref_data['short_name']}"
            if display_name in all_list_items:
                namespace_to_display[ref_data['namespace'].strip(':')] = display_name

        # Find matching references for selected objects
        items_to_select = set()
        matched_count = 0

        for obj in viewport_selection:
            # Extract namespace from object path
            # Object path might be: |SETS_CentralBusinessDistrictAExt_001:CBDAExtBuildB_003:CBDAExtBuildBADoorB_Geo
            obj_name = obj.split('|')[-1]  # Get the leaf node name

            # Try to find matching namespace
            for ns, display_name in namespace_to_display.items():
                # Check if object starts with or contains this namespace
                if obj_name.startswith(ns + ':') or obj_name.startswith(ns + '_') or ns in obj_name:
                    items_to_select.add(display_name)
                    matched_count += 1
                    break

        if not items_to_select:
            cmds.warning(f"No matching references found in {'Keep' if list_type == 'visible' else 'Remove'} list for selected objects!")
            return

        # Deselect all first
        cmds.textScrollList(list_widget, edit=True, deselectAll=True)

        # Select matching items
        for item in items_to_select:
            try:
                cmds.textScrollList(list_widget, edit=True, selectItem=item)
            except Exception as e:
                print(f"Could not select item: {item} - {str(e)}")

        print(f"Selected {len(items_to_select)} reference(s) in {'Keep' if list_type == 'visible' else 'Remove'} list from viewport selection")

        self.update_remove_count()

    def select_reference_in_scene(self, list_type):
        """Select references in Maya scene"""
        if list_type == 'visible':
            selected = cmds.textScrollList(self.visible_list, query=True, selectItem=True)
            ref_list = self.visible_references
        else:
            selected = cmds.textScrollList(self.invisible_list, query=True, selectItem=True)
            ref_list = self.invisible_references
        
        if not selected:
            return
        
        nodes_to_select = []
        for item in selected:
            ref_data = self.get_ref_from_display_name(item, ref_list)
            if ref_data:
                try:
                    ref_nodes = cmds.referenceQuery(ref_data['node'], nodes=True)
                    transforms = [n for n in ref_nodes if cmds.nodeType(n) == 'transform']
                    if transforms:
                        nodes_to_select.extend(transforms[:5])  # Select first 5 transforms
                except:
                    pass
        
        if nodes_to_select:
            cmds.select(nodes_to_select, replace=True)
            print(f"Selected {len(nodes_to_select)} node(s) in scene")
    
    def remove_selected_references(self, *args):
        """Remove selected references from scene"""
        selected_items = cmds.textScrollList(self.invisible_list, query=True, selectItem=True) or []
        
        if not selected_items:
            cmds.warning("No references selected to remove!")
            return
        
        print(f"\n{'='*60}")
        print(f"Removing Selected References")
        print(f"{'='*60}")
        
        refs_to_remove = []
        for item in selected_items:
            ref_data = self.get_ref_from_display_name(item, self.invisible_references)
            if ref_data:
                refs_to_remove.append(ref_data)
                print(f"  Will remove: {ref_data['namespace']} ({ref_data['short_name']})")
        
        if not refs_to_remove:
            cmds.warning("Could not find selected references!")
            return
        
        result = cmds.confirmDialog(
            title='Confirm Removal',
            message=f'Remove {len(refs_to_remove)} reference(s) from scene?',
            button=['Yes', 'No'],
            defaultButton='Yes',
            cancelButton='No'
        )
        
        if result != 'Yes':
            print("Removal cancelled by user.")
            return
        
        removed_count = 0
        failed_refs = []
        
        # Build a set of nodes we want to KEEP (to prevent accidental removal)
        keep_nodes = {ref['node'] for ref in self.visible_references}

        for ref_data in refs_to_remove:
            ref_node = ref_data['node']

            # Safety check: Skip if this node is somehow in keep list
            if ref_node in keep_nodes:
                print(f"⚠ Skipping {ref_data['namespace']} - found in keep list!")
                continue

            try:
                # Check if reference still exists before removing
                if not cmds.objExists(ref_node):
                    print(f"⚠ Reference node no longer exists: {ref_node}")
                    continue

                # Use referenceNode to remove SPECIFIC reference instance
                cmds.file(referenceNode=ref_node, removeReference=True)
                print(f"✓ Removed: {ref_data['namespace']}")
                removed_count += 1
            except Exception as e:
                print(f"✗ Failed to remove {ref_data['namespace']}: {str(e)}")
                failed_refs.append(ref_data['namespace'])
        
        if failed_refs:
            msg = f"Removed {removed_count} reference(s).\n\nFailed: {', '.join(failed_refs)}"
        else:
            msg = f"Successfully removed {removed_count} reference(s)!"
        
        cmds.confirmDialog(title='Complete', message=msg, button=['OK'])
        
        print(f"\n{'='*60}")
        print(f"Removal Complete: {removed_count} removed, {len(failed_refs)} failed")
        print(f"{'='*60}\n")
        
        self.scan_references()
    
    def refresh_lists(self, *args):
        if self.selected_camera:
            self.scan_references()
        else:
            cmds.warning("Please select a camera first!")
    
    def close_window(self, *args):
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)


def show_reference_cleanup_ui():
    ui = ReferenceCleanupUI()
    ui.create_ui()


if __name__ == "__main__":
    show_reference_cleanup_ui()