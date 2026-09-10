# Pinned ARM64 base; this TrellisMX port still requires hardware qualification.
# This existing ARM64 recipe includes Mia-derived GLM geometry and DFlash2 patches.
ARG BASE=ghcr.io/tpurtell/single-spark-glm-5.3-flash@sha256:1e91406e6c9520bf0e102bd0ead3b43426740671f308ca81c948ad6010136009
FROM ${BASE}
# Keep the base image's application-facing B12X API. The quant runtime and its
# dependencies coexist under a private package and use a separate compile cache.
COPY .work/sparkinfer/b12x /opt/trellismx/source/b12x
COPY .work/sparkinfer/scripts/export_trellismx_runtime.py /opt/trellismx/export_runtime.py
RUN python3 /opt/trellismx/export_runtime.py /opt/trellismx/source/b12x /opt/trellismx/runtime \
    && python3 -c 'import site; from pathlib import Path; (Path(site.getsitepackages()[0])/"trellismx-runtime.pth").write_text("/opt/trellismx/runtime\n")' \
    && rm -rf /opt/trellismx/source
COPY .work/sparkinfer/third_party/trellismx /opt/trellismx/licenses/runtime
COPY overlay /opt/trellismx/overlay
COPY licenses /opt/trellismx/licenses
COPY data /opt/trellismx/data
COPY container/entrypoint.sh /opt/trellismx/entrypoint.sh
RUN python3 /opt/trellismx/overlay/install.py \
    && python3 -c 'from trellismx_b12x.moe._shared.trellismx.p8_native_kernel import P8NativeTPMoE; from b12x.attention.sparse_mla import run_decode, run_extend; from vllm.model_executor.layers.quantization.trellismx import TrellisMXMoEMethod'
ENTRYPOINT ["/bin/bash", "/opt/trellismx/entrypoint.sh"]
ARG RECIPE_REVISION=unknown
ARG RUNTIME_REVISION=unknown
LABEL org.opencontainers.image.source="https://github.com/tpurtell/glm-5.3-flash-mxfp8-trellis-brandon-spark" \
      org.opencontainers.image.title="GLM-5.3 Flash TrellisMX on DGX Sparks" \
      org.opencontainers.image.description="Experimental ARM64 TrellisMX port; qualification pending" \
      org.opencontainers.image.revision="${RECIPE_REVISION}" \
      org.opencontainers.image.licenses="LicenseRef-SHAPLEYMCG AND Apache-2.0 AND MIT" \
      io.tpurtell.trellismx.runtime-revision="${RUNTIME_REVISION}"
