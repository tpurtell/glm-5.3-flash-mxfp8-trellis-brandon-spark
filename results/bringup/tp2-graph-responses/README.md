# TP2 full-model CUDA-graph bring-up

The emu + kiwi target-only launch completed four piecewise and three full CUDA
graph captures. All three live response checks passed: default thinking,
explicit thinking off, and automatic tool parsing. Answer text, reasoning,
finish reasons, token usage, and tool function/arguments match the previous
TP2 eager responses exactly on these prompts (response and tool IDs excluded).

This verifies basic full-model graph serving on three requests, not the full
quality or performance matrix. Raw responses, both worker logs, client and
launch receipt are preserved. Graph memory accounting in the engine log reports
a negative delta; it is not interpreted as a memory saving or a startup score.
