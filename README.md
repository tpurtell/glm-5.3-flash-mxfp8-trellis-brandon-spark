# GLM-5.3 Flash TrellisMX on DGX Sparks

A serving recipe for Brandon Music's
[GLM-5.3-Flash-TrellisMX-MXFP8](https://huggingface.co/brandonmusic/GLM-5.3-Flash-TrellisMX-MXFP8)
on two and four NVIDIA DGX Sparks. **Port and qualification in progress; no
Spark performance results or recommended TP/EP settings have been established.**

The checkpoint contains compressed K4/K5 routed experts that reconstruct FP8
operands. It also requires the pinned NVFP4 carrier model. Both identities are
recorded in [sources.lock.json](sources.lock.json).

Download on the head Spark, then distribute over RDMA:

```bash
./scripts/download.sh
./scripts/sync-models.sh tj@10.55.0.1 tj@10.55.0.2 tj@10.55.0.4
```

`MODEL_ROOT` defaults to `$HOME/models/glm53-trellismx`. The example starts on
emu and transfers to ostrich, dodo, and kiwi. `rdmasync` is required on each
host; transfers fail if RDMA cannot be negotiated.

See the [qualification plan](docs/qualification.md) for the measurement matrix
and [provenance](docs/provenance.md) for source attribution. Results will be
committed and pushed separately as each complete block finishes.
