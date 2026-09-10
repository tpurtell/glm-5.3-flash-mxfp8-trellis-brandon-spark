#!/usr/bin/env python3
"""Distribute pinned snapshots and their blobs using required RDMA transport."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from model_paths import COMPONENTS, ROOT, resolve

if len(sys.argv) < 2:
    raise SystemExit('Usage: scripts/sync-models.sh host [host ...]')
lock = json.loads((ROOT/'sources.lock.json').read_text())
resolver = (ROOT/'scripts/model_paths.py').read_text().split("if __name__ == '__main__':")[0]
resolver = resolver.replace('ROOT = Path(__file__).resolve().parents[1]', 'ROOT = Path.cwd()')
for host in sys.argv[1:]:
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
        subprocess.run(['rdmasync','-a','--partial','--mkpath','--rdma=required',
                        '--rdma-rails=auto','--rdma-show-config','--stats',
                        '--rsync-path='+os.environ.get('REMOTE_RDMASYNC','/home/tj/.local/bin/rdmasync'),
                        '--exclude=.cache/', *extra, str(source)+'/', host+':'+destination+'/'],check=True)
