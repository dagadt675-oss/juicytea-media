#!/bin/bash
# start_redo.sh "<chunk list>" : wait until the main chunk runners exit, then re-render the listed chunks into chunks/redo
# (forward + reverse runner, 2 jobs each; they cooperate through chunk locks). Finished files are moved over the originals by hand.
S=$SCRATCH
while pgrep -f "render_chunks.py.*--only 2,40" >/dev/null; do sleep 20; done
echo "main render finished $(date -u)"
cd $S/engine
$S/venv/bin/python $S/tools/render_chunks.py --ep ep01 --frames 30329 --chunk 450 --par 2 --only "$1" --dir $S/engine/chunks/redo --out $S/engine/chunks/redo/unused.mp4 > $S/engine/render_redoF.log 2>&1 &
sleep 45
$S/venv/bin/python $S/tools/render_chunks.py --ep ep01 --frames 30329 --chunk 450 --par 2 --only "$1" --reverse --dir $S/engine/chunks/redo --out $S/engine/chunks/redo/unused.mp4 > $S/engine/render_redoR.log 2>&1 &
wait
echo "redo finished $(date -u)"
ls $S/engine/chunks/redo
