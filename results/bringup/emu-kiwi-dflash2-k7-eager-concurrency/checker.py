import concurrent.futures, importlib.util, json, sys, time, urllib.request
from pathlib import Path
root=Path('/home/tj/Developer/glmflash-mxfp8-spark')
launch=root/'.work/launches/20260910T160310/launch.json'
url='http://10.55.0.3:8000'
out=root/'results/bringup/emu-kiwi-dflash2-k7-eager-concurrency'
end=time.monotonic()+3600
while True:
 d=json.loads(launch.read_text())
 if d.get('error'):raise RuntimeError(d['error'])
 try:
  with urllib.request.urlopen(url+'/health',timeout=3) as r:
   if r.status==200:break
 except OSError:pass
 if time.monotonic()>end:raise TimeoutError('No healthy service; no requests sent')
 time.sleep(5)
spec=importlib.util.spec_from_file_location('mia',root/'scripts/bench-mia-style.py');mia=importlib.util.module_from_spec(spec);spec.loader.exec_module(mia)
with urllib.request.urlopen(url+'/v1/models') as r:model=json.load(r)['data'][0]['id']
out.mkdir(parents=True,exist_ok=False)
(out/'launch.json').write_bytes(launch.read_bytes())
(out/'checker.py').write_bytes(Path(__file__).read_bytes())
prompts=json.loads((root/'data/mia-prompts.json').read_text())
expected={'structured':' '.join(map(str,range(1,201))), 'code':' '.join(('\n\n'.join(f'def clamp_{i:02d}(x, lo=0, hi=1):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x' for i in range(50))).split())}
summary={'purpose':'Eager DFlash2 K7 concurrency output audit; prefix match allows cap truncation and normalizes whitespace','waves':[],'failures':[]}
for kind in ('structured','code'):
 warm=mia.stream(url,model,prompts[kind],32);(out/(kind+'-warmup.json')).write_text(json.dumps(warm,indent=2)+'\n')
 if 'error' in warm:raise RuntimeError(warm['error'])
 for c in (1,2,4):
  for repeat in range(5):
   name=f'{kind}-c{c}-r{repeat}'
   ps=[prompts[kind]+(f' (stream {i+1}/{c})' if c>1 else '') for i in range(c)]
   with concurrent.futures.ThreadPoolExecutor(max_workers=c) as pool:rs=list(pool.map(lambda p:mia.stream(url,model,p,400),ps))
   wave=mia.wave_summary(rs)
   for i,r in enumerate(rs):
    r['prefix_contract_passed']='error' not in r and expected[kind].startswith(' '.join(r.get('text','').split()))
    if not r['prefix_contract_passed']:summary['failures'].append({'wave':name,'stream_index':i,'error':r.get('error'),'completion_tokens':r.get('usage',{}).get('completion_tokens')})
   (out/(name+'.json')).write_text(json.dumps({'results':rs,'summary':wave},indent=2)+'\n')
   row={'wave':name,**wave,'output_passes':sum(r['prefix_contract_passed'] for r in rs),'responses':len(rs)}
   summary['waves'].append(row)
   (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
   print(json.dumps(row),flush=True)
summary['completed']=True;summary['quality_passed']=not summary['failures']
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('Completed;',len(summary['failures']),'output failures',flush=True)
