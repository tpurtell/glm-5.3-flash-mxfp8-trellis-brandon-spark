# Separate Mia-style comparison block

Source protocol: sparkDash revision `f035ca243855b3a88c270a9a84a358c2cb1fbcc3`,
`src/shared/llmPrompts.js`, `server/collectors/DecodeBench.js`,
`PrefillBench.js`, and `LlmStreaming.js`. Prompt strings in `data/mia-prompts.json`
are extracted from that revision. Its MIT license is in `licenses/`.

The README's Mia values come from the pinned Mia recipe README, not a rerun here.
Its historical dashboard revision is not identified, so this reproduces the
published workload style using inspected current sparkDash source. Do not call
it a controlled quantization-only A/B. Hardware count, software and launch
settings differ; the receipts must make those differences visible.

Decode uses the exact counting, clamp_00–49 and hash-map prompts, 32-token warmup,
T0/top_p1, thinking off, 400-token cap, C1/C2/C4, five waves per cell. Concurrent
prompts receive the same `(stream i/n)` suffix as sparkDash. Per-stream rate is
(completion tokens − 1)/(last content time − first content time); aggregate rate
uses the total post-first tokens across the earliest-first/latest-last window.
Raw SSE events, requests and usage are saved. Missing usage fails the cell;
there is no chunk-count token estimate. Failed responses are retained and make
the block fail, not silently excluded from the final result.

Prefill uses sparkDash's salted ` the` filler construction, 512-token warmup and
8-token generation cap. Each rung is a fresh C1 request; the server's sequence
capacity may be four (the recipe README's C4 setting). Record actual prompt
counts and TTFT; nominal targets are only labels. This block records per-cell
metrics snapshots to check prefix-cache activity. Unlike retained-context
prefill, throughput is the whole prompt token count divided by TTFT.

Run each block for each topology after runtime qualification:

```bash
python3 scripts/bench-mia-style.py decode --launch-receipt .work/launches/RUN/launch.json --out results/2x/mia-decode
python3 scripts/bench-mia-style.py prefill --launch-receipt .work/launches/RUN/launch.json --out results/2x/mia-prefill
```

Select the actual four-node receipt and distinct output directories for 4x.
This client is implemented; no live-model measurements have completed yet.
It complements the weighted seven-category and orchid suite.
