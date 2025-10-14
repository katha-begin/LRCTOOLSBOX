"""
Simple Numeric Suffix Test

A simple test to verify the numeric suffix fix is working.
Run this in Maya to test the create -> delete -> create cycle.
"""

from maya.lrc_toolbox.core.render_setup_api import RenderSetupAPI
from maya.lrc_toolbox.utils import render_layers


def simple_test():
    """Simple test for numeric suffix fix."""
    print("🧪 SIMPLE NUMERIC SUFFIX TEST")
    print("=" * 50)
    
    # Initialize
    rs_api = RenderSetupAPI()
    
    if not render_layers.is_available():
        print("❌ Maya Render Setup not available")
        return
    
    # Clear all layers first
    print("🧹 Clearing all existing layers...")
    render_layers.clear_layers(keep_default=True)
    initial_layers = render_layers.list_layers()
    print(f"Initial layers: {initial_layers}")
    
    # Test layer name
    test_name = "MASTER_BG_A"
    
    print(f"\n🚀 Step 1: Creating {test_name}...")
    success1 = rs_api.create_bg_template("MASTER", "A")
    
    if success1:
        layers1 = render_layers.list_layers()
        print(f"✅ Created successfully: {layers1}")
        
        if test_name in layers1:
            print(f"✅ {test_name} found in layers")
        else:
            print(f"❌ {test_name} NOT found in layers")
            return
    else:
        print("❌ Failed to create template")
        return
    
    print(f"\n🗑️  Step 2: Deleting {test_name}...")
    success2 = render_layers.remove_layer_by_name(test_name)
    
    if success2:
        layers2 = render_layers.list_layers()
        print(f"✅ Deleted successfully: {layers2}")
        
        if test_name not in layers2:
            print(f"✅ {test_name} successfully removed")
        else:
            print(f"❌ {test_name} still exists after deletion")
            return
    else:
        print("❌ Failed to delete layer")
        return
    
    print(f"\n🚀 Step 3: Recreating {test_name}...")
    success3 = rs_api.create_bg_template("MASTER", "A")
    
    if success3:
        layers3 = render_layers.list_layers()
        print(f"✅ Recreated successfully: {layers3}")
        
        # Check for exact name match
        if test_name in layers3:
            print(f"🎉 SUCCESS! {test_name} recreated with exact same name!")
            
            # Check for numeric variants
            variants = [f"{test_name}1", f"{test_name}2", f"{test_name}01"]
            found_variants = [v for v in variants if v in layers3]
            
            if found_variants:
                print(f"⚠️  WARNING: Found numeric variants: {found_variants}")
                print("❌ Numeric suffix fix is NOT working")
            else:
                print("✅ No numeric suffixes found - fix is working!")
                
        else:
            print(f"❌ FAILED: {test_name} not found after recreation")
            print(f"Available layers: {layers3}")
            
            # Check for suffixed versions
            suffixed = [l for l in layers3 if l.startswith("MASTER_BG_A")]
            if suffixed:
                print(f"❌ Found suffixed versions: {suffixed}")
                print("❌ Numeric suffix fix is NOT working")
            else:
                print("❓ No related layers found - unknown issue")
    else:
        print("❌ Failed to recreate template")
    
    print("\n" + "=" * 50)


def debug_layer_info():
    """Show detailed layer information for debugging."""
    print("\n🔍 DEBUG: Current Layer Information")
    print("-" * 40)
    
    try:
        layers = render_layers.list_layers()
        print(f"Current layers: {layers}")
        
        if layers:
            for layer_name in layers:
                print(f"\n📋 Layer: {layer_name}")
                render_layers.debug_layer_structure(layer_name)
        else:
            print("No custom layers found (only default layer exists)")
            
    except Exception as e:
        print(f"Error getting layer info: {e}")


if __name__ == "__main__":
    print("🎯 RUNNING SIMPLE NUMERIC SUFFIX TEST")
    print("This test will:")
    print("1. Create MASTER_BG_A template")
    print("2. Delete MASTER_BG_A")
    print("3. Create MASTER_BG_A again")
    print("4. Check if it has the exact same name (no numeric suffix)")
    print()
    
    simple_test()
    debug_layer_info()
    
    print("\n💡 If the test shows numeric suffixes are still being added:")
    print("1. Try saving and reopening the Maya scene")
    print("2. Run the test again")
    print("3. Check Maya's undo settings (Edit > Preferences > Undo)")
    print("4. Try running: maya.cmds.flushUndo() manually")
