# TP2 target-only CUDA-graph decode screen

One screening wave per cell, 400-token cap, temperature zero, thinking off.
Same emu + kiwi, image, 8192 context, 1024 batch-token limit, four sequences,
and NVFP4 cache settings as the eager screen. Full five-wave comparison and
weighted workload qualification remain pending.

| Workload | C | Graph aggregate tok/s | Eager aggregate tok/s | Change |
|---|---:|---:|---:|---:|
| structured | 1 | 14.96 | 10.24 | +46.1% |
| structured | 2 | 28.27 | 23.53 | +20.2% |
| structured | 4 | 38.86 | 41.38 | -6.1% |
| code | 1 | 15.00 | 10.14 | +47.9% |
| code | 2 | 27.31 | 23.38 | +16.8% |
| code | 4 | 43.39 | 42.41 | +2.3% |
| prose | 1 | 14.94 | 9.94 | +50.3% |
| prose | 2 | 27.50 | 23.69 | +16.1% |
| prose | 4 | 41.74 | 41.18 | +1.4% |

All 21 responses passed transport, usage, decode-window and thinking-off checks.
Twenty reached 400 tokens. Counting C4 stream 1 ended at 218 tokens, repeated
77 and 78, and added `stream 1/4 ends here`. That sample is preserved; the
counting C4 row uses actual generated token counts and is not a uniform-length
400-token comparison. Its transport pass is not a content-quality pass.

C1 improves on all three workloads; C4 does not improve consistently in this
single-wave screen. No universal speedup or quality equivalence is claimed.
Performance traffic was serialized across the graph and EP2 candidates.
