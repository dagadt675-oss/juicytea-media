# finish ch5a (still running; latest notes)

The cut is now seamless: 0.33 at 20682 versus 0.29-0.34 around it (the master spiked to 2.28). Let me view the diff image to be sure the ripple doesn't reset.

---

`EXCL` is now unused in ch5a.js; I'll drop it from the import, then queue the final batch.

---

While the final batch renders, let me double-check which scenes overlap which chunks, to report exact re-render ranges (D, the Bacon insert, is the only scene whose frames cannot change).

---

All seven chunks 40-46 (frames 18000-21149) need re-rendering. Let me wait for the final batch.

---

All four exited 0, with no scene errors logged. First the K-scene tick check (master spiked at 19804).

---

K's base-land ticks are gone (19804: master 1.27 → test 0.47; the small 0.59 at 19814 is the counter digit). Now the slam with the shifted crumple marks.

---

The crumple ridges now sit entirely on the Asian land above the contact, and India's tip is pressed into the coast. Now the O-scene aim arrows and the P-scene scars with the reworked path drawing.

---

Nothing is running, the last test render exited 0, and no scene errors were logged. Let me collect line numbers for the report.
