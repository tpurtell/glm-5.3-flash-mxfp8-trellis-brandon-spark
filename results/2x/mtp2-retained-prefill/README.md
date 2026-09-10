# MTP K2 retained prefill: full 60-cell matrix

All five bases × six suffix sizes × two repeats were attempted. **48 requests
returned valid timing and usage**, and all 48 match the installed runtime's
one-block EAGLE/MTP cache-drop policy. The 12 requests at a 256K base and that
base's prime were rejected with HTTP 400 by the configured 165000-token limit.
This does not establish a hardware capacity ceiling.

The original strict receipt remains **failed**: 12 zero-base cells pass,
36 retained cells fail its expectation of full aligned-base reuse, and 12
cells fail after rejected priming. No original result was rewritten. The
separate audit reports observed cache behavior and timings; it is not a claim
that the original exact-cache contract passed.

Median **fresh suffix tokens / server prefill seconds**, two repeats:

| Base | +1K | +2K | +4K | +8K | +16K | +32K |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 1192.5 | 1179.6 | 1123.0 | 1132.7 | 1115.7 | 1113.2 |
| 32K | 123.8 | 222.0 | 370.5 | 553.9 | 737.8 | 885.9 |
| 64K | 100.5 | 183.8 | 314.8 | 489.2 | 676.7 | 840.2 |
| 128K | 120.9 | 209.2 | 352.1 | 517.2 | 655.7 | 779.8 |
| 256K | Rejected | Rejected | Rejected | Rejected | Rejected | Rejected |

| Base tokens | Aligned base | Actual cached, every sample | Recomputed base |
|---|---:|---:|---:|
| 32768 | 30720 | 24576 | 8192 |
| 65536 | 61440 | 55296 | 10240 |
| 131072 | 129024 | 122880 | 8192 |

The installed cache manager explicitly drops a matched block for EAGLE/MTP
recomputation. With 6144-token hybrid blocks, this predicts the observed cache
counts at every tested base. `cache-policy-source.json` preserves excerpts and
hashes from image dcc6559. This explains the difference from the benchmark's
aligned-base assumption; it does not remove the latency cost. Small suffixes
must pay for thousands of recomputed base tokens.

`audit.py` verifies the complete matrix, exact prompt lengths, successful
priming, one server histogram sample per measured request, positive timing,
and actual cache counts. `audit.json` retains every error and reports both fresh
tokens/s and all computed tokens/s, plus client TTFT. The table uses fresh
tokens/s, so recomputation is never credited as useful new input throughput.

Configuration: emu/kiwi TP2 graphs, MTP K2, NVFP4 MLA cache, context 165000,
batch 1024, four sequence slots, memory utilization 0.895, image dcc6559,
runtime 3ac1597. Inputs use the pinned thinking-off template and tokenized source
corpus, with one output token. They differ from the Mia filler prefill and are
not semantic output-quality tests. No competing inference or transfer workload
was launched during this block. Raw token prompts, usage, SSE, metrics and
launch provenance are retained.
