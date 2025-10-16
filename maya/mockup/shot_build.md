I want to continue working on @e:\dev\LRCtoolsbox\LRCtoolsbox/maya\mockup\igl_shot_build.py for create mock up shot reference build. this is standalone script and everything stay inside this file.

1. create 4 tap for shot build
2. create drop down mane to selected project,ep,seq, shot, version  by walk thought the directory V:/
3. after select the shot list cache from V:\{project}\all\scene\{ep}\{seq}\{shot}\anim\publish\{version}
4. list  all asset from the directory and store in memory, ex. name Ep01_sq0010_SH0020__PROP_ChickenAlarmClock_001.abc = {Ep}_{sq}_{shot}__{catagory}_{name}_{identifier}.abc 
5. we will use {catagory}_{name}_{identifier} for reference namespace
6. we need to reference the shader and groom(if it has) to the shot, by use {catagory} and {name} to navigate to the shader asset root V:\SWA\all\asset\{catagory}\Main\{name}\hero , V:\SWA\all\asset\{catagory}\object\{name}\hero, V:\SWA\all\asset\{catagory}\Exterior\{name}\hero Interion is same,  

We have 4 catagory 
directory = namespace prefix
Character = CHAR
Props = PROP
Setdress =SDRS
Sets = SETS

7. file name is {name}_rsshade.ma for shader and {name}_groom.ma namespace is {catagory}_{name}_{identifier}_shade abd {catagory}_{name}_{identifier}_groom
8. before import reference
9. check current scene and ask user to start new scene , replace references with same name but new shot or remove all and import all from the shot select
10. if user select new, create empty group name Camera_Grp, Character_Grp, Setdress_Grp, Props_Grp, Sets_Grp
11. Always Start with Sets, Only cache with prefix "SETS" we will import alembic to the scene and we will get the locator with transform. We need to reference their component to the shot. ex. locator name is SETS_KitBedRoomInt_001:KBDIntCelling_001_Loc, We need to split ":" and look for asset name KBDIntCelling_001 in our asset list and reference {name0}_geo.abc to the shot. then we need to trans form to SETS_KitBedRoomInt_001:KBDIntCelling_001_Loc by get the TRS fromthe locator inmemory and aset locator to origin then parent the asset to the locator then apply the TRS back to locator the reason is we need to keep asset transform at origin. We loop this process until all locator is match with asset in our list. 
12 . We continue with other asset and move them to their group.
13 then we reference the shader and groom to the shot.
14. We will assign shader to the asset by namespace. with the function in igl_shot_build.py
15. We will create blendshape for character by using the function in igl_shot_build.py
16. We will use Place3D Linker to connect the shader to the asset by using the function in igl_shot_build.py for character
17. after finish save new version of the maya file.
 
 Example of the Sets locator
 import maya.cmds as cmds

# get the current selection
```
    Node: SETS_KitBedRoomInt_001:Main_Grp | Type: transform
    Translate: (0.0, 0.0, 0.0)
    Rotate:    (0.0, 0.0, 0.0)
    Scale:     (1.0, 1.0, 1.0)
    Node: SETS_KitBedRoomInt_001:KBDIntCelling_001_Loc | Type: transform
    Translate: (-0.037029266357421875, 68.4910888671875, 3.7310943603515625)
    Rotate:    (0.0, 0.0, 0.0)
    Scale:     (1.0, 1.0, 1.0)
    Node: SETS_KitBedRoomInt_001:KBDIntCelling_001_LocShape | Type: locator
    Node: SETS_KitBedRoomInt_001:KBDIntCloset_001_Loc | Type: transform
    Translate: (46.99803066253662, -0.0021545439958572388, 72.50307273864746)
    Rotate:    (0.0, 0.0, 0.0)
    Scale:     (1.0, 1.0, 1.0)
    Node: SETS_KitBedRoomInt_001:KBDIntCloset_001_LocShape | Type: locator
    Node: SETS_KitBedRoomInt_001:KBDIntFloor_001_Loc | Type: transform
    Translate: (4.5378570556640625, -0.17751915752887726, 4.687477111816406)
    Rotate:    (0.0, 0.0, 0.0)
    Scale:     (1.0, 1.0, 1.0)
    Node: SETS_KitBedRoomInt_001:KBDIntFloor_001_LocShape | Type: locator
    Node: SETS_KitBedRoomInt_001:KBDIntJPDesk_001_Loc | Type: transform
    Translate: (-20.983661651611328, -0.19964027404785156, 68.5810489654541)
    Rotate:    (0.0, 0.0, 0.0)
    Scale:     (1.0, 1.0, 1.0)
    Node: SETS_KitBedRoomInt_001:KBDIntJPDesk_001_LocShape | Type: locator
    Node: SETS_KitBedRoomInt_001:KBDIntWallB_001_Loc | Type: transform
    Translate: (-0.060398101806640625, 0.0, 81.2269172668457)
    Rotate:    (0.0, 0.0, 0.0)
    Scale:     (1.0, 1.0, 1.0)
    Node: SETS_KitBedRoomInt_001:KBDIntWallB_001_LocShape | Type: locator
    Node: SETS_KitBedRoomInt_001:KBDIntWallA_001_Loc | Type: transform
    Translate: (73.25802612304688, -0.162144273519516, 3.9066810607910156)
    Rotate:    (0.0, 0.0, 0.0)
    Scale:     (1.0, 1.0, 1.0)
    Node: SETS_KitBedRoomInt_001:KBDIntWallA_001_LocShape | Type: locator
    Node: SETS_KitBedRoomInt_001:KBDIntWallC_001_Loc | Type: transform
    Translate: (-0.33417510986328125, -0.177254319190979, -70.4105167388916)
    Rotate:    (0.0, 0.0, 0.0)
    Scale:     (1.0, 1.0, 1.0)
    Node: SETS_KitBedRoomInt_001:KBDIntWallC_001_LocShape | Type: locator
    Node: SETS_KitBedRoomInt_001:KBDIntWallD_001_Loc | Type: transform
    Translate: (-66.55768775939941, -0.21856117248535156, 3.7306976318359375)
    Rotate:    (0.0, 0.0, 0.0)
    Scale:     (1.0, 1.0, 1.0)
    Node: SETS_KitBedRoomInt_001:KBDIntWallD_001_LocShape | Type: locator
    Node: SETS_KitBedRoomInt_001:KBDIntDesk_001_Loc | Type: transform
    Translate: (-5.132195472717285, -0.17983996868133545, -70.0441951751709)
    Rotate:    (0.0, 0.0, 0.0)
    Scale:     (1.0, 1.0, 1.0)
    Node: SETS_KitBedRoomInt_001:KBDIntDesk_001_LocShape | Type: locator
    Node: SETS_KitBedRoomInt_001:KBDIntBed_001_Loc | Type: transform
    Translate: (-58.41715621948242, -0.3203543424606323, -41.357327699661255)
    Rotate:    (0.0, 0.0, 0.0)
    Scale:     (1.0, 1.0, 1.0)
    Node: SETS_KitBedRoomInt_001:KBDIntBed_001_LocShape | Type: locator
    Node: SETS_KitBedRoomInt_001:ChickenAlarmClock_001_Loc | Type: transform
    Translate: (-57.31331253051758, -472.057579, -77.18057250976562)
    Rotate:    (0.0, 0.0, 0.0)
    Scale:     (1.0, 1.0, 1.0)
    Node: SETS_KitBedRoomInt_001:ChickenAlarmClock_001_LocShape | Type: locator
```

