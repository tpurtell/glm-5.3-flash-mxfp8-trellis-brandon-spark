# MTP K2: five weighted replays and five orchid probes

The complete weighted seven-category aggregate is **24.05 tokens/s** across
40 responses (eight cases per replay, JSON cases each half weight). All **40/40**
content-contract checks pass, with no transport errors. The aggregate is total
weighted post-first tokens divided by total weighted decode time, not an average
of per-case rates. All raw requests, SSE, usage and metrics are retained.

| Replay | Weighted tokens/s | Content checks |
|---|---:|---:|
| 1 | 23.95 | 8/8 |
| 2 | 24.30 | 8/8 |
| 3 | 23.80 | 8/8 |
| 4 | 24.21 | 8/8 |
| 5 | 24.01 | 8/8 |

Orchid median speed is **28.49 tokens/s**, but **0/5** probes satisfy exactly
100 space-separated copies with no extra text. Four hit the 1500-token cap; one
stopped at 1402 tokens. Outputs contain 799, 833, 972, 736 and 805 words. These
are speed-only results, not instruction-following successes. `summary.json`
records each probe and the per-replay rates.

This supersedes the one-replay MTP screen for rate estimation, but does not erase
its observed code-format failure. The successful forty contracts here are narrow
checks, not broad quality qualification. Earlier counting/code failures and the
orchid failures remain unresolved and visible. No bad response was removed to
improve timing; benchmark receipt status denotes transport/timing completion.

Launch: emu/kiwi, TP2 graphs, MTP two-token draft, NVFP4 MLA cache, context 8192,
batch 1024, four sequence slots, memory utilization 0.85. Actual hybrid block
size 6144. Image dcc6559 / runtime 3ac1597 includes the MTP metadata mapper fix.
Thinking is off for these comparison requests; ordinary serving defaults to on.
No competing inference or transfer workload was launched during this block.
This block is separate from Mia-style decode/prefill. Large-context performance,
EP2 comparison, tool evaluation and other qualification remain pending.
