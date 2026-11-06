# fix ch3 (still running; latest notes)

Let me check how `globeShot` and the globe overlay work before deciding on the S5-6 fix.

---

The globe has a `refreshOverlay()` hook and `globeShot` has a `pre` callback, so animating the overlay is possible. Let me check the rumble cue's sound to size the twitch to it.

---

Let me look at the other two arrow shots (s053/s054 at 442-444 s and s055 at 456-460 s) that S5-5 covers.

---

The arrows in the later tetra shots stay clear of the Explorer, so S5-2 only needs the first shot's ring rotated. I've verified every reported defect. Let me back up the module files before editing.

---

Now let me make the edits. First S5-1 (the title push as one move).

---

Now S5-8: let `topPill` pass a background through, and use a near-opaque one for the two pills over printed paper.

---

Now S5-10: a normalized out-expo curve in the module's own helper file (the shared `fx.js` stays untouched).

---

Now S5-2 (rotate the first shot's arrow ring so no arrow lands on the Explorer at the top) plus the matching out-expo swap in that scene.
