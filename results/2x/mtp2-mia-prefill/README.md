# MTP K2 cold prefill: five replays per size

All 25 samples from approximately 8K through 128K completed with thinking off,
zero cached tokens, valid streamed usage and no reasoning leakage. Five 256K
requests were rejected with HTTP 400 because this launch is configured for
165000 tokens. The full benchmark exits 1 and retains status `failed`; it is
not a six-size passing block. The configured limit is not a measured hardware
capacity ceiling.

| Nominal prompt | Median tokens/s | Mia E3 tokens/s | Delta |
|---|---:|---:|---:|
| 8K | 1390.03 | 1492.1 | -6.8% |
| 16K | 1477.22 | 1553.7 | -4.9% |
| 32K | 1517.88 | 1428.2 | +6.3% |
| 64K | 1548.45 | 1587.0 | -2.4% |
| 128K | 1546.42 | 1561.7 | -1.0% |
| 256K | Configured-context rejection, 5/5 | 1516.8 | — |

Rate is server-reported prompt tokens divided by client time to first streamed
token. Prompts use salted filler and an eight-token generation cap. Actual
prompt counts include template and instruction overhead. This measures cold
prefix-cache prefill, not cold model startup. Raw requests, SSE events, usage,
metrics and HTTP error bodies are retained. `audit.py` verifies all 30 cells,
thinking-off requests, zero cache reuse and the rate calculation, and writes
the per-sample records and medians in `audit.json`.

TrellisMX configuration: emu/kiwi TP2 graphs, MTP K2, NVFP4 MLA cache,
165000 context, batch 1024, four sequence slots, memory utilization 0.895,
hybrid block 6144, image dcc6559, runtime 3ac1597. No other benchmark or
transfer workload ran concurrently. Retained benchmarks started only after
this block finished.

Reference: [Mia's pinned September 7 E3 README](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks/blob/94bddea5db64137db41e4ef4c6c120e6e69e32d7/README.md).
Its reported configuration is DFlash2 K7, batch 7168, 900000 context,
memory utilization 0.86, four sequence slots and thinking off. The shared
client rate definition permits a recipe comparison; the speculation method,
batch size and context settings differ, so these deltas do not isolate the
effect of the quantization or kernel implementation. The separate decode
and weighted/orchid blocks retain their own settings and quality limitations.
