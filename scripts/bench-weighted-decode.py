#!/usr/bin/env python3
"""Five mixed-corpus replays with separate orchid probe and vLLM acceptance."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import urllib.request
from decode_contract import CASES, WEIGHTED_CASE_IDS, structured_edit_response_format, validate_case_content

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mia',ROOT/'scripts/bench-mia-style.py')
client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)
METRIC=re.compile(r'^(vllm:spec_decode_(?:num_draft_tokens|num_accepted_tokens|num_drafts)_total)(?:\{[^}]*\})?\s+([^ ]+)')


def counter_totals(text):
    result={}
    for line in text.splitlines():
        match=METRIC.match(line)
        if match:
            key,value=match.groups();result[key]=result.get(key,0)+float(value)
    return result


def acceptance(before,after):
    delta={k:after.get(k,0)-before.get(k,0) for k in set(before)|set(after)}
    if any(v<0 for v in delta.values()):
        raise ValueError('Speculation counters reset during request')
    proposed=delta.get('vllm:spec_decode_num_draft_tokens_total',0)
    accepted=delta.get('vllm:spec_decode_num_accepted_tokens_total',0)
    if accepted>proposed:
        raise ValueError('Accepted tokens exceed proposed tokens')
    return {'deltas':delta,'draft_tokens':proposed,'accepted_tokens':accepted,
            'ratio':accepted/proposed if proposed else None}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    parser.add_argument('--launch-receipt',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--runs',type=int,default=5)
    args=parser.parse_args()
    if args.runs<1:parser.error('Runs must be positive')
    args.out.mkdir(parents=True,exist_ok=False)
    base=args.base_url.rstrip('/')
    with urllib.request.urlopen(base+'/v1/models',timeout=30) as response:models=json.load(response)
    if len(models['data'])!=1:raise ValueError('Expected one served model')
    model=models['data'][0]['id']
    receipt={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'launch':json.loads(args.launch_receipt.read_text()),
             'template':json.loads((ROOT/'data/chat-template-receipt.json').read_text()),
             'contract_sha256':hashlib.sha256((ROOT/'scripts/decode_contract.py').read_bytes()).hexdigest(),
             'client_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'runs':args.runs,'samples':[]}
    def save(name,data):(args.out/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    def snapshot(name):
        with urllib.request.urlopen(base+'/metrics',timeout=30) as response:raw=response.read().decode()
        (args.out/(name+'.prom')).write_text(raw)
        return counter_totals(raw)
    save('receipt',receipt)
    warmup=client.stream(base,model,'Say hello in one sentence.',32)
    save('warmup',warmup)
    if 'error' in warmup:raise RuntimeError(warmup['error'])
    for repeat in range(args.runs):
        for case_id in WEIGHTED_CASE_IDS:
            case=CASES[case_id];name=f'r{repeat}-{case_id}'
            before=snapshot(name+'-before')
            result=client.stream(base,model,case.prompt,case.max_tokens,
                response_format=structured_edit_response_format() if case.json_schema else None)
            after=snapshot(name+'-after')
            result['quality']=validate_case_content(case_id,result.get('text',''))
            result['acceptance']=acceptance(before,after)
            save(name,result)
            summary={'case':case_id,'repeat':repeat,'weight':case.weight,
                     'completion_tokens':result.get('usage',{}).get('completion_tokens'),
                     'decode_tokens':result.get('decode_tokens'),
                     'decode_seconds':result['last']-result['first'] if 'last' in result else None,
                     'decode_tps':result.get('decode_tps'),'acceptance':result['acceptance'],
                     'quality':result['quality'],'error':result.get('error')}
            receipt['samples'].append(summary);save('receipt',receipt)
            print(json.dumps(summary),flush=True)
    # Timing includes responses that fail output checks. Transport failures make
    # the performance block incomplete; never compute a survivor-only headline.
    samples=receipt['samples']
    if any(s['error'] for s in samples):
        receipt['status']='failed';save('receipt',receipt);raise SystemExit(1)
    receipt['weighted_decode_tps']=sum(s['weight']*s['decode_tokens'] for s in samples)/sum(s['weight']*s['decode_seconds'] for s in samples)
    receipt['output_checks_passed']=sum(s['quality']['quality_contract_passed'] for s in samples)
    receipt['output_checks_total']=len(samples)
    orchid=[]
    for repeat in range(args.runs):
        prompt='Repeat only the single word "orchid" exactly 100 times, separated by spaces. Do not add any other text.'
        result=client.stream(base,model,prompt,1500)
        save(f'orchid-r{repeat}',result)
        orchid.append({k:result.get(k) for k in ('decode_tps','decode_tokens','error')})
    receipt['orchid_speed_only']=orchid
    receipt['status']='passed' if not any(s.get('error') for s in orchid) else 'failed'
    save('receipt',receipt)
    if receipt['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()
