"""Distinctiveness gate: python3 gate.py thumb.jpg [...]
Prints colour shares and mean feature distance to each competitor cluster (refs/ thumbs, groups.json).
Pass: tan<=10%, red<=3%, blue<=45%; mean feature distance to A_drain_clones and to D_template_farms >= 11.0
(drain clones sit at 8.7 from their own cluster, small craft thumbnails at 11.7)."""
import json,sys,numpy as np
sys.argv=[a for a in sys.argv]
exec(open('/tmp/claude-0/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/scratchpad/research/niche/work/sim_lib.py').read())
