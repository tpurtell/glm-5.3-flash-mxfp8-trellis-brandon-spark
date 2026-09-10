# Two- and four-Spark launch options (bring-up)

These commands are implemented but **not yet hardware-qualified**. The current
port supports TP2/TP4 with EP off; optimal settings remain to be measured.
Defaults use a short context and target-only decoding for initial correctness.

Edit `cluster.example.json` for host names, CX7 addresses, local model paths and
image. Rank zero is the first host; the two-node launch uses the first two entries.
The supplied inventory uses emu/kiwi for two nodes and adds dodo/ostrich for four.
Each node needs the identical image and local model files. A null `model_root`
resolves pinned snapshots in that host's HF cache, including Mia's default cache
location. Set it only to override with a target/carrier/draft directory layout.
Thinking is enabled by default; only comparison requests explicitly disable it.

```bash
./scripts/fetch-runtime.sh
./build.sh
./scripts/download.sh
python3 scripts/verify-target.py "$(python3 scripts/model_paths.py target)"
./scripts/sync-models.sh ostrich dodo kiwi
./scripts/sync-image.sh glm53-trellismx-spark:dev ostrich dodo kiwi

# Inspect without changing any host:
python3 scripts/cluster.py plan --nodes 2
python3 scripts/cluster.py plan --nodes 4

# Initial target-only runs (choose one at a time):
python3 scripts/cluster.py start --nodes 2
python3 scripts/cluster.py start --nodes 4

# Explicit speculation candidates, not recommendations:
python3 scripts/cluster.py start --nodes 2 --speculation dflash2 --draft-tokens 7
python3 scripts/cluster.py start --nodes 4 --speculation mtp --draft-tokens 3

python3 scripts/cluster.py status --nodes 2
python3 scripts/cluster.py stop --nodes 2
```

Start refuses an existing running container. Stop before changing candidates.
It verifies all rank image IDs and checkpoint file inventory before launching
workers then the head. It retains exited containers and a launch receipt under
`.work/launches/` for failure diagnosis. Ready time in that receipt measures this
start operation only; it is not yet a qualified cold/warm startup result.

DFlash2 requires the same pinned draft files locally on each participating host;
`scripts/download.sh` includes `incoai/GLM-5.3-Flash-DFlash2`
revision `bf582e4eacc1810f76656d1811693ff6c6737d2a` in the HF cache by default
(or `MODEL_ROOT/draft` with an explicit local layout).
The model synchronization script distributes the draft over RDMA too. The correct draft policy and TP setting
must be qualified for this target.

Additional switches: `--eager`, `--max-model-len`, `--batch-tokens`, `--max-seqs`,
`--memory-utilization`, `--kv-cache`, `--draft-tp`. `--ep` exists for explicit
qualification runs: dense TP stays at the node count while routed experts use
EP2/EP4 with contiguous placement. Single-layer K4/K5 numerical and mutable
graph checks pass; distributed serving and performance remain unqualified, so
EP is not yet a launch recommendation. DP/PCP/SP and expert load balancing are
rejected. No inference profiler is enabled.

With `--kv-cache nvfp4_ds_mla`, the launcher selects the base image's B12X
368-byte cache format using `KV_FP8_ROPE=1` and per-token dynamic scaling using
`VLLM_NVFP4_MLA_DYNAMIC_SCALE=1`. These settings keep the cache writer and
readers on the same format. The installed ARM64 stock writer rejects this
cache dtype; the B12X writer passed an isolated GPU dispatch check. Full-model
qualification is still pending. The engine may increase the requested cache
block size to accommodate hybrid state; benchmark cache reuse must be checked
against the actual reported token counts.

To relocate an existing local layout after strict target/carrier verification:

```bash
python3 scripts/adopt-hf-cache.py --model-root ~/models/glm53-trellismx --verified
```

This moves model bytes into HF blobs and pinned snapshots, retaining legacy
paths as symlinks. Stop writers to the local layout before migrating it.
