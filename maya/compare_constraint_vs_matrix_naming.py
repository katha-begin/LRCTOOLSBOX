"""
Compare naming patterns between constraint and matrix methods.

This shows the difference in how nodes are named.
"""

import maya.cmds as cmds

def _short(node):
    """Strip namespace - same as in igl_shot_build.py"""
    return node.split(":")[-1] if node else node

def compare_naming():
    """Compare constraint vs matrix naming patterns."""
    
    print("\n" + "="*80)
    print("CONSTRAINT vs MATRIX NAMING COMPARISON")
    print("="*80)
    
    # Test cases: Multiple assets with same Place3D node names
    test_cases = [
        {
            "asset": "CHAR_Kit_001",
            "src": "CHAR_Kit_001:Body_Grp",
            "dst": "CHAR_Kit_001_shade:Body_Place3dTexture"
        },
        {
            "asset": "CHAR_Fox_001",
            "src": "CHAR_Fox_001:Body_Grp",
            "dst": "CHAR_Fox_001_shade:Body_Place3dTexture"
        },
        {
            "asset": "CHAR_Bear_001",
            "src": "CHAR_Bear_001:Body_Grp",
            "dst": "CHAR_Bear_001_shade:Body_Place3dTexture"
        }
    ]
    
    print("\n" + "-"*80)
    print("CONSTRAINT METHOD NAMING (uses _short())")
    print("-"*80)
    
    constraint_names = {"pcon": [], "scon": []}
    
    for i, case in enumerate(test_cases, 1):
        dst_node = case['dst']
        
        # Constraint naming (uses _short)
        pcon_name = "EE_{}_pcon".format(_short(dst_node))
        scon_name = "EE_{}_scon".format(_short(dst_node))
        
        constraint_names["pcon"].append(pcon_name)
        constraint_names["scon"].append(scon_name)
        
        print(f"\n{i}. Asset: {case['asset']}")
        print(f"   Destination: {dst_node}")
        print(f"   Short name: {_short(dst_node)}")
        print(f"   Parent Constraint: {pcon_name}")
        print(f"   Scale Constraint:  {scon_name}")
    
    # Check for collisions
    print("\n" + "-"*80)
    print("CONSTRAINT METHOD - Collision Check")
    print("-"*80)
    
    pcon_unique = len(set(constraint_names["pcon"]))
    scon_unique = len(set(constraint_names["scon"]))
    
    if pcon_unique < len(constraint_names["pcon"]):
        print(f"⚠️  Parent Constraint COLLISION: {len(constraint_names['pcon'])} names, only {pcon_unique} unique")
        print(f"   All names: {constraint_names['pcon'][0]}")
    else:
        print(f"✅ Parent Constraint: All {pcon_unique} names are unique")
    
    if scon_unique < len(constraint_names["scon"]):
        print(f"⚠️  Scale Constraint COLLISION: {len(constraint_names['scon'])} names, only {scon_unique} unique")
        print(f"   All names: {constraint_names['scon'][0]}")
    else:
        print(f"✅ Scale Constraint: All {scon_unique} names are unique")
    
    print("\n" + "-"*80)
    print("MATRIX METHOD NAMING (uses full namespace)")
    print("-"*80)
    
    matrix_names = []
    
    for i, case in enumerate(test_cases, 1):
        dst_node = case['dst']
        
        # Matrix naming (uses full name with : replaced by _)
        decomp_name = "EE_{}_decomp".format(dst_node.replace(":", "_"))
        matrix_names.append(decomp_name)
        
        print(f"\n{i}. Asset: {case['asset']}")
        print(f"   Destination: {dst_node}")
        print(f"   DecomposeMatrix: {decomp_name}")
    
    # Check for collisions
    print("\n" + "-"*80)
    print("MATRIX METHOD - Collision Check")
    print("-"*80)
    
    matrix_unique = len(set(matrix_names))
    
    if matrix_unique < len(matrix_names):
        print(f"⚠️  DecomposeMatrix COLLISION: {len(matrix_names)} names, only {matrix_unique} unique")
    else:
        print(f"✅ DecomposeMatrix: All {matrix_unique} names are unique")
    
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    print("\nConstraint Method:")
    print("  - Uses _short() which strips namespace")
    print("  - Creates name collisions with multiple assets")
    print("  - BUT: Checks if constraint already exists on destination node")
    print("  - Uses: cmds.listRelatives(dst_node, type='parentConstraint')")
    print("  - This checks the DESTINATION, not the global constraint name")
    
    print("\nMatrix Method:")
    print("  - Uses full namespace (colon → underscore)")
    print("  - Creates unique names for each asset")
    print("  - Checks if decomposeMatrix node exists globally")
    print("  - Uses: cmds.objExists(decomp_name)")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    print("\nOption 1: Keep current matrix naming (RECOMMENDED)")
    print("  ✅ Unique names per asset")
    print("  ✅ No collisions")
    print("  ✅ Easy to identify which asset owns the node")
    
    print("\nOption 2: Match constraint naming (use _short)")
    print("  ⚠️  Name collisions possible")
    print("  ⚠️  Need to check connections instead of node existence")
    print("  ⚠️  Less clear which asset owns the node")
    
    print("\n" + "="*80)

# Run the comparison
if __name__ == "__main__":
    compare_naming()

