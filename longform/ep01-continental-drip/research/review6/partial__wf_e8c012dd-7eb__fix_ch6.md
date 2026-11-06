# fix ch6 (still running; latest notes)

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
