# Eager DFlash2 K7 counting/code concurrency control

Thirty waves / 70 responses complete; seven output-prefix failures, with no
transport errors. The failures include five counting C2 responses and two code
C4 responses. All C1 counting/code responses pass. The run uses emu/kiwi TP2,
DFlash2 K7, 8192 context, 1024 batch tokens, four sequences, 0.85 memory
utilization, thinking-off requests and eager execution. Launch receipt and raw
SSE are retained. Serving defaults remain thinking-on.

| Workload | Median aggregate tokens/s, five waves | Prefix checks passed |
|---|---:|---:|
| structured C1 | 51.95 | 5/5 |
| structured C2 | 60.82 | 5/10 |
| structured C4 | 154.22 | 20/20 |
| code C1 | 52.03 | 5/5 |
| code C2 | 63.11 | 10/10 |
| code C4 | 123.14 | 18/20 |

The matching graph run had nine counting/code prefix failures out of 70 responses.
These are small diagnostic samples, not statistically established failure rates.
Disabling graphs does not remove the failures. The much higher eager C4 timing
also warrants investigation; it is not a serving recommendation while output
correctness remains unresolved. Timings include all responses without excluding
bad outputs. Tests normalize whitespace and permit a correct truncated prefix.

The saved checker reproduces exact counting/code prompts and the same stream
suffixes at C2/C4. Serial requests with those exact suffixes are a separate queued
control to distinguish prompt behavior from concurrent execution. The historical
target-only audit also found failures without speculation and without graphs.
