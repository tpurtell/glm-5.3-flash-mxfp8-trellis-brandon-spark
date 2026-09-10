# GLM-5.3 Flash TrellisMX on DGX Sparks

A serving recipe for Brandon Music's
[GLM-5.3-Flash-TrellisMX-MXFP8](https://huggingface.co/brandonmusic/GLM-5.3-Flash-TrellisMX-MXFP8)
on two and four NVIDIA DGX Sparks. **Port and qualification in progress; no
Spark performance results or recommended TP/EP settings have been established.**

## Comparison with Mia's two-Spark recipe (thinking off)

Mia's published numbers below are the reference; TrellisMX measurements and
percentage differences will be filled from fresh runs on this hardware.
All rates are tokens/s. **Pending cells are unmeasured.** This comparison explicitly
disables thinking to match Mia; the serving recipe defaults to **thinking on**.
The weighted seven-category and orchid results remain separate.

| Measurement | Mia 2× Spark | TrellisMX 2× | Δ vs Mia | TrellisMX 4× | Δ vs Mia |
|---|---:|---:|---:|---:|---:|
| Structured/code decode, C1 | 62.9 | Pending | — | Pending | — |
| Structured/code decode, C4 aggregate | 146.5 | Pending | — | Pending | — |
| Prose decode, C1, adaptive + FP8 dense | 32.1 | Pending | — | Pending | — |
| Cold prefill, ~8K | 1,492.1 | Pending | — | Pending | — |
| Cold prefill, ~32K | 1,428.2 | Pending | — | Pending | — |
| Cold prefill, ~128K | 1,561.7 | Pending | — | Pending | — |
| Cold prefill, ~256K | 1,516.8 | Pending | — | Pending | — |

Source: [Mia's pinned README](https://github.com/MiaAI-Lab/GLM-5.3-Flash-EXL3-2x-DGX-Sparks/blob/94bddea5db64137db41e4ef4c6c120e6e69e32d7/README.md).
Decode uses sparkDash counting/code prompts, temperature 0, thinking off, a
400-token cap and DFlash2 K7; prose is a separately tuned configuration.
Prefill uses the September 7 E3 results, client prompt tokens / TTFT.
The new recipe needs matching benchmark-style runs for this table, separately
from the weighted seven-category decode suite and orchid speed probe. The 4×
comparison will include the change in hardware count, not isolate quantization.

The checkpoint contains compressed K4/K5 routed experts that reconstruct FP8
operands. It also requires the pinned NVFP4 carrier model. Both identities are
recorded in [sources.lock.json](sources.lock.json).

Download on the head Spark, then distribute over RDMA:

```bash
./scripts/download.sh
python3 scripts/verify-target.py "$(python3 scripts/model_paths.py target)"
python3 scripts/verify-carrier.py "$(python3 scripts/model_paths.py carrier)"
./scripts/sync-models.sh ostrich dodo kiwi
```

Downloads default to the real Hugging Face cache: `$HF_HUB_CACHE`, or
`$HF_HOME/hub`, or `${XDG_CACHE_HOME:-$HOME/.cache}/huggingface/hub`.
The recipe checks these and Mia's `~/.cache/huggingface/hub` for the exact pinned
snapshots, then an existing `~/models/glm53-trellismx` layout. Missing models go
into the HF cache. Set `MODEL_ROOT` (and `model_root` in the cluster config) only
for an explicit local layout. The default cluster config resolves each host's
cache independently; Docker mounts include the blobs referenced by snapshots.
The example starts on
emu and transfers to ostrich, dodo, and kiwi. The helper prefers `rdmasync` on
both endpoints and falls back to rsync over SSH if RDMA is unavailable or fails.
It preserves the same HF cache layout with either transport. Repeat the verification on
each destination before qualification. Downloads use Hugging Face's default backend and concurrency. Optional
per-machine environment settings such as `HF_HUB_DISABLE_XET=1` or
`HF_DOWNLOAD_WORKERS` are honored without imposing them on the recipe.

Transfer a built Docker image directly over RDMA, bootstrapping through SSH:

```bash
./scripts/sync-image.sh glm53-trellismx-spark:dev ostrich dodo kiwi
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

The [launch options](docs/launch.md) cover both node counts. The separate
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
