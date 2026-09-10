#!/usr/bin/env python3
"""Distributed GPU correctness check for Spark NCCL/RoCE, not a speed test."""
import argparse
import datetime
import json
import socket
import torch
import torch.distributed as dist

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rank',type=int,required=True)
parser.add_argument('--world-size',type=int,required=True)
parser.add_argument('--master',required=True)
args=parser.parse_args()
torch.cuda.set_device(0)
dist.init_process_group('nccl',init_method=f'tcp://{args.master}',rank=args.rank,
                        world_size=args.world_size,timeout=datetime.timedelta(seconds=180),
                        device_id=torch.device('cuda',0))
expected=args.world_size*(args.world_size+1)/2
for size in (1,4096,1048576):
    data=torch.full((size,),float(args.rank+1),device='cuda')
    dist.all_reduce(data);torch.cuda.synchronize()
    assert torch.equal(data,torch.full_like(data,expected))
    for _ in range(3):
        data.fill_(args.rank+1);dist.all_reduce(data)
    torch.cuda.synchronize();dist.barrier()
    graph=torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        dist.all_reduce(data)
    for _ in range(3):
        data.fill_(args.rank+1);graph.replay();torch.cuda.synchronize()
        assert torch.equal(data,torch.full_like(data,expected))
    print(json.dumps({'host':socket.gethostname(),'rank':args.rank,'world_size':args.world_size,
                      'elements':size,'eager_exact':True,'graph_replay_exact':True}),flush=True)
dist.destroy_process_group()
