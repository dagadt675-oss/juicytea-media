# fix ch4 (still running; latest notes)

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
