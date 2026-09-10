# EP bring-up failures and correction

The first mixed-route test found uninitialized skipped route outputs in grouped
batches. Runtime `638309c` zeroes those slots. A second mismatch at 256 tokens
persisted: repeated eager calls produced different packed inputs for a few tokens.
The diagnostic logs compare route outputs and packed input/scale buffers; they
are correctness diagnostics, not performance profiling.

An experimental batch-end barrier alone did not fix the discrepancy. Inspection
then found that the M64 routing kernel has ten warps (five token pairs), but the
pair synchronization helper mapped pairs 2, 3 and 4 to the same named barrier.
Each pair now has a distinct barrier; a batch-end barrier also prevents early
reuse of the CTA's shared batch index. The corrected diagnostic has identical
packed inputs and route outputs over six calls.

These intermediate logs were collected during development. The authoritative
clean-commit acceptance runs are the adjacent `native-ep2-k5-layer3` and
`native-ep4-k5-layer3` receipts at runtime `58d3ef0`, including owned, mixed and
remote routes plus input mutation during graph replay. Full serving remains
unqualified.
