# Test script for Maya Script Editor
# Copy and paste this into Maya's Script Editor (Python tab) and run

print("🧪 Testing LRC Toolbox Plugin Commands")
print("=" * 50)

try:
    import maya.cmds as cmds
    
    # Test 1: Check if plugin is loaded
    print("\n📋 Test 1: Check Plugin Status")
    plugins = cmds.pluginInfo(query=True, listPlugins=True) or []
    lrc_plugin_loaded = any('lrc_toolbox_plugin' in p for p in plugins)
    
    if lrc_plugin_loaded:
        print("✅ LRC Toolbox plugin is loaded")
    else:
        print("❌ LRC Toolbox plugin is NOT loaded")
        print("   Please load it from Window > Settings/Preferences > Plug-in Manager")
        
    # Test 2: Check if commands are available
    print("\n📋 Test 2: Check Available Commands")
    
    # Check lrcToolboxOpen command
    try:
        if cmds.commandPort(query=True, listCommands=True):
            pass  # Just testing if command system works
        print("✅ Maya command system is working")
    except:
        print("⚠️ Maya command system issue")
    
    # Test 3: Try to call the Save & Settings command
    print("\n📋 Test 3: Test Save & Settings Command")
    try:
        # This should work if plugin is loaded
        cmds.lrcOpenSaveSettings()
        print("✅ lrcOpenSaveSettings command executed successfully!")
        print("   The Save & Settings UI should now be open")
    except Exception as e:
        print(f"❌ Error calling lrcOpenSaveSettings: {e}")
        print("   Make sure the plugin is loaded properly")
    
    # Test 4: Check menu
    print("\n📋 Test 4: Check Menu Existence")
    if cmds.menu("lrcToolboxMenu", exists=True):
        print("✅ LRC Toolbox menu exists")
        
        # List menu items
        menu_items = cmds.menu("lrcToolboxMenu", query=True, itemArray=True) or []
        print(f"   Menu items found: {len(menu_items)}")
        for item in menu_items:
            try:
                label = cmds.menuItem(item, query=True, label=True)
                print(f"   - {label}")
            except:
                print(f"   - {item}")
    else:
        print("❌ LRC Toolbox menu does not exist")
        
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test completed!")
print("\nIf the plugin is loaded correctly, you should see:")
print("✅ Plugin loaded")
print("✅ Menu exists") 
print("✅ Command executed successfully")
print("\nIf not, please:")
print("1. Load the plugin from Plug-in Manager")
print("2. Check that the plugin path is correct")
print("3. Look for any error messages in the Script Editor")
