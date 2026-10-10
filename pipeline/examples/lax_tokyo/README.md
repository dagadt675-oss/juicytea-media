# Why LA→Tokyo curves toward Alaska

Silent picture for a later ElevenLabs read. The renderer does not call espeak or ElevenLabs.

```bash
python3 pipeline/make_short.py pipeline/specs/lax_tokyo.yaml --preset final --out pipeline/out/lax_tokyo
```

Outputs:

- `silent.mp4` — 1080×1920, 30 fps, H.264, no audio, no burned-in karaoke
- `timeline.json` — eight beats with `start`, `end`, `say`, and `on_screen` (`claim`, `sub`)
- `qc.txt` — resolution, duration, and a check that y 0.64–0.72 has no text pixels

The spoken lines in `say` are the script, in order. Fit the voice to those start and end times. Keep karaoke inside y 0.64–0.72 of the height; that band is empty navy on purpose.

On-screen copy says “hundreds of kilometers” only. It does not say the flight passes over Alaska. The great-circle arc bends north toward the Aleutians. The last beat returns to the opening camera with that arc, so a loop can cut back to the question.
