# Retained-context prefill protocol

`scripts/bench-retained-prefill.py` measures the requested 5×6 matrix: retained
bases 0/32K/64K/128K/256K, fresh suffixes 1K/2K/4K/8K/16K/32K, two repeats.
Run each topology in a separate output directory and commit completed blocks
separately. This is distinct from the cold sparkDash-style comparison.

The client uses the pinned carrier tokenizer and the explicit serving template's
thinking-off wrappers. It sends token IDs to `/v1/completions` so the planned
prompt length is exact. Source files supply inert filler; their content hash,
tokenizer hash, template hash, raw prompt IDs, SSE responses, metric snapshots,
and launch receipt are retained. A unique run/branch marker prevents accidental
reuse of earlier suffixes. The base is primed with a short extra suffix so its
last aligned cache block can be reused. This token-ID transport differs from the
GLMRT reference's chat/text fitting and is recorded as a protocol difference.

Every measured request must report **exactly** the planned cached base and
`base + suffix` prompt tokens. The launcher enables
`--enable-prompt-tokens-details`. Missing details, cache eviction, excess suffix
reuse, or token-count disagreement invalidate the cell. Failed repeats cannot
contribute a survivor-only median.

Primary throughput is fresh suffix tokens divided by the delta of vLLM's
`request_prefill_time_seconds_sum`. The histogram count must increase by exactly
one; this requires an otherwise idle server. The client allows up to 30 seconds
for delayed metric publication. Client TTFT and fresh tokens/TTFT are recorded
separately, not silently substituted for the server measurement. vLLM's request
prefill timer includes its scheduler/chunked-prefill boundaries; it is not claimed
to be identical to GLMRT's layerwave-only compute timer.

Example (inside an environment with the image's `tokenizers` and `transformers`):

```bash
python3 scripts/bench-retained-prefill.py \
  --tokenizer /home/tj/models/glm53-trellismx/carrier/tokenizer.json \
  --corpus-root /path/to/pinned/measurement-reference/python \
  --launch-receipt .work/launches/ACTUAL_LAUNCH.json \
  --out results/2x/retained-prefill
```

Eleven local transport/accounting tests pass. A mock-server smoke run using the
real pinned tokenizer and template also verified two bases, two suffixes and two
repeats. Those mock timings are excluded from results. Real server cache/timing
validation and the full performance matrices remain pending model bring-up.
