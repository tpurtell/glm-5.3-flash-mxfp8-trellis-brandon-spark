#!/usr/bin/env bash
set -euo pipefail

if (( $# < 2 )); then
    echo "Usage: $0 IMAGE HOST [HOST ...]" >&2
    exit 2
fi
image=$1
shift
command -v rdmapipe >/dev/null
expected=$(docker image inspect --format '{{.Id}}' "$image")
for host in "$@"; do
    # Export the named image to preserve its tag on the destination.
    current=$(docker image inspect --format '{{.Id}}' "$image")
    [[ "$current" == "$expected" ]] || { echo "Source image changed" >&2; exit 1; }
    docker save "$image" | rdmapipe \
        --remote-path="${RDMAPIPE_REMOTE_PATH:-rdmapipe}" "$host" -- docker load
    # SSH invokes a remote shell: quote the image argument for that shell.
    printf -v inspect_command 'docker image inspect --format %q -- %q' '{{.Id}}' "$image"
    actual=$(ssh "$host" "$inspect_command")
    [[ "$actual" == "$expected" ]] || { echo "Image ID mismatch on $host" >&2; exit 1; }
    echo "$host: verified $expected"
done
