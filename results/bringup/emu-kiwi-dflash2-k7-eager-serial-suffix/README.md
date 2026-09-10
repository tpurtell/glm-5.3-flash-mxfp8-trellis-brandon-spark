# Eager DFlash2 K7 serial suffix control

Fifteen requests were sent one at a time after the eager concurrency block
finished. Fourteen pass the normalized output-prefix check; one code response
fails. All five counting requests with `(stream 1/2)` pass; code with `(stream
2/4)` passes 4/5 and `(stream 1/4)` passes 5/5. Temperature is zero and thinking
is explicitly off, as in the earlier comparison. Same emu/kiwi launch and image.

The failed code response changes clamp_07's `if x < lo:` to `if x < lo, hi=1):`.
This resembles the malformed clamp_07 condition in earlier concurrent output.
The raw response and checker are retained. Concurrency is not necessary for
every code failure, and graphs are disabled here. The passing serial counting
samples do not establish that counting failures require concurrency. These small
samples do not establish reliable failure rates or a root cause.

Next controlled variable: compare the same eager DFlash2 K7 setup using FP8
instead of NVFP4 MLA KV cache. This tests cache precision while preserving the
target weights, draft configuration, template, prompts and execution mode.
