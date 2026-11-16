#!/usr/bin/env python3
"""Arm runner for the Basalt v0.4.1 / Qwen3.8-27B-QUASAR-NVFP4 express bench.

One arm = one engine start (cold weights), N requests, engine summary line,
token-accurate decode quarters from the SSE stream, 1 Hz telemetry slice.
No engine sources are modified; only documented flags and the OpenAI-compatible API.
"""
import csv, json, os, re, signal, subprocess, sys, time, urllib.request

B = os.path.expanduser("~/bench27b")
BIN = os.path.expanduser("~/basalt-041/bin/basalt")
PYP = os.path.expanduser("~/basalt/.venv/bin/python")
PACK = B + "/model/Qwen3.8-27B-QUASAR-NVFP4.basalt"
HOST, PORT, ALIAS = "127.0.0.1", 18080, "q27b"
BASE = f"http://{HOST}:{PORT}"
DONE_RE = re.compile(r"\[server\]\s+\S+\s+done\s+(.*)$")
KV_BYTES = 33 * 1024            # int8 KV bytes per position (docs/models/qwen38-27b.md)


def log(m):
    print(time.strftime("%Y-%m-%d_%H:%M:%S"), m, flush=True)


def post(path, payload, timeout=120):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def get(path, timeout=8):
    return json.loads(urllib.request.urlopen(BASE + path, timeout=timeout).read())


def tokenize(text):
    return post("/tokenize", {"content": text, "parse_special": False}, timeout=300)["tokens"]


def gpu():
    q = ("memory.used,memory.free,power.draw,temperature.gpu,utilization.gpu,"
         "clocks.current.sm,clocks_throttle_reasons.active")
    s = subprocess.run(["nvidia-smi", "--query-gpu=" + q, "--format=csv,noheader,nounits"],
                       capture_output=True, text=True).stdout.strip().split(", ")
    return {"vram_used_mib": int(s[0]), "vram_free_mib": int(s[1]), "power_w": float(s[2]),
            "temp_c": int(s[3]), "util": int(s[4]), "sm_clock": int(s[5]), "throttle": s[6]}


def start_serve(cfg, logfile):
    cmd = [BIN, "serve", "--python", PYP, "--config", cfg]
    fh = open(logfile, "w")
    p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    return p, fh


def wait_loaded(p, t=480):
    t0 = time.time()
    while time.time() - t0 < t:
        if p.poll() is not None:
            return None, p.returncode, time.time() - t0
        try:
            d = get("/health")
            if d.get("loaded"):
                return d, 0, time.time() - t0
        except Exception:
            pass
        time.sleep(2)
    return None, -1, time.time() - t0


def stop_serve(p, fh):
    try:
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
    except Exception:
        pass
    for _ in range(30):
        if p.poll() is not None:
            break
        time.sleep(1)
    if p.poll() is None:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except Exception:
            pass
    time.sleep(3)
    fh.close()


def telem_stats(path, t0, t1):
    out = {}
    try:
        rows = [r for r in csv.DictReader(open(path)) if r.get("ts") and t0 <= float(r["ts"]) <= t1]
    except Exception:
        return out
    if not rows:
        return out
    def f(k):
        v = []
        for r in rows:
            try:
                v.append(float(r[k]))
            except Exception:
                pass
        return v
    for k, agg in (("vram_used_mib", "max"), ("ram_used_b", "max"), ("ram_avail_b", "min"),
                   ("swap_used_b", "max"), ("power_w", "mean"), ("power_w2", "max"),
                   ("temp_c", "max"), ("sm_clock", "min"), ("proc_rss_kb", "max"),
                   ("gpu_util", "mean")):
        key = k.rstrip("2") if k == "power_w2" else k
        v = f("power_w" if k.startswith("power_w") else k)
        if not v:
            continue
        if agg == "max":
            out[("peak_" if key in ("vram_used_mib", "ram_used_b", "swap_used_b", "power_w",
                                    "temp_c", "proc_rss_kb") else "") + key] = round(max(v), 1)
        elif agg == "min":
            out["min_" + key] = round(min(v), 1)
        else:
            out["avg_" + key] = round(sum(v) / len(v), 1)
    out["telem_samples"] = len(rows)
    thr = sum(1 for r in rows if r.get("throttle", "0x0").strip() not in ("0x0", "0", ""))
    out["throttled_samples"] = thr
    return out


def stream_chat(prompt, max_tokens, extra=None, wall_limit=900, history=None):
    msgs = (history or []) + [{"role": "user", "content": prompt}]
    pl = {"model": ALIAS, "messages": msgs, "max_tokens": max_tokens, "temperature": 0,
          "top_p": 1.0, "top_k": 0, "presence_penalty": 0, "frequency_penalty": 0,
          "repetition_penalty": 1.0, "stream": True, "stream_options": {"include_usage": True},
          "reasoning_effort": "none"}
    if extra:
        pl.update(extra)
    t0 = time.time()
    req = urllib.request.Request(BASE + "/v1/chat/completions", data=json.dumps(pl).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    ttft, pieces, usage, text = None, [], {}, []
    truncated = False
    with urllib.request.urlopen(req, timeout=wall_limit) as r:
        for raw in r:
            if time.time() - t0 > wall_limit:
                truncated = True
                break
            if not raw.startswith(b"data:"):
                continue
            s = raw[5:].strip()
            if s == b"[DONE]":
                break
            try:
                d = json.loads(s)
            except Exception:
                continue
            if d.get("usage"):
                usage = d["usage"]
            ch = (d.get("choices") or [{}])[0]
            dl = ch.get("delta") or {}
            piece = dl.get("content") or ""
            if piece:
                if ttft is None:
                    ttft = time.time() - t0
                text.append(piece)
                pieces.append((time.time() - t0, len("".join(text))))
    return ttft, pieces, usage, "".join(text), truncated, time.time() - t0


def quarters(pieces, full_text):
    """Token-accurate decode quarters: every SSE piece boundary is tokenized, so the
    25/50/75/100% cuts fall on real generated-token counts (granularity = verify window)."""
    if not pieces or not full_text:
        return {}, 0
    marks, ntok = [], 0
    for t, nchar in pieces:
        n = len(tokenize(full_text[:nchar]))
        if n > ntok:
            marks.append((t, n))
            ntok = n
    if ntok < 8:
        return {}, ntok
    q = {}
    bounds = [0, ntok * 0.25, ntok * 0.5, ntok * 0.75, ntok]
    est = {}
    for i in range(4):
        lo, hi = bounds[i], bounds[i + 1]
        a = next((m for m in marks if m[1] >= lo), None)
        b = next((m for m in marks if m[1] >= hi), None)
        if not a or not b or b[0] <= a[0]:
            continue
        q[f"D{i+1}_tok_s"] = round((hi - lo) / (b[0] - a[0]), 1)
        est[f"D{i+1}"] = f"{int(lo)}-{int(hi)} tok over windows ending {a[0]:.2f}..{b[0]:.2f}s"
    q["decode_tok_s_all"] = round(ntok / (marks[-1][0] - marks[0][0]) * (ntok / (ntok)), 1) if len(marks) > 1 else None
    q["gen_tokens_counted"] = ntok
    return {"quarters": q, "qdebug": est}, ntok


def parse_done(logfile, since):
    last = None
    try:
        for line in open(logfile, errors="replace"):
            m = DONE_RE.search(line)
            if m:
                last = m.group(1)
    except Exception:
        pass
    if not last:
        return {}
    d = {}
    for k, pat in (("done_raw", r".*"),):
        pass
    d["done_raw"] = last
    for k, pat, cast in (("prompt_tokens", r"pp=(\d+)", int), ("cached_tokens", r"pp=\d+/(\d+)c", int),
                         ("prefill_s", r"pp=\S+\s+([\d.]+)s", float),
                         ("prefill_tok_s", r"pp=\S+\s+[\d.]+s\s+(\d+)t/s", float),
                         ("gen_tokens", r"tg=(\d+)", int), ("decode_tok_s", r"tg=\d+\s+([\d.]+)t/s", float),
                         ("accept_pct", r"acc=(\d+)%", float), ("draft_len", r"dl=([\d.]+)", float),
                         ("ttft_s_engine", r"ttft=([\d.]+)s", float), ("end", r"end=(\w+)", str),
                         ("hit_pct", r"hit=([\d.]+)%", float), ("pcie_pct", r"pcie=([\d.]+)%", float)):
        m = re.search(pat, last)
        if m:
            d[k] = cast(m.group(1))
    return d


def fail_row(arm, why, extra=None):
    r = {"run_id": arm["id"], "status": why}
    if extra:
        r.update(extra)
    os.makedirs(B + "/results", exist_ok=True)
    with open(B + "/results/failures.csv", "a") as f:
        json.dump(r, f)
        f.write("\n")
    log(f"{arm['id']}: {why}")


def run_arm(arm):
    os.makedirs(B + "/configs", exist_ok=True)
    os.makedirs(B + "/logs", exist_ok=True)
    os.makedirs(B + "/results", exist_ok=True)
    residents = arm.get("kv_residents", [0])
    rec = {"run_id": arm["id"], "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "context_target": arm["ctx"], "max_context": arm["max_context"], "kv": "int8",
           "spec": arm["spec"], "suffix_draft": arm.get("suffix_draft", 3),
           "model": "Qwen3.8-27B-QUASAR-NVFP4", "basalt": "v0.4.1",
           "commit": "d3b75742967c7f9fd892c6894a2b9ac6e36e0cf3",
           "sampling": {"temperature": 0, "top_p": 1, "top_k": 0, "reasoning_effort": "none",
                        "seed": None}, "reps": []}
    for res in residents:
        cfg = {"version": 2,
               "server": {"host": HOST, "port": PORT, "request-lines": True,
                          "max-payload-mib": 512},
               "models": [{"model": PACK, "alias": ALIAS, "kv": "int8",
                           "max-context": arm["max_context"]}],
               "engine": {"kv-resident": res, "spec": arm["spec"],
                          "suffix-draft": arm.get("suffix_draft", 3)}}
        if arm.get("diag", True):
            cfg["engine"]["decode-timing"] = True
            cfg["engine"]["draft-log"] = f"{B}/logs/{arm['id']}.draftlog"
        cfgp = f"{B}/configs/{arm['id']}_r{res}.json"
        json.dump(cfg, open(cfgp, "w"), indent=1)
        rec["engine_config"] = cfg
        rec["kv_resident"] = res
        logfile = f"{B}/logs/{arm['id']}_r{res}.serve.log"
        subprocess.run(["pkill", "-f", "bench27b/configs"])
        for _ in range(60):
            if gpu().get("vram_free_mib", 0) > 20000:
                break
            time.sleep(2)
        t_start = time.time()
        p, fh = start_serve(cfgp, logfile)
        h, rc, load_s = wait_loaded(p, arm.get("load_timeout", 480))
        if h is None:
            tail = ""
            try:
                tail = "".join(open(logfile, errors="replace").readlines()[-12:])
            except Exception:
                pass
            stop_serve(p, fh)
            why = "START_FAILED"
            if re.search(r"out of memory|OOM|does not fit|no free memory|CUDA error", tail, re.I):
                why = "OOM"
            fail_row(arm, why, {"kv_resident": res, "load_seconds": round(load_s, 1),
                                "log_tail": tail[-1200:]})
            continue
        tele = f"{B}/logs/{arm['id']}_r{res}.telem.csv"
        tp = None
        try:
            rec["load_seconds"] = round(load_s, 1)
            rec["health"] = h
            rec["vram_after_load"] = gpu()
            tp = subprocess.Popen(["python3", B + "/telem.py", tele, "basalt"])
            mfp = B + "/prompts/manifest.json"
            manifest = json.load(open(mfp)) if os.path.exists(mfp) else {}
            for rep in range(arm.get("reps", 1)):
                pname = arm["prompt"].replace("@rep", f"_r{rep+1}")
                pfile = f"{B}/prompts/{pname}.txt"
                if not os.path.exists(pfile):
                    sys.path.insert(0, B)
                    import mkprompts as MP
                    text0, mk0, n0 = MP.build(arm["kind"], arm["ctx"], lambda t: len(tokenize(t)), salt=rep)
                    open(pfile, "w").write(text0)
                    import hashlib
                    manifest[pname] = {"path": pfile, "tokens": n0, "kind": arm["kind"], "salt": rep,
                                       "sha256": hashlib.sha256(text0.encode()).hexdigest(),
                                       "markers": mk0, "seed": MP.SEED}
                    json.dump(manifest, open(mfp, "w"), indent=1)
                    log(f"{arm['id']}: built prompt {pname} = {n0} tokens")
                ptxt = open(pfile).read()
                ptoks = len(tokenize(ptxt))
                t0 = time.time()
                ttft, pieces, usage, text, trunc, wall = stream_chat(
                    ptxt, arm["max_tokens"], arm.get("extra"), wall_limit=arm.get("wall_limit", 900))
                t1 = time.time()
                d = parse_done(logfile, t0)
                q, ntok = quarters(pieces, text)
                row = {"rep": rep + 1, "prompt_file": pname, "prompt_tokens_actual": ptoks,
                       "ttft_s": round(ttft, 3) if ttft else None, "wall_s": round(wall, 2),
                       "usage": usage, "truncated": trunc, "engine": d,
                       "telem": telem_stats(tele, t0, t1)}
                row.update(q.get("quarters", {}))
                row["quarter_note"] = q.get("qdebug")
                open(f"{B}/logs/{arm['id']}_rep{rep+1}.answer.txt", "w").write(text)
                rec["reps"].append(row)
                log(f"{arm['id']} rep{rep+1}: prompt={ptoks} ttft={row['ttft_s']}s "
                    f"engine_decode={d.get('decode_tok_s')} prefill={d.get('prefill_tok_s')} "
                    f"accept={d.get('accept_pct')}% quarters="
                    f"{[row.get(k) for k in ('D1_tok_s','D2_tok_s','D3_tok_s','D4_tok_s')]}")
                if arm.get("recall") and rec.get("health"):
                    mk = json.load(open(B + "/prompts/manifest.json")).get(pname, {}).get("markers", [])
                    if mk:
                        ask = ("List every CONTROL record in the dump above as `id = value`, "
                               "one per line. If you cannot find one, say so.")
                        hist = [{"role": "assistant", "content": text[:2000]}]
                        _, _, u2, txt2, _, w2 = stream_chat(ask, 512, None, 600, history=hist)
                        hit = {m["id"]: (m["id"] in txt2 and m["value"] in txt2) for m in mk}
                        found = {m["id"]: m["value"] in (txt2 or "") for m in mk}
                        row["recall"] = {"asked": len(mk), "id_and_value_ok": sum(hit.values()),
                                         "id_ok": sum(1 for m in mk if m["id"] in (txt2 or "")),
                                         "value_ok": sum(found.values()),
                                         "detail": hit, "answer_len": len(txt2 or ""),
                                         "prefill_hit_pct": parse_done(logfile, t1).get("hit_pct"),
                                         "wall_s": round(w2, 2)}
                        open(f"{B}/logs/{arm['id']}_rep{rep+1}.recall.txt", "w").write(txt2 or "")
                        log(f"{arm['id']} recall: {row['recall']['id_and_value_ok']}/{len(mk)} exact")

        finally:
            if tp:
                tp.terminate()
            stop_serve(p, fh)
        rec["status"] = "ok"
        with open(B + "/results/results_raw.jsonl", "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec
    rec["status"] = "no_working_config"
    with open(B + "/results/results_raw.jsonl", "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def main():
    plan = json.load(open(sys.argv[1]))
    arm = plan[int(sys.argv[2])]
    r = run_arm(arm)
    log(f"{arm['id']}: status={r.get('status')} kv_resident={r.get('kv_resident')}")


if __name__ == "__main__":
    main()
