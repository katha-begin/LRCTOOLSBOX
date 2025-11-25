"""
Test script to diagnose matrix method issues with multiple assets.

Run this in Maya Script Editor to test the matrix method with multiple assets.
"""

import maya.cmds as cmds

def test_matrix_naming():
    """Test decomposeMatrix node naming with multiple assets."""
    
    print("\n" + "="*60)
    print("Testing Matrix Method Node Naming")
    print("="*60)
    
    # Test cases: Different assets with same Place3D node names
    test_cases = [
        {
            "src": "CHAR_Kit_001:Body_Grp",
            "dst": "CHAR_Kit_001_shade:Body_Place3dTexture",
            "expected_decomp": "EE_CHAR_Kit_001_shade_Body_Place3dTexture_decomp"
        },
        {
            "src": "CHAR_Fox_001:Body_Grp",
            "dst": "CHAR_Fox_001_shade:Body_Place3dTexture",
            "expected_decomp": "EE_CHAR_Fox_001_shade_Body_Place3dTexture_decomp"
        },
        {
            "src": "CHAR_Bear_001:Body_Grp",
            "dst": "CHAR_Bear_001_shade:Body_Place3dTexture",
            "expected_decomp": "EE_CHAR_Bear_001_shade_Body_Place3dTexture_decomp"
        },
        {
            "src": "PROP_Table_001:Body_Grp",
            "dst": "PROP_Table_001_shade:Body_Place3dTexture",
            "expected_decomp": "EE_PROP_Table_001_shade_Body_Place3dTexture_decomp"
        }
    ]
    
    print("\nTest Cases:")
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. Asset: {case['dst'].split(':')[0]}")
        print(f"   Source: {case['src']}")
        print(f"   Destination: {case['dst']}")
        print(f"   Expected decomp name: {case['expected_decomp']}")
        
        # Generate the name using current logic
        decomp_name = "EE_{}_decomp".format(case['dst'].replace(":", "_"))
        print(f"   Generated decomp name: {decomp_name}")
        
        if decomp_name == case['expected_decomp']:
            print(f"   ✅ Name generation correct")
        else:
            print(f"   ❌ Name generation WRONG!")
    
    print("\n" + "="*60)
    print("Checking for name collisions...")
    print("="*60)
    
    generated_names = []
    for case in test_cases:
        decomp_name = "EE_{}_decomp".format(case['dst'].replace(":", "_"))
        generated_names.append(decomp_name)
    
    if len(generated_names) == len(set(generated_names)):
        print("✅ All names are unique - no collisions!")
    else:
        print("❌ NAME COLLISION DETECTED!")
        from collections import Counter
        counts = Counter(generated_names)
        for name, count in counts.items():
            if count > 1:
                print(f"   Duplicate: {name} (appears {count} times)")
    
    print("\n" + "="*60)
    print("Testing actual node creation in Maya...")
    print("="*60)
    
    # Clean up any existing test nodes
    for name in generated_names:
        if cmds.objExists(name):
            cmds.delete(name)
            print(f"Cleaned up existing: {name}")
    
    # Try creating all nodes
    created_nodes = []
    for i, case in enumerate(test_cases, 1):
        decomp_name = "EE_{}_decomp".format(case['dst'].replace(":", "_"))
        
        print(f"\n{i}. Creating: {decomp_name}")
        
        if cmds.objExists(decomp_name):
            print(f"   ⚠️  Node already exists!")
            actual_name = decomp_name
        else:
            try:
                actual_name = cmds.createNode("decomposeMatrix", name=decomp_name)
                print(f"   ✅ Created: {actual_name}")
                
                if actual_name != decomp_name:
                    print(f"   ⚠️  WARNING: Maya renamed node!")
                    print(f"      Requested: {decomp_name}")
                    print(f"      Actual: {actual_name}")
                
                created_nodes.append(actual_name)
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"Test cases: {len(test_cases)}")
    print(f"Nodes created: {len(created_nodes)}")
    print(f"Success rate: {len(created_nodes)}/{len(test_cases)}")
    
    if len(created_nodes) == len(test_cases):
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED!")
    
    # Cleanup
    print("\nCleaning up test nodes...")
    for node in created_nodes:
        if cmds.objExists(node):
            cmds.delete(node)
    print("Cleanup complete.")
    
    print("\n" + "="*60)

# Run the test
if __name__ == "__main__":
    test_matrix_naming()

