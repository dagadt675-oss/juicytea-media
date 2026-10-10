# Map Shorts generator / Térkép Shorts gyártó

Generic, script-driven YouTube Shorts renderer for map facts. One YAML file is one video. The picture, karaoke, sound and QC all come from that file.

The default picture is a flat political map: navy field, muted land, one country in neon red, a single line or a pin with radar rings, and white pills with red type. It is the look of the Canada Short (flat fills, no shaded relief). Mercator and Lambert are still available. A distance-field "relief" is not drawn.

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
  - `route` — `mode: great` (great-circle arc) or `mode: rhumb` (straight on Mercator), `a: [lat, lon]`, `b: [lat, lon]`, optional `label`, `style: solid` or `dashed`
  - `ruler` with `a: [lat, lon]`, `b: [lat, lon]`, `label`
  - `bignum` (`text`, `unit`)
  - `ghost` — true-size overlay (`country`, `anchor_lon`, `anchor_lat`, `label`)
  - `island` — procedural split island when the real feature is smaller than the data (`left`, `right`, `ruler`)

Themes: `midnight`, `dusk`, `emerald`, `ember`, `noir`. Use `ember` or `noir` when the story is dangerous.

The last line should use the same camera and the same claim as the first line. The renderer copies frame 0 onto the last frame so the loop is exact.

### Layout rules (enforced in the drawer)

1080×1920, 30 fps. Captions are 1–3 uppercase words, the spoken word is yellow `(255, 214, 10)`, and the colour changes 0.04 s before the word start (inside ±0.1 s). Glyphs are at least 64 px, centred near 68% of the height. Nothing important sits in the top 12%, the bottom 20%, or past x = 900.

### Sound

A shippable Short does not use espeak. espeak-ng is only the stand-in when no recording exists, so the pipeline can be checked. Do not publish that audio.

Shippable input is one wav and one timing file per line. `engine` is `takes`. No API key is read.

```yaml
voice:
  engine: takes
  takes:
    - {wav: takes/s00.wav, words: takes/s00.json}
    - {wav: takes/s01.wav, words: takes/s01.json}
```

`words` is either `{words: [{text, start, end}]}` or an ElevenLabs alignment file (`characters`, `character_start_times_seconds`, `character_end_times_seconds`). Put the spoken word in `text` if you use the first form. One entry per line, in order. `engine: whisper` aligns a wav with faster-whisper using the line as the prompt, when that package is installed.

`engine: silent` renders no voice and no karaoke. Each line needs `dur` (seconds). The picture stays empty from 64% to 72% of the height so captions can be composited later. `timeline.json` lists each beat's start, end, spoken line, and on-screen claim. See `pipeline/examples/lax_tokyo/`.

The mixer then:

- Level-matches the takes, inserts the gaps from the spec, and uses room tone rather than digital silence.
- Adds a whoosh on each camera move, a pop on a keyword, a tick on a number, a ding on the punchline, and a swell into the loop. All synthesised. No samples.
- Keeps the SFX peak 12 dB under the voice peak.
- Lifts keyword tails about +7 dB on the last 0.3 s.
- Runs two-pass loudnorm to −14 LUFS, true peak ≤ −1.5 dBTP, AAC 320 kbps.

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

Az alap kép lapos politikai térkép: sötétkék háttér, egy ország neonpirossal, egy vonal vagy egy tű radar-gyűrűkkel, fehér kapszula piros felirattal. Nincs domborzat. A Mercator és a Lambert megmarad.

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

Az espeak-ng csak ellenőrzés, nem publikálható hang. Éles anyag: soronként egy wav és egy időzítés (`engine: takes`), ElevenLabs kulcs nélkül. A formátum a fenti angol részben van. `engine: silent` néma kép, karaoke nélkül; a sorok `dur` mezője adja a hosszt, a felirat helye a kép 64–72%-a.

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
