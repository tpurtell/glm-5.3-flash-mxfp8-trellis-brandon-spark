"""Locate optional RDMA tools locally and through noninteractive SSH."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess


def local_tool(name):
    found = shutil.which(name)
    if found:
        return found
    for directory in (Path.home()/'.local/bin', Path('/home/linuxbrew/.linuxbrew/bin')):
        candidate = directory/name
        if os.access(candidate, os.X_OK) and candidate.is_file():
            return str(candidate)
    return None


def remote_tool(host, name, override=None):
    if override:
        command = f'command -v -- {shlex.quote(override)}'
    else:
        command = (f'command -v {shlex.quote(name)} || '
                   f'for p in "$HOME/.local/bin/{name}" /home/linuxbrew/.linuxbrew/bin/{name}; '
                   'do if test -x "$p"; then printf "%s\\n" "$p"; break; fi; done')
    result = subprocess.run(['ssh', host, command], text=True, capture_output=True)
    # A failed SSH connection must not silently become a different transfer.
    if result.returncode == 255:
        raise RuntimeError(result.stderr.strip() or f'SSH failed for {host}')
    return result.stdout.strip().splitlines()[0] if result.returncode == 0 and result.stdout.strip() else None
