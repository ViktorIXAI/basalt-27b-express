Qwen3.8-27B-QUASAR-NVFP4 (dense 27B, 4-bit) on Basalt v0.4.1, on a 24 GB laptop RTX 5090.
Numbers, not vibes. Full data + harness: https://github.com/ViktorIXAI/basalt-27b-express

1/ Decode speed, 4K context, one request, temp 0:
 - plain: 37 tok/s
 - DFlash 2 (spec 16): 120.5 tok/s
 - JSON output task: 194.3 tok/s (fastest quarter: 264.3 tok/s)

2/ DFlash 2 speedup by context length:
 4K x3.2 | 32K x3.0-3.2 | 66K x2.9 | 131K x3.2 | 256K x1.09
 Draft acceptance 49-77%; code tasks accept less than JSON tasks.

3/ Speed inside one 512-token answer (4 quarters):
 plain stays flat (D4/D1 = 0.98-1.00).
 DFlash 2 accelerates as the answer goes: 66K 79->99->106->100, 131K 77->90->95->89 tok/s.

4/ Where 24 GB stops (whole KV cache in VRAM):
 140,288 tokens with DFlash 2, 203,776 without (engine refuses one step higher,
 and it prints the exact numbers: "of 224000 cells need 9575 MiB, 9487 MiB are free").
 At the ceiling (plain, 203,776 max-context): 197,886 actual prompt tokens -> 23.5 tok/s decode, TTFT 80.04 s, prefill 2,476 tok/s

5/ Past the ceiling we used --kv-resident (part of KV in RAM). 256K: 4.7 tok/s plain, 5.1 tok/s DFlash 2.
 Reason: this laptop's GPU link trains at PCIe 4.0 x8 -> measured 14.4 GB/s host->device.
 Speculation cannot help when the bus is the bottleneck.

6/ Long-context correctness, two methods:
 "List every control record hidden in 131K/256K tokens" -> 0/5, answer was
 "I cannot find any CONTROL records in the provided text."
 Ask each record by its exact id -> 5/5 correct at 131K and at 256K.
 Retrieval works; the enumerate-everything instruction does not trigger it.

Method: token counts from the engine's /tokenize after the chat template, quarters cut at exact
token boundaries of one continuous streamed answer, failures kept with the engine's own refusal text.
