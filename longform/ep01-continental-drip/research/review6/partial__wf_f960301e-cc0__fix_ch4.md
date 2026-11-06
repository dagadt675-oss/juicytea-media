# fix ch4 (still running; latest notes)

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
