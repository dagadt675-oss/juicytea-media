# Myth Juice: start here (for any assistant in this repo)

Myth Juice is a faceless YouTube channel (map, geography and earth myth-busting, true stories about places). This repo holds the film engine, every episode project and the rules.

## Before any work
- Read PLAYBOOK.md (DO and DONT rules with evidence) and the newest entries of LESSONS_LOG.md.
- Follow the owner's rules; they beat every other rule, brief or benchmark.

## Owner rules (non-negotiable)
- Never publish, upload, schedule or post anything, and make no visible channel change, without the owner's explicit OK.
- Never print, log, write or commit API keys, tokens or passwords. The ElevenLabs key comes only from ELEVENLABS_API_KEY, filled from a secrets file outside the repo.
- Never mention AI in videos, titles, descriptions, thumbnails, comments or on the channel.
- Billing and paid settings only together with the owner. Ask before writing to his Google Drive.
- ElevenLabs sign-in only with the account the owner designates. No random gateways, proxies or foreign mods.
- No false claims. No emojis. No sources on screen (credits in the description only).
- Narration: ElevenLabs "Rodney - Clear Educator" (eY2VJs4Gi8QKG2RV01sS, eleven_v4); never Brian.
- Exactly 7 Shorts per long-form, rebuilt (never clipped), each with hook, payoff and seamless loop.

## Where things live
- engine/: the shared film engine (ENGINE.md, ASSETS.md, tools/ for render, mix, TTS, QC, Colab).
- longform/<ep>/: one folder per episode, with README.md (status and file map), research/ (context, brief, facts, reviews), engine/ or lab/ (scenes), tools/, release/ and shorts/.
- PLAYBOOK.md and LESSONS_LOG.md at the repo root.

## After every task
1. Add what worked to PLAYBOOK.md DO and what failed to DONT, with evidence path and tag.
2. Add a dated entry to LESSONS_LOG.md.
3. Commit and push.

Never commit secrets or large media (videos, renders, chunks, raw DEM, models); hand media to the owner outside git.

Reply to the owner in Hungarian, short and useful.
