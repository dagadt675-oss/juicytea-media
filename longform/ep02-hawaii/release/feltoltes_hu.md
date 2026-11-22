# Ep02 feltöltése lépésről lépésre (YouTube Studio)

A bemásolandó szövegek a `metadata.md`-ben vannak.
Számítógépen dolgozz (studio.youtube.com), mert az A/B teszt csak ott érhető el.
A menüneveket magyarul és angolul is megadom, zárójelben az angol.

## 0. Előtte

- Kéznél legyen: a videófájl, a 2 tesztkép (`thumb_A_no_ocean.jpg`, `thumb_B_one_island.jpg`) és a `metadata.md`.
- A `thumb_C_walk_to_maui.jpg` **tartalék, ne töltsd fel** (a `metadata.md` Nyitott kérdések 1. pontja mondja meg, mikor jöhet).
- Az A/B teszthez a csatornán be kell kapcsolni a speciális funkciókat:
  - Beállítások (Settings) → Csatorna (Channel) → Funkciókra való jogosultság (Feature eligibility).
  - Ha ez nincs bekapcsolva, a teszt gomb nem jelenik meg.

## 1. Feltöltés privátként

1. Létrehozás (CREATE) → Videók feltöltése (Upload videos) → válaszd ki a videófájlt.
2. A feltöltés alatt töltsd ki a következő lépéseket. A láthatóság végig **Privát (Private)** marad.

## 2. Részletek (Details)

1. **Cím (Title):** másold be a `metadata.md` Title blokkját.
2. **Leírás (Description):** másold be a Description blokkot. A fejezetek ebből automatikusan létrejönnek.
3. **Bélyegkép (Thumbnail):** Fájl feltöltése → `thumb_A_no_ocean.jpg`. Ez a fő kép.
4. **Közönség (Audience):** Nem, nem gyerekeknek készült (No, it's not made for kids).
5. Kattints a **Továbbiak megjelenítése (Show more)** gombra:
   - **Címkék (Tags):** másold be a Tags blokkot.
   - **Videó nyelve (Video language):** English.
   - **Kategória (Category):** Oktatás (Education).
   - **Módosított vagy szintetikus tartalom (Altered content):** a te döntésed, lásd a `metadata.md` Settings részét.
   - A hozzászólások maradjanak bekapcsolva.

## 3. A/B teszt (régi nevén Test & Compare) 2 képpel: A és B

A YouTube súgója szerint (support.google.com/youtube/answer/13861714, 2026-11-22):
- csak számítógépen működik;
- legfeljebb 3 cím vagy kép tesztelhető;
- a győztest a **megtekintési idő** dönti el, nem a CTR;
- **privát videón nem használható**;
- a teszt néhány nap, legfeljebb 2 hét;
- három eredmény lehet: győztes (Winner), egyformán teljesítettek (Performed same), vagy nem dönthető el (Inconclusive);
- ha egyik kép sem nyer (Performed same vagy Inconclusive), az elsőként feltöltött kép marad.

Így csináld:

1. Ha a Bélyegkép alatt már feltöltéskor látod az **A/B tesztelés (A/B Testing)** gombot, és engedi:
   - válaszd a **Csak bélyegkép (Thumbnail only)** lehetőséget;
   - töltsd fel sorban: **először az A, utána a B**;
   - kattints a Kész (Done) gombra.
2. Ha privát videónál nem engedi (ez a várható eset), **közvetlenül a megjelenés után** állítsd be:
   - Tartalom (Content) → a videó → Bélyegkép (Thumbnail) → A/B tesztelés (A/B Testing) → Csak bélyegkép (Thumbnail only);
   - a képek sorrendje **A, aztán B**; ha az A már ott van első helyen, hagyd ott, és csak a B-t add hozzá;
   - Kész (Done).
3. Ha a gomb sehol nincs, a csatorna (még) nem jogosult. Ekkor maradjon az A kép, és szólj.
4. A teszt alatt **ne változtass címet vagy képet**, mert az leállítja a tesztet.
5. **A C-t ne tedd be.** A tesztben csak az A és a B legyen. Harmadik kar csak akkor lehet, ha a C átmegy a vak ellenőrzésen, és erről külön szólok.

## 4. Videóelemek (Video elements)

1. **Feliratok (Subtitles):** ha elkészül a `captions_en.srt`, Hozzáadás → Fájl feltöltése → Időzítéssel (With timing). Addig kihagyható.
2. **Záróképernyő (End screen):** Hozzáadás.
   - **Videó (Video)** elem → **Konkrét videó kiválasztása (Choose specific video)** → a **Lake Peigneur** videónk.
   - **Feliratkozás (Subscribe)** elem.
   - Mindkettő 12:15-től a videó végéig (12:26) látszik.
   - A háttér ott üres, így az elemek bárhová mehetnek.
3. **Kártyák (Cards):** Hozzáadás → Videó → a Lake Peigneur videó, kezdés **12:07**. Ekkor hangzik el: „And what happens when a real lake drains, straight down a hole?”

## 5. Ellenőrzések (Checks)

Várd meg, amíg a szerzői jogi ellenőrzés lefut. Hiba esetén ne publikálj, hanem szólj.

## 6. Láthatóság és ütemezés (Visibility)

1. Most válaszd a **Privát (Private)** lehetőséget, és mentsd. Így a videó fent van, de senki nem látja.
2. A Nyilvános (Public) vagy az Ütemezés (Schedule) **csak a te döntésed**.
   - **Előtte egy dolgot el kell intézni:** a 2026-os Hōlei-fotó jóváírását (a `metadata.md` Nyitott kérdések 2. pontja). Amíg ez nincs meg, maradjon Privát.
   - Ütemezésnél a videó a megjelenésig privát, ezért az A/B tesztet a megjelenés után állítsd be (3. pont).
   - Az első percek megjelenítései teszt nélkül mennek ki, és mind az A képpel.

## 7. A megjelenés után

1. Állítsd be az A/B tesztet (3. pont), ha még nincs bent.
2. **Rögzített komment:** írd be a `metadata.md` Pinned comment blokkját, majd a három pont menüben válaszd: Rögzítés (Pin).
3. Az eredményt **kb. 10 ezer megjelenítés előtt ne olvasd**.
   - A teszt magától lezárul (legfeljebb 2 hét), és a győztes kép marad.
   - Ha egyik sem nyert (Performed same vagy Inconclusive), az A marad, ezen ne változtass.
4. **Ha elakad:**
   - **Amíg a kép-teszt fut, a címhez ne nyúlj.** A címcsere leállítja a tesztet, és 72 óránál a teszt általában még fut (néhány nap, legfeljebb 2 hét). Ez a szabály az erősebb.
   - Ha a teszt lezárult, és az utolsó 72 óra kb. 3 ezernél kevesebb megjelenítést hozott, cseréld a címet a `metadata.md` 2. címére.
   - Ez legyen az egyetlen változtatás. Utána várj újabb 72 órát.
   - Címet és képet soha ne cserélj ugyanazon a napon.
