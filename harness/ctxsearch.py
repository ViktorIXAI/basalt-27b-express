#!/usr/bin/env python3
"""Find the largest --max-context that actually starts fully in VRAM (kv-resident 0).
Each attempt only loads and checks /health; the engine's own refusal line gives the exact
memory numbers. Records everything to results/ctx_ceiling.json."""
import json, os, re, subprocess, sys, time, urllib.request

B = os.path.expanduser("~/bench27b")
BIN = os.path.expanduser("~/basalt-041/bin/basalt")
PYP = os.path.expanduser("~/basalt/.venv/bin/python")
PACK = B + "/model/Qwen3.8-27B-QUASAR-NVFP4.basalt"
BASE = "http://127.0.0.1:18080"
REFUSE = re.compile(r"need (\d+) MiB, (\d+) MiB are free")
LOADED = re.compile(r"loaded\s+([\d.]+)GiB\s+([\d.]+)s")


def attempt(mc, spec):
    cfg = {"version": 2, "server": {"host": "127.0.0.1", "port": 18080, "request-lines": True,
                                    "max-payload-mib": 512},
           "models": [{"model": PACK, "alias": "q27b", "kv": "int8", "max-context": mc}],
           "engine": {"kv-resident": 0, "spec": spec, "suffix-draft": 0}}
    cfgp = f"{B}/configs/ctx_{mc}_s{spec}.json"
    json.dump(cfg, open(cfgp, "w"))
    log = f"{B}/logs/ctx_{mc}_s{spec}.serve.log"
    fh = open(log, "w")
    p = subprocess.Popen([BIN, "serve", "--python", PYP, "--config", cfgp],
                         stdout=fh, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    ok, rec = False, {"max_context": mc, "spec": spec}
    try:
        for _ in range(150):
            try:
                if json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read()).get("loaded"):
                    ok = True
                    break
            except Exception:
                pass
            time.sleep(1)
            if p.poll() is not None:
                break
        time.sleep(1)
        txt = open(log, errors="replace").read()
        m = REFUSE.search(txt)
        if m:
            rec.update(needed_mib=int(m.group(1)), free_mib=int(m.group(2)),
                       per_cell_kib=round(int(m.group(1)) * 1024 / mc, 2))
        lm = LOADED.search(txt)
        if lm:
            rec.update(loaded_gib=float(lm.group(1)), load_s=float(lm.group(2)))
    finally:
        try:
            os.killpg(os.getpgid(p.pid), 15)
        except Exception:
            pass
        for _ in range(40):
            if not subprocess.run(["pgrep", "-f", "bench27b/configs/ctx_"],
                                  stdout=subprocess.DEVNULL).stdout:
                break
            time.sleep(2)
        fh.close()
    rec["starts"] = ok
    print(f"mc={mc} spec={spec} starts={ok} {rec.get('needed_mib','')}/{rec.get('free_mib','')}", flush=True)
    return rec


def main():
    spec = int(sys.argv[1])
    cands = [int(x) for x in sys.argv[2:]]
    recs = [attempt(mc, spec) for mc in cands]
    ok = [r["max_context"] for r in recs if r["starts"]]
    out = {"spec": spec, "attempts": recs, "max_starting_context": max(ok) if ok else None}
    with open(B + "/results/ctx_ceiling.json", "a") as f:
        f.write(json.dumps(out) + "\n")
    print("MAX_STARTING", out["max_starting_context"])


if __name__ == "__main__":
    main()
