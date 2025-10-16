# User Journey Examples - Sequence-Based Lighting Workflow

## User Persona Definitions

### **Senior Lighting Artist (Sarah)**
- 8+ years experience
- Responsible for establishing master setups
- Works on hero sequences and key shots
- Needs efficiency and consistency across shots

### **Mid-Level Lighting Artist (Mike)**
- 3-5 years experience  
- Adapts master setups for specific shots
- Handles key shots and technical challenges
- Balances creativity with technical constraints

### **Junior Lighting Artist (Jenny)**
- 1-2 years experience
- Primarily works on child shots
- Follows established workflows
- Needs clear guidance and minimal complexity

---

## Journey 1: Senior Artist - Master Shot Creation

### **Scenario**: Sarah sets up the master lighting for "Forest Chase" sequence (60 shots)

#### **Context**
- New sequence with outdoor forest environment
- Mixed lighting: dappled sunlight, rim lighting, atmospheric haze
- 60 shots total: wide establishing shots, medium action, close-ups
- Timeline: 2 days for master setup

#### **User Journey**

##### **Day 1 Morning: Scene Analysis & Planning**

**Step 1: Project Initialization**
```
Sarah opens Maya and loads the sequence geometry
- Opens: forest_chase_master.ma
- Reviews: Shot breakdown document
- Identifies: 3 main lighting scenarios needed
```

**Sarah's Actions:**
- Launches the Lighting Manager tool
- Creates new project: "FOREST_CHASE_SEQ001"
- Sets up master namespace: "SEQ001_MASTER"
- Reviews provided geometry and camera blocking

**System Response:**
- Tool creates base project structure
- Establishes naming conventions
- Sets up master collections framework
- Displays project dashboard

**Sarah's Thoughts:**
> "I need to identify the core lighting that works for most shots. The forest has three main areas - dense canopy, clearings, and the stream. I'll design for the clearing since that covers 70% of shots."

##### **Day 1 Afternoon: Core Lighting Setup**

**Step 2: Master Key Lighting**
```
Sarah establishes the primary lighting rig
- Sun light: Directional for primary illumination
- Sky dome: HDRI for ambient/reflections  
- Atmosphere: Volume lights for god rays
```

**Sarah's Actions:**
1. **Creates Sun Light**
   ```
   Tool > Create Light > Directional
   Name: SEQ001_MASTER_SUN_primary_001
   Position: High angle simulating 2PM forest light
   Color: Warm 3200K
   Intensity: 2.5
   ```

2. **Sets up Sky Dome**
   ```
   Tool > Create Light > Dome  
   Name: SEQ001_MASTER_SKY_fill_001
   HDRI: forest_overcast_4k.exr
   Intensity: 0.8
   Rotation: Aligned with sun direction
   ```

3. **Adds Atmospheric Volume**
   ```
   Tool > Create Light > Volume
   Name: SEQ001_MASTER_ATMOS_godrays_001
   Shape: Cylinder aligned with sun
   Scatter: 0.1 for subtle haze
   ```

**System Response:**
- Automatically applies naming conventions
- Groups lights into "MASTER_KEY_LIGHTS"
- Updates light manager interface
- Shows real-time preview

**Sarah's Thoughts:**
> "This gives me good base illumination. The god rays add atmosphere without being distracting. I need some fill lights to lift the shadows in dense areas."

**Step 3: Fill Lighting System**
```
Sarah adds fill and accent lights
- Bounce cards: Simulated fill from forest floor
- Rim lights: Edge definition for characters
- Accent lights: Practical motivations
```

**Sarah's Actions:**
1. **Forest Floor Bounce**
   ```
   Tool > Create Light > Area
   Name: SEQ001_MASTER_FILL_forest_001  
   Size: Large area light below canopy
   Color: Green-tinted warm (forest bounce)
   Intensity: 0.4
   ```

2. **Character Rim Light**
   ```
   Tool > Create Light > Area
   Name: SEQ001_MASTER_RIM_edge_001
   Position: Camera-relative rim position
   Color: Cool blue (sky reflection)
   Intensity: 1.2
   ```

**System Response:**
- Groups fills into "MASTER_FILL_LIGHTS"
- Updates collection organization
- Validates naming consistency
- Shows lighting overview

##### **Day 2 Morning: Render Setup & Collections**

**Step 4: Render Layer Organization**
```
Sarah sets up render layers and collections
- BG Layer: Environment, distant trees, sky
- CHAR Layer: Characters, hero props
- ATMOS Layer: Volumes, particles, atmosphere
```

**Sarah's Actions:**
1. **Creates BG Layer**
   ```
   Render Setup > Create Layer > BG
   Collections: 
   - Add: forest_environment_*
   - Add: trees_background_*  
   - Add: terrain_*
   AOVs: beauty, diffuse, specular, reflection, environment
   ```

2. **Creates CHAR Layer**
   ```
   Render Setup > Create Layer > CHAR
   Collections:
   - Add: character_*
   - Add: props_hero_*
   - Add: clothing_*
   AOVs: beauty, diffuse, specular, subsurface, normal, motion_vector
   ```

3. **Creates ATMOS Layer**
   ```
   Render Setup > Create Layer > ATMOS
   Collections:
   - Add: volume_*
   - Add: particles_*
   - Add: atmosphere_*
   AOVs: beauty, volume, emission, opacity
   ```

**System Response:**
- Creates render layers without overrides
- Populates collections based on naming patterns
- Sets up AOV structure
- Validates layer completeness

**Sarah's Thoughts:**
> "The automatic collection population is working well. I just need to verify the AOVs are correct for each layer and do some test renders."

##### **Day 2 Afternoon: Testing & Documentation**

**Step 5: Validation & Testing**
```
Sarah tests the master setup across different scenarios
- Test renders from multiple camera angles
- Verify lighting works for character heights
- Check atmosphere levels
```

**Sarah's Actions:**
1. **Renders Test Shots**
   - Wide establishing shot: forest_001
   - Medium character shot: forest_015  
   - Close-up detail: forest_045
   - Each rendered with all layers

2. **Reviews and Adjusts**
   ```
   Adjustments made:
   - Sun intensity: 2.5 → 2.2 (slightly softer)
   - Rim light position: Moved 15° for better edge
   - Forest fill: Added second area light for balance
   ```

3. **Documents Setup**
   ```
   Tool > Generate Documentation
   - Light positions and settings
   - Render layer configurations  
   - Collection membership rules
   - Known limitations and notes
   ```

**System Response:**
- Saves final master configuration
- Generates setup documentation
- Creates template for key shot inheritance
- Marks master as "APPROVED"

**Sarah's Thoughts:**
> "Master setup is solid. It handles wide shots and medium shots well. Close-ups might need some hero lighting additions, but that's for the key shot phase."

---

## Journey 2: Mid-Level Artist - Key Shot Adaptation

### **Scenario**: Mike adapts the master setup for a dramatic close-up sequence

#### **Context**
- Shot 045: Hero character close-up during emotional forest scene
- Requires enhanced facial lighting and mood adjustment
- Inherits from Sarah's master setup
- Timeline: 4 hours for key shot setup

#### **User Journey**

##### **Morning: Setup Inheritance**

**Step 1: Project Inheritance**
```
Mike inherits Sarah's master setup for Shot 045
- Loads master configuration
- Creates key shot workspace  
- Maintains all master elements
```

**Mike's Actions:**
1. **Opens Key Shot Tool**
   ```
   Tool > Create Key Shot
   Source: SEQ001_MASTER
   Shot ID: SHOT_045
   Type: Hero Close-up
   ```

2. **Inherits Master Setup**
   ```
   System automatically:
   - Copies all master lights to SHOT045_OVERRIDE namespace
   - Inherits all render layers and collections
   - Maintains parent-child relationships
   - Creates shot-specific workspace
   ```

**System Response:**
- Creates SHOT045_OVERRIDE namespace
- Establishes inheritance links to master
- Copies collections with extension capability
- Shows inheritance status panel

**Mike's Thoughts:**
> "Good, I have all of Sarah's lighting as my base. Now I need to add some specific lighting for this close-up without breaking the master setup."

##### **Mid-Morning: Hero Lighting Additions**

**Step 2: Face-Specific Lighting**
```
Mike adds hero lighting for close-up emotional scene
- Key light: Closer, softer key for face
- Fill light: Gentle fill for shadow detail
- Eye light: Catchlight for eyes
```

**Mike's Actions:**
1. **Adds Hero Key Light**
   ```
   Tool > Add Shot Light > Area
   Name: SHOT045_FACE_key_hero_001
   Parent Group: SHOT045_HERO_LIGHTS
   Inherits Properties From: SEQ001_MASTER_SUN_primary_001
   
   Adjustments:
   - Position: Closer to character face
   - Size: Larger for softer shadows
   - Intensity: 1.8 (vs master 2.2)
   - Temperature: Slightly warmer
   ```

2. **Adds Facial Fill**
   ```
   Tool > Add Shot Light > Area
   Name: SHOT045_FACE_fill_soft_001
   Parent Group: SHOT045_HERO_LIGHTS
   
   Setup:
   - Position: Camera left for shadow fill
   - Size: Large soft area
   - Intensity: 0.6
   - Color: Neutral warm
   ```

3. **Adds Eye Catchlight**
   ```
   Tool > Add Shot Light > Spot
   Name: SHOT045_EYE_catch_spec_001
   Parent Group: SHOT045_HERO_LIGHTS
   
   Setup:
   - Position: High angle for natural catchlight
   - Cone: Narrow, focused on eyes
   - Intensity: 0.8
   - Color: Cool white
   ```

**System Response:**
- Groups new lights in SHOT045_HERO_LIGHTS
- Maintains inheritance relationships
- Updates shot documentation
- Shows lighting preview

**Mike's Thoughts:**
> "The face lighting is looking good. I should check how this interacts with the master atmosphere and make sure I'm not over-lighting."

##### **Afternoon: Render Layer Extensions**

**Step 3: Collection and AOV Extensions**
```
Mike extends render collections for close-up needs
- Adds high-detail face geometry
- Includes eye detail models
- Extends AOV list for compositing
```

**Mike's Actions:**
1. **Extends CHAR Collection**
   ```
   Tool > Extend Collection > CHAR
   Additional Items:
   - character_face_closeup_geo
   - character_eyes_detail_geo
   - character_skin_subsurface_geo
   ```

2. **Adds Shot-Specific AOVs**
   ```
   Tool > Extend AOVs > CHAR Layer
   Additional AOVs:
   - face_id (for compositing isolation)
   - eye_reflection (for eye enhancement)
   - skin_subsurface (for skin work)
   ```

3. **Tests Integration**
   ```
   Tool > Test Render
   - Renders with master + shot additions
   - Verifies all collections work
   - Checks AOV generation
   ```

**System Response:**
- Extends collections without modifying master
- Adds AOVs to shot-specific render layers
- Validates no conflicts with master setup
- Generates test renders

**Mike's Thoughts:**
> "Perfect, I'm getting the detail I need for the close-up while keeping all of Sarah's master lighting intact. The compositors will have good control with these extra AOVs."

##### **End of Day: Final Validation**

**Step 4: Documentation and Handoff**
```
Mike finalizes the key shot setup
- Documents changes made
- Validates inheritance integrity
- Prepares for child shot distribution
```

**Mike's Actions:**
1. **Final Render Test**
   ```
   Renders final beauty pass with all layers
   Compares with master setup consistency
   Verifies lighting continuity
   ```

2. **Documents Key Shot**
   ```
   Tool > Generate Shot Documentation
   - Lists all additions made
   - Notes intended use cases
   - Identifies child shots that should inherit this setup
   ```

3. **Marks Shot Ready**
   ```
   Tool > Mark Key Shot Complete
   Status: APPROVED for child shot inheritance
   Child Shots: 046-049 (related close-ups)
   ```

**System Response:**
- Saves key shot configuration
- Updates inheritance tree
- Makes setup available for child shot distribution
- Generates handoff documentation

---

## Journey 3: Junior Artist - Child Shot Assignment

### **Scenario**: Jenny applies key shot setup to child shots 046-049

#### **Context**
- Shots 046-049: Continuation of close-up sequence
- Should inherit Mike's Shot 045 setup
- Minor adjustments only for camera differences
- Timeline: 2 hours for all 4 shots

#### **User Journey**

##### **Morning: Batch Inheritance**

**Step 1: Child Shot Assignment**
```
Jenny receives shots 046-049 to complete
- Uses Mike's Shot 045 as template
- Applies to all 4 shots automatically
- Makes minimal manual adjustments
```

**Jenny's Actions:**
1. **Opens Child Shot Manager**
   ```
   Tool > Child Shot Manager
   Available Templates:
   - SEQ001_MASTER (base template)
   - SHOT_045 (hero close-up template) ✓ Selected
   ```

2. **Selects Target Shots**
   ```
   Target Shots: 046, 047, 048, 049
   Inheritance Source: SHOT_045 (includes master)
   Assignment Type: Batch automatic
   ```

3. **Applies Batch Inheritance**
   ```
   Tool > Apply Inheritance
   System processes:
   - Creates namespaces: SHOT046_MICRO, SHOT047_MICRO, etc.
   - Copies all lights from master + key shot
   - Inherits all collections and render setup
   - Maintains inheritance relationships
   ```

**System Response:**
- Creates 4 new shot configurations simultaneously
- Copies master + Shot 045 elements to each
- Establishes inheritance chains
- Reports success status for each shot

**Jenny's Thoughts:**
> "Great! All four shots are set up with Mike's hero lighting. Now I just need to check each one and make small adjustments for the different camera angles."

##### **Mid-Morning: Shot-Specific Adjustments**

**Step 2: Shot 046 - Camera Right Close-up**
```
Jenny adjusts lighting for camera angle differences
- Slight rim light adjustment for new angle
- Minor key light intensity change
```

**Jenny's Actions:**
1. **Reviews Shot 046**
   ```
   Tool > Open Shot > SHOT_046
   Camera Angle: 30° camera right from Shot 045
   Issues Identified: Rim light needs repositioning
   ```

2. **Makes Micro-Adjustment**
   ```
   Tool > Micro Adjust > SHOT045_RIM_edge_001
   Adjustment Type: Position offset
   Change: Rotate Y +30° to match camera angle
   Intensity: Keep inherited value
   ```

**System Response:**
- Creates micro-adjustment override
- Maintains inheritance link to parent
- Documents change for tracking
- Updates shot preview

**Step 3: Shot 047 - Slightly Wider Frame**
```
Jenny adjusts for wider framing
- Reduces hero key intensity slightly
- Maintains all other lighting
```

**Jenny's Actions:**
1. **Reviews Shot 047**
   ```
   Camera Angle: Pulled back 2 feet from Shot 045
   Issues: Hero key too intense for wider frame
   ```

2. **Adjusts Hero Key**
   ```
   Tool > Micro Adjust > SHOT045_FACE_key_hero_001
   Adjustment Type: Intensity multiplier
   Change: 0.85x (reduce to 85% of inherited value)
   ```

**Step 4: Shots 048-049 - Timing Adjustments**
```
Jenny makes animation timing-based adjustments
- Particle timing for Shot 048
- Motion blur settings for Shot 049
```

**Jenny's Actions:**
1. **Shot 048 - Particle Timing**
   ```
   Tool > Micro Adjust > Animation Timing
   Target: ATMOS layer particles
   Change: Offset +12 frames for animation sync
   ```

2. **Shot 049 - Motion Blur**
   ```
   Tool > Micro Adjust > Render Settings
   Target: Motion blur samples
   Change: Increase to 8 samples (character movement)
   ```

##### **Afternoon: Batch Validation**

**Step 5: Quality Control & Batch Testing**
```
Jenny validates all 4 shots together
- Batch render tests
- Consistency checking
- Final approval
```

**Jenny's Actions:**
1. **Batch Test Renders**
   ```
   Tool > Batch Operations > Test Render
   Shots: 046, 047, 048, 049
   Layers: All (BG, CHAR, ATMOS)
   Resolution: Quarter-res for speed
   ```

2. **Reviews Consistency**
   ```
   Tool > Consistency Checker
   Compares all 4 shots for:
   - Lighting continuity
   - Color consistency  
   - Inheritance integrity
   ```

3. **Final Approval**
   ```
   Tool > Mark Shots Complete
   Status: All shots approved
   Notes: Minor adjustments documented
   Ready: For final lighting review
   ```

**System Response:**
- Generates batch test renders
- Reports consistency metrics
- Documents all micro-adjustments made
- Updates shot status to completed

**Jenny's Thoughts:**
> "All four shots look consistent with the key shot while handling their specific camera needs. The micro-adjustment system worked perfectly - I didn't break any inheritance and the changes are all documented."

---

## Journey 4: Production Scenario - Sequence Review & Updates

### **Scenario**: Director requests changes that propagate through the sequence

#### **Context**
- Director wants warmer lighting across entire sequence
- Sarah (Senior Artist) makes master changes
- System automatically updates all related shots
- Timeline: 1 hour for propagation + validation

#### **User Journey**

##### **Change Request Processing**

**Step 1: Master Update by Sarah**
```
Sarah receives director feedback: "Make the forest lighting warmer and more romantic"
- Adjusts master sun temperature
- Modifies atmosphere color
- Updates master documentation
```

**Sarah's Actions:**
1. **Opens Master Setup**
   ```
   Tool > Master Shot Manager > SEQ001_MASTER
   Change Request: Warmer, more romantic lighting
   ```

2. **Adjusts Sun Light**
   ```
   Light: SEQ001_MASTER_SUN_primary_001
   Temperature: 3200K → 2800K (warmer)
   Intensity: 2.2 → 2.4 (slightly brighter)
   ```

3. **Modifies Atmosphere**
   ```
   Light: SEQ001_MASTER_ATMOS_godrays_001
   Color: Neutral → Warm amber
   Scatter: 0.1 → 0.12 (more visible)
   ```

**System Response:**
- Updates master configuration
- Identifies all dependent shots
- Calculates propagation impact
- Shows update preview

##### **Automatic Propagation**

**Step 2: System Propagates Changes**
```
System automatically updates all shots that inherit from master
- Updates key shots (045, 050, 090)
- Updates child shots (046-049, 051-059, etc.)
- Maintains all shot-specific additions
```

**System Actions:**
1. **Identifies Inheritance Tree**
   ```
   Master Changes Affect:
   - Direct children: 40 shots inherit directly from master
   - Key shot children: 20 shots inherit from key shots
   - Total impact: 60 shots need updates
   ```

2. **Batch Update Process**
   ```
   For each affected shot:
   - Updates inherited light properties
   - Maintains shot-specific overrides
   - Preserves micro-adjustments
   - Validates no conflicts
   ```

3. **Reports Update Status**
   ```
   Update Results:
   - Successfully updated: 58 shots
   - Conflicts detected: 2 shots (require manual review)
   - Validation errors: 0 shots
   ```

##### **Validation and Review**

**Step 3: Team Reviews Updates**
```
Mike and Jenny review their affected shots
- Mike checks key shots for consistency
- Jenny validates child shots maintained their adjustments
- Team coordinates any manual fixes needed
```

**Mike's Review (Key Shots):**
1. **Checks Shot 045**
   ```
   Tool > Review Changes > SHOT_045
   Master Changes Applied:
   ✓ Sun temperature: Updated to 2800K
   ✓ Atmosphere color: Updated to warm amber
   ✓ Hero lighting: Maintained shot-specific additions
   ✓ Collections: Unchanged
   Result: No issues, maintains shot intent
   ```

**Jenny's Review (Child Shots):**
1. **Batch Reviews 046-049**
   ```
   Tool > Batch Review > SHOT_046_to_049
   All micro-adjustments preserved:
   ✓ Shot 046: Rim light position offset maintained
   ✓ Shot 047: Hero key intensity reduction maintained  
   ✓ Shot 048: Particle timing offset maintained
   ✓ Shot 049: Motion blur settings maintained
   Result: All shots updated successfully
   ```

**Final Result:**
- 58 shots updated automatically in 15 minutes
- 2 shots flagged for manual review (had custom sun modifications)
- All artist-specific work preserved
- Sequence maintains consistency with new director feedback

---

## Key User Benefits Demonstrated

### **For Senior Artists (Sarah)**
- **Efficiency**: Master setup once, applies to 60 shots
- **Control**: Maintains authority over sequence look
- **Flexibility**: Can update master and propagate changes
- **Quality**: Consistent base across all shots

### **For Mid-Level Artists (Mike)**
- **Creative Freedom**: Can enhance shots without breaking master
- **Non-Destructive**: Additions don't interfere with base setup
- **Inheritance**: Gets all master improvements automatically
- **Documentation**: Changes tracked and documented

### **For Junior Artists (Jenny)**
- **Guided Workflow**: Clear inheritance from approved setups
- **Minimal Complexity**: Only micro-adjustments needed
- **Safety**: Can't accidentally break master or key setups
- **Learning**: Sees how complex lighting is structured

### **For Production (Team)**
- **Consistency**: Automatic sequence-wide consistency
- **Speed**: Batch operations and inheritance reduce manual work
- **Flexibility**: Director changes propagate automatically
- **Quality Control**: Validation catches issues early

This user journey framework gives Claude Code clear examples of how real artists would interact with the system in production scenarios, helping ensure the implementation meets actual workflow needs.