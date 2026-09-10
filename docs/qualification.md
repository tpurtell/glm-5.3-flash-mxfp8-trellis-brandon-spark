# Two-Spark qualification plan

The active task uses **emu and kiwi only**, one GB10 each. All remaining work
runs sequentially on this pair. Four-Spark qualification is canceled. Retired
hosts dodo and ostrich must not be accessed; they are reserved for DeepSeek
Flash development. Historical result receipts remain as provenance;
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
three prompts. These are preliminary results, not completed performance qualification.
Retained-cache checks verify actual 6144-token reuse and recomputed base tails.

Preliminary one-wave target-only decode screens and a one-replay weighted
baseline are in `results/screening/`. They are not final five-replay comparisons.
The graph counting C4 screen contains an early-terminated response and repeated
numbers; the orchid baseline hit its cap and overlapped tiny transfer checks.
Those limitations remain recorded and must not become qualified headline scores.
DFlash2 K7 graph serving passed the three basic thinking/tool checks and
produced observed draft acceptance. Its one-replay weighted screen measured
19.65 tokens/s (8/8 content contracts passed), with a separate 52.74 tokens/s
orchid probe that emitted exactly 100 repetitions. These remain screening
results; the requested five-replay weighted/orchid block is still pending.

The five-wave DFlash2 Mia-style decode block completed 45 waves / 105 responses.
Its timing medians and deltas are now in the README. Nine counting/code outputs
departed from the requested prefix. Eager NVFP4 and FP8 controls each produced
seven failures out of 70 concurrent responses and one out of 15 serial suffix
probes, in different responses. Historical target-only failures also exist.
These controls do not identify a root cause, show that all symptoms share one,
or qualify output correctness. Preserve failures when reporting performance.

MTP K2 now passes the basic thinking/tool checks after correcting the draft
model's ModelOpt metadata prefix mapping. Its full five-replay weighted block
measured **24.05 tokens/s**, with **40/40** content checks passing. The separate
orchid median was **28.49 tokens/s**, with **0/5** instruction checks passing;
these orchid rates do not establish output quality. This block used TP2 graphs
and an 8192-token context. Larger-context capacity and performance still require
their own measurements.

The MTP K2 cold-prefill block now records five replays at each of six sizes.
All 25 samples at 8K through 128K pass with zero cached tokens; the 128K median
is 1546.42 tokens/s, 1.0% below Mia's pinned E3 reference. All five 256K requests
were rejected by the configured 165000-token context limit. The complete block
retains a failed status and those diagnostics. This is a configured limit, not
a measured hardware ceiling; larger-context tuning remains pending. The README
reports the measured deltas and the differing MTP/batch/context settings.

| Completed evidence | Receipt and interpretation |
|---|---|
| DFlash2 smoke checks | [Thinking, tool parsing, and draft proposals](../results/bringup/emu-kiwi-dflash2-7-resumed-responses/README.md) |
| DFlash2 one-replay weighted/orchid | [Separate rates and limitations](../results/screening/emu-kiwi-dflash2-7-resumed-weighted/README.md) |
| Five-wave Mia-style decode | [All timings and output audit](../results/2x/dflash2-k7-mia-decode/README.md) |
| MTP K2 smoke checks | [Thinking, tool parsing, and draft proposals](../results/bringup/emu-kiwi-mtp2-mapper-fixed-responses/README.md) |
| MTP K2 five-replay weighted/orchid | [Weighted rates and orchid failures](../results/2x/mtp2-weighted/README.md) |
| MTP K2 five-replay cold prefill | [25 supported samples and five configured-limit rejections](../results/2x/mtp2-mia-prefill/README.md) |
| MTP K2 retained prefill | [Full 60-cell matrix, cache-policy accounting and failures](../results/2x/mtp2-retained-prefill/README.md) |
| Historical target-only output audit | [Failures without speculation or graphs](../results/bringup/historical-target-only-output-audit/README.md) |
| Eager NVFP4 control | [Concurrent](../results/bringup/emu-kiwi-dflash2-k7-eager-concurrency/README.md), [serial](../results/bringup/emu-kiwi-dflash2-k7-eager-serial-suffix/README.md) |
| Eager FP8 control | [Concurrent](../results/bringup/emu-kiwi-dflash2-k7-eager-fp8kv-concurrency/README.md), [serial](../results/bringup/emu-kiwi-dflash2-k7-eager-fp8kv-serial-suffix/README.md) |

Remaining speculation/TP2/EP2 and larger-context tuning, DFlash2 five-replay
weighted/orchid, retained decode and further context tuning, concurrency suite, tool evaluation,
needle retrieval, startup measurements and final package qualification remain
pending. No completed timing block substitutes for those remaining deliverables.
