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
emu and transfers to ostrich, dodo, and kiwi. `rdmasync` is required on each
host; transfers fail if RDMA cannot be negotiated. Repeat the verification on
each destination before qualification. Downloads use plain HTTP with Xet disabled (`HF_HUB_DISABLE_XET=1`) and
eight file workers (`HF_DOWNLOAD_WORKERS`).

The recipe pins Z.ai’s current official chat template, with an explicit
adaptation that honors an explicit `enable_thinking: false` for comparison
requests. Ordinary requests keep thinking enabled. See the [template audit](docs/chat-template.md).

The [launch options](docs/launch.md) cover both node counts. The separate
[Mia comparison protocol](docs/mia-comparison-protocol.md) records matching
prompts and timing definitions.

See the [qualification plan](docs/qualification.md) for the measurement matrix
and [provenance](docs/provenance.md) for source attribution. Results will be
committed and pushed separately as each complete block finishes.
