# DFlash2 K7 Mia-style decode: five waves, emu/kiwi

45 timing waves / 105 responses completed without transport errors or observed
reasoning leakage. 104 responses reached the 400-token cap; code-c4-r2 stream 0
stopped at 393 tokens and inserted prompt text into its output. The benchmark's
receipt status describes transport/timing validity, **not a quality pass**.

| Workload/concurrency | Median aggregate tokens/s over five waves |
|---|---:|
| structured-c1 | 53.52 |
| structured-c2 | 61.19 |
| structured-c4 | 89.81 |
| code-c1 | 52.59 |
| code-c2 | 64.56 |
| code-c4 | 83.41 |
| prose-c1 | 23.03 |
| prose-c2 | 28.39 |
| prose-c4 | 37.66 |

The deterministic output-prefix audit finds nine deviations: four counting
responses (three C2, one C4), and five code C4 responses. All C1 counting/code
responses match the requested prefix up to the token cap. Whitespace is
normalized for these prefix checks; truncated final output is allowed. Prose
has not received a semantic quality score. See `audit.json` for first mismatches
and `audit.py` to reproduce the timing medians and checks. No failed output is
excluded from timing statistics. C2/C4 quality remains unqualified.

Mia's published 62.9 C1 and 146.5 C4 aggregate structured/code rates compare with
our separate structured/code results. Mia prose 32.1 C1 uses adaptive verification
and FP8 dense layers; this candidate uses fixed K7 and the existing carrier dense
layers. Software, quantization and launch settings differ, so these are workload
comparisons rather than a quantization-only controlled A/B.

This run uses target/draft TP2, CUDA graphs, 8192 context, 1024 batch tokens,
four sequence slots, memory utilization 0.85, and thinking-off requests. Serving
still defaults to thinking on. The engine uses 6400-token hybrid cache blocks.
The source/launch/image/template identities and every raw SSE event are retained.
No competing inference or transfer workload was launched during this block.

Next: diagnose concurrent output corruption before selecting serving settings;
MTP, speculation tuning, cold prefill and remaining qualification are pending.
