# fix ch5a (still running; latest notes)

Syntax is fine. Note: edit.js filters with `ch.id !== only && ch.id !== 'ch' + only`, so `"only":5` would skip `ch5a` entirely; I'll use `"only":"5a"`. First a short smoke render in the zipper scene.

---

The module loads and the slider now travels. Frame 28 shows the slider turned sideways, so let me inspect consecutive frames there at full resolution.

---

Now let me test the zipper from just before the slider appears (G scene).

---

While that renders, let me review the full diff against the original.

---

While the zipper render runs, let me prepare a slider-tracking check (yellow-pixel centroid per frame).

---

While the renders run, let me look at the first finished zipper frames as soon as they exist. Meanwhile, here is a tiling helper for test videos.

---

Madagascar's 180-Ma polygon sits in the channel between Africa and India, which is the correct Gondwana position, so un-excluding it is right. Waiting for the render monitor now.

---

My render completed fine (the OOM kill hit another agent's Chromium). Let me analyze the zipper render: slider track and tiles.
