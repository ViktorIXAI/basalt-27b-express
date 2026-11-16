#!/usr/bin/env python3
"""Summarize the express bench into CSV tables + four PNG charts (English labels).
Pure PIL: no plotting library is installed on the test box, and none is added."""
import csv, json, os, sys
from PIL import Image, ImageDraw, ImageFont

B = os.path.expanduser("~/bench27b")
W, H, M = 1100, 620, 70


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def chart(path, title, xlab, ylab, series, xlog=False, yticks=None, bars=False):
    """series: list of (label, [(x, y), ...], color)"""
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f, ft, fl = font(16), font(22), font(15)
    pts = [p for _, s, _ in series for p in s if p[1] is not None]
    if not pts:
        d.text((20, 20), "no data", font=f, fill="black")
        im.save(path)
        return
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = min(xs), max(xs)
    y0, y1 = 0, max(ys) * 1.12
    def px(x):
        if xlog and x > 0 and x0 > 0:
            import math
            return M + (math.log(x) - math.log(x0)) / max(1e-9, (math.log(x1) - math.log(x0))) * (W - 2 * M)
        return M + (x - x0) / max(1e-9, (x1 - x0)) * (W - 2 * M)
    def py(y):
        return H - M - (y - y0) / max(1e-9, (y1 - y0)) * (H - 2 * M)
    d.line([M, H - M, W - M, H - M], fill=(120, 120, 120), width=2)
    d.line([M, M, M, H - M], fill=(120, 120, 120), width=2)
    yt = yticks or [y0 + (y1 - y0) * i / 5 for i in range(6)]
    for y in yt:
        yy = py(y)
        d.line([M, yy, W - M, yy], fill=(225, 225, 225))
        d.text((8, yy - 8), f"{y:,.0f}", font=fl, fill=(90, 90, 90))
    for x in sorted(set(xs)):
        xx = px(x)
        d.line([xx, H - M, xx, H - M + 6], fill=(120, 120, 120))
        d.text((xx - 22, H - M + 10), f"{x:,}", font=fl, fill=(90, 90, 90))
    if bars:
        n = len(series)
        for si, (lab, s, c) in enumerate(series):
            for k, (x, y) in enumerate(s):
                if y is None:
                    continue
                bw = (W - 2 * M) / max(1, len(s)) / (n + 1)
                x_left = M + k * (W - 2 * M) / max(1, len(s)) + si * bw
                d.rectangle([x_left, py(y), x_left + bw * 0.95, H - M], fill=c)
    else:
        for lab, s, c in series:
            pts2 = [(px(x), py(y)) for x, y in s if y is not None]
            if len(pts2) > 1:
                d.line(pts2, fill=c, width=3)
            for p in pts2:
                d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=c)
    d.text((M, 18), title, font=ft, fill=(20, 20, 20))
    d.text((W / 2 - 60, H - 28), xlab, font=f, fill=(60, 60, 60))
    d.text((10, M - 30), ylab, font=f, fill=(60, 60, 60))
    ly = M + 6
    for lab, _, c in series:
        d.rectangle([W - 320, ly, W - 296, ly + 12], fill=c)
        d.text((W - 288, ly - 3), lab, font=f, fill=(30, 30, 30))
        ly += 22
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def main():
    rows = [json.loads(l) for l in open(B + "/results/results_raw.jsonl")]
    os.makedirs(B + "/results", exist_ok=True)
    out = []
    for r in rows:
        for rep in r.get("reps", []):
            e = rep.get("engine", {})
            t = rep.get("telem", {})
            out.append({
                "run_id": r["run_id"], "rep": rep["rep"], "context_tokens": rep.get("prompt_tokens_actual"),
                "max_context": r["max_context"], "mode": "plain" if r["spec"] == 0 else "dflash2",
                "spec": r["spec"], "suffix_draft": r["suffix_draft"], "kv": r["kv"],
                "kv_resident": r.get("kv_resident"),
                "ttft_s": rep.get("ttft_s"), "prefill_tok_s": e.get("prefill_tok_s"),
                "prefill_s": e.get("prefill_s"), "decode_tok_s_engine": e.get("decode_tok_s"),
                "D1_tok_s": rep.get("D1_tok_s"), "D2_tok_s": rep.get("D2_tok_s"),
                "D3_tok_s": rep.get("D3_tok_s"), "D4_tok_s": rep.get("D4_tok_s"),
                "decode_tok_s_all": rep.get("decode_tok_s_all"),
                "accept_pct": e.get("accept_pct"), "draft_len": e.get("draft_len"),
                "prompt_cache_hit_pct": e.get("hit_pct"), "pcie_pct": e.get("pcie_pct"),
                "wall_s": rep.get("wall_s"), "gen_tokens_usage": (rep.get("usage") or {}).get("completion_tokens"),
                "prompt_tokens_usage": (rep.get("usage") or {}).get("prompt_tokens"),
                "vram_peak_mib": t.get("peak_vram_used_mib"), "ram_peak_mib": (t.get("peak_ram_used_b") or 0) / 2**20 or None,
                "gpu_power_avg_w": t.get("avg_power_w"), "gpu_power_peak_w": t.get("peak_power_w"),
                "gpu_temp_max_c": t.get("peak_temp_c"), "throttled_samples": t.get("throttled_samples"),
                "load_seconds": r.get("load_seconds"), "status": r.get("status"),
            })
    with open(B + "/results/results_summary.csv", "w", newline="") as fh:
        if out:
            w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
            w.writeheader()
            w.writerows(out)
    print(f"summary rows: {len(out)}")

    def best(mode, key):
        d = {}
        for r in out:
            if r["mode"] != mode or not r["context_tokens"]:
                continue
            v = r.get(key)
            if v is None:
                continue
            k = r["context_tokens"]
            if k not in d or v > d[k]:
                d[k] = v
        return sorted(d.items())
    ctx = sorted({r["context_tokens"] for r in out if r["context_tokens"]})
    plain = {k: v for k, v in best("plain", "decode_tok_s_engine")}
    dfl = {k: v for k, v in best("dflash2", "decode_tok_s_engine")}
    pre = {k: v for k, v in best("plain", "prefill_tok_s")}
    vpk = {}
    ram = {}
    for r in out:
        k = r["context_tokens"]
        if not k:
            continue
        if r["vram_peak_mib"] and (k not in vpk or r["vram_peak_mib"] > vpk[k]):
            vpk[k] = r["vram_peak_mib"]
        if r["ram_peak_mib"] and (k not in ram or r["ram_peak_mib"] > ram[k]):
            ram[k] = r["ram_peak_mib"]
    os.makedirs(B + "/charts", exist_ok=True)
    chart(B + "/charts/prefill_vs_context.png", "Prefill speed vs context length (int8 KV, plain decode)",
          "prompt tokens", "tok/s", [(f"prefill ({len(pre)} pts)", [(k, v) for k, v in pre.items()], (30, 90, 200))])
    chart(B + "/charts/decode_vs_context.png", "Decode speed vs context length: plain vs DFlash 2",
          "prompt tokens", "tok/s",
          [("plain (--spec 0)", [(k, v) for k, v in plain.items()], (200, 90, 30)),
           ("DFlash 2 (--spec 16)", [(k, v) for k, v in dfl.items()], (30, 140, 60))])
    qs = []
    for mode, col in (("plain", (200, 90, 30)), ("dflash2", (30, 140, 60))):
        for i, key in enumerate(("D1_tok_s", "D2_tok_s", "D3_tok_s", "D4_tok_s")):
            d = {}
            for r in out:
                if r["mode"] == mode and r.get(key) and r["context_tokens"]:
                    d.setdefault(r["context_tokens"], []).append(r[key])
            s = [(k, sum(v) / len(v)) for k, v in sorted(d.items())]
            qs.append((f"{mode} {key[:2]}", s, col))
    chart(B + "/charts/decode_quarters.png", "Decode speed across four quarters of one answer (D1..D4)",
          "prompt tokens", "tok/s", qs)
    chart(B + "/charts/memory_vs_context.png", "Peak VRAM and RAM vs context length (MiB)",
          "prompt tokens", "MiB",
          [("peak VRAM used", [(k, v) for k, v in sorted(vpk.items())], (150, 40, 160)),
           ("peak RAM used", [(k, v) for k, v in sorted(ram.items())], (40, 140, 190))])
    print("charts written")
    md = ["| context | mode | prefill tok/s | decode tok/s | D1 | D2 | D3 | D4 | TTFT s | accept % | VRAM peak MiB | kv-resident |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(out, key=lambda r: (r["context_tokens"] or 0, r["mode"], r["rep"])):
        md.append("| {context_tokens} | {mode} | {prefill_tok_s} | {decode_tok_s_engine} | {D1_tok_s} | {D2_tok_s} | "
                  "{D3_tok_s} | {D4_tok_s} | {ttft_s} | {accept_pct} | {vram_peak_mib} | {kv_resident} |".format(**r))
    open(B + "/results/table_main.md", "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
