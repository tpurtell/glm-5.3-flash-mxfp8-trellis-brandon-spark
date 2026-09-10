#!/usr/bin/env python3
"""Launch the same pinned TrellisMX image across two or four Spark hosts."""
import argparse
import datetime
import json
from pathlib import Path
import shlex
import socket
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def execute(host, command, *, check=True):
    argv = command if host in (socket.gethostname(), 'localhost') else [
        'ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', host, shlex.join(command)]
    return subprocess.run(argv, text=True, capture_output=True, check=check)


def docker_command(config, node, rank, args):
    name = f'glm53-trellis-{args.nodes}x-r{rank}'
    command = ['docker', 'run', '-d', '--name', name, '--gpus', 'all',
               '--network', 'host', '--ipc', 'host', '--device', '/dev/infiniband',
               '--cap-add', 'IPC_LOCK', '--ulimit', 'memlock=-1', '--ulimit', 'stack=67108864']
    locations = node.get('model_locations')
    if locations is None:
        locations = {k: {'mount': str(Path(config.get('model_root') or '/models')/k),
                         'container': f'/models/{k}'}
                     for k in ('target', 'carrier', 'draft')}
        if config.get('draft_path'):
            locations['draft']['mount'] = config['draft_path']
    env = {
        'VLLM_TRELLISMX_CHECKPOINT': locations['target']['container'], 'VLLM_HOST_IP': node['ip'],
        'NCCL_SOCKET_IFNAME': config['socket_interface'],
        'GLOO_SOCKET_IFNAME': config['socket_interface'],
        'NCCL_IB_HCA': config['rdma_devices'], 'NCCL_IB_GID_INDEX': str(config['gid_index']),
        'NCCL_NET': 'IB', 'NCCL_IB_DISABLE': '0', 'NCCL_IB_ROCE_VERSION_NUM': '2',
        'NCCL_NET_PLUGIN': 'none', 'NCCL_NVLS_ENABLE': '0', 'NCCL_CUMEM_ENABLE': '0',
        'NCCL_IB_MERGE_NICS': '0', 'NCCL_CROSS_NIC': '1', 'NCCL_DEBUG': 'WARN',
        'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
        'VLLM_CACHE_ROOT': '/cache/vllm', 'TRITON_CACHE_DIR': '/cache/triton',
        'B12X_COMPILE_CACHE_DIR': '/cache/b12x',
        'TRELLISMX_COMPILE_CACHE_DIR': '/cache/trellismx', 'VLLM_ENGINE_READY_TIMEOUT_S': str(args.timeout),
        'VLLM_USE_B12X_SPARSE_INDEXER': '1', 'VLLM_USE_B12X_KPOOL_INDEXER': '1',
    }
    for key, value in env.items():
        command += ['-e', f'{key}={value}']
    for component in ('target', 'carrier') + (('draft',) if args.speculation == 'dflash2' else ()):
        command += ['-v', f"{locations[component]['mount']}:/models/{component}:ro"]
    command += ['-v', f"{config['cache_root']}/{args.nodes}x-r{rank}:/cache"]
    command += [config['image'], locations['carrier']['container'], '--served-model-name', 'glm53-trellismx',
                '--host', '0.0.0.0', '--port', str(args.port),
                '--tensor-parallel-size', str(args.nodes), '--nnodes', str(args.nodes),
                '--node-rank', str(rank), '--master-addr', config['nodes'][0]['ip'],
                '--master-port', str(args.master_port), '--distributed-executor-backend', 'mp',
                '--disable-custom-all-reduce', '--attention-backend', 'B12X_MLA_SPARSE',
                '--kv-cache-dtype', args.kv_cache, '--block-size', '256',
                '--max-model-len', str(args.max_model_len),
                '--max-num-batched-tokens', str(args.batch_tokens),
                '--max-num-seqs', str(args.max_seqs),
                '--gpu-memory-utilization', str(args.memory_utilization),
                '--no-enable-flashinfer-autotune', '--language-model-only',
                '--enable-prefix-caching', '--enable-prompt-tokens-details',
                '--enable-auto-tool-choice',
                '--tool-call-parser', 'glm47', '--reasoning-parser', 'glm45']
    if rank:
        command += ['--headless']
    if args.eager:
        command += ['--enforce-eager']
    if args.ep:
        command += ['--enable-expert-parallel']
    if args.speculation != 'none':
        spec = {'method': 'dflash' if args.speculation == 'dflash2' else 'mtp',
                'num_speculative_tokens': args.draft_tokens}
        if args.speculation == 'dflash2':
            spec.update(model=locations['draft']['container'], draft_tensor_parallel_size=args.draft_tp or args.nodes,
                        kv_cache_dtype='bfloat16', draft_sample_method='probabilistic',
                        rejection_sample_method='standard')
        command += ['--speculative-config', json.dumps(spec)]
    return name, command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'start', 'status', 'stop'])
    parser.add_argument('--config', type=Path, default=ROOT/'cluster.example.json')
    parser.add_argument('--nodes', type=int, choices=[2, 4], required=True)
    parser.add_argument('--speculation', choices=['none', 'mtp', 'dflash2'], default='none')
    parser.add_argument('--draft-tokens', type=int, default=3)
    parser.add_argument('--draft-tp', type=int, choices=[1, 2, 4])
    parser.add_argument('--ep', action='store_true', help='Experimental EP2/EP4 routed experts; distributed serving qualification pending')
    parser.add_argument('--eager', action='store_true')
    parser.add_argument('--max-model-len', type=int, default=8192)
    parser.add_argument('--batch-tokens', type=int, default=1024)
    parser.add_argument('--max-seqs', type=int, default=4)
    parser.add_argument('--memory-utilization', type=float, default=0.85)
    parser.add_argument('--kv-cache', choices=['fp8_ds_mla', 'nvfp4_ds_mla'], default='nvfp4_ds_mla')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--master-port', type=int, default=29553)
    parser.add_argument('--timeout', type=int, default=3600)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    nodes = config['nodes'][:args.nodes]
    if len(nodes) != args.nodes or len({n['host'] for n in nodes}) != args.nodes:
        parser.error('Configuration must contain distinct hosts for every rank')
    if min(args.max_model_len, args.batch_tokens, args.max_seqs, args.draft_tokens) <= 0:
        parser.error('Lengths, batch capacity, sequences and draft tokens must be positive')
    if not 0 < args.memory_utilization < 1:
        parser.error('Memory utilization must be between zero and one')
    if args.action in ('plan', 'start'):
        resolver = (ROOT/'scripts/model_paths.py').read_text().split("if __name__ == '__main__':")[0]
        # This small resolver runs on each host, honoring that host's HF settings.
        resolver = resolver.replace("ROOT = Path(__file__).resolve().parents[1]", "ROOT = Path.cwd()")
        lock = json.loads((ROOT/'sources.lock.json').read_text())
        for node in nodes:
            code = resolver + '\nlock = ' + repr(lock) + '\nresult = {}\n'
            code += 'for k in COMPONENTS:\n'
            code += '    p = resolve(k, lock, ' + repr(config.get('model_root')) + ')\n'
            if config.get('draft_path'):
                code += '    if k == "draft": p = Path(' + repr(config['draft_path']) + ')\n'
            code += '    m, c = mount(p, k)\n    result[k] = dict(path=str(p), mount=m, container=c)\nprint(json.dumps(result))\n'
            node['model_locations'] = json.loads(execute(node['host'], ['python3','-c',code]).stdout)
    plan = [dict(host=node['host'], name=name, command=command, model_locations=node.get('model_locations'))
            for rank, node in enumerate(nodes)
            for name, command in [docker_command(config, node, rank, args)]]
    receipt = {'created': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'source_commit': subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
               'sources':json.loads((ROOT/'sources.lock.json').read_text()), 'plan':plan}
    if args.action == 'plan':
        print(json.dumps(receipt, indent=2)); return
    if args.action in ('status','stop'):
        for item in plan:
            command = ['docker', 'inspect', '--format', '{{json .State}}', item['name']] if args.action == 'status' else ['docker','stop',item['name']]
            result = execute(item['host'], command, check=False)
            print(item['host'], result.stdout.strip() or result.stderr.strip())
        return
    # Preflight every node before creating any containers. Never replace a live run.
    for item in plan:
        host = item['host']
        existing = execute(host, ['docker','inspect','--format','{{.State.Running}}',item['name']], check=False)
        if existing.returncode == 0 and existing.stdout.strip() == 'true':
            raise RuntimeError(f"{host}: {item['name']} is already running")
        item['image_id'] = execute(host, ['docker','image','inspect','--format','{{.Id}}',config['image']]).stdout.strip()
        locations = item['model_locations']
        for component, file in (('carrier','config.json'),('target','trellismx-manifest.json')):
            execute(host, ['test','-f',str(Path(locations[component]['path'])/file)])
        inventory_check = """import json,sys
from pathlib import Path
target,carrier=map(Path,sys.argv[1:])
manifest=json.loads((target/'trellismx-manifest.json').read_text())
for record in manifest['files']:
    path=target/record['path']
    if not path.is_file() or path.stat().st_size != record['bytes']:
        raise RuntimeError(f'Missing or incomplete sidecar: {path}')
index=json.loads((carrier/'model.safetensors.index.json').read_text())
for shard in set(index['weight_map'].values()):
    if not (carrier/shard).is_file():
        raise RuntimeError(f'Missing carrier shard: {shard}')
"""
        execute(host, ['python3','-c',inventory_check,locations['target']['path'],locations['carrier']['path']])
        if args.speculation == 'dflash2':
            execute(host, ['test','-f',str(Path(locations['draft']['path'])/'config.json')])
    if len({item['image_id'] for item in plan}) != 1:
        raise RuntimeError('All ranks must use the identical image ID')
    run_dir = ROOT/'.work'/'launches'/datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt_path = run_dir/'launch.json'
    def save():
        receipt_path.write_text(json.dumps(receipt, indent=2)+'\n')
    save()
    started = time.monotonic()
    try:
        for item in list(reversed(plan[1:])) + plan[:1]:
            execute(item['host'], ['docker','rm',item['name']], check=False)
            item['container_id'] = execute(item['host'], item['command']).stdout.strip()
            save()
        url = f"http://{nodes[0]['ip']}:{args.port}/health"
        while time.monotonic() - started < args.timeout:
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    if response.status == 200:
                        receipt['ready_seconds'] = time.monotonic()-started
                        save(); print(str(receipt_path)); return
            except OSError:
                pass
            for item in plan:
                state = execute(item['host'], ['docker','inspect','--format','{{.State.Running}}',item['name']], check=False)
                if state.returncode == 0 and state.stdout.strip() == 'false':
                    raise RuntimeError(f"{item['host']}: container exited; inspect docker logs {item['name']}")
            time.sleep(5)
        raise TimeoutError('Readiness timeout; containers retained for inspection')
    except Exception as exc:
        receipt['error'] = str(exc); save(); raise


if __name__ == '__main__':
    main()
