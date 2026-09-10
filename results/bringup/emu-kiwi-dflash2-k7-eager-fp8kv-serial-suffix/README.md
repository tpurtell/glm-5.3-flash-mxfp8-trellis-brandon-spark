# Eager FP8 KV-cache serial suffix control

Fourteen of fifteen sequential responses pass the normalized output-prefix
check. All counting `(stream 1/2)` and code `(stream 2/4)` requests pass; code
`(stream 1/4)` repeat 2 fails. No transport errors occurred. Requests use
thinking off; ordinary serving retains thinking on. Raw responses are retained.

The earlier NVFP4 serial control also had one failure out of fifteen, on a
different code prompt. The concurrent control had seven failures out of seventy
with each format, also in different responses. These small samples do not
establish equal failure rates, and do not demonstrate that changing KV format
fixes output errors. Failures occur with FP8 and NVFP4, eager and graph execution,
and with a single active request. Historical target-only counting failures also
exist. The controls do not isolate a root cause or prove all failures share one.

Same eager DFlash2 K7 emu/kiwi launch as the FP8 concurrency control. That block
finished before these serial requests started. The cache change also alters
record layout and hybrid block size. Continue MTP/performance qualification with
the observed quality limits reported; do not represent timing success as a full
quality pass.
