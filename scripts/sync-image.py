#!/usr/bin/env python3
"""Stream Docker images over RDMA, falling back to SSH, and verify image IDs."""
import os
import shlex
import subprocess
import sys
from transfer_tools import local_tool, remote_tool


def stream_image(image, receiver):
    with subprocess.Popen(['docker', 'image', 'save', image], stdout=subprocess.PIPE) as sender:
        try:
            result = subprocess.run(receiver, stdin=sender.stdout)
        finally:
            sender.stdout.close()
        sent = sender.wait()
    return result.returncode == 0 and sent == 0


def main():
    if len(sys.argv) < 3:
        raise SystemExit('Usage: scripts/sync-image.sh IMAGE HOST [HOST ...]')
    image, *hosts = sys.argv[1:]
    expected = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', image], text=True).strip()
    local = local_tool('rdmapipe')
    for host in hosts:
        remote = remote_tool(host, 'rdmapipe', os.environ.get('RDMAPIPE_REMOTE_PATH')) if local else None
        transferred = False
        if local and remote:
            print(f'{host}: streaming image over RDMA', flush=True)
            transferred = stream_image(image, [local, '--remote-path='+remote, host, '--', 'docker', 'image', 'load'])
        if not transferred:
            print(f'{host}: RDMA unavailable or failed; streaming image over SSH', flush=True)
            if not stream_image(image, ['ssh', host, 'docker image load']):
                raise RuntimeError(f'{host}: Docker image transfer failed')
        command = shlex.join(['docker', 'image', 'inspect', '--format', '{{.Id}}', image])
        actual = subprocess.check_output(['ssh', host, command], text=True).strip()
        if actual != expected:
            raise RuntimeError(f'{host}: image ID mismatch (source tag may have changed)')
        print(f'{host}: verified {expected}', flush=True)


if __name__ == '__main__':
    main()
