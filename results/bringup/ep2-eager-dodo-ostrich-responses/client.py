import datetime, json, time, urllib.request
from pathlib import Path
out=Path('/home/tj/Developer/glmflash-mxfp8-spark/results/bringup/ep2-eager-dodo-ostrich-responses')
url='http://10.55.0.2:8000'
end=time.monotonic()+3600
while True:
    try:
        with urllib.request.urlopen(url+'/health',timeout=3) as response:
            if response.status==200: break
    except OSError: pass
    if time.monotonic()>end: raise TimeoutError('Server never became ready; no requests sent')
    time.sleep(5)
out.mkdir(parents=True,exist_ok=False)
launch=Path('/home/tj/Developer/glmflash-mxfp8-spark/.work/launches/20260910T142543/launch.json')
(out/'launch.json').write_bytes(launch.read_bytes())
with urllib.request.urlopen(url+'/v1/models') as r: models=json.load(r)
(out/'models.json').write_text(json.dumps(models,indent=2)+'\n')
model=models['data'][0]['id']
cases=[('thinking-default',{'messages':[{'role':'user','content':'What is 17 multiplied by 23? Give the result.'}]}),
       ('thinking-off',{'messages':[{'role':'user','content':'What is 17 multiplied by 23? Reply with only the integer.'}],'chat_template_kwargs':{'enable_thinking':False}}),
       ('tool-default',{'messages':[{'role':'user','content':'Get the current weather in Taipei using the provided tool.'}], 'tools':[{'type':'function','function':{'name':'get_weather','description':'Fetch current weather for a city','parameters':{'type':'object','properties':{'city':{'type':'string'}},'required':['city']}}}], 'tool_choice':'auto'})]
for name,extra in cases:
    body={'model':model,'temperature':0,'max_tokens':512,**extra}
    result={'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'request':body}
    start=time.monotonic()
    try:
        req=urllib.request.Request(url+'/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=900) as r: result['response']=json.load(r)
    except Exception as e: result['error']=repr(e)
    result['elapsed_seconds']=time.monotonic()-start
    (out/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'case':name,**result}),flush=True)
