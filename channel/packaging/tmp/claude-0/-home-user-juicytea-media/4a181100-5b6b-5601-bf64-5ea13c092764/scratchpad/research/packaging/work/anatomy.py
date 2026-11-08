#!/usr/bin/env python3
"""Title anatomy: classify titles, score performance, compare top decile vs median.
Usage: anatomy.py WORKDIR OUT_TITLES_JSON OUT_STATS_JSON"""
import json, re, sys, math, statistics as st, collections

W, OUT_TITLES, OUT_STATS = sys.argv[1], sys.argv[2], sys.argv[3]
f = json.load(open(W + '/raw/filtered.json'))
ch = json.load(open(W + '/raw/channels.json'))

# ---------------- space filter ----------------
EXC2 = re.compile(r"\breact|\bkids\b|for kids|\bks[1-4]\b|lesson|\bclass\b|grade \d|\bupdate\b|\bseason\b|weather|\bstorm\b|hurricane|mayor|cycling|\bbike|hik(e|ing)|camping|\bcamp\b|overnight|i visited|visiting|we visited|\btrip\b|tourist|\bguide\b|beach|game|gameplay|\brpg\b|\bsteam\b|board game|texture|blender|tutorial|drawing|cannabis|\bhash\b|crime|murder|vanished|missing|serial|killer|police|arrest|unsolved|how to play|\bdiy\b|review|unboxing|interview|q&a|rant|prank|\bnasa live|official|\bep\.? ?\d|episode|part \d|pt\. ?\d|#\w+|cast\b|disney|nat geo wild|national geographic$|colorized|cesar romero|\bsurvivor\b|ghost|haunted|paranormal|alien|ufo|bigfoot|giants? (?:found|skeleton)|nephilim|flat earth|tartaria|mud flood|ancestry|dna\b|bloodline", re.I)
NONENG = re.compile(r"\b(apa|itu|dan|yang|pernah|jadi|di manakah|el|la|los|las|del|que|und|der|die|das|ist|nicht|une|les|des|est|sur|il|di|da|em|com|para|nao|não|ve|bir|ile|ne|kya|hai|hindi|ang|ng|mga|sa)\b", re.I)
NICHE = re.compile(r"hawai|island|ocean|\bsea\b|\bseas\b|volcan|everest|mountain|\bmaps?\b|geograph|continent|\bearth|drain|without (?:water|ice|the ocean|oceans)|trench|underwater|\blost (?:land|continent|world|city|island)|sunken|atlantis|doggerland|zealandia|sundaland|beringia|countr|border|lake|river|\bbay\b|mediterranean|pacific|atlantic|deepest|tallest|forbidden|remote|abandoned|isolated|seafloor|sea floor|abyss|glacier|antarctic|arctic|greenland|tsunami|earthquake|tectonic|magma|crater|caldera|desert|canyon|cave|planet|world|places?\b|land\b|state\b|city|cities|region|coast|reef|atoll|ice age|sea level", re.I)

def months(age):
    m = re.match(r'(?:Streamed )?(\d+)\s*(\w+)', age or '')
    if not m: return None
    n, unit = int(m.group(1)), m.group(2)
    if unit.startswith('mo'): return float(n)
    if unit.startswith('min'): return n / 43800
    return n * {'s': 1/2.6e6, 'h': 1/730, 'd': 1/30.4, 'w': 7/30.4, 'y': 12}.get(unit[0], 0) or None

def niche_share(c):
    rec = [v for v in c.get('recent', []) if v.get('title')]
    if not rec: return None
    return sum(1 for v in rec if NICHE.search(v['title'])) / len(rec)

# ---------------- gazetteer for proper nouns ----------------
PLACES = """Hawaii Hawaiian Hawai'i Hawaiʻi Oahu Maui Kauai Molokai Lanai Niihau Mauna Kea Loa Kilauea Midway Honolulu Pearl Harbor Nihoa Kure Loihi
Everest Himalaya Himalayas Himalayan K2 Kilimanjaro Denali Alps Andes Rockies Appalachia Appalachian Olympus Mons Fuji Vesuvius Pompeii Krakatoa Krakatau Tambora Pinatubo Etna Yellowstone Hunga Tonga Iceland Icelandic Santorini Thera Toba Campi Flegrei St. Helens Helens Rainier Hood
Mariana Marianas Challenger Puerto Rico Kermadec Tonga
Pacific Atlantic Indian Arctic Antarctic Antarctica Southern Mediterranean Caribbean Baltic Black Caspian Red Dead Aral North Sea South China Bering Beringia Doggerland Zealandia Sundaland Sahul Atlantis Lemuria Mu Kumari Kandam Gondwana Pangaea Pangea Rodinia Laurasia Tethys Panthalassa
Africa African Asia Asian Europe European America American Americas Australia Australian Oceania Greenland Siberia Siberian Alaska Alaskan Canada Canadian Mexico Mexican Brazil China Chinese Japan Japanese Korea Korean India Indian Russia Russian Indonesia Indonesian Philippines Filipino Britain British UK England English Scotland Ireland Wales France French Germany German Italy Italian Spain Spanish Portugal Greece Greek Turkey Egypt Egyptian Israel Iran Iraq Saudi Arabia Arabian Norway Sweden Finland Denmark Netherlands Dutch Belgium Switzerland Austria Poland Ukraine Romania Chile Peru Argentina Colombia Venezuela Cuba Haiti Jamaica Bahamas Bermuda Fiji Samoa Tahiti Polynesia Polynesian Micronesia Melanesia Madagascar Mauritius Maldives Seychelles Sri Lanka Nepal Tibet Bhutan Pakistan Afghanistan Mongolia Kazakhstan Vietnam Thailand Malaysia Singapore Borneo Sumatra Java Bali Papua Guinea Taiwan Hong Kong Kamchatka Kuril Sakhalin Svalbard Faroe Azores Canary Galapagos Galápagos Easter Pitcairn Tristan Cunha Bouvet Kerguelen Heard Macquarie Diego Garcia Chagos Socotra Sentinel Iwo Jima Okinawa Guam Saipan Wake Johnston Palmyra Baker Howland Jarvis Nauru Kiribati Tuvalu Marshall Bikini Antarctica Sahara Gobi Amazon Congo Nile Mississippi Colorado Grand Canyon Great Lakes Michigan Superior Erie Ontario Huron Chesapeake Florida Texas California Californian Nevada Arizona Utah Oregon Washington Montana Wyoming Idaho Maine Louisiana Georgia Carolina Virginia Tennessee Kentucky Ohio Missouri Kansas Nebraska Dakota Minnesota Iowa Illinois Indiana Wisconsin Arkansas Oklahoma Alabama Mississippi Mexico York Jersey Midwest Mojave Powell Mead Baikal Titicaca Victoria Tanganyika Malawi Chad Okeechobee Superior Nazca Giza Stonehenge Tunguska Chernobyl Bermuda Svalbard Kola Darvaza Siberia Patagonia Tierra Fuego Cape Horn Drake Gibraltar Bosphorus Suez Panama Zanclean Messinian Black Sea Lake Peigneur Peigneur Mars Moon Venus Jupiter Titan Europa Sun""".split()
PLACESET = set(w.lower() for w in PLACES)
COMMON_CAP = set("""the a an of in on at to is are was were why how what who which that this these those and or for with from by it its be as do does did you your we our they their can could would will not no if then than into over under about there here i i'm we're it's here's what's that's don't can't won't isn't aren't wasn't nobody no one never ever every all most more less just only real really actually finally earth world ocean oceans sea seas island islands mountain mountains volcano volcanoes map maps lake lakes river rivers land lands continent continents country countries place places planet water ice""".split())

POWER = re.compile(r"\b(insane|terrifying|terrified|shocking|shocked|creepy|creepiest|scary|scariest|eerie|dark|darkest|deadly|deadliest|dangerous|disturbing|bizarre|strange|strangest|weird|weirdest|incredible|unbelievable|haunting|nightmare|horrifying|horrific|mysterious|mystery|mysteries|secret|secrets|forbidden|impossible|unexplained|terrible|massive|giant|gigantic|huge|enormous|monster|monstrous|mind-blowing|crazy|wild|epic|extreme|brutal|chilling|frightening|unsettling|catastrophic|apocalyptic|doomed|vanished|lost|hidden|truth|real|really|actually|finally|never|nobody|no one|everything|every|only|ultimate|greatest|biggest|largest|deepest|tallest|highest|oldest|hardest|longest|worst|best|most)\b", re.I)
HEDGE = re.compile(r"\b(maybe|might|could|not just|sort of|kind of|probably|possibly|may|perhaps|almost|nearly|partly|somewhat|not entirely|not quite)\b", re.I)

def tokens(t):
    return re.findall(r"[A-Za-z0-9'’ʻ.,-]+", t)

def is_title_case(t):
    ws = [w for w in re.findall(r"[A-Za-z][A-Za-z'’]*", t) if len(w) > 3]
    if not ws: return True
    return sum(1 for w in ws if w[0].isupper()) / len(ws) > 0.6

def proper_nouns(t):
    """Return list of proper-noun tokens (gazetteer + sentence-case capitals)."""
    out = []
    toks = re.findall(r"[A-Za-z][A-Za-z'’ʻ.-]*", t)
    tc = is_title_case(t)
    for i, w in enumerate(toks):
        lw = w.lower().strip("'’.-")
        lw2 = re.sub(r"['’]s$", '', lw)
        if lw2 in PLACESET or lw in PLACESET:
            out.append(w)
        elif (not tc) and i > 0 and w[0].isupper() and lw2 not in COMMON_CAP and not w.isupper():
            out.append(w)
    return out

def first3(t):
    return ' '.join(re.findall(r"[^\s]+", t)[:3])

# ---------------- formula tags ----------------
FORM = [
 ('drained', r"\bdrain(ed|ing|s)?\b|\bwithout (the )?(water|ocean|oceans|sea)\b|if (the )?(oceans?|seas?|lakes?|water)( suddenly)? (disappeared|vanished|dried up|drained|were gone)|\bwater (was|were) gone|all the water"),
 ('without_x', r"\bwithout\b"),
 ('looks_like', r"looks? like|look like|what .* would look|really looks|actually looks"),
 ('what_if', r"^(what|so what) if\b|what would happen if|what happens if|what if\b"),
 ('hidden_under', r"\bhidden|\bhiding|\bhides\b|beneath|underneath|\bunder (the |antarctica|the ice|the sea|the ocean|water|\w+'s)|lies below|lurk|buried|below the"),
 ('is_hiding', r"\bis hiding|are hiding|was hiding|hiding something|hides something"),
 ('heres_what', r"here'?s what|here'?s why|here'?s how|this is what|this is why|what (was|is) (hidden|found|left|discovered)|what (they|we|scientists|it) (found|discovered|saw)"),
 ('cant_visit', r"can'?t (visit|go|enter|land|travel|reach)|cannot (visit|go|enter)|not allowed|forbidden|banned|off[- ]limits|no one (is allowed|can (go|visit|enter))|never (visit|enter|go)|impossible to (reach|visit)|hardest .* to (reach|visit)|you can'?t"),
 ('bigger_than_think', r"(bigger|larger|deeper|taller|older|stranger|weirder|worse|better|smaller|closer|farther|further|longer|higher) than (you|we|anyone|people|most) (think|thought|realize|imagined|know)|than you think|people are (only )?just realising|realizing how|true size|actual size|real size|how big .* (really|actually) is|is (actually|really) (huge|massive|tiny|enormous)"),
 ('is_actually', r"\b(is|are|was|were) (actually|really|secretly|not|n't)\b|isn'?t|aren'?t|\bactually\b|\bwrong\b|\blies?\b|\blied\b|\bmyth\b|everything you know|you('ve| have) been|we('ve| have) been|misconception"),
 ('superlative', r"\b(most|biggest|largest|deepest|tallest|highest|oldest|hardest|longest|strangest|weirdest|creepiest|deadliest|scariest|worst|best|greatest|loneliest|remotest|smallest|youngest|newest|coldest|hottest|wettest|driest|richest|poorest|least)\b"),
 ('number_list', r"^\d+ |^top \d+|^(the )?\d+ (\w+ ){0,3}(places|islands|mountains|volcanoes|countries|maps|facts|things|secrets|mysteries|discoveries|lakes|borders|reasons|ways|cities|lost|ancient|strange|weird|hidden|abandoned|forbidden|remote|creepiest|deepest|largest|biggest|most)"),
 ('every_x', r"^every\b|\bevery (\w+ ){0,2}(island|place|country|volcano|mountain|ocean|sea|map|state|forbidden|unexplored|lost|continent)|^all \d+|^all (the )?\w+ (ranked|explained|compared)|ranked\b|explained in \d"),
 ('why_q', r"^why\b"),
 ('how_q', r"^how\b"),
 ('what_q', r"^(what|what's|whats)\b(?! if)"),
 ('is_there_q', r"^(is|are|can|could|does|do|did|will|would|should|was|were|has|have)\b.*\?$"),
 ('question_mark', r"\?"),
 ('the_x_that', r"^(the|this|a|an) (\w+[ -]){0,4}(that|which|where|who|nobody|no one)\b"),
 ('two_sentence', r"[a-z0-9'\")][.!] +[A-Z]"),
 ('colon_subtitle', r"[a-z0-9'\")]: "),
 ('dash_split', r" [-–—|] "),
 ('discovery_news', r"\bscientists?\b|\bjust (found|discovered|revealed|made|uncovered|detected)|\bfinally\b|\bdiscover(ed|y|ies)\b|\buncover(ed|s)?\b|\bnew (study|discovery|evidence|research|data|map|images?)\b|\breveal(ed|s)?\b|\bfound\b|\bnasa\b|\bsatellite\b|\bsonar\b|\bscan(s|ned)?\b|\bsurvey\b"),
 ('nobody_talks', r"nobody (talks|knows|tells|told|expected|noticed|believed|realized|realised)|no one (talks|knows|tells|told|expected|noticed)|you (never|didn'?t) (knew|know|heard|learned|realized|noticed)|never (told|taught)|they don'?t (teach|tell|want)|you were never|you'?re not (supposed|allowed)|not supposed to"),
 ('mystery', r"myster|unexplained|can'?t explain|cannot explain|no one can explain|still can'?t|baffl|puzzl|enigma|unsolved|impossible|no geologist|scientists can'?t|science can'?t|shouldn'?t exist|should not exist|defies"),
 ('documentary_label', r"documentary|\bexplained\b|history of|a history|the story of|full story|\bsummarized\b|\bin \d+ minutes\b|\bmarathon\b|\bfor sleep\b|to fall asleep|sleep"),
 ('first_person', r"\b(we|i|i'm|we're|i've|we've|my|our|us)\b"),
 ('second_person', r"\b(you|your|you're|you've|you'll)\b"),
 ('number_any', r"\d"),
 ('allcaps_word', None),
 ('bracket', r"[\(\[]"),
 ('hedge', None),
 ('sleep_doc', r"for sleep|to fall asleep|sleep|bedtime|relaxing documentary|calm documentary"),
 ('disaster_story', r"disaster|eruption|erupted|explod|tsunami|earthquake|collapse|catastroph|claimed .* lives|killed|deaths?|died|survival|surviv|tragedy|destroyed|wiped"),
 ('time_span', r"\b\d[\d,]* (years|million years|billion years|years ago)\b|\bfrom \d|\bto \d[\d,]* (years|ad|bc)|\beve?ry year\b|timelapse|time-lapse"),
]
FORM_RE = {k: (re.compile(v, re.I) if v else None) for k, v in FORM}

def tags_for(t):
    out = {}
    for k, rx in FORM_RE.items():
        if k == 'allcaps_word':
            caps = [w for w in re.findall(r"\b[A-Z][A-Z']{2,}\b", t) if w not in ('USA', 'UK', 'US', 'NASA', 'USGS', 'NOAA', 'WWII', 'WW2', 'II', 'III', 'UN', 'EU', 'AD', 'BC', 'DNA', 'CIA', 'FBI', 'UFO', 'TV', 'NYC', 'LA', 'USSR', 'NATO', 'AI', 'K2')]
            out[k] = bool(caps)
        elif k == 'hedge':
            out[k] = bool(HEDGE.search(t))
        else:
            out[k] = bool(rx.search(t))
    return out

PRIORITY = [  # primary formula family, first match wins
 ('drain_without', lambda g: g['drained'] or (g['without_x'] and (g['looks_like'] or g['what_if']))),
 ('without_x_other', lambda g: g['without_x']),
 ('what_if', lambda g: g['what_if']),
 ('cant_visit', lambda g: g['cant_visit']),
 ('is_hiding', lambda g: g['is_hiding']),
 ('hidden_under', lambda g: g['hidden_under']),
 ('bigger_than_think', lambda g: g['bigger_than_think']),
 ('nobody_talks', lambda g: g['nobody_talks']),
 ('number_list', lambda g: g['number_list']),
 ('every_x', lambda g: g['every_x']),
 ('is_actually_myth', lambda g: g['is_actually']),
 ('mystery', lambda g: g['mystery']),
 ('discovery_news', lambda g: g['discovery_news']),
 ('why_q', lambda g: g['why_q']),
 ('how_q', lambda g: g['how_q']),
 ('what_q', lambda g: g['what_q']),
 ('other_question', lambda g: g['question_mark']),
 ('the_x_that_story', lambda g: g['the_x_that']),
 ('superlative', lambda g: g['superlative']),
 ('statement_twist', lambda g: g['two_sentence'] or g['dash_split'] or g['colon_subtitle']),
 ('label_topic', lambda g: True),
]

def primary(g):
    for name, fn in PRIORITY:
        if fn(g): return name

def curiosity(t, g):
    if g['drained'] or g['without_x'] or g['what_if'] or g['looks_like']: return 'transformation_reveal'
    if g['heres_what'] or re.search(r"\b(something|this|what|why)\b", t, re.I) and (g['two_sentence'] or g['dash_split'] or g['is_hiding']): return 'withheld_object'
    if g['is_hiding'] or g['hidden_under']: return 'hidden_thing'
    if g['cant_visit']: return 'forbidden_access'
    if g['is_actually'] or g['bigger_than_think'] or g['nobody_talks']: return 'belief_violation'
    if g['number_list'] or g['every_x']: return 'list_completeness'
    if g['question_mark'] or g['why_q'] or g['how_q'] or g['what_q']: return 'open_question'
    if g['mystery']: return 'mystery'
    if g['the_x_that']: return 'story_hook'
    if g['superlative']: return 'superlative'
    return 'label_none'

def bracket_kind(t):
    m = re.findall(r"[\(\[]([^\)\]]*)[\)\]]", t)
    if not m: return None
    b = ' '.join(m).lower()
    if HEDGE.search(b) or 'not just' in b or 'coincidence' in b: return 'hedge'
    if re.search(r"4k|hd|documentary|full|marathon|sleep|series|part|ep|compilation|\d+ ?(min|hour|hr)", b): return 'format_label'
    if re.search(r"\d", b): return 'number'
    if re.search(r"shocking|insane|real|truth|actually|nobody|no one|terrifying|you|not|never|wrong|explained", b): return 'twist_or_emotion'
    return 'other'

# ---------------- build table ----------------
rows = []
for r in f:
    t = r['title'].strip()
    if EXC2.search(t) or NONENG.search(t): continue
    c = ch.get(r['channel_id'], {})
    mo = r.get('age_months') or months(r['age'])
    subs = c.get('subs')
    med = c.get('median_recent_views')
    g = tags_for(t)
    pn = proper_nouns(t)
    words = re.findall(r"[^\s]+", t)
    f3 = ' '.join(words[:3])
    rows.append({
        'id': r['id'], 'title': t, 'channel': r['channel'], 'channel_id': r['channel_id'],
        'subs': subs, 'channel_median_recent_views': med, 'channel_niche_share': round(niche_share(c), 2) if c.get('recent') else None,
        'views': r['views'], 'age': r['age'], 'age_months': round(mo, 2), 'len_s': r['len_s'],
        'views_per_month': round(r['views'] / max(mo, 0.25)),
        'views_per_sub': round(r['views'] / subs, 2) if subs else None,
        'breakout': round(r['views'] / med, 2) if med and med >= 50 else None,
        'chars': len(t), 'n_words': len(words), 'first3': f3,
        'proper_nouns': pn, 'proper_in_first3': any(p in ' '.join(words[:3]) for p in pn),
        'power_words': sorted(set(m.group(0).lower() for m in POWER.finditer(t))),
        'formula': primary(g), 'tags': [k for k, v in g.items() if v],
        'curiosity': curiosity(t, g), 'bracket': bracket_kind(t),
        'url': 'https://www.youtube.com/watch?v=' + r['id'],
        'queries': r['queries'],
    })

json.dump(rows, open(OUT_TITLES, 'w'), indent=0, ensure_ascii=False)
print('rows', len(rows), file=sys.stderr)
