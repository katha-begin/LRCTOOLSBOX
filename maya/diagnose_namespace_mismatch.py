"""
Diagnostic script to find namespace mismatches between geo and shader namespaces.

This helps identify when Maya auto-renames namespaces (e.g., _shade1, _shade2).
"""

import maya.cmds as cmds
import re

def diagnose_namespace_mismatch():
    """Find all geo/shader namespace pairs, including auto-renamed ones."""
    
    print("\n" + "="*80)
    print("NAMESPACE MISMATCH DIAGNOSTIC")
    print("="*80)
    
    # Get all namespaces
    all_namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True) or []
    
    # Filter out system namespaces
    user_namespaces = [ns for ns in all_namespaces if ns not in ["UI", "shared"]]
    
    print(f"\nFound {len(user_namespaces)} user namespaces:")
    for ns in sorted(user_namespaces):
        print(f"  - {ns}")
    
    # Find geo namespaces (pattern: CHAR_Name_001, PROP_Name_001, etc.)
    geo_pattern = re.compile(r'^(CHAR|PROP|SET|VEH)_([^_]+)_(\d+)$')
    geo_namespaces = []
    
    for ns in user_namespaces:
        if geo_pattern.match(ns):
            geo_namespaces.append(ns)
    
    print(f"\n" + "-"*80)
    print(f"GEO NAMESPACES (pattern: CATEGORY_Name_ID)")
    print("-"*80)
    
    if not geo_namespaces:
        print("No geo namespaces found!")
        return
    
    # For each geo namespace, find corresponding shader namespace(s)
    results = []
    
    for geo_ns in sorted(geo_namespaces):
        match = geo_pattern.match(geo_ns)
        category = match.group(1)
        name = match.group(2)
        identifier = match.group(3)
        
        # Expected shader namespace
        expected_shader_ns = f"{category}_{name}_{identifier}_shade"
        
        # Find actual shader namespaces (may be auto-renamed)
        actual_shader_ns = []
        shader_pattern = re.compile(rf'^{category}_{name}_{identifier}_shade\d*$')
        
        for ns in user_namespaces:
            if shader_pattern.match(ns):
                actual_shader_ns.append(ns)
        
        result = {
            'geo_ns': geo_ns,
            'expected_shader_ns': expected_shader_ns,
            'actual_shader_ns': actual_shader_ns,
            'status': 'OK' if expected_shader_ns in actual_shader_ns else 'MISMATCH'
        }
        results.append(result)
        
        print(f"\n{geo_ns}")
        print(f"  Expected shader: {expected_shader_ns}")
        
        if actual_shader_ns:
            if len(actual_shader_ns) == 1 and actual_shader_ns[0] == expected_shader_ns:
                print(f"  Actual shader:   {actual_shader_ns[0]} ✅")
            else:
                print(f"  Actual shader:   {', '.join(actual_shader_ns)} ⚠️ AUTO-RENAMED")
        else:
            print(f"  Actual shader:   NONE ❌")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    ok_count = sum(1 for r in results if r['status'] == 'OK' and r['actual_shader_ns'])
    mismatch_count = sum(1 for r in results if r['status'] == 'MISMATCH' and r['actual_shader_ns'])
    missing_count = sum(1 for r in results if not r['actual_shader_ns'])
    
    print(f"\nTotal geo namespaces: {len(results)}")
    print(f"  ✅ Matching shader namespaces: {ok_count}")
    print(f"  ⚠️  Auto-renamed shader namespaces: {mismatch_count}")
    print(f"  ❌ Missing shader namespaces: {missing_count}")
    
    if mismatch_count > 0:
        print("\n" + "-"*80)
        print("AUTO-RENAMED SHADER NAMESPACES (NEED FIX)")
        print("-"*80)
        
        for r in results:
            if r['status'] == 'MISMATCH' and r['actual_shader_ns']:
                print(f"\nGeo: {r['geo_ns']}")
                print(f"  Expected: {r['expected_shader_ns']}")
                print(f"  Actual:   {', '.join(r['actual_shader_ns'])}")
                
                # Check for Place3D nodes
                for shader_ns in r['actual_shader_ns']:
                    place3d_nodes = cmds.ls(f"{shader_ns}:*", type="place3dTexture") or []
                    if place3d_nodes:
                        print(f"  Place3D nodes in {shader_ns}: {len(place3d_nodes)}")
                        for p3d in place3d_nodes[:3]:  # Show first 3
                            print(f"    - {p3d}")
                        if len(place3d_nodes) > 3:
                            print(f"    ... and {len(place3d_nodes) - 3} more")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    if mismatch_count > 0:
        print("\nThe shot build code needs to be updated to handle auto-renamed namespaces.")
        print("Instead of assuming exact namespace names, it should:")
        print("  1. Search for shader namespaces matching pattern: {geo_ns}_shade*")
        print("  2. Handle multiple shader namespaces per geo namespace")
        print("  3. Process Place3D nodes from all matching shader namespaces")
    else:
        print("\n✅ All shader namespaces match expected names!")
    
    print("\n" + "="*80)

# Run the diagnostic
if __name__ == "__main__":
    diagnose_namespace_mismatch()

