#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$root"
runtime_revision=$(python3 -c 'import json; print(json.load(open("sources.lock.json"))["sparkinfer"]["revision"])')
if [[ ! -d .work/sparkinfer/.git ]]; then
    ./scripts/fetch-runtime.sh
fi
actual=$(git -C .work/sparkinfer rev-parse HEAD)
[[ "$actual" == "$runtime_revision" ]] || {
    echo 'Runtime checkout differs from lock; run scripts/fetch-runtime.sh' >&2; exit 1;
}
[[ -z $(git -C .work/sparkinfer status --porcelain) ]] || {
    echo 'Runtime checkout has uncommitted changes' >&2; exit 1;
}
python3 scripts/prepare-chat-template.py
exec docker build --build-arg "RECIPE_REVISION=$(git rev-parse HEAD)" \
    --build-arg "RUNTIME_REVISION=$runtime_revision" \
    -t "${IMAGE:-glm53-trellismx-spark:dev}" .
