#!/usr/bin/env python3
"""Distribute pinned snapshots and blobs, preferring RDMA with an SSH fallback."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from model_paths import COMPONENTS, ROOT, resolve
from transfer_tools import local_tool, remote_tool

if len(sys.argv) < 2:
    raise SystemExit('Usage: scripts/sync-models.sh host [host ...]')
lock = json.loads((ROOT/'sources.lock.json').read_text())
resolver = (ROOT/'scripts/model_paths.py').read_text().split("if __name__ == '__main__':")[0]
resolver = resolver.replace('ROOT = Path(__file__).resolve().parents[1]', 'ROOT = Path.cwd()')
for host in sys.argv[1:]:
    rdma = local_tool('rdmasync')
    remote_rdma = remote_tool(host, 'rdmasync', os.environ.get('REMOTE_RDMASYNC')) if rdma else None
    remote_hub = subprocess.check_output(['ssh', host, 'python3 -c '+shlex.quote(resolver+'\nprint(hub_cache())')], text=True).strip()
    for component in COMPONENTS:
        source = resolve(component, lock).resolve()
        if not source.is_dir():
            raise FileNotFoundError(source)
        remote_root = os.environ.get('REMOTE_MODEL_ROOT') or os.environ.get('MODEL_ROOT')
        if remote_root:
            destination = str(Path(remote_root)/component)
            # Explicit local layouts are materialized; cache defaults preserve blobs.
            extra = ['--copy-links']
        elif source.parent.name == 'snapshots':
            source = source.parent.parent
            destination = str(Path(remote_hub)/source.name)
            extra = []
        else:
            # Compatibility for an existing local-dir download while it completes.
            remote_home = subprocess.check_output(['ssh',host,'printf %s "$HOME"'],text=True).strip()
            destination = str(Path(remote_home)/'models/glm53-trellismx'/component)
            extra = ['--copy-links']
        subprocess.run(['ssh', host, 'mkdir -p -- '+shlex.quote(destination)], check=True)
        common = ['-a', '--partial', '--stats', '--exclude=.cache/', *extra,
                  str(source)+'/', host+':'+destination+'/']
        transferred = False
        if rdma and remote_rdma:
            print(f'{host}: syncing {component} over RDMA', flush=True)
            transferred = subprocess.run([rdma, '--rdma=required', '--rdma-rails=auto',
                '--rdma-show-config', '--rsync-path='+shlex.quote(remote_rdma), *common]).returncode == 0
        if not transferred:
            rsync = local_tool('rsync')
            remote_rsync = remote_tool(host, 'rsync')
            if not rsync or not remote_rsync:
                raise RuntimeError(f'{host}: RDMA unavailable or failed, and rsync fallback is unavailable')
            print(f'{host}: RDMA unavailable or failed; syncing {component} with rsync over SSH', flush=True)
            subprocess.run([rsync, '-e', 'ssh', '--rsync-path='+shlex.quote(remote_rsync), *common], check=True)
