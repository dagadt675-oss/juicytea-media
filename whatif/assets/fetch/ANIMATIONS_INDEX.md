# ANIMATIONS INDEX (all CC0 / attribution-free)

## Human clip libraries (this folder)

| Pack | Source / License | Format | Rig | Clips |
|---|---|---|---|---|
| quaternius_universal_animation_library | quaternius.itch.io/universal-animation-library, CC0 | GLB (+ _RM root-motion variant) | Quaternius Universal humanoid rig (same as characters/quaternius_universal_base_characters; Mannequin) | 43: A_TPose, Idle_Loop, Idle_Talking_Loop, Idle_Torch_Loop, Walk_Loop, Walk_Formal_Loop, Jog_Fwd_Loop, Sprint_Loop (=panic run), Crouch_Idle_Loop, Crouch_Fwd_Loop, Jump_Start/Jump_Loop/Jump_Land, Roll, Sitting_Enter/Sitting_Idle_Loop/Sitting_Talking_Loop/Sitting_Exit, Swim_Idle_Loop, Swim_Fwd_Loop, Death01, Hit_Chest, Hit_Head, Interact, PickUp_Table, Push_Loop, Driving_Loop, Fixing_Kneeling, Dance_Loop, Punch_Jab/Cross, Pistol_*, Sword_*, Spell_Simple_* |
| quaternius_universal_animation_library_2 | quaternius.itch.io/universal-animation-library-2, CC0 | GLB (+ Female Mannequin) | same Universal rig | 43: ClimbUp_1m, Consume, Farm_Harvest/PlantSeed/Watering, Hit_Knockback, Idle_FoldArms_Loop, Idle_Lantern_Loop, Idle_No_Loop, Idle_Rail_Call/Loop, Idle_TalkingPhone_Loop, LayToIdle, NinjaJump_*, OverhandThrow, Slide_Start/Loop/Exit, TreeChopping_Loop, Walk_Carry_Loop, Yes, Zombie_Idle_Loop/Walk_Fwd_Loop/Scratch, Chest_Open, Melee/Shield/Sword_* |
| cmu_mocap_bvh | CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu) via cgspeed BVH conversion (github.com/una-dinosauria/cmu-mocap). READMEFIRST: "free for use in research and commercial projects"; no attribution required (CMU only asks not to resell the raw data) | BVH, 120 fps | CMU skeleton (Hips, LHipJoint, LeftUpLeg, LeftLeg, ... ~31 joints); units ~inches/scale 0.056; NOT native to Quaternius - retarget in Blender (Rokoko Studio Live addon retarget, or Auto-Rig Pro/Expy) onto the Universal rig | 74 clips (see table below) |
| sketchfab_cc0_fish_swim | Sketchfab CC0 (ffishAsia-and-floraZia): Carp c79dcd2ce7074bac9ce3cb0c11eccb6b, Pale Bleak 83a46c7261ef471194f0a268c5b5aafc, Rice Fish 2505f19d127044b0b304ace799b4cd3b | GLB, skinned | own fish rig | 1 swim loop each ("Animation") |

## Animated models elsewhere in the library (embedded clips)

| Path | Rig | Clips | Retarget to Universal rig? |
|---|---|---|---|
| characters/quaternius_ultimate_modular_men + _women (GLB) | CharacterArmature (older Quaternius rig) | Idle, Idle_Neutral, Walk, Run, Run_Back/Left/Right, Wave, Interact, Roll, Death, HitRecieve, Punch/Kick, Gun/Sword clips (24) | Bone names differ; retarget needed |
| characters/quaternius_animated_men + animated_women (GLB) | HumanArmature | Idle, Standing, Walk, Run, Jump, RunningJump, Sitting, Clapping, Death, Punch, SwordSlash (11) | retarget needed |
| characters/kenney_mini_characters (GLB) | Kenney mini rig | static, idle, walk, sprint, jump, fall, crouch, sit, drive, die, pick-up, emote-yes/no, holding-*, interact-*, wheelchair-* (32) | no (use as-is) |
| characters/kenney_blocky_characters (GLB) | node animation (no skin) | idle, walk, sprint, sit, drive, die, pick-up, emote-yes/no, ... (27) | no |
| characters/kenney_animated_characters_* (FBX) | characterMedium rig | Animations/idle.fbx, run.fbx, jump.fbx | no |
| animals/quaternius_ultimate_animated_animals (GLB) | AnimalArmature per species | DOGS: Husky, Shiba Inu (+ Fox, Wolf): Idle, Idle_2, Idle_2_HeadLow, Walk, Gallop (run), Gallop_Jump, Jump_ToIdle, Eating, Attack, Death, Idle_HitReact_L/R. Hoofed (Horse, White Horse, Deer, Stag, Cow, Bull, Donkey, Alpaca): + Attack_Headbutt/Kick, Idle_Headlow | n/a |
| animals/kenney_cube_pets (GLB) | node animation | CAT, DOG, bunny, penguin, parrot, fox, etc.: static, idle, walk, run, eat, dance, gesture-positive/negative | n/a |
| animals/quaternius_farm_animals_animated (FBX/.blend) | per animal | animated (clips inside FBX/.blend; pack is titled "Farm Animals Animated"): cow, pig, sheep, llama, pug dog, zebra, horse | n/a |
| animals/quaternius_animated_fish (FBX/.blend), animals/quaternius_*fish_bundle* (GLB) | Fish_Armature | GLB bundle: Swimming_Fast, Swimming_Normal(etc.), Attack, Death, Out_Of_Water | n/a |
| vehicles/quaternius_animated_tanks (GLB) | - | Tank_Forward, Tank_Backwards, Tank_TurningLeft, Tank_TurningRight | n/a |

**Gaps:** no CC0 rigged CAT with walk/run/jump/sit was found (Kenney cube-pet cat has idle/walk/run only; BlendKit cats are in the PRIVATE zip, see its catalog). No CC0 flying bird flock with flap cycle among Kenney/Quaternius/Poly Haven/Sketchfab-CC0; see PRIVATE BlendKit zip. "Look up"/"point" exist only as CMU clips (77_05 look around; 14_24..26 direct traffic/wave/point). Mixamo NOT used (Adobe login + own license).

## CMU clips included

| Folder | Trial | CMU description |
|---|---|---|
| idle | 141_20 | Waiting |
| idle | 140_06 | Idle |
| idle | 140_07 | Idle |
| idle | 113_21 | Standing Still |
| idle | 111_28 | Standing still |
| walk | 144_33 | Walking |
| walk | 143_32 | Walk |
| walk | 141_19 | Walk |
| walk | 141_25 | Walk |
| walk | 139_28 | Walking |
| run | 143_01 | Run |
| run | 143_42 | Run |
| run | 141_01 | Run |
| run | 141_02 | Run |
| run | 141_03 | Run |
| panic_run | 142_16 | Scared |
| panic_run | 142_17 | Scared |
| panic_run | 105_32 | ScaredWalk |
| panic_run | 91_32 | ScaredWalk |
| panic_run | 79_73 | scared |
| fall | 105_59 | 360 smallStumble |
| fall | 104_02 | neutral Male walk, exact footfalls |
| fall | 104_03 | Frankenstein male walk, exact footfalls |
| fall | 104_13 | StumbleWalk |
| fall | 91_59 | 360 smallStumble |
| jump | 143_05 | Jumping Distances |
| jump | 143_06 | Jumping Heights |
| jump | 143_07 | Jumping Sideways |
| jump | 143_08 | Jumping Twists |
| jump | 143_09 | Jumping Twists |
| sit | 143_18 | Sit Down And Get Up |
| sit | 143_19 | Sit On Stool And Get Up |
| sit | 141_17 | Sit on Stool |
| sit | 114_05 | Sitting in chair |
| sit | 114_16 | Sit down and stretch |
| wave | 141_16 | Wave Hello |
| wave | 113_27 | Wave |
| wave | 111_37 | Wave |
| wave | 14_24 | direct traffic, wave, point |
| wave | 14_25 | direct traffic, wave, point |
| look_up | 77_05 | look around with flashlight |
| point | 23_21 | conversation - B pounds high stool, points at A (2 subjects - subject B) |
| point | 22_21 | conversation - B pounds high stool, points at A (2 subjects - subject A) |
| point | 14_24 | direct traffic, wave, point |
| point | 14_25 | direct traffic, wave, point |
| point | 14_26 | direct traffic, wave, point |
| crouch | 139_09 | Ducking |
| crouch | 136_09 | Walk Crouched |
| crouch | 136_10 | Walk Crouched |
| crouch | 136_11 | Walk Backwards Crouched |
| crouch | 136_12 | Walk Backwards Crouched |
| swim | 80_72 | swimming |
| swim | 79_02 | swimming |
| swim | 79_03 | swimming |
| climb | 143_37 | Climb Up And Down Ladder |
| climb | 81_14 | climb backwards off ledge |
| climb | 81_15 | climb backwards off ledge |
| climb | 41_07 | climb, step over, jump over, navigate around stepstool |
| climb | 41_08 | climb, step over, jump over, navigate around stepstool |
| dance | 141_12 | Dance, Twist |
| dance | 113_04 | Dance |
| dance | 111_05 | Dance |
| dance | 61_01 | salsa dance |
| dance | 61_02 | salsa dance |
| push | 143_28 | Sweeping, Push Broom |
| push | 134_06 | Push Turn Left |
| push | 134_07 | Push Turn Left |
| push | 134_08 | Push Turn Right |
| push | 134_09 | Push Turn Right |
| carry | 113_26 | Walk and carry |
| carry | 111_36 | Walk and carry |
| carry | 70_01 | carry 5.5lb suitcase |
| carry | 70_02 | carry 5.5lb suitcase |
| carry | 70_03 | carry 19.5lb suitcase |