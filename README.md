# GLM-5.3 Flash TrellisMX on DGX Sparks

A serving recipe for Brandon Music's
[GLM-5.3-Flash-TrellisMX-MXFP8](https://huggingface.co/brandonmusic/GLM-5.3-Flash-TrellisMX-MXFP8)
on two NVIDIA DGX Sparks: **emu and kiwi**. Earlier bring-up
produced preliminary target-only screens; fresh emu/kiwi qualification and
speculation tuning are in progress.

## Comparison with Mia's two-Spark recipe (thinking off)

Mia's published numbers below are the reference. TrellisMX decode uses five-wave
medians from the earlier emu/kiwi fixed-K7 candidate. The corrected no-spec
prefill launch uses batch 7168 and memory utilization 0.80; it could not start. All rates are tokens/s. This comparison explicitly
disables thinking to match Mia; the serving recipe defaults to **thinking on**.
The weighted seven-category and orchid results remain separate.

| Measurement | Mia 2× Spark | TrellisMX 2× | Δ vs Mia |
|---|---:|---:|---:|
| Structured decode, C1 | 62.9 | 53.52 | -14.9% |
| Code decode, C1 | 62.9 | 52.59 | -16.4% |
| Structured decode, C4 aggregate † | 146.5 | 89.81 | -38.7% |
| Code decode, C4 aggregate † | 146.5 | 83.41 | -43.1% |
| Prose decode, C1 (Mia: adaptive + FP8 dense) | 32.1 | 23.03 | -28.2% |
| Cold prefill, ~8K (no spec) | 1,492.1 | null | — |
| Cold prefill, ~16K (no spec) | 1,553.7 | null | — |
| Cold prefill, ~32K (no spec) | 1,428.2 | null | — |
| Cold prefill, ~64K (no spec) | 1,587.0 | null | — |
| Cold prefill, ~128K (no spec) | 1,561.7 | null | — |
| Cold prefill, ~256K (no spec) | 1,516.8 | null | — |

**No-spec prefill:** `null` means no measurement: the batch-7168, memory-0.80
launch failed before readiness, reporting **−4.23 GiB available KV memory**
even with a 9000-token context. Shorter input cannot resolve this allocation
failure. [Launch evidence](results/2x/none-b7168-m080-prefill/README.md).

† **Output quality is not qualified:** nine counting/code responses
departed from the requested pattern; one code response stopped at 393 tokens.
Follow-up eager tests also reproduce failures, including one serial code request
([controls](results/bringup/emu-kiwi-dflash2-k7-eager-serial-suffix/README.md)).
All timings are retained. [Full results and output audit](results/2x/dflash2-k7-mia-decode/README.md).
TrellisMX prose uses fixed K7; Mia's prose configuration is separately tuned.

Source: [Mia's pinned README](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks/blob/94bddea5db64137db41e4ef4c6c120e6e69e32d7/README.md).
Decode uses sparkDash counting/code prompts, temperature 0, thinking off, a
400-token cap and DFlash2 K7; prose is a separately tuned configuration.
Prefill uses the September 7 E3 results, client prompt tokens / TTFT.
Decode is measured separately from the weighted seven-category suite and orchid
speed probe. Historical MTP/batch-1024 results are in the [cold-prefill receipts and audit](results/2x/mtp2-mia-prefill/README.md)
verify zero cached tokens in all 25 supported samples. All five 256K rejections
are retained; they establish this launch's configured limit, not the hardware's
maximum capacity. Prefill settings differ: TrellisMX uses MTP K2, batch 1024 and
165K context; Mia uses DFlash2 K7, batch 7168 and 900K context. These are measured
recipe comparisons, not an isolated quantization comparison.

The separate [five-replay MTP K2 weighted block](results/2x/mtp2-weighted/README.md)
measured **24.05 tokens/s**, with **40/40 content checks passed**. Orchid median
speed was **28.49 tokens/s**, but **0/5 probes followed the exact-repeat instruction**.
These results do not replace the DFlash2 Mia-style measurements above.

The checkpoint contains compressed K4/K5 routed experts that reconstruct FP8
operands. It also requires the pinned NVFP4 carrier model. Both identities are
recorded in [sources.lock.json](sources.lock.json).

Download on the head Spark, then distribute over RDMA:

```bash
./scripts/download.sh
python3 scripts/verify-target.py "$(python3 scripts/model_paths.py target)"
python3 scripts/verify-carrier.py "$(python3 scripts/model_paths.py carrier)"
./scripts/sync-models.sh kiwi
```

Downloads default to the real Hugging Face cache: `$HF_HUB_CACHE`, or
`$HF_HOME/hub`, or `${XDG_CACHE_HOME:-$HOME/.cache}/huggingface/hub`.
The recipe checks these and Mia's `~/.cache/huggingface/hub` for the exact pinned
snapshots, then an existing `~/models/glm53-trellismx` layout. Missing models go
into the HF cache. Set `MODEL_ROOT` (and `model_root` in the cluster config) only
for an explicit local layout. The default cluster config resolves each host's
cache independently; Docker mounts include the blobs referenced by snapshots.
The example starts on
emu and transfers to kiwi. The helper prefers `rdmasync` on
both endpoints and falls back to rsync over SSH if RDMA is unavailable or fails.
It preserves the same HF cache layout with either transport. Repeat the verification on
each destination before qualification. Downloads use Hugging Face's default backend and concurrency. Optional
per-machine environment settings such as `HF_HUB_DISABLE_XET=1` or
`HF_DOWNLOAD_WORKERS` are honored without imposing them on the recipe.

Transfer a built Docker image directly over RDMA, bootstrapping through SSH:

```bash
./scripts/sync-image.sh glm53-trellismx-spark:dev kiwi
# Streams: docker save IMAGE | rdmapipe HOST -- docker load
```

The helper prefers `rdmapipe`, falls back to `docker save` streamed over SSH,
and checks each destination for the source image ID. Both transfer helpers
discover tools in PATH, `~/.local/bin`, and `/home/linuxbrew/.linuxbrew/bin`
on each endpoint. `RDMAPIPE_REMOTE_PATH` and `REMOTE_RDMASYNC` can override
remote discovery. See the [RDMA tools installation guide below](#rdma-tools-for-dgx-spark-and-roce-pcs).

The recipe pins Z.ai’s current official chat template, with an explicit
adaptation that honors an explicit `enable_thinking: false` for comparison
requests. Ordinary requests keep thinking enabled. See the [template audit](docs/chat-template.md).

The [launch options](docs/launch.md) cover the two-node configuration. The separate
[Mia comparison protocol](docs/mia-comparison-protocol.md) records matching
prompts and timing definitions.

See the [qualification plan](docs/qualification.md) for the measurement matrix
and [provenance](docs/provenance.md) for source attribution. Results will be
committed and pushed separately as each complete block finishes.

## RDMA tools for DGX Spark and RoCE PCs

Move model weights, checkpoints, datasets, and container images between your local AI machines with [Local AI Tap](https://github.com/tpurtell/local-ai-tap):

- **`rdmasync`** — rsync-style file synchronization with RDMA bulk transfers.
- **`rdmapipe`** — stream command output over RDMA into a remote command, using SSH for authentication and orchestration.

Native **ARM64 and AMD64 binary bottles** are available for Linux, including DGX Spark. Homebrew installs the dependencies automatically.

**Install on both endpoints**, with [Homebrew](https://brew.sh/) already installed:

```bash
brew tap tpurtell/local-ai https://github.com/tpurtell/local-ai-tap.git

if brew commands | grep -qx trust; then
  brew trust --tap tpurtell/local-ai
fi

brew install tpurtell/local-ai/rdmapipe tpurtell/local-ai/rdmasync
```

Replace `spark` below with your machine’s SSH hostname or alias.

**Copy model files over RDMA:**

```bash
rdmasync -a --rdma=required \
  --rsync-path=/home/linuxbrew/.linuxbrew/bin/rdmasync \
  ./models/ spark:~/models/
```

**Stream an ARM64 container image directly into a Spark:**

```bash
docker image save --platform linux/arm64 my-ai-image:latest |
  rdmapipe \
    --remote-path=/home/linuxbrew/.linuxbrew/bin/rdmapipe \
    spark -- docker image load
```

The Docker example requires an ARM64 image locally and Docker access on both machines.

Use these tools on a trusted, configured RDMA/RoCE fabric with working Linux drivers and SSH access. Bulk RDMA traffic is not encrypted.

[Installation guide and documentation →](https://github.com/tpurtell/local-ai-tap#readme)
