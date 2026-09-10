# Retained-context decode protocol

`scripts/bench-retained-decode.py` preserves the three prompts from
`bench_release_decode_matrix.py` at measurement-reference revision
`dc6d9b8e1600e001cb1d4228bd911f4df8091f99`: Python interval merging, a parrot at
a night market, and the sum-of-cubes derivation. Each runs twice at retained
bases 0/32K/64K/128K/256K, temperature zero, with a 192-token response cap.

The client uses the same pinned tokenizer, explicit thinking-off template,
inert source corpus, exact token-ID transport, unique branch markers and cache
checks as the retained-prefill client. Every response must report exactly the
requested cached base and planned total prompt length. Source/tokenizer/template
hashes, raw token IDs, SSE events, text, usage, metric snapshots and launch
settings remain in the output directory. This uses vLLM completions with locally
rendered template wrappers; it is not a byte-identical replay of GLMRT chat
requests.

Decode throughput is `(completion_tokens - 1) / (last content arrival - first
content arrival)`. Token counts come from server usage, never SSE chunk counts.
This client-observed metric is separate from GLMRT's internal decode timer.
Missing usage, an invalid timing window, reasoning leakage or a cache mismatch
invalidates a sample and its cell median. Python structural output checks are
recorded without executing generated code; failing those checks does not remove
the timing sample. Writing and mathematical correctness require separate review;
the timing status is not a quality verdict.

Example inside the image's Python environment:

```bash
python3 scripts/bench-retained-decode.py \
  --tokenizer /home/tj/models/glm53-trellismx/carrier/tokenizer.json \
  --corpus-root /path/to/pinned/measurement-reference/python \
  --launch-receipt .work/launches/ACTUAL_LAUNCH.json \
  --out results/2x/retained-decode
```

A real-tokenizer/template smoke run against a mock server passed all 12 requests
across two bases, three workloads and two repeats. Mock timings are excluded
from results. Actual serving, cache validation and performance remain pending.
