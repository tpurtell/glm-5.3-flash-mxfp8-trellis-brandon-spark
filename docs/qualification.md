# Qualification plan and current evidence

## Hardware

Verified 2026-09-10 through local/SSH queries: ostrich, dodo, emu, kiwi each have
one NVIDIA GB10. No running Docker containers were present. Emu is the download
host. CX7 addresses on the first rail are 10.55.0.1, .2, .3, .4 respectively;
the second rail uses .5, .6, .7, .8.

## Runtime gates

The pinned upstream vLLM adapter rejects anything except SM120, TP4, EP1,
intermediate partition 512. GB10 is SM121. The native P8 kernel has TP2 hooks
but references an unpublished `glm53_nvfp4.p8_tp2_repack` helper for parent-pair
loading. These are porting requirements, not evidence that 2x or 4x works.

Before performance: verify checkpoint hashes, native P8 numerical correctness,
TP2 repacking equivalence, SM121 execution, CUDA graph replay, full-model output,
and DFlash2 behavior against the same target without speculation.

Screen TP2 with EP off/on on two Sparks and TP4 with EP off/on on four Sparks.
Record unsupported candidates and the actual cause; add other valid TP/EP
factorizations if the loader and model support them. Select based on measured
mixed decode, prefill, and concurrency; preserve losses and failures. DFlash2
must be freshly swept against target-only and native MTP, including fixed K and
adaptive policies if supported. Do not reuse EXL3 acceptance or recommendations.

## Required blocks for each topology

1. Speculation qualification: five full replays of eight semantic workloads
   (Python, math, creative prose, short response, exposition, natural JSON,
   constrained JSON, multilingual), correctness checks, acceptance, weighted
   decode with half weight for each JSON variant; low-entropy speed probe.
2. Prefill: retained base 0/32K/64K/128K/256K crossed with fresh suffix
   1K/2K/4K/8K/16K/32K; report median new-suffix throughput and cache evidence.
3. Retained-context decode: Python/creative/math at the same bases, two
   deterministic responses each, 192-token cap.
4. Concurrency: C1/C2/C4 aggregate throughput and scaling.
5. Tool use: pinned tool-eval-bench, 88 scenarios including hard mode, three
   distinct seeds; record scorer revision and all failures.
6. Needle retrieval: 8K/32K/128K/256K/384K at 10%/50%/90% depth, exact keys,
   prompt token counts, and request times.
7. Startup: explicit cold and warm definitions, readiness wall time in a table.

Preserve raw responses, metrics, launch settings, commands, revisions, hardware,
and failures. A context beyond tested capacity is an explicit limitation, never
an inferred pass. Performance runs use no profiler. No pi agent task,
micro-timeline benchmark, startup graph, or performance-profile comparison.

Commit and push each completed topology/block independently. Published plots
must derive from this recipe's raw measurements, never source-project numbers.
