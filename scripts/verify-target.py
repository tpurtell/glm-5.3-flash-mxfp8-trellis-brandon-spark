#!/usr/bin/env python3
"""Verify the pinned TrellisMX manifest, all sidecar hashes and metadata."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'overlay'))
from trellismx_manifest import load_overlay

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('directory', type=Path)
args = parser.parse_args()
overlay = load_overlay(str(args.directory))
for index, (layer, rank) in enumerate(sorted(overlay.records), 1):
    overlay.sidecar(layer, rank, verify=True)
    print(json.dumps({'verified': index, 'total': len(overlay.records),
                      'layer': layer, 'tp4_rank': rank}), flush=True)
print(json.dumps({'status': 'passed', 'sidecars': len(overlay.records),
                  'transform_sha256': overlay.transform_hash}), flush=True)
