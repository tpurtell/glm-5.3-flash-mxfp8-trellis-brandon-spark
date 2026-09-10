#!/usr/bin/env python3
"""Resolve pinned models in the Hugging Face cache or an explicit local layout."""
import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ('target', 'carrier', 'draft')

def hub_cache():
    home = Path(os.environ.get('HF_HOME', str(Path(os.environ.get('XDG_CACHE_HOME', str(Path.home()/'.cache')))/'huggingface'))).expanduser()
    return Path(os.environ.get('HF_HUB_CACHE', str(home/'hub'))).expanduser()

def snapshot(component, lock, hub=None):
    item = lock[component]
    return (hub or hub_cache())/('models--'+item['repo_id'].replace('/', '--'))/'snapshots'/item['revision']

def resolve(component, lock, model_root=None):
    # Explicit overrides retain their meaning. Otherwise reuse Mia's HF layout.
    override = model_root or os.environ.get('MODEL_ROOT')
    if override:
        return Path(override).expanduser()/component
    caches = [hub_cache(), Path.home()/'.cache/huggingface/hub']
    for cache in dict.fromkeys(caches):
        candidate = snapshot(component, lock, cache)
        if candidate.is_dir():
            return candidate
    legacy = Path.home()/'models/glm53-trellismx'/component
    if legacy.is_dir():
        return legacy
    return snapshot(component, lock)

def mount(path, component):
    path = Path(path).resolve()
    # Mount the entire repo so snapshot -> blob symlinks remain valid in Docker.
    if path.parent.name == 'snapshots':
        return str(path.parent.parent), f'/models/{component}/snapshots/{path.name}'
    return str(path), f'/models/{component}'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('component', choices=COMPONENTS)
    parser.add_argument('--model-root')
    args = parser.parse_args()
    print(resolve(args.component, json.loads((ROOT/'sources.lock.json').read_text()), args.model_root))
