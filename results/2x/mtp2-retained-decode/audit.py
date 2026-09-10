"""Retained decode timings with observed MTP cache accounting; preserve strict failures."""
import json,math,statistics
from pathlib import Path

def audit(root):
    receipt=json.loads((root/'receipt.json').read_text())
    assert receipt.get('status') in ('passed','failed'), 'Run is not complete'
    assert len(receipt['samples'])==30 and len({r['cell'] for r in receipt['samples']})==30
    block=receipt['cache_block_size'];assert block==6144
    samples=[]
    for cell in receipt['samples']:
        raw=json.loads((root/(cell['cell']+'.json')).read_text())
        base=cell['base']
        row={k:cell[k] for k in ('cell','base','workload','repeat')}
        row['original_status']=cell['status']
        finishes=[c['finish_reason'] for e in raw.get('events',[]) for c in e['data'].get('choices',[]) if c.get('finish_reason')]
        row['finish_reasons']=finishes
        row['hit_length_cap']='length' in finishes
        if 'output_check' in cell:row['output_check']=cell['output_check']
        if 'error' in raw:
            row.update(status='request_failed',error=raw['error'],http_status=raw.get('http_status'),
                       http_error_body=raw.get('http_error_body'))
        else:
            if base:
                assert 'error' not in json.loads((root/f'base-{base}-prime.json').read_text())
            usage=raw['usage'];cached=usage['prompt_tokens_details']['cached_tokens']
            assert 0<=cached<=base
            assert usage['prompt_tokens']==len(raw['request']['prompt'])
            assert not raw['reasoning']
            elapsed=raw['last']-raw['first'];tokens=usage['completion_tokens']-1
            assert elapsed>0 and tokens>0 and math.isclose(tokens/elapsed,raw['decode_tps'])
            expected=max(0,base//block*block-block) if base else 0
            row.update(status='measured',cached_tokens=cached,policy_expected_cached_tokens=expected,
                policy_matches=cached==expected,recomputed_base_tokens=base-cached,
                prompt_tokens=usage['prompt_tokens'],completion_tokens=usage['completion_tokens'],
                decode_tps=raw['decode_tps'],ttft_seconds=raw['ttft_seconds'])
        samples.append(row)
    medians=[]
    workloads=sorted({s['workload'] for s in samples})
    assert len(workloads)==3
    for base in receipt['bases']:
        for workload in workloads:
            rows=[r for r in samples if r['base']==base and r['workload']==workload]
            assert len(rows)==2
            valid=all(r['status']=='measured' and r['policy_matches'] for r in rows)
            medians.append({'base':base,'workload':workload,'policy_matches_all':valid,
                'decode_tps':statistics.median(r['decode_tps'] for r in rows) if valid else None})
    report={'original_status':receipt['status'],'cache_block_size':block,'samples':samples,'medians':medians,
        'interpretation':'Observed MTP cache policy; timing validity does not establish output quality or change strict receipt status.'}
    (root/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    import sys
    report=audit(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent)
    print(json.dumps(report['medians'],indent=2))
