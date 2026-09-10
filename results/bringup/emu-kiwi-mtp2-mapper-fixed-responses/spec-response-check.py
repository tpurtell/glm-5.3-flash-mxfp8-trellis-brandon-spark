import importlib.util, json, subprocess, sys, time, urllib.request
from pathlib import Path
root=Path('/home/tj/Developer/glmflash-mxfp8-spark')
name,launch,url=sys.argv[1:]
out=root/'results/bringup'/name
receipt=root/'.work/launches'/launch/'launch.json'
end=time.monotonic()+3600
while True:
    if receipt.exists() and json.loads(receipt.read_text()).get('error'):
        raise RuntimeError('Launch failed: '+receipt.read_text())
    try:
        with urllib.request.urlopen(url+'/health',timeout=3) as r:
            if r.status==200: break
    except OSError: pass
    if time.monotonic()>end: raise TimeoutError('Not ready; no requests sent')
    time.sleep(5)
sys.path.insert(0,str(root/'scripts'))
spec=importlib.util.spec_from_file_location('weighted',root/'scripts/bench-weighted-decode.py')
weighted=importlib.util.module_from_spec(spec);spec.loader.exec_module(weighted)
def metrics():
    with urllib.request.urlopen(url+'/metrics',timeout=10) as r:return r.read().decode()
before=metrics()
source=Path('/tmp/glm-trellis-work/live-response-check.py').read_text()
source=source.replace('tp2-eager-responses',name).replace('20260910T135951',launch).replace('http://127.0.0.1:8000',url)
exec(compile(source,'live-response-check.py','exec'),{'__name__':'__main__'})
(out/'metrics-before.prom').write_text(before)
end=time.monotonic()+30
while True:
    after=metrics()
    delta=weighted.acceptance(weighted.counter_totals(before),weighted.counter_totals(after))
    if delta['draft_tokens']>0 or time.monotonic()>end:break
    time.sleep(1)
(out/'metrics-after.prom').write_text(after)
(out/'speculation.json').write_text(json.dumps(delta,indent=2)+'\n')
if delta['draft_tokens']<=0:raise RuntimeError('No observed speculative proposals')
print('Observed speculation:',json.dumps(delta),flush=True)
