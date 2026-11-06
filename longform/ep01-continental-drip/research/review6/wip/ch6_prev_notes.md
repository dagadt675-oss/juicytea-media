# Notes of the previous ch6 fix agent (cut off by a usage limit), in order

I'll start by reading the reported defects and the module code.

---

Now let me read the retention panel files for drop_risks in my range.

---

Let me look at the engine structure and the ch6 code.

---

Now the main ch6.js module.

---

Let me read the ch6 helper files and edit.js.

---

Now the timing markers and segments for ch6.

---

Let me look at the grab tool and render script.

---

Let me check reviewer evidence files and the delivered video path.

---

Let me test the grabber on a frame in my range.

---

The grabber works. Let me verify S10-1 (the gag 10a run) first.

---

Let me check the reviewer's FK analysis script to validate the clip-direction claim.

---

The FK numbers confirm the clip directions (Run_Left's planted foot moves -x, so the clip travels +x, which is screen-right for a camera-facing hero). Let me look at the reviewer's crop of the feet.

---

S10-2 is confirmed: the hero stands in Idle and glides from about 1320 px to about 1080 px over 28098-28134. Frame 28138 also shows the black blink (S10-3). Let me check all three S10-3 transitions.

---

My helper reads exact frames: 28137 is black (luma 0.9). Now S10-4, the filmstrip snap on "shot.".

---

S10-12 is confirmed: a faint vertical white line sits at the left edge in 29486-29487. Next, S10-5 (ridge pop at the s097 to s098 switch).

---

The camera handoff at s097 to s098 also jumps slightly: camA(A1) gives alt about 0.907 and tilt 21.7, while camB starts at alt 0.9 and tilt 22. Now S10-6, the fast spin.

---

S10-6 is confirmed: the code peaks at 38° per frame, and consecutive frames show unrelated faces of the Earth. Next, S10-8 (Aurica glow switching off at the tile handover).

---

S10-8 is confirmed: Australia's gold glow is on through 27627 and off from 27628, the first live frame. Next, S10-9 (the countdown line shifting sideways).

---

The pill fades over about 6 frames (27586-27591), so "disappears in one frame" is not accurate. Let me look at an expand (model 2, around 15:12.6, where a panel says the zoom frame "pops away").

---

I've now checked every reported picture defect on exact frames. Before editing, let me quickly check the S10-7 audio claim (it is outside my module's files, but I should report it accurately).

---

Now the S10-5 edit: continue s097's camera, ridge alpha, cold overlay, drip arcs and look into the start of s098.

---

Now S10-1 and S10-2: swap the strafe clips, match clip speed to root speed, and replace the idle glide with a short foot-planted sidestep.

---

Now S10-3: keep the three outgoing scenes running under the incoming fades.

---

Now S10-8: the Aurica glow uses the time-based alpha for the still as well, so the still matches the first live frame.

---

Now S10-10: ease the filmstrip scroll in, centred on the old start so every frame after the ramp is unchanged.

---

Now the filmstrip (S10-4, S10-11, S10-12). Let me view the current FS block before rewriting it.

---

I need to avoid a few uncovered pixels at the screen edges when the copies are shifted, so I'll give the offscreen layer a horizontal margin and shift the source rectangle instead.

---

Now S10-13: interpolate the sparks along each arm, fade them in after the crack draw-on, and fade them at both ends of an arm so the wrap is invisible.

---

Now the grid card border pop flagged by the retention panels: the full-screen shortcut should only take over once the card actually fills the frame.

---

Let me syntax-check the module before rendering.

---

The module parses. Now the first test render: gag 10a through the splash cross-fade (S10-1, S10-2, the first S10-3 transition), starting a little before the first run.

---

The render exited 0. Let me check for scene errors and look at the runs.

---

The run now heads left. To judge foot planting I need full-resolution crops of the feet over the planted phase (computed as film 934.435-934.677, i.e. test frames 28-35).

---

The first cross-fade is fixed: the gag dissolves into the splash map over 9 frames with luma falling smoothly from 27.4 to 21.3, and no black frame. Next render: the s097 to s098 handover (S10-5).

---

The chunks use the same BT.601 tagging as my test, so they are the right baseline. Let me write a compare helper that reads the original frame from its chunk and diffs it against my test render.

---

The residual sits along the ridge line and the gap outline, which suggests a small geometric shift rather than a brightness pop. Let me crop both frames side by side at full resolution.

---

Re-rendering the switch to confirm the carried-over camera motion.
