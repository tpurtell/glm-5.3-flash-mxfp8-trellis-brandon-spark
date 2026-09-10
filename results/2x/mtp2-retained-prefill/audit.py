"""Report observed MTP cache reuse without changing the original strict receipt."""
import json,math,re,statistics
from pathlib import Path

METRIC=re.compile(r'^(vllm:request_prefill_time_seconds_(?:sum|count))(?:\{[^}]*\})?\s+([^ ]+)')
def totals(path):
    values={}
    for line in path.read_text().splitlines():
        match=METRIC.match(line)
        if match:
            key,value=match.groups();values[key]=values.get(key,0)+float(value)
    assert len(values)==2, f'Missing histogram: {path}'
    return values

def audit(root):
    receipt=json.loads((root/'receipt.json').read_text())
    assert receipt.get('status') in ('passed','failed'), 'Run is not complete'
    expected={f'base-{b}-suffix-{s}-r{r}' for b in (0,32768,65536,131072,262144)
              for s in (1024,2048,4096,8192,16384,32768) for r in range(2)}
    assert len(receipt['samples'])==60 and {s['cell'] for s in receipt['samples']}==expected
    block=receipt['cache_block_size'];assert block==6144
    samples=[]
    for cell in receipt['samples']:
        name=cell['cell'];base=cell['base'];suffix=cell['suffix']
        raw=json.loads((root/(name+'.json')).read_text())
        row={'cell':name,'base':base,'suffix':suffix,'original_status':cell['status']}
        if 'error' in raw:
            row.update(status='request_failed',error=raw['error'],http_status=raw.get('http_status'),
                       http_error_body=raw.get('http_error_body'))
        else:
            if base:
                prime=json.loads((root/f'base-{base}-prime.json').read_text())
                assert 'error' not in prime
            before=totals(root/(name+'-before.prom'));after=totals(root/(name+'-after.prom'))
            assert after['vllm:request_prefill_time_seconds_count']-before['vllm:request_prefill_time_seconds_count']==1
            seconds=after['vllm:request_prefill_time_seconds_sum']-before['vllm:request_prefill_time_seconds_sum']
            assert math.isfinite(seconds) and seconds>0
            usage=raw['usage'];assert usage['prompt_tokens']==base+suffix
            cached=usage['prompt_tokens_details']['cached_tokens']
            assert 0<=cached<=base and raw['ttft_seconds']>0
            aligned=base//block*block
            policy_expected=max(0,aligned-block) if base else 0
            row.update(status='measured',cached_tokens=cached,aligned_base_tokens=aligned,
                policy_expected_cached_tokens=policy_expected,policy_matches=cached==policy_expected,
                recomputed_base_tokens=base-cached,computed_tokens=base+suffix-cached,
                server_prefill_seconds=seconds,new_tokens_per_second=suffix/seconds,
                computed_tokens_per_second=(base+suffix-cached)/seconds,
                client_ttft_seconds=raw['ttft_seconds'])
        samples.append(row)
    medians=[]
    for base in receipt['bases']:
        for suffix in receipt['suffixes']:
            cells=[s for s in samples if s['base']==base and s['suffix']==suffix]
            valid=len(cells)==2 and all(s['status']=='measured' and s['policy_matches'] for s in cells)
            medians.append({'base':base,'suffix':suffix,'policy_matches_all':valid,
                'new_tokens_per_second':statistics.median(s['new_tokens_per_second'] for s in cells) if valid else None,
                'computed_tokens_per_second':statistics.median(s['computed_tokens_per_second'] for s in cells) if valid else None})
    result={'original_status':receipt['status'],'cache_block_size':block,
        'interpretation':'Observed timing and one-block EAGLE/MTP cache-drop policy; original strict contract is unchanged.',
        'source_evidence':'cache-policy-source.json','samples':samples,'medians':medians}
    (root/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    import sys
    report=audit(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent)
    print(json.dumps(report['medians'],indent=2))
