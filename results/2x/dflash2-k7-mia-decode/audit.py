"""Recompute five-wave timing medians and deterministic prefix checks from raw SSE."""
import json, statistics
from pathlib import Path
p=Path(__file__).resolve().parent
receipt=json.loads((p/'receipt.json').read_text())
assert receipt['status']=='passed' and receipt['runs']==5 and len(receipt['cells'])==45
expected={'structured':' '.join(map(str,range(1,201))), 'code':' '.join(('\n\n'.join(f'def clamp_{i:02d}(x, lo=0, hi=1):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x' for i in range(50))).split())}
audit={'timing_medians':{},'responses':0,'errors':[],'short_responses':[],'pattern_failures':[], 'quality_status':'not fully qualified; prose not scored'}
for kind in ('structured','code','prose'):
 for c in (1,2,4):
  cells=[x for x in receipt['cells'] if x['cell'].startswith(f'{kind}-c{c}-')]
  assert len(cells)==5
  audit['timing_medians'][f'{kind}-c{c}']={'aggregate_tps':statistics.median(x['aggregate_tps'] for x in cells),'median_stream_tps':statistics.median(x['median_stream_tps'] for x in cells)}
  for cell in cells:
   for i,r in enumerate(json.loads((p/(cell['cell']+'.json')).read_text())['results']):
    audit['responses']+=1; ident={'cell':cell['cell'],'stream_index':i}
    if 'error' in r:audit['errors'].append({**ident,'error':r['error']})
    assert not r.get('reasoning')
    if r['usage']['completion_tokens']!=400:audit['short_responses'].append({**ident,'completion_tokens':r['usage']['completion_tokens']})
    if kind in expected:
     t=' '.join(r['text'].split());e=expected[kind]
     if not e.startswith(t):
      j=next((j for j,(a,b) in enumerate(zip(e,t)) if a!=b),min(len(e),len(t)))
      audit['pattern_failures'].append({**ident,'normalized_offset':j,'expected':e[max(0,j-40):j+100],'actual':t[max(0,j-40):j+100]})
assert audit['responses']==105 and not audit['errors']
(p/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
