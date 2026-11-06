# find S4 ch2 4:26.19 (still running; latest notes)

The code is clear on scene structure. Let me compute the exact narration-anchored times for this segment by replicating the `tm` calculations.

---

Key match: E12 (frame 9776) lands exactly on `tAusA`, where the hero's position switches source. Let me read the shared helpers (easings, headline, counter, globe).

---

Now let me start grabbing frames. First the hero teleport at E12 (frame 9776, `tAusA`).

---

South America pops in the same way at frame 9687 (a thin crescent on the right limb). Continuing with Europe, Africa and Antarctica.

---

The grabber seeks by PTS. To make sure the master's frame numbering matches render frames, let me compare against the raw chunk file for chunk 21.

---

The master starts at PTS 0, so the offset must come from the grab tool. My guess is that its first output frame is duplicated, which shifts every later label by +1. Let me test that directly.

---

The corrected grabber is aligned (cut at 9602). Now the montage veil: let me measure background brightness before and after `tMont2` and through the `tMont4` decay.

---

The mini's poses are clean: no T-pose, a smooth rise, a held jump pose, then the emote. Now the waffle sort (E6), frames 8636 to 8659.
