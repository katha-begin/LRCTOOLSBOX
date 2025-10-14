# Test script to verify the plugin fix
# Run this in Maya Script Editor after loading the plugin

import maya.cmds as cmds

print("🧪 Testing LRC Toolbox Plugin Fix")
print("=" * 40)

try:
    # Test 1: Check if plugin is loaded
    loaded_plugins = cmds.pluginInfo(query=True, listPlugins=True) or []
    lrc_plugin = None
    for plugin in loaded_plugins:
        if 'lrc_toolbox_plugin' in plugin:
            lrc_plugin = plugin
            break
    
    if lrc_plugin:
        print(f"✅ Plugin loaded: {lrc_plugin}")
        
        # Get plugin path
        try:
            plugin_path = cmds.pluginInfo(lrc_plugin, query=True, path=True)
            print(f"✅ Plugin path: {plugin_path}")
        except:
            print("⚠️ Could not get plugin path")
    else:
        print("❌ LRC Toolbox plugin not loaded")
        print("Please load it from Plug-in Manager first")
        
    # Test 2: Check if command exists
    print(f"\n🔧 Testing command availability:")
    try:
        # This should work if plugin is properly loaded
        result = cmds.lrcOpenSaveSettings()
        print(f"✅ Command executed successfully!")
    except Exception as e:
        print(f"❌ Command failed: {e}")
        
    # Test 3: Check menu
    print(f"\n📋 Testing menu:")
    if cmds.menu("lrcToolboxMenu", exists=True):
        print("✅ LRC Toolbox menu exists")
    else:
        print("❌ LRC Toolbox menu missing")

except Exception as e:
    print(f"❌ Test failed: {e}")

print("\n" + "=" * 40)
print("Test completed!")
