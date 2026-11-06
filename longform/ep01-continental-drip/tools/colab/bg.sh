#!/bin/bash
# bg.sh "<shell command>" LOGFILE: start a detached job on the Colab VM (session mj), output to LOGFILE on the VM
S=$SCRATCH
timeout 120 $S/colabvenv/bin/colab --auth oauth2 exec -s mj --timeout 60 --env "CMD=$1" --env "LOG=$2" -f $S/colab/run_bg.py 2>&1 | sed -E 's#(token|code|access_token)=[^& ]+#\1=***#g'
