#!/usr/bin/env python3
"""Native P8 single-layer bring-up; no serving-performance claim."""
import argparse
import hashlib
import json
from pathlib import Path
import torch
from b12x.moe._shared.trellismx.p8_native_kernel import P8NativeTPMoE

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('checkpoint', type=Path)
parser.add_argument('--layer', type=int, default=3)
parser.add_argument('--tp2', action='store_true')
args = parser.parse_args()
manifest = json.loads((args.checkpoint / 'trellismx-manifest.json').read_text())
records = {r['rank']: r for r in manifest['files'] if r['layer'] == args.layer}
paths = []
for rank in range(2 if args.tp2 else 1):
    record = records[rank]
    path = args.checkpoint / record['path']
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert digest == record['sha256'], f'Parent {rank} hash mismatch'
    paths.append(path)
transform_hash = hashlib.sha256((args.checkpoint / 'design/transform.json').read_bytes()).hexdigest()
torch.manual_seed(20260910)
print(json.dumps({'gpu': torch.cuda.get_device_name(), 'capability': torch.cuda.get_device_capability(),
                  'torch': torch.__version__, 'layer': args.layer,
                  'parents': [records[r]['sha256'] for r in range(len(paths))]}), flush=True)

def make(rank, tp):
    return P8NativeTPMoE(tuple(paths) if tp == 2 else paths[rank],
        device=torch.device('cuda'), tp_rank=rank, world_size=tp, layer=args.layer,
        tp4_parent_sha256=tuple(records[r]['sha256'] for r in range(2)) if tp == 2 else None,
        expected_design_sha256=records[rank]['source_design_sha256'],
        expected_transform_sha256=transform_hash,
        intermediate=2048//tp, small_m_scheduler=True, fc1_tile_n=128,
        fuse_scratch_zero=True, grid_policy=True, fc1_warp_quant=False, fc1_broadcast_a=True)

runtimes = [make(r, 4) for r in range(len(paths))]
joined = make(0, 2) if args.tp2 else None
with torch.inference_mode():
    for m in (1, 8, 32, 128):
        x = torch.randn((m, 4096), dtype=torch.bfloat16, device='cuda') * 0.1
        ids = torch.stack([torch.randperm(288, device='cuda')[:8] for _ in range(m)]).int()
        weights = torch.softmax(torch.randn(m, 8, device='cuda'), dim=-1)
        outputs = []
        for runtime in [*runtimes, *([joined] if joined else [])]:
            for _ in range(2):
                reference = runtime(x, weights, ids).clone()
            torch.cuda.synchronize()
            assert torch.isfinite(reference).all() and torch.count_nonzero(reference), 'Invalid output'
            graph = torch.cuda.CUDAGraph()
            with torch.cuda.graph(graph):
                captured = runtime(x, weights, ids)
            for _ in range(3):
                graph.replay()
            torch.cuda.synchronize()
            torch.testing.assert_close(captured, reference, rtol=0, atol=0)
            outputs.append(reference)
            print(json.dumps({'tokens': m, 'tp': runtime.world_size, 'rank': runtime.tp_rank,
                              'finite_nonzero': True, 'graph_replay_exact': True}), flush=True)
        if joined:
            expected = outputs[0].float() + outputs[1].float()
            actual = outputs[2].float()
            cosine = torch.nn.functional.cosine_similarity(expected.flatten(), actual.flatten(), dim=0).item()
            relative_l2 = ((expected-actual).norm()/expected.norm()).item()
            print(json.dumps({'tokens': m, 'tp2_vs_tp4_pair_cosine': cosine,
                              'relative_l2': relative_l2}), flush=True)
            # A changed TP reduction rounds at different BF16 boundaries.
            assert cosine >= 0.999 and relative_l2 <= 0.02, 'TP2 partition equivalence failed'
print(json.dumps({'status': 'passed', 'scope': 'native layer and graph replay only'}), flush=True)
