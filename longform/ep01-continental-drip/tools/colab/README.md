# Rendering the film engine on a Colab GPU (Colab CLI)

The engine (headless Chromium + three.js) runs on the NVIDIA GPU of a Colab L4 instead of SwiftShader on CPUs.
Control is headless through the official `google-colab-cli` (`pip install google-colab-cli`); the one-time Google login
(`colab --auth oauth2 sessions` prints a URL, the owner pastes back the code) is done by the owner, never stored in the repo.

1. `colab new -s mj --gpu L4`
2. upload: `tar -cf engine_www.tar www` (from `engine/`), then `colab upload -s mj engine_www.tar /content/engine_www.tar`,
   `engine/render.cjs` -> `/content/mj/engine/render.cjs`, `tools/render_chunks.py` -> `/content/mj/tools/render_chunks.py`,
   `vm_setup.sh`, `vm_render.sh` -> `/content/`
3. `bg.sh "bash /content/vm_setup.sh" /content/setup.log` (Playwright Chromium, NVIDIA EGL ICD, WebGL renderer check: must print NVIDIA)
4. `bg.sh "bash /content/vm_render.sh '' 3" /content/render.log` (all 68 chunks, 3 in parallel; `GPU=1` makes render.cjs use
   ANGLE on EGL, assert the NVIDIA renderer and discard one warm-up frame)
5. poll with `cx.sh "tail -3 /content/render.log"` every few minutes (an idle client lets Colab reclaim the VM)
6. `colab download -s mj /content/out/c_000NN.mp4 ...`, verify frame counts (450; 179 for chunk 67), swap into `chunks/`.
Never `| head` after a long remote command (SIGPIPE), always give `colab exec` an explicit `--timeout`, start long jobs detached (`run_bg.py`).
