#!/bin/bash
# cx.sh "<shell command>" [timeout_s]: run a shell command on the Colab VM (session mj) and print its output (last 6000 chars)
S=$SCRATCH
T=${2:-120}
timeout $((T+60)) $S/colabvenv/bin/colab --auth oauth2 exec -s mj --timeout $T --env "CMD=$1" --env "T=$T" -f $S/colab/run_fg.py 2>&1 | sed -E 's#(token|code|access_token)=[^& ]+#\1=***#g'
