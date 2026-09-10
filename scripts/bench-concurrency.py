#!/usr/bin/env python3
"""GLMRT code/exact-count fixtures at C1/C2/C4 with synchronized starts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import threading
import urllib.request
import uuid
from decode_contract import validate_case_content

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mia',ROOT/'scripts/bench-mia-style.py')
client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)
FIXTURES={
    'code':{'prompt':'Write a Python function merge_intervals(intervals) that merges overlapping integer intervals. Include type hints, a short docstring, and three assert-based examples. Return only one Python code block.','max_tokens':320},
    'exact-50':{'prompt':'Background words below are irrelevant. '+'beta '*946+'\nCount from 1 to 50, one number per line. Do not add any other text.','max_tokens':99},
}


def summarize(results):
    summary=client.wave_summary(results)
    if summary['status']!='passed':return summary
    cached=[r['usage'].get('prompt_tokens_details',{}).get('cached_tokens') for r in results]
    if any(c!=0 for c in cached):
        return {'status':'failed','error':f'Cold-prefix cache contract failed: {cached}'}
    summary['completion_tokens']=sum(r['usage']['completion_tokens'] for r in results)
    summary['request_makespan_seconds']=max(r['end'] for r in results)-min(r['start'] for r in results)
    summary['end_to_end_aggregate_tps']=summary['completion_tokens']/summary['request_makespan_seconds']
    summary['output_checks_passed']=sum(r['output_check']['quality_contract_passed'] for r in results)
    summary['output_checks_total']=len(results)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    parser.add_argument('--launch-receipt',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--runs',type=int,default=5)
    parser.add_argument('--warmups',type=int,default=2)
    args=parser.parse_args()
    if args.runs<1 or args.warmups<0:parser.error('Positive runs and nonnegative warmups required')
    args.out.mkdir(parents=True,exist_ok=False)
    url=args.base_url.rstrip('/')
    with urllib.request.urlopen(url+'/v1/models',timeout=30) as response:models=json.load(response)
    if len(models['data'])!=1:raise ValueError('Expected one target')
    model=models['data'][0]['id'];run_id=uuid.uuid4().hex
    receipt={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_id':run_id,
        'launch':json.loads(args.launch_receipt.read_text()),'models':models,'runs':args.runs,'warmups':args.warmups,
        'template':json.loads((ROOT/'data/chat-template-receipt.json').read_text()),'fixtures':FIXTURES,
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (Path(__file__),ROOT/'scripts/bench-mia-style.py',ROOT/'scripts/decode_contract.py')},'waves':[]}
    def save(name,value):(args.out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    def snapshot(name):
        with urllib.request.urlopen(url+'/metrics',timeout=30) as response:
            (args.out/(name+'.prom')).write_bytes(response.read())
    save('receipt',receipt)
    for fixture,contract in FIXTURES.items():
        for concurrency in (1,2,4):
            for repeat in range(-args.warmups,args.runs):
                label=f'{fixture}-c{concurrency}-'+(f'warmup{-repeat}' if repeat<0 else f'r{repeat}')
                barrier=threading.Barrier(concurrency)
                def execute(lane):
                    # The unique prefix occurs before a cache block can be shared.
                    prompt=f'Nonce {run_id}-{fixture}-{concurrency}-{repeat}-{lane}.\n'+contract['prompt']
                    barrier.wait()
                    result=client.stream(url,model,prompt,contract['max_tokens'])
                    text=result.get('text','')
                    result['output_check']=(validate_case_content('code',text) if fixture=='code' else
                        {'quality_contract_passed':text.strip()=='\n'.join(str(n) for n in range(1,51))})
                    return result
                snapshot(label+'-before')
                with ThreadPoolExecutor(max_workers=concurrency) as executor:results=list(executor.map(execute,range(concurrency)))
                snapshot(label+'-after')
                summary=summarize(results);save(label,{'results':results,'summary':summary})
                receipt['waves'].append(dict(fixture=fixture,concurrency=concurrency,repeat=repeat,warmup=repeat<0,**summary))
                save('receipt',receipt);print(json.dumps(receipt['waves'][-1]),flush=True)
    receipt['medians']=[]
    for fixture in FIXTURES:
        baseline=None
        for concurrency in (1,2,4):
            cells=[r for r in receipt['waves'] if r['fixture']==fixture and r['concurrency']==concurrency and not r['warmup']]
            valid=len(cells)==args.runs and all(r['status']=='passed' for r in cells)
            aggregate=statistics.median(r['aggregate_tps'] for r in cells) if valid else None
            if concurrency==1:baseline=aggregate
            receipt['medians'].append({'fixture':fixture,'concurrency':concurrency,'status':'passed' if valid else 'failed',
                'aggregate_decode_tps':aggregate,'scaling_vs_c1':aggregate/baseline if aggregate and baseline else None,
                'end_to_end_aggregate_tps':statistics.median(r['end_to_end_aggregate_tps'] for r in cells) if valid else None})
    receipt['status']='passed' if all(r['status']=='passed' for r in receipt['waves']) else 'failed'
    save('receipt',receipt)
    if receipt['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()
