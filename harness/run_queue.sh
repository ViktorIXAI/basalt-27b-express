#!/usr/bin/env bash
# Sequential arm queue with a hard wall-clock budget.
# usage: run_queue.sh "<indices, space separated>" <deadline_epoch>
cd ~/bench27b || exit 2
IDX="$1"; DEADLINE="$2"
for i in $IDX; do
  now=$(date +%s)
  if [ "$now" -ge "$DEADLINE" ]; then echo "$(date -Iseconds) BUDGET EXCEEDED, stopping before arm $i"; break; fi
  echo "$(date -Iseconds) ARM $i START"
  python3 bench.py plan.json "$i" 2>&1
  echo "$(date -Iseconds) ARM $i DONE rc=$?"
done
echo "$(date -Iseconds) QUEUE FINISHED"
