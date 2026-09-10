# Current user-requested experiment

First run cold-prefill measurements with speculation
disabled (no DFlash2, no MTP), using Mia-matched batch size 7168, followed by
README table results labeled "(no spec)". Do not run a batch-1024 control.
GPU memory utilization must not exceed 0.80. Test only prompt sizes that fit;
use null for sizes that cannot fit. Never raise the memory limit to complete rows.
After prefill, the user authorizes DFlash2 decode tests with the same EMA adaptive
drafting algorithm and settings as Mia, to compare the expert format's Spark
performance. Verify the actual adaptive policy and report matching settings and
measured deltas; fixed-K DFlash2 is not an acceptable substitute.
After each of these two corrected experiments, separately update the README,
commit, and push its results before proceeding to publication of the next block.
Only emu and kiwi remain authorized hosts. Earlier tool-evaluation and concurrency
automation was canceled; do not restart that queue or the broader qualification
campaign as part of this experiment.

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
