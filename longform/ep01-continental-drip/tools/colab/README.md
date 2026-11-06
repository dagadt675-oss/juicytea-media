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

## Measured on 2026-11-06 (Colab L4, 12 vCPU, 52 GB)
- Setup (Playwright Chromium 1.63 + NVIDIA EGL ICD): about 1 minute; `glcheck.cjs` printed `ANGLE (NVIDIA Corporation, NVIDIA L4/PCIe/SSE2, OpenGL ES 3.2)`.
- One 450-frame chunk (1920x1080, CRF 12): 32 s on the GPU, against 6-12 minutes on the 4-CPU box with SwiftShader (15-20x).
- Picture: identical to the eye; mean absolute difference 0.6-1.3/255 against the SwiftShader frames (sub-pixel anti-aliasing only).
- Cost: 1.94 compute units per hour while the L4 session runs; stop the session (`colab stop -s mj`) as soon as the chunks are downloaded.
- `colab upload` returned HTTP 500 for a 343 MB file: upload in 40 MB parts (`upload_parts.sh`) and `cat` them on the VM, md5-verified.

## Handing a large file to the owner (2026-11-06)
`colab drivemount` fails on a headless session (the Drive mount needs the notebook's permission pop-up), and the in-chat file limit is
400 MiB. What worked: upload the master to a CPU session in 40 MB parts (`upload_master.sh`, md5-checked on the VM), then give the
owner `colab url -s up`; in that notebook a two-line cell mounts Drive interactively and copies `/content/mythjuice/*` to My Drive.
A CPU session costs about 0.08 compute units per hour; stop it once the owner has the files.
