# Notes of the previous ch4 fix agent (cut off by a usage limit), in order

I'll start by reading the reported defects and the module code.

---

S6-2 is confirmed: the dot and ring are there in 15668 and gone in 15669. Next, S6-3 (the Graz globe to spin globe hand-off).

---

I'll read the art helpers (`bigQ`, `gauge`, and anything else the shots I'm fixing call) before designing the S6-3 hand-off.

---

The tiles alone can't show velocity kinks, so I'll simulate the `kenburns` crop numerically (same formulas as `photo()` and fx.js) and track a fixed image point's on-screen velocity per frame.

---

The tiles are too small to judge the arrows, so I'll look at full-resolution crops of the key frames.

---

S6-9 is confirmed: all four chevrons jump back toward the ridge between 17219 and 17220. Next, S6-10 (the fingernail panel title).

---

S6-10 is confirmed: the title spans the globe and the panel edge, and the two African arrows end exactly at the panel border. Next, S6-11 (the drip-globe arrows).

---

S6-11 is confirmed: the Cape Horn arrow hangs off the lower-left limb into space, and India's arrow sits on the right limb with only a sliver of red. Next, S6-12 (the rewind card counter).

---

Backups are in place. First, the corridor push ease (S6-1) in ch4_sets.js.

---

Now the seafloor needles (S6-7, S6-8 arrows): floor needles before the page, plus a copy that rides on the page.

---

Next, the chevron loop (S6-9).

---

Now ch4.js. First the S6-1 key times, keeping tGraz (and so the pop and whoosh cues) at its original value.

---

Now the Graz shot: S6-2 (fade the dot with the overlay) and S6-3 (end on the spin shot's camera and look, fade the "?"), plus a hard cut into the spin shot.

---

Now S6-4 (keep the Villumsen keys inside the photo) and S6-6 (white ramp ends at tIce, ice shot starts on its own white).

---

Now the slow push-in during the '33 YEARS TOO LATE' hold (fan panel item).

---

Now the panel title, centred on the visible part of the panel (S6-10).

---

Now the fight-card shake (the aliased `sin(t*160)`) and the rewind card (drop the MYA readout, put the icon in front of the track, shrink the box).

---

All edits are in. I'll review the full diff and syntax-check both modules before rendering.

---

Both modules parse. Before rendering, I'll rerun the crop simulation with the new Villumsen keys to confirm the pan never touches the clamp and has no velocity kinks.

---

The render exited 0 with 150 frames. Test-video frame 0 is film frame 15540, so I'll grab test frames 10-45 (film 15550-15585) to judge the push and the reveal.

---

That crop missed the dot. I'll read the tile to locate it.

---

In the test, the Austria highlight and the Graz dot now fade out together (test frames 108-114). I'll crop that region at full resolution to confirm the dot fades smoothly rather than popping.

---

To judge the pan motion I'll track a patch on Villumsen's face frame to frame (template matching) in both the delivered film and the test render.

---

OpenCV isn't installed, so I'll do the patch matching with a small numpy SSD search instead.

---

That render was killed for lack of memory. I'll check what else is running and how much memory is free before retrying.

---

I'll run it in the background; it notifies me when it exits.

---

The render is running. I'll load the Monitor tool so I can wait on it without polling by hand.

---

I'll block in the foreground until the background render reports its exit line.

---

The render succeeded. I'll start the next one (seafloor flip and arrows, film 17040-17189) in the background while I analyse this clip.
