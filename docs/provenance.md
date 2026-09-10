# Source provenance

- Brandon M. Music supplies the TrellisMX checkpoint, native P8 expert kernels,
  and runtime integration in the pinned Hugging Face release. Its source is
  available under the bundled SHAPLEYMCG license; it is not represented as MIT
  or Apache licensed. Preserve the source release's licenses when packaging.
- MiaAI-Lab's GLM-5.3-Flash-EXL3-2x-DGX-Sparks recipe supplies the starting point
  for ARM64 vLLM, multi-host launch, GLM geometry patches, and DFlash2 integration.
  Its EXL3 weights and published performance are not qualification of this port.
- tpurtell/glmrt-5.3-1rtx-4spark supplies the measurement design. Its results use
  different hardware and weights and are not copied into this recipe's results.
- Runtime modifications belong on a dedicated branch of
  tpurtell/sparkinfer-glmrt, never on its main branch.

Exact starting revisions are in `sources.lock.json`.
