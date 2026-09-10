# Emu/kiwi TP2 graphs, DFlash2 K7: one-replay weighted screen

Weighted seven-category rate: **19.65 tokens/s**.
All eight content-contract checks pass (JSON cases each have half weight),
with no transport errors. Thinking is explicitly off for these benchmark requests;
serving defaults remain on. This is screening, not the final five-replay block.

| Case | Decode tokens/s | Observed draft acceptance |
|---|---:|---:|
| code | 40.11 | 69.3% |
| math | 37.29 | 61.9% |
| fable | 12.77 | 12.6% |
| hello | 34.97 | 38.1% |
| topic | 19.97 | 27.5% |
| structured-json | 30.93 | 60.7% |
| structured-json-schema | 30.82 | 63.9% |
| multilingual | 15.95 | 18.8% |

The earlier same-pair TP2 graph target-only one-replay screen measured 15.04
weighted tokens/s, so this screen is 30.7% higher. Runs were not interleaved and
outputs differ; this does not establish a repeatable final speedup. Low prose
acceptance is a tuning concern: fable is slower than that target-only baseline.
Per-case metrics can lag request boundaries; raw snapshots are retained.

The separate orchid probe measured 52.74 tokens/s over 200 post-first tokens.
Its output contains exactly 100 space-separated copies of orchid and no other
words. The old target-only orchid probe hit the 1500-token cap and overlapped
tiny transfer checks, so it is not a controlled orchid speedup comparison.
No competing inference or transfer workload was launched during this screen.

Launch receipt records emu/kiwi, identical image IDs, target/draft TP2, graphs,
DFlash2 seven-token probabilistic draft / standard rejection, 8192 context,
1024 batch tokens, four sequence slots, and 0.85 memory utilization. Full Mia
comparison, MTP and further speculation tuning remain pending.
