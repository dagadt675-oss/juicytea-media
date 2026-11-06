# finish ch6 (still running; latest notes)

The filmstrip render finished (exit 0). Let me measure it, and the original chunk for comparison.

---

The live hole and push-in look continuous, but I can't read the last zoom frames (29481-29487) at this size. Let me look at a few at full resolution.

---

Original: the sparks hold position for several frames, then hop. I'll write a tracker for spark peaks along the Gulf of Aden arm to compare per-frame motion once the new render lands.

---

The tracker reproduces the reported hops (1150 → 1165 → 1189 every 6 frames). Waiting for the spark render.

---

The Monitor will notify me as each job finishes. Meanwhile, let me compute and record the exact changed scene ranges from the timing so the report is precise.

---

The spark render finished (exit 0). Let me track the sparks and look at the fade-in.

---

The sparks now glide 2-5 px per frame (1154 → 1192 over 13 frames), where the original held and then hopped 15-25 px. Now the fade-in after the crack draw-on.

---

The sed in that chain replaces queue.log, which my `tail -f` monitor would stop following. Let me re-arm the monitor with `tail -F` (follow by name).
