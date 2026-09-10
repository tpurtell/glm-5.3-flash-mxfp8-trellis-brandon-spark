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

## Bring-up receipts

- Source import branch `trellismx-glm53-spark` published at `2a1e17f`.
- Native P8 class imports successfully with the imported package and local ARM64
  `ghcr.io/tpurtell/single-spark-glm-5.3-flash:dev` (PyTorch 2.13.0+cu130,
  CUTLASS DSL 4.6.2). This checks Python dependencies only, not GPU execution.
- `rdmasync --rdma=required --rdma-show-config` emu → dodo successfully negotiated
  two rails: 10.55.0.7 → .6 and 10.55.0.3 → .2. The probe was a small metadata file,
  not a model-bandwidth measurement. Host names use the existing SSH host keys.
- The development ARM64 container builds successfully with the P8 kernel package
  and a narrow ModelOpt adapter hook. The hook allows SM121 while retaining TP4
  and EP1 guards. Build-time imports pass; no full-model execution is implied.
  The rebuild on the pinned published September 5 base also passed, producing
  local image `sha256:fbc16727629d6251137975ec739a06fb3a0d81cbe914f5d18457d6f6c243424d`.
- This vLLM base lacks the Jovian `B12xWarmupUnit` extension. The adapter currently
  relies on vLLM's normal eager warmup before graph capture. Actual graph replay
  must pass before this can be treated as a serving recipe.

## Added comparison requirement

The README must lead with a concise differential against the pinned Mia README's
published two-Spark decode and cold-prefill figures. Reproduce the sparkDash
counting/code (400 tokens, T0, thinking off), prose and cold-prefill protocol;
inspect sparkDash source for exact prompts, concurrency and aggregation before
claiming a matched comparison. Preserve this block separately from the preferred
weighted seven-category suite (natural and constrained JSON split one category)
and orchid speed probe. Include both new two- and four-Spark measurements and
relative percent changes; distinguish hardware scaling and configuration changes.

## TP2 port status

Runtime branch `67c20df` adds a parent-hash-bound TP2 view of adjacent TP4
sidecars. It joins compressed words and native scale planes without decoding or
requantizing weights. Gate/up planes, three coupled scale roles, replicated
vectors and global sign slices retain their original order. Four CPU tests pass:
physical-plane reconstruction, role ordering, replicated-value rejection, and
TP2/TP4 sign equivalence. These are layout tests, not GPU numerical qualification.

The ARM64 adapter now accepts TP2/TP4 with EP off. The pinned-base image builds
with this branch. `scripts/check-native-p8.py` will compare native TP2 output
against its two TP4 parent outputs and require exact eager/graph-replay equality
at 1/8/32/128 token rows. This check is pending downloaded parent files and does
not replace an independent numerical oracle or full-model serving tests.

## Distributed transport bring-up

The published bring-up image passed NCCL/RoCE all-reduce on **emu + dodo** at
1/4,096/1,048,576 FP32 elements, including three exact CUDA graph replays per
size. Both ranks passed. NCCL logs selected NET/IB over both configured NICs.
This is transport correctness on that named pair, not a model performance result
or qualification of the default emu + kiwi pair. Raw logs and command receipt:
`results/bringup/roce-emu-dodo/`.

Bring-up image published (qualification pending):
`ghcr.io/tpurtell/glm-5.3-flash-trellismx-spark@sha256:bf64997c14affabe5dc5ece52bca5ac7000f4c268728d6c8f8467a34ea2c8c20`.

The initial transport test retained its last graph while destroying the NCCL
process group and hung at teardown. The corrected test releases that graph first.
A fresh run reproduced all six exact checks and exited successfully on both
ranks; complete receipts are in `results/bringup/roce-emu-dodo-clean/`. The original
run and its teardown failure remain recorded separately.

The default **emu + kiwi** pair and **emu + kiwi + dodo + ostrich** group now pass
the same three sizes in eager execution and exact graph replay. Every rank exits
cleanly. Their independent receipts are in `results/bringup/roce-default-2x/`
and `results/bringup/roce-4x/`. These checks qualify transport only.
