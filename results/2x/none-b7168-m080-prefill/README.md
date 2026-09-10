# Corrected cold prefill (no spec): startup memory failure

No prefill requests were sent and no throughput was measured. All six requested
size rows are null because the engine failed before readiness.

The emu/kiwi TP2 launch used batch 7168, memory utilization 0.80, four sequence
slots, NVFP4 MLA cache, CUDA graphs, and no DFlash2 or MTP. The context limit was
9000, sufficient for the smallest approximately 8K prompt. Image identity and
complete arguments are in `launch.json`; raw logs from both ranks are retained.

Emu loaded 96.23 GiB of model weights. Profiling reported 100.35 GiB non-KV
memory, an estimated 1.19 GiB CUDA-graph reservation, and **−4.23 GiB available
KV memory** against 121.63 GiB total GPU memory. Initialization failed with
`No available memory for the cache blocks`. Reducing prompt length cannot repair
a negative startup KV budget. The 0.80 limit was not raised.

This is an allocation failure under the requested configuration, not zero
tokens/s, a measured slowdown, or evidence of an expert-format speed difference.
The failed head exited; the remaining kiwi worker was explicitly stopped.
