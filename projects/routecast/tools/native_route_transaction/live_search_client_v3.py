#!/usr/bin/python3
"""Serial file request publication with explicit step identity."""
import os,sys,json,time
from pathlib import Path
box=Path(os.environ['ROUTECAST_SEARCH_MAILBOX']);index=os.environ['ROUTECAST_REUSE_STEP'];assert index.isdigit();config={k:os.environ[k] for k in ('ROUTECAST_SEARCH_ENDPOINT','ROUTECAST_SEARCH_REPORT','ROUTECAST_TX_CANDIDATE','ROUTECAST_TX_REQUEST')};config['place']=os.path.abspath('design.place')
request=box/f'request_{index}.json';assert not request.exists();temp=box/f'request_{index}.tmp'
with temp.open('x') as f:f.write(json.dumps(dict(stem=sys.argv[1],config=config))+'\n')
os.link(temp,request);temp.unlink();response=box/f'response_{index}.json';deadline=time.monotonic()+110
while not response.exists():
 if time.monotonic()>deadline:raise TimeoutError('producer response timeout')
 time.sleep(.02)
result=json.loads(response.read_text());assert result['index']==int(index)
if not result['ok']:raise RuntimeError(result['error'])
