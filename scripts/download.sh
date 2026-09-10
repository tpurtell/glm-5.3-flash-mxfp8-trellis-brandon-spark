#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
model_root=${MODEL_ROOT:-$HOME/models/glm53-trellismx}
for component in target carrier draft; do
    mapfile -t identity < <(python3 - "$root/sources.lock.json" "$component" <<'PY'
import json, sys
item = json.load(open(sys.argv[1]))[sys.argv[2]]
print(item['repo_id'])
print(item['revision'])
PY
    )
    hf download "${identity[0]}" --revision "${identity[1]}" --local-dir "$model_root/$component"
done
