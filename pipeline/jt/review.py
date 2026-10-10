"""One folder a reviewer can read without opening the timeline by hand."""

from __future__ import annotations

import json
from pathlib import Path


def write_packet(spec, out: Path, qc: dict, mix_report: dict) -> Path:
    lines = []
    for i, ln in enumerate(spec.lines):
        gap = f"  gap {ln.gap:.2f}s" if i < len(spec.lines) - 1 else ""
        lines.append(f"{i}. [{ln.kind}] {ln.text}{gap}")
        lines.append(f"   claim: {ln.claim.replace(chr(10), ' / ')}")
        vis = ", ".join(v.get("type", "?") for v in ln.visuals) or "—"
        cam = ln.camera
        lines.append(f"   camera: {cam.proj} lon {cam.lon:.1f} lat {cam.lat:.1f} span {cam.span:.0f}°  visuals: {vis}")
    checks = "\n".join(f"- {c['status']} {c['name']}: {c['detail']}" for c in qc.get("checks", []))
    body = f"""# Review packet — {spec.title}

Theme `{spec.theme}`. This packet is the test render of the generic map generator.
The old seven-topic slate (Hans, London, France, Diomede, Ceuta, Congo) is not in production.

## Script

{chr(10).join(lines)}

## What changed in the picture

- Script-driven beats, not a hardcoded camera.
- Orthographic globe plus Mercator and Lambert equal-area, with a whip when the projection changes.
- Flat political map: neon country, one line or a pin, white pills. No relief.
- Claim slam, karaoke (spoken word yellow), markers, rulers, big numbers, true-size ghost, split-island card.
- Every glyph is clamped inside the safe zone by the drawer.

## QC

{checks}

## Mix

```json
{json.dumps({k: v for k, v in mix_report.items() if k != 'events'}, indent=2)}
```

## Sources

{chr(10).join('- ' + s for s in spec.sources) or '- (none in the spec)'}

## Files

- `final.mp4` — the rendered short
- `contact.jpg` — 12 frames
- `stills/` — 1080×1920 PNG heroes
- `qc.txt` / `qc.json`
- `timeline.json` — word starts
- `description.txt`
"""
    path = out / "review_packet.md"
    path.write_text(body)
    (out / "description.txt").write_text(spec.description if spec.description.strip() else spec.title + "\n")
    return path
