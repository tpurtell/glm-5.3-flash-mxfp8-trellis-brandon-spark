# TP2 target-only eager decode screen

Single screening wave per cell, 400-token cap, temperature zero, thinking off.
This is not the five-wave final Mia comparison. Graph serving and speculation
have not yet been compared. Both Sparks use the launch receipt in this directory.

| Workload | C1 tok/s | C2 aggregate tok/s | C4 aggregate tok/s |
|---|---:|---:|---:|
| structured | 10.24 | 23.53 | 41.38 |
| code | 10.14 | 23.38 | 42.41 |
| prose | 9.94 | 23.69 | 41.18 |

All 21 measured responses passed transport, usage, decode-window and thinking-off
checks. Manual review of the C1 outputs found coherent counting, clamp functions,
and hash-map prose. Responses hit the requested token cap; this is not a formal
quality score. Raw SSE events and metrics remain alongside the receipt.
