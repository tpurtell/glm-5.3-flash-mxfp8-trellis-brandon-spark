# Active scope and host availability

The latest user instruction restricts this recipe and its full qualification to
**two DGX Sparks only: emu and kiwi**. Four-Spark work is canceled.
This supersedes the previous kiwi/dodo allocation and prohibition on emu GPU work.

Do not access or use dodo or ostrich for serving, GPU tests, transfers, or
benchmarks. They are reserved for the user's DeepSeek Flash development.
The previous kiwi/dodo launch and its queued benchmark automation were canceled;
never restart those jobs. Use only emu and kiwi for subsequent work.

Run DFlash2, MTP, TP2/EP2 comparison and the full requested measurements
sequentially on emu/kiwi. Keep thinking-on serving defaults, the thinking-off
Mia comparison, and separate weighted-seven/orchid results. Commit and push
completed measurement blocks. Runtime modifications stay on the dedicated
runtime branch; no four-host deployment or qualification is required.

Historical receipts naming other hosts remain provenance only. They do not
authorize access to those hosts or qualify the current pair. Preserve the original
checkpoint's TP4 shard/repacking logic: four input partitions do not mean four hosts.
