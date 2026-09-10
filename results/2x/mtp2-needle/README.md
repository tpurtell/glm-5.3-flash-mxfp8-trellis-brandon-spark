# MTP K2 needle retrieval: all 15 cells attempted

**Nine of nine supported cells pass exact-key retrieval**, with server prompt
counts matching the locally rendered/tokenized requests and completion within
600 seconds. All six cells at 256K and 384K receive HTTP 400 because the server
is configured for 165000 tokens. The original receipt therefore remains
`failed`, with exit code 1. These are configured-limit rejections, not evidence
of failed retrieval at those lengths or a hardware capacity ceiling.

| Nominal context | 10% depth | 50% depth | 90% depth |
|---|---:|---:|---:|
| 8K | Pass, 7.79 s | Pass, 7.83 s | Pass, 7.78 s |
| 32K | Pass, 27.28 s | Pass, 27.48 s | Pass, 27.52 s |
| 128K | Pass, 113.40 s | Pass, 106.53 s | Pass, 106.59 s |
| 256K | HTTP 400 | HTTP 400 | HTTP 400 |
| 384K | HTTP 400 | HTTP 400 | HTTP 400 |

Times are whole-request elapsed times, including prefill and key generation.
Each cell uses a unique exact key and the pinned needle construction protocol,
temperature zero, thinking off, and a 32-token generation cap. Successful raw
responses contain the exact key without reasoning. One key at each depth is a
narrow retrieval test, not broad long-context quality qualification.

`audit.json` records the independent raw-response check for every cell: exact
key against the request contract, server/local token agreement, elapsed limit,
and the HTTP 400 configured-limit diagnostics. Raw requests, responses, SSE,
usage, metrics, tokenizer/template hashes and launch provenance are retained.

Configuration: emu/kiwi TP2 graphs, MTP K2, NVFP4 MLA cache, context 165000,
batch 1024, four sequence slots, memory utilization 0.895, hybrid block 6144,
image dcc6559, runtime 3ac1597. No competing inference or transfer workload was
launched during this block. The thinking-on tool evaluation started afterward.
