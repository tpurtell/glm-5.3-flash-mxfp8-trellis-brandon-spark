# Concurrency protocol

`scripts/bench-concurrency.py` runs the GLMRT code and exact-50 fixtures at
C1/C2/C4. Prompts and output budgets (320/99 tokens) match
`bench_real_full_concurrency.py` at reference revision
`dc6d9b8e1600e001cb1d4228bd911f4df8091f99`. Each cell gets two untimed warmup
waves and five measured waves. Worker threads synchronize before issuing a wave.

Each request gets a unique prefix before the task prompt. Unlike the GLMRT
reference's tokenizer-verified first-token marker bank, this uses run/fixture/
wave/lane identifiers and requires server-reported cached tokens to equal zero.
Missing cache details or any reuse invalidates the wave. This difference is
explicit; it is not a claim of byte-identical historical requests.

The client reports both:

- Aggregate decode throughput: sum of `(completion_tokens - 1)` across lanes,
  divided by the interval from the earliest first content to latest last content.
- End-to-end aggregate throughput: all completion tokens divided by the interval
  from earliest request start to latest request completion.

Per-stream rates and TTFT are also retained. C2/C4 scaling divides the median
aggregate decode rate by the same fixture's C1 median. Transport/cache failures
invalidate the cell; failing Python structural checks or exact-count output
checks remain in timing and are reported separately. No generated code executes.
Every warmup and measured response, request, SSE event, metric snapshot, source
hash, template receipt and launch receipt is retained.

```bash
python3 scripts/bench-concurrency.py \
  --launch-receipt .work/launches/ACTUAL_LAUNCH.json \
  --out results/2x/concurrency
```

Accounting tests distinguish decode-window throughput from request makespan,
reject missing/reused-cache evidence and prevent dropping failed lanes. Actual
C1/C2/C4 serving measurements remain pending complete model bring-up. This suite
is separate from the sparkDash-style concurrency measurements in the Mia table.
