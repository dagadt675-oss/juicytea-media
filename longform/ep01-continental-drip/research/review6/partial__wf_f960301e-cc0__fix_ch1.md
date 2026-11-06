# fix ch1 (still running; latest notes)

The quote bar now fades in and sits between Greenland and Africa, with all five tips fully visible. Next, the magnifier (S2-7):

---

The magnifier now fades in on the cut (F4771-4774) and fades out in the wide (F4848-4856) instead of popping. Before the last renders, let me remove the temporary debug instrumentation.

---

Debug code is gone, the module parses, and only `ch1.js` changed. Now S2-8 (byline ring):

---

The run-to-hit pose change happens exactly while the wave crest covers him (F3704-3706), so it reads as the impact rather than a snap. Let me review the complete diff against the original module.

---

The diff contains exactly the intended changes. Let me compute the exact scene ranges and their frames and chunks for the report.

---

All changes stay inside ch1 scenes. Let me scan every test-render log for scene errors or coverage gaps.

---

All renders are clean. As a last visual check, let me compare a close-up frame before and after, since the planet under the hero now carries the run's roll.

---

The close-up now shows him standing on land, consistent with where the rolled planet stopped in the wide shot. Nothing reads oddly. Let me collect final line numbers for the report.
