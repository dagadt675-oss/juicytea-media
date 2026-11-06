# fix ch3 (still running; latest notes)

For S5-4 I want to fade page 237 out, but `drawPage` overwrites `globalAlpha` (it sets 0.9 for the shadow, then 1). Let me check who else uses `drawPage` before making it respect the incoming alpha.

---

`drawPage` is only used in ch3.js, always with an incoming alpha of 1, so making it multiply rather than overwrite is safe.

---

Now the kids page: the normalized slide and the "1918" pill fading in as the page lands rather than before it appears.

---

Now S5-9: pins ride on their cards (scale with the pop-in, turn with the falling card), and the red X turns with the falling card. At-rest positions stay exactly as before.

---

Now S5-5: hide each arrow's reset by fading it at the ends of its push cycle.

---

Now S5-3 in the tetra rig: one roll over the path, travel-direction facing, and a 0.3 s turn to the camera after the roll.

---

Now S5-6. Let me check `rings()` handles the `asFeat` polygon form before reusing it for the moving overlay.

---

`rings()` handles both forms. Now the S5-6 edit: a readable twitch (fills and coast strokes jolt apart together, with a decaying globe shake), settling back to the original end state.
