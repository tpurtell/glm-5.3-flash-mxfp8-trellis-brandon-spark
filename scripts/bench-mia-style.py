#!/usr/bin/env python3
"""Fresh sparkDash-style decode/prefill block, separate from weighted workloads."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]


def stream(base, model, prompt, max_tokens, require_decode=True, response_format=None):
    body = dict(model=model, messages=[{'role':'user','content':prompt}],
                temperature=0, top_p=1, max_tokens=max_tokens, stream=True,
                stream_options={'include_usage':True},
                chat_template_kwargs={'enable_thinking':False})
    if response_format is not None:
        body['response_format'] = response_format
    return stream_request(base, body, '/v1/chat/completions', require_decode)


def stream_request(base, body, endpoint, require_decode=True):
    result = {'request':body, 'start':time.perf_counter(), 'events':[]}
    first = last = None
    text = reasoning = ''
    usage = {}
    try:
        request = urllib.request.Request(base+endpoint,
            data=json.dumps(body).encode(), headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request, timeout=2700) as response:
            for line in response:
                if not line.startswith(b'data:'):
                    continue
                data = line[5:].strip()
                if data == b'[DONE]':
                    break
                event = json.loads(data)
                now = time.perf_counter()
                result['events'].append({'time':now,'data':event})
                if event.get('usage'):
                    usage = event['usage']
                for choice in event.get('choices',[]):
                    delta = choice.get('delta',{})
                    content = delta.get('content') or choice.get('text') or ''
                    thought = delta.get('reasoning_content') or delta.get('reasoning') or ''
                    if content or thought:
                        first = now if first is None else first
                        last = now
                    text += content
                    reasoning += thought
        if not usage.get('completion_tokens') or first is None or (require_decode and last <= first):
            raise ValueError('Missing token usage or a valid streamed decode window; no chunk-count fallback')
        decode_tokens = usage['completion_tokens'] - 1
        result.update(first=first,last=last,usage=usage,text=text,reasoning=reasoning,
                      decode_tokens=decode_tokens,decode_tps=decode_tokens/(last-first) if last>first else None,
                      ttft_seconds=first-result['start'],
                      prefill_tps=usage['prompt_tokens']/(first-result['start']))
        if reasoning or '<think>' in text or '</think>' in text:
            raise ValueError('Thinking-off request generated reasoning; comparison cell invalid')
    except Exception as exc:
        result['error'] = repr(exc)
    result['end'] = time.perf_counter()
    return result


def wave_summary(results):
    if any('error' in r for r in results):
        return {'status':'failed', 'failures':sum('error' in r for r in results)}
    return {'status':'passed', 'concurrency':len(results),
            'mean_stream_tps':statistics.mean(r['decode_tps'] for r in results),
            'median_stream_tps':statistics.median(r['decode_tps'] for r in results),
            'median_ttft_seconds':statistics.median(r['ttft_seconds'] for r in results),
            'aggregate_tps':sum(r['decode_tokens'] for r in results)/
                (max(r['last'] for r in results)-min(r['first'] for r in results))}


def prefill_prompt(tokens, salt):
    header = f'[prefill-bench {salt}]\nIgnore the filler below. Reply with the single word OK.\n'
    footer = '\nReply OK.'
    reserved = math.ceil(len(header+footer)/4)
    return header + ' the'*max(1,tokens-reserved) + footer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('block', choices=['decode','prefill'])
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--launch-receipt',type=Path,required=True)
    parser.add_argument('--runs',type=int,default=5)
    args = parser.parse_args()
    if args.runs < 1:
        parser.error('--runs must be positive')
    args.out.mkdir(parents=True,exist_ok=False)
    base = args.base_url.rstrip('/')
    with urllib.request.urlopen(base+'/v1/models',timeout=30) as response:
        models = json.load(response)
    if len(models['data']) != 1:
        raise ValueError('Expected one served target')
    model = models['data'][0]['id']
    receipt = {'block':args.block,'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'launch':json.loads(args.launch_receipt.read_text()),
               'template':json.loads((ROOT/'data/chat-template-receipt.json').read_text()),
               'benchmark_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'sparkdash_revision':'f035ca243855b3a88c270a9a84a358c2cb1fbcc3',
               'models':models,'runs':args.runs,'cells':[]}
    def save(name,value):
        (args.out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    def metrics(label):
        with urllib.request.urlopen(base+'/metrics',timeout=30) as response:
            (args.out/(label+'.prom')).write_bytes(response.read())
    save('receipt',receipt)
    metrics('before')
    if args.block == 'decode':
        prompts = json.loads((ROOT/'data/mia-prompts.json').read_text())
        for kind in ('structured','code','prose'):
            warmup = stream(base,model,prompts[kind],32)
            save(f'{kind}-warmup',warmup)
            if 'error' in warmup:
                raise RuntimeError(warmup['error'])
            for concurrency in (1,2,4):
                for repeat in range(args.runs):
                    cell = f'{kind}-c{concurrency}-r{repeat}'
                    requests = [prompts[kind] + (f' (stream {i+1}/{concurrency})' if concurrency>1 else '')
                                for i in range(concurrency)]
                    with ThreadPoolExecutor(max_workers=concurrency) as executor:
                        results = list(executor.map(lambda prompt:stream(base,model,prompt,400),requests))
                    summary = wave_summary(results)
                    save(cell,{'results':results,'summary':summary})
                    receipt['cells'].append(dict(cell=cell,**summary));save('receipt',receipt)
                    print(json.dumps(receipt['cells'][-1]),flush=True)
    else:
        warmup = stream(base,model,prefill_prompt(512,str(uuid.uuid4())),8,False)
        save('warmup',warmup)
        if 'error' in warmup:
            raise RuntimeError(warmup['error'])
        for tokens in (8192,16384,32768,65536,131072,262144):
            for repeat in range(args.runs):
                cell=f'prefill-{tokens}-r{repeat}'
                metrics(cell+'-before')
                result=stream(base,model,prefill_prompt(tokens,str(uuid.uuid4())),8,False)
                metrics(cell+'-after')
                save(cell,result)
                summary={'cell':cell,'status':'failed' if 'error' in result else 'passed',
                         'nominal_tokens':tokens,'prefill_tps':result.get('prefill_tps'),
                         'prompt_tokens':result.get('usage',{}).get('prompt_tokens'),
                         'ttft_seconds':result.get('ttft_seconds')}
                receipt['cells'].append(summary);save('receipt',receipt)
                print(json.dumps(summary),flush=True)
    metrics('after')
    receipt['status']='passed' if all(c['status']=='passed' for c in receipt['cells']) else 'failed'
    save('receipt',receipt)
    if receipt['status'] != 'passed':
        raise SystemExit(1)


if __name__=='__main__':
    main()
