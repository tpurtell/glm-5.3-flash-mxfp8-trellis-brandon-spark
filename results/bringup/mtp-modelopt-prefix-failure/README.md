# MTP ModelOpt mixed-precision prefix failure

The emu/kiwi MTP K2 graph launch failed before readiness. Kiwi's MTP draft
layer registered only unquantized expert weights, then the carrier's scale
loader requested `w2_weight_scale` and raised KeyError. No inference or weighted
decode was performed; the queued client exited after the launch error. Emu's
remaining rank was explicitly stopped after preserving logs.

The pinned carrier's `quantized_layers` map declares
`model.language_model.layers.45.mlp.experts` as MXFP8, group size 32. The MTP
module constructs layers under `model.layers.45`, but does not expose the
multimodal-to-text weights mapper to quantization setup. ModelOpt's existing
prefix aliases exchange the two multimodal forms; they do not include this
plain-text MTP prefix. The resulting lookup misses and constructs unquantized
experts, explaining the missing scale parameters.

The intended fix is a scoped weights mapper on the GLM MTP model class, applied
to quantization metadata before layer construction. It preserves the carrier's
MXFP8 MTP tensors and the existing manual weight-name loader. No performance
claim follows from this failed launch. Full MTP startup and inference must be
repeated after validating the mapper.
