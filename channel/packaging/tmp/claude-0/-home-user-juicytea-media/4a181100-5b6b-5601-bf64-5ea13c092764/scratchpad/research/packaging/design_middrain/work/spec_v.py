import json,sys
titles={1:"Where Does Hawaii Begin? (Not at Sea Level)",
        2:"Hawaii Is Only the Summit. You Can't See the Rest.",
        3:"Hawaii Is Only the Summit. We Measured the Rest.",
        4:"Hawaii's Volcanoes Go Down Farther Than They Go Up"}
tag=sys.argv[1]; ids=[int(x) for x in sys.argv[2].split(',')] if len(sys.argv)>2 else [1,2,3,4]
spec={"candidates":[{"id":f"c{i}","thumb":f"{tag}/cand_{i}.jpg" if tag!="cur" else f"../cand_{i}.jpg","title":titles[i],"channel":"Myth Juice",
      "views":"52 views","age":"1d ago","duration":"13:05","avatar":"../../feedsim/ours_avatar.jpg"} for i in ids],
      "hosts":"../../refs/hosts/hosts.json#hawaii","now_playing":"34Ojnyi9xLw","seed":2,"n":{"home":6,"upnext":10,"sidebar":10}}
json.dump(spec,open(f'/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/packaging/design_middrain/work/spec_{tag}.json','w'),indent=1)
