# Historical target-only counting output audit

Rechecking the existing one-wave structured/counting screens finds deviations
from the requested 1-to-200 prefix in 4/7 eager responses and 5/7 graph responses.
Both runs used emu/kiwi with no MTP or DFlash2. The graph run includes a C1
failure; therefore the observed issue is not confined to concurrent execution.
The raw results were already preserved; this audit adds output checks without
running inference or accessing any remote host.

Several C2 responses repeat or restart numbers near 77, similar to the newer
DFlash2 graph failures. These symptoms already existed without speculation and
without graphs. This rules out either feature being necessary for every observed
counting failure; it does not identify the root cause or prove identical causes.
Prompt suffix, target/quantization behavior, cache and serving runtime remain
possible factors. Serial tests using the exact suffixed prompts are queued on
the current eager DFlash2 launch to isolate prompt suffix from concurrency.

Run `python3 results/bringup/historical-target-only-output-audit/audit.py` from any
working directory. It checks existing counting responses only, normalizing
whitespace and allowing a correct prefix truncated by the token cap. This is not
a comprehensive quality evaluation. Original performance figures remain timing
measurements, not evidence of full output correctness.
