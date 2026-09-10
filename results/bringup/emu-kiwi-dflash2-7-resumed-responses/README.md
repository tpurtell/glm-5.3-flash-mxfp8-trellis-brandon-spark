# Emu/kiwi TP2 DFlash2 K7 graph-serving smoke checks

All three response checks pass: default thinking computes 17 × 23 = 391 with
reasoning; explicit thinking-off returns exactly 391 with null reasoning; default
thinking emits a parsed get_weather call with {"city":"Taipei"}. No external tool
was executed. Raw requests, responses, usage, launch receipt and metrics are saved.

The target and draft use TP2 on emu and kiwi, with CUDA graphs, context 8192,
1024 batched tokens, four sequence slots and memory utilization 0.85. The actual
hybrid cache block is 6400 tokens. DFlash2 uses seven draft tokens. This proves
basic graph serving and speculation on this pair, not full quality equivalence.

The observed metrics delta is 175 proposed / 111 accepted draft tokens (63.43%).
Metrics export can lag request completion; this snapshot establishes active
speculation, not a precisely synchronized per-case acceptance measurement.
Arithmetic with default thinking emitted 93 completion tokens; explicit off 3;
the tool response 40. Request elapsed times include prefill and are not decode
benchmark scores. Weighted decode screening is recorded separately.

The two Python files preserve the checker source used. The wrapper receives the
result name, launch directory name and base URL; its absolute workspace paths
and source adaptation describe this local run and require adjustment elsewhere.
