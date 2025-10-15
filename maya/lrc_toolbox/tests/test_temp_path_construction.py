# -*- coding: utf-8 -*-
"""
Test Temp Path Construction

Tests the context-aware temporary file path generation for batch rendering.
"""


def test_temp_path_construction():
    """
    Test temporary file path construction with various scenarios.
    
    Run this in Maya Script Editor to test temp path generation.
    """
    print("=" * 80)
    print("TEMP PATH CONSTRUCTION TEST")
    print("=" * 80)
    
    from lrc_toolbox.utils.temp_file_manager import TempFileManager
    
    temp_manager = TempFileManager()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Shot Scene (with version)",
            "scene_path": "V:/SWA/all/scene/Ep01/sq0010/SH0010/lighting/version/SH0010_lighting_v001.ma",
            "layer_name": "MASTER_BG_A",
            "process_id": "12345"
        },
        {
            "name": "Shot Scene (different episode)",
            "scene_path": "V:/SWA/all/scene/Ep02/sq0050/SH0050/lighting/version/SH0050_lighting_v003.ma",
            "layer_name": "MASTER_CHAR_B",
            "process_id": "12346"
        },
        {
            "name": "Asset Scene (character)",
            "scene_path": "V:/SWA/all/asset/characters/main/hero_char/lighting/version/hero_char_lighting_v002.ma",
            "layer_name": "HERO_CHAR_BG_A",
            "process_id": "12347"
        },
        {
            "name": "Asset Scene (prop)",
            "scene_path": "V:/SWA/all/asset/props/weapons/sword/lighting/version/sword_lighting_v001.ma",
            "layer_name": "SWORD_CHAR_B",
            "process_id": "12348"
        },
        {
            "name": "No Context (fallback to Documents)",
            "scene_path": "C:/Users/artist/Desktop/test_scene.ma",
            "layer_name": "MASTER_ATMOS",
            "process_id": "12349"
        },
        {
            "name": "No Version Number",
            "scene_path": "V:/SWA/all/scene/Ep01/sq0010/SH0010/lighting/SH0010_lighting.ma",
            "layer_name": "MASTER_FX_C",
            "process_id": "12350"
        },
        {
            "name": "Empty Scene Path (fallback)",
            "scene_path": "",
            "layer_name": "MASTER_BG_A",
            "process_id": "12351"
        }
    ]
    
    print("\n" + "=" * 80)
    print("TESTING TEMP PATH GENERATION")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {test_case['name']}")
        print("-" * 80)
        print(f"Scene Path: {test_case['scene_path']}")
        print(f"Layer Name: {test_case['layer_name']}")
        print(f"Process ID: {test_case['process_id']}")
        
        try:
            temp_path = temp_manager.generate_temp_filepath(
                test_case['scene_path'],
                test_case['layer_name'],
                test_case['process_id']
            )
            
            print(f"\n✓ Generated Temp Path:")
            print(f"  {temp_path}")
            
            # Parse the path to show structure
            import os
            parts = temp_path.split(os.sep)
            print(f"\n  Path Structure:")
            for j, part in enumerate(parts):
                indent = "  " * (j + 1)
                print(f"{indent}└─ {part}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("EXPECTED PATH STRUCTURES")
    print("=" * 80)
    
    print("\n1. Shot Scene:")
    print("   V:/SWA/all/scene/.tmp/Ep01/sq0010/SH0010/lighting/MASTER_BG_A/")
    print("   └─ render_SH0010_lighting_v001_20250115_143022_12345.ma")
    
    print("\n2. Asset Scene:")
    print("   V:/SWA/all/asset/.tmp/characters/main/hero_char/lighting/HERO_CHAR_BG_A/")
    print("   └─ render_hero_char_lighting_v002_20250115_143022_12347.ma")
    
    print("\n3. Fallback (No Context):")
    print("   ~/Documents/maya_batch_tmp/MASTER_ATMOS/")
    print("   └─ render_test_scene_20250115_143022_12349.ma")
    
    print("\n" + "=" * 80)
    print("PATH COMPONENTS EXPLANATION")
    print("=" * 80)
    
    print("\nShot Path Structure:")
    print("  {project_root}/scene/.tmp/{episode}/{sequence}/{shot}/{department}/{layer}/")
    print("  └─ render_{shot}_{department}_{version}_{timestamp}_{pid}.ma")
    
    print("\nAsset Path Structure:")
    print("  {project_root}/asset/.tmp/{category}/{subcategory}/{asset}/{department}/{layer}/")
    print("  └─ render_{asset}_{department}_{version}_{timestamp}_{pid}.ma")
    
    print("\nFallback Path Structure:")
    print("  ~/Documents/maya_batch_tmp/{layer}/")
    print("  └─ render_{scene_name}_{version}_{timestamp}_{pid}.ma")
    
    print("\n" + "=" * 80)
    print("KEY FEATURES")
    print("=" * 80)
    
    print("\n✓ Context-aware directory structure")
    print("✓ Temp files under /scene/.tmp or /asset/.tmp")
    print("✓ Organized by episode/sequence/shot or category/subcategory/asset")
    print("✓ Department-specific subdirectories")
    print("✓ Layer-specific subdirectories")
    print("✓ Version number included in filename")
    print("✓ Fallback to ~/Documents/maya_batch_tmp if no context detected")
    print("✓ Automatic directory creation")
    
    print("\n" + "=" * 80)
    print("CLEANUP TESTING")
    print("=" * 80)
    
    print("\nTesting temp file discovery...")
    try:
        temp_files = temp_manager.get_temp_files()
        print(f"✓ Found {len(temp_files)} temp files")
        
        if temp_files:
            print("\nTemp files:")
            for temp_file in temp_files[:5]:  # Show first 5
                print(f"  - {temp_file}")
            if len(temp_files) > 5:
                print(f"  ... and {len(temp_files) - 5} more")
        else:
            print("  (No temp files found - this is normal if you haven't rendered yet)")
    except Exception as e:
        print(f"✗ Error finding temp files: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nTo use in batch rendering:")
    print("1. Open a scene file in standard project structure")
    print("2. Select a render layer")
    print("3. Start batch render")
    print("4. Temp file will be created in context-aware location")
    print("\nTo cleanup temp files:")
    print("  temp_manager.cleanup_temp_files()  # Keep latest 5")
    print("  temp_manager.cleanup_old_files()   # Delete files older than 24 hours")
    print("  temp_manager.cleanup_all()         # Delete all temp files")
    print("=" * 80)


if __name__ == "__main__":
    test_temp_path_construction()

