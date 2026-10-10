# Why LA→Tokyo curves toward Alaska

Silent picture for a later ElevenLabs read. The renderer does not call espeak or ElevenLabs.

The six scenes are built. Their durations in the spec are placeholders. Wait for `words.json` before the timed render, then fit each beat to the new read.

```bash
python3 pipeline/make_short.py pipeline/specs/lax_tokyo.yaml --preset final --out pipeline/out/lax_tokyo
```

Outputs, once that render is run:

- `silent.mp4` — 1080×1920, 30 fps, H.264, no audio, no burned-in karaoke
- `timeline.json` — six beats with `start`, `end`, `say`, and `on_screen` (`claim`, `sub`)
- `qc.txt` — resolution, duration, and a check that y 0.64–0.72 has no text pixels

Beat order:

1. Curved arc already drawing, top pill `YOUR MAP IS LYING`.
2. Big pill `≈300 MI SHORTER`, with `480 KM` under it.
3. The same lie, still on the flat map.
4. Dashed rhumb: the straight line on a Mercator map.
5. The dashed rhumb stays, and the solid path bends north off it. A globe could not keep both cities on screen and still show that bend, so the reveal is the arc.
6. Cut back to the opening map so the loop can return to frame 0.

The spoken lines say the flight curves toward Alaska and that the shortest path is a great circle. They do not say the flight flies over Alaska or that it flies exactly the great circle. The last encoded frame is a byte copy of frame 0.
