# Notes of the previous ch2 fix agent (cut off by a usage limit), in order

I'll start by reading the reported defects and the module code.

---

Confirmed: the shared grab.py labels are off by one in multi-frame runs; I'll use my passthrough copy (g.py) for exact frames. Now verifying S3-1/S3-2 at the G→H cut.

---

S3-1/S3-2 confirmed (title pops off and the globe jumps/brightens at 7103). Now checking S3-3 (drag camera).

---

S3-4 confirmed (roll abandoned mid-air at 58%, head-first entry, boot-only frames 7547-7552, then an upright snap). Next S3-5 (whip-head band) and S3-7 (South Pole readout).

---

S3-5 confirmed (navy band at 5722 slicing the pill before the panel moves). Now S3-7.

---

S3-7 confirmed ('1.8 MI' white-on-white; '0.0 MI' beside a ruler already ~0.4 mi long). Next S3-6 and S3-8.

---

S3-6 confirmed (cyan US pops in at 7882 at full opacity in the corner). Now S3-8.

---

S3-8 confirmed (overlay visible only 6895-6945, then a near-static plain globe through "not more land"). Now the segment-4 defects, starting with S4-11 and S4-10.

---

S4-11 confirmed (China turns grey in one frame at 8007). Now S4-10.

---

S4-10 confirmed (white outline appears at 8201 and flies off before Argentina's fill arrives at 8212-8214). Now the waffle card: S4-8 holes and the panel-reported pop-ins around 4:48.

---

The grid entrance is a clean eased outBack pop (8548-8556), so no defect there. Now grabbing the segment-4 globe/tile/montage moments in one batch.

---

S4-4 confirmed in the grid (opaque black cards behind every globe). Next the Pacific shot frames.

---

S4-3 confirmed (grey veil from 9881; drains over 9967-9969) and S4-4 confirmed on the montage water globe (black tilted square, soft). Next the drip headline, tetra corner and the seam.

---

S4-7 (headline already formed at 10037), S4-6 (corner glow pops on at 10297) and the 10350 seam (opaque to x-ray look in one frame) all confirmed. Now the JUICE CHECK stamp.

---

Now S3-3 (drag easing and a camera that follows the eased drag progress instead of a hard clamp).

---

Now scene G (S3-8 overlay hold, S3-2 camera end, S3-1 headline moved to an overlay scene).

---

Now scene H's first camera key and dim (S3-2).

---

Now S3-4 (let the roll complete above the water).

---

Now the flat map: S3-6 (US fade-in), S4-11 (China copy fade-in), S4-10 (Argentina lights before its outline flips).

---

Now S4-8 (waffle: unlit cells always drawn, lit squares slide over them).

---

Now S4-4 (tiles masked to the globe disc; the montage water globe rendered at 900 px instead of being upscaled from 420).

---

Now S4-9 (Pacific lights up on the cut/word "Pacific").

---

Now S4-2/S4-1. First a `facing` helper on the ch2 projector (ch2_lib.js), then the drop loop and the hero hand-off.

---

Now S4-3 (montage flash counts only cuts already passed).

---

Now S4-6 (soft limb occlusion for the tetra corner glows).

---

Now S4-5/S4-12. First the juiceStamp options in ch2_lib.js (opt-out of the restart fade, optional plate colour; defaults unchanged for the other caller).

---

Now the stamp flight/landing in ch2.js.

---

All edits are in. Syntax check of the modified module files before rendering:

---

Checking whether any other module imports ch2_lib.js (my lib edits are additive with unchanged defaults, but I want to be sure).

---

Only ch2.js uses ch2_lib.js, and the existing FALSE stamp call keeps its defaults. Starting test renders, first the G→H cut (S3-1/S3-2): frames 7085-7184.

---

Rendered in 61 s, exit 0. Checking the log for scene errors and viewing the cut (video index 0 = film frame 7085).

---

Headline now holds through "If you dig straight down" and fades out at 7151-7163 before China lights up; the globe move is continuous. S3-1/S3-2 fixed. Next S3-8 (overlay hold), frames 6875-7024:

---

The overlay now holds from 6895 through "not more land" and fades out at about 6985-6992. Checking numerically that the hand-over to the headline dim has no bright dip:

---

Smooth: luma eases down as the overlay fades and the headline then fades in, with no dip. S3-8 fixed. Next S3-3, the forward drag (6220-6339):

---

The drag now starts, travels and lands smoothly with the camera following. Confirming the speed profile numerically (frame-difference ramp) against the raw chunk:

---

The return is smooth too: gradual start at 6408, peak around 6434, eased stop by 6468 (8 frames of rest before the designed hard cut at 6476). S3-3 fixed. Next S3-4, the roll (7510-7579):

---

The hero is small in a full frame, so I'll add a crop option to my grabber and look at a close-up of the pop-out.

---

The roll now completes (inverted around 7530-7538, upright by 7542) instead of being abandoned mid-air. I need a wider crop to confirm the head stays above the waterline while inverted.

---

No band before the whip any more (5719-5726 show the full Arctic panel and intact pill); the South panel's sky now enters only with the scroll. S3-5 fixed. Now the South Pole readout (S3-7):

---

The US now fades in at the corner over about 10 frames as the zoom-out reveals it. Numeric check on the top-left region (new versus raw chunk 17, which covers 7650-8099):

---

The one-frame jump at 7882 (diff 8.33) is now a gradual ramp merging into the zoom-out. S3-6 fixed. Now the China copy (S4-11):

---

The copy now fades in over 8007-8012 and then peels off, instead of snapping China grey in one frame. Numeric check on a box over China:

---

That box missed China (the map is moving, and both versions show the same drift). Let me look at a full-resolution crop around China instead.

---

Original snaps orange→grey between 8006 and 8007; the new version eases over 8007-8010 before the copy slides off. S4-11 fixed. Next S4-10 (Argentina), frames 8180-8239:

---

Order is now cause-then-effect: Argentina lights orange at 8198-8204, the outline leaves from about 8207 and lands on China around 8226. S4-10 fixed. Next the waffle sort (S4-8), frames 8625-8714:

---

After the sort every vacated cell keeps its unlit square, so no more moth-eaten grids. S4-8 fixed. Next the cap-tile grid (S4-4), frames 9215-9264:

---

The black cards are gone; the globes now sit as round discs on the navy grid. I notice a thin dark arc on the upper edge of the bottom-middle globe, so I'm zooming in to check whether that's new.

---

The Pacific now begins lighting up right after the 9602 cut and is mostly lit by "Pacific" (about 9614). S4-9 fixed. Now the continent arrivals at the rim, North America first (around 9668):

---

Europe also comes over the top limb gradually (translucent at 9703, firmer at 9704). Next Asia and the hero hand-off (S4-1), frames 9745-9809:

---

The globe is already filled orange by the pour here, so the orange count can't isolate Asia. Visual check instead:

---

No visible jump of the Explorer around 9776, and Asia now slides in from the upper-left limb translucent-first (9774-9776) instead of blinking on. Close-up of the hero across the old jump frame:

---

The montage water globe is now a crisp round globe on the navy grid, with no square. Quick look at the south disc and the antipode map, which previously sat under the veil:

---

South disc on clean navy, the antipode map crisp rather than milky, and the round water globe. S4-3/S4-4 fixed. Next S4-7 (drip headline at the 10037 cut), frames 10025-10074:

---

The x-ray onset is a smooth 20-frame ramp (31.9 → 37.1, max diff 0.75), so the look change is now an intended dissolve rather than a seam. Now the corner glow (S4-6):

---

Re-rendering the corner moment (10280-10319) to verify:

---

Those frames show the x-ray edges inside the globe brightening steadily (0.85·xr); the 10309 step is my 170-threshold metric tipping over, not a visual pop. Now the emergence itself:
