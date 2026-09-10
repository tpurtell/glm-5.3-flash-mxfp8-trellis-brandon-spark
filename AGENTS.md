# Active scope and host availability

The latest user instruction resumes this recipe and its full qualification on
**two DGX Sparks only: kiwi and dodo**. Four-Spark work remains canceled.
This explicitly supersedes the earlier emu/kiwi allocation and dodo prohibition.

Use only kiwi and dodo for model serving, GPU tests, transfers, and benchmarks.
Do not access ostrich. Do not start GPU/model work on emu. The local checkout may
be used for orchestration. Old emu/kiwi launch and benchmark jobs were canceled
when the pair changed; never restart their saved automation.

Run DFlash2, MTP, TP2/EP2 comparison and the full requested measurements
sequentially on kiwi/dodo. Keep thinking-on serving defaults, the thinking-off
Mia comparison, and separate weighted-seven/orchid results. Commit and push
completed measurement blocks. Runtime modifications stay on the dedicated
runtime branch; no four-host deployment or qualification is required.

Historical receipts naming other hosts remain provenance only. They cannot
prove results on the current kiwi/dodo pair. Preserve the original checkpoint's
TP4 shard/repacking logic: four input shard partitions do not mean four hosts.
