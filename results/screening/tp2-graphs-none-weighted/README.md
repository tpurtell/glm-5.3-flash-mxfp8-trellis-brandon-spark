# TP2 graph target-only weighted baseline screen

One replay of the preferred seven-category mix (eight cases, natural and
constrained JSON each half-weight), thinking off, no MTP or DFlash2.
Weighted decode: **15.04096 tokens/s**; all **8/8** output-contract checks passed.
This is a screening baseline, not the final five-replay performance block or a
comprehensive quality evaluation.

The separate orchid speed probe measured 14.95623 tokens/s and hit its 1500-token
cap, despite requesting 100 words. It is a speed probe, not an instruction-following
pass. Tiny transfer-helper validation overlapped this probe, so its timing is
provisional and must be rerun in the isolated final block. The eight weighted
workloads had finished before those transfer checks began. Raw responses,
usage, speculation counters and prompt/contract identities are preserved.
