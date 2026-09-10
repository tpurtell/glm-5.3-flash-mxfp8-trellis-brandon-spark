The TP2 eager launch loaded all routed expert layers on both ranks, then failed
in attention warmup: the stock ARM64 `concat_and_cache_mla` writer rejected
`nvfp4_ds_mla`. The launcher had omitted the base recipe's `KV_FP8_ROPE=1` and
`VLLM_NVFP4_MLA_DYNAMIC_SCALE=1` settings, which select the B12X writer and its
matching reader format. The cluster launcher now sets both for NVFP4 MLA only.

The included isolated GPU check reproduced the exact stock-writer exception,
then called the installed attention backend's dynamic-scale writer successfully.
Two requested records were written; unused slots remained untouched. This is a
writer-dispatch check, not a numerical attention or full-model qualification.
Image: `sha256:7bc894f9453b04b4244044133586e0a012cc9c74178a2f4b507e2c7c606f3cc1`.
Full-model validation with the corrected launch settings is pending.
