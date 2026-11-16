# fix ch6 (still running; latest notes)

The module parses. Now the first test render: gag 10a through the splash cross-fade (S10-1, S10-2, the first S10-3 transition), starting a little before the first run.

---

The render exited 0. Let me check for scene errors and look at the runs.

---

The run now heads left. To judge foot planting I need full-resolution crops of the feet over the planted phase (computed as film 934.435-934.677, i.e. test frames 28-35).

---

The first cross-fade is fixed: the gag dissolves into the splash map over 9 frames with luma falling smoothly from 27.4 to 21.3, and no black frame. Next render: the s097 to s098 handover (S10-5).

---

The chunks use the same BT.601 tagging as my test, so they are the right baseline. Let me write a compare helper that reads the original frame from its chunk and diffs it against my test render.

---

The residual sits along the ridge line and the gap outline, which suggests a small geometric shift rather than a brightness pop. Let me crop both frames side by side at full resolution.

---

Re-rendering the switch to confirm the carried-over camera motion.

---

You've hit your 5-hour limit · resets 1:30pm (UTC)
