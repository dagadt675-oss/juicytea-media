# fix ch4 (still running; latest notes)

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

---

You've hit your 5-hour limit · resets 1:30pm (UTC)
