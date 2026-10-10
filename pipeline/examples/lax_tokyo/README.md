# Why LA→Tokyo curves toward Alaska

Silent picture fitted to the US read. The renderer does not call espeak or ElevenLabs.

Sentence starts are 0.03, 3.93, 7.24, 8.14, 10.81, 14.28, 20.25, 23.05. The picture is 24.2 s.

```bash
python3 pipeline/make_short.py pipeline/specs/lax_tokyo.yaml --preset final --out pipeline/out/lax_tokyo
```

Outputs:

- `silent.mp4` — 1080×1920, 30 fps, H.264, no audio, no burned-in karaoke
- `timeline.json` — eight beats with `start`, `end`, `say`, and `on_screen`
- `qc.txt` — resolution, the 24.2 s clock, and a check that y 0.64–0.72 has no text pixels

The miles pill springs in at 4.72 s, so it is up when the read says "three hundred miles" (about 4.9 s). The solid path bends from 18.55 s to 19.45 s, centered on "bends north" (about 19 s). Frame 0 already shows the curved arc and the pill `YOUR MAP IS LYING`. The last encoded frame is a byte copy of frame 0.

The spoken lines say the flight curves toward Alaska, and that the shortest path is a great circle that bends north. They do not say the flight flies over Alaska or that it flies exactly the great circle.
