"""
Quick Template Creation Demo

This script demonstrates the quick template creation system for render layers.
Run this in Maya to create standard template layers with hierarchical collections.
"""

from maya.lrc_toolbox.core.render_setup_api import RenderSetupAPI


def demo_quick_templates():
    """Demonstrate quick template creation."""
    print("=" * 60)
    print("QUICK TEMPLATE CREATION DEMO")
    print("=" * 60)
    
    # Initialize Render Setup API
    rs_api = RenderSetupAPI()
    
    # Check if Render Setup is available
    if not rs_api._maya_available:
        print("❌ Maya Render Setup not available")
        return
    
    print("✅ Maya Render Setup available")
    print()
    
    # Show available template types
    template_types = rs_api.get_available_template_types()
    print(f"📋 Available template types: {', '.join(template_types)}")
    print()
    
    # Show template information
    for template_type in template_types:
        info = rs_api.get_template_info(template_type)
        if info:
            print(f"🔧 {template_type} Template:")
            print(f"   Description: {info['description']}")
            print(f"   Default Pattern: {info['default_pattern']}")
            print(f"   Collections: {', '.join(info['collections'])}")
            print()
    
    # Create individual templates
    print("🚀 Creating individual templates...")
    context = "MASTER"
    variance = "A"
    
    # Create BG template
    print(f"Creating BG template: {context}_BG_{variance}")
    success = rs_api.create_bg_template(context, variance)
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    print()
    
    # Create CHAR template
    print(f"Creating CHAR template: {context}_CHAR_{variance}")
    success = rs_api.create_char_template(context, variance)
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    print()
    
    # Create ATMOS template
    print(f"Creating ATMOS template: {context}_ATMOS_{variance}")
    success = rs_api.create_atmos_template(context, variance)
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    print()
    
    # Create FX template
    print(f"Creating FX template: {context}_FX_{variance}")
    success = rs_api.create_fx_template(context, variance)
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    print()
    
    # List created layers
    from maya.lrc_toolbox.utils import render_layers
    created_layers = render_layers.list_layers()
    print(f"📝 Created layers: {created_layers}")
    print()


def demo_batch_creation():
    """Demonstrate batch template creation."""
    print("=" * 60)
    print("BATCH TEMPLATE CREATION DEMO")
    print("=" * 60)
    
    # Initialize Render Setup API
    rs_api = RenderSetupAPI()
    
    if not rs_api._maya_available:
        print("❌ Maya Render Setup not available")
        return
    
    # Clear existing layers first
    print("🧹 Clearing existing layers...")
    from maya.lrc_toolbox.utils import render_layers
    render_layers.clear_layers(keep_default=True)
    print("   Cleared existing layers")
    print()
    
    # Create all standard templates at once
    print("🚀 Creating all standard templates...")
    context = "SH0010"
    variance = "A"
    
    results = rs_api.create_all_standard_templates(context, variance)
    print()
    
    # Show detailed results
    print("📊 Detailed Results:")
    for template_type, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        layer_name = f"{context}_{template_type}_{variance}"
        print(f"   {template_type}: {layer_name} - {status}")
    print()
    
    # List final layers
    final_layers = render_layers.list_layers()
    print(f"📝 Final layers: {final_layers}")
    print()


def demo_layer_structure():
    """Demonstrate the layer structure created by templates."""
    print("=" * 60)
    print("LAYER STRUCTURE DEMONSTRATION")
    print("=" * 60)
    
    # Show the expected structure
    print("🏗️  Expected Layer Structure:")
    print()
    
    context = "MASTER"
    variance = "A"
    
    for template_type in ["BG", "CHAR", "ATMOS", "FX"]:
        layer_name = f"{context}_{template_type}_{variance}"
        print(f"📁 Layer: {layer_name}")
        print(f"   └── Filter: transforms, Pattern: '*_Grp'")
        print(f"   ├── 📂 Collection: {layer_name}_geo")
        print(f"   │   └── Filter: transforms, Pattern: '*'")
        print(f"   │   ├── 📄 Sub-Collection: {layer_name}_matte")
        print(f"   │   │   └── Filter: shapes, Pattern: '' (blank)")
        print(f"   │   └── 📄 Sub-Collection: {layer_name}_visibility")
        print(f"   │       └── Filter: shapes, Pattern: '' (blank)")
        print(f"   └── 📂 Collection: {layer_name}_light")
        print(f"       └── Filter: transforms, Pattern: '*'")
        print()


if __name__ == "__main__":
    # Run demos
    demo_layer_structure()
    demo_quick_templates()
    demo_batch_creation()
    
    print("=" * 60)
    print("DEMO COMPLETED")
    print("=" * 60)
    print()
    print("💡 Usage in your code:")
    print("   from maya.lrc_toolbox.core.render_setup_api import RenderSetupAPI")
    print("   rs_api = RenderSetupAPI()")
    print("   rs_api.create_bg_template('MASTER', 'A')")
    print("   rs_api.create_all_standard_templates('SH0010', 'A')")
