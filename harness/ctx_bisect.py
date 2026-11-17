#!/usr/bin/env python3
"""Bisect (renamed from bisect.py: stdlib shadowing) the largest --max-context that starts with the whole KV in VRAM (kv-resident 0).
Uses ctxsearch.attempt(); known-good lower bound comes from the completed main matrix."""
import json, os, sys
sys.path.insert(0, os.path.expanduser("~/bench27b"))
from ctxsearch import attempt

B = os.path.expanduser("~/bench27b")


def bisect(spec, lo, hi, tol=2048):
    recs = []
    assert attempt(lo, spec)["starts"], f"lower bound {lo} does not start"
    while hi - lo > tol:
        mid = ((lo + hi) // 2 // 1024) * 1024
        r = attempt(mid, spec)
        recs.append(r)
        if r["starts"]:
            lo = mid
        else:
            hi = mid
    rec = {"spec": spec, "bisected": True, "max_starting_context": lo,
           "upper_rejected": hi, "attempts": recs}
    with open(B + "/results/ctx_ceiling.json", "a") as f:
        f.write(json.dumps(rec) + "\n")
    print("MAX_STARTING", spec, lo)
    return lo


if __name__ == "__main__":
    spec = int(sys.argv[1]); lo = int(sys.argv[2]); hi = int(sys.argv[3])
    bisect(spec, lo, hi)
