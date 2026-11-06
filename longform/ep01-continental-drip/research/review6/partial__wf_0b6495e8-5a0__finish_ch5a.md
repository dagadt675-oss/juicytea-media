# finish ch5a (still running; latest notes)

Let me quantify that jump with a frame-diff image (master, 19032→19033).

---

The diff is dominated by the designed crack shake. Let me find the reviewer's source note for frame 19033.

---

Two panels flagged 19033; the strategist note says it is the 6-frame crack shake (alternating per-frame jitter). Let me check how `lookOffset` is applied in the globe to size a smoother shake.

---

Let me check the machine load and whether other renders are running before I queue test renders.

---

The machine is shared (load ~10 on 4 cores), so I need to keep renders lean. Let me check render.cjs options.

---

Let me quickly verify the Stage API used by the house-gag edits (project/camera/lookFrom).

---

While those render, let me look at the master's paper figure (scene N) after the lock, to judge Madagascar consistency there.

---

Let me quantify how far the smoothed tip paths (PATHS) deviate from the raw tip tracks, to decide how to lay trails behind the moving tips during the drift.
