# Notes of the previous ch5b fix agent (cut off by a usage limit), in order

I'll start by reading the defect reports and the module code.

---

Now the retention panel files.

---

Let me look at the module code, the film runtime, and the timing.

---

Confirmed the stock grab tool is one frame late; I'll use the corrected copy. Now verifying each defect on the delivered frames, starting with S8-2 (B1 to B2).

---

S8-2 confirmed (zoom snaps 1.1 to 0.9, arrows vanish). Next, S8-1: the hamster-wheel scene D.

---

S8-1 confirmed: the second flip completes at 21835, the check mark appears at 21838, and the cut comes at 21842. Next I'm checking S8-5 (blob twitch) and S8-3 (card text).

---

S8-5 (twist at 21977 to 21978) and S8-3 (date runs off the card) are both confirmed. Next, S8-6 and S8-7 around the split screen and the reference card.

---

The whoosh peaks about 0.15 s after its cue. If the cue stays at 726.54, it lands mid-flip in the earlier run 2, so I'll keep that cue time. Next, verifying S9-1 (the dip at the Cape Agulhas cut).

---

S9-1 confirmed (frame 24931 is near black at luma 4.4, then ramps up over 3 frames). Next, S9-2 (N1 to N2) and the S9-4/S9-5 timing.

---

The shared Baja border is 10 identical edges along 28N, so the cross line can be dropped by stroking only the non-shared edges. Next, I'm measuring the K camera motion for S9-6.

---

S9-6 confirmed: motion rises to about 2.2, drops to about 0.1 at 23937-23944, then climbs again for the dive. Now the Florida cross-section (S9-7 and the bedrock wipe the casual panel flagged).

---

R2 confirmed in the frames: a hard-edged red rectangle sweeps left to right across the black void under the platform (24530-24552). Let me see it at full resolution.

---

The bedrock wipe is a real visual defect: a hard rectangle sweeps across the void and reads as a render error. Now R1, the "empty navy screen" at the start of scene I that all four panels flagged.

---

R1 confirmed: about 1.1 s of near-empty navy (23276-23308) with only a faint scan line before the grid pops in. Next, S8-4 (needles overshooting the bottom-row tiles).

---

I've verified every reported item. Before editing, I'm backing up the original module so I can diff and revert.

---

Now the edits. First S8-2: fade B1's tip arrows out, then ease B2's framing in from where B1 ends.

---

Next S8-1: anchor run 2 on the word "first" and keep its whoosh cue at the same absolute time as in the delivered mix.

---

Now S8-5 (ramp the extra wobble in) and S8-3 (fit the card text to the card).

---

Now S8-6 (retract the divider as the bracket draws) and S8-7 (card already entering on the cut frame).

---

Now S8-9 (keep the drip highlight inside the bulb) and S8-8 (land the honey drop on the puddle exactly when it reacts and the existing pop cue plays).

---

Now I'll move the scan line to draw after the tiles, so it sits on top of the ghosts.

---

Now scene K: S9-6 (one continuous camera move) and S9-3 (hide the real peninsula while the red copy is away, and stroke only the outer outline).

---

Now L2: S9-7 (gentler rise ease) and R2 (soft top-down bedrock reveal instead of the hard left-to-right wipe).

---

Now S9-1: a real crossfade from the Cape globe into the ASTER plate.

---

Now N1/N2/N3: S9-2 (fade the stamp and coin, then tilt the camera instead of the jump cut), S9-4 (scar lines draw across "tore apart around Antarctica") and S9-5 (cut to N3 on "The small ones").

---

Let me review the full diff before rendering.

---

The machine is heavily loaded (load around 25, 11 other renders running), so it's about 3.6 s per frame. I'll keep test renders short. Checking the B1 to B2 result.

---

While the batch runs, I'll load the Monitor tool so I can wait for each render to finish.

---

The E render finished. Checking S8-5 (the blob outline around 21977 to 21978) and S8-3 (the card text at rest).

---

The jump at 21977 to 21978 dropped from 6.61 to 4.04 but hasn't gone. Something else starts at that instant. Let me look at the frames.

---

S8-3 is fixed: both lines now sit inside the card with a right margin matching the clock's left margin. Let me check batch progress.

---

The F/G1 render is done. Checking the divider (S8-6) and the card's first frames (S8-7).

---

S8-4 is fixed: at 23468 all four bottom-row needles end inside their tiles, and they stay inside after the relayout. Let me look closer at York's swing to judge the length growth.
