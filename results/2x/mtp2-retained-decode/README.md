# MTP K2 retained decode: 30 cells

All five bases × three workloads × two responses were attempted. **24 responses
have valid streamed timing and usage**, all matching the measured one-block
MTP cache-drop policy. Six requests at the 256K base and that base's prime
received HTTP 400 context-limit rejections. The limit is configured at 165000;
it is not a measured hardware ceiling.

Median post-first-token decode tokens/s, two responses per cell:

| Base | Python | Creative writing | Math |
|---|---:|---:|---:|
| 0 | 29.10 | 18.77 | 25.24 |
| 32K | 25.24 | 19.39 | 23.81 |
| 64K | 26.61 | 20.13 | 24.62 |
| 128K | 26.48 | 19.59 | 25.12 |
| 256K | Rejected | Rejected | Rejected |

**These are capped timing probes, not completed-task quality scores.** All 24
responses hit the 192-token cap. All eight supported Python responses fail the
complete-code-block contract; zero-base examples stop inside their assertions.
The inspected zero-base math derivation and creative scene are also unfinished.
No semantic pass is inferred for writing or math. All output text and finish
reasons are retained, and no bad output was dropped to improve timing.

The original receipt remains **failed**: six zero-base timing/cache cells pass,
18 retained cells fail its full aligned-base cache expectation, and six requests
fail at the configured limit. Actual cached tokens are 24576, 55296 and 122880
for 32K, 64K and 128K bases respectively. These match the installed EAGLE/MTP
recomputation policy documented with [source evidence in the prefill block](../mtp2-retained-prefill/README.md).
The separate audit does not rewrite the original strict contract.

`audit.py` verifies all 30 cells, successful priming for measured requests,
prompt length, actual cache reuse, absence of reasoning, and post-first-token
rate calculations. `audit.json` retains finish reasons, original output checks,
cache accounting and all HTTP diagnostics. Decode rate excludes TTFT; the
recomputed base still costs prefill latency, retained separately in the raw
records and audit.

Configuration: emu/kiwi TP2 graphs, MTP K2, NVFP4 MLA cache, context 165000,
batch 1024, four sequence slots, memory utilization 0.895, hybrid block 6144,
image dcc6559, runtime 3ac1597. Requests use the pinned thinking-off template
and source corpus. Ordinary serving defaults to thinking on. No competing
inference or transfer workload was launched during this block.
