# TASK SPEC — Basalt v0.4.1 express benchmark: Qwen3.8-27B-QUASAR-NVFP4 on a laptop RTX 5090 (24 GB)

Issued: 2026-11-16 (owner's spec, translated from Russian; the Russian original is the source of truth for the owner, this file is its English publication copy).
Time budget: 5 hours of wall-clock for preparation, measurement and reporting.
Ground rule: **no invented numbers, no extrapolation** — only what was actually measured. A configuration that does not run is recorded with its real failure reason.

## 1. Scope

Measure the real speed of `Qwen3.8-27B-QUASAR-NVFP4` (dense 27B, 4-bit NVFP4 weights, native 262 144-token context) on the Basalt v0.4.1 engine, on a **laptop** NVIDIA RTX 5090 with 24 GB VRAM, for contexts up to 256K tokens.

Deliverables: speed at five context sizes, decode speed broken into four quarters of one continuous answer, TTFT, prefill speed, peak VRAM/RAM, GPU power and temperature, the working `--kv-resident` value when the cache does not fit the card, and the DFlash 2 speculative-decoding gain versus plain decoding.

## 2. Preparation

1. Verify the installed Basalt v0.4.1 (tag + commit are recorded per run).
2. Download the official model pack if it is absent.
3. Record GPU, CPU, RAM and software versions.
4. Save the working production configuration before touching anything (the production brain runs on the same machine and is shut down for the benchmark window, then restored).
5. Enable logging of speed, VRAM, RAM, GPU power and GPU temperature (1 Hz sampler).

## 3. Context sizes

| Label | Tokens |
|---|---|
| short | 4 096 |
| medium | 32 768 |
| long | 65 536 |
| very long | 131 072 |
| maximum | 256 000 |

Per size: prefill tok/s, TTFT, decode tok/s, total response time, peak VRAM and RAM.
If 256K does not fit in VRAM, place part of the KV cache in RAM with `--kv-resident` and find the largest working context without spending long search times.

## 4. Two primary modes

| Mode | Flags | Meaning |
|---|---|---|
| A | `--spec 0 --kv int8` | no speculative decoding (baseline) |
| B | `--spec 16 --kv int8 --suffix-draft 0` | DFlash 2 block drafter, no prompt-lookup suffix drafting |

All other parameters identical, including effective KV placement where that is possible. One request at a time, `temperature 0`, thinking disabled.
Additionally, at 4K / 64K / 128K, check `--suffix-draft 3` if time allows.

## 5. Decode in four quarters (the main test)

Request ~512 generated tokens per context (256 if a large context makes 512 too slow; the actual length is recorded).
Measure speed on four stretches of **one continuous answer**:

| Stretch | Part of answer |
|---|---|
| D1 | 0–25 % |
| D2 | 25–50 % |
| D3 | 50–75 % |
| D4 | 75–100 % |

Record tok/s per stretch, the mean speed of the whole answer, and the D1/D4 ratio.
Use the engine's own measurements where available; otherwise use the available logging and state the approximation. Do not spend hours modifying the engine.

## 6. Prefill

Total prefill speed at all five sizes. For 64K / 128K / 256K also measure the first and last quarter of the input **if existing Basalt tools allow it**; if they do not, total prefill speed is sufficient. No source changes for this.

## 7. Three task types

| Type | What | Where |
|---|---|---|
| chat | technical question with a long answer; the main test | all five sizes |
| code | analyse code and propose a fix | 32K, 64K |
| JSON | generate JSON against a given schema | 4K, 32K |

All inputs are saved for reuse. Long contexts must **not** be filled with a single repeated phrase; the corpus here is real documentation and real source code from two project trees, assembled with a fixed seed.

## 8. Long-context correctness

At 128K and 256K, embed unique control records near the beginning, middle and end of the dump and ask the model to reproduce them. Record correctness separately: if the context is processed technically but the model answers wrong, that is reported as its own finding.

## 9. Memory and temperature

Per test: peak VRAM, RAM used, GPU power, GPU temperature, throttling indicators, the `--kv-resident` value used.
The key question: how much decode speed is lost at 128K–256K when the KV cache moves to system RAM.
No separate long stress tests.

## 10. Repetitions

4K and 32K: two measurements per primary mode. 64K and 128K: one mandatory measurement, repeat only a doubtful one. 256K: one successful measurement per available mode. A too-slow long test is kept as a partial result with a "not completed" note.

## 11. Time budget

| Stage | Budget |
|---|---|
| model + logging preparation | 30 min |
| 4K / 32K / 64K tests | 60 min |
| 128K and 256K tests | 90 min |
| JSON, code, correctness | 45 min |
| analysis, tables, report | 45 min |
| error reserve | 30 min |
| **total** | **300 min** |

The agent tracks the clock itself: if a stage runs long, cut the optional tests but keep the primary results.

## 12. Output

Final tables (speeds in tok/s):

```
Context  Prefill  Decode no-DFlash  Decode DFlash  VRAM  RAM
4K … 32K … 64K … 128K … 256K
```

```
Context  Mode            0–25%  25–50%  50–75%  75–100%
4K … 32K … 64K … 128K … 256K    (one row per mode)
```

Four charts in English: prefill speed vs context length; decode speed vs context length (plain and DFlash 2); decode speed across the four quarters; VRAM/RAM usage vs context length.

Artifacts in a separate directory: CSV tables, raw logs, exact launch parameters, PNG charts, a short technical report in Russian, and a short English summary for X. The report answers five questions: maximum speed reached; sustained speed; the DFlash 2 gain; how speed changes inside an answer; the largest context that actually works on 24 GB VRAM and at what speed.

## 13. Agent instructions

Work autonomously; do not ask for confirmation of each test. Do not break the working production configuration. Do not spend time on deep Basalt modifications — use existing tools, the API and the logs. If a test fails, save the reason and move on. Priority: real speed measurements, four decode quarters, the context limit, DFlash 2 versus plain decode. After five hours, stop, save everything measured and deliver the report even if secondary tests are missing.
