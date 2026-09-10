"""Audit saved target-only counting responses without contacting any host."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
expected=' '.join(map(str,range(1,201)))
audit={'scope':'Historical one-wave target-only structured/counting outputs; normalized prefix check permits cap truncation','runs':[]}
for name in ('tp2-eager-none-mia-decode','tp2-graphs-none-mia-decode'):
 p=root/'results/screening'/name
 run={'source':str(p.relative_to(root)),'responses':0,'failures':[]}
 for f in sorted(p.glob('structured-c*.json')):
  for i,r in enumerate(json.loads(f.read_text())['results']):
   run['responses']+=1;t=' '.join(r.get('text','').split())
   if 'error' in r or not expected.startswith(t):
    j=next((j for j,(a,b) in enumerate(zip(expected,t)) if a!=b),min(len(expected),len(t)))
    run['failures'].append({'file':f.name,'stream_index':i,'normalized_offset':j,'actual':t[max(0,j-40):j+100],'error':r.get('error')})
 assert run['responses']==7
 audit['runs'].append(run)
Path(__file__).with_name('audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print([(r['source'],len(r['failures']),r['responses']) for r in audit['runs']])
