# Startup timing protocol

`scripts/bench-startup.py` records one compiler-cache-cold start and one warm
restart for the selected topology and launch options. Report these as table
rows; no startup graph is required.

Cold means a new, empty, uniquely named persistent compiler-cache directory on
every rank. Warm means a restart after cold readiness and a short inference
check, preserving that same directory. The warm run requires evidence that
B12X cache files actually persisted on each rank. The launcher sets the runtime's
`B12X_COMPILE_CACHE_DIR`, plus the vLLM and Triton cache directories, under the
mounted path. It does not clear global caches or alter the OS page cache.
Consequently this is compiler-cache-cold startup, not storage-cold startup.

The primary time starts immediately before launching the first worker container
and ends when the head's `/health` succeeds. It includes container launches,
weight loading, runtime compilation, warmup and graph capture. Checkpoint/image
preflight is excluded. Total client-command time including preflight is retained
as a separate field. A short inference request confirms the ready server can
produce content; its time is not added to the readiness measurement.

The runner refuses to replace an existing live serving run. On success it saves
launch receipts, before/after cache inventories, inference output and every
rank's logs, then stops only the exact container IDs it created. Failed launches
remain available for inspection. Model files and cache directories are retained.

```bash
python3 scripts/bench-startup.py --nodes 2 --out results/2x/startup -- \
  --speculation dflash2 --draft-tokens 3 --max-model-len 294912
```

Use the final measured serving options in place of the example. `--plan-only`
validates and records commands without starting containers or touching remote
caches. Plans for both two and four nodes passed; actual startup timings remain
pending full-model qualification.
