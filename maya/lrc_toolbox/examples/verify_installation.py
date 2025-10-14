# Installation Verification Script
# Run this to verify that the LRC Toolbox and Save & Settings are properly installed

import os

def verify_installation():
    """Verify that all required files are in the correct relative locations."""
    print("🔍 LRC Toolbox Installation Verification")
    print("=" * 50)
    
    # Try to find this script's location to determine the base directory
    try:
        script_file = __file__
        script_dir = os.path.dirname(script_file)  # examples/
        lrc_toolbox_dir = os.path.dirname(script_dir)  # lrc_toolbox/
        maya_dir = os.path.dirname(lrc_toolbox_dir)  # maya/
        
        print(f"📍 Detected maya directory: {maya_dir}")
        
        # Check required directories and files
        checks = [
            ("Plugin directory", os.path.join(maya_dir, "plugins")),
            ("Plugin file", os.path.join(maya_dir, "plugins", "lrc_toolbox_plugin.py")),
            ("Mockup directory", os.path.join(maya_dir, "mockup")),
            ("Save & Settings script", os.path.join(maya_dir, "mockup", "save_and_setting.py")),
            ("LRC Toolbox directory", os.path.join(maya_dir, "lrc_toolbox")),
            ("LRC Toolbox main", os.path.join(maya_dir, "lrc_toolbox", "main.py")),
        ]
        
        all_good = True
        
        for name, path in checks:
            if os.path.exists(path):
                print(f"   ✅ {name}: {path}")
            else:
                print(f"   ❌ {name}: MISSING - {path}")
                all_good = False
        
        # Verify Save & Settings script content
        save_settings_path = os.path.join(maya_dir, "mockup", "save_and_setting.py")
        if os.path.exists(save_settings_path):
            try:
                with open(save_settings_path, 'r') as f:
                    content = f.read(1000)
                if 'WIN_ID' in content and 'EE_ShotSetup_RS_IO' in content:
                    print(f"   ✅ Save & Settings script content verified")
                else:
                    print(f"   ⚠️ Save & Settings script may be incorrect (missing WIN_ID)")
            except Exception as e:
                print(f"   ⚠️ Could not verify Save & Settings script: {e}")
        
        print(f"\n📋 Installation Status:")
        if all_good:
            print("   ✅ Installation looks correct!")
            print("   ✅ Plugin should work with relative paths")
            print("   ✅ No hardcoded paths needed")
        else:
            print("   ❌ Installation has issues")
            print("   ❌ Some files are missing")
            
        print(f"\n📁 Expected directory structure:")
        print(f"   maya/")
        print(f"   ├── plugins/")
        print(f"   │   └── lrc_toolbox_plugin.py")
        print(f"   ├── mockup/")
        print(f"   │   └── save_and_setting.py")
        print(f"   └── lrc_toolbox/")
        print(f"       └── main.py")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

# Run verification
if __name__ == "__main__":
    verify_installation()
else:
    # When imported or run in Maya Script Editor
    verify_installation()
