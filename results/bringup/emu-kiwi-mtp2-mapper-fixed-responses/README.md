# Emu/kiwi MTP K2 graph-serving smoke checks

The rebuilt image with the scoped MTP quantization mapper passes full target
and draft loading on both hosts, CUDA graph capture, and all three response
contracts. Default thinking computes 17 × 23 = 391 with reasoning; explicit
thinking-off returns exactly 391 with null reasoning; default thinking emits a
parsed get_weather call with {"city":"Taipei"}. No external tool was executed.
Raw requests, responses, usage, launch receipt and metrics are retained.

The observed snapshot delta is 98 proposed / 84 accepted draft tokens (85.71%).
Metrics export can lag request completion; this proves active speculation, not
precisely synchronized per-case acceptance. Weighted decode is a separate block.
Default arithmetic emitted 90 completion tokens, explicit off 3, tool response
40. Elapsed request times include prefill and are not decode benchmark scores.

Target TP2 and carrier MXFP8 MTP use emu/kiwi, two draft tokens, graphs, NVFP4
MLA KV cache, context 8192, batch 1024, four sequence slots and memory utilization
0.85. Actual hybrid block size is 6144 tokens. The draft uses the base Marlin
MXFP8 backend; target routed experts use the private TrellisMX runtime. Graph
capture completed; its negative reported memory delta is not treated as a memory
saving. Model loading measured 99.5 GiB on kiwi.

This closes the observed missing-scale startup failure and proves basic MTP
serving. It is not full quality qualification. Earlier counting/code output
failures with other candidates remain documented. Checker source is preserved;
absolute paths and source adaptation in these local-run scripts require adjustment
when reproducing elsewhere.
