# Myth Juice: start here (for any assistant in this repo)

Myth Juice is a faceless YouTube channel (map, geography and earth myth-busting, true stories about places). This repo holds the film engine, every episode project and the rules.

## Before any work
- Read the whole playbook: PLAYBOOK.md (read-first list, owner rules, research, topic, facts, story, hook, competitive edge), PLAYBOOK_craft.md (pacing, visuals, text, humour, audio, ending, packaging) and PLAYBOOK_production.md (Shorts, pipeline, QC, delivery, superseded rules). Then read the newest entries of LESSONS_LOG.md.
- Playbook files must be read in full; if a read says PARTIAL or is truncated, read the rest with an offset.
- Follow the owner's rules; they beat every other rule, brief or benchmark. Where engine/ENGINE.md, an ep01 research checklist or a brief differs from the playbook, the playbook wins.

## Owner rules (non-negotiable)
- Never publish, upload, schedule or post anything, and make no visible channel change, without the owner's explicit OK.
- The owner asked on 2026-11-08 to save all good work in this repo, so commit and push. The repo is public (checked 2026-11-08); the owner was advised to make it private. Until then, never push secrets, personal data, other channels' thumbnails or unreleased video.
- Never print, log, write or commit API keys, tokens or passwords. The ElevenLabs key comes only from ELEVENLABS_API_KEY, filled from a secrets file outside the repo.
- Never mention AI in videos, titles, descriptions, thumbnails, comments or on the channel.
- Billing and paid settings only together with the owner. Ask before writing to his Google Drive.
- ElevenLabs sign-in only with the account the owner designates, never with the owner's other Google accounts. No random gateways, proxies or foreign mods.
- Storytelling first; only about 6-10 big vivid numbers per long-form; funny scenes and real animation.
- No false claims. No emojis. No sources on screen (credits in the description only).
- Narration: ElevenLabs "Rodney - Clear Educator" (eY2VJs4Gi8QKG2RV01sS, eleven_v4); never Brian (pass the voice explicitly: tts.py still defaults to Brian).
- Exactly 7 Shorts per long-form, rebuilt (never clipped), each with hook, payoff and seamless loop. Shorts need not look or play like the long-form; never change the long-form because of the Shorts.

## Where things live
- engine/: the shared film engine (ENGINE.md, ASSETS.md, tools/ for render, mix, TTS, QC, Colab). The playbook wins where ENGINE.md differs.
- longform/<ep>/: one folder per episode, with README.md (status and file map), research/ (context, brief, facts, reviews), engine/ or lab/ (scenes), tools/, release/ and shorts/.
- PLAYBOOK.md, PLAYBOOK_craft.md, PLAYBOOK_production.md and LESSONS_LOG.md at the repo root.

## After every task
1. Add what worked to the playbook's DO lists and what failed to DONT, with evidence path and tag.
2. Add a dated entry to LESSONS_LOG.md.
3. Commit and push (the owner asked for everything good to be saved in the repo).

Never commit secrets or large media (videos, renders, chunks, raw DEM, models); hand media to the owner outside git.

Reply to the owner in Hungarian, short and useful.
