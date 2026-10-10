# Map Shorts generator / Térkép Shorts gyártó

Generic, script-driven YouTube Shorts renderer for map facts. One YAML file is one video. The picture, karaoke, sound and QC all come from that file.

The old one-off Alaska renderer only drew an orthographic globe with flat fills. This one flies between an orthographic globe, Mercator and Lambert equal-area, shades relief, and refuses to finish when QC fails.

The seven old topics (Hans Island, London, France, Diomede, Ceuta/Melilla, Congo) are not specs here. `specs/alaska.yaml` is only a renderer test. Later videos should be more dramatic: danger, scandal, stories that are hard to believe. Copy the Alaska file and change the lines.

---

## English

### What a spec contains

Each line is one sentence:

- `text` — spoken line. Capitalise the one word that should hit harder (`EAST`).
- `say` — optional, only when the spoken form differs (`E U` so a voice spells it, while `text` shows `EU`).
- `kind` — `q` question, `h` hook statement, `s` statement, `p` punchline (exactly one).
- `gap` — pause after the line, in seconds. Ordinary pauses 0.20–0.45, never two equal in a row, and 0.55–0.60 before the punchline. Standard deviation must be at least 0.10 s.
- `claim` / `sub` — the big card. Wrap with `\n`. `*stars*` mark the yellow word.
- `camera` — `proj` (`ortho`, `merc`, `laea`), `lon`, `lat`, `span` (degrees across the view).
- `visuals` — any of:
  - `highlight` with `countries: [USA]` or `sovereignties: ["France"]`
  - `marker` (`lat`, `lon`, `label`)
  - `latline` / `lonline`
  - `ruler` with `a: [lat, lon]`, `b: [lat, lon]`, `label`
  - `bignum` (`text`, `unit`)
  - `ghost` — true-size overlay (`country`, `anchor_lon`, `anchor_lat`, `label`)
  - `island` — procedural split island when the real feature is smaller than the data (`left`, `right`, `ruler`)

Themes: `midnight`, `dusk`, `emerald`, `ember`, `noir`. Use `ember` or `noir` when the story is dangerous.

The last line should use the same camera and the same claim as the first line. The renderer copies frame 0 onto the last frame so the loop is exact.

### Layout rules (enforced in the drawer)

1080×1920, 30 fps. Captions are 1–3 uppercase words, the spoken word is yellow `(255, 214, 10)`, and the colour changes 0.04 s before the word start (inside ±0.1 s). Glyphs are at least 64 px, centred near 68% of the height. Nothing important sits in the top 12%, the bottom 20%, or past x = 900.

### Sound

Input is a voice wav plus word times, or the built-in espeak-ng placeholder.

- Per-line takes, level-matched, with the gaps from the spec and a little room tone (not digital silence).
- Whoosh on each camera move, pop on a keyword, tick on a number, ding on the punchline, swell into the loop. All synthesised. No samples.
- SFX peak is kept 12 dB under the voice peak.
- Keyword tails get about +7 dB on the last 0.3 s.
- Two-pass loudnorm to −14 LUFS, true peak ≤ −1.5 dBTP, AAC 320 kbps.

Drop real reads in later without code changes:

```yaml
voice:
  engine: espeak
  takes:
    - {wav: takes/s00.wav, words: takes/s00.json}
```

`words` is either `{words: [{text, start, end}]}` or ElevenLabs character alignment (`characters`, `character_start_times_seconds`, `character_end_times_seconds`). `engine: whisper` aligns a wav with faster-whisper using the line as the prompt, when that package is installed.

### Commands

From the repo root:

```bash
python3 -m pip install --break-system-packages -r pipeline/requirements.txt
# espeak-ng and ffmpeg must already be on the machine
python3 pipeline/setup_data.py
python3 pipeline/selftest.py
python3 pipeline/make_short.py pipeline/specs/alaska.yaml --preset preview --out pipeline/out/alaska
```

`--preset final` is 1080×1920, crf 17. `--preset preview` is 540×960, which is the file to keep under 15 MB. Hero stills are always 1080×1920 PNGs unless you pass `--no-hero`.

QC writes `qc.txt`. Exit code 0 means pass. Exit code 2 means fail; `final.mp4` is still on disk so you can see why. `review_packet.md` is the reviewer bundle (script, measurements, file list).

The opening-motion check warns under 0.03 (that bar comes from high-detail footage) and fails only when the first second is effectively still, under 0.008. A shaded globe cannot hit 0.03 without flashing the whole frame.

### Output folder

```
pipeline/out/alaska/
  final.mp4  silent.mp4  contact.jpg  qc.txt  review_packet.md
  stills/t00.00.png …   timeline.json  mix_report.json  description.txt
```

---

## Magyar

Egy YAML = egy Short. A kép, a karaoke, a hang és az ellenőrzés mind abból készül.

A régi Alaska-render csak egy gömböt rajzolt, lapos színekkel. Ez gömb és lapos térkép között is repül (Mercator és egyenlő területű vetület), domborzatot árnyal, és ha az ellenőrzés bukik, nem enged tovább.

A régi hét téma (Hans-sziget, London, Franciaország, Diomede, Ceuta, Kongó) nincs benne. Az `specs/alaska.yaml` csak teszt. A következő témák legyenek erősebbek: veszély, botrány, hihetetlen történet. Másoláshoz az Alaska fájl a minta.

### Mit ír a YAML

- `text` — a mondat. A hangsúlyos szó NAGYBETŰS (`EAST`).
- `say` — csak ha másképp kell kimondani, mint ahogy kiírjuk.
- `kind` — `q` kérdés, `h` állító horog, `s` sima mondat, `p` csattanó (pontosan egy).
- `gap` — szünet a mondat után, másodperc. A sima szünet 0,20–0,45, két egyforma nem jöhet egymás után, a csattanó előtt 0,55–0,60. A szórás legalább 0,10 s.
- `claim` — a nagy felirat. Sortörés: `\n`. A `*csillag*` sárga.
- `camera` — `ortho` (gömb), `merc` vagy `laea`, plusz `lon`, `lat`, `span`.
- `visuals` — kiemelés, jelölő, szélességi vagy hosszúsági vonal, vonalzó, nagy szám, valódi méretű árnyék (`ghost`), rajzolt sziget.

Témák: `midnight`, `dusk`, `emerald`, `ember`, `noir`. Veszélyes történethez `ember` vagy `noir`.

Az utolsó mondat kamerája és nagy felirata egyezzen az elsővel. Az utolsó képkocka az első másolata, így a loop zárul.

### Felirat

1–3 szó, NAGYBETŰ. A kimondott szó sárga, és 0,04 másodperccel a szó kezdete előtt vált (a ±0,1 s-on belül). Legalább 64 px, a kép magasságának kb. 68%-ánál. A felső 12%, az alsó 20%, és az x = 900-on túli rész üres marad. Ezt a rajzoló kényszeríti minden szövegre.

### Hang

A teszt hang espeak-ng. Később egy wav és egy időzítés-JSON elég, ElevenLabs kulcs nélkül.

A hangeffek kódból vannak (suhintás, kattanás, tikkelés, csengés). A csúcsuk legalább 12 dB-lel a hang alatt marad. A nagybetűs szó vége kb. +7 dB. A hangerő két menetben −14 LUFS, a csúcs ≤ −1,5 dBTP, AAC 320 kbps.

### Parancsok

A repo gyökeréből:

```bash
python3 -m pip install --break-system-packages -r pipeline/requirements.txt
python3 pipeline/setup_data.py
python3 pipeline/selftest.py
python3 pipeline/make_short.py pipeline/specs/alaska.yaml --preset preview --out pipeline/out/alaska
```

A `--preset final` 1080×1920. A `--preset preview` 540×960, ez fér 15 MB alá. A nagy PNG kockák akkor is 1080×1920-asak, ha a videó előnézet. `--no-hero` kikapcsolja őket.

Ha a QC rendben van, a program 0-val lép ki. Ha bukik, 2-vel, és a `qc.txt` megmondja, melyik pont bukott. A `review_packet.md` a bírálónak készül. A nyitó mozgás 0,03 alatt figyelmeztetés (ez a határ részletgazdag felvételre való), és csak 0,008 alatt bukik, ha az első másodperc gyakorlatilag áll.
