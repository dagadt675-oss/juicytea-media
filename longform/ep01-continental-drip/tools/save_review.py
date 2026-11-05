#!/usr/bin/env python3
"""save_review.py OUT_DIR RUN_ID [RUN_ID ...]
Saves everything the review agents have produced so far, so nothing is lost if the session stops:
  OUT_DIR/<run>__<label>.json   every finished agent's structured result (from the workflow journal)
  OUT_DIR/partial__<run>__<label>.md   the latest notes of agents still running (their last assistant messages)
  OUT_DIR/SUMMARY.md            one readable list: every finding / risk with time, severity and fix, per agent
Idempotent: rewrites the files each run."""
import glob, json, os, re, sys

W = '/root/.claude/projects/-home-user-juicytea-media/4a181100-5b6b-5601-bf64-5ea13c092764/subagents/workflows'
def slug(s): return re.sub(r'[^A-Za-z0-9]+', '_', s).strip('_')[:60]
def mmss(t):
    try: t = float(t); return '%d:%05.2f' % (int(t) // 60, t - 60 * (int(t) // 60))
    except Exception: return str(t)

def main():
    out = sys.argv[1]; runs = sys.argv[2:]
    os.makedirs(out, exist_ok=True)
    for f in glob.glob(os.path.join(out, 'partial__*.md')): os.remove(f)
    summary = ['# Review round 6: what the agents found (auto-saved)\n']
    for run in runs:
        d = os.path.join(W, run); j = os.path.join(d, 'journal.jsonl')
        if not os.path.exists(j): continue
        started, results = {}, {}
        for line in open(j):
            try: e = json.loads(line)
            except Exception: continue
            if e.get('type') == 'started': started[e['agentId']] = e.get('label', e['agentId'])
            elif e.get('type') == 'result': results[e['agentId']] = e.get('result')
        summary.append(f'\n## {run}: {len(results)} finished, {len(set(started) - set(results))} running\n')
        for aid, res in results.items():
            label = started.get(aid, aid)
            json.dump({'run': run, 'agent': aid, 'label': label, 'result': res}, open(os.path.join(out, f'{run}__{slug(label)}.json'), 'w'), indent=1)
            summary.append(f'\n### {label}\n')
            if not isinstance(res, dict): summary.append(f'(no structured result: {str(res)[:300]})\n'); continue
            for f in res.get('findings', []):
                summary.append(f"- **{f.get('id')}** {mmss(f.get('t0'))}-{mmss(f.get('t1'))} [{f.get('severity')}/{f.get('confidence')}, {f.get('category')}] {f.get('what_viewer_sees')}\n  - cause: {f.get('likely_cause')}\n  - fix: {f.get('suggested_fix')} ({f.get('code_location')})\n")
            for v in res.get('verdicts', []):
                summary.append(f"- verdict **{v.get('id')}**: {v.get('verdict')} [{v.get('severity')}] {mmss(v.get('t0'))}-{mmss(v.get('t1'))}: {v.get('reason')}\n  - fix: {v.get('fix')} ({v.get('code_location')})\n")
            for m in res.get('missed', []):
                summary.append(f"- missed **{m.get('id')}** {mmss(m.get('t0'))} [{m.get('severity')}] {m.get('what_viewer_sees')}\n  - fix: {m.get('suggested_fix')} ({m.get('code_location')})\n")
            if 'drop_risks' in res:
                summary.append(f"- would leave at: {res.get('would_leave_at')}\n- top 3: {json.dumps(res.get('top3'))}\n")
                for r in res['drop_risks']:
                    summary.append(f"- risk {mmss(r.get('t0'))}-{mmss(r.get('t1'))} [{r.get('severity')}, {r.get('fix_type')}] {r.get('why')}\n  - fix: {r.get('fix')}\n")
                for p in res.get('fatigue_points', []): summary.append(f"- fatigue {mmss(p.get('t'))}: {p.get('why')}\n")
            if 'issues' in res:
                for r in res['issues']: summary.append(f"- audio {mmss(r.get('t0'))}-{mmss(r.get('t1'))} [{r.get('severity')}, {r.get('kind')}] {r.get('evidence')}\n  - fix: {r.get('fix')}\n")
                summary.append(f"- voice fatigue: {res.get('voice_fatigue')}\n")
            if 'fixes' in res:
                summary.append(f"- verdict: {res.get('verdict')}\n")
                for r in res['fixes']: summary.append(f"- #{r.get('rank')} {mmss(r.get('t0'))}-{mmss(r.get('t1'))} [{r.get('effort')}, votes {r.get('votes')}, new voice: {r.get('needs_new_voice')}] {r.get('problem')}\n  - fix: {r.get('fix')}\n")
            if res.get('intended_notes'): summary.append(f"- notes: {res['intended_notes']}\n")
        for aid in set(started) - set(results):
            label = started[aid]; tp = os.path.join(d, f'agent-{aid}.jsonl'); texts = []
            if os.path.exists(tp):
                for line in open(tp):
                    try: e = json.loads(line)
                    except Exception: continue
                    msg = e.get('message') or {}
                    if msg.get('role') != 'assistant': continue
                    for c in msg.get('content') or []:
                        if isinstance(c, dict) and c.get('type') == 'text' and c.get('text', '').strip(): texts.append(c['text'].strip())
            with open(os.path.join(out, f'partial__{run}__{slug(label)}.md'), 'w') as fh:
                fh.write(f'# {label} (still running; latest notes)\n\n' + '\n\n---\n\n'.join(texts[-8:]) + '\n')
    open(os.path.join(out, 'SUMMARY.md'), 'w').write(''.join(summary))
    print('saved', len(glob.glob(os.path.join(out, '*.json'))), 'results,', len(glob.glob(os.path.join(out, 'partial__*.md'))), 'partials')

if __name__ == '__main__':
    main()
