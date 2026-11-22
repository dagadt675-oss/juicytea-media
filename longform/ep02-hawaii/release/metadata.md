# Myth Juice, long-form #2 (Hawaiʻi): feltöltési csomag

A videó angol, ezért minden bemásolandó szöveg angol. A kódblokkok egy az egyben mehetnek a YouTube Studióba.
Feltölteni csak te töltesz fel. Én semmit nem töltöttem fel, nem publikáltam és nem ütemeztem.
A lépésről lépésre útmutató: `feltoltes_hu.md`.

| Fájl | Mire való |
|---|---|
| `thumb_A_no_ocean.jpg` | A thumbnail (NO OCEAN), 1280×720, 213 KB. **Ez az alapértelmezett**, és az A/B tesztben is ez legyen az első. A film 1. képkockája ugyanez a kép (maszkolt SSIM 0,955). A színei a tesztelt változat szintjén vannak, nem élénkebbek a filmnél. |
| `thumb_B_one_island.jpg` | B thumbnail (ONE ISLAND), 1280×720, 167 KB. Az A/B tesztben ez a második. A film 0:18-0:20 között fizeti ki („They become one island”, a felirat 0:19-től). A képen ugyanaz a vékony fehér körvonal fut az egybeolvadt sziget partján, mint a filmben ott. |
| `thumb_C_walk_to_maui.jpg` | C thumbnail (WALK TO MAUI), 1280×720, 196 KB. **Tartalék, ne töltsd fel.** Nem kerül a tesztbe (lásd a Nyitott kérdések 1. pontját). |
| videófájl | Külön adom át, nem kerül gitbe. |
| felirat (`captions_en.srt`) | **Még nincs.** Amíg nincs, a YouTube automatikus angol felirata megy. |

Mindhárom kép a film saját motorjának renderje, stock vagy generált kép nélkül. Az A és a C a mai filmből renderelt tiszta képkocka (2560×1440, felirat nélkül). A B a 3. csomagolási kör 1920×1080-as motorrendere (ugyanazon a tengerszinten, mint a film egybeolvadt szigete), nagyobb felirattal és a film fehér partvonalával. A felirat Barlow Condensed 800. Forrásmegjelölés a képeken nincs, az a leírásba kerül.

---

## Title

```
Why Can't You See Most of Hawaii? (Look Down)
```

Rangsor (a bemásolandó cím az 1.):

1. **Why Can't You See Most of Hawaii? (Look Down)** (45 karakter). Marad.
   - A legerősebb címforma: „Why Can't You See / Visit / Reach X?” plusz utasító zárójel (1,56× a saját csatornás medián, vak teszt 9/10).
   - A zárójelet a film kétszer fizeti ki: 0:29-nél („Keep draining. And look down.”) és 12:04-nél („So next time you see one, look down.”).
   - Egyik thumbnaillel sincs közös tartalmi szava (NO OCEAN, ONE ISLAND, WALK TO MAUI), így nem ismétlik egymást.
   - Nincs benne klón-szó (drain, hidden, bottom, nobody), Everest vagy szám.
2. **Hawaii Used to Be Bigger. Where Did It Go?** (42). Vak teszt 7/10. A ONE ISLAND és a WALK TO MAUI képhez illik.
   - A film 0:42-0:48 között kimondja mindkét okot: a jégkorszak után emelkedett a tenger, és a Big Island most is süllyed.
3. **What's Holding Hawaii Up? (It's Slowly Sinking)** (47). Vak teszt 7/10, de a NO OCEAN képpel csak 2/10, mert a képen nem látszik süllyedés.
   - Csak süllyedést mutató képpel használd.

Szabályok:
- Egyszerre csak egy dolgot változtass.
- Címet és thumbnailt soha ne cserélj ugyanazon a napon.
- **Amíg a thumbnail-teszt fut, a címhez nem nyúlunk**, mert a címcsere leállítja a tesztet. Ez erősebb, mint az elakadási szabály.
- Elakadási szabály, csak a teszt lezárulta után (Winner, Performed same vagy Inconclusive; legfeljebb 2 hét):
  - ha az utolsó 72 óra kb. 3 ezernél kevesebb megjelenítést hozott, cseréld a címet a 2. címre;
  - ez az egyetlen változtatás, utána várj újabb 72 órát.
- 72 óránál a teszt általában még fut (néhány nap, legfeljebb 2 hét), ezért a régi „72 óra után cserélj” szabály addig nem érvényes.

## Description

```
Most of Hawaii is out of sight. The Big Island is only the top of a mountain that keeps going down for miles under the sea.
So we take the water away step by step, walk between islands that were one in the last Ice Age, and keep going down to where these mountains really start.

0:00 Only the Top
1:34 Oʻahu’s Missing Side
3:02 The Island Stands Up
5:16 Watch It Grow Old
7:16 Fought Over a Volcano
9:59 We Haven’t Hit Bottom

Also in this film: the night a beach at Halapē dropped into the sea, the side of Oʻahu that slid away, the Hōlei Sea Arch, the old volcano the Battle of Midway was fought over, and Kamaʻehuakanaloa, the volcano growing off the coast right now.

Myth Juice checks one thing you think you know about a place against the real planet. Subscribe for the next one.

Made with real elevation data, satellite imagery and public-domain photos:
- Elevation and sea floor: NOAA NCEI (ETOPO 2022 and coastal topo-bathy DEMs), USGS 3D Elevation Program (3DEP), Terrain Tiles (Mapzen/Tilezen: SRTM, GMTED2010, ETOPO1, USGS 3DEP; AWS Open Data)
- Imagery: USDA NAIP (via NOAA Digital Coast and USGS The National Map), NASA HLS, MODIS and Blue Marble (NASA GIBS), NASA Black Marble (night lights), VIIRS cloud imagery from NOAA-20 and Suomi NPP (NASA GIBS), USGS Landsat; contains modified Copernicus Sentinel data 2022-2025
- Geology and roads: USGS Open-File Report 2007-1089, Geologic Map of the State of Hawaiʻi (Sherrod et al., 2007); USGS The National Map transportation data (U.S. Census Bureau TIGER)
- Photos: USGS (Pohoiki black sand beach); USGS Volcano Hazards Program (submerged coconut grove at Halapē, 1975); NPS Photo/Janice Wei (Hōlei Sea Arch, 2022); NPS Photo/J. Wei (Hōlei Sea Arch after the collapse, 2026); U.S. Navy photo 80-G-21627, Naval History and Heritage Command (USS Yorktown, 1942); USDA NAIP 2023 (Lake Peigneur)
- Paper cut-outs from public-domain photos: Library of Congress, FSA/OWI Collection (Russell Lee, 1939; Fort Benning, 1942); U.S. Fish and Wildlife Service (Hawaiian monk seals; Laysan albatrosses, Midway Atoll National Wildlife Refuge); Library of Congress, Frank and Frances Carpenter Collection ("Climbing Mt. McKinley")

#Hawaii #Geography #Volcanoes
```

Megjegyzések:
- A fejezetidők a vágott film fejezetkártyáinak kezdetei, **felfelé** kerekítve, hogy a fejezetre ugrás a már látható kártyára essen, ne az előző fejezet végére (motor timing, 746,93 s = 12:26).
  - Kártyakezdetek: 93,81 / 181,65 / 315,55 / 435,89 / 598,99 s; a kártya 1,62 s-ig látszik. A kerekített idők 0,01-0,45 s-mal a kártya kezdete után esnek.
  - A legszűkebb a 6. fejezet: 9:59 csak 0,01 s-mal van a kártya kezdete után. Ha a végleges masteren a kártya akár egy képkockával később indul, 10:00 kell.
- A fejezetcímek betűre egyeznek a kártyákkal, az ʻokina (U+02BB) és a ’ (U+2019) is.
- A leírás „these mountains”-t ír, nem Mauna Keát és Mauna Loát: a film csak a Mauna Loát méri a valódi aljától, a Mauna Keát a tengerfenéktől.
- A leírásban nincs szám, Everest vagy „taller than” (P3: elhasznált horog). A csattanót (a valódi alaptól mért magasság) nem lövi le.
- A forrásokat a motor `img/SOURCES.md`, `img/ch1/4/5/6/LICENSE.md` és `data/SOURCES.md` fájljaiból vettem át. A 2026-os Hōlei-fotó jóváírása nyitott kérdés (lásd lent).

## Tags

```
why can't you see most of hawaii, hawaii without water, hawaii drained, what is under hawaii, big island hawaii, mauna kea, mauna loa, maui nui, hawaii ice age, is hawaii sinking, kilauea, midway atoll, hawaiian islands geography, underwater volcano, Myth Juice
```

15 tag, 261 karakter (a YouTube 500-at enged). Szándékosan kimaradt: Everest, „tallest mountain”, 56,000 (P3).

## Pinned comment

```
Have you stood at the Pali Lookout or driven up Mauna Kea? Did you know what was under your feet?
```

## Settings

- **Category:** Education. **Language:** English. **Audience:** No, it's not made for kids.
- **Captions:** a `captions_en.srt` még nincs kész (az `engine/tools/make_srt.py` elkészíti). Ha megvan, töltsd fel (Feliratok → Fájl feltöltése → Időzítéssel). Addig az automatikus felirat megy.
- **Chapters:** a leírásból automatikusan jönnek.
- **A/B teszt (régi nevén Test & Compare): 2 kar, A és B.**
  - Típus: csak thumbnail, a cím fix.
  - Sorrend: **először az A, utána a B.** Az A az első, mert eldöntetlen eredménynél az elsőként feltöltött kép marad.
  - A C **nem kerül a tesztbe**. Tartalék, és csak akkor jöhet harmadik karnak, ha átmegy egy vak ellenőrzésen (lásd a Nyitott kérdések 1. pontját).
  - Miért 2 kar: a 2. kutatási kör ezt döntötte el, és egy harmadik kar a kezdeti megjelenítések harmadát egy teszteletlen képre adná.
  - Az A-t és a B-t ellenőriztem telefonméretben (168×94), világos és sötét témán is.
  - Kockázat az A-nál: a „víz nélküli Hawaiʻi” kép már létezik más csatornákon (Bright Side Dark Secrets: „What Hawaii Looks Like Without Water (The 30,000 ft Drop)”; Unseen Works: „What the Pacific Ocean Looks Like Drained?”). Az ajánlott videók mellett az A ezekhez hasonlít a legjobban; a megkülönböztetőnk a cím „(Look Down)” része. Az Analytics „Suggested videos” forrásainál figyeld, kik mellett jelenik meg. Ha a teszt a B-t hozza ki győztesnek, a B marad. Ha eldöntetlen, az A.
- **End screen:** 12:15-től a végéig (kb. 12 s; a YouTube 5-20 s-ot enged).
  - A kép 12:14.9-től üres háttér, semmi nincs rárajzolva, így az elemek bárhová mehetnek.
  - Videó elem: **„Egy konkrét videó” → a Lake Peigneur videónk.** A film utolsó mondata ezt vezeti fel: 12:07.7-nél „And what happens when a real lake drains, straight down a hole?”, majd „Louisiana found out.”
  - Feliratkozás elem.
- **Kártya:** 12:07-nél egy videó-kártya a Lake Peigneur videóra, a felvezető mondatra.
- **„Altered or synthetic content” jelölőnégyzet:** a te döntésed, a YouTube aktuális útmutatója („Disclosing use of altered or synthetic content”) alapján. Ez a kérdés a képre és a hangra is vonatkozik.
  - Kép: térképek, valós adatokból készült terep-renderek és közkincs archív fotók. A tenger eltüntetése szemléltető animáció, ezt a leírás is kimondja.
  - Hang: narráció, zene és hangeffektek. A narráció egyetlen valós, megnevezett személy szájába sem ad szavakat, és nincs benne valós esemény hangfelvételét utánzó rész.
  - Valós személyt vagy eseményt utánzó, valósághű felvétel nincs benne.
- **Visibility:** feltöltéskor Private. A Public vagy az ütemezés a te döntésed (lásd `feltoltes_hu.md`).

## Nyitott kérdések (a tulajdonos dönt)

1. **A C (WALK TO MAUI) tartalék, nem kerül a tesztbe.**
   - A mostani formájában a C a legerősebb „utazós” kép a háromból (aloha-inges turista bőrönddel), látszik rajta egy arc, és telefonméretben a padló sónak vagy aszfaltnak látszik, nem tengerfenéknek.
   - Harmadik kar csak akkor lehet belőle, ha javítás után egy vak ellenőrzésen (A és B mellett, alacsony Up next helyen) legalább annyiszor választják, mint a B-t, és a gyors ránézés nem mondja „utazás”-nak vagy „sivatag”-nak. Ezt nem én döntöm el, hanem a vak teszt.
   - A javításhoz új motorrender kell, a mostani képkockákból nem jön ki: a kalapemelős pillanatban (0:25 körül) is látszik az arc, és mindegyiken ott a bőrönd. Kell: arc nélküli alak, bőrönd nélkül, a háttérben vízpart és a régi part vékony fehér vonala, a film tengerszintjén.
2. **A 2026-os Hōlei-fotó jóváírása: a nyilvános közzétételt blokkolja, a privát feltöltést nem.**
   - A képet (az ív helye az omlás után, 2026. szept. 30.) a FOX Weather oldaláról vettük. A FOX Weather és a Popular Science is „NPS Photo/J.Wei” jóváírással közli.
   - Az nps.gov-on nincs fent: a park sajtóközleménye (2026. okt. 1.) csak a 2022-es, még álló ívet mutatja. A CNN szerint a park a Facebookon és az Instagramon tett közzé előtte-utána képeket. A FOX Weather fájlneve Facebook-stílusú, tehát valószínűleg onnan való. Bejelentkezés nélkül ezt nem tudtam megnyitni, és USGS-változatot sem találtam.
   - **Teendőd:** nyisd meg a Hawaiʻi Volcanoes National Park Facebook- vagy Instagram-posztját 2026. okt. 1-jéről („Yes, it's true. RIP Hōlei Sea Arch”). Nézd meg, hogy ugyanaz a fotó van-e rajta, és a park sajátjaként vagy NPS-jóváírással jelenik-e meg.
   - Ha igen, a jóváírás marad, a fotó közkincs (szövetségi alkalmazott munkája).
   - Ha nem, vagy nem találod, a filmben cserélni kell a felvételt (például a 2022-es NPS/Janice Wei fotó plusz a motor terepe), mielőtt a videó nyilvános lesz. Ez a film módosítása, nem a csomagé.
3. **Felirat:** `captions_en.srt` még nincs.
4. **End screen és kártya:** erősítsd meg, hogy a Lake Peigneur videóra mutasson.
5. **A film még véglegesítés alatt van.** A képek és a fejezetidők a mai állapotot tükrözik. A videófájl átadása előtt a végleges masteren ellenőrizni kell:
   - hogy az 1. képkocka egyezik-e az A képpel (`engine/www/ep/ep02/tools/frame1_check.py --mask-label`);
   - hogy a fejezetkártyák kezdetei nem mozdultak-e el. Ez legfőképp a 6. fejezetre igaz: a 9:59 csak 0,01 s-mal van a kártya kezdete után.
