# voice + audio (still running; latest notes)

Let me find the word-timing file so I can map each masking window and offset to the exact words.

---

I'll write a small helper to list the script words (with segment ids) for any time range, then batch the ASR re-checks so the model loads once.

---

The medium.en model is cached too, which gives an independent second opinion. Let me write a batch ASR runner (loads the model once).

---

While that runs, let me look at the masking windows in the final mix — the per-50ms levels of voice vs SFX/music around each one.

---

The 1-4 kHz band tells the story: the voice stays 15-40 dB above the bed through every flagged word so far. Let me get a compact summary for the rest instead of frame dumps.

---

`impact_deep` is used only 8 times, about once a minute, so the booms don't wear thin. Let me wait for the rest of the batch.

---

The earlier pass ran medium.en on many windows, against both the stem and the final mix. That's useful as a third opinion. Let me read it all.

---

Nothing crossed the flag threshold. Let me see the raw numbers.
