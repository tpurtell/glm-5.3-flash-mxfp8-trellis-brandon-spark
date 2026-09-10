#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# Use resumable HTTP downloads; do not load the Xet transfer backend.
export HF_HUB_DISABLE_XET=1
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
