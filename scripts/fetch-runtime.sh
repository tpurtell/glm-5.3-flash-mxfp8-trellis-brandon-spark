#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
destination=${1:-$root/.work/sparkinfer}
mapfile -t identity < <(python3 - "$root/sources.lock.json" <<'PY'
import json, sys
source = json.load(open(sys.argv[1]))['sparkinfer']
print(source['repository'])
print(source['revision'])
PY
)
if [[ ! -d "$destination/.git" ]]; then
    git init "$destination"
    git -C "$destination" remote add origin "${identity[0]}"
elif [[ -n $(git -C "$destination" status --porcelain) ]]; then
    echo "Refusing to replace modified runtime checkout: $destination" >&2
    exit 1
fi
git -C "$destination" fetch --depth 1 origin "${identity[1]}"
git -C "$destination" checkout --detach "${identity[1]}"
