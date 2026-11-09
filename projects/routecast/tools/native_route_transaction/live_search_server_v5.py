#!/usr/bin/python3
"""Serial filesystem mailbox pilot; no concurrent/durable service claim."""
import json,sys,traceback,time
from pathlib import Path
from live_search_worker_v5 import produce
box=Path(sys.argv[1]);box.mkdir();(box/'ready').write_text('ready\n');ctx=inventory=None
for index in range(int(sys.argv[2])):
 request=box/f'request_{index}.json';deadline=time.monotonic()+180
 while not request.exists():
  if time.monotonic()>deadline:raise TimeoutError('request timeout')
  time.sleep(.02)
 data=json.loads(request.read_text())
 try:
  ctx,inventory=produce(data['stem'],data['config'],ctx,inventory);result={'ok':True,'index':index}
 except Exception:
  result={'ok':False,'index':index,'error':traceback.format_exc()};ctx=inventory=None
 temp=box/f'response_{index}.tmp';temp.write_text(json.dumps(result)+'\n');temp.rename(box/f'response_{index}.json')
