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
| 4K (4163) | DFlash 2 (--spec 16) | none (all in VRAM) | 7213.0 | 0.6 | 100.1 | 104.6 / 122.4 / 101.0 / 82.0 | 37.0% | 19264.0 | 6688 | 148.5 avg / 154.8 peak | 55.0 | 16.0 GT/s PCIe x8 |
| 4K (4163) | plain (--spec 0) | none (all in VRAM) | 7417.0 | 0.59 | 38.3 | 38.5 / 38.4 / 38.1 / 38.4 | n/a | 16858.0 | 6221 | 139.8 avg / 161.8 peak | 54.0 | 16.0 GT/s PCIe x8 |
| 4K (4165) | DFlash 2 (--spec 16) | none (all in VRAM) | 7120.0 | 0.63 | 121.0 | 118.1 / 118.5 / 105.6 / 157.4 | 50.0% | 19250.0 | 6720 | 148.5 avg / 154.8 peak | 55.0 | 16.0 GT/s PCIe x8 |
| 4K (4165) | DFlash 2 + suffix-draft 3 | none (all in VRAM) | 7107.0 | 0.63 | 119.9 | 124.9 / 118.2 / 98.4 / 156.2 | 51.0% | 19250.0 | 6547 | 150.7 avg / 169.6 peak | 54.0 | 16.0 GT/s PCIe x8 |
| 4K (4165) | plain (--spec 0) | none (all in VRAM) | 5581.0 | 1.15 | 37.3 | 38.9 / 38.3 / 38.2 / 38.2 | n/a | 16858.0 | 6302 | 139.8 avg / 161.8 peak | 54.0 | 16.0 GT/s PCIe x8 |
| 32K (31803) | DFlash 2 (--spec 16) | none (all in VRAM) | 5578.0 | 5.75 | 105.5 | 87.8 / 127.2 / 117.7 / 101.9 | 50.0% | 20078.0 | 6599 | 164.0 avg / 178.7 peak | 66.0 | 16.0 GT/s PCIe x8 |
| 32K (31803) | plain (--spec 0) | none (all in VRAM) | 5739.0 | 5.59 | 35.1 | 35.5 / 35.1 / 35.1 / 35.1 | n/a | 17682.0 | 6368 | 152.5 avg / 174.3 peak | 64.0 | 16.0 GT/s PCIe x8 |
| 33K (32649) | DFlash 2 (--spec 16) | none (all in VRAM) | 5577.0 | 5.89 | 113.1 | 104.6 / 110.8 / 134.1 / 109.9 | 55.0% | 20080.0 | 6611 | 164.0 avg / 178.7 peak | 66.0 | 16.0 GT/s PCIe x8 |
| 33K (32649) | plain (--spec 0) | none (all in VRAM) | 5705.0 | 5.76 | 35.0 | 35.3 / 34.9 / 34.9 / 34.9 | n/a | 17682.0 | 6232 | 152.5 avg / 174.3 peak | 64.0 | 16.0 GT/s PCIe x8 |
| 66K (65785) | DFlash 2 (--spec 16) | none (all in VRAM) | 4440.0 | 14.87 | 94.1 | 78.8 / 99.0 / 106.3 / 100.2 | 55.0% | 21128.0 | 6583 | 168.9 avg / 173.2 peak | 67.0 | 16.0 GT/s PCIe x8 |
| 66K (65785) | DFlash 2 + suffix-draft 3 | none (all in VRAM) | 4439.0 | 14.88 | 91.3 | 82.3 / 85.9 / 106.4 / 97.1 | 55.0% | 21130.0 | 6696 | 168.3 avg / 173.1 peak | 67.0 | 16.0 GT/s PCIe x8 |
| 66K (65785) | plain (--spec 0) | none (all in VRAM) | 4524.0 | 14.6 | 31.6 | 32.0 / 31.7 / 31.7 / 31.6 | n/a | 18738.0 | 6330 | 159.7 avg / 172.7 peak | 66.0 | 16.0 GT/s PCIe x8 |
| 131K (131492) | DFlash 2 (--spec 16) | none (all in VRAM) | 3182.0 | 41.42 | 86.6 | 77.0 / 90.2 / 95.4 / 89.2 | 71.0% | 23228.0 | 6627 | 170.1 avg / 175.0 peak | 69.0 | 16.0 GT/s PCIe x8 |
| 131K (131492) | plain (--spec 0) | none (all in VRAM) | 3249.0 | 40.55 | 27.0 | 27.3 / 27.1 / 27.1 / 27.0 | n/a | 20850.0 | 6380 | 165.5 avg / 173.9 peak | 64.0 | 16.0 GT/s PCIe x8 |
| 256K (256115) | DFlash 2 (--spec 16) | 131072 | 2010.0 | 127.9 | 5.1 | 4.6 / 5.2 / 5.7 / 5.2 | 77.0% | 23482.0 | 10946 | 148.0 avg / 175.4 peak | 71.0 | 16.0 GT/s PCIe x8 |
| 256K (256115) | plain (--spec 0) | 196608 | 2030.0 | 126.44 | 4.7 | 4.7 / 4.8 / 4.7 / 4.7 | n/a | 23068.0 | 8533 | 150.0 avg / 174.9 peak | 71.0 | 16.0 GT/s PCIe x8 |

`D1..D4` are four equal quarters of **one continuous answer** (512 tokens, cut at exact token
boundaries of the streamed response), not four separate requests.
Rows are never averaged across different prompt content: chat, code and JSON arms are listed separately.
Task arms use `--spec 16` (DFlash 2) and are shown only as task-specific numbers.

## Task arms (different prompt content, same engine settings)

| task arm | prompt tokens | prefill tok/s | TTFT s | decode tok/s | D1 / D2 / D3 / D4 tok/s | draft accept |
|---|---|---|---|---|---|---|
| Bjson4k | 4179 | 7129 | 0.63 | 194.3 | 169.0 / 192.0 / 186.2 / 264.3 | 69.0% |
| Bcode32k | 32564 | 5625 | 5.84 | 106.3 | 93.3 / 114.0 / 111.3 / 112.9 | 56.0% |
| Bjson32k | 32937 | 5553 | 5.98 | 144.5 | 114.4 / 155.6 / 179.9 / 150.7 | 67.0% |
| Bcode64k | 65541 | 4480 | 14.69 | 73.4 | 74.2 / 77.9 / 74.7 / 68.8 | 49.0% |

## Context ceiling with the whole KV cache in VRAM

| mode | largest context that starts with KV fully in VRAM | first rejected value | note |
|---|---|---|---|
| spec 0 | 203776 | 205824 | 204K fits, 206K refused |
| spec 16 | 140288 | 142336 | 140K fits, 142K refused |

Measured at those ceilings:

| run | actual prompt tokens | mode | max-context | prefill tok/s | TTFT s | decode tok/s | D1 / D2 / D3 / D4 | VRAM peak MiB | KV in RAM |
|---|---|---|---|---|---|---|---|---|---|
| CEIL140288_s16 | 134561 | DFlash 2 | 140288 | 3136 | 43.09 | 64.7 | 55.0 / 78.5 / 76.9 / 63.6 | 23498 | none |
| CEIL203776_s0 | 197886 | plain | 203776 | 2476 | 80.04 | 23.5 | 23.9 / 23.5 / 23.5 / 23.5 | 23160 | none |

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

3. **DFlash 2 gain (median decode speed):**

| context (tokens) | plain tok/s | DFlash 2 tok/s | speedup | KV positions in VRAM (plain / DFlash) |
|---|---|---|---|---|
| 4163 | 38.3 | 100.1 | x2.61 | all / all |
| 4165 | 37.3 | 121.0 | x3.24 | all / all |
| 31803 | 35.1 | 105.5 | x3.01 | all / all |
| 32649 | 35.0 | 113.1 | x3.23 | all / all |
| 65785 | 31.6 | 94.1 | x2.98 | all / all |
| 131492 | 27.0 | 86.6 | x3.21 | all / all |
| 256115 | 4.7 | 5.1 | x1.09 | 196608 / 131072 |

4. **Speed change inside the answer** (quarters of one continuous answer):

| context (tokens) | mode | D1 tok/s | D4 tok/s | D4 / D1 |
|---|---|---|---|---|
| 4163 | dflash2 | 104.6 | 82.0 | 0.78 |
| 4163 | plain | 38.5 | 38.4 | 1.0 |
| 4165 | dflash2 | 118.1 | 157.4 | 1.33 |
| 4165 | plain | 38.9 | 38.2 | 0.98 |
| 31803 | dflash2 | 87.8 | 101.9 | 1.16 |
| 31803 | plain | 35.5 | 35.1 | 0.99 |
| 32649 | dflash2 | 104.6 | 109.9 | 1.05 |
| 32649 | plain | 35.3 | 34.9 | 0.99 |
| 65785 | dflash2 | 78.8 | 100.2 | 1.27 |
| 65785 | plain | 32.0 | 31.6 | 0.99 |
| 131492 | dflash2 | 77.0 | 89.2 | 1.16 |
| 131492 | plain | 27.3 | 27.0 | 0.99 |
| 256115 | dflash2 | 4.6 | 5.2 | 1.13 |
| 256115 | plain | 4.7 | 4.7 | 1.0 |

5. **Maximum working context on 24 GB:** whole KV cache in VRAM is possible up to
**203,776 tokens without speculation** and **140,288 tokens with DFlash 2**;
measured at that ceiling:
- 134,561 tokens, max-context 140288, plain: prefill 3,136 tok/s, TTFT 43.09 s, decode 64.7 tok/s, VRAM peak 23,498 MiB
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
