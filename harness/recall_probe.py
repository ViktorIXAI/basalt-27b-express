#!/usr/bin/env python3
"""Targeted long-context recall probe: one big prompt, then ask for each control record by id.
Separate from the speed arms so the correctness method is explicit and reproducible."""
import json, os, subprocess, sys, time, urllib.request

B = os.path.expanduser("~/bench27b")
BIN = os.path.expanduser("~/basalt-041/bin/basalt")
PYP = os.path.expanduser("~/basalt/.venv/bin/python")
PACK = B + "/model/Qwen3.8-27B-QUASAR-NVFP4.basalt"
BASE = "http://127.0.0.1:18080"
ALIAS = "q27b"
DONE = __import__("re").compile(r"\[server\]\s+\S+\s+done\s+(.*)$")


def post(p, pl, t=1200):
    r = urllib.request.Request(BASE + p, data=json.dumps(pl).encode(),
                               headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(r, timeout=t).read())


def main():
    prompt_name, mc, res, spec = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    man = json.load(open(B + "/prompts/manifest.json"))
    meta = man[prompt_name]
    text = open(meta["path"]).read()
    cfg = {"version": 2, "server": {"host": "127.0.0.1", "port": 18080, "request-lines": True,
                                    "max-payload-mib": 512},
           "models": [{"model": PACK, "alias": ALIAS, "kv": "int8", "max-context": mc}],
           "engine": {"kv-resident": res, "spec": spec, "suffix-draft": 0}}
    cfgp = f"{B}/configs/recall_{prompt_name}_{res}.json"
    json.dump(cfg, open(cfgp, "w"), indent=1)
    log = f"{B}/logs/recall_{prompt_name}_{res}.serve.log"
    fh = open(log, "w")
    p = subprocess.Popen([BIN, "serve", "--python", PYP, "--config", cfgp],
                         stdout=fh, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    out = {"probe_id": f"recall_{prompt_name}_{mc}_r{res}_s{spec}", "prompt": prompt_name,
           "prompt_tokens": meta["tokens"], "max_context": mc, "kv_resident": res, "spec": spec,
           "markers": meta["markers"], "checks": []}
    try:
        for _ in range(300):
            try:
                if json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read()).get("loaded"):
                    break
            except Exception:
                pass
            time.sleep(2)
        ptoks = len(post("/tokenize", {"content": text, "parse_special": False})["tokens"])
        t0 = time.time()
        r = post("/v1/chat/completions", {"model": ALIAS, "temperature": 0, "max_tokens": 8,
                                          "reasoning_effort": "none",
                                          "messages": [{"role": "user", "content": text}]})
        out["cold_prefill_s"] = round(time.time() - t0, 2)
        out["cold_prompt_tokens"] = ptoks
        for m in meta["markers"]:
            ask = (f"In the reference dump above there is a line that starts with `CONTROL {m['id']}`. "
                   f"Output only the VALUE that follows it.")
            t1 = time.time()
            a = post("/v1/chat/completions", {"model": ALIAS, "temperature": 0, "max_tokens": 48,
                                              "reasoning_effort": "none",
                                              "messages": [{"role": "user", "content": text + "\n\n" + ask}]})
            ans = (a["choices"][0]["message"].get("content") or "").strip()
            ok = m["value"] in ans
            out["checks"].append({"id": m["id"], "expected": m["value"], "answer": ans[:120],
                                  "correct": ok, "s": round(time.time() - t1, 2)})
            print(f"{m['id']}: expected={m['value']} answer={ans[:60]!r} correct={ok}", flush=True)
        tail = [l for l in open(log, errors="replace") if DONE.search(l)]
        out["last_engine_lines"] = [DONE.search(l).group(1) for l in tail[-3:]]
        out["n_correct"] = sum(1 for c in out["checks"] if c["correct"])
    finally:
        try:
            os.killpg(os.getpgid(p.pid), 15)
        except Exception:
            pass
        time.sleep(4)
        fh.close()
    with open(B + "/results/recall_probes.jsonl", "a") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
    print(f"recall {prompt_name}: {out['n_correct']}/{len(out['checks'])} correct")


if __name__ == "__main__":
    main()
