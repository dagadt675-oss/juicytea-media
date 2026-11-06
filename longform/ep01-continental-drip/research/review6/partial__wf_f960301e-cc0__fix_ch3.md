# fix ch3 (still running; latest notes)

Now the kids page (fan's pill-on-empty-desk claim at 426.5 and the strategist's kids claim at 427.9-432).

---

Confirmed: frames 12794-12796 show the "1918" pill alone on the empty desk before the page drops in. Now the kids themselves (strategist's claim).

---

The kids scale in over ~14 frames with a stagger, so "appear in a single frame" is false. Let me check the "snap into a new pose" claim at about 7:11.9.

---

S5-4 confirmed: the page-237 strip on the left at 12349 is gone at 12350. Now S5-7 (the rushed lunge into figure 5a).

---

S5-7 confirmed: the page sits still until 12471, then lunges to about 2x zoom by the cut at 12492 while the outline draws (energy peaks at 27). Now S5-8 (pills over printed text).

---

S5-8 confirmed: "FIGURE 1." and "N." read through the Figure 1 pill, and the body text reads through the 1899 pill. Now S5-9 (board pins and the red X).

---

Let me check how `globeShot` and the globe overlay work before deciding on the S5-6 fix.

---

The globe has a `refreshOverlay()` hook and `globeShot` has a `pre` callback, so animating the overlay is possible. Let me check the rumble cue's sound to size the twitch to it.
