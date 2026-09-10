#!/usr/bin/env python3
"""Measure compiler-cache-cold and warm startup in an isolated cache directory."""
import argparse
import datetime
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import uuid
import cluster

ROOT=Path(__file__).resolve().parents[1]


def cache_inventory(config,nodes):
    code="""import json,sys
from pathlib import Path
root=Path(sys.argv[1])
files=[p for p in root.rglob('*') if p.is_file()] if root.exists() else []
print(json.dumps({'path':str(root),'files':len(files),'bytes':sum(p.stat().st_size for p in files),
 'b12x_files':sum('b12x' in p.relative_to(root).parts for p in files)}))
"""
    return [dict(host=node['host'],**json.loads(cluster.execute(node['host'],
        ['python3','-c',code,str(Path(config['cache_root'])/f'{nodes}x-r{rank}')]).stdout))
        for rank,node in enumerate(config['nodes'][:nodes])]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'cluster.example.json')
    parser.add_argument('--nodes',type=int,choices=[2],default=2)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--plan-only',action='store_true')
    parser.add_argument('launch_args',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    extra=args.launch_args[1:] if args.launch_args[:1]==['--'] else args.launch_args
    if any(x.split('=')[0] in ('--config','--nodes') for x in extra):
        parser.error('Set topology and config through the wrapper options')
    args.out.mkdir(parents=True,exist_ok=False)
    config=json.loads(args.config.read_text())
    config['cache_root']=str(Path(config['cache_root'])/('startup-'+uuid.uuid4().hex))
    config_path=(args.out/'cluster.json').resolve();config_path.write_text(json.dumps(config,indent=2)+'\n')
    command=[sys.executable,str(ROOT/'scripts/cluster.py'),'plan','--config',str(config_path),'--nodes',str(args.nodes),*extra]
    plan=json.loads(subprocess.check_output(command,text=True))
    receipt={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'nodes':args.nodes,'plan':plan,
        'cold_definition':'Fresh empty per-rank persistent compiler-cache directory; OS page cache uncontrolled.',
        'warm_definition':'Restart after cold readiness and a short inference check, preserving the same compiler cache.',
        'timing_definition':'First container launch through successful /health, excluding preflight and checkpoint validation.',
        'plan_only':args.plan_only,'phases':[]}
    def save(): (args.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    save()
    if args.plan_only:
        receipt['status']='planned';save();return
    # Do not stop or replace an existing serving run.
    for item in plan['plan']:
        state=cluster.execute(item['host'],['docker','inspect','--format','{{.State.Running}}',item['name']],check=False)
        if state.returncode==0 and state.stdout.strip()=='true':raise RuntimeError('Stop the current serving run before startup measurement')
        cluster.execute(item['host'],['python3','-c',
            'from pathlib import Path; import sys; p=Path(sys.argv[1]); assert not p.exists(); p.mkdir(parents=True)',config['cache_root']])
    port=8000
    for i,arg in enumerate(extra):
        if arg=='--port':port=int(extra[i+1])
        elif arg.startswith('--port='):port=int(arg.split('=',1)[1])
    url=f"http://{config['nodes'][0]['ip']}:{port}"
    for phase in ('compiler-cache-cold','warm'):
        before=cache_inventory(config,args.nodes)
        if phase=='compiler-cache-cold' and any(r['files'] for r in before):raise RuntimeError('Cold cache is not empty')
        if phase=='warm' and any(not r['b12x_files'] for r in before):raise RuntimeError('No persisted P8 compiler cache on a rank; warm label unsupported')
        start_command=command.copy();start_command[2]='start'
        started=time.monotonic()
        completed=subprocess.run(start_command,text=True,capture_output=True)
        wall=time.monotonic()-started
        (args.out/(phase+'.stdout.log')).write_text(completed.stdout)
        (args.out/(phase+'.stderr.log')).write_text(completed.stderr)
        if completed.returncode:raise RuntimeError('Startup failed; containers retained for inspection')
        launch=json.loads(Path(completed.stdout.strip().splitlines()[-1]).read_text())
        phase_record={'phase':phase,'launch':launch,'ready_seconds':launch['ready_seconds'],
                      'client_command_seconds_including_preflight':wall,'cache_before':before}
        receipt['phases'].append(phase_record);save()
        body={'model':'glm53-trellismx','messages':[{'role':'user','content':'Reply only OK.'}],
              'max_tokens':8,'temperature':0,'chat_template_kwargs':{'enable_thinking':False}}
        request=urllib.request.Request(url+'/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=300) as response:smoke=json.load(response)
        (args.out/(phase+'-inference-check.json')).write_text(json.dumps(smoke,indent=2)+'\n')
        if not smoke.get('choices') or not smoke['choices'][0]['message'].get('content'):
            raise RuntimeError('Ready server did not produce content; retained for inspection')
        phase_record['cache_after']=cache_inventory(config,args.nodes);save()
        for item in launch['plan']:
            logs=cluster.execute(item['host'],['docker','logs',item['container_id']],check=False)
            (args.out/f"{phase}-{item['host']}.log").write_text(logs.stdout+logs.stderr)
            # Stop only the exact containers created by this measured launch.
            cluster.execute(item['host'],['docker','stop',item['container_id']])
        print(json.dumps({'phase':phase,'ready_seconds':phase_record['ready_seconds']}),flush=True)
    receipt['status']='complete';save()


if __name__=='__main__':main()
