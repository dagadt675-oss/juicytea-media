# fix ch3 (still running; latest notes)

Now S5-3 in the tetra rig: one roll over the path, travel-direction facing, and a 0.3 s turn to the camera after the roll.

---

Now S5-6. Let me check `rings()` handles the `asFeat` polygon form before reusing it for the moving overlay.

---

`rings()` handles both forms. Now the S5-6 edit: a readable twitch (fills and coast strokes jolt apart together, with a decaying globe shake), settling back to the original end state.

---

Let me review the full diff and syntax-check the modules.

---

The diff is as intended. Let me check the rest of render.cjs (exit codes and logging) before the first test render.

---

The machine is idle. First test render: the title push (S5-1), frames 10780-10919.

---

Fast render (0.2 s/frame for the 2D page). Let me check for page errors, then measure motion and look at the frames.

---

"FIGURE 1." no longer reads through the pill. Next the tetra shot: arrows (S5-2, S5-5) and the roll (S5-3), frames 11390-11539.
