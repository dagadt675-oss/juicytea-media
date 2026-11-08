#!/usr/bin/env python3
"""Title anatomy v2 (packaging lab, 2026-11-08).
Builds the raw title table and the evidence stats from two samples:
  A = search sample: titles that YouTube search surfaces for ~100 niche queries (5 filters each).
  B = upload sample: every recent long-form upload of in-space channels (channel /videos pages),
      which has no search-ranking survivorship.
Performance = breakout (views / the channel's own median recent long-form views), i.e. views relative
to channel size; fallback = views per month of age (A rows whose channel has no usable baseline).
Usage: title_anatomy.py WORKDIR COMP_CHANS_JSON OUT_TITLES_JSON OUT_STATS_JSON
"""
import json, re, sys, math, statistics as st, collections, random
import numpy as np

W, COMP, OUT_T, OUT_S = sys.argv[1:5]
random.seed(7); np.random.seed(7)

# ------------------------------------------------------------------ helpers
def months(age):
    m = re.match(r'(?:Streamed )?(\d+)\s*([a-z]+)', (age or '').strip())
    if not m: return None
    n, u = int(m.group(1)), m.group(2)
    if u.startswith('mo'): return float(n)
    if u.startswith('mi'): return n / 43800
    return n * {'s': 1 / 2.6e6, 'h': 1 / 730, 'd': 1 / 30.4, 'w': 7 / 30.4, 'y': 12}.get(u[0], 0) or None

def len_s(s):
    t = 0
    for p in (s or '').split(':'):
        if p.isdigit(): t = t * 60 + int(p)
    return t

EXC = re.compile(r"relax|ambient|asmr|white noise|sleep music|meditat|calming|\bmusic\b|lofi|lo-fi|drone footage|4k drone|scenic|itinerar|things to do|vlog|hotel|resort|airbnb|cost of living|real estate|moving to|minecraft|roblox|\bgta\b|fortnite|\blive\b|livestream|\bnews\b|cnn|\bfox\b|sermon|prophecy|\bbible\b|jesus|god's|trailer|full movie|movie|official video|lyrics|song|cooking|recipe|food tour|surf|snorkel|scuba|fishing|cruise|budget|travel guide|travel tips|best beaches|walking tour|tour\b|#shorts|podcast|episode \d+ \|", re.I)
EXC2 = re.compile(r"\breact|\bkids\b|for kids|\bks[1-4]\b|lesson|\bclass\b|grade \d|\bupdate\b|\bseason\b|weather|\bstorm\b|hurricane|mayor|cycling|\bbike|hik(e|ing)|camping|\bcamp\b|overnight|i visited|visiting|we visited|\btrip\b|tourist|\bguide\b|beach|game|gameplay|\brpg\b|\bsteam\b|board game|texture|blender|tutorial|drawing|cannabis|\bhash\b|crime|murder|missing|serial|killer|police|arrest|unsolved|how to play|\bdiy\b|review|unboxing|interview|q&a|rant|prank|\bnasa live|official|\bep\.? ?\d|episode|part \d|pt\. ?\d|#\w+|cast\b|disney|colorized|\bsurvivor\b|ghost|haunted|paranormal|alien|ufo|bigfoot|giants? (?:found|skeleton)|nephilim|flat earth|tartaria|mud flood|ancestry|bloodline|trump|election|tariff|war with|\bwwiii\b|stock|crypto|bitcoin", re.I)
NONENG = re.compile(r"\b(apa|itu|dan|yang|pernah|jadi|di manakah|el|la|los|las|del|que|und|der|die|das|ist|nicht|une|les|des|est|sur|il|di|da|em|com|para|nao|não|ve|bir|ile|ne|kya|hai|hindi|ang|ng|mga|sa)\b", re.I)
TOPIC = re.compile(r"hawai|island|ocean|\bsea\b|seas\b|volcan|everest|mountain|\bmap|geograph|continent|earth|drain|without|water|\bice\b|trench|underwater|\blost\b|sunken|sank|atlantis|doggerland|zealandia|sundaland|beringia|countr|border|\bland|world|planet|lake|river|\bbay\b|mediterranean|pacific|atlantic|deep|tallest|biggest|largest|forbidden|remote|abandon|isolated|hidden|myster|places|place\b|mauna|kilauea|eruption|seafloor|sea floor|bottom|abyss|glacier|antarctic|arctic|greenland|tsunami|earthquake|plate|tectonic|magma|crater|caldera|summit|peak|canyon|desert|cave|coast|reef|atoll|ice age|sea level|state\b|states\b|city\b|cities|region|america|alaska|florida|california|texas|siberia|australia|africa|europe|asia", re.I)
NICHE = re.compile(r"hawai|island|ocean|\bsea\b|\bseas\b|volcan|everest|mountain|\bmaps?\b|geograph|continent|\bearth|drain|without (?:water|ice|the ocean|oceans)|trench|underwater|\blost (?:land|continent|world|city|island)|sunken|atlantis|doggerland|zealandia|sundaland|beringia|countr|border|lake|river|\bbay\b|mediterranean|pacific|atlantic|deepest|tallest|forbidden|remote|abandoned|isolated|seafloor|sea floor|abyss|glacier|antarctic|arctic|greenland|tsunami|earthquake|tectonic|magma|crater|caldera|desert|canyon|cave|planet|world|places?\b|land\b|state\b|city|cities|region|coast|reef|atoll|ice age|sea level", re.I)

CLONE = set(h.lower() for h in '''contouratlas hiddenprovinces DrainedAtlas highgroundatlas EarthTipping originofeverydaythings SignalNonsense MapTally GreenstoneEurope RedlineTerritory oscar-campbell-g6n theprimalyears WatchOddlyTold Strangeography BrightSideDarkSecrets waterlineearth vanishingmaps PanicMaps BelowTheMapHQ GeoMetriics UnknownAmericaHQ Mapredacted statesXplained UnderTheAtlasYT GeorgePembroke-j2e WaterlineAtlas BareEarthHQ TheReasonMap MapWhysTV NorthernGrounds CANADA_DISCOVERIES dylan-sinclair-canada Waterwakee TheDrainedMap AtlasBeyondStudio Geospacy TheSilentSpeculation GeoWhatIf-74 TheHiddenMerica HiddenHawaii0 justaboutearth earthdynamics-p4k deeppastearth geographyscoped urbanxplain1 mrtruestates TheHiddenStates-h6t HiddenonEarth-yt Acrosstheglobechannel Submerged-History-YT HiddenHistory-02 MystralTV ExplorerVaultOfficial BuriedSignalYT theultimatefining UnchartedDepthsOfficial ThePlanetUnseen GlobeHaven geographyunfold'''.split())
CRAFT = set(h.lower() for h in '''mr.scienceYT xverse.studios FossilVideos Paintify7 itscuriositydude TheLastDay01 WhereTheyStood Earthyphus AstrumEarth GeographyByGeoff RealLifeLore eons AtlasPro1 besmart halfasinteresting Wendoverproductions kurzgesagt pbsterra pwhitewick flaggeography ExtinctZoo'''.split())

# gazetteer for proper nouns (title case makes capital-letter detection useless on its own)
PLACES = """Hawaii Hawaiian Hawai'i Hawaiʻi Hawaii's Oahu O'ahu Maui Kauai Molokai Lanai Niihau Mauna Kea Loa Kilauea Kīlauea Midway Honolulu Pearl Harbor Nihoa Kure Loihi Lō'ihi Kamaehuakanaloa Hilo Kona Waikiki Diamond Head
Everest Himalaya Himalayas Himalayan K2 Kilimanjaro Denali Alps Andes Rockies Appalachia Appalachian Appalachians Olympus Mons Fuji Vesuvius Pompeii Krakatoa Krakatau Tambora Pinatubo Etna Yellowstone Hunga Tonga Iceland Icelandic Santorini Thera Toba Campi Flegrei Helens Rainier Hood Shasta Mazama Crater Lituya Niagara Death Valley Manly Bonneville Missoula Tulare
Mariana Marianas Challenger Kermadec Pacific Atlantic Arctic Antarctic Antarctica Mediterranean Caribbean Baltic Caspian Aral Bering Beringia Doggerland Zealandia Sundaland Sahul Atlantis Lemuria Mu Gondwana Pangaea Pangea Rodinia Laurasia Tethys Panthalassa Zanclean Messinian
Africa African Asia Asian Europe European America American Americas America's Americans Australia Australian Oceania Greenland Siberia Siberian Alaska Alaskan Canada Canadian Mexico Mexican Brazil China Chinese Japan Japanese Korea Korean India Indian Russia Russian Indonesia Indonesian Philippines Britain British UK England English Scotland Ireland Wales France French Germany German Italy Italian Spain Spanish Portugal Greece Greek Turkey Egypt Egyptian Israel Iran Iraq Saudi Arabia Arabian Norway Sweden Finland Denmark Netherlands Dutch Belgium Switzerland Austria Poland Ukraine Romania Chile Peru Argentina Colombia Venezuela Cuba Haiti Jamaica Bahamas Bermuda Fiji Samoa Tahiti Polynesia Polynesian Micronesia Melanesia Madagascar Mauritius Maldives Seychelles Lanka Nepal Tibet Bhutan Pakistan Afghanistan Mongolia Kazakhstan Vietnam Thailand Malaysia Singapore Borneo Sumatra Java Bali Papua Taiwan Kamchatka Kuril Sakhalin Svalbard Faroe Azores Canary Galapagos Galápagos Easter Pitcairn Tristan Cunha Bouvet Kerguelen Macquarie Diego Garcia Chagos Socotra Sentinel Iwo Jima Okinawa Guam Saipan Wake Johnston Palmyra Howland Jarvis Nauru Kiribati Tuvalu Marshall Bikini Sahara Gobi Amazon Congo Nile Mississippi Colorado Grand Canyon Great Lakes Michigan Superior Erie Ontario Huron Chesapeake Florida Texas California Californian Nevada Arizona Utah Oregon Washington Montana Wyoming Idaho Maine Louisiana Georgia Carolina Virginia Tennessee Kentucky Ohio Missouri Kansas Nebraska Dakota Minnesota Iowa Illinois Indiana Wisconsin Arkansas Oklahoma Alabama York Jersey Midwest Mojave Powell Mead Tahoe Baikal Titicaca Victoria Tanganyika Malawi Chad Okeechobee Nazca Giza Stonehenge Tunguska Chernobyl Kola Darvaza Patagonia Tierra Fuego Horn Drake Gibraltar Bosphorus Suez Panama Peigneur Mars Moon Venus Jupiter Titan Europa Earth's Tromelin Diomede Delmarva Siberia's Australia's Africa's Canada's Japan's China's Russia's Alaska's Florida's Texas's California's Antarctica's Greenland's Iceland's Everest's Hawaii's Europe's Asia's Earth Moon's""".split()
PLACESET = set(w.lower() for w in PLACES) - {'earth', "earth's"}   # "Earth" is too generic to count as a named place
COMMON_CAP = set("""the a an of in on at to is are was were why how what who which that this these those and or for with from by it its be as do does did you your we our they their can could would will not no if then than into over under about there here i i'm we're it's here's what's that's don't can't won't isn't aren't wasn't nobody no one never ever every all most more less just only real really actually finally earth world ocean oceans sea seas island islands mountain mountains volcano volcanoes map maps lake lakes river rivers land lands continent continents country countries place places planet water ice""".split())

def is_title_case(t):
    ws = [w for w in re.findall(r"[A-Za-z][A-Za-z'’]*", t) if len(w) > 3]
    return (not ws) or sum(1 for w in ws if w[0].isupper()) / len(ws) > 0.6

def proper_nouns(t):
    out = []
    toks = re.findall(r"[A-Za-zÀ-ÿʻ'’][A-Za-zÀ-ÿ'’ʻ.-]*", t)
    tc = is_title_case(t)
    for i, w in enumerate(toks):
        lw = w.lower().strip("'’.-")
        lw2 = re.sub(r"['’]s$", '', lw)
        if lw2 in PLACESET or lw in PLACESET: out.append(w)
        elif (not tc) and i > 0 and w[0].isupper() and lw2 not in COMMON_CAP and not w.isupper(): out.append(w)
    return out

POWERCAT = {
 'fear_shock': r"insane|terrifying|terrified|shocking|shocked|creepy|creepiest|scary|scariest|eerie|deadly|deadliest|dangerous|disturbing|nightmare|horrifying|horrific|chilling|frightening|unsettling|catastrophic|apocalyptic|doomed|brutal|monster|monstrous|crazy|mind-blowing|bizarre|strange|strangest|weird|weirdest|wild",
 'mystery_secret': r"mysterious|mystery|mysteries|secret|secrets|secretly|hidden|hiding|forbidden|unexplained|impossible|vanished|lost|unknown|unseen|untold|buried|sealed|banned",
 'scale_superlative': r"massive|giant|gigantic|huge|enormous|biggest|largest|deepest|tallest|highest|oldest|hardest|longest|greatest|most|remote|isolated|extreme|ultimate|entire",
 'truth_correction': r"real|really|actually|truth|true|finally|only|wrong|myth|lie|lies|fake|misunderstands|isn't|wasn't|aren't",
 'absolute_nobody': r"never|nobody|no one|everything|everyone|every|all|nothing",
}
POWERCAT_RE = {k: re.compile(r"\b(" + v + r")\b", re.I) for k, v in POWERCAT.items()}
HEDGE = re.compile(r"\b(maybe|might|could be|not just|sort of|kind of|probably|possibly|perhaps|somewhat|not entirely|not quite)\b", re.I)
# the pass/fail regex from niche_report.md section 4.1 (farm and clone vocabulary)
FARM_RX = re.compile(r"\b(hidden|hiding|hides|nobody|no one|secret|found|discovered|reveal\w*|bottom|beneath|drain\w*|without (water|ice)|what if|here'?s what|talks about|sitting on|isn'?t really|no longer makes sense|survives|shocking|terrifying|sleep|documentary)\b", re.I)

# ------------------------------------------------------------------ formula library (primary = first match)
F = collections.OrderedDict([
 ('drain_we_heres_what',  r"^we drained\b|\bdrained\b.*\bhere'?s what"),
 ('looks_like_without',   r"looks? like without|look like (?:with no|without|if)|^(?:[\w'’ʻ-]+ ){0,3}without (?:the |its |any |all )?(?:water|ocean|oceans|sea|seas|ice|lakes?)\b(?!.*\b(?:survive|days|million|runs|dry|aquifer)\b)|(?:water|ocean|ice) (?:removed|disappeared|vanished)"),
 ('drain_other',          r"\bdrain(?:ed|ing|s)?\b|if (?:the )?(?:oceans?|seas?|lakes?) (?:suddenly )?(?:disappeared|vanished|dried up|were gone)|all the water"),
 ('what_if',              r"^(?:so )?what if\b|what would happen if|what happens if|\bwhat if\b"),
 ('cant_visit_forbidden', r"can'?t (?:visit|go|enter|land|travel|reach|live)|cannot (?:visit|go|enter)|not allowed|forbidden|banned|off[- ]limits|no one (?:is allowed|can (?:go|visit|enter))|impossible to (?:reach|visit)|hardest .* to (?:reach|visit)|you'?re not allowed"),
 ('is_hiding_something',  r"\b(?:is|are|was|were) hiding\b|hiding something|hides something|(?:is|are) sitting on"),
 ('hidden_under_beneath', r"\bhidden\b|\bbeneath\b|underneath|lies (?:below|beneath|under)|\bunder (?:the )?(?:ice|sea|ocean|water|sand|lake|seafloor)\b|what'?s (?:really )?(?:under|below|at the bottom)|at the bottom of|\bburied\b"),
 ('nobody_talks_never_told', r"nobody (?:talks|knows|tells|told|expected|noticed|believed|realized|realised|mentions)|no one (?:talks|knows|tells|told|expected|noticed)|you (?:never|didn'?t) (?:knew|know|heard|learned|realized|noticed)|never (?:told|taught)|they don'?t (?:teach|tell|want)|you were never|not supposed to"),
 ('bigger_than_you_think', r"(?:bigger|larger|deeper|taller|older|stranger|weirder|worse|smaller|closer|farther|further|longer|higher|wider|heavier) than (?:you|we|anyone|people|most) (?:think|thought|realize|imagined|know)|than you think|people are (?:only )?just realising|realizing how|true size|actual size|real size|how big .* (?:really|actually) is|true scale"),
 ('myth_correction',      r"\bisn'?t\b|\baren'?t\b|\bwasn'?t\b|\bweren'?t\b|\bis not\b|\bwas not\b|\bwrong\b|\bmyth\b|\blies?\b|\blied\b|everything you know|you(?:'ve| have) been|misconception|misunderstand|\bfake\b|\bnever (?:was|were|existed|happened)\b"),
 ('mystery_unexplained',  r"myster|unexplained|can'?t explain|cannot explain|no one can explain|still can'?t|baffl|puzzl|enigma|impossible|no geologist|scientists can'?t|science can'?t|shouldn'?t exist|should not exist|defies"),
 ('discovery_news',       r"\bscientists?\b|\bjust (?:found|discovered|revealed|made|uncovered|detected)|\bfinally\b|\bdiscover(?:ed|y|ies)\b|\buncover(?:ed|s)?\b|\bnew (?:study|discovery|evidence|research|data|map|images?)\b|\breveal(?:ed|s)?\b|\bfound\b|\bnasa\b|\bsatellite\b|\bsonar\b|\bscan(?:s|ned)?\b|\bsurvey\b"),
 ('number_list',          r"^\d+ |^top \d+|^(?:the )?\d+ (?:\w+ ){0,3}(?:places|islands|mountains|volcanoes|countries|maps|facts|things|secrets|mysteries|discoveries|lakes|borders|reasons|ways|cities)"),
 ('every_x',              r"^every\b|\bevery (?:\w+ ){0,2}(?:island|place|country|volcano|mountain|ocean|sea|map|state|forbidden|unexplored|lost|continent|year|era)|^all \d+|^all (?:the )?\w+ (?:ranked|explained|compared)|\branked\b"),
 ('why_question',         r"^why\b"),
 ('how_question',         r"^how\b"),
 ('what_question',        r"^(?:what|what's|whats|where|who|which)\b"),
 ('yes_no_question',      r"^(?:is|are|can|could|does|do|did|will|would|should|was|were|has|have)\b"),
 ('other_question',       r"\?"),
 ('when_deep_time',       r"^when\b|\b(?:million|billion) years\b|\bice age\b|\bdeep time\b|\bused to be\b|\bonce (?:was|were)\b|\bwas once\b"),
 ('statement_twist',      r"^[^.!?|:]{12,}[a-z0-9'\")’][.!] +[A-Z]"),
 ('the_x_that_story',     r"^(?:the|this|a|an) (?:[\w'’-]+ ){0,5}(?:that|which|who|where)\b"),
 ('place_plain_claim',    r"^(?:[A-Z][\w'’ʻ.-]*\s){1,4}(?i:is|are|was|were|has|had|have|used to|will|won'?t|can'?t|could|isn'?t|wasn'?t|became|becomes|sits|stands|moves|ate|swallowed|walks|grew|keeps|is only|was once)\b(?!.*\?)"),
 ('inside_explorer',      r"^inside\b|^exploring\b|^(?:i|we) (?:visited|went|spent|explored|climbed|sailed|flew|found|mapped|measured)\b|^journey|^a (?:journey|trip|voyage)"),
 ('superlative_label',    r"\b(?:most|biggest|largest|deepest|tallest|highest|oldest|hardest|longest|strangest|weirdest|creepiest|deadliest|scariest|worst|best|greatest|loneliest|remotest|smallest|youngest|newest|coldest|hottest|driest|richest|poorest|least)\b"),
 ('label_subtitle',       r"[a-z0-9'\")’]: |\s[-–—|]\s"),
 ('label_topic',          r"."),
])
F_RE = {k: re.compile(v, re.I) for k, v in F.items()}
F_RE['place_plain_claim'] = re.compile(F['place_plain_claim'])          # case-sensitive capitals
F_RE['statement_twist'] = re.compile(F['statement_twist'])
F_RE['label_subtitle'] = re.compile(F['label_subtitle'])
NICE = {
 'drain_we_heres_what': '"We Drained X. Here\'s What Was Hidden at the Bottom."',
 'looks_like_without': '"What X Looks Like Without Y" / "X Without Water"',
 'drain_other': 'Other drain verb ("What If We Drained X", "Draining X")',
 'what_if': '"What If X?" / "What Would Happen If X"',
 'cant_visit_forbidden': '"Why Can\'t You Visit X?" / forbidden access',
 'is_hiding_something': '"X Is Hiding Something (Nobody Talks About)"',
 'hidden_under_beneath': '"What\'s Hidden Under X" / beneath / buried',
 'nobody_talks_never_told': '"...Nobody Talks About" / "You Were Never Told"',
 'bigger_than_you_think': '"X Is Bigger Than You Think" / true size',
 'myth_correction': '"X Isn\'t Really Y" / "X Is Wrong" (myth correction)',
 'mystery_unexplained': '"...That No Geologist Can Explain" (mystery)',
 'discovery_news': '"Scientists Just Found X" (discovery/news)',
 'number_list': 'Number list ("10 Places...")',
 'every_x': '"Every X" / ranked completeness',
 'why_question': '"Why X?" (why-explainer, with or without "?")',
 'how_question': '"How X?"',
 'what_question': '"What/Where/Who X?"',
 'yes_no_question': '"Is/Can/Did X?" (yes-no question)',
 'other_question': 'Other question with "?"',
 'when_deep_time': '"When Earth Had X" / "X Used to Be Y" (deep time)',
 'statement_twist': 'Statement + twist (two sentences)',
 'the_x_that_story': '"The X That Y" (story hook)',
 'place_plain_claim': '"Place Is/Was Y" (plain claim, place first)',
 'inside_explorer': '"Inside X" / "I Visited X" (explorer)',
 'superlative_label': 'Superlative label ("The World\'s Most Remote Island")',
 'label_subtitle': 'Label: subtitle / label - subtitle',
 'label_topic': 'Plain topic label',
}

def formulas(t):
    return [k for k in F if F_RE[k].search(t)]

def primary(fs):
    return fs[0] if fs else 'label_topic'

def curiosity(t, fs):
    s = set(fs)
    if s & {'drain_we_heres_what', 'looks_like_without', 'drain_other', 'what_if'}: return 'transformation_reveal'
    if s & {'is_hiding_something', 'hidden_under_beneath'}: return 'hidden_thing'
    if 'cant_visit_forbidden' in s: return 'forbidden_access'
    if s & {'myth_correction', 'bigger_than_you_think', 'nobody_talks_never_told'}: return 'belief_violation'
    if 'statement_twist' in s and re.search(r"\b(?:we|i)\b", t, re.I): return 'withheld_result'      # "We Measured the Rest."
    if 'mystery_unexplained' in s: return 'mystery'
    if s & {'number_list', 'every_x'}: return 'list_completeness'
    if s & {'why_question', 'how_question', 'what_question', 'yes_no_question', 'other_question'}: return 'open_question'
    if 'when_deep_time' in s: return 'deep_time_contrast'
    if 'place_plain_claim' in s or 'statement_twist' in s: return 'surprising_claim'
    if 'the_x_that_story' in s: return 'story_hook'
    if 'superlative_label' in s: return 'superlative'
    return 'none_label'

def bracket_kind(t):
    m = re.findall(r"[\(\[]([^\)\]]*)[\)\]]", t)
    if not m: return None
    b = ' '.join(m).lower()
    if HEDGE.search(b) or 'not just' in b or 'coincidence' in b: return 'hedge'
    if re.search(r"4k|hd|documentary|full|marathon|sleep|series|part|ep\b|compilation|\d+ ?(min|hour|hr)|explained", b): return 'format_label'
    if re.search(r"\d", b): return 'number_or_date'
    if re.search(r"shocking|insane|real|truth|actually|nobody|no one|terrifying|you|not|never|wrong|despite|and why|isn|but", b): return 'twist_or_emotion'
    return 'other'

def first3_kind(t, pn):
    ws = re.findall(r"[^\s]+", t)
    w0 = re.sub(r"[^a-z0-9']", '', (ws[0] if ws else '').lower())
    f3 = ' '.join(ws[:3])
    if w0 in ('we', 'i', "we're", "i'm", "we've", "i've"): return 'we_I'
    if re.match(r"\d", w0) or w0 == 'top': return 'number'
    if re.match(r"(?i)what if", f3): return 'what_if'
    if w0 in ('why', 'how', 'what', "what's", 'whats', 'where', 'who', 'which'): return 'question_word'
    if w0 == 'when': return 'when'
    if w0 in ('is', 'are', 'can', 'could', 'does', 'do', 'did', 'will', 'would', 'should', 'was', 'were', 'has', 'have'): return 'aux_question'
    if w0 in ('every', 'all'): return 'every_all'
    if any(p in f3 for p in pn): return 'proper_noun'
    if w0 in ('the', 'this', 'these', 'a', 'an', 'that', 'there'): return 'the_this'
    if w0 in ('inside', 'exploring', 'journey'): return 'inside'
    return 'other_word'

def features(t):
    fs = formulas(t)
    pn = proper_nouns(t)
    ws = re.findall(r"[^\s]+", t)
    f3 = ' '.join(ws[:3])
    caps = [w for w in re.findall(r"\b[A-Z][A-Z']{2,}\b", t) if w not in ('USA', 'UK', 'US', 'NASA', 'USGS', 'NOAA', 'WWII', 'WW2', 'II', 'III', 'UN', 'EU', 'AD', 'BC', 'DNA', 'CIA', 'FBI', 'UFO', 'TV', 'NYC', 'LA', 'USSR', 'NATO', 'AI', 'K2', 'CGI', 'HD', '4K')]
    pw = {k: sorted(set(m.group(0).lower() for m in rx.finditer(t))) for k, rx in POWERCAT_RE.items()}
    return {
        'chars': len(t), 'n_words': len(ws), 'first3': f3, 'first3_kind': first3_kind(t, pn),
        'proper_nouns': pn, 'n_proper': len(pn), 'proper_in_first3': any(p in f3 for p in pn),
        'power_words': pw, 'n_power': sum(len(v) for v in pw.values()),
        'farm_regex_hit': (FARM_RX.search(t).group(0) if FARM_RX.search(t) else None),
        'formula': primary(fs[:-1] if len(fs) > 1 else fs), 'formulas': [f for f in fs if f != 'label_topic'],
        'curiosity': curiosity(t, fs), 'bracket': bracket_kind(t),
        'question': '?' in t, 'two_sentence': bool(F_RE['statement_twist'].search(t)),
        'has_number': bool(re.search(r"\d", t)), 'allcaps_word': bool(caps),
        'hedge': bool(HEDGE.search(t)), 'first_person': bool(re.search(r"\b(we|i|i'm|we're|i've|we've|my|our|us)\b", t, re.I)),
        'second_person': bool(re.search(r"\b(you|your|you're|you've|you'll|you'd)\b", t, re.I)),
        'emoji': bool(re.search(r"[\U0001F300-\U0001FAFF☀-➿]", t)),
    }

# ------------------------------------------------------------------ load
rows_s = []
for i in (1, 2, 3, 4):
    rows_s += json.load(open(f'{W}/raw/search{i}.json'))
chmeta = {}
qcount = collections.Counter()
for r in rows_s:
    if r.get('channel_id'): chmeta.setdefault(r['channel_id'], {'name': r['channel'], 'url': r.get('channel_url', '')})
queries = sorted(set(r['query'] for r in rows_s))
filtered = json.load(open(f'{W}/raw/filtered.json'))
chans = json.load(open(f'{W}/raw/channels.json'))
comp = json.load(open(COMP))

def chan_profile(recent):
    lf = [v for v in recent if v.get('views') is not None and len_s(v.get('len')) >= 240 and (months(v.get('age')) or 0) >= 14 / 30.4]
    base_set = lf if len(lf) >= 5 else [v for v in recent if v.get('views') is not None]
    base = st.median([v['views'] for v in base_set]) if len(base_set) >= 5 else None
    up30 = sum(1 for v in recent if len_s(v.get('len')) >= 240 and (months(v.get('age')) or 99) <= 1.0)
    ns = (sum(1 for v in recent if v.get('title') and NICHE.search(v['title'])) / len(recent)) if recent else None
    return base, len(base_set), up30, ns

profiles = {}
for cid, c in chans.items():
    if c.get('err'): continue
    base, nb, up30, ns = chan_profile(c.get('recent', []))
    url = chmeta.get(cid, {}).get('url', '')
    h = url.split('/@')[-1].lower() if '/@' in url else ''
    profiles[cid] = {'name': chmeta.get(cid, {}).get('name', ''), 'url': url, 'handle': h, 'subs': c.get('subs'), 'baseline': base,
                     'n_baseline': nb, 'uploads_30d': up30, 'niche_share': ns, 'recent': c.get('recent', [])}
handle2cid = {p['handle']: cid for cid, p in profiles.items() if p['handle']}
for h, c in comp.items():
    hh = h.split('/@')[-1].lower()
    if hh in handle2cid: continue           # already have this channel with video ids
    base, nb, up30, ns = chan_profile(c.get('videos', []))
    profiles['comp:' + hh] = {'name': c.get('name', ''), 'url': h, 'handle': hh, 'subs': c.get('subs'), 'baseline': base,
                              'n_baseline': nb, 'uploads_30d': up30, 'niche_share': ns, 'recent': c.get('videos', [])}

def group_of(p):
    if p['handle'] in CLONE: return 'clone_listed'
    if p['handle'] in CRAFT: return 'craft_listed'
    if (p['uploads_30d'] or 0) >= 20 and (p['niche_share'] or 0) >= 0.5: return 'mass_producer'
    return 'other'

def mk(title, views, age, ls, cid, vid, source, extra=None):
    p = profiles.get(cid, {})
    mo = months(age)
    subs, base = p.get('subs'), p.get('baseline')
    r = {'id': vid, 'url': ('https://www.youtube.com/watch?v=' + vid) if vid else None, 'title': title,
         'channel': p.get('name'), 'channel_handle': p.get('handle'), 'channel_key': cid, 'subs': subs,
         'channel_baseline_views': base, 'channel_uploads_30d': p.get('uploads_30d'),
         'channel_niche_share': round(p['niche_share'], 2) if p.get('niche_share') is not None else None,
         'group': group_of(p) if p else 'other',
         'views': views, 'age': age, 'age_months': round(mo, 2) if mo else None, 'len_s': ls,
         'views_per_month': round(views / max(mo or 0.25, 0.25)),
         'views_per_sub': round(views / subs, 3) if subs else None,
         'breakout': round(views / base, 3) if (base and base >= 50 and p.get('n_baseline', 0) >= 5) else None,
         'source': source}
    if extra: r.update(extra)
    r.update(features(title))
    return r

EXC3 = re.compile(r"upsc|\bias\b|\bssc\b|lecture|^e\d+\.|\b4k\b|travel (?:video|documentary|edit)|living in\b|how people (?:survive|live)|\bwonders of\b|planetball|breaking\b|nurse|psych|after work|hogwarts|harry potter|mansion|\$\d|econom|stock market|invade|minecraft|anime|\blore\b|subscriber|we bought|apartment|home tour|flood threat|evacuat|quiz|self-test|soul|rhythm|my (?:house|life)|homestead|off[- ]grid|cabin|sailing|yacht|van life|family|wedding|honeymoon|\bfood\b|\bvegan\b|\bcars?\b|truck|train ride|\bflight\b|airport|\bairline|\bpopulation 20\d\d|ranked by|gdp|languages?\b|religion|\bsong\b|poem|bedtime story", re.I)
def keep_title(t, ls, mo):
    if not t or not (240 <= ls <= 4 * 3600): return False
    if sum(1 for c in t if ord(c) < 128) / max(1, len(t)) < 0.9: return False
    if EXC.search(t) or EXC2.search(t) or EXC3.search(t) or NONENG.search(t): return False
    return bool(TOPIC.search(t)) and bool(NICHE.search(t))

table = {}
# A: search sample
for r in filtered:
    t = r['title'].strip(); mo = r.get('age_months') or months(r['age'])
    if not keep_title(t, r['len_s'], mo) or not mo: continue
    row = mk(t, r['views'], r['age'], r['len_s'], r['channel_id'], r['id'], 'search', {'queries': r['queries']})
    row['in_A_core'] = 0.25 <= mo <= 24
    row['in_B_core'] = False
    table[r['id']] = row
# B: upload sample (in-space channels, all recent long-form uploads)
nB = 0
for cid, p in profiles.items():
    if (p['niche_share'] or 0) < 0.5 and p['handle'] not in CLONE and p['handle'] not in CRAFT: continue
    for v in p['recent']:
        t = (v.get('title') or '').strip(); ls = len_s(v.get('len')); mo = months(v.get('age'))
        if v.get('views') is None or mo is None: continue
        if not keep_title(t, ls, mo): continue
        key = v.get('id') or (cid + '|' + t)
        core = (14 / 30.4) <= mo <= 12
        if key in table:
            table[key]['source'] = 'search+uploads'; table[key]['in_B_core'] = core and table[key]['breakout'] is not None
            continue
        row = mk(t, v['views'], v['age'], ls, cid, v.get('id'), 'uploads')
        row['in_A_core'] = False; row['in_B_core'] = core and row['breakout'] is not None
        table[key] = row; nB += 1
rows = list(table.values())
print('rows', len(rows), 'A_core', sum(r['in_A_core'] for r in rows), 'B_core', sum(r['in_B_core'] for r in rows),
      'channels', len(set(r['channel_key'] for r in rows)), file=sys.stderr)

# ------------------------------------------------------------------ performance percentiles
def pct_rank(vals):
    s = sorted(vals); n = len(s)
    import bisect
    return lambda x: (bisect.bisect_left(s, x) + bisect.bisect_right(s, x)) / 2 / n

def assign(sample, key):
    sub = [r for r in rows if r[key]]
    bo = [r['breakout'] for r in sub if r['breakout'] is not None]
    pr_b = pct_rank(bo); pr_v = pct_rank([r['views_per_month'] for r in sub])
    vps = [r['views_per_sub'] for r in sub if r['views_per_sub'] is not None]; pr_s = pct_rank(vps)
    for r in sub:
        r[f'pct_{sample}'] = round(pr_b(r['breakout']) if r['breakout'] is not None else pr_v(r['views_per_month']), 4)
        r[f'pct_{sample}_metric'] = 'breakout' if r['breakout'] is not None else 'views_per_month'
        r[f'pct_{sample}_vpm'] = round(pr_v(r['views_per_month']), 4)
        r[f'pct_{sample}_vps'] = round(pr_s(r['views_per_sub']), 4) if r['views_per_sub'] is not None else None
    return sub
A = assign('A', 'in_A_core'); B = assign('B', 'in_B_core')
for r in rows:
    r['top_decile_A'] = r.get('pct_A', 0) >= 0.9 if r['in_A_core'] else None
    r['top_decile_B'] = r.get('pct_B', 0) >= 0.9 if r['in_B_core'] else None

# ------------------------------------------------------------------ stats
def boot_lift(sub, pred, pkey, B_ITER=400):
    """channel-clustered bootstrap of P(top decile | pred) / P(top decile)."""
    by = collections.defaultdict(lambda: [0, 0, 0, 0])   # f&top, f, top, all
    for r in sub:
        top = r[pkey] >= 0.9; f = pred(r)
        a = by[r['channel_key']]; a[0] += f and top; a[1] += f; a[2] += top; a[3] += 1
    M = np.array(list(by.values()), dtype=float)
    if M[:, 1].sum() == 0: return None, None
    idx = np.random.randint(0, len(M), size=(B_ITER, len(M)))
    S = M[idx].sum(axis=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        lift = (S[:, 0] / S[:, 1]) / (S[:, 2] / S[:, 3])
    lift = lift[np.isfinite(lift)]
    return round(float(np.percentile(lift, 10)), 2), round(float(np.percentile(lift, 90)), 2)

def cell(sub, pred, pkey='pct', alt=True):
    s = [r for r in sub if pred(r)]
    n = len(s)
    if n == 0: return {'n': 0}
    top = [r for r in s if r[pkey] >= 0.9]; mid = [r for r in s if 0.4 <= r[pkey] <= 0.6]
    ptop = len(top) / n
    lo, hi = boot_lift(sub, pred, pkey)
    out = {'n': n, 'channels': len(set(r['channel_key'] for r in s)), 'top_channels': len(set(r['channel_key'] for r in top)),
           'p_top': round(ptop, 3), 'lift': round(ptop / 0.1, 2), 'lift_p10': lo, 'lift_p90': hi,
           'share_of_top': None, 'median_pct': round(st.median(r[pkey] for r in s), 3),
           'median_views': int(st.median(r['views'] for r in s)),
           'median_breakout': (round(st.median([r['breakout'] for r in s if r['breakout'] is not None]), 2) if any(r['breakout'] is not None for r in s) else None),
           'clone_share': round(sum(1 for r in s if r['group'] in ('clone_listed', 'mass_producer')) / n, 2),
           'recent_3mo_share': round(sum(1 for r in s if (r['age_months'] or 99) <= 3) / n, 2)}
    if alt:
        for k in ('vpm', 'vps'):
            ss = [r for r in s if r.get(pkey + '_' + k) is not None]
            out['p_top_' + k] = round(sum(1 for r in ss if r[pkey + '_' + k] >= 0.9) / len(ss), 3) if ss else None
    return out

stats = {'queries': queries, 'n_queries': len(queries), 'n_rows': len(rows), 'samples': {}}
for name, sub in (('A', A), ('B', B)):
    pk = 'pct_' + name
    for r in sub:
        r['pct'] = r[pk]; r['pct_vpm'] = r[pk + '_vpm']; r['pct_vps'] = r[pk + '_vps']
    topn = sum(1 for r in sub if r['pct'] >= 0.9)
    S = {'n': len(sub), 'channels': len(set(r['channel_key'] for r in sub)), 'n_top': topn,
         'metric_mix': collections.Counter(r[pk + '_metric'] for r in sub)}
    topr = [r for r in sub if r['pct'] >= 0.9]; midr = [r for r in sub if 0.4 <= r['pct'] <= 0.6]
    S['top_vs_mid'] = {
        'median_chars': [st.median(r['chars'] for r in topr), st.median(r['chars'] for r in midr), st.median(r['chars'] for r in sub)],
        'median_words': [st.median(r['n_words'] for r in topr), st.median(r['n_words'] for r in midr), st.median(r['n_words'] for r in sub)],
        'median_breakout': [st.median([r['breakout'] for r in topr if r['breakout']] or [0]), st.median([r['breakout'] for r in midr if r['breakout']] or [0])],
        'median_views': [st.median(r['views'] for r in topr), st.median(r['views'] for r in midr)],
        'median_subs': [st.median([r['subs'] for r in topr if r['subs']] or [0]), st.median([r['subs'] for r in midr if r['subs']] or [0])],
    }
    BIN = {
        'question_mark': lambda r: r['question'], 'two_sentences': lambda r: r['two_sentence'],
        'proper_noun_any': lambda r: r['n_proper'] > 0, 'proper_noun_in_first3': lambda r: r['proper_in_first3'],
        'number_digit': lambda r: r['has_number'], 'allcaps_word': lambda r: r['allcaps_word'],
        'bracket_any': lambda r: r['bracket'] is not None, 'hedge_word': lambda r: r['hedge'],
        'first_person_we_I': lambda r: r['first_person'], 'second_person_you': lambda r: r['second_person'],
        'farm_regex_hit': lambda r: r['farm_regex_hit'] is not None, 'any_power_word': lambda r: r['n_power'] > 0,
        'no_power_word': lambda r: r['n_power'] == 0, 'colon_or_dash': lambda r: bool(F_RE['label_subtitle'].search(r['title'])),
        'emoji': lambda r: r['emoji'],
    }
    for k in POWERCAT: BIN['power_' + k] = (lambda kk: (lambda r: len(r['power_words'][kk]) > 0))(k)
    S['features'] = {}
    for k, fn in BIN.items():
        c = cell(sub, fn)
        if c['n']:
            c['share_top'] = round(sum(1 for r in topr if fn(r)) / len(topr), 3)
            c['share_mid'] = round(sum(1 for r in midr if fn(r)) / len(midr), 3)
            c['share_all'] = round(c['n'] / len(sub), 3)
        S['features'][k] = c
    S['length_bins'] = {}
    for lo_, hi_ in ((0, 30), (31, 40), (41, 50), (51, 60), (61, 70), (71, 200)):
        S['length_bins'][f'{lo_}-{hi_}'] = cell(sub, lambda r, a=lo_, b=hi_: a <= r['chars'] <= b, alt=False)
    S['formula_primary'] = {k: cell(sub, lambda r, kk=k: r['formula'] == kk) for k in F}
    S['formula_any'] = {k: cell(sub, lambda r, kk=k: kk in r['formulas']) for k in F if k != 'label_topic'}
    S['curiosity'] = {k: cell(sub, lambda r, kk=k: r['curiosity'] == kk, alt=False) for k in sorted(set(r['curiosity'] for r in sub))}
    S['first3_kind'] = {k: cell(sub, lambda r, kk=k: r['first3_kind'] == kk, alt=False) for k in sorted(set(r['first3_kind'] for r in sub))}
    S['bracket_kind'] = {k: cell(sub, lambda r, kk=k: r['bracket'] == kk, alt=False) for k in sorted(set(r['bracket'] for r in sub if r['bracket']))}
    S['group'] = {k: cell(sub, lambda r, kk=k: r['group'] == kk, alt=False) for k in sorted(set(r['group'] for r in sub))}
    wc = collections.Counter(w for r in sub for v in r['power_words'].values() for w in v)
    S['power_words'] = {w: cell(sub, lambda r, ww=w: any(ww in v for v in r['power_words'].values()), alt=False) for w, n in wc.items() if n >= 20}
    fw = collections.Counter(r['farm_regex_hit'].lower() for r in sub if r['farm_regex_hit'])
    S['farm_words'] = {w: cell(sub, lambda r, ww=w: (r['farm_regex_hit'] or '').lower() == ww, alt=False) for w, n in fw.items() if n >= 10}
    # examples per formula: top 3 by pct, distinct channels, prefer <=12 months old
    ex = {}
    for k in F:
        cand = sorted([r for r in sub if r['formula'] == k or k in r['formulas']], key=lambda r: (-(r['pct']), -(r['views'])))
        seen, out = set(), []
        for r in cand:
            if r['channel_key'] in seen: continue
            seen.add(r['channel_key']); out.append({kk: r[kk] for kk in ('title', 'channel', 'subs', 'views', 'age', 'breakout', 'views_per_month', 'url', 'group')})
            if len(out) == 5: break
        ex[k] = out
    S['examples'] = ex
    stats['samples'][name] = S
    for r in sub:
        del r['pct'], r['pct_vpm'], r['pct_vps']

# ------------------------------------------------------------------ within-channel paired analysis (B core)
# Same channel, different title. Age-adjusted: within-channel regression of log(views) on log(age).
Bc = [r for r in rows if r['in_B_core']]
byc = collections.defaultdict(list)
for r in Bc: byc[r['channel_key']].append(r)
xs, ys = [], []
for c, rs in byc.items():
    if len(rs) < 5: continue
    la = [math.log(r['age_months']) for r in rs]; lv = [math.log(max(r['views'], 1)) for r in rs]
    ma, mv = sum(la) / len(la), sum(lv) / len(lv)
    xs += [a - ma for a in la]; ys += [v - mv for v in lv]
AGE_B = sum(x * y for x, y in zip(xs, ys)) / sum(x * x for x in xs)
for c, rs in byc.items():
    la = [math.log(r['age_months']) for r in rs]; lv = [math.log(max(r['views'], 1)) for r in rs]
    ma, mv = sum(la) / len(la), sum(lv) / len(lv)
    for r, a, v in zip(rs, la, lv):
        r['within_channel_index'] = round(math.exp(v - mv - AGE_B * (a - ma)), 3) if len(rs) >= 5 else None
stats['age_slope_within_channel'] = round(AGE_B, 3)

def paired(pred, min_non=3, B_ITER=600):
    ds, nF = [], 0
    for c, rs in byc.items():
        rs = [r for r in rs if r.get('within_channel_index')]
        f = [math.log(r['within_channel_index']) for r in rs if pred(r)]
        o = [math.log(r['within_channel_index']) for r in rs if not pred(r)]
        if f and len(o) >= min_non:
            ds.append(sum(f) / len(f) - sum(o) / len(o)); nF += len(f)
    if len(ds) < 3: return {'channels': len(ds), 'videos': nF}
    d = np.array(ds)
    bs = d[np.random.randint(0, len(d), size=(B_ITER, len(d)))].mean(axis=1)
    return {'channels': len(ds), 'videos': nF, 'ratio': round(float(math.exp(d.mean())), 2),
            'ratio_p10': round(float(math.exp(np.percentile(bs, 10))), 2), 'ratio_p90': round(float(math.exp(np.percentile(bs, 90))), 2),
            'win_share': round(float((d > 0).mean()), 2), 'median_ratio': round(float(math.exp(np.median(d))), 2)}

W_ = {}
W_['formula_any'] = {k: paired(lambda r, kk=k: kk in r['formulas']) for k in F if k != 'label_topic'}
W_['formula_primary'] = {k: paired(lambda r, kk=k: r['formula'] == kk) for k in F}
W_['features'] = {
    'question_mark': paired(lambda r: r['question']), 'two_sentences': paired(lambda r: r['two_sentence']),
    'proper_noun_in_first3': paired(lambda r: r['proper_in_first3']), 'proper_noun_any': paired(lambda r: r['n_proper'] > 0),
    'number_digit': paired(lambda r: r['has_number']), 'allcaps_word': paired(lambda r: r['allcaps_word']),
    'bracket_any': paired(lambda r: r['bracket'] is not None), 'hedge_word': paired(lambda r: r['hedge']),
    'first_person_we_I': paired(lambda r: r['first_person']), 'second_person_you': paired(lambda r: r['second_person']),
    'farm_regex_hit': paired(lambda r: r['farm_regex_hit'] is not None), 'any_power_word': paired(lambda r: r['n_power'] > 0),
    'colon_or_dash_or_pipe': paired(lambda r: bool(F_RE['label_subtitle'].search(r['title']))),
    'chars_le_50': paired(lambda r: r['chars'] <= 50), 'chars_le_40': paired(lambda r: r['chars'] <= 40),
    'chars_gt_60': paired(lambda r: r['chars'] > 60), 'chars_gt_70': paired(lambda r: r['chars'] > 70),
}
for k in POWERCAT: W_['features']['power_' + k] = paired(lambda r, kk=k: len(r['power_words'][kk]) > 0)
W_['curiosity'] = {k: paired(lambda r, kk=k: r['curiosity'] == kk) for k in sorted(set(r['curiosity'] for r in Bc))}
W_['first3_kind'] = {k: paired(lambda r, kk=k: r['first3_kind'] == kk) for k in sorted(set(r['first3_kind'] for r in Bc))}
W_['length_bins'] = {f'{a}-{b}': paired(lambda r, a=a, b=b: a <= r['chars'] <= b) for a, b in ((0, 30), (31, 40), (41, 50), (51, 60), (61, 70), (71, 200))}
fw = collections.Counter(r['farm_regex_hit'].lower() for r in Bc if r['farm_regex_hit'])
W_['farm_words'] = {w: paired(lambda r, ww=w: (r['farm_regex_hit'] or '').lower() == ww) for w, n in fw.items() if n >= 15}
wc = collections.Counter(w for r in Bc for v in r['power_words'].values() for w in v)
W_['power_words'] = {w: paired(lambda r, ww=w: any(ww in v for v in r['power_words'].values())) for w, n in wc.items() if n >= 25}
# the same paired test restricted to craft-like channels (not clone-listed, not mass producers)
craftlike = lambda r: r['group'] in ('craft_listed', 'other')
W_['formula_any_noncl'] = {}
for k in F:
    if k == 'label_topic': continue
    ds = []
    for c, rs in byc.items():
        rs = [r for r in rs if r.get('within_channel_index') and craftlike(r)]
        f = [math.log(r['within_channel_index']) for r in rs if k in r['formulas']]
        o = [math.log(r['within_channel_index']) for r in rs if k not in r['formulas']]
        if f and len(o) >= 3: ds.append(sum(f) / len(f) - sum(o) / len(o))
    W_['formula_any_noncl'][k] = {'channels': len(ds), 'ratio': round(math.exp(sum(ds) / len(ds)), 2) if ds else None}
W_['bracket_kind'] = {k: paired(lambda r, kk=k: r['bracket'] == kk) for k in sorted(set(r['bracket'] for r in Bc if r['bracket']))}
# length within non-clone channels only (clone channels use long template titles)
def paired_sub(pred, keep):
    ds = []
    for c, rs in byc.items():
        rs = [r for r in rs if r.get('within_channel_index') and keep(r)]
        f = [math.log(r['within_channel_index']) for r in rs if pred(r)]
        o = [math.log(r['within_channel_index']) for r in rs if not pred(r)]
        if f and len(o) >= 3: ds.append(sum(f) / len(f) - sum(o) / len(o))
    if len(ds) < 3: return {'channels': len(ds)}
    d = np.array(ds); bs = d[np.random.randint(0, len(d), size=(600, len(d)))].mean(axis=1)
    return {'channels': len(ds), 'ratio': round(float(math.exp(d.mean())), 2), 'ratio_p10': round(float(math.exp(np.percentile(bs, 10))), 2),
            'ratio_p90': round(float(math.exp(np.percentile(bs, 90))), 2), 'win_share': round(float((d > 0).mean()), 2)}
W_['length_bins_nonclone'] = {f'{a}-{b}': paired_sub(lambda r, a=a, b=b: a <= r['chars'] <= b, craftlike) for a, b in ((0, 30), (31, 40), (41, 50), (51, 60), (61, 70), (71, 200))}
W_['length_bins_clone'] = {f'{a}-{b}': paired_sub(lambda r, a=a, b=b: a <= r['chars'] <= b, lambda r: not craftlike(r)) for a, b in ((0, 40), (41, 50), (51, 60), (61, 70), (71, 200))}
W_['features_nonclone'] = {
    'question_mark': paired_sub(lambda r: r['question'], craftlike), 'two_sentences': paired_sub(lambda r: r['two_sentence'], craftlike),
    'farm_regex_hit': paired_sub(lambda r: r['farm_regex_hit'] is not None, craftlike), 'bracket_any': paired_sub(lambda r: r['bracket'] is not None, craftlike),
    'proper_noun_in_first3': paired_sub(lambda r: r['proper_in_first3'], craftlike), 'power_fear_shock': paired_sub(lambda r: len(r['power_words']['fear_shock']) > 0, craftlike),
    'chars_le_40': paired_sub(lambda r: r['chars'] <= 40, craftlike), 'chars_41_50': paired_sub(lambda r: 41 <= r['chars'] <= 50, craftlike),
}
W_['n_channels_B'] = len([c for c, rs in byc.items() if len(rs) >= 5])
stats['within_channel'] = W_

json.dump(rows, open(OUT_T, 'w'), ensure_ascii=False, indent=0, default=str)
json.dump(stats, open(OUT_S, 'w'), ensure_ascii=False, indent=1, default=str)
print('ok', file=sys.stderr)
