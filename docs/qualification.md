# Two-Spark qualification plan

The active task uses **kiwi and dodo only**, one GB10 each. All remaining work
runs sequentially on this pair. Four-Spark qualification is canceled. Retired
hosts must not be accessed. Historical result receipts remain as provenance;
they do not authorize new runs or establish current recommendations.

## Remaining qualification

Compare TP2 and EP2, eager and CUDA-graph serving, and fresh target-only, MTP,
and DFlash2 candidates on this quant. Measure proposal acceptance and output
quality as well as speed. Select the serving settings from actual results.
Keep serving thinking enabled; explicitly disable it for the Mia comparison.

Complete and publish these two-Spark blocks separately:

1. Mia-style decode and cold prefill with thinking off, matching the pinned
   protocol; put measured deltas against Mia at the top of the README.
2. Preferred weighted seven-category decode (eight cases, JSON half weights),
   five replays, plus the separate orchid speed probe.
3. Retained prefill: bases 0/32K/64K/128K/256K crossed with fresh suffixes
   1K/2K/4K/8K/16K/32K, two repeats. Verify actual cache reuse and report any
   recomputed base tail caused by hybrid block alignment.
4. Retained decode: Python/creative/math at the same bases, two responses each.
5. Concurrency at C1/C2/C4. These are request counts, not numbers of Sparks.
6. Tool evaluation: all 88 cases, three seeds, including every failure.
7. Needle retrieval: 8K/32K/128K/256K/384K at 10%/50%/90% depth. Record any
   capacity limit explicitly; never infer a pass beyond measured capacity.
8. Cold/warm startup timings in a table, using the documented definitions.

No Pi agent task, micro-timeline, profiler, or startup graph is required.
Runtime changes remain on the `trellismx-glm53-spark` branch of the runtime
fork. Publish the package privately and commit/push each completed test block.

## Current evidence

Pinned model files are verified and stored in the real HF cache. TP2 native
numerical checks and mutable CUDA-graph checks pass. The original checkpoint's
four TP shard files remain necessary input data for TP2/EP2 repacking; they do
not imply a four-machine deployment.

Earlier emu/kiwi runs passed basic thinking and tool-parser checks with
target-only eager and graph serving. Graph responses matched eager on those
three prompts. These are historical results, not qualification of kiwi/dodo.
Retained-cache checks verify actual 6144-token reuse and recomputed base tails.

Preliminary one-wave target-only decode screens and a one-replay weighted
baseline are in `results/screening/`. They are not final five-replay comparisons.
The graph counting C4 screen contains an early-terminated response and repeated
numbers; the orchid baseline hit its cap and overlapped tiny transfer checks.
Those limitations remain recorded and must not become qualified headline scores.
Fresh speculation qualification and the full matrices above are still pending.
