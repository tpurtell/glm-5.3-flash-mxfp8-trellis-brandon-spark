# EP2 target-only eager decode screen

Dodo + ostrich, dense TP2 / routed EP2, one wave per cell, 400-token cap,
temperature zero and thinking off. Same image and capacity limits as the TP2
screens, but a different host pair; differences cannot isolate EP alone.
No MTP or DFlash2 is enabled.

| Workload | C1 tok/s | C2 aggregate tok/s | C4 aggregate tok/s |
|---|---:|---:|---:|
| structured | 9.44 | 22.37 | 36.45 |
| code | 8.69 | 19.61 | 35.46 |
| prose | 9.14 | 21.21 | 35.62 |

All 21 responses passed transport, usage, timing-window and thinking-off checks. 21 reached the 400-token cap.
Completion token counts range from 400 to 400. Rates use actual token counts.
These are preliminary screening timings, not the five-wave final comparison or
a formal quality score. EP2 graph-mode and speculation remain unqualified.
