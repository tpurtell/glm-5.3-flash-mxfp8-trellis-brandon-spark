"""Audit all five cold-prefill replays, including configured context rejections."""
import json, math, statistics
from pathlib import Path

def audit(root):
    receipt=json.loads((root/'receipt.json').read_text())
    assert receipt.get('status') in ('passed','failed'), 'Run is not finished'
    expected={f'prefill-{n}-r{r}' for n in (8192,16384,32768,65536,131072,262144) for r in range(5)}
    assert len(receipt['cells'])==30 and {c['cell'] for c in receipt['cells']}==expected
    references={8192:1492.1,16384:1553.7,32768:1428.2,65536:1587.0,131072:1561.7,262144:1516.8}
    rows=[]
    for n,mia in references.items():
        samples=[]
        for cell in [c for c in receipt['cells'] if c['nominal_tokens']==n]:
            raw=json.loads((root/(cell['cell']+'.json')).read_text())
            if 'error' in raw:
                samples.append({'cell':cell['cell'],'status':'failed','http_status':raw.get('http_status'),
                    'error':raw['error'],'http_error_body':raw.get('http_error_body')})
                continue
            assert cell['status']=='passed'
            assert raw['request']['chat_template_kwargs']['enable_thinking'] is False
            assert not raw['reasoning']
            assert raw['usage']['prompt_tokens_details']['cached_tokens']==0
            assert raw['usage']['completion_tokens']<=8
            rate=raw['usage']['prompt_tokens']/(raw['first']-raw['start'])
            assert math.isclose(rate,cell['prefill_tps'],rel_tol=1e-10)
            samples.append({'cell':cell['cell'],'status':'passed','prompt_tokens':raw['usage']['prompt_tokens'],
                'ttft_seconds':raw['ttft_seconds'],'prefill_tps':rate,'cached_tokens':0})
        valid=all(s['status']=='passed' for s in samples)
        rate=statistics.median(s['prefill_tps'] for s in samples) if valid else None
        rows.append({'nominal_tokens':n,'status':'passed' if valid else 'failed','median_prefill_tps':rate,
            'mia_prefill_tps':mia,'delta_percent':100*(rate/mia-1) if valid else None,'samples':samples})
    result={'definition':'server-reported prompt tokens / client time to first streamed token',
            'replays':5,'rows':rows}
    (root/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    import sys
    print(json.dumps(audit(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent),indent=2))
