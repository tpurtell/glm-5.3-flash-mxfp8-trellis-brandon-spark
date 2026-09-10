#!/usr/bin/env python3
"""Move a verified legacy snapshot into the real HF cache without downloading it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from model_paths import ROOT, COMPONENTS, snapshot


def adopt(component, source, lock):
    destination = snapshot(component, lock)
    if source.resolve() == destination.resolve():
        return destination
    records = {}
    if component == 'carrier':
        records = {r['path']: r['digest'] for r in json.loads((ROOT/'data/carrier-files.json').read_text())['files']}
    elif component == 'target':
        records = {r['path']: r['sha256'] for r in json.loads((source/'trellismx-manifest.json').read_text())['files']}
    files = [p for p in source.rglob('*') if p.is_file() and '.cache' not in p.relative_to(source).parts]
    for path in files:
        relative = path.relative_to(source)
        digest = records.get(relative.as_posix())
        metadata = source/'.cache/huggingface/download'/f'{relative}.metadata'
        if not digest and metadata.exists():
            lines = metadata.read_text().splitlines()
            if lines[0] != lock[component]['revision']:
                raise ValueError(f'Unexpected revision: {metadata}')
            digest = lines[1]
        if not digest:
            # Unlisted small Git assets or a draft imported from another cache.
            hasher = hashlib.sha256() if path.suffix == '.safetensors' else hashlib.sha1()
            if path.suffix != '.safetensors':
                hasher.update(f'blob {path.stat().st_size}\0'.encode())
            with path.open('rb') as f:
                while block := f.read(8*1024*1024):
                    hasher.update(block)
            digest = hasher.hexdigest()
        if len(digest) not in (40, 64) or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError(f'Invalid blob identity: {path}')
        blob = destination.parent.parent/'blobs'/digest
        blob.parent.mkdir(parents=True, exist_ok=True)
        if blob.exists():
            if blob.stat().st_size != path.stat().st_size:
                raise ValueError(f'Conflicting cache blob: {blob}')
        else:
            # Rename is atomic and avoids copying hundreds of GB on the same disk.
            # Cross-device moves use shutil's copy-then-remove fallback.
            shutil.move(str(path), str(blob))
        target = destination/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            if target.resolve() != blob.resolve():
                raise ValueError(f'Conflicting cached snapshot file: {target}')
        else:
            target.symlink_to(os.path.relpath(blob, target.parent))
        # Keep the old view usable during migration and on interrupted retries.
        if path.exists() or path.is_symlink():
            path.unlink()
        path.symlink_to(target)
    # Retain legacy entry points as aliases, with all actual bytes in HF cache.
    shutil.rmtree(source)
    source.symlink_to(destination, target_is_directory=True)
    return destination

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-root', type=Path, required=True)
    parser.add_argument('--verified', action='store_true', required=True,
                        help='Assert the pinned target/carrier verification has passed')
    args = parser.parse_args()
    lock = json.loads((ROOT/'sources.lock.json').read_text())
    for component in COMPONENTS:
        print(json.dumps({'component': component, 'snapshot': str(adopt(component, args.model_root/component, lock))}), flush=True)
