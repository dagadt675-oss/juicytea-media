#!/usr/bin/env python3
"""el_voices.py NAME : list ElevenLabs voices whose name contains NAME (account voices + shared library). Prints name, id, labels; never the key."""
import json, os, sys, urllib.request, urllib.parse
k = os.environ.get('ELEVENLABS_API_KEY', '').strip() or sys.exit('ELEVENLABS_API_KEY not set')
name = sys.argv[1].lower()
def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'xi-api-key': k}), timeout=30))
try:
    for v in get('https://api.elevenlabs.io/v2/voices?page_size=100&search=' + urllib.parse.quote(name)).get('voices', []):
        print('ACCOUNT', v['name'], v['voice_id'], v.get('category'), json.dumps(v.get('labels', {})))
except Exception as e: print('account lookup failed:', type(e).__name__, getattr(e, 'code', ''))
try:
    for v in get('https://api.elevenlabs.io/v1/shared-voices?page_size=30&search=' + urllib.parse.quote(name)).get('voices', [])[:30]:
        print('SHARED', v['name'], v['voice_id'], '| owner', v.get('public_owner_id', '')[:8], '|', v.get('accent'), v.get('age'), v.get('gender'), v.get('use_case'), '| uses', v.get('usage_character_count_1y') or v.get('cloned_by_count'), '|', (v.get('description') or '')[:110].replace('\n', ' '))
except Exception as e: print('shared lookup failed:', type(e).__name__, getattr(e, 'code', ''))
