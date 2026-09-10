import importlib.util,json,time,urllib.request
from pathlib import Path
root=Path('/home/tj/Developer/glmflash-mxfp8-spark')
p=root/'results/bringup/emu-kiwi-dflash2-k7-eager-concurrency'
launch=root/'.work/launches/20260910T160310/launch.json'
end=time.monotonic()+5400
while not (p/'summary.json').exists() or not json.loads((p/'summary.json').read_text()).get('completed'):
 if json.loads(launch.read_text()).get('error'):raise RuntimeError('Launch failed; no suffix probes sent')
 if time.monotonic()>end:raise TimeoutError('Concurrency test not complete; no serial probes sent')
 time.sleep(5)
out=root/'results/bringup/emu-kiwi-dflash2-k7-eager-serial-suffix';out.mkdir(parents=True,exist_ok=False)
(out/'checker.py').write_bytes(Path(__file__).read_bytes());(out/'launch.json').write_bytes(launch.read_bytes())
spec=importlib.util.spec_from_file_location('mia',root/'scripts/bench-mia-style.py');mia=importlib.util.module_from_spec(spec);spec.loader.exec_module(mia)
url='http://10.55.0.3:8000'
with urllib.request.urlopen(url+'/v1/models') as r:model=json.load(r)['data'][0]['id']
prompts=json.loads((root/'data/mia-prompts.json').read_text())
expected={'structured':' '.join(map(str,range(1,201))), 'code':' '.join(('\n\n'.join(f'def clamp_{i:02d}(x, lo=0, hi=1):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x' for i in range(50))).split())}
summary={'purpose':'Serial requests with the exact suffixes of failing concurrent streams','results':[]}
for kind,i,c in [('structured',1,2),('code',2,4),('code',1,4)]:
 for repeat in range(5):
  name=f'{kind}-suffix{i}of{c}-r{repeat}';r=mia.stream(url,model,prompts[kind]+f' (stream {i}/{c})',400)
  r['prefix_contract_passed']='error' not in r and expected[kind].startswith(' '.join(r.get('text','').split()))
  (out/(name+'.json')).write_text(json.dumps(r,indent=2)+'\n')
  row={'case':name,'prefix_contract_passed':r['prefix_contract_passed'],'error':r.get('error')};summary['results'].append(row);print(json.dumps(row),flush=True)
  (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
summary['completed']=True;(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
