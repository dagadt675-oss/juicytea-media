# fix ch2 (still running; latest notes)

Now S4-2/S4-1. First a `facing` helper on the ch2 projector (ch2_lib.js), then the drop loop and the hero hand-off.

---

Now S4-3 (montage flash counts only cuts already passed).

---

Now S4-6 (soft limb occlusion for the tetra corner glows).

---

Now S4-5/S4-12. First the juiceStamp options in ch2_lib.js (opt-out of the restart fade, optional plate colour; defaults unchanged for the other caller).

---

Now the stamp flight/landing in ch2.js.

---

All edits are in. Syntax check of the modified module files before rendering:

---

Checking whether any other module imports ch2_lib.js (my lib edits are additive with unchanged defaults, but I want to be sure).

---

Only ch2.js uses ch2_lib.js, and the existing FALSE stamp call keeps its defaults. Starting test renders, first the G→H cut (S3-1/S3-2): frames 7085-7184.
