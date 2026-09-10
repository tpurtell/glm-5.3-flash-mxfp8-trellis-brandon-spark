# MTP K2 graph-serving weighted screen, emu/kiwi

One-replay weighted seven-category rate: **24.04 tokens/s**, with **7/8** output
contracts passed. All eight responses remain in the weighted rate; no transport
errors occurred. The receipt's passed status denotes timing/transport completion,
not a quality pass. The code answer includes explanatory prose after its Python
block, violating the exact-one-code-block contract. Its raw content is retained.

| Case | Decode tokens/s | Observed draft acceptance | Content contract |
|---|---:|---:|---|
| code | 27.87 | 84.8% | fail |
| math | 29.35 | 91.2% | pass |
| fable | 19.52 | 44.2% | pass |
| hello | 26.07 | 50.0% | pass |
| topic | 22.78 | 59.7% | pass |
| structured-json | 26.56 | 75.9% | pass |
| structured-json-schema | 24.80 | 71.4% | pass |
| multilingual | 24.13 | 64.9% | pass |

The separate orchid speed probe measured 28.39 tokens/s and hit its 1500-token
cap. It emitted 791 whitespace-separated words with extraneous text, failing the
exactly-100-orchids instruction. It is speed-only evidence, not valid instruction
following. Do not treat its timing as a like-for-like orchid comparison with the
DFlash2 probe that ended after exactly 100 repetitions.

Earlier same-pair one-replay weighted screens measured 15.04 tokens/s target-only
and 19.65 DFlash2 K7. This MTP screen is 59.8% and 22.3% higher respectively, but
it has a failed content contract and uses the rebuilt image with the MTP mapper
fix. Runs are not interleaved and outputs differ. No repeatable final speedup or
serving recommendation follows. Five-replay weighted measurements remain needed.

TP2, graphs, MTP two-token draft, NVFP4 MLA cache, context 8192, batch 1024,
four sequence slots and memory utilization 0.85. Actual hybrid block: 6144 tokens.
Benchmark requests disable thinking; ordinary serving retains thinking on.
All source/image/template identities, raw SSE and metrics snapshots are retained.
Metrics may lag per-request boundaries. No competing inference/transfer workload
was launched during the screen.
