import json,sys
s=json.load(open(sys.argv[1]))
for name in sys.argv[2].split(','):
    S=s['samples'][name]
    print('=====',name,'n',S['n'],'channels',S['channels'],'top',S['n_top'],S['metric_mix'])
    print('top_vs_mid',S['top_vs_mid'])
    def tab(d, keys=None, minn=15):
        items=sorted(d.items(), key=lambda kv: -(kv[1].get('lift') or 0))
        for k,c in items:
            if c.get('n',0)<minn: continue
            print(f"  {k:28s} n={c['n']:5d} ch={c['channels']:4d} topch={c['top_channels']:3d} ptop={c['p_top']:.3f} lift={c['lift']:.2f} [{c['lift_p10']},{c['lift_p90']}] medBO={c['median_breakout']} medV={c['median_views']} clone={c['clone_share']} rec3={c['recent_3mo_share']}"
                  + (f" vpm={c.get('p_top_vpm')} vps={c.get('p_top_vps')}" if 'p_top_vpm' in c else '')
                  + (f" top%={c.get('share_top')} mid%={c.get('share_mid')} all%={c.get('share_all')}" if 'share_top' in c else ''))
    for sec in sys.argv[3].split(','):
        print('--',sec); tab(S[sec])
