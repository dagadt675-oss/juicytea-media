# fix ch4 (still running; latest notes)

I'll start by reading the reported defects and the module code.

---

S6-2 is confirmed: the dot and ring are there in 15668 and gone in 15669. Next, S6-3 (the Graz globe to spin globe hand-off).

---

I'll read the art helpers (`bigQ`, `gauge`, and anything else the shots I'm fixing call) before designing the S6-3 hand-off.

---

The tiles alone can't show velocity kinks, so I'll simulate the `kenburns` crop numerically (same formulas as `photo()` and fx.js) and track a fixed image point's on-screen velocity per frame.

---

The tiles are too small to judge the arrows, so I'll look at full-resolution crops of the key frames.

---

S6-9 is confirmed: all four chevrons jump back toward the ridge between 17219 and 17220. Next, S6-10 (the fingernail panel title).
