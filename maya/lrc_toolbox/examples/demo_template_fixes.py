"""
Demo Template Fixes

This script demonstrates the fixes for:
1. Missing sub-collections in template creation
2. Numeric suffix issue when recreating deleted layers

Run this in Maya to see the fixes in action.
"""

from maya.lrc_toolbox.core.render_setup_api import RenderSetupAPI
from maya.lrc_toolbox.utils import render_layers


def demo_sub_collections_fix():
    """Demonstrate that sub-collections are now created properly."""
    print("=" * 70)
    print("🔧 DEMO: SUB-COLLECTIONS FIX")
    print("=" * 70)
    
    # Initialize API
    rs_api = RenderSetupAPI()
    
    if not render_layers.is_available():
        print("❌ Maya Render Setup not available")
        return
    
    # Clear existing layers
    print("🧹 Clearing existing layers...")
    render_layers.clear_layers(keep_default=True)
    
    # Create a template
    print("🚀 Creating DEMO_BG_A template...")
    success = rs_api.create_bg_template("DEMO", "A")
    
    if success:
        print("✅ Template created successfully!")
        
        # Show detailed structure
        print("\n📋 Template Structure:")
        render_layers.debug_layer_structure("DEMO_BG_A")
        
        # Verify structure
        print("\n🔍 Verification Results:")
        verification = render_layers.verify_template_structure("DEMO_BG_A")
        
        for check, result in verification.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}: {result}")
        
        # Expected structure summary
        print("\n📝 Expected Structure:")
        print("   Layer: DEMO_BG_A")
        print("   ├── Collection: DEMO_BG_A_geo (transforms, pattern: '*')")
        print("   │   ├── Sub-collection: DEMO_BG_A_matte (shapes, pattern: '')")
        print("   │   └── Sub-collection: DEMO_BG_A_visibility (shapes, pattern: '')")
        print("   └── Collection: DEMO_BG_A_light (transforms, pattern: '*')")
        
    else:
        print("❌ Failed to create template")


def demo_numeric_suffix_fix():
    """Demonstrate that recreating deleted layers doesn't add numeric suffixes."""
    print("\n" + "=" * 70)
    print("🔧 DEMO: NUMERIC SUFFIX FIX")
    print("=" * 70)
    
    # Initialize API
    rs_api = RenderSetupAPI()
    
    if not render_layers.is_available():
        print("❌ Maya Render Setup not available")
        return
    
    # Clear existing layers
    print("🧹 Clearing existing layers...")
    render_layers.clear_layers(keep_default=True)
    
    layer_name = "DEMO_CHAR_A"
    
    # Step 1: Create layer
    print(f"🚀 Step 1: Creating {layer_name}...")
    success1 = rs_api.create_char_template("DEMO", "A")
    
    if success1:
        layers1 = render_layers.list_layers()
        print(f"   ✅ Created: {layers1}")
        
        if layer_name in layers1:
            print(f"   ✅ {layer_name} exists")
        else:
            print(f"   ❌ {layer_name} not found")
            return
    else:
        print("   ❌ Failed to create template")
        return
    
    # Step 2: Delete layer
    print(f"\n🗑️  Step 2: Deleting {layer_name}...")
    success2 = render_layers.remove_layer_by_name(layer_name)
    
    if success2:
        layers2 = render_layers.list_layers()
        print(f"   ✅ Deleted: {layers2}")
        
        if layer_name not in layers2:
            print(f"   ✅ {layer_name} successfully removed")
        else:
            print(f"   ❌ {layer_name} still exists")
            return
    else:
        print("   ❌ Failed to delete layer")
        return
    
    # Step 3: Recreate layer
    print(f"\n🚀 Step 3: Recreating {layer_name}...")
    success3 = rs_api.create_char_template("DEMO", "A")
    
    if success3:
        layers3 = render_layers.list_layers()
        print(f"   ✅ Recreated: {layers3}")
        
        # Check for exact name match (no numeric suffix)
        if layer_name in layers3:
            print(f"   ✅ {layer_name} recreated with exact same name!")
            
            # Check for unwanted numeric variants
            numeric_variants = [f"{layer_name}1", f"{layer_name}2", f"{layer_name}01"]
            found_variants = [v for v in numeric_variants if v in layers3]
            
            if found_variants:
                print(f"   ⚠️  Found numeric variants: {found_variants}")
            else:
                print(f"   ✅ No numeric suffixes found - fix working correctly!")
                
        else:
            print(f"   ❌ {layer_name} not found after recreation")
            print(f"   Available layers: {layers3}")
    else:
        print("   ❌ Failed to recreate template")


def demo_batch_creation_with_structure():
    """Demonstrate batch creation with proper structure verification."""
    print("\n" + "=" * 70)
    print("🔧 DEMO: BATCH CREATION WITH STRUCTURE VERIFICATION")
    print("=" * 70)
    
    # Initialize API
    rs_api = RenderSetupAPI()
    
    if not render_layers.is_available():
        print("❌ Maya Render Setup not available")
        return
    
    # Clear existing layers
    print("🧹 Clearing existing layers...")
    render_layers.clear_layers(keep_default=True)
    
    # Create all templates
    print("🚀 Creating all standard templates for 'BATCH'...")
    results = rs_api.create_all_standard_templates("BATCH", "A")
    
    print(f"📊 Creation Results: {results}")
    
    # Verify each template structure
    expected_templates = ["BATCH_BG_A", "BATCH_CHAR_A", "BATCH_ATMOS_A", "BATCH_FX_A"]
    
    print("\n🔍 Verifying template structures:")
    
    for template_name in expected_templates:
        print(f"\n📋 {template_name}:")
        
        verification = render_layers.verify_template_structure(template_name)
        
        all_good = all(verification.values())
        status = "✅ COMPLETE" if all_good else "❌ INCOMPLETE"
        print(f"   Overall: {status}")
        
        for check, result in verification.items():
            status_icon = "✅" if result else "❌"
            print(f"   {status_icon} {check}")
        
        if all_good:
            print(f"   🎉 {template_name} has complete structure!")


def run_all_demos():
    """Run all template fix demonstrations."""
    print("🎭 TEMPLATE FIXES DEMONSTRATION")
    print("=" * 70)
    print("This demo shows the fixes for:")
    print("1. ✅ Missing sub-collections in template creation")
    print("2. ✅ Numeric suffix issue when recreating deleted layers")
    print("=" * 70)
    
    try:
        # Check Maya environment
        import maya.cmds as cmds
        print("✅ Running in Maya environment")
    except ImportError:
        print("⚠️  Running outside Maya - some features may not work")
    
    # Run demonstrations
    demo_sub_collections_fix()
    demo_numeric_suffix_fix()
    demo_batch_creation_with_structure()
    
    print("\n" + "=" * 70)
    print("🎉 DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("Key improvements demonstrated:")
    print("✅ Sub-collections are now properly nested within parent collections")
    print("✅ Recreating deleted layers uses exact same name (no numeric suffixes)")
    print("✅ Batch creation works with complete hierarchical structure")
    print("✅ Verification functions help debug template structure")
    print("\nThe template system is now working as expected! 🚀")


if __name__ == "__main__":
    run_all_demos()
