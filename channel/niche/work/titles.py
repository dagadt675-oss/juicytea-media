import json,re,statistics as st
c=json.load(open('../../../comp/chans.json'))
CLONE='''contouratlas hiddenprovinces DrainedAtlas highgroundatlas EarthTipping originofeverydaythings SignalNonsense MapTally GreenstoneEurope RedlineTerritory oscar-campbell-g6n theprimalyears WatchOddlyTold Strangeography BrightSideDarkSecrets waterlineearth vanishingmaps PanicMaps BelowTheMapHQ GeoMetriics UnknownAmericaHQ Mapredacted statesXplained UnderTheAtlasYT GeorgePembroke-j2e WaterlineAtlas BareEarthHQ TheReasonMap MapWhysTV NorthernGrounds CANADA_DISCOVERIES dylan-sinclair-canada Waterwakee TheDrainedMap AtlasBeyondStudio Geospacy TheSilentSpeculation GeoWhatIf-74 TheHiddenMerica HiddenHawaii0 justaboutearth earthdynamics-p4k deeppastearth geographyscoped urbanxplain1 mrtruestates TheHiddenStates-h6t HiddenonEarth-yt Acrosstheglobechannel Submerged-History-YT HiddenHistory-02 MystralTV ExplorerVaultOfficial BuriedSignalYT theultimatefining UnchartedDepthsOfficial ThePlanetUnseen GlobeHaven geographyunfold'''.split()
CRAFT='''mr.scienceYT xverse.studios FossilVideos Paintify7 itscuriositydude TheLastDay01 WhereTheyStood Earthyphus AstrumEarth GeographyByGeoff RealLifeLore eons AtlasPro1 besmart halfasinteresting Wendoverproductions kurzgesagt pbsterra pwhitewick flaggeography ExtinctZoo'''.split()
def vids(hs):
    out=[]
    for h in hs:
        v=c.get('/@'+h)
        if not v: print('missing',h); continue
        for x in v.get('videos',[]):
            ln=x.get('len') or '0'
            s=sum(int(p)*60**i for i,p in enumerate(reversed(ln.split(':'))) if p.isdigit())
            if s>=360: out.append((h,x['title'],x['views'],x['age']))
    return out
A=vids(CLONE); Bv=vids(CRAFT)
print('titles: clone/template',len(A),'from',len(CLONE),'channels; craft',len(Bv),'from',len(CRAFT))
fam={
 'we drained / drained / drain':r'\bdrain',
 'hidden / hiding / hides':r'\bhid(den|ing|es)\b',
 'nobody / no one / never':r'\bnobody\b|\bno one\b|\bnever\b',
 'secret(s)':r'\bsecret',
 'found / discovered / revealed':r'\bfound\b|\bdiscover|\breveal',
 'without water/ice':r'without (water|ice)',
 'what if':r'\bwhat if\b',
 "here's what / what's":r"here.s what|what.s\b|what was",
 'bottom / beneath / under(neath)':r'\bbottom\b|\bbeneath\b|\bunder(neath)?\b',
 'really / actually / truth / real':r'\breally\b|\bactually\b|\btruth\b|\breal\b',
 'scientists / NASA / experts':r'scientist|\bnasa\b|expert|geologist',
 'shocking / terrifying / insane / strange':r'shock|terrif|insane|strange|creep|disturb|horrif|weird',
 'sleep / documentary':r'sleep|documentary',
 'starts "When"':r'^when\b',
 'starts "Why"':r'^why\b',
 'starts "How"':r'^how\b',
 'contains "Every"':r'\bevery\b',
 'question mark':r'\?',
 'a number':r'\d',
 'ALL-CAPS word (4+ letters)':None,
 'second person you/your':r'\byou(r|.d|.re)?\b',
 'nothing about / isn\'t really / no longer makes sense':r"nothing about|isn.t really|no longer makes sense|isn.t what",
}
def has(t,rx):
    if rx is None: return bool(re.search(r'\b[A-Z]{4,}\b',t))
    return bool(re.search(rx,t,re.I))
print(f"{'family':45} {'clone%':>7} {'craft%':>7}")
for k,rx in fam.items():
    a=100*sum(has(t,rx) for _,t,_,_ in A)/len(A); b=100*sum(has(t,rx) for _,t,_,_ in Bv)/len(Bv)
    print(f"{k:45} {a:7.0f} {b:7.0f}")
la=[len(t) for _,t,_,_ in A]; lb=[len(t) for _,t,_,_ in Bv]
print('median title length chars clone',st.median(la),'craft',st.median(lb))
wa=[len(t.split()) for _,t,_,_ in A]; wb=[len(t.split()) for _,t,_,_ in Bv]
print('median words clone',st.median(wa),'craft',st.median(wb))
json.dump({'A':A,'B':Bv},open('titles_sets.json','w'))
