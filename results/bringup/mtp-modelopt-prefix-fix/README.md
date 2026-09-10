# Scoped GLM MTP quantization mapper

Runtime branch `trellismx-glm53-spark` commit
`3ac1597674bff576241b7c72929bc3a3d18d7616` adds a weights mapper to Glm5NextMTP.
It translates either multimodal carrier prefix to the text MTP namespace before
vLLM constructs draft layers. The existing manual tensor-name loader remains
unchanged. The recipe installs this patch when building the image.

The included checker ran against the actual installed vLLM
`configure_quant_config`, patched MTP class, and pinned carrier config. It
reproduced the unresolved draft algorithm before mapping, then verified MXFP8
for `model.layers.45.mlp.experts` and preservation of all 43 quantization records.
Two patcher checks also passed (scoped insertion and rejection of source drift
or duplicate installation). This is quantization-metadata validation, not
full-model startup, GPU numerical validation or performance evidence.

Validation used the previous recipe image with only the patched MTP file mounted
read-only. The full rebuilt image must still complete MTP loading and inference.
The checker expects the pinned carrier config at `/carrier-config.json`.
