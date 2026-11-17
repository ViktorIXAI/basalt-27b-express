# Qwen3.8-27B-QUASAR-NVFP4 on Basalt v0.4.1 — measured results

Machine: RTX 5090 **Laptop** (24 GB VRAM), PCIe link trained at **16 GT/s x8 (PCIe 4.0 x8)**,
measured host→device **14.4 GB/s**. Engine: Basalt v0.4.1, commit `d3b75742967c7f9fd892c6894a2b9ac6e36e0cf3`.
Model pack: `Qwen3.8-27B-QUASAR-NVFP4.basalt`, SHA-256 `5ec89e71b4bd461a5abf607825d3cd99e74d2476b8ba087fd690f09a067919ba`.
Sampling: temperature 0, thinking disabled, one concurrent request, int8 KV, `--parallel 1`.
Every context length below is the **actual token count returned by the engine's `/tokenize`** after the
chat template was applied — no character or word estimates. Every number is a measured run; failures are
recorded with the engine's own refusal text instead of zero speeds.

## Main matrix (context × decode mode)

| context (actual tokens) | mode | KV in RAM | prefill tok/s | TTFT s | decode tok/s | D1 / D2 / D3 / D4 tok/s | draft accept | VRAM peak MiB | RAM peak MiB | GPU power W | GPU °C max | PCIe link under load |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4K (4165) | DFlash 2 (spec 16) | none (all in VRAM) | 7124.0 | 0.63 | 120.5 | 121.5 / 120.5 / 103.3 / 156.8 | 50.0% | 19250.0 | 6677 | 150.7 avg / 169.6 peak | 55.0 | 16.0 GT/s PCIe x8 |
| 4K (4165) | plain | none (all in VRAM) | 6499.0 | 0.87 | 37.8 | 38.7 / 38.3 / 38.2 / 38.3 | n/a | 16858.0 | 6262 | 139.8 avg / 161.8 peak | 54.0 | 16.0 GT/s PCIe x8 |
| 32K (31803) | DFlash 2 (spec 16) | none (all in VRAM) | 5578.0 | 5.75 | 105.5 | 87.8 / 127.2 / 117.7 / 101.9 | 50.0% | 20078.0 | 6599 | 164.0 avg / 178.7 peak | 66.0 | 16.0 GT/s PCIe x8 |
| 32K (31803) | plain | none (all in VRAM) | 5739.0 | 5.59 | 35.1 | 35.5 / 35.1 / 35.1 / 35.1 | n/a | 17682.0 | 6368 | 152.5 avg / 174.3 peak | 64.0 | 16.0 GT/s PCIe x8 |
| 33K (32649) | DFlash 2 (spec 16) | none (all in VRAM) | 5577.0 | 5.89 | 113.1 | 104.6 / 114.0 / 134.1 / 112.9 | 56.0% | 20074.0 | 6611 | 160.8 avg / 178.7 peak | 66.0 | 16.0 GT/s PCIe x8 |
| 33K (32649) | plain | none (all in VRAM) | 5705.0 | 5.76 | 35.0 | 35.3 / 34.9 / 34.9 / 34.9 | n/a | 17682.0 | 6232 | 152.5 avg / 174.3 peak | 64.0 | 16.0 GT/s PCIe x8 |
| 66K (65785) | DFlash 2 (spec 16) | none (all in VRAM) | 4440.0 | 14.87 | 91.3 | 78.8 / 85.9 / 106.3 / 97.1 | 55.0% | 21128.0 | 6583 | 168.3 avg / 174.6 peak | 67.0 | 16.0 GT/s PCIe x8 |
| 66K (65785) | plain | none (all in VRAM) | 4524.0 | 14.6 | 31.6 | 32.0 / 31.7 / 31.7 / 31.6 | n/a | 18738.0 | 6330 | 159.7 avg / 172.7 peak | 66.0 | 16.0 GT/s PCIe x8 |
| 131K (131492) | DFlash 2 (spec 16) | none (all in VRAM) | 3182.0 | 41.42 | 86.6 | 77.0 / 90.2 / 95.4 / 89.2 | 71.0% | 23228.0 | 6627 | 170.1 avg / 175.0 peak | 69.0 | 16.0 GT/s PCIe x8 |
| 131K (131492) | plain | none (all in VRAM) | 3249.0 | 40.55 | 27.0 | 27.3 / 27.1 / 27.1 / 27.0 | n/a | 20850.0 | 6380 | 165.5 avg / 173.9 peak | 64.0 | 16.0 GT/s PCIe x8 |
| 135K (134561) | DFlash 2 (spec 16) | none (all in VRAM) | 3136.0 | 43.09 | 64.7 | 55.0 / 78.5 / 76.9 / 63.6 | 63.0% | 23498.0 | 6584 | 170.5 avg / 174.6 peak | 70.0 | 16.0 GT/s PCIe x8 |
| 198K (197886) | plain | none (all in VRAM) | 2476.0 | 80.04 | 23.5 | 23.9 / 23.5 / 23.5 / 23.5 | n/a | 23160.0 | 6264 | 170.3 avg / 176.0 peak | 68.0 | 16.0 GT/s PCIe x8 |
| 256K (256115) | DFlash 2 (spec 16) | 131072 | 2010.0 | 127.9 | 5.1 | 4.6 / 5.2 / 5.7 / 5.2 | 77.0% | 23482.0 | 10946 | 148.0 avg / 175.4 peak | 71.0 | 16.0 GT/s PCIe x8 |
| 256K (256115) | plain | 196608 | 2030.0 | 126.44 | 4.7 | 4.7 / 4.8 / 4.7 / 4.7 | n/a | 23068.0 | 8533 | 150.0 avg / 174.9 peak | 71.0 | 16.0 GT/s PCIe x8 |

`D1..D4` are four equal quarters of **one continuous answer** (512 tokens, cut at exact token
boundaries of the streamed response), not four separate requests.

## Context ceiling with the whole KV cache in VRAM

| mode | largest context that starts with KV fully in VRAM | first rejected value | note |
|---|---|---|---|
| spec 0 | 203776 | 205824 | 204K fits, 206K refused |
| spec 16 | 140288 | 142336 | 140K fits, 142K refused |

Engine refusal text is kept verbatim in `raw/failures.csv`, e.g.
`1 session(s) of 224000 cells need 9575 MiB, 9487 MiB are free`.

## Long-context correctness

Two different methods, deliberately separated:

| run | free-form 'list all control records' | correct |
|---|---|---|
| A128k | requested | 0/5 |
| B128k | requested | 0/5 |
| A256k | requested | 0/5 |
| B256k | requested | 0/5 |

Free-form answer text (verbatim): `I cannot find any CONTROL records in the provided text.`

| prompt tokens | KV in RAM | spec | targeted questions answered correctly |
|---|---|---|---|
| 131492 | none | 16 | 5/5 |
| 256115 | 131072 | 16 | 5/5 |

When each control record is asked **by its exact id**, the model returns the exact value, both at
131K and at 256K tokens (with 131 072 KV positions served from RAM). So retrieval works; the
"enumerate everything you can find" instruction does not trigger it.

## Answers to the five questions

1. **Maximum speed, short task:** 194.3 tok/s decode (DFlash 2, 4K context);
   fastest single quarter in the same group: 264.3 tok/s.
2. **Sustained speed, long task:**
- 66K: whole answer 31.7 tok/s plain / 92.0 tok/s DFlash 2; last quarter 31.6 / 97.1 tok/s
- 131K: whole answer 27.1 tok/s plain / 87.4 tok/s DFlash 2; last quarter 27.0 / 89.2 tok/s
- 256K: whole answer 4.7 tok/s plain / 5.1 tok/s DFlash 2; last quarter 4.7 / 5.2 tok/s
3. **DFlash 2 gain (median decode speed):**

| context (tokens) | plain tok/s | DFlash 2 tok/s | speedup | KV positions in VRAM (plain / DFlash) |
|---|---|---|---|---|
| 4165 | 37.8 | 120.5 | x3.19 | all / all |
| 31803 | 35.1 | 105.5 | x3.01 | all / all |
| 32649 | 35.0 | 113.1 | x3.23 | all / all |
| 65785 | 31.6 | 91.3 | x2.89 | all / all |
| 131492 | 27.0 | 86.6 | x3.21 | all / all |
| 256115 | 4.7 | 5.1 | x1.09 | 196608 / 131072 |

4. **Speed change inside the answer** (quarters of one continuous answer):

| context (tokens) | mode | D1 tok/s | D4 tok/s | D4 / D1 |
|---|---|---|---|---|
| 4165 | dflash2 | 121.5 | 156.8 | 1.29 |
| 4165 | plain | 38.7 | 38.3 | 0.99 |
| 31803 | dflash2 | 87.8 | 101.9 | 1.16 |
| 31803 | plain | 35.5 | 35.1 | 0.99 |
| 32649 | dflash2 | 104.6 | 112.9 | 1.08 |
| 32649 | plain | 35.3 | 34.9 | 0.99 |
| 65785 | dflash2 | 78.8 | 97.1 | 1.23 |
| 65785 | plain | 32.0 | 31.6 | 0.99 |
| 131492 | dflash2 | 77.0 | 89.2 | 1.16 |
| 131492 | plain | 27.3 | 27.0 | 0.99 |
| 134561 | dflash2 | 55.0 | 63.6 | 1.16 |
| 197886 | plain | 23.9 | 23.5 | 0.98 |
| 256115 | dflash2 | 4.6 | 5.2 | 1.13 |
| 256115 | plain | 4.7 | 4.7 | 1.0 |

5. **Maximum working context on 24 GB:** whole KV cache in VRAM is possible up to
**203,776 tokens without speculation** and **140,288 tokens with DFlash 2**;
measured at that ceiling:
- 134,561 tokens, max-context 140288, DFlash 2: prefill 3,136 tok/s, TTFT 43.09 s, decode 64.7 tok/s, VRAM peak 23,498 MiB
- 197,886 tokens, max-context 203776, plain: prefill 2,476 tok/s, TTFT 80.04 s, decode 23.5 tok/s, VRAM peak 23,160 MiB
- 256115 tokens (DFlash 2) needs --kv-resident 131072: decode 5.1 tok/s
- 256115 tokens (plain) needs --kv-resident 196608: decode 4.7 tok/s

## Hardware facts measured, not copied from a datasheet

```
hardware (measured before the engine starts)
  CPU   AMD Ryzen 9 9955HX, 16 cores
  RAM   read 58.8 GB/s
  GPU   RTX 5090 Laptop GPU  PCIe 4.0 x8  host-to-device 14.4 GB/s
```

```
CPU(s):                                  32
Model name:                              AMD Ryzen 9 9955HX 16-Core Processor
Thread(s) per core:                      2
Core(s) per socket:                      16
Socket(s):                               1
CPU(s) scaling MHz:                      44%
CPU max MHz:                             5460.5269
               total        used        free      shared  buff/cache   available
Mem:     64963141632 58704912384   793706496  2093563904  8262262784  6258229248
Swap:    68719468544    68255744 68651212800
Linux 7.0.0-43-generic
PRETTY_NAME="Ubuntu 24.04.5 LTS"
NAME="Ubuntu"
/usr/local/cuda
/usr/local/cuda-13
/usr/local/cuda-13.0
```

## Reproduction

```bash
python3 mkprompts.py            # builds corpus prompts, exact token counts via /tokenize
bash run_queue.sh "0 1 2" …     # runs plan.json arms sequentially under a wall-clock deadline
python3 bench.py plan.json N    # one arm
python3 ctxsearch.py 0 221184 … # does a given --max-context start at all
python3 bisect.py 0 132096 208896
python3 recall_probe.py <prompt> <max-context> <kv-resident> <spec>
~/basalt/.venv/bin/python report.py   # CSV tables + PNG charts
```
