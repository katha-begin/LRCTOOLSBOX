# -*- coding: utf-8 -*-
"""
Render Layer Detection Test Script

Run this in Maya Script Editor to debug render layer detection issues.
"""

def test_render_layer_detection():
    """Test render layer detection with detailed output."""
    print("\n" + "="*60)
    print("RENDER LAYER DETECTION TEST")
    print("="*60)
    
    # Test 1: Check Render Setup availability
    print("\n[TEST 1] Checking Render Setup availability...")
    try:
        from lrc_toolbox.utils.render_layers import is_available
        
        if is_available():
            print("  ✓ Render Setup is available")
        else:
            print("  ✗ Render Setup is NOT available")
            print("    Make sure you're running in Maya with Render Setup enabled")
            return
            
    except Exception as e:
        print(f"  ✗ Error checking Render Setup: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: List layers using Maya API directly
    print("\n[TEST 2] Listing layers using Maya Render Setup API...")
    try:
        import maya.app.renderSetup.model.renderSetup as renderSetup
        
        rs = renderSetup.instance()
        layers = rs.getRenderLayers()
        
        print(f"  Found {len(layers)} total layers:")
        for layer in layers:
            name = layer.name()
            
            # Check if enabled
            enabled = True
            try:
                if hasattr(layer, 'isEnabled'):
                    enabled = layer.isEnabled()
                elif hasattr(layer, 'isRenderable'):
                    enabled = layer.isRenderable()
            except:
                pass
            
            is_default = (name == "defaultRenderLayer")
            status = "DEFAULT" if is_default else ("ENABLED" if enabled else "DISABLED")
            
            print(f"    - {name} [{status}]")
            
    except Exception as e:
        print(f"  ✗ Error listing layers: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Test list_layers function
    print("\n[TEST 3] Testing list_layers() function...")
    try:
        from lrc_toolbox.utils.render_layers import list_layers
        
        layer_names = list_layers()
        
        if layer_names:
            print(f"  ✓ list_layers() returned {len(layer_names)} layers:")
            for name in layer_names:
                print(f"    - {name}")
        else:
            print("  ✗ list_layers() returned empty list")
            
    except Exception as e:
        print(f"  ✗ Error in list_layers(): {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Test get_all_layers function
    print("\n[TEST 4] Testing get_all_layers() function...")
    try:
        from lrc_toolbox.utils.render_layers import get_all_layers
        
        layers_info = get_all_layers()
        
        if layers_info:
            print(f"  ✓ get_all_layers() returned {len(layers_info)} layers:")
            for info in layers_info:
                name = info.get("name", "Unknown")
                enabled = info.get("enabled", False)
                is_default = info.get("is_default", False)
                
                status = "DEFAULT" if is_default else ("ENABLED" if enabled else "DISABLED")
                print(f"    - {name} [{status}]")
        else:
            print("  ✗ get_all_layers() returned empty list")
            
    except Exception as e:
        print(f"  ✗ Error in get_all_layers(): {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Test ScenePreparation.get_render_layers
    print("\n[TEST 5] Testing ScenePreparation.get_render_layers()...")
    try:
        from lrc_toolbox.core.scene_preparation import ScenePreparation
        
        scene_prep = ScenePreparation()
        layer_names = scene_prep.get_render_layers()
        
        if layer_names:
            print(f"  ✓ ScenePreparation found {len(layer_names)} layers:")
            for name in layer_names:
                print(f"    - {name}")
        else:
            print("  ✗ ScenePreparation returned empty list")
            print("    This is what the Batch Render UI uses!")
            
    except Exception as e:
        print(f"  ✗ Error in ScenePreparation: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Check if layers are enabled
    print("\n[TEST 6] Checking layer enabled status...")
    try:
        import maya.app.renderSetup.model.renderSetup as renderSetup
        
        rs = renderSetup.instance()
        layers = rs.getRenderLayers()
        
        non_default_layers = [l for l in layers if l.name() != "defaultRenderLayer"]
        
        if not non_default_layers:
            print("  ⚠ No non-default layers found!")
            print("    Please create layers in Render Setup window first")
        else:
            print(f"  Found {len(non_default_layers)} non-default layers:")
            for layer in non_default_layers:
                name = layer.name()
                
                # Try multiple methods to check enabled status
                enabled_methods = []
                
                if hasattr(layer, 'isEnabled'):
                    try:
                        enabled_methods.append(("isEnabled()", layer.isEnabled()))
                    except:
                        pass
                
                if hasattr(layer, 'isRenderable'):
                    try:
                        enabled_methods.append(("isRenderable()", layer.isRenderable()))
                    except:
                        pass
                
                print(f"    - {name}:")
                if enabled_methods:
                    for method_name, result in enabled_methods:
                        print(f"        {method_name} = {result}")
                else:
                    print(f"        No enabled check methods available")
                    
    except Exception as e:
        print(f"  ✗ Error checking enabled status: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    # Summary
    print("\n📋 SUMMARY:")
    print("  If you see 3 layers in TEST 2 but 0 in TEST 5:")
    print("    → Layers might be disabled")
    print("    → Check 'Renderable' checkbox in Render Setup")
    print("  ")
    print("  If you see 0 layers in TEST 2:")
    print("    → No layers created in Render Setup")
    print("    → Open Render Setup window and create layers")
    print("")


# Run the test
if __name__ == "__main__":
    test_render_layer_detection()
else:
    # When imported, provide easy function to run
    print("Render Layer Detection Test loaded. Run: test_render_layer_detection()")

