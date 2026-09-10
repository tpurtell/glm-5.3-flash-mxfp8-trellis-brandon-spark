# Live retained-cache accounting check

TP2 eager, target-only, NVFP4 dynamic cache, 6144-token engine block size.
All six measured requests passed exact usage and server histogram checks:
nominal bases 0, 6144, and 7168, with 512 fresh tokens and two repeats each.
Both nonzero bases reused exactly 6144 tokens. The 7168 base recomputed its
1024-token tail, yielding 1536 computed tokens for a 512-token fresh suffix.

This small matrix validates live cache/timing accounting. It is not the requested
full 0/32K/64K/128K/256K performance matrix and is excluded from the README
comparison. Raw SSE responses, usage, prompt IDs and metrics are preserved.
