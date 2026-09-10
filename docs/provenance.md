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

`overlay/trellismx_manifest.py` comes from the pinned release's
`runtime/vllm/vllm/utils/trellismx.py`; only its regex import uses Python's standard
library so the checkpoint can be verified without installing vLLM. Bundled
licenses are retained in `licenses/`.

The runtime branch applies both `runtime/b12x/b12x` and the selected September 9
`runtime-reference-20260909/b12x/b12x` overlay, in that order. The reference
source manifest is retained in that branch. Use `scripts/fetch-runtime.sh` to
check out the exact revision named by this recipe.

The container starts from the pinned released ARM64
`tpurtell/single-spark-glm-5.3-flash` image, which already integrates Mia-derived
GLM geometry and DFlash2 support. `overlay/trellismx.py` is adapted from Brandon's
base vLLM adapter: it admits SM121 and omits the unavailable Jovian warmup-provider
interface. `overlay/install.py` inserts narrow ModelOpt hooks rather than
replacing ARM64 vLLM with the x86 reference's Python tree. These changes are
experimental until real loading, output and graph tests pass.

The container preserves the pinned base image's public `b12x` package for
attention, dense layers and its vLLM integration. TrellisMX uses the runtime
branch exported as `trellismx_b12x`, including a separate Torch operator
namespace and `TRELLISMX_COMPILE_CACHE_DIR`. The export changes package names
and cache location, preserving kernel code and source attribution. Its manifest
binds original and generated files by SHA256. Replacing the entire public B12X
package failed the base attention API; that failure is retained in
`results/bringup/attention-api-mismatch/`.
