#!/usr/bin/env bash
set -euo pipefail
# Run on the download host. Remote rdmasync must be installed at this path.
model_root=${MODEL_ROOT:-$HOME/models/glm53-trellismx}
remote_root=${REMOTE_MODEL_ROOT:-$model_root}
remote_rdmasync=${REMOTE_RDMASYNC:-/home/tj/.local/bin/rdmasync}
if (($# == 0)); then
    echo 'Usage: scripts/sync-models.sh user@rdma-host [user@rdma-host ...]' >&2
    exit 2
fi
for component in target carrier; do
    test -f "$model_root/$component/config.json" || {
        echo "Missing downloaded $component/config.json" >&2; exit 1;
    }
done
for host in "$@"; do
    rdmasync -a --partial --mkpath --rdma=required --rdma-rails=auto \
        --rdma-show-config --stats --rsync-path="$remote_rdmasync" \
        --exclude='.cache/' "$model_root/" "$host:$remote_root/"
done
