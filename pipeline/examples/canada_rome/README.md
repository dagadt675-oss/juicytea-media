# Part of Canada is further south than Rome

Silent style-kit proof. The picture is drawn with `pipeline/style/gold.py`. The renderer does not call espeak or ElevenLabs, and it does not burn karaoke.

```bash
python3 pipeline/make_short.py pipeline/specs/canada_rome.yaml --preset final --out pipeline/out/canada_rome
```

The spoken lines are reconstructed. YouTube's caption track for the gold Short came back empty, so `say` is not a transcript. The geography is Middle Island in Lake Erie (41.6814°N), about 24 km south of Rome's latitude. It is not Point Pelee.

`timeline.json` has the beat clock. Leave y 0.64–0.72 empty for a later caption pass.

The camera pushes in once, then eases or cuts. It does not sway. Measured notes and the 7.5/10 storyboard score are in `pipeline/style/gold_canada.md`.
