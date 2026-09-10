# Eager DFlash2 K7 FP8 KV-cache control

Thirty waves / 70 responses complete without transport errors; seven responses
fail the normalized counting/code prefix check. The NVFP4 eager control also
had seven failures out of 70, in different responses. These small samples do not
establish equivalent failure rates, a precision-related improvement or a root
cause. Both formats exhibit output failures. All timing samples are retained.

| Workload | Median aggregate tokens/s, five waves | Prefix checks passed |
|---|---:|---:|
| structured C1 | 51.96 | 5/5 |
| structured C2 | 64.18 | 8/10 |
| structured C4 | 100.74 | 16/20 |
| code C1 | 50.96 | 5/5 |
| code C2 | 64.08 | 9/10 |
| code C4 | 91.33 | 20/20 |

Only the requested cache format and its format-specific environment flags changed
from the NVFP4 eager launch. The image IDs and model paths match on emu and kiwi;
target/draft TP2, eager DFlash2 K7, context 8192, batch 1024, four sequence slots,
and memory utilization 0.85 remain fixed. Requests disable thinking explicitly;
serving defaults remain on. FP8 uses 656-byte cache records and an actual hybrid
block of 3584 tokens, compared with NVFP4's 368-byte records / 6400-token blocks.
The comparison thus changes layout/block alignment as well as precision.

JIT warnings were observed around initial warmup; these timings are diagnostic,
not final qualified performance figures. Raw SSE, source checker, launch receipt
and output checks are retained. The separate serial-suffix control follows this
block without competing inference or transfers. MTP and remaining performance
qualification continue with these quality limitations recorded.
