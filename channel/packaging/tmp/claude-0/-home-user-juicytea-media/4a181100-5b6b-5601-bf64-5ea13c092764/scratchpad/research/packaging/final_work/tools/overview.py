"""final_overview.jpg: the final ep02 package (3 Test & Compare thumbnails under the launch title, backup titles)
and the ep01 repackage proposal (current vs proposed), labelled in Hungarian. PIL only.
usage: python3 -I overview.py"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PK = '/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging'
INTER = '/usr/share/fonts/opentype/inter/'
ROBOTO = PK + '/feedsim/fonts/'
OUT = PK + '/final_overview.jpg'

BG = (18, 18, 20); PANEL = (30, 30, 34); TXT = (240, 240, 240); SUB = (170, 170, 176)
ACC = (126, 214, 223); WARN = (255, 196, 92); OK = (140, 220, 150)


def F(name, size):
    return ImageFont.truetype(INTER + name, size)


def R(size):
    return ImageFont.truetype(ROBOTO + 'Roboto-Medium.ttf', size)


def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= width: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def para(d, xy, text, font, width, fill, lh=None):
    x, y = xy; lh = lh or int(font.size * 1.35)
    for ln in wrap(d, text, font, width):
        d.text((x, y), ln, font=font, fill=fill); y += lh
    return y


def thumb(path, w):
    im = Image.open(path).convert('RGB'); h = round(w * 9 / 16)
    im = im.resize((w, h), Image.LANCZOS)
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=14, fill=255)
    return im, m


def badge(d, x, y, text, font, fg, bg):
    tw = d.textlength(text, font=font); d.rounded_rectangle([x, y, x + tw + 24, y + font.size + 16], radius=8, fill=bg)
    d.text((x + 12, y + 7), text, font=font, fill=fg)
    return x + tw + 34


def card(S, d, x, y, w, path, tag, tagcol, title, lines, compact=True):
    im, m = thumb(path, w); S.paste(im, (x, y), m); h = im.height
    if compact:  # the 168x94 card as it appears in the Up next list / desktop sidebar
        c = Image.open(path).convert('RGB').resize((168, 94), Image.LANCZOS)
        cm = Image.new('L', (168, 94), 0); ImageDraw.Draw(cm).rounded_rectangle([0, 0, 167, 93], radius=8, fill=255)
        bx, by = x + w - 168 - 12, y + h - 94 - 12
        d.rounded_rectangle([bx - 4, by - 4, bx + 172, by + 98], radius=10, fill=(15, 15, 15))
        S.paste(c, (bx, by), cm)
        d.text((bx, by - 26), '168x94', font=F('Inter-Medium.otf', 16), fill=(220, 220, 220))
    yy = y + h + 14
    badge(d, x, yy, tag, F('Inter-Bold.otf', 22), (15, 15, 15), tagcol); yy += 52
    if title:
        for ln in wrap(d, title, R(27), w):
            d.text((x, yy), ln, font=R(27), fill=TXT); yy += 36
        yy += 6
    for t in lines:
        yy = para(d, (x, yy), t, F('Inter-Regular.otf', 20), w, SUB, 27) + 4
    return yy


def main():
    ends = layout(None)                      # pass 1: measure the two sections
    layout(ends)                             # pass 2: draw panels to fit, then the content


def layout(ends):
    W = 2100
    H = 4000 if ends is None else 175 + (ends[0] - 175 + 30) + 40 + ends[1] + 70
    S = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(S)
    M = 60
    d.text((M, 44), 'Myth Juice: végleges csomag', font=F('Inter-ExtraBold.otf', 54), fill=TXT)
    d.text((M, 112), '2026-11-08  ·  címek és bélyegképek  ·  minden bélyegkép átment a megkülönböztethetőségi kapun (klón- és farm-távolság a kézműves medián felett)',
           font=F('Inter-Regular.otf', 22), fill=SUB)

    # ---------------- ep02 ----------------
    y = 175
    h1 = 1390 if ends is None else ends[0] - y + 30
    d.rounded_rectangle([M - 20, y, W - M + 20, y + h1], radius=22, fill=PANEL)
    d.text((M, y + 26), '2. rész: Hawaii  ·  INDÍTÓ CÍM', font=F('Inter-Bold.otf', 30), fill=ACC)
    d.text((M, y + 70), "Why Can't You See Most of Hawaii? (Look Down)", font=R(50), fill=TXT)
    d.text((M, y + 136), '45 karakter  ·  hozzáférés-kérdés + csavar-zárójel  ·  vak teszt 1. kör: 9/10 választás, a 12 jelölt közül a legjobb (78 pont)  ·  0 azonos hosszú videó a keresésben',
           font=F('Inter-Regular.otf', 22), fill=SUB)
    tw = 640; gap = 30; x0 = M; ty = y + 190
    cards = [
        (PK + '/final_ep02_1.jpg', '1. INDÍTÓ BÉLYEGKÉP (Test & Compare A)', OK, None,
         ['NO OCEAN: a teljesen leengedett óceán, a hegy alsó része látszik.',
          'Kör 1 (ezzel a címmel): 9/10 választás (a véletlen 2,4-szerese), 2/10 első kattintás; Home-on az utolsó helyről is 5/5.',
          'Javítva: világosabb szürke bazalt (fényesség 90 -> 109), felirat 13% -> 15%. Feedsim (3 futás): fényesség-rang 3-5/6 -> 2-3/6 (Home), 7-8/10 -> 3-4/10 (Up next).',
          'Kapu: klón 12.04 (küszöb 11.71), farm 11.48 (11.43).']),
        (PK + '/final_ep02_2.jpg', '2. TESZT B', ACC, None,
         ['ONE ISLAND: a jégkori Maui Nui, ahol Maui, Molokaʻi és Lānaʻi egy sziget (Kahoʻolawe külön).',
          'Kör 1 (saját címével): 7/10 választás, 3 kihagyás is "majdnem".',
          'A melegebb ég és a tónusjavítás elbukott a kapun, ezért a tesztelt kép marad, a földhíd kissé kivilágosítva.',
          'Kapu: klón 11.79, farm 11.45 (szűk, de átment).']),
        (PK + '/final_ep02_3.jpg', '3. TESZT C', ACC, None,
         ['YOU ARE HERE: térképtű a mai partvonalon, alatta a sötét hegyoldal a félig leengedett vízig.',
          'Kör 1-ben a "Summit" cím buktatta (2/10), a tű mindkét választásnál ok volt. Most a nyertes címmel, nagyobb tűvel és felirattal (12.6% -> 15%).',
          'Feltétel: a filmben legyen egy "you are here" pillanat 30 mp-en belül.',
          'Kapu: klón 11.87, farm 11.65.']),
    ]
    yb = 0
    for i, (p, tag, col, title, lines) in enumerate(cards):
        yb = max(yb, card(S, d, x0 + i * (tw + gap), ty, tw, p, tag, col, title, lines))
    yb += 14
    d.text((M, yb), 'TARTALÉK CÍMEK (csak 72 óra elakadás után, egyszerre egy változtatás):', font=F('Inter-Bold.otf', 24), fill=WARN); yb += 40
    for t in ["1. What's Holding Hawaii Up? (It's Slowly Sinking)   (47; kör 1-ben a cím hozta a 7 választásból 5-öt)",
              '2. Hawaii Used to Be Bigger. Where Did It Go?   (42; csak ha a film kimondja: emelkedett a tenger ÉS süllyednek a szigetek)',
              "3. Hawaii's Volcanoes Go Down Farther Than They Go Up   (50; 3 kedvező említés; tényjegyzék-sor kell a többes számhoz)"]:
        d.text((M + 10, yb), t, font=F('Inter-Regular.otf', 23), fill=TXT); yb += 34
    yb += 6
    d.text((M, yb), 'Kiesett: "Only the Summit" címek (a nézők a PBS "legmagasabb hegy" videójához sorolták), képeslap (13 kihagyás: "utazási videó"), szöveg nélküli kép, "How Tall".',
           font=F('Inter-Regular.otf', 21), fill=SUB)
    end1 = yb + 30

    # ---------------- ep01 ----------------
    y = 175 + h1 + 40
    if ends is not None: d.rounded_rectangle([M - 20, y, W - M + 20, H - 40], radius=22, fill=PANEL)
    d.text((M, y + 26), '1. rész: JAVASLAT, CSAK A TULAJDONOS JÓVÁHAGYÁSÁVAL. A YouTube-on még semmi nem változott.', font=F('Inter-Bold.otf', 30), fill=WARN)
    ty = y + 82
    cards = [
        ('/home/user/juicytea-media/longform/ep01-continental-drip/release/thumb_B_pointing_at_what.jpg', 'JELENLEGI (élő)', (200, 120, 120),
         'Why the Continents Point South (Not Just a Coincidence)',
         ['Suggested CTR 1,97% (862 megjelenés), összesen 2,27%.',
          'A legsötétebb kártya minden felületen (fényesség 61, a szomszédok mediánja 90-143). Kapu: BUKOTT (68% kék, 9% piros).',
          'A zárójel bizonytalankodás ("Not Just"), az Up next listában 3 sorra törik.']),
        (PK + '/final_ep01_1.jpg', 'JAVASOLT 1 (alapértelmezett)', OK,
         "Why the Continents Point South (Pangaea's Breakup)",
         ['A Dél-Atlanti-óceán felnyílása 116 millió éve: Dél-Amerika és Afrika két ék, alattuk Antarktisz.',
          'Kör 1: 8/10 kattintás, 4/10 első kattintás (a legjobb a 3 közül). Javítva: hátrébb a kamera, palaszürke háttér (fényesség 80 -> 104).',
          'Kapu: klón 12.42, farm 11.82.']),
        (PK + '/final_ep01_2.jpg', 'JAVASOLT 2 (Test & Compare B)', ACC,
         "Why the Continents Point South (Pangaea's Breakup)",
         ['A valódi Föld délről: a két csúcs a korongon belül, Antarktisz felé mutat.',
          'Kör 1: 5/10 (Home-on 5/5, Up next-ben 0/5). Javítva: a csúcsok most teljesen látszanak.',
          'Kapu: klón 12.02, farm 12.09.']),
    ]
    yb = 0
    for i, (p, tag, col, title, lines) in enumerate(cards):
        yb = max(yb, card(S, d, x0 + i * (tw + gap), ty, tw, p, tag, col, title, lines))
    yb += 10
    d.text((M, yb), 'Tartalék címek: "Why South America and Africa Point at Antarctica" (48)  ·  "South America Points at Antarctica. So Does Africa" (50).',
           font=F('Inter-Regular.otf', 22), fill=TXT); yb += 34
    d.text((M, yb), 'Figyelem: a film itt óvatos ("most likely"), a zárójel a film záró mondatát ismétli ("It was a breakup."). Ha a bizonytalanságnak a címben is ott kell lennie, az 1. tartalék cím a jó.',
           font=F('Inter-Regular.otf', 21), fill=SUB)
    if ends is None:
        return (end1, yb - y)
    S.save(OUT, quality=88, optimize=True, progressive=True)
    print(OUT, S.size, os.path.getsize(OUT) // 1024, 'KB')


if __name__ == '__main__':
    main()
