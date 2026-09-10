#!/usr/bin/env python3
"""Fifteen exact-key retrieval cells with locally checked chat token counts."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import urllib.request
import uuid
from needle_contract import build_prompt, filler_text, prompt_token_ids, Tokenizer

ROOT = Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mia', ROOT/'scripts/bench-mia-style.py')
client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    parser.add_argument('--tokenizer',type=Path,required=True)
    parser.add_argument('--launch-receipt',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--plan-only',action='store_true')
    parser.add_argument('--timeout',type=float,default=600)
    args=parser.parse_args()
    if args.timeout<=0:parser.error('Timeout must be positive')
    args.out.mkdir(parents=True,exist_ok=False)
    tokenizer=Tokenizer.from_file(str(args.tokenizer))
    bank=tokenizer.encode(filler_text(),add_special_tokens=False).ids
    template=json.loads((ROOT/'data/chat-template-receipt.json').read_text())
    if hashlib.sha256((ROOT/'data/serving_chat_template.jinja').read_bytes()).hexdigest()!=template['serving_sha256']:
        raise ValueError('Serving template identity mismatch')
    url=args.base_url.rstrip('/');models=None;model=None
    if not args.plan_only:
        with urllib.request.urlopen(url+'/v1/models',timeout=30) as response:models=json.load(response)
        if len(models['data'])!=1:raise ValueError('Expected one model')
        model=models['data'][0]['id']
    receipt={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_id':uuid.uuid4().hex,
        'launch':json.loads(args.launch_receipt.read_text()),'template':template,'models':models,
        'tokenizer_sha256':hashlib.sha256(args.tokenizer.read_bytes()).hexdigest(),
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (Path(__file__),ROOT/'scripts/needle_contract.py',ROOT/'scripts/bench-mia-style.py')},
        'plan_only':args.plan_only,'timeout_seconds':args.timeout,'cells':[]}
    def save(name,data):(args.out/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    def snapshot(name):
        with urllib.request.urlopen(url+'/metrics',timeout=30) as response:
            (args.out/(name+'.prom')).write_bytes(response.read())
    save('receipt',receipt)
    for context in (8192,32768,131072,262144,393216):
        for depth in (.1,.5,.9):
            name=f'context-{context}-depth-{int(depth*100)}'
            messages,contract=build_prompt(tokenizer=tokenizer,filler_ids=bank,
                target_context=context,depth=depth,session_id=receipt['run_id'])
            ids=prompt_token_ids(tokenizer,messages)
            contract['prompt_ids_sha256']=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()
            body={'model':model,'messages':messages,'max_tokens':32,'temperature':0,'top_p':1,
                'stream':True,'stream_options':{'include_usage':True},
                'chat_template_kwargs':{'enable_thinking':False}}
            save(name+'-request',{'contract':contract,'request':body})
            if args.plan_only:
                summary={'status':'planned','contract':contract}
            else:
                snapshot(name+'-before')
                result=client.stream_request(url,body,'/v1/chat/completions',False,args.timeout)
                snapshot(name+'-after');save(name+'-response',result)
                elapsed=result['end']-result['start']
                exact=result.get('text','').strip()==contract['needle_key']
                tokens_match=result.get('usage',{}).get('prompt_tokens')==len(ids)
                valid='error' not in result and tokens_match and elapsed<=args.timeout
                summary={'status':'passed' if valid and exact else 'failed','contract':contract,
                    'exact_key':exact,'token_count_matches':tokens_match,'elapsed_seconds':elapsed,
                    'error':result.get('error'),'usage':result.get('usage'),
                    'ttft_seconds':result.get('ttft_seconds'),'within_time_limit':elapsed<=args.timeout}
            receipt['cells'].append(dict(cell=name,**summary));save('receipt',receipt)
            print(json.dumps({'cell':name,'status':summary['status'],'prompt_tokens':len(ids)}),flush=True)
    receipt['status']='planned' if args.plan_only else ('passed' if all(c['status']=='passed' for c in receipt['cells']) else 'failed')
    save('receipt',receipt)
    if receipt['status']=='failed':raise SystemExit(1)


if __name__=='__main__':main()
