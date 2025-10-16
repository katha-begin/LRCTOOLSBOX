"""Maya Render Setup utilities (thin facade over Maya API).

Encapsulates availability checks and common operations so other tools
can reuse render setup functionality without duplicating API calls.

This module safely imports Maya renderSetup modules only when used.
Includes quick template creation system for standard render layer hierarchies.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


# Debug flag for override creation tracing
DEBUG_RS_OVERRIDES = True

# Template configuration constants
STANDARD_TEMPLATES = {
    "BG": {
        "element": "BG",
        "description": "Background elements",
        "default_pattern": "*_Grp",
        "collections": ["geo", "light"]
    },
    "CHAR": {
        "element": "CHAR", 
        "description": "Character elements",
        "default_pattern": "*_Grp",
        "collections": ["geo", "light"]
    },
    "ATMOS": {
        "element": "ATMOS",
        "description": "Atmospheric elements", 
        "default_pattern": "*_Grp",
        "collections": ["geo", "light"]
    },
    "FX": {
        "element": "FX",
        "description": "Effects elements",
        "default_pattern": "*_Grp", 
        "collections": ["geo", "light"]
    }
}

@dataclass
class CollectionConfig:
    """Configuration for render layer collection."""
    name: str
    pattern: str
    filter_type: str  # "transforms" or "shapes"
    parent: Optional[str] = None
    sub_collections: Optional[List['CollectionConfig']] = None

@dataclass
class LayerTemplate:
    """Template configuration for render layer creation."""
    name: str
    pattern: str
    filter_type: str
    collections: List[CollectionConfig]
    description: str = ""


def _dbg(msg: str) -> None:
    try:
        if DEBUG_RS_OVERRIDES:
            print(f"[RenderSetup] {msg}")
    except Exception:
        pass

def _api():  # lazy import to avoid import errors outside Maya
    import maya.app.renderSetup.model.renderSetup as renderSetup
    import maya.app.renderSetup.model.renderLayer as renderLayer  # noqa: F401 - kept for completeness
    import maya.app.renderSetup.model.collection as collection
    import maya.app.renderSetup.model.override as override  # noqa: F401 - kept for completeness
    return renderSetup, collection


def is_available() -> bool:
    try:
        _api()
        return True
    except Exception:
        return False


def _layer_enabled(layer) -> bool:
    """Best-effort layer enabled flag across Maya versions.
    Some Maya versions expose isEnabled(), others may not. Fall back to True.
    """
    try:
        fn = getattr(layer, "isEnabled", None)
        if callable(fn):
            return bool(fn())
    except Exception:
        pass
    try:
        fn = getattr(layer, "isRenderable", None)
        if callable(fn):
            return bool(fn())
    except Exception:
        pass
    return True


def _selector_set_shapes_filter(selector):
    """Set selector to filter shapes."""
    try:
        _, collection_mod = _api()
        # Try different Maya API versions
        for const in ("kShapes", "kShape", "Shapes", "SHAPES"):
            if hasattr(collection_mod, const):
                selector.setFilterType(getattr(collection_mod, const))
                return
        # Fallback to integer constants
        for filter_val in (2, "shapes", "Shapes"):
            try:
                selector.setFilterType(filter_val)
                return
            except Exception:
                continue
    except Exception:
        pass


def _selector_set_transforms_filter(selector):
    """Set selector to filter transforms."""
    try:
        _, collection_mod = _api()
        # Try different Maya API versions
        for const in ("kTransforms", "kTransform", "Transforms", "TRANSFORMS"):
            if hasattr(collection_mod, const):
                selector.setFilterType(getattr(collection_mod, const))
                return
        # Fallback to integer constants
        for filter_val in (1, "transforms", "Transforms"):
            try:
                selector.setFilterType(filter_val)
                return
            except Exception:
                continue
    except Exception:
        pass


def _set_collection_filter(collection_obj, filter_type: str, pattern: str = "*"):
    """Set collection selector filter and pattern."""
    try:
        selector = collection_obj.getSelector()
        
        # Set pattern
        if pattern:
            selector.setPattern(pattern)
        
        # Set filter type
        if filter_type.lower() == "shapes":
            _selector_set_shapes_filter(selector)
        else:  # default to transforms
            _selector_set_transforms_filter(selector)
            
        _dbg(f"Set collection filter: {filter_type}, pattern: '{pattern}'")
        
    except Exception as e:
        _dbg(f"Failed to set collection filter: {e}")


def _coll_set_abs_override(coll_obj, attr: str, val: Any):
    """Set absolute override on collection."""
    try:
        override_obj = coll_obj.createAbsOverride(attr, val)
        _dbg(f"Created abs override: {attr} = {val}")
        return override_obj
    except Exception as e:
        _dbg(f"Failed to create abs override {attr}: {e}")
        return None


def list_layers() -> List[str]:
    rs, _ = _api()
    try:
        names = [l.name() for l in rs.instance().getRenderLayers() if l.name() != "defaultRenderLayer"]
        _dbg(f"list_layers -> {len(names)}: {names}")
        return names
    except Exception as e:
        _dbg(f"list_layers failed: {e}")
        return []


def get_all_layers() -> List[Dict[str, Any]]:
    """
    Get all render layers with detailed information.

    Returns list of dictionaries with layer information:
    - name: Layer name
    - enabled: Whether layer is enabled/renderable
    - is_default: Whether this is the default render layer

    Returns:
        List of layer info dictionaries
    """
    try:
        rs, _ = _api()
        layers_info = []

        for layer in rs.instance().getRenderLayers():
            layer_info = {
                "name": layer.name(),
                "enabled": _layer_enabled(layer),
                "is_default": layer.name() == "defaultRenderLayer"
            }
            layers_info.append(layer_info)

        _dbg(f"get_all_layers -> {len(layers_info)} layers")
        return layers_info

    except Exception as e:
        _dbg(f"get_all_layers failed: {e}")
        import traceback
        traceback.print_exc()
        return []


def clear_layers(keep_default: bool = True) -> None:
    """Clear all render layers, optionally keeping the default layer."""
    rs, _ = _api()
    layers_to_remove = []

    # Collect layers to remove (avoid modifying list while iterating)
    for layer in rs.instance().getRenderLayers():
        if keep_default and layer.name() == "defaultRenderLayer":
            continue
        layers_to_remove.append(layer)

    # Remove collected layers
    for layer in layers_to_remove:
        try:
            rs.instance().detachRenderLayer(layer)
            _dbg(f"Removed layer: {layer.name()}")
        except Exception as e:
            _dbg(f"Failed to remove layer {layer.name()}: {e}")


def force_clear_maya_name_cache():
    """
    Force clear Maya's internal name cache to prevent numeric suffixes.

    This function attempts various methods to clear Maya's naming history
    so that deleted layer names can be reused without numeric suffixes.
    """
    try:
        import maya.cmds as cmds

        # Method 1: Flush undo queue
        try:
            cmds.flushUndo()
            _dbg("Flushed undo queue")
        except:
            pass

        # Method 2: Force garbage collection
        try:
            import gc
            gc.collect()
            _dbg("Forced garbage collection")
        except:
            pass

        # Method 3: Clear any lingering references
        try:
            # This forces Maya to refresh its internal node tracking
            cmds.dgdirty(allPlugs=True)
            _dbg("Marked dependency graph dirty")
        except:
            pass

    except Exception as e:
        _dbg(f"Error clearing name cache: {e}")


def remove_layer_by_name(layer_name: str) -> bool:
    """
    Remove a specific render layer by name.

    Args:
        layer_name: Name of the layer to remove

    Returns:
        Success status
    """
    try:
        rs, _ = _api()

        # Find and remove the layer
        for layer in rs.instance().getRenderLayers():
            if layer.name() == layer_name:
                rs.instance().detachRenderLayer(layer)
                _dbg(f"Removed layer: {layer_name}")

                # Clear naming cache after removal
                force_clear_maya_name_cache()

                return True

        _dbg(f"Layer not found: {layer_name}")
        return False

    except Exception as e:
        _dbg(f"Failed to remove layer {layer_name}: {e}")
        return False


def create_layer(name: str) -> None:
    rs, _ = _api()
    rs.instance().createRenderLayer(name)


def create_collection(layer_name: str, collection_name: str, pattern: str = "*") -> None:
    rs, _ = _api()
    layer = next((l for l in rs.instance().getRenderLayers() if l.name() == layer_name), None)
    if not layer:
        raise ValueError(f"Layer not found: {layer_name}")
    coll = layer.createCollection(collection_name)
    coll.getSelector().setPattern(pattern)


def generate_layer_name(context: str, element: str, variance: str = "A") -> str:
    """Generate layer name following naming convention."""
    return f"{context}_{element}_{variance}"


def generate_collection_name(context: str, element: str, variance: str, collection_type: str) -> str:
    """Generate collection name following naming convention."""
    return f"{context}_{element}_{variance}_{collection_type}"


def create_standard_template_config(template_type: str, context: str, variance: str = "A") -> LayerTemplate:
    """
    Create standard template configuration.
    
    Args:
        template_type: Template type (BG, CHAR, ATMOS, FX)
        context: Context prefix (e.g., MASTER, SH0010)
        variance: Variance suffix (default: A)
        
    Returns:
        LayerTemplate configuration
    """
    if template_type not in STANDARD_TEMPLATES:
        raise ValueError(f"Unknown template type: {template_type}. Available: {list(STANDARD_TEMPLATES.keys())}")
    
    template_info = STANDARD_TEMPLATES[template_type]
    element = template_info["element"]
    
    # Generate names
    layer_name = generate_layer_name(context, element, variance)
    geo_collection_name = generate_collection_name(context, element, variance, "geo")
    light_collection_name = generate_collection_name(context, element, variance, "light")
    matte_collection_name = generate_collection_name(context, element, variance, "matte")
    visibility_collection_name = generate_collection_name(context, element, variance, "visibility")
    
    # Create collection configurations
    collections = [
        CollectionConfig(
            name=geo_collection_name,
            pattern="*",
            filter_type="transforms",
            sub_collections=[
                CollectionConfig(
                    name=matte_collection_name,
                    pattern="",  # blank pattern
                    filter_type="shapes",
                    parent=geo_collection_name
                ),
                CollectionConfig(
                    name=visibility_collection_name,
                    pattern="",  # blank pattern
                    filter_type="shapes",
                    parent=geo_collection_name
                )
            ]
        ),
        CollectionConfig(
            name=light_collection_name,
            pattern="*",
            filter_type="transforms"
        )
    ]
    
    return LayerTemplate(
        name=layer_name,
        pattern=template_info["default_pattern"],
        filter_type="transforms",
        collections=collections,
        description=template_info["description"]
    )


def create_template_layer(template: LayerTemplate) -> bool:
    """
    Create render layer from template configuration.

    Args:
        template: LayerTemplate configuration

    Returns:
        Success status
    """
    try:
        rs, _ = _api()
        import maya.cmds as cmds

        # Remove any existing layer with the same name
        existing_layers = rs.instance().getRenderLayers()
        for existing_layer in existing_layers:
            if existing_layer.name() == template.name:
                _dbg(f"Removing existing layer: {template.name}")
                rs.instance().detachRenderLayer(existing_layer)
                break

        # Force clear Maya's naming cache to prevent numeric suffixes
        force_clear_maya_name_cache()

        # Additional cleanup - ensure no nodes with this name exist
        if cmds.objExists(template.name):
            try:
                cmds.delete(template.name)
                _dbg(f"Deleted existing node: {template.name}")
            except:
                pass

        # Try multiple approaches to create layer without suffix
        layer = None
        final_name = None

        # Approach 1: Direct Render Setup API
        try:
            layer = rs.instance().createRenderLayer(template.name)
            final_name = layer.name()
            _dbg(f"Approach 1 - Created layer: {final_name}")

            if final_name == template.name:
                _dbg("✅ Approach 1 successful - exact name match")
            else:
                _dbg(f"⚠️  Approach 1 added suffix: {final_name}")
                # Try to rename
                try:
                    layer.setName(template.name)
                    final_name = layer.name()
                    if final_name == template.name:
                        _dbg("✅ Rename successful")
                    else:
                        _dbg(f"⚠️  Rename failed, still: {final_name}")
                        # Remove and try different approach
                        rs.instance().detachRenderLayer(layer)
                        layer = None
                except Exception as e:
                    _dbg(f"Rename error: {e}")
                    rs.instance().detachRenderLayer(layer)
                    layer = None

        except Exception as e:
            _dbg(f"Approach 1 failed: {e}")

        # Approach 2: Maya commands + Render Setup (if approach 1 failed)
        if layer is None or final_name != template.name:
            try:
                _dbg("Trying Approach 2 - Maya commands + Render Setup")

                # Use Maya commands to create render layer first
                cmds.createRenderLayer(name=template.name, empty=True)

                # Now get it through Render Setup API
                for rs_layer in rs.instance().getRenderLayers():
                    if rs_layer.name() == template.name:
                        layer = rs_layer
                        final_name = layer.name()
                        _dbg(f"✅ Approach 2 successful: {final_name}")
                        break

                if layer is None:
                    _dbg("❌ Approach 2 failed - could not find created layer")

            except Exception as e:
                _dbg(f"Approach 2 failed: {e}")

        # Approach 3: Fallback with temporary name (if both approaches failed)
        if layer is None:
            try:
                _dbg("Trying Approach 3 - Temporary name fallback")
                import time
                temp_name = f"temp_layer_{int(time.time() * 1000)}"

                layer = rs.instance().createRenderLayer(temp_name)
                layer.setName(template.name)
                final_name = layer.name()

                _dbg(f"Approach 3 result: {final_name}")

            except Exception as e:
                _dbg(f"Approach 3 failed: {e}")
                return False

        if layer is None:
            _dbg(f"❌ All approaches failed to create layer: {template.name}")
            return False

        _dbg(f"✅ Final layer created: {layer.name()}")

        # Create collections
        for collection_config in template.collections:
            _create_collection_from_config(layer, collection_config)

        _dbg(f"Template layer created successfully: {layer.name()}")
        return True

    except Exception as e:
        _dbg(f"Failed to create template layer {template.name}: {e}")
        return False


def _create_collection_from_config(parent_layer, collection_config: CollectionConfig) -> bool:
    """
    Create collection from configuration.

    Args:
        parent_layer: Maya render layer object
        collection_config: Collection configuration

    Returns:
        Success status
    """
    try:
        # Create collection
        collection_obj = parent_layer.createCollection(collection_config.name)
        _dbg(f"Created collection: {collection_config.name}")

        # Set collection filter and pattern
        _set_collection_filter(collection_obj, collection_config.filter_type, collection_config.pattern)

        # Create sub-collections if any
        if collection_config.sub_collections:
            for sub_config in collection_config.sub_collections:
                _create_sub_collection_from_config(collection_obj, sub_config)

        return True

    except Exception as e:
        _dbg(f"Failed to create collection {collection_config.name}: {e}")
        return False


def _create_sub_collection_from_config(parent_collection, sub_config: CollectionConfig) -> bool:
    """
    Create sub-collection from configuration.

    Maya Render Setup API supports nested collections through createCollection on parent collection.

    Args:
        parent_collection: Maya collection object
        sub_config: Sub-collection configuration

    Returns:
        Success status
    """
    try:
        # Create nested sub-collection within the parent collection
        sub_collection = parent_collection.createCollection(sub_config.name)
        _dbg(f"Created nested sub-collection: {sub_config.name} under {parent_collection.name()}")

        # Set sub-collection filter and pattern
        _set_collection_filter(sub_collection, sub_config.filter_type, sub_config.pattern)

        # Recursively create any nested sub-collections
        if sub_config.sub_collections:
            for nested_config in sub_config.sub_collections:
                _create_sub_collection_from_config(sub_collection, nested_config)

        return True

    except Exception as e:
        _dbg(f"Failed to create sub-collection {sub_config.name}: {e}")
        return False


# Quick template creation methods
def create_bg_template(context: str, variance: str = "A") -> bool:
    """Create background template layer."""
    template = create_standard_template_config("BG", context, variance)
    return create_template_layer(template)


def create_char_template(context: str, variance: str = "A") -> bool:
    """Create character template layer."""
    template = create_standard_template_config("CHAR", context, variance)
    return create_template_layer(template)


def create_atmos_template(context: str, variance: str = "A") -> bool:
    """Create atmospheric template layer."""
    template = create_standard_template_config("ATMOS", context, variance)
    return create_template_layer(template)


def create_fx_template(context: str, variance: str = "A") -> bool:
    """Create effects template layer."""
    template = create_standard_template_config("FX", context, variance)
    return create_template_layer(template)


def create_all_standard_templates(context: str, variance: str = "A") -> Dict[str, bool]:
    """
    Create all standard template layers.

    Args:
        context: Context prefix (e.g., MASTER, SH0010)
        variance: Variance suffix (default: A)

    Returns:
        Dictionary mapping template type to success status
    """
    results = {}

    for template_type in STANDARD_TEMPLATES.keys():
        try:
            template = create_standard_template_config(template_type, context, variance)
            success = create_template_layer(template)
            results[template_type] = success

            if success:
                _dbg(f"Created {template_type} template: {template.name}")
            else:
                _dbg(f"Failed to create {template_type} template: {template.name}")

        except Exception as e:
            _dbg(f"Error creating {template_type} template: {e}")
            results[template_type] = False

    return results


def debug_layer_structure(layer_name: str = None) -> None:
    """
    Debug function to print detailed layer structure.

    Args:
        layer_name: Specific layer to debug, or None for all layers
    """
    try:
        rs, _ = _api()

        layers = rs.instance().getRenderLayers()

        for layer in layers:
            if layer_name and layer.name() != layer_name:
                continue

            if layer.name() == "defaultRenderLayer":
                continue

            print(f"\n🔍 Layer: {layer.name()}")

            try:
                collections = layer.getCollections()
                print(f"   Collections: {len(collections)}")

                for i, collection in enumerate(collections):
                    print(f"   📂 [{i+1}] Collection: {collection.name()}")

                    # Get selector info
                    try:
                        selector = collection.getSelector()
                        pattern = selector.getPattern()
                        print(f"       Pattern: '{pattern}'")

                        # Try to get filter type (may vary by Maya version)
                        try:
                            filter_type = selector.getFilterType()
                            print(f"       Filter Type: {filter_type}")
                        except:
                            print(f"       Filter Type: [Unable to determine]")

                    except Exception as e:
                        print(f"       Selector Error: {e}")

                    # Check for sub-collections (nested collections)
                    try:
                        sub_collections = collection.getCollections()
                        if sub_collections:
                            print(f"       Sub-collections: {len(sub_collections)}")

                            for j, sub_collection in enumerate(sub_collections):
                                print(f"       📄 [{j+1}] Sub-collection: {sub_collection.name()}")

                                # Get sub-collection selector info
                                try:
                                    sub_selector = sub_collection.getSelector()
                                    sub_pattern = sub_selector.getPattern()
                                    print(f"           Pattern: '{sub_pattern}'")

                                    try:
                                        sub_filter_type = sub_selector.getFilterType()
                                        print(f"           Filter Type: {sub_filter_type}")
                                    except:
                                        print(f"           Filter Type: [Unable to determine]")

                                except Exception as e:
                                    print(f"           Sub-selector Error: {e}")
                        else:
                            print(f"       Sub-collections: 0")

                    except Exception as e:
                        print(f"       Sub-collections Error: {e}")

            except Exception as e:
                print(f"   Collections Error: {e}")

    except Exception as e:
        print(f"Debug Error: {e}")


def verify_template_structure(template_name: str) -> Dict[str, bool]:
    """
    Verify that a template has the expected structure.

    Args:
        template_name: Name of the template to verify (e.g., "MASTER_BG_A")

    Returns:
        Dictionary with verification results
    """
    results = {
        "layer_exists": False,
        "geo_collection_exists": False,
        "light_collection_exists": False,
        "matte_sub_collection_exists": False,
        "visibility_sub_collection_exists": False
    }

    try:
        rs, _ = _api()

        # Find the layer
        target_layer = None
        for layer in rs.instance().getRenderLayers():
            if layer.name() == template_name:
                target_layer = layer
                results["layer_exists"] = True
                break

        if not target_layer:
            return results

        # Check collections
        collections = target_layer.getCollections()

        geo_collection = None
        light_collection = None

        for collection in collections:
            if collection.name().endswith("_geo"):
                results["geo_collection_exists"] = True
                geo_collection = collection
            elif collection.name().endswith("_light"):
                results["light_collection_exists"] = True
                light_collection = collection

        # Check sub-collections in geo collection
        if geo_collection:
            sub_collections = geo_collection.getCollections()
            for sub_collection in sub_collections:
                if sub_collection.name().endswith("_matte"):
                    results["matte_sub_collection_exists"] = True
                elif sub_collection.name().endswith("_visibility"):
                    results["visibility_sub_collection_exists"] = True

        return results

    except Exception as e:
        print(f"Verification Error: {e}")
        return results
