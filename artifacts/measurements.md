# Football Earth v5

Silent picture. Voice and karaoke are added downstream.

```
RESULT PASS  fails=0
silent 1080x1920  18.40s  hook 0.0535  loop 0.39

PASS  geometry          1080x1920 @ 30.000 fps, 552 frames, 18.40s
PASS  codec             h264 yuv420p bt709/bt709/bt709
PASS  silent            0 audio streams
PASS  hook_motion       mean abs diff/255 in 0–1 s = 0.0535 (bar 0.03)
PASS  loop              last vs first mean abs 0.39/255
PASS  frozen            none over 0.5 s
PASS  caption_band      y 1229:1382 bright pixels none
PASS  sat_hold          0.84s from sat to spring-back
PASS  length            18.40s

Weaknesses (honest):
- Santa and the sitter are shaded ellipsoids. They read as a figure and a cabin, not a sculpt.
- The ocean slide is a latitude flow on the real water mask, not a fluid simulation.
- The last frame is an exact copy of frame 0, so the loop seam holds one frame.
- No numerals are burned in. 'Forty-three kilometers' is the oblate shape plus the dashed limb; the bot speaks the number.
- Word times follow the mapped v4 read. A new ElevenLabs take will need a nudge if its pace differs.
```

Timeline: `artifacts/short15_timeline.json`

Caption plate: y 1229–1382 (0.64–0.72).
