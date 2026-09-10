#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# Xet 1.5 uses adaptive concurrency. Its high-performance preset can override
# the fixed bounds, so an explicit fixed-concurrency request disables that preset.
if [[ -n ${HF_XET_FIXED_DOWNLOAD_CONCURRENCY:-} ]]; then
    export HF_XET_HIGH_PERFORMANCE=0
    export HF_XET_CLIENT_ENABLE_ADAPTIVE_CONCURRENCY=false
else
    export HF_XET_HIGH_PERFORMANCE=${HF_XET_HIGH_PERFORMANCE:-1}
fi
for component in target carrier draft; do
    mapfile -t identity < <(python3 - "$root/sources.lock.json" "$component" <<'PY'
import json, sys
item = json.load(open(sys.argv[1]))[sys.argv[2]]
print(item['repo_id'])
print(item['revision'])
PY
    )
    location=$(python3 "$root/scripts/model_paths.py" "$component")
    args=("${identity[0]}" --max-workers "${HF_DOWNLOAD_WORKERS:-8}" --revision "${identity[1]}")
    if [[ -n ${MODEL_ROOT:-} || "$location" != */snapshots/"${identity[1]}" ]]; then
        args+=(--local-dir "$location")
    else
        # Preserve a discovered Mia cache even if HF_HOME now points elsewhere.
        args+=(--cache-dir "${location%/models--*/snapshots/*}")
    fi
    hf download "${args[@]}"
done
