#!/usr/bin/env python3
"""Pinned 88-scenario hard-mode tool evaluation, three distinct serial seeds."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def summarize(result, plan):
    scores=result['scores'];rows=scores['scenario_results']
    categories={s['id']:s['category'] for s in plan['scenarios']}
    ids=[r['scenario_id'] for r in rows]
    if len(ids)!=88 or len(set(ids))!=88 or set(ids)!=set(categories):
        raise ValueError('Missing, duplicate or unexpected scenarios')
    if scores.get('excluded_scenarios') or scores['max_points']!=176:
        raise ValueError('Infrastructure exclusions make this qualification block incomplete')
    if any(type(r['points']) is not int or r['points'] not in (0,1,2) for r in rows):
        raise ValueError('Unexpected per-scenario points')
    total=sum(r['points'] for r in rows)
    if total!=scores['total_points']:raise ValueError('Point totals disagree')
    hard=sum(r['points'] for r in rows if categories[r['scenario_id']]=='P')
    return {'status':'complete','original_points':total-hard,'original_max':138,
            'hard_points':hard,'hard_max':38,'total_points':total,'max_points':176,
            'displayed_score':scores['final_score'],
            'failures':[r for r in rows if r['points']<2]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    parser.add_argument('--model',default='glm53-trellismx')
    parser.add_argument('--launch-receipt',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--tool',default=shutil.which('tool-eval-bench'))
    parser.add_argument('--tool-python',help='Interpreter owning the installed evaluator; defaults to its absolute shebang')
    parser.add_argument('--seeds',type=int,nargs=3,default=[2026091001,2026091002,2026091003])
    parser.add_argument('--plan-only',action='store_true')
    args=parser.parse_args()
    if not args.tool:parser.error('Pinned tool-eval-bench executable is required')
    if len(set(args.seeds))!=3:parser.error('Three distinct seeds required')
    pin=json.loads((ROOT/'sources.lock.json').read_text())['tool_eval']
    version=subprocess.check_output([args.tool,'--version'],text=True).strip()
    if version!='tool-eval-bench '+pin['version']:raise ValueError(f'Wrong evaluator version: {version}')
    python=args.tool_python or Path(args.tool).read_text().splitlines()[0].removeprefix('#!')
    if not Path(python).is_file():raise ValueError('Supply --tool-python for a non-absolute interpreter shebang')
    metadata=json.loads(subprocess.check_output([python,'-c',
        "import importlib.metadata as m; print(m.distribution('tool-eval-bench').read_text('direct_url.json'))"],text=True))
    if metadata.get('vcs_info',{}).get('commit_id')!=pin['revision'] or metadata.get('url')!=pin['repository']:
        raise ValueError('Evaluator installation does not identify the pinned Git source')
    args.out.mkdir(parents=True,exist_ok=False)
    common=[args.tool,'--base-url',args.base_url.rstrip('/')+'/v1/','--model',args.model,
        '--backend','vllm','--format','openai','--parallel','1','--hardmode','--temperature','0',
        '--reference-date',pin['reference_date'],'--backend-kwargs',
        json.dumps({'chat_template_kwargs':{'enable_thinking':True}}),'--json']
    plan=json.loads(subprocess.check_output(common+['--seed',str(args.seeds[0]),'--dry-run'],text=True))
    if plan['total_scenarios']!=88 or plan['categories']['P']['count']!=19:
        raise ValueError('Expected 69 original plus 19 hard scenarios')
    def save(name,value):(args.out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    save('scenario-plan',plan)
    receipt={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'evaluator':pin,
        'installation':metadata,'version':version,'launch':json.loads(args.launch_receipt.read_text()),
        'template':json.loads((ROOT/'data/chat-template-receipt.json').read_text()),
        'client_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'runs':[],
        'plan_only':args.plan_only}
    for seed in args.seeds:
        path=(args.out/f'seed-{seed}.json').resolve()
        command=common+['--seed',str(seed),'--json-file',str(path),'--output-dir',str((args.out/f'seed-{seed}-artifacts').resolve())]
        record={'seed':seed,'command':command,'status':'planned'}
        receipt['runs'].append(record);save('receipt',receipt)
        if args.plan_only:continue
        with (args.out/f'seed-{seed}.stdout.log').open('w') as stdout, (args.out/f'seed-{seed}.stderr.log').open('w') as stderr:
            completed=subprocess.run(command,stdout=stdout,stderr=stderr)
        record['exit_code']=completed.returncode
        try:
            if completed.returncode:raise ValueError('Evaluator process failed')
            record.update(summarize(json.loads(path.read_text()),plan))
        except Exception as exc:record.update(status='incomplete',error=repr(exc))
        save('receipt',receipt);print(json.dumps({'seed':seed,'status':record['status'],'total_points':record.get('total_points')}),flush=True)
    complete=all(r['status']=='complete' for r in receipt['runs'])
    receipt['status']='planned' if args.plan_only else ('complete' if complete else 'incomplete')
    if complete:receipt['median_total_points']=statistics.median(r['total_points'] for r in receipt['runs'])
    save('receipt',receipt)
    if receipt['status']=='incomplete':raise SystemExit(1)


if __name__=='__main__':main()
