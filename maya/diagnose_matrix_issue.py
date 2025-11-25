"""
Diagnostic script to identify matrix method issues with multiple assets.

Run this in Maya after a failed build to see what went wrong.
"""

import maya.cmds as cmds

def diagnose_matrix_connections():
    """Diagnose existing matrix connections in the scene."""
    
    print("\n" + "="*80)
    print("MATRIX METHOD DIAGNOSTIC REPORT")
    print("="*80)
    
    # Find all decomposeMatrix nodes
    decomp_nodes = cmds.ls(type="decomposeMatrix") or []
    
    print(f"\nFound {len(decomp_nodes)} decomposeMatrix nodes in scene:")
    print("-"*80)
    
    if not decomp_nodes:
        print("No decomposeMatrix nodes found. Matrix method hasn't been used yet.")
        return
    
    # Analyze each decomposeMatrix node
    for i, decomp in enumerate(decomp_nodes, 1):
        print(f"\n{i}. {decomp}")
        print("   " + "-"*76)
        
        # Check input connections (source transform)
        input_conns = cmds.listConnections(
            "{}.inputMatrix".format(decomp),
            source=True, destination=False, plugs=True
        ) or []
        
        if input_conns:
            print(f"   Input: {input_conns[0]}")
            source_node = input_conns[0].split(".")[0]
            print(f"   Source Node: {source_node}")
        else:
            print("   Input: NONE (disconnected!)")
        
        # Check output connections (destination place3dTexture)
        output_attrs = ["outputTranslate", "outputRotate", "outputScale", "outputShear"]
        destinations = []
        
        for attr in output_attrs:
            out_conns = cmds.listConnections(
                "{}.{}".format(decomp, attr),
                source=False, destination=True, plugs=True
            ) or []
            destinations.extend(out_conns)
        
        if destinations:
            # Get unique destination nodes
            dest_nodes = list(set([conn.split(".")[0] for conn in destinations]))
            print(f"   Output: {dest_nodes[0]}")
            print(f"   Connected Attributes: {len(destinations)}")
        else:
            print("   Output: NONE (disconnected!)")
    
    print("\n" + "="*80)
    print("CHECKING FOR ISSUES")
    print("="*80)
    
    # Check for naming collisions
    print("\n1. Checking for naming pattern issues...")
    ee_decomp_nodes = [n for n in decomp_nodes if n.startswith("EE_") and n.endswith("_decomp")]
    
    if len(ee_decomp_nodes) != len(decomp_nodes):
        print(f"   ⚠️  Found {len(decomp_nodes) - len(ee_decomp_nodes)} nodes with unexpected naming")
        for node in decomp_nodes:
            if node not in ee_decomp_nodes:
                print(f"      - {node}")
    else:
        print(f"   ✅ All {len(ee_decomp_nodes)} nodes follow naming convention")
    
    # Check for disconnected nodes
    print("\n2. Checking for disconnected nodes...")
    disconnected = []
    for decomp in decomp_nodes:
        input_conns = cmds.listConnections("{}.inputMatrix".format(decomp)) or []
        if not input_conns:
            disconnected.append(decomp)
    
    if disconnected:
        print(f"   ⚠️  Found {len(disconnected)} disconnected nodes:")
        for node in disconnected:
            print(f"      - {node}")
    else:
        print(f"   ✅ All nodes are properly connected")
    
    # Check for duplicate connections to same place3dTexture
    print("\n3. Checking for duplicate connections...")
    place3d_map = {}
    
    for decomp in decomp_nodes:
        output_attrs = ["outputTranslate", "outputRotate", "outputScale", "outputShear"]
        for attr in output_attrs:
            out_conns = cmds.listConnections(
                "{}.{}".format(decomp, attr),
                source=False, destination=True, plugs=True
            ) or []
            for conn in out_conns:
                place3d = conn.split(".")[0]
                if place3d not in place3d_map:
                    place3d_map[place3d] = []
                if decomp not in place3d_map[place3d]:
                    place3d_map[place3d].append(decomp)
    
    duplicates = {k: v for k, v in place3d_map.items() if len(v) > 1}
    if duplicates:
        print(f"   ⚠️  Found {len(duplicates)} place3dTexture nodes with multiple connections:")
        for place3d, decomps in duplicates.items():
            print(f"      - {place3d}: connected to {len(decomps)} decomposeMatrix nodes")
            for d in decomps:
                print(f"         * {d}")
    else:
        print(f"   ✅ No duplicate connections found")
    
    # List all place3dTexture nodes and their connection status
    print("\n" + "="*80)
    print("PLACE3D TEXTURE NODES STATUS")
    print("="*80)
    
    all_place3d = cmds.ls(type="place3dTexture") or []
    print(f"\nFound {len(all_place3d)} place3dTexture nodes in scene")
    
    connected_count = 0
    unconnected_count = 0
    
    for place3d in all_place3d:
        # Check if translate is connected
        translate_conn = cmds.listConnections(
            "{}.translate".format(place3d),
            source=True, destination=False
        ) or []
        
        if translate_conn:
            connected_count += 1
        else:
            unconnected_count += 1
    
    print(f"\nConnected: {connected_count}")
    print(f"Unconnected: {unconnected_count}")
    
    if unconnected_count > 0:
        print(f"\n⚠️  {unconnected_count} place3dTexture nodes are not connected!")
        print("   These nodes may need matrix connections:")
        for place3d in all_place3d:
            translate_conn = cmds.listConnections(
                "{}.translate".format(place3d),
                source=True, destination=False
            ) or []
            if not translate_conn:
                print(f"      - {place3d}")
    
    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)

# Run the diagnostic
if __name__ == "__main__":
    diagnose_matrix_connections()

