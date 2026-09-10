# MTP K2 at 165,000-token configured context

Emu/kiwi TP2 graph serving passes all three response contracts: default thinking
answers 17 × 23 = 391 with reasoning, explicit thinking-off returns exactly
391 with null reasoning, and default thinking produces the parsed
`get_weather({"city":"Taipei"})` call. No external tool was executed.
Completion counts are respectively 90, 3 and 40 tokens.

Observed metric deltas show 98 proposed and 84 accepted draft tokens (85.71%).
Exporter lag prevents interpreting this as synchronized per-request acceptance.
These are smoke checks, not decode speed or broad quality scores.

Configuration: two Sparks, TP2, MTP two-token draft, CUDA graphs, NVFP4 MLA
cache, context 165000, batch 1024, four sequence slots, memory utilization
0.895. Image `dcc6559`, runtime `3ac1597`; the draft uses base Marlin MXFP8
and target routed experts use private TrellisMX. Actual hybrid cache block size
is 6144. The launch reached readiness in 1023.44 seconds. This is an observed
launch duration, not a controlled cold/warm startup comparison.

Emu reports 99.5 GiB model loading and 7.8 GiB available KV memory. The engine
reports 990,000 cache tokens and accepts the configured context; that aggregate
accounting is not evidence of a successful 990,000-token request. Long-prompt
performance and usable retained capacity require their separate benchmarks.
Graph capture's negative memory delta is not treated as a memory saving.

Raw responses, launch configuration, metrics, checker source and startup log
excerpts are retained. The checker scripts contain local paths requiring
adjustment elsewhere. Earlier output-quality failures remain documented.
