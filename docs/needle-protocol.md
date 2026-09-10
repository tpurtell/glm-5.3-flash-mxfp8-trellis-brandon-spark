# Needle retrieval protocol

`scripts/bench-needle.py` runs 15 cells: nominal 8K/32K/128K/256K/384K
contexts at 10%/50%/90% filler depth. It preserves the reference archive filler,
Zephyr access-code question, deterministic session-bound key generation and
±8-token fitting tolerance from GLMRT revision
`dc6d9b8e1600e001cb1d4228bd911f4df8091f99`. Rendering uses our pinned Z.ai
serving template with thinking explicitly disabled.

Each answer has a 32-token cap. Success requires the exact key after stripping
outer whitespace, no reasoning leakage, matching server/local prompt counts,
and completion within the configured time limit (600 seconds by default).
The limit also sets the HTTP socket timeout. A response that exceeds the total
wall-time limit fails even if its key is correct. Requests rejected for context
capacity are retained as failed cells, never inferred passes or silently omitted.

The output directory retains each request and prompt contract, exact key,
prompt-token hash, raw SSE response, usage, text, elapsed time, metrics and
source/tokenizer/template/launch identities. The depth denotes the fraction of
filler before the needle; template and question overhead is recorded in total
prompt tokens. Token fitting is the same reference algorithm with the updated
chat renderer, not an assertion of byte-identical historical prompts.

```bash
python3 scripts/bench-needle.py \
  --tokenizer /home/tj/models/glm53-trellismx/carrier/tokenizer.json \
  --launch-receipt .work/launches/ACTUAL_LAUNCH.json \
  --out results/2x/needle
```

`--plan-only` constructs all prompts without contacting a server. All 15 prompt
contracts passed this check using the actual pinned tokenizer and template.
This proves prompt construction only; model retrieval results remain pending.
