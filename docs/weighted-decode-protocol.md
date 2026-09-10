# Weighted decode and orchid

`scripts/decode_contract.py` preserves the prompt cases and non-executing output
validators from the pinned GLMRT reference's
`python/tools/bench_real_full_mtp_acceptance.py` (MIT license retained).
The eight cases represent seven equally weighted categories: Python, math,
creative prose, greeting, exposition, JSON, and Traditional Chinese. Natural and
schema-constrained JSON each carry weight 0.5. Their original output budgets are
preserved. This suite is separate from the sparkDash/Mia comparison client.

```bash
python3 scripts/bench-weighted-decode.py \
  --launch-receipt .work/launches/RUN/launch.json \
  --out results/2x/target-only-weighted
```

Run five complete replays for each qualified target-only, MTP and DFlash2
configuration on each topology. Retain the actual launch receipt and template
hash. The client uses T0, explicit thinking off, and streaming server token
usage. Prompts are repeated without a nonce; decode excludes TTFT. This differs
from reference runs that used unique nonce prefixes and is stated rather than
claiming a byte-identical replay.

Weighted rate pools `sum(weight × (completion tokens − 1))` divided by
`sum(weight × decode seconds)`. Output-check failures remain in timing and in
the numerator/denominator; transport or missing-metric failures invalidate the
block rather than silently filtering responses. The checks are prompt-contract
checks, not a general quality score, and generated code is never executed by this
client. Acceptance comes from before/after vLLM draft and accepted-token counters,
with raw metric snapshots retained. Target-only acceptance is null.

The separate orchid probe requests 100 repetitions with a 1,500-token cap, five
responses, and records speed only. It is excluded from the weighted rate and is
not a counting-quality test. Its prompt omits the reference's random nonce.

This client has not run against the full model yet. Parser behavior, actual metric
availability, and output checks must pass their live bring-up gates before results
are qualified.
