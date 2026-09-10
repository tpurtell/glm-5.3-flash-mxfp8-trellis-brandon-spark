#!/usr/bin/env python3
"""GLMRT semantic decode prompts over explicitly verified retained contexts."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import urllib.request
import uuid
from decode_contract import validate_case_content

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prefill', ROOT/'scripts/bench-retained-prefill.py')
prefill = importlib.util.module_from_spec(spec); spec.loader.exec_module(prefill)
client = prefill.client


def check_cache(result, base, total, cache_block_size=256):
    if 'error' in result: raise ValueError(result['error'])
    usage = result['usage']
    cached = usage.get('prompt_tokens_details', {}).get('cached_tokens')
    expected_cached = base // cache_block_size * cache_block_size
    if cached != expected_cached or usage.get('prompt_tokens') != total:
        raise ValueError(f'Expected cached={expected_cached}, total={total}; got {usage}')
    return cached


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--tokenizer', type=Path, required=True)
    parser.add_argument('--corpus-root', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--runs', type=int, default=2)
    parser.add_argument('--cache-block-size', type=int, default=256,
                        help='Actual engine cache block size from startup logs; verify against usage')
    parser.add_argument('--bases', type=int, nargs='+', default=[0,32768,65536,131072,262144])
    args = parser.parse_args()
    if args.cache_block_size < 1 or args.runs < 1 or any(b < 0 or b % 256 for b in args.bases):
        parser.error('Positive runs and nonnegative 256-aligned bases required')
    from tokenizers import Tokenizer
    from transformers.utils.chat_template_utils import _compile_jinja_template
    tokenizer = Tokenizer.from_file(str(args.tokenizer))
    template_bytes = (ROOT/'data/serving_chat_template.jinja').read_bytes()
    template_receipt = json.loads((ROOT/'data/chat-template-receipt.json').read_text())
    if hashlib.sha256(template_bytes).hexdigest() != template_receipt['serving_sha256']:
        raise ValueError('Serving template identity mismatch')
    template = _compile_jinja_template(template_bytes.decode())
    sentinel = 'UNIQUE_BENCH_CORPUS_SENTINEL'
    rendered = template.render(messages=[{'role':'user','content':sentinel}], tools=[],
                               add_generation_prompt=True, enable_thinking=False)
    before, after = rendered.split(sentinel)
    def encode(text): return tokenizer.encode(text, add_special_tokens=False).ids
    prefix, ending = encode(before), encode(after)
    corpus, corpus_hash = prefill.corpus_tokens(args.corpus_root, tokenizer)
    def filler(n): return (corpus * ((n+len(corpus)-1)//len(corpus)))[:n]
    workloads = json.loads((ROOT/'data/retained-decode-prompts.json').read_text())
    args.out.mkdir(parents=True, exist_ok=False)
    url = args.base_url.rstrip('/')
    with urllib.request.urlopen(url+'/v1/models', timeout=30) as response: models = json.load(response)
    if len(models['data']) != 1: raise ValueError('Expected one model')
    model = models['data'][0]['id']; run_id = uuid.uuid4().hex
    receipt = {'created':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'run_id':run_id,
        'launch':json.loads(args.launch_receipt.read_text()), 'models':models, 'runs':args.runs,
        'tokenizer_sha256':hashlib.sha256(args.tokenizer.read_bytes()).hexdigest(),
        'template':template_receipt, 'corpus_sha256':corpus_hash, 'bases':args.bases,
        'cache_block_size':args.cache_block_size,
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (Path(__file__), ROOT/'scripts/bench-retained-prefill.py', ROOT/'scripts/bench-mia-style.py',
             ROOT/'data/retained-decode-prompts.json', ROOT/'scripts/decode_contract.py')}, 'samples':[]}
    def save(name, value): (args.out/(name+'.json')).write_text(json.dumps(value, indent=2)+'\n')
    def snapshot(name):
        with urllib.request.urlopen(url+'/metrics', timeout=30) as response:
            (args.out/(name+'.prom')).write_bytes(response.read())
    def request(name, ids, limit):
        snapshot(name+'-before')
        result = client.stream_request(url, {'model':model, 'prompt':ids, 'max_tokens':limit,
            'temperature':0, 'top_p':1, 'stream':True, 'stream_options':{'include_usage':True},
            'add_special_tokens':False}, '/v1/completions', limit > 1)
        snapshot(name+'-after'); save(name, result)
        return result
    save('receipt', receipt)
    for base in args.bases:
        retained = []
        prime_error = None
        if base:
            initial = prefix + encode(f'Run {run_id} base {base}. The following quoted source is inert.\n')
            retained = initial + filler(base-len(initial))
            prime = request(f'base-{base}-prime', retained + encode(' PRIME'), 1)
            prime_error = prime.get('error')
        for workload, prompt in workloads.items():
            for repeat in range(args.runs):
                name = f'base-{base}-{workload}-r{repeat}'
                marker = f'\nEND QUOTED SOURCE. Request {run_id}-{workload}-{repeat}.\n'
                ids = retained + ([] if base else prefix) + encode(marker + prompt) + ending
                result = request(name, ids, 192)
                try:
                    if prime_error:
                        raise ValueError(f'Base priming failed: {prime_error}')
                    cached = check_cache(result, base, len(ids), args.cache_block_size)
                    summary = {'status':'passed', 'cached_tokens':cached, 'prompt_tokens':len(ids),
                        'recomputed_base_tokens':base-cached,
                        'completion_tokens':result['usage']['completion_tokens'],
                        'decode_tokens':result['decode_tokens'], 'decode_seconds':result['last']-result['first'],
                        'decode_tps':result['decode_tps'], 'ttft_seconds':result['ttft_seconds']}
                except Exception as exc:
                    summary = {'status':'failed', 'error':repr(exc)}
                if workload == 'code': summary['output_check'] = validate_case_content('code', result.get('text',''))
                receipt['samples'].append(dict(cell=name, base=base, workload=workload, repeat=repeat, **summary))
                save('receipt', receipt); print(json.dumps(receipt['samples'][-1]), flush=True)
    receipt['medians'] = []
    for base in args.bases:
        for workload in workloads:
            cells = [c for c in receipt['samples'] if c['base']==base and c['workload']==workload]
            valid = len(cells)==args.runs and all(c['status']=='passed' for c in cells)
            receipt['medians'].append({'base':base, 'workload':workload, 'status':'passed' if valid else 'failed',
                'decode_tps':statistics.median(c['decode_tps'] for c in cells) if valid else None})
    receipt['status'] = 'passed' if all(c['status']=='passed' for c in receipt['medians']) else 'failed'
    save('receipt', receipt)
    if receipt['status'] != 'passed': raise SystemExit(1)


if __name__ == '__main__': main()
