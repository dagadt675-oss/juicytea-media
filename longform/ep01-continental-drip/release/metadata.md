# Myth Juice, long-form #1: feltöltési csomag

Minden szöveg angolul van, mert a videó angol. A blokkok egy az egyben bemásolhatók a YouTube Studióba.
Feltölteni csak te töltesz fel. Én semmit nem publikáltam, és nem mentem fel sehova.

| Fájl | Mire való |
|---|---|
| `video_final.mp4` | A teljes minőségű mester: 1920×1080, 30 fps, 15:34, AAC 320k, -14 LUFS |
| `myth_juice_ep01_upload.mp4` | Ugyanez 500 MB alatt (2 menetes kódolás, ~4 Mbps): ezt küldtem át, ez tölthető fel |
| `thumb_B_pointing_at_what.jpg` | Thumbnail B, 1280×720: **ez legyen az alapértelmezett** |
| `thumb_A_cant_unsee_it.jpg` | Thumbnail A, 1280×720 |
| `thumb_S_theyre_scars.jpg` | Thumbnail S, 1280×720 |
| `captions_en.srt` | Angol felirat, külön feltöltendő (Feliratok → Fájl feltöltése → Időzítéssel). Nincs beégetve. |

A három thumbnailen ugyanaz a kép, csak a szöveg más, így a Test & Compare tisztán azt méri, melyik szöveg működik jobban.

---

## Title

```
Why the Continents Point South (Not Just a Coincidence)
```

Alternatives for a later title test. Run it only after the thumbnail test ends, and keep thumbnail B:

```
Why Earth Looks Like It's Dripping South
A 400-Year-Old Clue in the Shape of the Continents
```

Don't pair thumbnail B with a title that also says "pointing", because the two would repeat each other.

## Description

```
Why do the continents point south? Spin a globe and South America, Africa and India all taper to a point at the bottom, as if the Earth were melting. Four hundred years ago, Francis Bacon wrote that the matching capes of Africa and South America were no accident. Then came a man who thought the Earth was slowly turning into a pyramid, and Alfred Wegener, whose idea of continental drift the experts laughed at.

Here's what the drips are really pointing at, and where they're dripping next.

0:00 Why do the continents point south?
2:15 What's on Earth's other side?
3:13 Can you dig to China?
5:06 Is Earth secretly a pyramid?
7:10 Why did geologists laugh at Wegener?
9:13 Where are the drips pointing?
10:43 Was the answer hidden in a joke?
11:46 What doesn't drip?
13:10 Where is the drip going next?

Plus the four competing models for the next supercontinent, from Pangaea Proxima to Amasia.

Myth Juice takes one thing you were taught about the world and checks it against the real planet. Subscribe so you don't miss the next one.

Africa, Antarctica, Asia or Australia: which neighbor are you betting on? One word in the comments.

Made with real satellite imagery and real data:
- Earth imagery: NASA Blue Marble and Black Marble (NASA Earth Observatory, NASA GIBS); Apollo 17 "Blue Marble" photograph (NASA); ASTER image of Cape Agulhas (NASA/METI/AIST/Japan Space Systems, and U.S./Japan ASTER Science Team)
- Maps: Natural Earth
- Elevation: Terrain Tiles (Mapzen, AWS Open Data), from SRTM, GMTED2010, ETOPO1 and other sources
- Past positions of the continents: GPlates Web Service, EarthByte Group; plate model by Müller et al. (2019), CC BY 4.0, simplified
- 3D characters: Quaternius and Kenney (CC0)
- Historical images (public domain): Francis Bacon, Novum Organum (1620), and his portrait by Paul van Somer (1617); Arnold Guyot (1849); William Lowthian Green, Vestiges of the Molten Globe (1875); J. W. Gregory, The Plan of the Earth and Its Causes (1899); Abraham Ortelius, Typus Orbis Terrarum (1570); Alexander von Humboldt by Joseph Karl Stieler. Scans via Internet Archive, Wellcome Collection and Wikimedia Commons.
- Photographs of Alfred Wegener and the 1930 Greenland expedition: Archive of the Alfred Wegener Institute (via Wikimedia Commons)
```

## Tags

```
why do continents point south, why do all the continents point south, continents point south, continental drip, why does earth look drippy, continental drift, Alfred Wegener, plate tectonics, Gondwana, Pangaea, Pangea, next supercontinent, future supercontinent, Pangaea Proxima, Novopangaea, Amasia, Aurica, can you dig to China, Antarctica, geography facts, Myth Juice
```

## Pinned comment

```
In a couple hundred million years, America crashes into a new neighbor. Africa, Antarctica, Asia or Australia: which one are you betting on? One word.
```

## Settings

- **Category:** Education.
- **Language:** English.
- **Captions:** upload `captions_en.srt`.
- **Chapters:** they come from the description automatically.
- **Test & Compare:** run B, A and S together with the title fixed, and upload B as the default image. All three are checked at phone size.
- **End screen:**
  - The video ends on "What happens if Africa splits in two? That's our next story", over a moving map with a "WATCH NEXT" frame drawn on the right.
  - Put a Video element over that frame from 15:17 to the end, and a Subscribe element from 15:20 to the end (17 s in all, within YouTube's 20 s limit).
  - Until there is a video about Africa splitting, set the element to "Best for viewer". Don't link the "Split in Two" Short, because it is about country borders, not Africa.
  - Once episode #2 (Africa splitting) is out, swap it in. End screens can be edited after publishing.
- **"Altered or synthetic content" checkbox:** your call. Check YouTube's current guide ("Disclosing use of altered or synthetic content") before you decide. The parts of this video it may concern are the synthetic narration voice and the generated background music. The footage is maps, renders and archival images, not realistic people or events.
- **Before upload:** run the search check again (`tools/ytsearch.py`, "why do continents point south"). The query had no long-form competition on 2026-11-05, but there are popular Shorts on the topic.
