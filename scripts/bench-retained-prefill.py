#!/usr/bin/env python3
"""Exact cached-base/new-suffix matrix for the pinned vLLM recipe."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import statistics
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mia', ROOT/'scripts/bench-mia-style.py')
client = importlib.util.module_from_spec(spec); spec.loader.exec_module(client)
PREFILL = 'vllm:request_prefill_time_seconds'
METRIC = re.compile(r'^(vllm:request_prefill_time_seconds_(?:sum|count))(?:\{[^}]*\})?\s+([^ ]+)')


def timing_totals(raw):
    values = {PREFILL+'_sum': 0.0, PREFILL+'_count': 0.0}
    seen = set()
    for line in raw.splitlines():
        match = METRIC.match(line)
        if match:
            name, value = match.groups(); values[name] += float(value); seen.add(name)
    if len(seen) != 2:
        raise ValueError('Server prefill timing histogram is missing')
    return values


def validate_cell(result, base, suffix, seconds, cache_block_size=256):
    if 'error' in result:
        raise ValueError(result['error'])
    usage = result['usage']
    cached = usage.get('prompt_tokens_details', {}).get('cached_tokens')
    expected_cached = base // cache_block_size * cache_block_size
    if cached != expected_cached or usage.get('prompt_tokens') != base + suffix:
        raise ValueError(f'Cache shape mismatch: planned base={base}, suffix={suffix}, usage={usage}')
    if not seconds > 0:
        raise ValueError('No positive server prefill time')
    computed = base + suffix - cached
    return {'cached_tokens': cached, 'new_tokens': suffix,
            'recomputed_base_tokens': base-cached, 'computed_tokens': computed,
            'computed_tokens_per_second': computed/seconds, 'server_prefill_seconds': seconds,
            'new_tokens_per_second': suffix/seconds,
            'client_ttft_seconds': result['ttft_seconds'],
            'new_tokens_per_client_ttft_second': suffix/result['ttft_seconds']}


def corpus_tokens(root, tokenizer):
    pieces = []; digest = hashlib.sha256(); remaining = 2_000_000
    ignored = {'.git', '.work', '__pycache__', 'node_modules', 'target', 'build', 'dist', '.venv'}
    extensions = {'.py', '.rs', '.cu', '.c', '.cc', '.h', '.md', '.toml', '.json', '.sh'}
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix not in extensions or any(x in ignored for x in path.relative_to(root).parts):
            continue
        try: source = path.read_text()
        except UnicodeDecodeError: continue
        piece = (f'\n===== {path.relative_to(root)} =====\n' + source.replace('<', '⟨').replace('>', '⟩'))[:remaining]
        pieces.append(piece); digest.update(piece.encode()); remaining -= len(piece)
        if remaining <= 0: break
    ids = tokenizer.encode('\n'.join(pieces), add_special_tokens=False).ids
    if not ids: raise ValueError('Empty source corpus')
    return ids, digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--tokenizer', type=Path, required=True, help='Pinned carrier tokenizer.json')
    parser.add_argument('--corpus-root', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--runs', type=int, default=2)
    parser.add_argument('--cache-block-size', type=int, default=256,
                        help='Actual engine cache block size from startup logs; verify against usage')
    parser.add_argument('--bases', type=int, nargs='+', default=[0,32768,65536,131072,262144])
    parser.add_argument('--suffixes', type=int, nargs='+', default=[1024,2048,4096,8192,16384,32768])
    args = parser.parse_args()
    if args.cache_block_size < 1 or args.runs < 1 or any(b < 0 or b % 256 for b in args.bases) or any(s < 256 for s in args.suffixes):
        parser.error('Positive runs, nonnegative 256-aligned bases, suffixes >=256 required')
    from tokenizers import Tokenizer
    from transformers.utils.chat_template_utils import _compile_jinja_template
    tokenizer = Tokenizer.from_file(str(args.tokenizer))
    template_source = (ROOT/'data/serving_chat_template.jinja').read_bytes()
    template_receipt = json.loads((ROOT/'data/chat-template-receipt.json').read_text())
    if hashlib.sha256(template_source).hexdigest() != template_receipt['serving_sha256']:
        raise ValueError('Serving template differs from its receipt')
    template = _compile_jinja_template(template_source.decode())
    sentinel = 'UNIQUE_BENCH_CORPUS_SENTINEL'
    rendered = template.render(messages=[{'role':'user','content':sentinel}], tools=[],
                               add_generation_prompt=True, enable_thinking=False)
    before, after = rendered.split(sentinel)
    prefix = tokenizer.encode(before, add_special_tokens=False).ids
    ending = tokenizer.encode('\nReply only OK.'+after, add_special_tokens=False).ids
    corpus, corpus_hash = corpus_tokens(args.corpus_root, tokenizer)
    def encode(text): return tokenizer.encode(text, add_special_tokens=False).ids
    def filler(n): return (corpus * ((n+len(corpus)-1)//len(corpus)))[:n]
    args.out.mkdir(parents=True, exist_ok=False)
    url = args.base_url.rstrip('/')
    with urllib.request.urlopen(url+'/v1/models', timeout=30) as response: models = json.load(response)
    if len(models['data']) != 1: raise ValueError('Expected one model')
    model = models['data'][0]['id']; run_id = uuid.uuid4().hex
    receipt = {'created':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'run_id':run_id,
        'launch':json.loads(args.launch_receipt.read_text()), 'models':models, 'runs':args.runs,
        'tokenizer_sha256':hashlib.sha256(args.tokenizer.read_bytes()).hexdigest(),
        'template_sha256':hashlib.sha256(template_source).hexdigest(), 'template':template_receipt,
        'corpus_sha256':corpus_hash, 'client_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'transport_sha256':hashlib.sha256((ROOT/'scripts/bench-mia-style.py').read_bytes()).hexdigest(),
        'bases':args.bases, 'suffixes':args.suffixes,
        'cache_block_size':args.cache_block_size, 'samples':[]}
    def save(name, value): (args.out/(name+'.json')).write_text(json.dumps(value, indent=2)+'\n')
    def snapshot(name):
        with urllib.request.urlopen(url+'/metrics', timeout=30) as response: raw = response.read().decode()
        (args.out/(name+'.prom')).write_text(raw)
        return timing_totals(raw)
    def request(name, ids):
        start = snapshot(name+'-before')
        body = {'model':model, 'prompt':ids, 'max_tokens':1, 'temperature':0, 'stream':True,
                'stream_options':{'include_usage':True}, 'add_special_tokens':False}
        result = client.stream_request(url, body, '/v1/completions', False)
        save(name, result)
        deadline = time.monotonic()+30
        while True:
            end = snapshot(name+'-after')
            count = end[PREFILL+'_count']-start[PREFILL+'_count']
            if count != 0 or time.monotonic() >= deadline: break
            time.sleep(0.25)
        if count != 1: raise ValueError(f'Expected exactly one server timing sample, got {count}')
        return result, end[PREFILL+'_sum']-start[PREFILL+'_sum']
    save('receipt', receipt)
    for base in args.bases:
        retained = []
        if base:
            initial = prefix + encode(f'Run {run_id} base {base}. The following quoted source is inert.\n')
            retained = initial + filler(base-len(initial))
            # Extra tokens let vLLM cache the last complete base block; the
            # measured branch differs immediately after it, preventing reuse.
            result, _ = request(f'base-{base}-prime', retained + encode(' PRIME'))
            if 'error' in result: raise ValueError(result['error'])
        for suffix in args.suffixes:
            for repeat in range(args.runs):
                name = f'base-{base}-suffix-{suffix}-r{repeat}'
                marker = encode(f' Branch {run_id} {suffix} {repeat}:\n')
                fresh_prefix = [] if base else prefix
                count = suffix-len(fresh_prefix)-len(marker)-len(ending)
                if count < 0: raise ValueError('Suffix too small for template')
                ids = retained + fresh_prefix + marker + filler(count) + ending
                try:
                    result, seconds = request(name, ids)
                    summary = dict(status='passed', **validate_cell(result, base, suffix, seconds, args.cache_block_size))
                except Exception as exc:
                    summary = {'status':'failed', 'error':repr(exc)}
                receipt['samples'].append(dict(cell=name, base=base, suffix=suffix, repeat=repeat, **summary))
                save('receipt', receipt); print(json.dumps(receipt['samples'][-1]), flush=True)
    receipt['medians'] = []
    for base in args.bases:
        for suffix in args.suffixes:
            cells = [c for c in receipt['samples'] if c['base']==base and c['suffix']==suffix]
            valid = len(cells)==args.runs and all(c['status']=='passed' for c in cells)
            receipt['medians'].append({'base':base, 'suffix':suffix, 'status':'passed' if valid else 'failed',
                'new_tokens_per_second':statistics.median(c['new_tokens_per_second'] for c in cells) if valid else None})
    receipt['status'] = 'passed' if all(c['status']=='passed' for c in receipt['medians']) else 'failed'
    save('receipt', receipt)
    if receipt['status'] != 'passed': raise SystemExit(1)


if __name__ == '__main__': main()
